"""Per-match 1X2 odds loader and normalization."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import DATA_DIR

DEFAULT_MATCH_ODDS_PATH = DATA_DIR / "match_odds.csv"

MATCH_ODDS_COLUMNS = [
    "date",
    "match_num",
    "home",
    "away",
    "p_home",
    "p_draw",
    "p_away",
    "source",
]


def load_match_odds(path: Path | str = DEFAULT_MATCH_ODDS_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=MATCH_ODDS_COLUMNS)
    df = pd.read_csv(path)
    for col in MATCH_ODDS_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[MATCH_ODDS_COLUMNS].copy()


def normalize_match_odds_row(p_home: float, p_draw: float, p_away: float) -> tuple[float, float, float]:
    probs = np.array([max(p_home, 1e-6), max(p_draw, 1e-6), max(p_away, 1e-6)], dtype=float)
    probs /= probs.sum()
    return float(probs[0]), float(probs[1]), float(probs[2])


def lookup_match_odds(
    home: str,
    away: str,
    match_date: str | None = None,
    match_num: int | None = None,
    odds_df: pd.DataFrame | None = None,
) -> tuple[float, float, float] | None:
    """Return normalized (p_home, p_draw, p_away) for a fixture, or None."""
    df = odds_df if odds_df is not None else load_match_odds()
    if df.empty:
        return None

    subset = df.copy()
    if match_date is not None:
        subset = subset[subset["date"].astype(str) == str(match_date)]
    if match_num is not None and "match_num" in subset.columns:
        num_mask = subset["match_num"].astype("Int64") == int(match_num)
        if num_mask.any():
            subset = subset[num_mask]

    exact = subset[(subset["home"] == home) & (subset["away"] == away)]
    if exact.empty:
        exact = subset[(subset["home"] == away) & (subset["away"] == home)]
        if not exact.empty:
            row = exact.iloc[-1]
            p_h, p_d, p_a = normalize_match_odds_row(
                float(row["p_away"]), float(row["p_draw"]), float(row["p_home"])
            )
            return p_h, p_d, p_a

    if exact.empty:
        return None

    row = exact.iloc[-1]
    return normalize_match_odds_row(
        float(row["p_home"]), float(row["p_draw"]), float(row["p_away"])
    )


def blend_match_probabilities(
    model: tuple[float, float, float],
    market: tuple[float, float, float],
    blend: float,
) -> tuple[float, float, float]:
    """Convex blend of model and market 1X2 probabilities."""
    w = float(np.clip(blend, 0.0, 1.0))
    blended = tuple((1.0 - w) * m + w * k for m, k in zip(model, market, strict=True))
    total = sum(blended)
    if total <= 0:
        return model
    return tuple(p / total for p in blended)