"""Build calibrated Dixon-Coles model components."""

from __future__ import annotations

import pandas as pd

from .config import SimulationConfig
from .data_loaders import build_team_features, fetch_historical_matches
from .dixon_coles import DixonColesModel
from .monte_carlo import MonteCarloEngine
from .team_strength import TeamStrengthModel
from .tournament_simulator import TournamentSimulator


def build_calibrated_models(
    config: SimulationConfig | None = None,
    refresh_external: bool = False,
) -> tuple[TeamStrengthModel, DixonColesModel, TournamentSimulator]:
    """Return strength model, match model, and simulator calibrated to market odds."""
    cfg = config or SimulationConfig(verbose=False)
    engine = MonteCarloEngine(cfg, refresh_external=refresh_external)
    return engine.strength_model, engine.model, engine.simulator