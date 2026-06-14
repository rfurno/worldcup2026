"""Build calibrated Dixon-Coles model components."""

from __future__ import annotations

from .config import SimulationConfig
from .dixon_coles import DixonColesModel
from .monte_carlo import MonteCarloEngine
from .team_strength import TeamStrengthModel
from .tournament_form import blend_tournament_form
from .tournament_simulator import TournamentSimulator

_MODEL_CACHE: dict[tuple, tuple[TeamStrengthModel, DixonColesModel, TournamentSimulator]] = {}


def clear_model_cache() -> None:
    """Invalidate cached models (call after results or events change)."""
    _MODEL_CACHE.clear()


def _cache_key(cfg: SimulationConfig, refresh_external: bool) -> tuple:
    return (
        refresh_external,
        cfg.random_seed,
        cfg.market_calibration_blend,
        cfg.tournament_form_blend,
        cfg.dixon_coles_rho,
        cfg.rho_floor,
        cfg.use_tournament_form,
        cfg.use_intl_xg,
        cfg.intl_xg_blend,
    )


def build_calibrated_models(
    config: SimulationConfig | None = None,
    refresh_external: bool = False,
    *,
    use_cache: bool = True,
) -> tuple[TeamStrengthModel, DixonColesModel, TournamentSimulator]:
    """Return strength model, match model, and simulator calibrated to market odds."""
    cfg = config or SimulationConfig(verbose=False)
    key = _cache_key(cfg, refresh_external)
    if use_cache and key in _MODEL_CACHE:
        return _MODEL_CACHE[key]

    engine = MonteCarloEngine(cfg, refresh_external=refresh_external)
    if cfg.use_tournament_form:
        blended = blend_tournament_form(
            engine.strength_model._strengths,
            blend=cfg.tournament_form_blend,
        )
        engine.strength_model.set_strengths(blended)
    result = (engine.strength_model, engine.model, engine.simulator)
    if use_cache:
        _MODEL_CACHE[key] = result
    return result