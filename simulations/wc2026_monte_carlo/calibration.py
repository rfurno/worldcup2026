"""Calibrate team strengths toward betting-market winner probabilities."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data_loaders import normalize_signal


def normalize_market_probabilities(market_probs: pd.Series) -> pd.Series:
    """Remove overround so probabilities sum to 1."""
    probs = market_probs.clip(lower=1e-6)
    return probs / probs.sum()


def market_log_strength(market_probs: pd.Series) -> pd.Series:
    """
    Map market win probabilities to a strength scale.

    Uses log-odds relative to the field median so favourites separate cleanly
    without extreme compression.
    """
    normed = normalize_market_probabilities(market_probs)
    median_p = float(normed.median())
    log_odds = np.log(normed / (1.0 - normed))
    median_log_odds = np.log(median_p / (1.0 - median_p))
    return pd.Series(log_odds - median_log_odds, index=normed.index)


def blend_with_market_anchor(
    statistical: pd.Series,
    market_probs: pd.Series,
    calibration_blend: float = 0.75,
    injury_multiplier: pd.Series | None = None,
    injury_market_discount: float = 0.35,
) -> pd.Series:
    """
    Blend statistical signals with a market anchor.

    injury_market_discount: fraction of injury penalty applied (books already
    price most injury news into winner odds).
    """
    anchor = market_log_strength(market_probs)
    anchor = normalize_signal(anchor)
    stat = normalize_signal(statistical)

    blended = calibration_blend * anchor + (1.0 - calibration_blend) * stat

    if injury_multiplier is not None:
        penalty = injury_multiplier.clip(0.65, 1.0)
        soft_injury = 1.0 - injury_market_discount * (1.0 - penalty)
        blended = blended * soft_injury

    return blended


def fill_missing_market_probs(
    teams: list[str],
    market_probs: pd.Series,
    elo: pd.Series,
) -> pd.Series:
    """Assign low tail probabilities to teams without quoted winner odds."""
    filled = market_probs.reindex(teams).copy()
    quoted = filled.dropna()
    quoted_mass = float(quoted.sum()) if not quoted.empty else 0.85
    tail_mass = max(0.01, 1.0 - quoted_mass)

    missing = filled[filled.isna()].index.tolist()
    if not missing:
        return normalize_market_probabilities(filled)

    elo_missing = elo.reindex(missing).fillna(elo.median())
    elo_weights = np.exp((elo_missing - elo_missing.min()) / 200.0)
    elo_weights = elo_weights / elo_weights.sum() * tail_mass
    for team, p in elo_weights.items():
        filled[team] = float(p)

    for team in quoted.index:
        filled[team] = quoted[team]

    return normalize_market_probabilities(filled)


def iterative_strength_adjustment(
    strengths: pd.Series,
    target_probs: pd.Series,
    simulate_fn,
    n_iterations: int = 6,
    n_sims_per_iter: int = 2500,
    learning_rate: float = 0.70,
    seed: int = 42,
) -> pd.Series:
    """
    Tune strengths so tournament win rates approach market targets.

    simulate_fn(rng) -> winner team name
    """
    adjusted = strengths.copy()
    target = normalize_market_probabilities(target_probs.reindex(strengths.index))
    rng = np.random.default_rng(seed)

    for _ in range(n_iterations):
        counts = {team: 0 for team in strengths.index}
        for _ in range(n_sims_per_iter):
            winner = simulate_fn(rng, adjusted)
            counts[winner] += 1

        observed = pd.Series(
            {team: counts[team] / n_sims_per_iter for team in strengths.index}
        )
        ratio = (target / observed.clip(lower=1e-5)).clip(0.5, 2.0)
        delta = learning_rate * np.log(ratio)
        adjusted = adjusted + delta
        adjusted = normalize_signal(adjusted)

    return adjusted