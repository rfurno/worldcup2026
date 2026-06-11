"""Configuration defaults for the World Cup 2026 Monte Carlo simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SIMULATIONS_DIR = REPO_ROOT / "simulations"
DATA_DIR = SIMULATIONS_DIR / "data"
OUTPUT_DIR = SIMULATIONS_DIR / "output"

# Internal markdown sources (additional-data-sources.md #7, #5)
INJURY_TRACKER_PATH = REPO_ROOT / "injury_tracker.md"
PLAYER_TRACKER_PATH = REPO_ROOT / "player_tracker.md"
WINNER_ODDS_PATH = REPO_ROOT / "winner_odds_table.md"
BETTING_ODDS_PATH = REPO_ROOT / "betting_sites_odds.md"
OPENING_FIXTURES_PATH = REPO_ROOT / "opening_fixtures_predictions.md"
ADDITIONAL_SOURCES_PATH = REPO_ROOT / "additional-data-sources.md"

# External CSV fallbacks (additional-data-sources.md #1-#4)
DEFAULT_ELO_PATH = DATA_DIR / "elo_ratings.csv"
DEFAULT_SQUAD_VALUES_PATH = DATA_DIR / "squad_values.csv"
DEFAULT_XG_FORM_PATH = DATA_DIR / "xg_form.csv"
DEFAULT_HISTORICAL_MATCHES_PATH = DATA_DIR / "historical_matches.csv"

# Elo fetch URL (additional-data-sources.md #1)
ELO_RATINGS_URL = "http://www.eloratings.net/world.csv"

# Kaggle historical results (additional-data-sources.md #3)
KAGGLE_RESULTS_URL = (
    "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
)


@dataclass
class BlendWeights:
    """Weights for combining strength signals (additional-data-sources.md integration)."""

    elo: float = 0.40
    market: float = 0.25
    squad_value: float = 0.15
    xg_form: float = 0.10
    player_tracker: float = 0.10


@dataclass
class SimulationConfig:
    """Runtime configuration for a Monte Carlo run."""

    n_simulations: int = 10_000
    random_seed: int = 42
    blend_weights: BlendWeights = field(default_factory=BlendWeights)
    home_advantage: float = 0.22
    travel_fatigue_per_1000km: float = 0.02
    host_bonus: float = 0.15
    extra_time_goal_factor: float = 0.85
    penalty_strength_weight: float = 0.6
    dixon_coles_rho: float = -0.13
    dixon_coles_xi: float = 0.003
    output_dir: Path = field(default_factory=lambda: OUTPUT_DIR)
    save_plot: bool = True
    verbose: bool = True