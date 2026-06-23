"""Collect post-match events (cards, suspensions, form, injuries) for predictions."""

from __future__ import annotations

import re
from datetime import date
from html import unescape
from pathlib import Path

import pandas as pd
import requests

from .config import (
    DATA_DIR,
    DEFAULT_MATCH_EVENTS_PATH,
    DEFAULT_MATCH_RESULTS_PATH,
    MATCH_EVENTS_TRACKER_PATH,
)
from .group_results import load_completed_group_matches
from .injury_media_collector import collect_media_injuries_for_match, should_replace_event
from .tournament_data import GROUPS

WIKI_GROUP_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_{group}"
SUPPLEMENT_PATH = DATA_DIR / "match_events_supplement.csv"
SCAN_LOG_PATH = DATA_DIR / "match_event_scans.csv"
SCAN_COLUMNS = ["date", "match_num", "home", "away", "scanned_at"]

EVENT_COLUMNS = [
    "date",
    "team",
    "player",
    "event_type",
    "severity",
    "misses_next_match",
    "yellow_count",
    "notes",
    "source",
]

_USER_AGENT = "wc2026-event-collector/1.0 (research; contact: local)"

_INJURY_KEYWORDS = re.compile(
    r"\b(?:injur(?:y|ies|ed)|hamstring|concussion|muscle strain|strained|"
    r"knock|torn|rupture|cramp|sprain|fracture|dislocat\w*)\b",
    re.IGNORECASE,
)
_INJURY_OUT_KEYWORDS = re.compile(
    r"\b(?:ruled out|will miss|out for|unable to|sidelined|miss(?:es)?\s+the\s+next)\b",
    re.IGNORECASE,
)
_EARLY_INJURY_SUB_MAX_MINUTE = 30


def _fetch_wiki_group_page(group: str, timeout: int = 25) -> str:
    url = WIKI_GROUP_URL.format(group=group)
    response = requests.get(url, headers={"User-Agent": _USER_AGENT}, timeout=timeout)
    response.raise_for_status()
    return response.text


def _normalize_player_name(name: str) -> str:
    name = unescape(name).strip()
    if " (" in name:
        name = name.split(" (")[0]
    return name


def _sub_off_minute(row_html: str) -> str:
    match = re.search(
        r"Sub_off\.svg.*?>(\d+(?:\+\d+)?)'</span>",
        row_html,
        re.DOTALL | re.IGNORECASE,
    )
    return match.group(1) if match else ""


def _is_concussion_sub(row_html: str) -> bool:
    return bool(
        re.search(
            r"concussion|>con\.<|title=\"Substituted off due to concussion\"",
            row_html,
            re.IGNORECASE,
        )
    )


def _is_starter_row(row_html: str) -> bool:
    return "<b>" in row_html


