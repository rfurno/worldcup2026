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


def _fetch_wiki_group_page(group: str, timeout: int = 25) -> str:
    url = WIKI_GROUP_URL.format(group=group)
    response = requests.get(url, headers={"User-Agent": _USER_AGENT}, timeout=timeout)
    response.raise_for_status()
    return response.text


def _parse_lineup_table(table_html: str) -> list[dict[str, str | bool]]:
    cards: list[dict[str, str | bool]] = []
    for match in re.finditer(
        r'title="([^"]+)"[^>]*>[^<]+</a></td>\s*<td>(.*?)</td>',
        table_html,
        re.DOTALL,
    ):
        name = unescape(match.group(1))
        if " (" in name:
            name = name.split(" (")[0]
        cell = match.group(2)
        minute_match = re.search(r"(\d+(?:\+\d+)?)'", cell)
        minute = minute_match.group(1) if minute_match else ""
        if "Yellow_card" in cell:
            cards.append(
                {
                    "player": name,
                    "event_type": "yellow_card",
                    "minute": minute,
                    "misses_next_match": False,
                }
            )
        elif "Red_card" in cell:
            cards.append(
                {
                    "player": name,
                    "event_type": "red_card",
                    "minute": minute,
                    "misses_next_match": True,
                }
            )
    return cards


def parse_wiki_match_cards(html: str, home: str, away: str) -> list[dict]:
    """Extract discipline events from a Wikipedia group-page match section."""
    idx = html.find(f"{home} vs")
    if idx < 0:
        return []
    chunk = html[idx:]
    end = chunk.find("<h3><span")
    if end > 0:
        chunk = chunk[:end]

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

    events: list[dict] = []
    for team, table_html in zip([home, away], lineup_tables[:2]):
        for card in _parse_lineup_table(table_html):
            severity = 0.12 if card["event_type"] == "red_card" else 0.0
            notes = f"{card['event_type'].replace('_', ' ')}"
            if card["minute"]:
                notes += f" {card['minute']}′"
            events.append(
                {
                    "team": team,
                    "player": card["player"],
                    "event_type": card["event_type"],
                    "severity": severity,
                    "misses_next_match": card["misses_next_match"],
                    "yellow_count": 1 if card["event_type"] == "yellow_card" else 0,
                    "notes": notes,
                    "source": "Wikipedia",
                }
            )
    return events


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
    Scrape Wikipedia for cards and merge curated supplements for unscanned dates.

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
            cards = parse_wiki_match_cards(html, home, away)
            new_rows.extend(_cards_to_rows(match_date, cards))
        except Exception as exc:
            print(f"  Warning: could not fetch Wikipedia cards for {home} vs {away}: {exc}")

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

    deduped: list[dict] = []
    seen = set(existing_keys)
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
        key = _event_key(row)
        if key in seen:
            continue
        seen.add(key)
        deduped.append({col: row[col] for col in EVENT_COLUMNS})

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
            "Collector: `python -m wc2026_monte_carlo.match_event_collector`",
            "Parser: `wc2026_monte_carlo.match_availability` → merged into team features.",
            "",
            "Evaluate impact: `python -m wc2026_monte_carlo.availability_report --compare`",
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