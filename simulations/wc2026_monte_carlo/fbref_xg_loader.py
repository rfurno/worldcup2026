"""International / tournament xG signals (FBref-style CSV)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import DATA_DIR
from .tournament_data import all_teams

DEFAULT_FBREF_INTL_XG_PATH = DATA_DIR / "fbref_intl_xg.csv"

FBREF_COLUMNS = ["team", "xg_for_per_match", "xg_against_per_match", "matches", "source"]


def load_fbref_intl_xg(path: Path | str = DEFAULT_FBREF_INTL_XG_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=FBREF_COLUMNS)
    df = pd.read_csv(path)
    for col in FBREF_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[FBREF_COLUMNS].copy()


def build_intl_xg_features(
    path: Path | str = DEFAULT_FBREF_INTL_XG_PATH,
) -> pd.DataFrame:
    """
    Team-level xG differential from international results.

    Falls back to zero diff when no row exists.
    """
    teams = pd.DataFrame({"team": all_teams()})
    fbref = load_fbref_intl_xg(path)
    if fbref.empty:
        teams["intl_xg_diff_per_match"] = 0.0
        return teams

    fbref = fbref.copy()
    fbref["intl_xg_diff_per_match"] = (
        fbref["xg_for_per_match"].astype(float) - fbref["xg_against_per_match"].astype(float)
    )
    merged = teams.merge(
        fbref[["team", "intl_xg_diff_per_match"]], on="team", how="left"
    )
    merged["intl_xg_diff_per_match"] = merged["intl_xg_diff_per_match"].fillna(0.0)
    return merged