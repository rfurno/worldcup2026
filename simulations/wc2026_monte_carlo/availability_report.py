"""Report how match events shift team features and upcoming predictions."""

from __future__ import annotations

import argparse
import sys

import numpy as np

from .config import SimulationConfig
from .data_loaders import build_team_features, fetch_historical_matches
from .dixon_coles import DixonColesModel
from .match_availability import build_availability_features
from .match_predictor import NEUTRAL_HOME_ADVANTAGE, MatchPredictor
from .team_strength import TeamStrengthModel

GROUP_A_TEAMS = ["Mexico", "South Africa", "South Korea", "Czechia"]

JUNE_18_FIXTURES = [
    {
        "home": "Mexico",
        "away": "South Korea",
        "venue": "Guadalajara",
        "neutral": True,
        "label": "Mexico vs South Korea",
    },
    {
        "home": "Czechia",
        "away": "South Africa",
        "venue": "Atlanta",
        "neutral": True,
        "label": "Czechia vs South Africa",
    },
]


def _strip_event_adjustments(features):
    out = features.copy()
    avail = build_availability_features().set_index("team")
    for team in GROUP_A_TEAMS:
        if team not in avail.index:
            continue
        mult = float(avail.loc[team, "availability_multiplier"])
        form = float(avail.loc[team, "form_adjustment"])
        mask = out["team"] == team
        if 0 < mult < 1:
            out.loc[mask, "injury_multiplier"] = (
                out.loc[mask, "injury_multiplier"] / mult
            ).clip(0.65, 1.0)
        if form:
            out.loc[mask, "player_tracker_adj"] -= form
    return out


def _predict_match(
    features,
    home: str,
    away: str,
    venue: str,
    neutral: bool,
) -> tuple[float, float, float, float, float]:
    cfg = SimulationConfig(verbose=False)
    sm = TeamStrengthModel(cfg, features=features)
    model = DixonColesModel(sm, cfg, fetch_historical_matches())
    saved = cfg.home_advantage
    if neutral:
        cfg.home_advantage = NEUTRAL_HOME_ADVANTAGE
    try:
        lam_h, lam_a = model.expected_rates(home, away, venue)
        mat = model.score_matrix(lam_h, lam_a)
        hw = float(np.tril(mat, -1).sum())
        dr = float(np.trace(mat).sum())
        aw = float(np.triu(mat, 1).sum())
        return hw, dr, aw, lam_h, lam_a
    finally:
        cfg.home_advantage = saved


def format_team_table(features) -> str:
    avail = build_availability_features()
    df = features[features["team"].isin(GROUP_A_TEAMS)][["team", "injury_multiplier"]].merge(
        avail[avail["team"].isin(GROUP_A_TEAMS)][
            ["team", "form_adjustment", "suspension_count", "yellow_risk_count"]
        ],
        on="team",
    )
    lines = [
        "| Team | Availability | Form adj | Suspensions | Yellow risk |",
        "|------|--------------|----------|-------------|-------------|",
    ]
    for _, row in df.iterrows():
        lines.append(
            f"| {row['team']} | {row['injury_multiplier']:.3f} | "
            f"{row['form_adjustment']:+.3f} | {int(row['suspension_count'])} | "
            f"{int(row['yellow_risk_count'])} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show match-event impact on predictions")
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare Jun 18 predictions with vs without event adjustments",
    )
    args = parser.parse_args(argv)

    with_events = build_team_features()
    print("# Match availability impact — Group A\n")
    print("## Team adjustments (with events)\n")
    print(format_team_table(with_events))
    print()

    avail = build_availability_features()
    for _, row in avail[avail["team"].isin(GROUP_A_TEAMS)].iterrows():
        notes = []
        if row["suspension_count"]:
            notes.append(f"{int(row['suspension_count'])} suspended next match")
        if row["yellow_risk_count"]:
            notes.append(f"{int(row['yellow_risk_count'])} on 1 yellow")
        if row["form_adjustment"]:
            notes.append(f"form {row['form_adjustment']:+.2f}")
        if notes:
            print(f"- **{row['team']}**: {', '.join(notes)}")
    print()

    predictor = MatchPredictor(SimulationConfig(verbose=False))
    print("## June 18 predictions (with events)\n")
    for fx in JUNE_18_FIXTURES:
        pred = predictor.predict(
            fx["home"], fx["away"], venue=fx["venue"], neutral=fx["neutral"]
        )
        print(
            f"- **{fx['label']}**: {pred.predicted_winner} — "
            f"{pred.home_win_prob * 100:.1f}% / {pred.draw_prob * 100:.1f}% / "
            f"{pred.away_win_prob * 100:.1f}% | xG "
            f"{pred.expected_home_goals:.2f}–{pred.expected_away_goals:.2f}"
        )
    print()

    if args.compare:
        base_features = _strip_event_adjustments(with_events)
        print("## Before vs after (June 18)\n")
        print("| Fixture | | Without | With | Delta |")
        print("|---------|--|---------|------|-------|")
        for fx in JUNE_18_FIXTURES:
            b = _predict_match(
                base_features, fx["home"], fx["away"], fx["venue"], fx["neutral"]
            )
            a = _predict_match(
                with_events, fx["home"], fx["away"], fx["venue"], fx["neutral"]
            )
            print(
                f"| {fx['label']} | P({fx['home']} win) | {b[0] * 100:.1f}% | "
                f"{a[0] * 100:.1f}% | {(a[0] - b[0]) * 100:+.1f}pp |"
            )
            print(
                f"| {fx['label']} | P({fx['away']} win) | {b[2] * 100:.1f}% | "
                f"{a[2] * 100:.1f}% | {(a[2] - b[2]) * 100:+.1f}pp |"
            )
            print(
                f"| {fx['label']} | xG | {b[3]:.2f}–{b[4]:.2f} | "
                f"{a[3]:.2f}–{a[4]:.2f} | — |"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())