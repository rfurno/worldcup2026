"""World Cup 2026 Monte Carlo simulation package."""

from .config import SimulationConfig
from .monte_carlo import MonteCarloEngine, SimulationSummary

__all__ = ["SimulationConfig", "MonteCarloEngine", "SimulationSummary"]
__version__ = "1.0.0"