"""[deprecated] Use: python -m wc2026_monte_carlo add-results"""

from __future__ import annotations

import argparse
import sys

from .workflow import fixture_meta_for_result, run_add_results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="[deprecated] Use: python -m wc2026_monte_carlo add-results",
    )
    parser.add_argument("-n", "--simulations", type=int, default=10_000)
    parser.add_argument("--group-simulations", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--match-num", type=int, default=None)
    parser.add_argument("--group", type=str, default=None)
    parser.add_argument("--home", type=str, default=None)
    parser.add_argument("--away", type=str, default=None)
    parser.add_argument("--home-goals", type=int, default=None)
    parser.add_argument("--away-goals", type=int, default=None)
    parser.add_argument("--venue", type=str, default=None)
    parser.add_argument("--stadium", type=str, default=None)
    parser.add_argument("--neutral", action="store_true")
    args = parser.parse_args(argv)

    rows: list[dict] = []
    fields = [
        args.date,
        args.match_num,
        args.group,
        args.home,
        args.away,
        args.home_goals,
        args.away_goals,
    ]
    if any(v is not None for v in fields):
        if not all(v is not None for v in fields):
            parser.error(
                "Provide --date, --match-num, --group, --home, --away, "
                "--home-goals, and --away-goals"
            )
        meta = fixture_meta_for_result(args.date, args.match_num) or {}
        rows.append(
            {
                "date": args.date,
                "match_num": args.match_num,
                "group": args.group,
                "home": args.home,
                "away": args.away,
                "home_goals": args.home_goals,
                "away_goals": args.away_goals,
                "venue": args.venue or meta.get("venue"),
                "stadium": args.stadium or meta.get("stadium"),
                "neutral": args.neutral or bool(meta.get("neutral", False)),
            }
        )

    run_add_results(
        rows,
        simulations=args.simulations,
        group_simulations=args.group_simulations,
        seed=args.seed,
        force_snapshot=args.force,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())