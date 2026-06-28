"""Single-match predictions using the Dixon-Coles model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import SimulationConfig
from .external_sims_loader import lookup_external_sim
from .lineup_signals import lineup_multipliers_for_match
from .match_odds_loader import blend_match_probabilities, lookup_match_odds
from .model_factory import build_calibrated_models

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
    pick_method: str = "max_outcome"


def _confidence_label(home_p: float, draw_p: float, away_p: float) -> str:
    top = max(home_p, draw_p, away_p)
    if top >= 0.70:
        return "High"
    if top >= 0.55:
        return "Moderate"
    return "Low"


def _pick_winner(
    home: str,
    away: str,
    home_win: float,
    draw: float,
    away_win: float,
    most_likely_score: str,
    config: SimulationConfig,
) -> tuple[str, str]:
    """Draw-aware winner selection."""
    top = max(home_win, draw, away_win)
    margin = config.draw_pick_margin
    modal = most_likely_score.strip()

    if draw >= top - margin and draw >= config.draw_modal_min_prob:
        return "Draw", "draw_within_margin"

    if modal in {"0-0", "1-1", "2-2"} and draw >= config.draw_modal_min_prob:
        if draw >= top - 0.05:
            return "Draw", "modal_draw"

    if home_win >= away_win and home_win >= draw:
        return home, "max_outcome"
    if away_win >= home_win and away_win >= draw:
        return away, "max_outcome"
    return "Draw", "max_outcome"


def _apply_md1_draw_bump(
    home_win: float,
    draw: float,
    away_win: float,
    factor: float,
) -> tuple[float, float, float]:
    draw_adj = draw * factor
    total = home_win + draw_adj + away_win
    if total <= 0:
        return home_win, draw, away_win
    scale = (home_win + draw + away_win) / total
    return home_win * scale, draw_adj * scale, away_win * scale


class MatchPredictor:
    def __init__(
        self,
        config: SimulationConfig | None = None,
        *,
        results_before_date: str | None = None,
        tournament_form_blend_override: float | None = None,
        use_model_cache: bool = True,
    ):
        self.config = config or SimulationConfig(verbose=False)
        self.results_before_date = results_before_date
        _, self.model, _ = build_calibrated_models(
            self.config,
            results_before_date=results_before_date,
            tournament_form_blend_override=tournament_form_blend_override,
            use_cache=use_model_cache,
        )

    def predict(
        self,
        home: str,
        away: str,
        venue: str | None = None,
        n_samples: int = 50_000,
        seed: int = 42,
        neutral: bool = False,
        match_date: str | None = None,
        match_num: int | None = None,
        matchday: int = 1,
        knockout: bool = False,
    ) -> MatchPrediction:
        saved_ha = self.config.home_advantage
        if neutral:
            self.config.home_advantage = NEUTRAL_HOME_ADVANTAGE

        try:
            home_mult, away_mult = (1.0, 1.0)
            if self.config.use_lineup_signals:
                home_mult, away_mult = lineup_multipliers_for_match(
                    home, away, match_date=match_date, match_num=match_num
                )

            lam_h, lam_a = self.model.expected_rates(home, away, venue)
            lam_h *= home_mult
            lam_a *= away_mult

            matrix = self.model.score_matrix(lam_h, lam_a, max_goals=8)
            home_win = float(np.tril(matrix, -1).sum())
            draw = float(np.trace(matrix).sum())
            away_win = float(np.triu(matrix, 1).sum())

            if self.config.use_md1_draw_bump and matchday == 1 and not knockout:
                home_win, draw, away_win = _apply_md1_draw_bump(
                    home_win, draw, away_win, self.config.md1_draw_factor
                )

            model_probs = (home_win, draw, away_win)

            if self.config.use_match_odds:
                market = lookup_match_odds(
                    home, away, match_date=match_date, match_num=match_num
                )
                if market is not None:
                    odds_blend = self.config.match_odds_blend
                    if match_num is not None and int(match_num) >= 73:
                        odds_blend = self.config.knockout_match_odds_blend
                    model_probs = blend_match_probabilities(
                        model_probs, market, odds_blend
                    )

            if self.config.use_external_ensemble:
                external = lookup_external_sim(
                    home, away, match_date=match_date, match_num=match_num
                )
                if external is not None:
                    model_probs = blend_match_probabilities(
                        model_probs, external, self.config.ensemble_external_weight
                    )

            home_win, draw, away_win = model_probs

            rng = np.random.default_rng(seed)
            scores: dict[str, int] = {}
            for _ in range(n_samples):
                hg, ag = self.model.simulate_scoreline(home, away, rng, venue)
                key = f"{hg}-{ag}"
                scores[key] = scores.get(key, 0) + 1

            top_scores = sorted(scores.items(), key=lambda x: -x[1])[:5]
            most_likely = [(s, c / n_samples) for s, c in top_scores]
            modal_score = most_likely[0][0] if most_likely else "1-1"

            winner, pick_method = _pick_winner(
                home, away, home_win, draw, away_win, modal_score, self.config
            )

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
                pick_method=pick_method,
            )
        finally:
            self.config.home_advantage = saved_ha