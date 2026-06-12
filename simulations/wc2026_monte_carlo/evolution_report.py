"""Generate markdown report showing how predictions evolved over the tournament."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import OUTPUT_DIR
from .prediction_tracker import save_evolution_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build prediction evolution report")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output markdown path (default: simulations/output/prediction_evolution.md)",
    )
    args = parser.parse_args(argv)

    output = Path(args.output) if args.output else OUTPUT_DIR / "prediction_evolution.md"
    path = save_evolution_report(output_path=output)
    print(f"Evolution report saved to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())