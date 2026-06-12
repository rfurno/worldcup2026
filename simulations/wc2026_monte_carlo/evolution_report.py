"""Generate markdown report showing how predictions evolved over the tournament."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import OUTPUT_DIR, SimulationConfig
from .prediction_tracker import refresh_after_results, save_evolution_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build prediction evolution report (alias for refresh_predictions --report-only)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output markdown path (default: simulations/output/prediction_evolution.md)",
    )
    args = parser.parse_args(argv)

    if args.output:
        path = save_evolution_report(output_path=Path(args.output))
    else:
        summary = refresh_after_results(
            config=SimulationConfig(verbose=False),
            report_only=True,
        )
        path = summary.evolution_report_path
    print(f"Evolution report saved to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())