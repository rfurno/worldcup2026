"""External match simulation probabilities for light ensemble blending."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import DATA_DIR
from .match_odds_loader import normalize_match_odds_row

DEFAULT_EXTERNAL_SIMS_PATH = DATA_DIR / "external_match_sims.csv"

EXTERNAL_SIM_COLUMNS = [
    "date",
    "match_num",
    "home",
    "away",
    "p_home",
    "p_draw",
    "p_away",
    "source",
]


def load_external_sims(path: Path | str = DEFAULT_EXTERNAL_SIMS_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=EXTERNAL_SIM_COLUMNS)
    df = pd.read_csv(path)
    for col in EXTERNAL_SIM_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[EXTERNAL_SIM_COLUMNS].copy()


def lookup_external_sim(
    home: str,
    away: str,
    match_date: str | None = None,
    match_num: int | None = None,
    sims_df: pd.DataFrame | None = None,
) -> tuple[float, float, float] | None:
    df = sims_df if sims_df is not None else load_external_sims()
    if df.empty:
        return None

    subset = df.copy()
    if match_date:
        subset = subset[subset["date"].astype(str) == str(match_date)]
    if match_num is not None and "match_num" in subset.columns:
        num_mask = subset["match_num"].astype("Int64") == int(match_num)
        if num_mask.any():
            subset = subset[num_mask]

    exact = subset[(subset["home"] == home) & (subset["away"] == away)]
    if exact.empty:
        return None

    row = exact.iloc[-1]
    return normalize_match_odds_row(
        float(row["p_home"]), float(row["p_draw"]), float(row["p_away"])
    )