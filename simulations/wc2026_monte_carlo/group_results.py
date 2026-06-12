"""Apply completed group-stage results from match_results.csv."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import DEFAULT_MATCH_RESULTS_PATH
from .tournament_data import GROUPS, GROUP_MATCH_SCHEDULE, GroupStanding


def _match_index(group: str, home: str, away: str) -> int | None:
    teams = GROUPS[group]
    for idx, (home_idx, away_idx) in enumerate(GROUP_MATCH_SCHEDULE):
        if teams[home_idx] == home and teams[away_idx] == away:
            return idx
    return None


def load_completed_group_matches(
    path: Path | str = DEFAULT_MATCH_RESULTS_PATH,
) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if df.empty or "group" not in df.columns:
        return pd.DataFrame()
    return df


def apply_completed_matches(
    group: str,
    standings: list[GroupStanding],
    completed: pd.DataFrame | None = None,
) -> set[int]:
    """
    Record actual results into standings.

    Returns match indices in GROUP_MATCH_SCHEDULE that are already played.
    """
    df = completed if completed is not None else load_completed_group_matches()
    if df.empty:
        return set()

    lookup = {s.team: s for s in standings}
    played: set[int] = set()
    group_rows = df[df["group"] == group]

    for _, row in group_rows.iterrows():
        home = str(row["home"])
        away = str(row["away"])
        idx = _match_index(group, home, away)
        if idx is None or home not in lookup or away not in lookup:
            continue
        hg, ag = int(row["home_goals"]), int(row["away_goals"])
        lookup[home].record_result(hg, ag)
        lookup[away].record_result(ag, hg)
        played.add(idx)

    return played