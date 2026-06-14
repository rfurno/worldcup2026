"""
World Cup 2026 prediction workflow — two commands:

  python -m wc2026_monte_carlo predict
  python -m wc2026_monte_carlo add-results --date ... --match-num ... \\
      --group ... --home ... --away ... --home-goals N --away-goals N

Advanced: full tournament Monte Carlo only (no match workflow):

  python -m wc2026_monte_carlo.cli --simulations 10000
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="World Cup 2026 match predictions and results workflow",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    predict = sub.add_parser(
        "predict",
        help="Predict tomorrow's fixtures (log + update match_predictions.md)",
    )
    predict.add_argument(
        "--date",
        type=str,
        default=None,
        help="Fixture date YYYY-MM-DD (default: tomorrow)",
    )

    add = sub.add_parser(
        "add-results",
        help="Add a result, collect events, re-simulate, evaluate, refresh markdown",
    )
    add.add_argument("--date", type=str, default=None, help="Match date YYYY-MM-DD")
    add.add_argument("--match-num", type=int, default=None)
    add.add_argument("--group", type=str, default=None)
    add.add_argument("--home", type=str, default=None)
    add.add_argument("--away", type=str, default=None)
    add.add_argument("--home-goals", type=int, default=None)
    add.add_argument("--away-goals", type=int, default=None)
    add.add_argument("--venue", type=str, default=None)
    add.add_argument("--stadium", type=str, default=None)
    add.add_argument(
        "--neutral",
        action="store_true",
        help="Neutral venue (auto-filled from fixture list when omitted)",
    )
    add.add_argument("-n", "--simulations", type=int, default=10_000)
    add.add_argument("--group-simulations", type=int, default=10_000)
    add.add_argument("--seed", type=int, default=42)
    add.add_argument(
        "--force",
        action="store_true",
        help="Recapture snapshot even if checkpoint already exists",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "predict":
        from .workflow import run_predict

        target = (
            date.fromisoformat(args.date)
            if args.date
            else date.today() + timedelta(days=1)
        )
        try:
            run_predict(target)
        except ValueError as exc:
            print(exc)
            return 1
        return 0

    if args.command == "add-results":
        from .workflow import fixture_meta_for_result, run_add_results

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
                    "To add a result, provide --date, --match-num, --group, "
                    "--home, --away, --home-goals, and --away-goals"
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
            rows or None,
            simulations=args.simulations,
            group_simulations=args.group_simulations,
            seed=args.seed,
            force_snapshot=args.force,
        )
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())