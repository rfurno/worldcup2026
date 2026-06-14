"""Pre-match lineup confidence multipliers from supplements."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import DATA_DIR
from .tournament_data import all_teams

LINEUP_SUPPLEMENT_PATH = DATA_DIR / "lineup_signals.csv"


def load_lineup_signals(path: Path | str = LINEUP_SUPPLEMENT_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(
            columns=["date", "match_num", "team", "lineup_strength", "notes", "source"]
        )
    return pd.read_csv(path)


def lineup_multipliers_for_match(
    home: str,
    away: str,
    match_date: str | None = None,
    match_num: int | None = None,
    signals: pd.DataFrame | None = None,
) -> tuple[float, float]:
    """
    Return (home_mult, away_mult) in ~[0.97, 1.03] from confirmed lineups.

    Default 1.0 when no signal exists.
    """
    df = signals if signals is not None else load_lineup_signals()
    if df.empty:
        return 1.0, 1.0

    subset = df.copy()
    if match_date:
        subset = subset[subset["date"].astype(str) == str(match_date)]
    if match_num is not None and "match_num" in subset.columns:
        num_mask = subset["match_num"].astype("Int64") == int(match_num)
        if num_mask.any():
            subset = subset[num_mask]

    def _mult(team: str) -> float:
        rows = subset[subset["team"] == team]
        if rows.empty:
            return 1.0
        strength = float(rows.iloc[-1]["lineup_strength"])
        return float(1.0 + 0.03 * strength)

    return _mult(home), _mult(away)


def all_teams_default() -> pd.DataFrame:
    return pd.DataFrame({"team": all_teams(), "lineup_strength": 0.0})