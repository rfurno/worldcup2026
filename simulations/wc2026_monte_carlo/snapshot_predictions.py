"""Capture a prediction snapshot at the current tournament checkpoint."""

from __future__ import annotations

import argparse
import sys

from .config import SimulationConfig
from .config import OUTPUT_DIR
from .prediction_tracker import (
    capture_snapshot,
    import_snapshot_from_output,
    seed_pre_opening_baseline,
    snapshot_exists,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Capture tournament/group prediction snapshot for evolution tracking"
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
        help="Simulations per group (when --groups enabled)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Override checkpoint (e.g. pre_opening)",
    )
    parser.add_argument(
        "--no-groups",
        action="store_true",
        help="Skip group-position snapshots (faster)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite if snapshot for this checkpoint already exists",
    )
    parser.add_argument(
        "--seed-baseline",
        action="store_true",
        help="Insert retrospective pre-opening baseline from June 10 forecasts",
    )
    parser.add_argument(
        "--import-from-output",
        action="store_true",
        help="Bootstrap snapshot from simulations/output/ CSVs (no re-simulation)",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Snapshot date label (YYYY-MM-DD). Default: today.",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Less output")
    args = parser.parse_args(argv)

    if args.seed_baseline:
        created = seed_pre_opening_baseline(force=args.force)
        if created:
            if not args.quiet:
                print("Seeded pre_opening baseline from June 10 forecasts.")
        elif not args.quiet:
            print("pre_opening baseline already exists (use --force to replace).")
        return 0

    if args.import_from_output:
        result = import_snapshot_from_output(
            OUTPUT_DIR,
            checkpoint_override=args.checkpoint,
            snapshot_date=args.date,
            force=args.force,
            n_simulations=args.simulations,
        )
        if not args.quiet:
            if result:
                print(f"Imported snapshot `{result.snapshot_id}` from {OUTPUT_DIR}/")
            else:
                print("Snapshot already exists (use --force to replace).")
        return 0

    config = SimulationConfig(
        n_simulations=args.simulations,
        random_seed=args.seed,
        verbose=not args.quiet,
    )

    from .prediction_tracker import resolve_checkpoint

    checkpoint = resolve_checkpoint(override=args.checkpoint)
    if snapshot_exists(checkpoint.snapshot_id) and not args.force and not args.quiet:
        print(
            f"Snapshot `{checkpoint.snapshot_id}` already exists. "
            "Use --force to recapture."
        )
        return 0

    if not args.quiet:
        print(f"Capturing snapshot: {checkpoint.label}")
        print(f"  Tournament sims: {args.simulations:,}")
        if not args.no_groups:
            print(f"  Group sims:      {args.group_simulations:,} × 12 groups")

    result = capture_snapshot(
        config=config,
        checkpoint_override=args.checkpoint,
        include_groups=not args.no_groups,
        group_simulations=args.group_simulations,
        force=args.force,
        snapshot_date=args.date,
    )

    if result is None:
        if not args.quiet:
            print("No new snapshot captured.")
        return 0

    if not args.quiet:
        print(f"Saved snapshot `{result.snapshot_id}` to simulations/data/")
    return 0


if __name__ == "__main__":
    sys.exit(main())