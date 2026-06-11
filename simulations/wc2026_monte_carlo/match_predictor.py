"""Single-match predictions using the Dixon-Coles model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import SimulationConfig
from .data_loaders import build_team_features, fetch_historical_matches
from .dixon_coles import DixonColesModel
from .team_strength import TeamStrengthModel

NEUTRAL_HOME_ADVANTAGE = 0.08


@dataclass
class MatchPrediction:
    home: str
    away: str
    venue: str | None
    expected_home_goals: float
    expected_away_goals: float
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    predicted_winner: str
    most_likely_scorelines: list[tuple[str, float]]
    confidence: str


def _confidence_label(home_p: float, draw_p: float, away_p: float) -> str:
    top = max(home_p, draw_p, away_p)
    if top >= 0.70:
        return "High"
    if top >= 0.55:
        return "Moderate"
    return "Low"


class MatchPredictor:
    def __init__(self, config: SimulationConfig | None = None):
        self.config = config or SimulationConfig()
        features = build_team_features()
        strength = TeamStrengthModel(self.config, features=features)
        historical = fetch_historical_matches()
        self.model = DixonColesModel(strength, self.config, historical_matches=historical)

    def predict(
        self,
        home: str,
        away: str,
        venue: str | None = None,
        n_samples: int = 50_000,
        seed: int = 42,
        neutral: bool = False,
    ) -> MatchPrediction:
        saved_ha = self.config.home_advantage
        if neutral:
            self.config.home_advantage = NEUTRAL_HOME_ADVANTAGE

        try:
            lam_h, lam_a = self.model.expected_rates(home, away, venue)
            matrix = self.model.score_matrix(lam_h, lam_a, max_goals=8)
            home_win = float(np.tril(matrix, -1).sum())
            draw = float(np.trace(matrix).sum())
            away_win = float(np.triu(matrix, 1).sum())

            rng = np.random.default_rng(seed)
            scores: dict[str, int] = {}
            for _ in range(n_samples):
                hg, ag = self.model.simulate_scoreline(home, away, rng, venue)
                key = f"{hg}-{ag}"
                scores[key] = scores.get(key, 0) + 1

            top_scores = sorted(scores.items(), key=lambda x: -x[1])[:5]
            most_likely = [(s, c / n_samples) for s, c in top_scores]

            if home_win >= away_win and home_win >= draw:
                winner = home
            elif away_win >= home_win and away_win >= draw:
                winner = away
            else:
                winner = "Draw"

            return MatchPrediction(
                home=home,
                away=away,
                venue=venue,
                expected_home_goals=lam_h,
                expected_away_goals=lam_a,
                home_win_prob=home_win,
                draw_prob=draw,
                away_win_prob=away_win,
                predicted_winner=winner,
                most_likely_scorelines=most_likely,
                confidence=_confidence_label(home_win, draw, away_win),
            )
        finally:
            self.config.home_advantage = saved_ha