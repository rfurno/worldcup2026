"""Dixon-Coles parameter estimation from historical internationals (#3, #8)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def time_decay_weights(dates: pd.Series, xi: float, reference: pd.Timestamp) -> np.ndarray:
    days = (reference - dates).dt.days.clip(lower=0)
    return np.exp(-xi * days.to_numpy(dtype=float))


def calibrate_goal_baselines(
    historical: pd.DataFrame,
    xi: float = 0.003,
    max_rows: int = 8000,
) -> tuple[float, float]:
    """Weighted mean home/away goals with Dixon-Coles time decay."""
    if historical is None or historical.empty:
        return 1.35, 1.05

    df = historical.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "home_score", "away_score"])
    df = df[(df["home_score"] >= 0) & (df["away_score"] >= 0)]
    df = df.sort_values("date").tail(max_rows)
    if df.empty:
        return 1.35, 1.05

    ref = df["date"].max()
    weights = time_decay_weights(df["date"], xi, ref)
    wsum = weights.sum()
    if wsum <= 0:
        return 1.35, 1.05

    home_rate = float(np.average(df["home_score"], weights=weights))
    away_rate = float(np.average(df["away_score"], weights=weights))
    return home_rate, away_rate


def estimate_rho(
    historical: pd.DataFrame,
    xi: float = 0.003,
    max_rows: int = 8000,
    default: float = -0.13,
) -> float:
    """
    Rough rho estimate from low-score frequency vs independent Poisson (#8).

    Negative rho increases draw mass at 0-0 / 1-1.
    """
    if historical is None or historical.empty:
        return default

    df = historical.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "home_score", "away_score"])
    df = df[(df["home_score"] >= 0) & (df["away_score"] >= 0)]
    df = df.sort_values("date").tail(max_rows)
    if len(df) < 100:
        return default

    ref = df["date"].max()
    weights = time_decay_weights(df["date"], xi, ref)
    lam_h, lam_a = calibrate_goal_baselines(df, xi=xi, max_rows=max_rows)

    from scipy.stats import poisson

    wsum = float(weights.sum())
    if wsum <= 0:
        return default

    low_mask = (df["home_score"] <= 1) & (df["away_score"] <= 1)
    if not low_mask.any():
        return default

    low_rate = float(weights[low_mask.to_numpy()].sum() / wsum)
    indep = 0.0
    for hg in range(2):
        for ag in range(2):
            indep += poisson.pmf(hg, lam_h) * poisson.pmf(ag, lam_a)
    if indep <= 0:
        return default

    ratio = low_rate / indep
    rho = float(np.clip((1.0 - ratio) * 0.25, -0.25, 0.05))
    return rho