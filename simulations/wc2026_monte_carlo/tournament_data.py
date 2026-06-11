"""Official 2026 World Cup group draw and tournament structure."""

from __future__ import annotations

from dataclasses import dataclass

# Source: 2026 FIFA World Cup draw (December 5, 2025)
GROUPS: dict[str, list[str]] = {
    "A": ["Mexico", "South Africa", "South Korea", "Czechia"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

HOST_NATIONS = {"Mexico", "Canada", "United States"}

# Approximate host cities for venue/travel effects (additional-data-sources.md #6)
TEAM_HOME_VENUES: dict[str, str] = {
    "Mexico": "Mexico City",
    "Canada": "Toronto",
    "United States": "Los Angeles",
}

VENUE_COORDINATES: dict[str, tuple[float, float]] = {
    "Mexico City": (19.43, -99.13),
    "Guadalajara": (20.67, -103.35),
    "Monterrey": (25.67, -100.31),
    "Toronto": (43.65, -79.38),
    "Vancouver": (49.28, -123.12),
    "Los Angeles": (34.05, -118.24),
    "San Francisco": (37.77, -122.42),
    "Seattle": (47.61, -122.33),
    "Dallas": (32.78, -96.80),
    "Houston": (29.76, -95.37),
    "Kansas City": (39.10, -94.58),
    "Miami": (25.76, -80.19),
    "Atlanta": (33.75, -84.39),
    "Boston": (42.36, -71.06),
    "Philadelphia": (39.95, -75.17),
    "New York": (40.71, -74.01),
}

# Group match schedule: (home_idx, away_idx) within each group's team list
GROUP_MATCH_SCHEDULE: list[tuple[int, int]] = [
    (0, 1),
    (2, 3),
    (0, 2),
    (3, 1),
    (3, 0),
    (1, 2),
]

STAGE_NAMES = {
    "group": "Group Stage",
    "r32": "Round of 32",
    "r16": "Round of 16",
    "qf": "Quarter-finals",
    "sf": "Semi-finals",
    "final": "Final",
    "winner": "Winner",
}


@dataclass
class GroupStanding:
    team: str
    group: str
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    def record_result(self, goals_for: int, goals_against: int) -> None:
        self.played += 1
        self.goals_for += goals_for
        self.goals_against += goals_against
        if goals_for > goals_against:
            self.won += 1
            self.points += 3
        elif goals_for < goals_against:
            self.lost += 1
        else:
            self.drawn += 1
            self.points += 1


def all_teams() -> list[str]:
    teams: list[str] = []
    for group_teams in GROUPS.values():
        teams.extend(group_teams)
    return teams


def team_group(team: str) -> str:
    for group, teams in GROUPS.items():
        if team in teams:
            return group
    raise KeyError(f"Unknown team: {team}")