def _parse_lineup_table(table_html: str) -> list[dict[str, str | bool | float]]:
    """Parse cards and injury signals from a single team's lineup table."""
    events: list[dict[str, str | bool | float]] = []
    for row in re.finditer(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL):
        row_html = row.group(1)
        name_match = re.search(r'title="([^"]+)"[^>]*>[^<]+</a>', row_html)
        if not name_match:
            continue
        name = _normalize_player_name(name_match.group(1))

        for cell in re.finditer(
            r"<td>(.*?)</td>",
            row_html,
            re.DOTALL,
        ):
            cell_html = cell.group(1)
            minute_match = re.search(r"(\d+(?:\+\d+)?)'", cell_html)
            minute = minute_match.group(1) if minute_match else ""
            if "Yellow_card" in cell_html:
                events.append(
                    {
                        "player": name,
                        "event_type": "yellow_card",
                        "minute": minute,
                        "misses_next_match": False,
                    }
                )
            elif "Red_card" in cell_html:
                events.append(
                    {
                        "player": name,
                        "event_type": "red_card",
                        "minute": minute,
                        "misses_next_match": True,
                    }
                )

        if "Sub_off" in row_html and _is_concussion_sub(row_html):
            minute = _sub_off_minute(row_html)
            events.append(
                {
                    "player": name,
                    "event_type": "injury_monitor",
                    "minute": minute,
                    "misses_next_match": False,
                    "severity": 0.08,
                    "notes_hint": "concussion substitution",
                }
            )
        elif (
            "Sub_off" in row_html
            and _is_starter_row(row_html)
            and not _is_concussion_sub(row_html)
            and "Yellow_card" not in row_html
            and "Red_card" not in row_html
        ):
            minute = _sub_off_minute(row_html)
            if minute:
                base_minute = int(minute.split("+")[0])
                if base_minute < _EARLY_INJURY_SUB_MAX_MINUTE:
                    events.append(
                        {
                            "player": name,
                            "event_type": "injury_monitor",
                            "minute": minute,
                            "misses_next_match": False,
                            "severity": 0.04,
                            "notes_hint": "early starter substitution",
                        }
                    )

        if re.search(r"Injury_icon", row_html, re.IGNORECASE):
            events.append(
                {
                    "player": name,
                    "event_type": "injury_monitor",
                    "minute": _sub_off_minute(row_html),
                    "misses_next_match": False,
                    "severity": 0.06,
                    "notes_hint": "injury icon in lineup",
                }
            )

    return events


def _strip_tables(html: str) -> str:
    return re.sub(r"<table[^>]*>.*?</table>", " ", html, flags=re.DOTALL)


