"""Evaluate logged predictions — invoked automatically by add-results."""

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
        description="[internal] Evaluation runs automatically via add-results",
    )
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--results", type=str, default=str(DEFAULT_MATCH_RESULTS_PATH))
    parser.add_argument("--predictions", type=str, default=str(DEFAULT_MATCH_PREDICTIONS_LOG_PATH))
    parser.add_argument("--no-save", action="store_true")
    parser.add_argument("--skip-score-probs", action="store_true")
    args = parser.parse_args(argv)

    results = load_match_results(args.results)
    predictions = load_predictions_log(args.predictions)
    if args.date:
        results = results[results["date"] == args.date]
        predictions = predictions[predictions["date"] == args.date]

    if results.empty or predictions.empty:
        print("No data to evaluate.")
        return 1

    summary = evaluate_predictions(
        results=results,
        predictions=predictions,
        config=SimulationConfig(verbose=False),
        recompute_score_probs=not args.skip_score_probs,
    )
    print(format_evaluation_report(summary))
    if not args.no_save:
        report_path, csv_path = save_evaluation(summary)
        print(f"\nSaved: {report_path}\nSaved: {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())