"""Same-club nationality cluster chemistry (additional-data-sources.md #2.5)."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .config import DEFAULT_SQUAD_CLUBS_PATH
from .tournament_data import all_teams


def cluster_synergy(cluster_size: int) -> float:
    """Synergy points for n national-team players at the same club (n >= 2)."""
    if cluster_size < 2:
        return 0.0
    return float((cluster_size - 1) ** 1.35)


def compute_chemistry_from_roster(roster: pd.DataFrame) -> pd.DataFrame:
    """
    Score teams by same-club nationality clusters.

    Each cluster of 2+ players at one club contributes synergy; multiple
    clusters add up (e.g. France at PSG + Real Madrid).
    """
    if roster.empty or "team" not in roster.columns or "club" not in roster.columns:
        return pd.DataFrame(columns=["team", "club_chemistry", "cluster_count"])

    df = roster.copy()
    df["team"] = df["team"].astype(str).str.strip()
    df["club"] = df["club"].astype(str).str.strip()
    df = df[(df["team"] != "") & (df["club"] != "")]

    rows: list[dict[str, float | int | str]] = []
    for team, group in df.groupby("team"):
        club_counts = group.groupby("club").size()
        clusters = club_counts[club_counts >= 2]
        score = sum(cluster_synergy(int(n)) for n in clusters)
        rows.append(
            {
                "team": team,
                "club_chemistry": score,
                "cluster_count": int(len(clusters)),
            }
        )
    return pd.DataFrame(rows)


def parse_clubs_from_player_tracker(text: str) -> pd.DataFrame:
    """
    Extract player/club hints from player_tracker_key.md tables.

    Looks for club names in the recent-form column (e.g. "Excellent, Barcelona star").
    """
    known_clubs = (
        "Barcelona",
        "Real Madrid",
        "Atletico Madrid",
        "Manchester City",
        "Manchester United",
        "Liverpool",
        "Arsenal",
        "Chelsea",
        "Tottenham",
        "Bayern Munich",
        "Borussia Dortmund",
        "Bayer Leverkusen",
        "Paris Saint-Germain",
        "PSG",
        "Inter Milan",
        "AC Milan",
        "Juventus",
        "Napoli",
        "Inter Miami",
        "Benfica",
        "Porto",
        "Sporting CP",
        "Ajax",
        "PSV",
        "Feyenoord",
        "Galatasaray",
        "Fenerbahce",
        "Besiktas",
        "Al Hilal",
        "Al Nassr",
        "River Plate",
        "Boca Juniors",
        "Flamengo",
        "Palmeiras",
        "Corinthians",
        "Sao Paulo",
        "Monterrey",
        "Club America",
        "LAFC",
        "LA Galaxy",
    )
    club_pattern = "|".join(re.escape(c) for c in sorted(known_clubs, key=len, reverse=True))

    rows: list[dict[str, str]] = []
    current_team: str | None = None

    for line in text.splitlines():
        header = re.match(r"^##\s+(.+)$", line)
        if header:
            name = header.group(1).strip()
            name = re.sub(r"\s*\(.*\)$", "", name)
            current_team = name if name in all_teams() else None
            if current_team is None:
                for team in all_teams():
                    if team.lower() in name.lower():
                        current_team = team
                        break
            continue

        if not line.startswith("|") or line.startswith("|-"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() in {"player", "..."}:
            continue
        if current_team is None:
            continue

        player = cells[0]
        form_blob = " ".join(cells[2:])
        match = re.search(rf"\b({club_pattern})\b", form_blob, re.I)
        if match:
            club = match.group(1)
            if club.upper() == "PSG":
                club = "Paris Saint-Germain"
            rows.append({"player": player, "team": current_team, "club": club})

    if not rows:
        return pd.DataFrame(columns=["player", "team", "club"])
    return pd.DataFrame(rows)


def load_squad_clubs(path: Path = DEFAULT_SQUAD_CLUBS_PATH) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["player", "team", "club"])
    df = pd.read_csv(path)
    required = {"player", "team", "club"}
    if not required.issubset(df.columns):
        raise ValueError(f"{path} must contain columns: {sorted(required)}")
    return df[list(required)].copy()


def build_club_chemistry_features(
    squad_clubs_path: Path = DEFAULT_SQUAD_CLUBS_PATH,
    player_tracker_text: str = "",
) -> pd.DataFrame:
    """Merge CSV roster clubs with optional markdown hints, then aggregate."""
    roster = load_squad_clubs(squad_clubs_path)
    if player_tracker_text:
        parsed = parse_clubs_from_player_tracker(player_tracker_text)
        if not parsed.empty:
            roster = pd.concat([roster, parsed], ignore_index=True)
            roster = roster.drop_duplicates(subset=["player", "team"], keep="first")

    scores = compute_chemistry_from_roster(roster)
    teams = pd.DataFrame({"team": all_teams()})
    if scores.empty:
        teams["club_chemistry"] = 0.0
        teams["cluster_count"] = 0
        return teams

    out = teams.merge(scores, on="team", how="left")
    out["club_chemistry"] = out["club_chemistry"].fillna(0.0)
    out["cluster_count"] = out["cluster_count"].fillna(0).astype(int)
    return out[["team", "club_chemistry", "cluster_count"]]