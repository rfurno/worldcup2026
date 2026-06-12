"""CLI: evaluate logged predictions against match results."""

from __future__ import annotations

import argparse
import sys

from .config import (
    DEFAULT_MATCH_PREDICTIONS_LOG_PATH,
    DEFAULT_MATCH_RESULTS_PATH,
    SimulationConfig,
)
from .prediction_evaluator import (
    evaluate_predictions,
    format_evaluation_report,
    load_match_results,
    load_predictions_log,
    save_evaluation,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate World Cup match predictions against actual results"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Filter to a single date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--results",
        type=str,
        default=str(DEFAULT_MATCH_RESULTS_PATH),
        help="Path to match_results.csv",
    )
    parser.add_argument(
        "--predictions",
        type=str,
        default=str(DEFAULT_MATCH_PREDICTIONS_LOG_PATH),
        help="Path to match_predictions_log.csv",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Print report only; do not write output files",
    )
    parser.add_argument(
        "--skip-score-probs",
        action="store_true",
        help="Skip Dixon-Coles recomputation of actual scoreline probability",
    )
    args = parser.parse_args(argv)

    results = load_match_results(args.results)
    predictions = load_predictions_log(args.predictions)

    if args.date:
        results = results[results["date"] == args.date]
        predictions = predictions[predictions["date"] == args.date]

    if results.empty:
        print("No match results found for evaluation.")
        return 1
    if predictions.empty:
        print("No logged predictions found for evaluation.")
        return 1

    summary = evaluate_predictions(
        results=results,
        predictions=predictions,
        config=SimulationConfig(verbose=False),
        recompute_score_probs=not args.skip_score_probs,
    )

    report = format_evaluation_report(summary)
    print(report)

    if not args.no_save:
        report_path, csv_path = save_evaluation(summary)
        print(f"\nSaved: {report_path}")
        print(f"Saved: {csv_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())