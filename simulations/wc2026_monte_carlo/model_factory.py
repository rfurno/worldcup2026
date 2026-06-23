"""Build calibrated Dixon-Coles model components."""

from __future__ import annotations

import pandas as pd

from .config import SimulationConfig
from .dixon_coles import DixonColesModel
from .group_results import load_completed_group_matches
from .monte_carlo import MonteCarloEngine
from .team_strength import TeamStrengthModel
from .tournament_form import blend_tournament_form, resolve_tournament_form_blend
from .tournament_simulator import TournamentSimulator

_MODEL_CACHE: dict[tuple, tuple[TeamStrengthModel, DixonColesModel, TournamentSimulator]] = {}


def clear_model_cache() -> None:
    """Invalidate cached models (call after results or events change)."""
    _MODEL_CACHE.clear()


def _results_before(
    before_date: str | None,
) -> pd.DataFrame | None:
    if before_date is None:
        return None
    df = load_completed_group_matches()
    if df.empty:
        return df
    return df[df["date"].astype(str) < before_date].copy()


def _cache_key(
    cfg: SimulationConfig,
    refresh_external: bool,
    results_before_date: str | None,
    tournament_form_blend_override: float | None,
    results_subset: pd.DataFrame | None,
) -> tuple:
    matches_n = 0 if results_subset is None or results_subset.empty else len(results_subset)
    blend = resolve_tournament_form_blend(
        cfg,
        results=results_subset,
        override=tournament_form_blend_override,
    )
    return (
        refresh_external,
        cfg.random_seed,
        cfg.market_calibration_blend,
        cfg.use_dynamic_tournament_form_blend,
        cfg.tournament_form_blend,
        cfg.tournament_form_blend_base,
        cfg.tournament_form_blend_per_match,
        cfg.tournament_form_blend_cap,
        cfg.use_wc_recent_form,
        cfg.dixon_coles_rho,
        cfg.rho_floor,
        cfg.use_tournament_form,
        cfg.use_intl_xg,
        cfg.intl_xg_blend,
        results_before_date,
        tournament_form_blend_override,
        matches_n,
        round(blend, 4),
    )


def build_calibrated_models(
    config: SimulationConfig | None = None,
    refresh_external: bool = False,
    *,
    use_cache: bool = True,
    results_before_date: str | None = None,
    tournament_form_blend_override: float | None = None,
) -> tuple[TeamStrengthModel, DixonColesModel, TournamentSimulator]:
    """Return strength model, match model, and simulator calibrated to market odds."""
    cfg = config or SimulationConfig(verbose=False)
    results_subset = _results_before(results_before_date)
    key = _cache_key(
        cfg,
        refresh_external,
        results_before_date,
        tournament_form_blend_override,
        results_subset,
    )
    if use_cache and key in _MODEL_CACHE:
        return _MODEL_CACHE[key]

    engine = MonteCarloEngine(
        cfg,
        refresh_external=refresh_external,
        results_before_date=results_before_date,
    )
    if cfg.use_tournament_form:
        blend = resolve_tournament_form_blend(
            cfg,
            results=results_subset,
            override=tournament_form_blend_override,
        )
        blended = blend_tournament_form(
            engine.strength_model._strengths,
            blend=blend,
            results=results_subset,
        )
        engine.strength_model.set_strengths(blended)
    result = (engine.strength_model, engine.model, engine.simulator)
    if use_cache:
        _MODEL_CACHE[key] = result
    return result