"""Refresh all predictions after match results are updated."""

from __future__ import annotations

import argparse
import sys

from .config import SimulationConfig
from .prediction_tracker import append_match_results, refresh_after_results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Re-simulate, snapshot, evaluate, and regenerate the evolution report "
            "after match_results.csv is updated"
        )
    )
    parser.add_argument(
        "-n",
        "--simulations",
        type=int,
        default=10_000,
        help="Tournament Monte Carlo simulations",
    )
    parser.add_argument(
        "--group-simulations",
        type=int,
        default=10_000,
        help="Simulations per group with completed matches",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recapture snapshot even if this checkpoint already exists",
    )
    parser.add_argument(
        "--no-evaluation",
        action="store_true",
        help="Skip match prediction evaluation",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only regenerate prediction_evolution.md (no re-simulation)",
    )
    parser.add_argument(
        "--date",
        type=str,
        required=False,
        help="Match date (YYYY-MM-DD) when appending a result via CLI",
    )
    parser.add_argument("--match-num", type=int, help="Match number")
    parser.add_argument("--group", type=str, help="Group letter")
    parser.add_argument("--home", type=str, help="Home team")
    parser.add_argument("--away", type=str, help="Away team")
    parser.add_argument("--home-goals", type=int, help="Home goals")
    parser.add_argument("--away-goals", type=int, help="Away goals")
    parser.add_argument("--venue", type=str, default=None, help="Venue city")
    parser.add_argument("--stadium", type=str, default=None, help="Stadium name")
    parser.add_argument(
        "--neutral",
        action="store_true",
        help="Neutral venue fixture",
    )
    args = parser.parse_args(argv)

    append_fields = [
        args.date,
        args.match_num,
        args.group,
        args.home,
        args.away,
        args.home_goals,
        args.away_goals,
    ]
    if any(v is not None for v in append_fields):
        if not all(v is not None for v in append_fields):
            parser.error(
                "To append a result, provide --date, --match-num, --group, "
                "--home, --away, --home-goals, and --away-goals"
            )
        added = append_match_results(
            [
                {
                    "date": args.date,
                    "match_num": args.match_num,
                    "group": args.group,
                    "home": args.home,
                    "away": args.away,
                    "home_goals": args.home_goals,
                    "away_goals": args.away_goals,
                    "venue": args.venue,
                    "stadium": args.stadium,
                    "neutral": args.neutral,
                }
            ]
        )
        if added:
            print(f"Added {added} result(s) to match_results.csv")
        else:
            print("No new results added (duplicate or empty).")

    config = SimulationConfig(
        n_simulations=args.simulations,
        random_seed=args.seed,
        verbose=True,
    )

    summary = refresh_after_results(
        config=config,
        force=args.force,
        run_evaluation=not args.no_evaluation,
        group_simulations=args.group_simulations,
        report_only=args.report_only,
    )

    print()
    print(f"Checkpoint: {summary.checkpoint.label}")
    print(f"Matches completed: {summary.matches_completed}")
    if summary.groups_updated:
        print(f"Groups updated: {', '.join(summary.groups_updated)}")
    print(f"Snapshot created: {'yes' if summary.snapshot_created else 'no (already exists)'}")
    print(f"Evolution report: {summary.evolution_report_path}")
    if summary.evaluation_report_path:
        print(f"Evaluation report: {summary.evaluation_report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())