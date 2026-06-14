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
PLAYER_TRACKER_KEY_PATH = REPO_ROOT / "player_tracker_key.md"
WINNER_ODDS_PATH = REPO_ROOT / "winner_odds_table.md"
BETTING_ODDS_PATH = REPO_ROOT / "betting_sites_odds.md"
OPENING_FIXTURES_PATH = REPO_ROOT / "opening_fixtures_predictions.md"
ADDITIONAL_SOURCES_PATH = REPO_ROOT / "additional-data-sources.md"

# External CSV fallbacks (additional-data-sources.md #1-#4)
DEFAULT_ELO_PATH = DATA_DIR / "elo_ratings.csv"
DEFAULT_SQUAD_VALUES_PATH = DATA_DIR / "squad_values.csv"
DEFAULT_XG_FORM_PATH = DATA_DIR / "xg_form.csv"
DEFAULT_SQUAD_CLUBS_PATH = DATA_DIR / "squad_clubs.csv"
DEFAULT_HISTORICAL_MATCHES_PATH = DATA_DIR / "historical_matches.csv"
DEFAULT_MATCH_RESULTS_PATH = DATA_DIR / "match_results.csv"
DEFAULT_MATCH_PREDICTIONS_LOG_PATH = DATA_DIR / "match_predictions_log.csv"
DEFAULT_PREDICTION_SNAPSHOTS_PATH = DATA_DIR / "prediction_snapshots.csv"
DEFAULT_PREDICTION_EVOLUTION_PATH = DATA_DIR / "prediction_evolution.csv"
DEFAULT_WINNER_RUNNER_UP_LOG_PATH = DATA_DIR / "winner_runner_up_log.csv"
DEFAULT_MATCH_EVENTS_PATH = DATA_DIR / "match_events.csv"
DEFAULT_MATCH_ODDS_PATH = DATA_DIR / "match_odds.csv"
DEFAULT_FBREF_INTL_XG_PATH = DATA_DIR / "fbref_intl_xg.csv"
DEFAULT_EXTERNAL_SIMS_PATH = DATA_DIR / "external_match_sims.csv"
DEFAULT_LINEUP_SIGNALS_PATH = DATA_DIR / "lineup_signals.csv"
MATCH_RESULTS_MD_PATH = REPO_ROOT / "match-results.md"
MATCH_PREDICTIONS_MD_PATH = REPO_ROOT / "match_predictions.md"
MATCH_EVENTS_TRACKER_PATH = REPO_ROOT / "match_events_tracker.md"

# Elo fetch URL (additional-data-sources.md #1)
ELO_RATINGS_URL = "http://www.eloratings.net/world.csv"

# Kaggle historical results (additional-data-sources.md #3)
KAGGLE_RESULTS_URL = (
    "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
)


@dataclass
class BlendWeights:
    """Weights for statistical signals (market handled via calibration anchor)."""

    elo: float = 0.35
    market: float = 0.0
    squad_value: float = 0.20
    xg_form: float = 0.12
    recent_form: float = 0.13
    player_tracker: float = 0.10
    club_chemistry: float = 0.10


@dataclass
class SimulationConfig:
    """Runtime configuration for a Monte Carlo run."""

    n_simulations: int = 10_000
    random_seed: int = 42
    blend_weights: BlendWeights = field(default_factory=BlendWeights)
    calibrate_to_market: bool = True
    market_calibration_blend: float = 0.90
    injury_market_discount: float = 0.40
    iterative_market_calibration: bool = True
    calibration_iterations: int = 5
    calibration_sims_per_iter: int = 2000
    strength_temperature: float = 0.42
    home_advantage: float = 0.22
    travel_fatigue_per_1000km: float = 0.02
    host_bonus: float = 0.15
    extra_time_goal_factor: float = 0.85
    penalty_strength_weight: float = 0.6
    dixon_coles_rho: float = -0.20
    dixon_coles_xi: float = 0.003
    use_h2h_adjustment: bool = True
    h2h_scale: float = 0.06
    estimate_rho_from_history: bool = True
    rho_floor: float = -0.25
    match_odds_blend: float = 0.35
    tournament_form_blend: float = 0.30
    intl_xg_blend: float = 0.40
    md1_draw_factor: float = 1.08
    ensemble_external_weight: float = 0.12
    draw_pick_margin: float = 0.03
    draw_modal_min_prob: float = 0.22
    use_match_odds: bool = True
    use_tournament_form: bool = True
    use_intl_xg: bool = True
    use_md1_draw_bump: bool = True
    use_lineup_signals: bool = True
    use_external_ensemble: bool = True
    output_dir: Path = field(default_factory=lambda: OUTPUT_DIR)
    save_plot: bool = True
    verbose: bool = True