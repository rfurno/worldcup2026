"""
World Cup 2026 Monte Carlo Simulation
======================================

SETUP
-----
1. Install dependencies::

       pip install -r simulations/requirements.txt

2. Populate external data (see additional-data-sources.md at repo root):

   - **Elo ratings** (#1): auto-fetched from eloratings.net, or place CSV at
     ``simulations/data/elo_ratings.csv`` with columns ``team,elo``.
   - **Squad values** (#2): Transfermarkt export at
     ``simulations/data/squad_values.csv`` (``team,squad_value_meur``).
   - **xG form** (#4): FBref-derived values at
     ``simulations/data/xg_form.csv`` (``team,xg_diff_per_match``).
   - **Historical matches** (#3): auto-fetched from Kaggle/GitHub mirror, or
     ``simulations/data/historical_matches.csv``.

3. Internal markdown (auto-loaded from repo root):

   - injury_tracker.md (#7)
   - player_tracker.md (#2, #7)
   - winner_odds_table.md / betting_sites_odds.md (#5)
   - opening_fixtures_predictions.md (#3, #6)

USAGE
-----
::

    python -m wc2026_monte_carlo --simulations 10000 --seed 42
    python -m wc2026_monte_carlo --refresh-external --simulations 50000

Outputs land in ``simulations/output/``.
"""

from __future__ import annotations

import argparse
import sys
import time

from .config import SimulationConfig
from .monte_carlo import MonteCarloEngine
from .visualize import plot_stage_heatmap, plot_winner_probabilities


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Monte Carlo simulation of the 2026 FIFA World Cup",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-n",
        "--simulations",
        type=int,
        default=10_000,
        help="Number of full tournament simulations (10,000-50,000 recommended)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--refresh-external",
        action="store_true",
        help="Re-fetch Elo and historical results from external URLs",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for CSV/plot outputs",
    )
    parser.add_argument("--no-plot", action="store_true", help="Skip matplotlib plots")
    parser.add_argument("-q", "--quiet", action="store_true", help="Less console output")
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Append a prediction snapshot for evolution tracking after the run",
    )
    parser.add_argument(
        "--no-group-snapshot",
        action="store_true",
        help="With --snapshot, skip group-position probabilities (faster)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = SimulationConfig(
        n_simulations=args.simulations,
        random_seed=args.seed,
        save_plot=not args.no_plot,
        verbose=not args.quiet,
    )
    if args.output_dir:
        from pathlib import Path

        config.output_dir = Path(args.output_dir)

    if config.verbose:
        print("World Cup 2026 Monte Carlo Simulation")
        print(f"  Simulations: {config.n_simulations:,}")
        print(f"  Random seed: {config.random_seed}")
        print(f"  Output dir:  {config.output_dir}")
        print()

    t0 = time.time()
    engine = MonteCarloEngine(config, refresh_external=args.refresh_external)

    if config.verbose:
        print("Running simulations...")

    summary = engine.run()
    engine.save_results(summary)

    if args.snapshot:
        from .prediction_tracker import save_snapshot_from_summary

        saved = save_snapshot_from_summary(
            summary,
            config,
            include_groups=not args.no_group_snapshot,
            group_simulations=10_000,
        )
        if config.verbose:
            if saved:
                print(f"Prediction snapshot saved: {saved.snapshot_id}")
            else:
                print("Snapshot for current checkpoint already exists — skipped.")

    if config.save_plot:
        plot_winner_probabilities(
            summary.winner_probabilities,
            config.output_dir / "winner_probabilities.png",
        )
        plot_stage_heatmap(
            summary.stage_probabilities,
            config.output_dir / "stage_probabilities.png",
        )

    elapsed = time.time() - t0
    if config.verbose:
        print()
        print(f"Done in {elapsed:.1f}s")
        print(f"Expected goals/match: {summary.expected_goals_per_match:.2f}")
        print()
        print("Top 10 First / Second Place Probabilities:")
        for _, row in summary.first_second_probabilities.head(10).iterrows():
            print(
                f"  {row['team']:<22} "
                f"1st: {row['p_first'] * 100:5.2f}%  "
                f"2nd: {row['p_second'] * 100:5.2f}%  "
                f"podium: {row['p_podium'] * 100:5.2f}%"
            )
        print()
        print("Top 5 Winner / Runner-up Pairs:")
        for _, row in summary.winner_runner_up_pairs.head(5).iterrows():
            print(
                f"  {row['winner']} / {row['runner_up']}: "
                f"{row['probability'] * 100:.2f}%"
            )
        print()
        print(f"Results saved to {config.output_dir}/")

    return 0


if __name__ == "__main__":
    sys.exit(main())