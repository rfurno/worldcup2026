"""Group-stage finishing position probabilities."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .config import SimulationConfig
from .match_predictor import NEUTRAL_HOME_ADVANTAGE
from .model_factory import build_calibrated_models
from .tournament_data import (
    GROUPS,
    GROUP_MATCH_SCHEDULE,
    GroupStanding,
    venue_for_group_match,
)
from .group_results import apply_completed_matches, load_completed_group_matches
from .tournament_simulator import rank_group

# Neutral-site fixtures within each group: (home_idx, away_idx) tuples
GROUP_NEUTRAL_FIXTURES: dict[str, set[tuple[int, int]]] = {
    "A": {(2, 3), (3, 1), (3, 0), (1, 2)},
}


@dataclass
class TeamGroupProbabilities:
    team: str
    p_first: float
    p_second: float
    p_third: float
    p_fourth: float
    p_top_two: float


@dataclass
class GroupPositionSummary:
    group: str
    teams: list[TeamGroupProbabilities]
    most_likely_top_two_pairs: list[tuple[str, str, float]] = field(default_factory=list)


def _simulate_group(
    group: str,
    model: DixonColesModel,
    config: SimulationConfig,
    rng: np.random.Generator,
) -> list[str]:
    teams = GROUPS[group]
    standings = [GroupStanding(team=t, group=group) for t in teams]
    lookup = {s.team: s for s in standings}
    neutral_fixtures = GROUP_NEUTRAL_FIXTURES.get(group, set())
    saved_ha = config.home_advantage

    completed = load_completed_group_matches()
    played = apply_completed_matches(group, standings, completed)

    for match_idx, (home_idx, away_idx) in enumerate(GROUP_MATCH_SCHEDULE):
        if match_idx in played:
            continue
        home = teams[home_idx]
        away = teams[away_idx]
        if (home_idx, away_idx) in neutral_fixtures:
            config.home_advantage = NEUTRAL_HOME_ADVANTAGE
        else:
            config.home_advantage = saved_ha

        venue = venue_for_group_match(group, match_idx, home)
        hg, ag = model.simulate_scoreline(home, away, rng, venue=venue)
        lookup[home].record_result(hg, ag)
        lookup[away].record_result(ag, hg)

    config.home_advantage = saved_ha
    return rank_group(standings, rng)


class GroupPositionPredictor:
    def __init__(self, config: SimulationConfig | None = None):
        self.config = config or SimulationConfig(verbose=False)
        _, self.model, _ = build_calibrated_models(self.config)

    def predict_group(
        self,
        group: str,
        n_simulations: int = 50_000,
        seed: int = 42,
    ) -> GroupPositionSummary:
        if group not in GROUPS:
            raise KeyError(f"Unknown group: {group}")

        teams = GROUPS[group]
        rng = np.random.default_rng(seed)
        position_counts = {t: {1: 0, 2: 0, 3: 0, 4: 0} for t in teams}
        top_two_pairs: dict[tuple[str, str], int] = {}

        for _ in range(n_simulations):
            ranked = _simulate_group(group, self.model, self.config, rng)
            for pos, team in enumerate(ranked, start=1):
                position_counts[team][pos] += 1
            pair = (ranked[0], ranked[1])
            top_two_pairs[pair] = top_two_pairs.get(pair, 0) + 1

        n = n_simulations
        team_probs = []
        for team in teams:
            team_probs.append(
                TeamGroupProbabilities(
                    team=team,
                    p_first=position_counts[team][1] / n,
                    p_second=position_counts[team][2] / n,
                    p_third=position_counts[team][3] / n,
                    p_fourth=position_counts[team][4] / n,
                    p_top_two=(position_counts[team][1] + position_counts[team][2]) / n,
                )
            )

        likely_pairs = sorted(
            [(a, b, c / n) for (a, b), c in top_two_pairs.items()],
            key=lambda x: -x[2],
        )[:8]

        return GroupPositionSummary(
            group=group,
            teams=sorted(team_probs, key=lambda t: -t.p_first),
            most_likely_top_two_pairs=likely_pairs,
        )