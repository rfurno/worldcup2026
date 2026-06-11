"""Recent form and head-to-head signals from historical match data (#3)."""

from __future__ import annotations

import numpy as np
import pandas as pd

# Map common historical name variants to 2026 draw names
TEAM_ALIASES: dict[str, str] = {
    "Korea Republic": "South Korea",
    "Republic of Korea": "South Korea",
    "Czech Republic": "Czechia",
    "USA": "United States",
    "United States of America": "United States",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "IR Iran": "Iran",
    "KSA": "Saudi Arabia",
    "Congo DR": "DR Congo",
    "Congo, DR": "DR Congo",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
}


def canonical_team(name: str) -> str:
    name = str(name).strip()
    return TEAM_ALIASES.get(name, name)


def _prepare_history(historical: pd.DataFrame) -> pd.DataFrame:
    if historical.empty:
        return historical
    df = historical.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "home_score", "away_score"])
    df = df[(df["home_score"] >= 0) & (df["away_score"] >= 0)]
    df["home_team"] = df["home_team"].map(canonical_team)
    df["away_team"] = df["away_team"].map(canonical_team)
    return df.sort_values("date")


def compute_recent_form(
    historical: pd.DataFrame,
    teams: list[str],
    xi: float = 0.003,
    reference_date: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """
    Time-decayed goal difference per match for each team (#3).

    Complements static xG CSV with actual recent international results.
    """
    df = _prepare_history(historical)
    if df.empty:
        return pd.DataFrame({"team": teams, "recent_form": 0.0})

    if reference_date is None:
        reference_date = df["date"].max()

    rows: list[dict[str, float | str]] = []
    for team in teams:
        as_home = df[df["home_team"] == team]
        as_away = df[df["away_team"] == team]
        weighted_gd = 0.0
        weight_sum = 0.0

        for _, m in as_home.iterrows():
            days = max((reference_date - m["date"]).days, 0)
            w = float(np.exp(-xi * days))
            weighted_gd += w * (m["home_score"] - m["away_score"])
            weight_sum += w

        for _, m in as_away.iterrows():
            days = max((reference_date - m["date"]).days, 0)
            w = float(np.exp(-xi * days))
            weighted_gd += w * (m["away_score"] - m["home_score"])
            weight_sum += w

        form = weighted_gd / weight_sum if weight_sum > 0 else 0.0
        rows.append({"team": team, "recent_form": form})

    return pd.DataFrame(rows)


def h2h_log_shift(
    historical: pd.DataFrame,
    home: str,
    away: str,
    xi: float = 0.003,
    max_matches: int = 8,
    scale: float = 0.06,
) -> tuple[float, float]:
    """
    Small Dixon-Coles rate shift from head-to-head history (#3).

    Returns (home_shift, away_shift) added to log goal rate.
    """
    df = _prepare_history(historical)
    if df.empty:
        return 0.0, 0.0

    mask = (
        ((df["home_team"] == home) & (df["away_team"] == away))
        | ((df["home_team"] == away) & (df["away_team"] == home))
    )
    meetings = df[mask].tail(max_matches)
    if meetings.empty:
        return 0.0, 0.0

    ref = df["date"].max()
    home_gd = 0.0
    weight_sum = 0.0
    for _, m in meetings.iterrows():
        days = max((ref - m["date"]).days, 0)
        w = float(np.exp(-xi * days))
        if m["home_team"] == home:
            home_gd += w * (m["home_score"] - m["away_score"])
        else:
            home_gd += w * (m["away_score"] - m["home_score"])
        weight_sum += w

    if weight_sum <= 0:
        return 0.0, 0.0

    avg_gd = home_gd / weight_sum
    shift = float(np.clip(scale * avg_gd, -0.12, 0.12))
    return shift, -shift