def _player_team_map(team_tables: list[tuple[str, str]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for team, table_html in team_tables:
        for row in re.finditer(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL):
            name_match = re.search(r'title="([^"]+)"', row.group(1))
            if name_match:
                mapping[_normalize_player_name(name_match.group(1))] = team
    return mapping


def parse_wiki_match_injuries_from_prose(
    chunk: str,
    player_teams: dict[str, str],
) -> list[dict]:
    """Extract injury mentions from match-report paragraphs on a group page."""
    if not chunk or not player_teams:
        return []

    events: list[dict] = []
    seen: set[tuple[str, str]] = set()
    prose = _strip_tables(chunk)

    for para in re.finditer(r"<p[^>]*>(.*?)</p>", prose, re.DOTALL):
        paragraph = para.group(1)
        if not _INJURY_KEYWORDS.search(paragraph):
            continue

        plain = unescape(re.sub(r"<[^>]+>", " ", paragraph))
        plain = re.sub(r"\s+", " ", plain).strip()
        event_type = (
            "injury_out"
            if _INJURY_OUT_KEYWORDS.search(plain)
            else "injury_monitor"
        )
        severity = 0.10 if event_type == "injury_out" else 0.05

        for link in re.finditer(r'title="([^"]+)"', paragraph):
            player = _normalize_player_name(link.group(1))
            team = player_teams.get(player)
            if not team:
                continue
            key = (player, event_type)
            if key in seen:
                continue
            seen.add(key)
            events.append(
                {
                    "team": team,
                    "player": player,
                    "event_type": event_type,
                    "severity": severity,
                    "misses_next_match": event_type == "injury_out",
                    "yellow_count": 0,
                    "notes": plain[:160],
                    "source": "Wikipedia",
                }
            )

    return events


def _score_variants(home_goals: int | None, away_goals: int | None) -> list[str]:
    if home_goals is None or away_goals is None:
        return []
    return [
        f"{home_goals}–{away_goals}",
        f"{home_goals}&ndash;{away_goals}",
        f"{home_goals}-{away_goals}",
        f"{home_goals}&#8211;{away_goals}",
    ]


def _extract_match_chunk(
    html: str,
    home: str,
    away: str,
    home_goals: int | None = None,
    away_goals: int | None = None,
) -> str:
    """
    Locate the completed-match section on a group page.

    Wikipedia group pages use `### Home vs Away` headings; we anchor on those
    and require the final score in the section body.
    """
    score_tokens = _score_variants(home_goals, away_goals)
    heading_patterns = [
        rf"<h3[^>]*>\s*(?:<span[^>]*>)?\s*{re.escape(home)}\s+vs\.?\s+{re.escape(away)}",
        rf"<h3[^>]*>\s*(?:<span[^>]*>)?\s*{re.escape(away)}\s+vs\.?\s+{re.escape(home)}",
    ]

    sections = re.split(r"(?=<h3[^>]*>)", html)
    best = ""
    best_score = -1

    for section in sections:
        heading_hit = any(re.search(pat, section, re.IGNORECASE) for pat in heading_patterns)
        if not heading_hit:
            continue

        score = 10
        if score_tokens and any(token in section for token in score_tokens):
            score += 8
        else:
            continue
        if "Yellow_card" in section or "Red_card" in section:
            score += 3
        if len(section) > len(best) or score > best_score:
            best = section
            best_score = score

    return best


def _team_from_lineup_block(table_html: str) -> str | None:
    bold = re.search(r"\*\*([^*\[]+)\[", table_html)
    if bold:
        return unescape(bold.group(1)).strip()
    header = re.search(
        r"<th[^>]*>(?:<a[^>]*>)?([^<]+?)(?:</a>)?</th>",
        table_html,
        re.IGNORECASE,
    )
    if not header:
        return None
    name = unescape(header.group(1)).strip()
    if " (" in name:
        name = name.split(" (")[0]
    return name or None


def _lineup_team_tables(
    chunk: str,
    home: str,
    away: str,
) -> list[tuple[str, str]]:
    tables = [
        match.group(1)
        for match in re.finditer(r"<table[^>]*>(.*?)</table>", chunk, re.DOTALL)
    ]
    lineup_tables = [
        table
        for table in tables
        if "Yellow_card" in table or "Red_card" in table or "Sub_off" in table
    ]
    if len(lineup_tables) < 2:
        return []

    team_tables: list[tuple[str, str]] = []
    for table_html in lineup_tables[:2]:
        header_team = _team_from_lineup_block(table_html)
        if header_team in {home, away}:
            team_tables.append((header_team, table_html))

    if len(team_tables) < 2:
        team_tables = [(home, lineup_tables[0]), (away, lineup_tables[1])]
    return team_tables


def _lineup_event_to_row(team: str, event: dict) -> dict:
    etype = str(event["event_type"])
    if etype in {"injury_monitor", "injury_out"}:
        notes_hint = str(event.get("notes_hint", "injury signal"))
        minute = str(event.get("minute", "") or "")
        notes = notes_hint
        if minute:
            notes += f" {minute}′"
        return {
            "team": team,
            "player": event["player"],
            "event_type": etype,
            "severity": float(event.get("severity", 0.05)),
            "misses_next_match": bool(event.get("misses_next_match", False)),
            "yellow_count": 0,
            "notes": notes,
            "source": "Wikipedia",
        }

    severity = 0.12 if etype == "red_card" else 0.0
    notes = etype.replace("_", " ")
    minute = str(event.get("minute", "") or "")
    if minute:
        notes += f" {minute}′"
    return {
        "team": team,
        "player": event["player"],
        "event_type": etype,
        "severity": severity,
        "misses_next_match": bool(event.get("misses_next_match", False)),
        "yellow_count": 1 if etype == "yellow_card" else 0,
        "notes": notes,
        "source": "Wikipedia",
    }


def parse_wiki_match_events(
    html: str,
    home: str,
    away: str,
    home_goals: int | None = None,
    away_goals: int | None = None,
) -> list[dict]:
    """Extract cards and injury signals from a Wikipedia group-page match section."""
    chunk = _extract_match_chunk(html, home, away, home_goals, away_goals)
    if not chunk:
        return []

    team_tables = _lineup_team_tables(chunk, home, away)
    if not team_tables:
        return []

    events: list[dict] = []
    for team, table_html in team_tables:
        for lineup_event in _parse_lineup_table(table_html):
            events.append(_lineup_event_to_row(team, lineup_event))

    player_teams = _player_team_map(team_tables)
    events.extend(parse_wiki_match_injuries_from_prose(chunk, player_teams))
    return events


def parse_wiki_match_cards(
    html: str,
    home: str,
    away: str,
    home_goals: int | None = None,
    away_goals: int | None = None,
) -> list[dict]:
    """Backward-compatible alias for card and injury event extraction."""
    return parse_wiki_match_events(html, home, away, home_goals, away_goals)


def load_supplement_events(path: Path | str = SUPPLEMENT_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=EVENT_COLUMNS)
    return pd.read_csv(path)


def _event_key(row: dict | pd.Series) -> tuple:
    return (
        str(row["date"]),
        str(row["team"]),
        str(row.get("player", "")),
        str(row["event_type"]),
    )


def _cards_to_rows(match_date: str, cards: list[dict]) -> list[dict]:
    rows = []
    for card in cards:
        rows.append({"date": match_date, **card})
    return rows


def _load_scan_log(path: Path = SCAN_LOG_PATH) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=SCAN_COLUMNS)
    return pd.read_csv(path)


def _save_scan_log(rows: list[dict], path: Path = SCAN_LOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_scan_log(path)
    new_df = pd.DataFrame(rows)
    combined = pd.concat([existing, new_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["date", "match_num"], keep="last")
    combined.to_csv(path, index=False)


def _matches_missing_events(
    results: pd.DataFrame,
    scans: pd.DataFrame,
) -> pd.DataFrame:
    if results.empty:
        return results.iloc[0:0]

    if scans.empty:
        return results.copy()

    scanned = set(zip(scans["date"].astype(str), scans["match_num"].astype(int)))
    mask = [
        (str(row["date"]), int(row["match_num"])) not in scanned
        for _, row in results.iterrows()
    ]
    return results[mask].copy()


def collect_events_for_new_results(
    results_path: Path | str = DEFAULT_MATCH_RESULTS_PATH,
    events_path: Path | str = DEFAULT_MATCH_EVENTS_PATH,
    supplement_path: Path | str = SUPPLEMENT_PATH,
    *,
    force_dates: list[str] | None = None,
) -> int:
    """
    Scrape Wikipedia for cards, injuries, and merge curated supplements.

    Injury capture uses Wikipedia lineup markers (concussion subs, early starter
    exits, injury icons), match-report prose, and sports media outlets (ESPN,
    AP, BBC, Guardian, FOX, CBS, Yahoo, USA Today, NYT Athletic, etc. via
    Google News RSS plus direct Guardian/ESPN feeds).

    Returns number of new event rows appended.
    """
    results_path = Path(results_path)
    events_path = Path(events_path)
    supplement_path = Path(supplement_path)

    results = load_completed_group_matches(results_path)
    existing = (
        pd.read_csv(events_path)
        if events_path.exists()
        else pd.DataFrame(columns=EVENT_COLUMNS)
    )

    scans = _load_scan_log()

    if force_dates:
        target = results[results["date"].astype(str).isin(force_dates)].copy()
    else:
        target = _matches_missing_events(results, scans)

    if target.empty:
        return 0

    new_rows: list[dict] = []
    scan_rows: list[dict] = []
    supplements = load_supplement_events(supplement_path)
    existing_keys = {_event_key(row) for _, row in existing.iterrows()}
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for _, match in target.iterrows():
        match_date = str(match["date"])
        match_num = int(match["match_num"])
        group = str(match["group"])
        home = str(match["home"])
        away = str(match["away"])

        try:
            html = _fetch_wiki_group_page(group)
            wiki_events = parse_wiki_match_events(
                html,
                home,
                away,
                home_goals=int(match["home_goals"]),
                away_goals=int(match["away_goals"]),
            )
            new_rows.extend(_cards_to_rows(match_date, wiki_events))
        except Exception as exc:
            print(
                f"  Warning: could not fetch Wikipedia events for {home} vs {away}: {exc}"
            )

        try:
            media_injuries = collect_media_injuries_for_match(home, away, match_date)
            new_rows.extend(_cards_to_rows(match_date, media_injuries))
            if media_injuries:
                sources = sorted({e["source"] for e in media_injuries})
                print(
                    f"  Media injuries for {home} vs {away}: "
                    f"{len(media_injuries)} from {', '.join(sources)}"
                )
        except Exception as exc:
            print(
                f"  Warning: could not fetch media injuries for {home} vs {away}: {exc}"
            )

        if not supplements.empty:
            supp = supplements[
                (supplements["date"].astype(str) == match_date)
                & (supplements["team"].isin([home, away]))
            ]
            for _, row in supp.iterrows():
                new_rows.append(row.to_dict())

        scan_rows.append(
            {
                "date": match_date,
                "match_num": match_num,
                "home": home,
                "away": away,
                "scanned_at": now,
            }
        )

    batch_by_key: dict[tuple, dict] = {}
    for row in new_rows:
        for col in EVENT_COLUMNS:
            if col not in row or pd.isna(row.get(col)):
                if col == "player":
                    row[col] = ""
                elif col in {"severity", "yellow_count"}:
                    row[col] = 0.0 if col == "severity" else 0
                elif col == "misses_next_match":
                    row[col] = False
                elif col == "notes":
                    row[col] = ""
                elif col == "source":
                    row[col] = "curated"
        normalized = {col: row[col] for col in EVENT_COLUMNS}
        key = _event_key(normalized)
        prev = batch_by_key.get(key)
        if prev is None or should_replace_event(prev, normalized):
            batch_by_key[key] = normalized

    deduped: list[dict] = []
    seen = set(existing_keys)
    for row in batch_by_key.values():
        key = _event_key(row)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    if not deduped:
        return 0

    events_path.parent.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame(deduped)
    if events_path.exists():
        combined = pd.concat([existing, out], ignore_index=True)
    else:
        combined = out
    combined.to_csv(events_path, index=False)
    if scan_rows:
        _save_scan_log(scan_rows)
    return len(deduped)


def regenerate_events_tracker(
    events_path: Path | str = DEFAULT_MATCH_EVENTS_PATH,
    results_path: Path | str = DEFAULT_MATCH_RESULTS_PATH,
    tracker_path: Path | str = MATCH_EVENTS_TRACKER_PATH,
) -> Path:
    """Rebuild match_events_tracker.md from CSV data and results."""
    events_path = Path(events_path)
    results_path = Path(results_path)
    tracker_path = Path(tracker_path)

    events = (
        pd.read_csv(events_path)
        if events_path.exists()
        else pd.DataFrame(columns=EVENT_COLUMNS)
    )
    results = load_completed_group_matches(results_path)

    today = date.today().isoformat()
    lines = [
        "# Match Events Tracker — World Cup 2026",
        "",
        "Post-match discipline, suspensions, injuries, and form signals that may affect "
        "**future** predictions.",
        "FIFA rules: **straight red or second yellow = 1-match ban**; "
        "**two yellows across matches = 1-match ban**; yellows reset after group stage.",
        "",
        f"**Updated**: {today} (auto-generated from `simulations/data/match_events.csv`)",
        "",
    ]

    if results.empty:
        lines.append("_No completed matches yet._")
    else:
        for match_date in sorted(results["date"].astype(str).unique()):
            day_matches = results[results["date"].astype(str) == match_date]
            groups = ", ".join(sorted(day_matches["group"].astype(str).unique()))
            lines.append(f"## {match_date} — Group(s) {groups}")
            lines.append("")

            for _, match in day_matches.iterrows():
                home = str(match["home"])
                away = str(match["away"])
                score = f"{int(match['home_goals'])}–{int(match['away_goals'])}"
                lines.append(f"### {home} {score} {away}")
                lines.append("")
                lines.append(
                    "| Player | Team | Event | Next-match impact | Source |"
                )
                lines.append(
                    "|--------|------|-------|-------------------|--------|"
                )

                if events.empty:
                    lines.append("| — | — | _No events logged_ | — | — |")
                else:
                    day_events = events[events["date"].astype(str) == match_date]
                    match_events = day_events[
                        day_events["team"].isin([home, away])
                    ].sort_values(["team", "event_type", "player"])

                    if match_events.empty:
                        lines.append("| — | — | _No events logged_ | — | — |")
                    else:
                        for _, ev in match_events.iterrows():
                            impact = _format_impact(ev)
                            event_label = _format_event_label(ev)
                            player = str(ev.get("player", "") or "—")
                            lines.append(
                                f"| {player} | {ev['team']} | {event_label} | "
                                f"{impact} | {ev.get('source', '')} |"
                            )
                lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Model integration",
            "",
            "Structured data: `simulations/data/match_events.csv`",
            "Supplements (form/injuries): `simulations/data/match_events_supplement.csv`",
            "Collected automatically by `python -m wc2026_monte_carlo add-results` "
            "(Wikipedia cards/injuries + ESPN, AP, BBC, Guardian, FOX, CBS, Yahoo, "
            "USA Today, NYT Athletic, and other outlets via media search).",
            "Manual re-scrape: `python -m wc2026_monte_carlo.match_event_collector --force-date YYYY-MM-DD`",
            "Parser: `match_availability` → merged into team features for `predict`.",
        ]
    )

    tracker_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tracker_path


def _format_event_label(row: pd.Series) -> str:
    etype = str(row["event_type"])
    notes = str(row.get("notes", "") or "")
    labels = {
        "yellow_card": "Yellow card",
        "red_card": "Red card",
        "injury_monitor": "Injury monitor",
        "injury_out": "Injury out",
        "form_boost": "Form boost",
        "form_concern": "Form concern",
        "team_discipline": "Team discipline",
        "yellow_accumulation": "Yellow accumulation ban",
    }
    base = labels.get(etype, etype.replace("_", " ").title())
    return f"{base} ({notes})" if notes and etype in {"yellow_card", "red_card"} else (
        f"{base} — {notes}" if notes else base
    )


def _format_impact(row: pd.Series) -> str:
    if str(row.get("misses_next_match", "")).lower() in {"true", "1", "yes"}:
        return "**Suspended** next match"
    if str(row["event_type"]) == "yellow_card":
        return "On **1 yellow** — second triggers ban"
    if str(row["event_type"]) == "injury_monitor":
        return "Monitor fitness"
    if str(row["event_type"]) == "injury_out":
        return "**Likely out** next match"
    if str(row["event_type"]) == "form_boost":
        return "**Form boost**"
    if str(row["event_type"]) == "form_concern":
        return "**Form concern**"
    return "—"


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect match events from Wikipedia and supplements"
    )
    parser.add_argument(
        "--force-date",
        action="append",
        dest="force_dates",
        help="Re-collect events for a specific match date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--tracker-only",
        action="store_true",
        help="Only regenerate match_events_tracker.md",
    )
    args = parser.parse_args(argv)

    if args.tracker_only:
        path = regenerate_events_tracker()
        print(f"Tracker updated: {path}")
        return 0

    added = collect_events_for_new_results(force_dates=args.force_dates)
    tracker = regenerate_events_tracker()
    print(f"Added {added} event row(s) to match_events.csv")
    print(f"Tracker updated: {tracker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())