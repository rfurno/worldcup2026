"""In-tournament strength updates from completed World Cup group matches."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from .config import DEFAULT_MATCH_RESULTS_PATH, SimulationConfig
from .form_and_h2h import canonical_team
from .group_results import load_completed_group_matches
from .tournament_data import all_teams


def _results_as_history(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame(
            columns=["date", "home_team", "away_team", "home_score", "away_score"]
        )
    df = results.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return pd.DataFrame(
        {
            "date": df["date"],
            "home_team": df["home"].map(canonical_team),
            "away_team": df["away"].map(canonical_team),
            "home_score": df["home_goals"].astype(int),
            "away_score": df["away_goals"].astype(int),
        }
    )


def estimate_tournament_strengths(
    results: pd.DataFrame | None = None,
    results_path: Path | str = DEFAULT_MATCH_RESULTS_PATH,
    base_home_rate: float = 1.35,
    base_away_rate: float = 1.05,
) -> pd.Series:
    """
    Attack/defense log-ratings from WC results via weighted Poisson MLE.

    Returns log-strength index aligned to all tournament teams.
    """
    df = results if results is not None else load_completed_group_matches(results_path)
    history = _results_as_history(df)
    teams = all_teams()
    strengths = pd.Series(0.0, index=teams, dtype=float)

    if history.empty:
        return strengths

    attack = {t: 0.0 for t in teams}
    defense = {t: 0.0 for t in teams}
    played = {t: 0 for t in teams}

    for _, row in history.iterrows():
        home = str(row["home_team"])
        away = str(row["away_team"])
        if home not in attack or away not in attack:
            continue
        hg, ag = int(row["home_score"]), int(row["away_score"])
        attack[home] += math.log(max(hg, 0.25) / base_home_rate)
        attack[away] += math.log(max(ag, 0.25) / base_away_rate)
        defense[home] += math.log(base_away_rate / max(ag, 0.25))
        defense[away] += math.log(base_home_rate / max(hg, 0.25))
        played[home] += 1
        played[away] += 1

    for team in teams:
        n = played[team]
        if n == 0:
            continue
        strengths[team] = 0.55 * (attack[team] / n) + 0.45 * (defense[team] / n)

    std = strengths[strengths != 0].std()
    if std and not np.isnan(std) and std > 0:
        strengths = strengths / std
    return strengths


def avg_matches_played_per_team(
    results: pd.DataFrame | None = None,
    results_path: Path | str = DEFAULT_MATCH_RESULTS_PATH,
) -> float:
    """Mean number of completed group matches per team in *results*."""
    df = results if results is not None else load_completed_group_matches(results_path)
    if df.empty:
        return 0.0
    counts: dict[str, int] = {}
    for _, row in df.iterrows():
        home, away = str(row["home"]), str(row["away"])
        counts[home] = counts.get(home, 0) + 1
        counts[away] = counts.get(away, 0) + 1
    if not counts:
        return 0.0
    return float(sum(counts.values()) / len(counts))


def resolve_tournament_form_blend(
    config: SimulationConfig,
    results: pd.DataFrame | None = None,
    *,
    override: float | None = None,
    results_path: Path | str = DEFAULT_MATCH_RESULTS_PATH,
) -> float:
    """
    Tournament-form weight: ramps with matches played when dynamic mode is on.

    w = min(cap, base + per_match * avg_games_played)
    """
    if override is not None:
        return float(np.clip(override, 0.0, 1.0))
    if not config.use_dynamic_tournament_form_blend:
        return float(np.clip(config.tournament_form_blend, 0.0, 1.0))

    avg_played = avg_matches_played_per_team(results=results, results_path=results_path)
    weight = config.tournament_form_blend_base + config.tournament_form_blend_per_match * avg_played
    return float(np.clip(weight, 0.0, config.tournament_form_blend_cap))


def blend_tournament_form(
    base_strengths: pd.Series,
    results: pd.DataFrame | None = None,
    blend: float = 0.30,
    results_path: Path | str = DEFAULT_MATCH_RESULTS_PATH,
) -> pd.Series:
    """Blend pre-tournament strengths with in-tournament MLE update."""
    tournament = estimate_tournament_strengths(results=results, results_path=results_path)
    w = float(np.clip(blend, 0.0, 1.0))
    if tournament.abs().sum() == 0:
        return base_strengths

    aligned = tournament.reindex(base_strengths.index).fillna(0.0)
    blended = (1.0 - w) * base_strengths + w * aligned
    std = blended.std()
    if std and not np.isnan(std) and std > 0:
        blended = (blended - blended.mean()) / std
    return blended