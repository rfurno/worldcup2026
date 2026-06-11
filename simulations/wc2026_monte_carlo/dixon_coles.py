"""Dixon-Coles bivariate Poisson match model (#8)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import poisson

from .config import SimulationConfig
from .form_and_h2h import h2h_log_shift
from .historical_calibration import calibrate_goal_baselines, estimate_rho
from .team_strength import TeamStrengthModel


@dataclass
class MatchOutcome:
    home_goals: int
    away_goals: int
    went_to_extra_time: bool = False
    went_to_penalties: bool = False
    penalty_winner: str | None = None


class DixonColesModel:
    """
    Dixon & Coles (1997) adjustment for low-score correlation.

    Calibrated on time-decayed international results (#3, #8).
    """

    def __init__(
        self,
        strength_model: TeamStrengthModel,
        config: SimulationConfig,
        historical_matches: pd.DataFrame | None = None,
    ):
        self.strength_model = strength_model
        self.config = config
        self.xi = config.dixon_coles_xi
        self.historical_matches = historical_matches
        self.base_home_rate, self.base_away_rate = calibrate_goal_baselines(
            historical_matches, xi=self.xi
        )
        if config.estimate_rho_from_history:
            self.rho = estimate_rho(
                historical_matches, xi=self.xi, default=config.dixon_coles_rho
            )
        else:
            self.rho = config.dixon_coles_rho

    def expected_rates(
        self,
        home: str,
        away: str,
        venue: str | None = None,
        rate_factor: float = 1.0,
    ) -> tuple[float, float]:
        sm = self.strength_model
        home_shift, away_shift = sm.venue_adjustment(home, away, venue)

        if self.config.use_h2h_adjustment and self.historical_matches is not None:
            h2h_h, h2h_a = h2h_log_shift(
                self.historical_matches,
                home,
                away,
                xi=self.xi,
                scale=self.config.h2h_scale,
            )
            home_shift += h2h_h
            away_shift += h2h_a

        home_attack = sm.get_attack(home)
        away_attack = sm.get_attack(away)
        home_defense = sm.get_defense(home)
        away_defense = sm.get_defense(away)

        lam_home = (
            self.base_home_rate
            * home_attack
            * away_defense
            * math.exp(home_shift)
            * rate_factor
        )
        lam_away = (
            self.base_away_rate
            * away_attack
            * home_defense
            * math.exp(away_shift)
            * rate_factor
        )
        return max(lam_home, 0.05), max(lam_away, 0.05)

    def _tau(self, x: int, y: int, lam_h: float, lam_a: float, rho: float) -> float:
        if x == 0 and y == 0:
            return 1.0 - lam_h * lam_a * rho
        if x == 0 and y == 1:
            return 1.0 + lam_h * rho
        if x == 1 and y == 0:
            return 1.0 + lam_a * rho
        if x == 1 and y == 1:
            return 1.0 - rho
        return 1.0

    def score_matrix(
        self, lam_home: float, lam_away: float, max_goals: int = 8
    ) -> np.ndarray:
        probs = np.zeros((max_goals + 1, max_goals + 1))
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                base = poisson.pmf(i, lam_home) * poisson.pmf(j, lam_away)
                probs[i, j] = base * self._tau(i, j, lam_home, lam_away, self.rho)
        probs = np.clip(probs, 0.0, None)
        total = probs.sum()
        if total <= 0:
            probs[0, 0] = 1.0
            return probs
        return probs / total

    def simulate_scoreline(
        self,
        home: str,
        away: str,
        rng: np.random.Generator,
        venue: str | None = None,
        rate_factor: float = 1.0,
    ) -> tuple[int, int]:
        lam_h, lam_a = self.expected_rates(home, away, venue, rate_factor)
        home_goals = int(rng.poisson(lam_h))
        away_goals = int(rng.poisson(lam_a))

        if home_goals <= 1 and away_goals <= 1:
            tau = self._tau(home_goals, away_goals, lam_h, lam_a, self.rho)
            if tau < 1.0 and rng.random() > max(tau, 0.0):
                home_goals = int(rng.poisson(lam_h))
                away_goals = int(rng.poisson(lam_a))

        return home_goals, away_goals

    def simulate_knockout_match(
        self,
        team_a: str,
        team_b: str,
        rng: np.random.Generator,
        neutral: bool = True,
    ) -> MatchOutcome:
        """90 minutes, extra time, then penalties if needed."""
        venue = None if neutral else TEAM_HOME_VENUES.get(team_a)
        hg, ag = self.simulate_scoreline(team_a, team_b, rng, venue=venue)

        if hg != ag:
            return MatchOutcome(hg, ag)

        et_factor = self.config.extra_time_goal_factor
        hg_et, ag_et = self.simulate_scoreline(
            team_a, team_b, rng, venue=venue, rate_factor=et_factor
        )
        total_home = hg + hg_et
        total_away = ag + ag_et
        if total_home != total_away:
            return MatchOutcome(
                total_home, total_away, went_to_extra_time=True
            )

        p_a = self.strength_model.penalty_skill(team_a)
        p_b = self.strength_model.penalty_skill(team_b)
        p_a = (
            self.config.penalty_strength_weight * p_a
            + (1 - self.config.penalty_strength_weight) * 0.5
        )
        winner = team_a if rng.random() < p_a / (p_a + p_b) else team_b
        return MatchOutcome(
            total_home,
            total_away,
            went_to_extra_time=True,
            went_to_penalties=True,
            penalty_winner=winner,
        )


from .tournament_data import TEAM_HOME_VENUES  # noqa: E402