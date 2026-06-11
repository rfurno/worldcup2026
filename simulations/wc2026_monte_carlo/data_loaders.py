"""Data pipeline: internal markdown, CSV fallbacks, and external sources."""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

from .config import (
    BETTING_ODDS_PATH,
    DEFAULT_ELO_PATH,
    DEFAULT_HISTORICAL_MATCHES_PATH,
    DEFAULT_SQUAD_VALUES_PATH,
    DEFAULT_XG_FORM_PATH,
    ELO_RATINGS_URL,
    INJURY_TRACKER_PATH,
    KAGGLE_RESULTS_URL,
    OPENING_FIXTURES_PATH,
    PLAYER_TRACKER_PATH,
    WINNER_ODDS_PATH,
)
from .tournament_data import all_teams


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def parse_injury_tracker(path: Path = INJURY_TRACKER_PATH) -> pd.DataFrame:
    """
    Parse injury_tracker.md (additional-data-sources.md #7).

    Returns team-level injury multipliers in (0, 1].
    """
    text = _read_text(path)
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("|-"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5 or cells[0].lower() == "player":
            continue
        player, team, status, impact, availability = cells[:5]
        if team.lower() == "team":
            continue

        severity = 0.0
        status_l = status.lower()
        impact_l = impact.lower()
        avail_l = availability.lower()
        if "out" in avail_l or "acl" in status_l or "rupture" in status_l:
            severity = 0.15
        elif "monitor" in avail_l or "limited" in avail_l:
            severity = 0.05
        elif "major" in impact_l:
            severity = 0.12
        elif "concern" in impact_l:
            severity = 0.06

        rows.append({"player": player, "team": team, "severity": severity})

    if not rows:
        return pd.DataFrame(columns=["team", "injury_multiplier"])

    df = pd.DataFrame(rows)
    agg = df.groupby("team", as_index=False)["severity"].sum()
    agg["injury_multiplier"] = (1.0 - agg["severity"].clip(0, 0.35)).clip(0.65, 1.0)
    return agg[["team", "injury_multiplier"]]


def parse_winner_odds(path: Path = WINNER_ODDS_PATH) -> pd.DataFrame:
    """
    Parse winner_odds_table.md and betting_sites_odds.md (additional-data-sources.md #5).
    """
    rows: list[dict[str, Any]] = []
    for source_path in (path, BETTING_ODDS_PATH):
        text = _read_text(source_path)
        for line in text.splitlines():
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 3:
                continue
            team = cells[1] if cells[0].isdigit() or cells[0] == "-" else cells[0]
            if team.lower() in {"team", "rank"}:
                continue
            if team.startswith("Others"):
                continue

            implied = None
            for cell in cells[2:]:
                m = re.search(r"(\d+(?:\.\d+)?)\s*%", cell)
                if m:
                    implied = float(m.group(1)) / 100.0
                    break
                odds_m = re.search(r"\+(\d+)", cell)
                if odds_m:
                    odds = int(odds_m.group(1))
                    implied = 100.0 / (odds + 100.0)
                    break

            if implied is not None and team:
                rows.append({"team": team, "market_prob": implied})

    if not rows:
        return pd.DataFrame(columns=["team", "market_prob"])

    df = pd.DataFrame(rows)
    return df.groupby("team", as_index=False)["market_prob"].mean()


def parse_player_tracker(path: Path = PLAYER_TRACKER_PATH) -> pd.DataFrame:
    """
    Parse player_tracker.md for qualitative strength adjustments (#2, #7).
    """
    text = _read_text(path)
    boosts: dict[str, float] = {}
    current_team: str | None = None

    for line in text.splitlines():
        header = re.match(r"^###\s+(.+)$", line)
        if header:
            name = header.group(1).strip()
            name = re.sub(r"\s*\(.*\)$", "", name)
            if name in all_teams() or name.split()[0] in {"Spain", "France", "England", "Brazil"}:
                current_team = name.split("(")[0].strip()
                if current_team not in all_teams():
                    for team in all_teams():
                        if team.lower() in name.lower():
                            current_team = team
                            break
            continue

        if "Favorites" in line or "favorites" in line:
            if current_team:
                boosts[current_team] = boosts.get(current_team, 0.0) + 0.03

        if "Out" in line and "ACL" in line and current_team:
            boosts[current_team] = boosts.get(current_team, 0.0) - 0.05

        if "downgraded" in line.lower():
            m = re.search(r"(\w+)\s+downgraded", line, re.I)
            if m:
                for team in all_teams():
                    if team.lower().startswith(m.group(1).lower()):
                        boosts[team] = boosts.get(team, 0.0) - 0.04

    if not boosts:
        return pd.DataFrame(columns=["team", "player_tracker_adj"])

    df = pd.DataFrame(
        [{"team": team, "player_tracker_adj": adj} for team, adj in boosts.items()]
    )
    return df


def parse_opening_fixtures(path: Path = OPENING_FIXTURES_PATH) -> pd.DataFrame:
    """Parse opening_fixtures_predictions.md for host/venue hints (#3, #6)."""
    text = _read_text(path)
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.startswith("|") or "Date" in line or line.startswith("|-"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        match, group, predicted, factors = cells[1], cells[2], cells[3], cells[4]
        if " vs " not in match:
            continue
        home, away = [p.strip() for p in match.split(" vs ")]
        rows.append(
            {
                "home": home,
                "away": away,
                "group": group,
                "predicted_winner": predicted,
                "factors": factors,
            }
        )
    return pd.DataFrame(rows)


def load_csv_ratings(path: Path, value_col: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["team", value_col])
    df = pd.read_csv(path)
    if "team" not in df.columns or value_col not in df.columns:
        raise ValueError(f"{path} must contain 'team' and '{value_col}' columns")
    return df[["team", value_col]].copy()


def fetch_elo_ratings(url: str = ELO_RATINGS_URL, timeout: int = 20) -> pd.DataFrame:
    """
    Fetch Elo ratings from eloratings.net (#1).

    Falls back to local CSV if the network request fails.
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        raw = response.text
        df = pd.read_csv(io.StringIO(raw), sep=None, engine="python")
        cols = {c.lower(): c for c in df.columns}
        country_col = cols.get("country") or cols.get("team") or list(df.columns)[0]
        rating_col = cols.get("rating") or cols.get("elo") or list(df.columns)[1]
        out = df[[country_col, rating_col]].rename(
            columns={country_col: "team", rating_col: "elo"}
        )
        out["team"] = out["team"].astype(str).str.strip()
        return out
    except Exception:
        return load_csv_ratings(DEFAULT_ELO_PATH, "elo")


def fetch_historical_matches(
    url: str = KAGGLE_RESULTS_URL, timeout: int = 30
) -> pd.DataFrame:
    """
    Fetch international results for Dixon-Coles calibration (#3).
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
        required = {"date", "home_team", "away_team", "home_score", "away_score"}
        if not required.issubset(df.columns):
            raise ValueError("Unexpected historical results schema")
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        return df
    except Exception:
        if DEFAULT_HISTORICAL_MATCHES_PATH.exists():
            df = pd.read_csv(DEFAULT_HISTORICAL_MATCHES_PATH)
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            return df.dropna(subset=["date"])
        return pd.DataFrame(
            columns=["date", "home_team", "away_team", "home_score", "away_score"]
        )


def build_team_features(
    refresh_external: bool = False,
) -> pd.DataFrame:
    """
    Merge all data sources into a single team feature table.
    """
    teams = pd.DataFrame({"team": all_teams()})

    if refresh_external:
        elo = fetch_elo_ratings()
        historical = fetch_historical_matches()
        if not historical.empty:
            historical.to_csv(DEFAULT_HISTORICAL_MATCHES_PATH, index=False)
        if not elo.empty:
            elo.to_csv(DEFAULT_ELO_PATH, index=False)
    else:
        elo = load_csv_ratings(DEFAULT_ELO_PATH, "elo")
        if elo.empty:
            elo = fetch_elo_ratings()

    squad = load_csv_ratings(DEFAULT_SQUAD_VALUES_PATH, "squad_value_meur")
    xg = load_csv_ratings(DEFAULT_XG_FORM_PATH, "xg_diff_per_match")
    market = parse_winner_odds()
    injuries = parse_injury_tracker()
    player_adj = parse_player_tracker()

    features = teams.merge(elo, on="team", how="left")
    features = features.merge(squad, on="team", how="left")
    features = features.merge(xg, on="team", how="left")
    features = features.merge(market, on="team", how="left")
    features = features.merge(injuries, on="team", how="left")
    features = features.merge(player_adj, on="team", how="left")

    # Reasonable defaults for teams missing external data
    features["elo"] = features["elo"].fillna(features["elo"].median())
    features["squad_value_meur"] = features["squad_value_meur"].fillna(
        features["squad_value_meur"].median()
    )
    features["xg_diff_per_match"] = features["xg_diff_per_match"].fillna(0.0)
    features["market_prob"] = features["market_prob"].fillna(
        1.0 / len(features)
    )
    features["injury_multiplier"] = features["injury_multiplier"].fillna(1.0)
    features["player_tracker_adj"] = features["player_tracker_adj"].fillna(0.0)

    return features


def normalize_signal(series: pd.Series) -> pd.Series:
    std = series.std()
    if std == 0 or np.isnan(std):
        return pd.Series(0.0, index=series.index)
    return (series - series.mean()) / std