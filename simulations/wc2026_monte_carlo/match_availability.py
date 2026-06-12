"""Post-match availability: suspensions, cards, and form adjustments."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import DATA_DIR
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


def build_availability_features(
    events: pd.DataFrame | None = None,
    as_of_date: str | None = None,
) -> pd.DataFrame:
    """
    Aggregate match events into team-level availability and form signals.

    availability_multiplier: product-style penalty in (0.65, 1.0]
    form_adjustment: additive boost/penalty for player_tracker blend
    suspension_count: players missing next match via red/accumulation
    yellow_risk_count: players on one yellow (ban if booked again)
    """
    df = events if events is not None else load_match_events()
    teams = pd.DataFrame({"team": all_teams()})

    if df.empty:
        teams["availability_multiplier"] = 1.0
        teams["form_adjustment"] = 0.0
        teams["suspension_count"] = 0
        teams["yellow_risk_count"] = 0
        return teams

    if as_of_date:
        df = df[df["date"] <= as_of_date]

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
            if bool(ev.get("misses_next_match", False)):
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