"""Post-match availability: suspensions, cards, and form adjustments."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .config import DATA_DIR, DEFAULT_MATCH_RESULTS_PATH
from .group_results import load_completed_group_matches
from .tournament_data import all_teams

DEFAULT_MATCH_EVENTS_PATH = DATA_DIR / "match_events.csv"

# event_type → how severity contributes to team multiplier
_PENALTY_EVENTS = {
    "red_card",
    "injury_out",
    "injury_monitor",
    "form_concern",
    "team_discipline",
    "yellow_accumulation",
}
_BOOST_EVENTS = {"form_boost"}
_INJURY_EVENTS = {"injury_monitor", "injury_out"}
_CLEAR_EVENTS = {"injury_clear"}
_SUSPENSION_EVENTS = {"red_card", "yellow_accumulation"}

_RECOVERY_NOTES = re.compile(
    r"\b(?:return(?:s|ed)?|comeback|available|cleared|fit again|back in|"
    r"recovered|passed fitness|starts?|starting)\b",
    re.IGNORECASE,
)


def load_match_events(path: Path | str = DEFAULT_MATCH_EVENTS_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(
            columns=[
                "date",
                "team",
                "player",
                "event_type",
                "severity",
                "misses_next_match",
                "yellow_count",
                "notes",
                "source",
            ]
        )
    df = pd.read_csv(path)
    if "misses_next_match" in df.columns:
        df["misses_next_match"] = df["misses_next_match"].astype(str).str.lower().isin(
            {"true", "1", "yes"}
        )
    return df


def _team_match_dates(
    results: pd.DataFrame,
    team: str,
    *,
    after_date: str | None = None,
    on_or_before: str | None = None,
) -> list[str]:
    if results.empty:
        return []
    mask = (results["home"] == team) | (results["away"] == team)
    subset = results[mask].copy()
    if after_date:
        subset = subset[subset["date"].astype(str) > after_date]
    if on_or_before:
        subset = subset[subset["date"].astype(str) <= on_or_before]
    return sorted(subset["date"].astype(str).unique().tolist())


def _suspension_served(
    event: pd.Series,
    results: pd.DataFrame,
    as_of_date: str | None,
) -> bool:
    if not bool(event.get("misses_next_match", False)):
        return False
    event_date = str(event["date"])
    team = str(event["team"])
    matches = _team_match_dates(
        results,
        team,
        after_date=event_date,
        on_or_before=as_of_date,
    )
    return len(matches) >= 1


def _injury_cleared_by_recovery_event(
    event: pd.Series,
    all_events: pd.DataFrame,
) -> bool:
    player = str(event.get("player", "") or "").strip()
    team = str(event["team"])
    event_date = str(event["date"])
    if not player:
        return False

    later = all_events[
        (all_events["date"].astype(str) > event_date)
        & (all_events["team"] == team)
        & (all_events["player"].astype(str) == player)
    ]
    if later.empty:
        return False

    if later["event_type"].isin(_CLEAR_EVENTS).any():
        return True

    for _, row in later.iterrows():
        if str(row["event_type"]) == "form_boost" and _RECOVERY_NOTES.search(
            str(row.get("notes", "") or "")
        ):
            return True
        if _RECOVERY_NOTES.search(str(row.get("notes", "") or "")):
            if str(row["event_type"]) not in _INJURY_EVENTS:
                return True
    return False


def _injury_cleared_by_match_played(
    event: pd.Series,
    results: pd.DataFrame,
    all_events: pd.DataFrame,
    as_of_date: str | None,
) -> bool:
    etype = str(event["event_type"])
    if etype not in _INJURY_EVENTS:
        return False

    player = str(event.get("player", "") or "").strip()
    if not player:
        return False

    event_date = str(event["date"])
    team = str(event["team"])
    newer_injury = all_events[
        (all_events["date"].astype(str) > event_date)
        & (all_events["team"] == team)
        & (all_events["player"].astype(str) == player)
        & (all_events["event_type"].isin(_INJURY_EVENTS))
    ]
    if not newer_injury.empty:
        return False

    matches = _team_match_dates(
        results,
        team,
        after_date=event_date,
        on_or_before=as_of_date,
    )
    if not matches:
        return False

    if etype == "injury_out" and bool(event.get("misses_next_match", False)):
        return len(matches) >= 1

    return len(matches) >= 1


def resolve_active_events(
    events: pd.DataFrame,
    *,
    results: pd.DataFrame | None = None,
    as_of_date: str | None = None,
) -> pd.DataFrame:
    """
    Drop penalties that no longer apply: served suspensions, cleared injuries.

    A one-match ban is served after the team completes any match following the
    event. Injuries clear on explicit injury_clear / recovery media signals, a
    recovery form_boost, or after the team plays again without a newer injury
    flag for that player.
    """
    if events.empty:
        return events

    df = events.copy()
    if as_of_date:
        df = df[df["date"].astype(str) <= as_of_date]

    results_df = results if results is not None else load_completed_group_matches()
    if as_of_date and not results_df.empty:
        results_df = results_df[results_df["date"].astype(str) <= as_of_date]

    active_rows: list[pd.Series] = []
    for _, event in df.iterrows():
        etype = str(event["event_type"])

        if etype in _CLEAR_EVENTS:
            continue

        if etype in _SUSPENSION_EVENTS and _suspension_served(
            event, results_df, as_of_date
        ):
            continue

        if etype in _INJURY_EVENTS:
            if _injury_cleared_by_recovery_event(event, df):
                continue
            if _injury_cleared_by_match_played(event, results_df, df, as_of_date):
                continue

        active_rows.append(event)

    if not active_rows:
        return df.iloc[0:0]
    return pd.DataFrame(active_rows).reset_index(drop=True)


def build_availability_features(
    events: pd.DataFrame | None = None,
    as_of_date: str | None = None,
    results: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Aggregate match events into team-level availability and form signals.

    availability_multiplier: product-style penalty in (0.65, 1.0]
    form_adjustment: additive boost/penalty for player_tracker blend
    suspension_count: players missing next match via red/accumulation
    yellow_risk_count: players on one yellow (ban if booked again)
    """
    raw = events if events is not None else load_match_events()
    df = resolve_active_events(raw, results=results, as_of_date=as_of_date)
    teams = pd.DataFrame({"team": all_teams()})

    if df.empty:
        teams["availability_multiplier"] = 1.0
        teams["form_adjustment"] = 0.0
        teams["suspension_count"] = 0
        teams["yellow_risk_count"] = 0
        return teams

    rows: list[dict[str, float | int | str]] = []
    for team, group in df.groupby("team"):
        penalty = 0.0
        boost = 0.0
        suspensions = 0
        yellow_risk = 0

        for _, ev in group.iterrows():
            etype = str(ev["event_type"])
            sev = float(ev["severity"])
            if etype in _PENALTY_EVENTS:
                penalty += sev
            elif etype in _BOOST_EVENTS:
                boost += sev
            elif etype == "yellow_card":
                yc = int(ev.get("yellow_count", 1) or 1)
                if yc >= 1:
                    yellow_risk += 1
            if bool(ev.get("misses_next_match", False)) and not _suspension_served(
                ev,
                results if results is not None else load_completed_group_matches(),
                as_of_date,
            ):
                suspensions += 1

        penalty = min(penalty, 0.35)
        boost = max(boost, -0.12)
        multiplier = max(0.65, 1.0 - penalty)
        form_adj = max(-0.08, min(0.08, boost))

        rows.append(
            {
                "team": team,
                "availability_multiplier": multiplier,
                "form_adjustment": form_adj,
                "suspension_count": suspensions,
                "yellow_risk_count": yellow_risk,
            }
        )

    agg = pd.DataFrame(rows)
    out = teams.merge(agg, on="team", how="left")
    out["availability_multiplier"] = out["availability_multiplier"].fillna(1.0)
    out["form_adjustment"] = out["form_adjustment"].fillna(0.0)
    out["suspension_count"] = out["suspension_count"].fillna(0).astype(int)
    out["yellow_risk_count"] = out["yellow_risk_count"].fillna(0).astype(int)
    return out