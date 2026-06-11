"""Full 48-team World Cup tournament simulation."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .dixon_coles import DixonColesModel, MatchOutcome
from .tournament_data import (
    GROUPS,
    GROUP_MATCH_SCHEDULE,
    HOST_NATIONS,
    GroupStanding,
)


@dataclass
class QualifiedTeam:
    team: str
    group: str
    position: int
    points: int
    goal_difference: int
    goals_for: int
    seed_score: float


@dataclass
class TournamentResult:
    winner: str
    runner_up: str
    stages_reached: dict[str, str]
    total_goals: int = 0
    match_count: int = 0


def _resolve_h2h(standings: list[GroupStanding], rng: np.random.Generator) -> list[str]:
    """Head-to-head tiebreaker among teams level on points/GD/GF."""
    if len(standings) == 1:
        return [standings[0].team]

    points = {s.team: s.points for s in standings}
    max_pts = max(points.values())
    contenders = [s for s in standings if s.points == max_pts]
    if len(contenders) == 1:
        return [contenders[0].team] + [
            s.team for s in standings if s.team != contenders[0].team
        ]

    gd = {s.team: s.goal_difference for s in contenders}
    max_gd = max(gd.values())
    contenders = [s for s in contenders if s.goal_difference == max_gd]
    if len(contenders) == 1:
        ordered = [contenders[0].team]
        for s in sorted(standings, key=lambda x: (-x.points, -x.goal_difference, -x.goals_for)):
            if s.team not in ordered:
                ordered.append(s.team)
        return ordered

    gf = {s.team: s.goals_for for s in contenders}
    max_gf = max(gf.values())
    contenders = [s for s in contenders if s.goals_for == max_gf]
    if len(contenders) == 1:
        ordered = [contenders[0].team]
        for s in sorted(standings, key=lambda x: (-x.points, -x.goal_difference, -x.goals_for)):
            if s.team not in ordered:
                ordered.append(s.team)
        return ordered

    tied = [s.team for s in contenders]
    rng.shuffle(tied)
    ordered = tied[:]
    for s in sorted(standings, key=lambda x: (-x.points, -x.goal_difference, -x.goals_for)):
        if s.team not in ordered:
            ordered.append(s.team)
    return ordered


def rank_group(standings: list[GroupStanding], rng: np.random.Generator) -> list[str]:
    buckets: dict[tuple[int, int, int], list[GroupStanding]] = {}
    for s in standings:
        key = (s.points, s.goal_difference, s.goals_for)
        buckets.setdefault(key, []).append(s)

    ranked: list[str] = []
    for key in sorted(buckets.keys(), reverse=True):
        bucket = buckets[key]
        if len(bucket) > 1:
            ranked.extend(_resolve_h2h(bucket, rng))
        else:
            ranked.append(bucket[0].team)
    return ranked


def select_third_place_qualifiers(
    third_places: list[GroupStanding], rng: np.random.Generator
) -> list[GroupStanding]:
    ordered = sorted(
        third_places,
        key=lambda s: (s.points, s.goal_difference, s.goals_for),
        reverse=True,
    )
    if len(ordered) <= 8:
        return ordered

    cutoff_key = (
        ordered[7].points,
        ordered[7].goal_difference,
        ordered[7].goals_for,
    )
    qualifiers = [s for s in ordered[:8]]
    tied = [
        s
        for s in ordered[8:]
        if (s.points, s.goal_difference, s.goals_for) == cutoff_key
    ]
    if tied:
        rng.shuffle(tied)
        qualifiers.extend(tied[: max(0, 8 - len(qualifiers))])
    return qualifiers[:8]


def build_knockout_field(
    group_tables: dict[str, list[GroupStanding]],
    rng: np.random.Generator,
    strength_lookup: dict[str, float],
) -> list[QualifiedTeam]:
    third_place_candidates: list[GroupStanding] = []
    qualifiers: list[QualifiedTeam] = []

    for group, standings in group_tables.items():
        ranked = rank_group(standings, rng)
        for pos, team in enumerate(ranked[:2], start=1):
            s = next(x for x in standings if x.team == team)
            qualifiers.append(
                QualifiedTeam(
                    team=team,
                    group=group,
                    position=pos,
                    points=s.points,
                    goal_difference=s.goal_difference,
                    goals_for=s.goals_for,
                    seed_score=strength_lookup.get(team, 0.0),
                )
            )
        third = next(x for x in standings if x.team == ranked[2])
        third_place_candidates.append(third)

    third_qualifiers = select_third_place_qualifiers(third_place_candidates, rng)
    for s in third_qualifiers:
        qualifiers.append(
            QualifiedTeam(
                team=s.team,
                group=s.group,
                position=3,
                points=s.points,
                goal_difference=s.goal_difference,
                goals_for=s.goals_for,
                seed_score=strength_lookup.get(s.team, 0.0),
            )
        )

    return qualifiers


def seed_knockout_bracket(qualifiers: list[QualifiedTeam]) -> list[str]:
    """
    Build a seeded Round of 32 bracket.

    Winners are seeded 1-12, runners-up 13-24, third-place 25-32.
    Pairings: 1v32, 16v17, 8v25, etc. (standard balanced bracket).
    """
    winners = sorted(
        [q for q in qualifiers if q.position == 1],
        key=lambda q: (q.points, q.goal_difference, q.goals_for, q.seed_score),
        reverse=True,
    )
    runners = sorted(
        [q for q in qualifiers if q.position == 2],
        key=lambda q: (q.points, q.goal_difference, q.goals_for, q.seed_score),
        reverse=True,
    )
    thirds = sorted(
        [q for q in qualifiers if q.position == 3],
        key=lambda q: (q.points, q.goal_difference, q.goals_for, q.seed_score),
        reverse=True,
    )

    seeded = [q.team for q in winners + runners + thirds]
    n = len(seeded)
    bracket_order: list[int] = []
    slots = list(range(1, n + 1))

    def fold(items: list[int]) -> list[int]:
        if len(items) == 2:
            return [items[0], items[1]]
        mid = len(items) // 2
        left = fold(items[:mid])
        right = fold(items[mid:])
        out: list[int] = []
        for a, b in zip(left, reversed(right)):
            out.extend([a, b])
        return out

    order = fold(slots)
    return [seeded[i - 1] for i in order]


def simulate_knockout_round(
    teams: list[str],
    model: DixonColesModel,
    rng: np.random.Generator,
) -> tuple[list[str], int, int]:
    if len(teams) == 1:
        return teams, 0, 0

    next_round: list[str] = []
    goals = 0
    matches = 0
    for i in range(0, len(teams), 2):
        a, b = teams[i], teams[i + 1]
        outcome = model.simulate_knockout_match(a, b, rng, neutral=True)
        goals += outcome.home_goals + outcome.away_goals
        matches += 1
        if outcome.penalty_winner:
            winner = outcome.penalty_winner
        elif outcome.home_goals > outcome.away_goals:
            winner = a
        else:
            winner = b
        next_round.append(winner)
    return next_round, goals, matches


class TournamentSimulator:
    def __init__(self, model: DixonColesModel):
        self.model = model

    def simulate_group_stage(
        self, rng: np.random.Generator
    ) -> tuple[dict[str, list[GroupStanding]], int, int]:
        tables: dict[str, list[GroupStanding]] = {}
        total_goals = 0
        match_count = 0

        for group, teams in GROUPS.items():
            standings = [GroupStanding(team=t, group=group) for t in teams]
            lookup = {s.team: s for s in standings}

            for home_idx, away_idx in GROUP_MATCH_SCHEDULE:
                home = teams[home_idx]
                away = teams[away_idx]
                venue = None
                if home in HOST_NATIONS:
                    venue = None
                hg, ag = self.model.simulate_scoreline(home, away, rng, venue=venue)
                lookup[home].record_result(hg, ag)
                lookup[away].record_result(ag, hg)
                total_goals += hg + ag
                match_count += 1

            tables[group] = standings
        return tables, total_goals, match_count

    def simulate(self, rng: np.random.Generator) -> TournamentResult:
        strength_lookup = {
            team: self.model.strength_model._strengths.get(team, 0.0)
            for team in self.model.strength_model._strengths.index
        }

        group_tables, goals, matches = self.simulate_group_stage(rng)
        qualifiers = build_knockout_field(group_tables, rng, strength_lookup)
        bracket = seed_knockout_bracket(qualifiers)

        stages_reached: dict[str, str] = {team: "group" for team in sum(GROUPS.values(), [])}
        for q in qualifiers:
            stages_reached[q.team] = "r32"

        current = bracket
        runner_up = bracket[0]
        for stage_key in ("r16", "qf", "sf", "final", "winner"):
            prev_round = current[:]
            current, g, m = simulate_knockout_round(current, self.model, rng)
            goals += g
            matches += m
            if stage_key == "winner":
                if len(prev_round) == 2 and len(current) == 1:
                    runner_up = prev_round[1] if current[0] == prev_round[0] else prev_round[0]
                stages_reached[current[0]] = "winner"
                stages_reached[runner_up] = "final"
            else:
                for team in current:
                    stages_reached[team] = stage_key

        if len(current) != 1:
            raise RuntimeError("Knockout bracket did not resolve to a single winner")

        winner = current[0]

        return TournamentResult(
            winner=winner,
            runner_up=runner_up,
            stages_reached=stages_reached,
            total_goals=goals,
            match_count=matches,
        )