"""Blend Elo, market, squad value, xG, and injury signals into team strengths."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .calibration import blend_with_market_anchor, fill_missing_market_probs
from .config import BlendWeights, SimulationConfig
from .data_loaders import build_team_features, normalize_signal
from .tournament_data import HOST_NATIONS, TEAM_HOME_VENUES, VENUE_COORDINATES


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return float(2 * r * np.arcsin(np.sqrt(a)))


class TeamStrengthModel:
    """Compute attack/defense parameters for Dixon-Coles simulation."""

    def __init__(
        self,
        config: SimulationConfig,
        features: pd.DataFrame | None = None,
        refresh_external: bool = False,
        strengths: pd.Series | None = None,
    ):
        self.config = config
        self.features = features if features is not None else build_team_features(
            refresh_external=refresh_external,
            config=config,
        )
        self.weights = config.blend_weights
        if strengths is not None:
            self._strengths = strengths
        else:
            self._strengths = self._compute_strengths()
        self._apply_temperature()
        self._attack, self._defense = self._compute_attack_defense()

    def _compute_strengths(self) -> pd.Series:
        df = self.features.set_index("team")
        w = self.weights
        cfg = self.config

        market_probs = fill_missing_market_probs(
            teams=list(df.index),
            market_probs=df["market_prob"],
            elo=df["elo"],
        )
        df = df.copy()
        df["market_prob"] = market_probs

        statistical = (
            w.elo * normalize_signal(df["elo"])
            + w.squad_value * normalize_signal(df["squad_value_meur"])
            + w.xg_form * normalize_signal(df["xg_diff_per_match"])
            + w.recent_form * normalize_signal(df["recent_form"])
            + w.player_tracker * normalize_signal(df["player_tracker_adj"])
            + w.club_chemistry * normalize_signal(df["club_chemistry"])
        )
        if w.market > 0:
            statistical = statistical + w.market * normalize_signal(df["market_prob"])

        if cfg.calibrate_to_market:
            return blend_with_market_anchor(
                statistical=statistical,
                market_probs=df["market_prob"],
                calibration_blend=cfg.market_calibration_blend,
                injury_multiplier=df["injury_multiplier"],
                injury_market_discount=cfg.injury_market_discount,
            )

        composite = statistical * df["injury_multiplier"]
        return composite

    def _apply_temperature(self) -> None:
        """Compress strength spread so tournament outcomes track market tails."""
        temp = self.config.strength_temperature
        if temp != 1.0:
            self._strengths = normalize_signal(self._strengths) * temp

    def set_strengths(self, strengths: pd.Series) -> None:
        self._strengths = strengths
        self._apply_temperature()
        self._attack, self._defense = self._compute_attack_defense()

    def _compute_attack_defense(self) -> tuple[dict[str, float], dict[str, float]]:
        strength = self._strengths
        attack = {}
        defense = {}
        for team in strength.index:
            s = float(strength.loc[team])
            attack[team] = np.exp(0.28 * s)
            defense[team] = np.exp(-0.24 * s)
        return attack, defense

    def get_attack(self, team: str) -> float:
        return self._attack[team]

    def get_defense(self, team: str) -> float:
        return self._defense[team]

    def venue_adjustment(
        self, home: str, away: str, venue: str | None = None
    ) -> tuple[float, float]:
        """
        Home advantage, host bonus, and travel fatigue (#6).
        Returns (home_shift, away_shift) added to log-rate.
        """
        cfg = self.config
        home_shift = cfg.home_advantage
        away_shift = 0.0

        if home in HOST_NATIONS:
            home_shift += cfg.host_bonus

        venue_name = venue or TEAM_HOME_VENUES.get(home)
        if away in HOST_NATIONS and venue_name == TEAM_HOME_VENUES.get(away):
            # Host nation listed as away but playing in their home market
            away_shift += cfg.host_bonus

        if venue_name and venue_name in VENUE_COORDINATES:
            vlat, vlon = VENUE_COORDINATES[venue_name]
            for team, sign in ((away, -1.0),):
                if team in HOST_NATIONS and venue_name == TEAM_HOME_VENUES.get(team):
                    continue
                origin = TEAM_HOME_VENUES.get(team)
                if origin and origin in VENUE_COORDINATES:
                    olat, olon = VENUE_COORDINATES[origin]
                    km = haversine_km(olat, olon, vlat, vlon)
                    fatigue = cfg.travel_fatigue_per_1000km * (km / 1000.0)
                    if sign < 0:
                        away_shift += sign * fatigue
        return home_shift, away_shift

    def penalty_skill(self, team: str) -> float:
        """Shootout skill from blended strength."""
        base = float(self._strengths.get(team, 0.0))
        return 1.0 / (1.0 + np.exp(-base))

    def to_dataframe(self) -> pd.DataFrame:
        df = self.features.copy()
        df["strength"] = df["team"].map(self._strengths)
        df["attack"] = df["team"].map(self._attack)
        df["defense"] = df["team"].map(self._defense)
        return df