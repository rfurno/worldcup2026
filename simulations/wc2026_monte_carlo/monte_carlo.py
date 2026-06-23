"""Monte Carlo engine: run N full tournaments and aggregate probabilities."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .calibration import fill_missing_market_probs, iterative_strength_adjustment
from .config import SimulationConfig
from .data_loaders import build_team_features, fetch_historical_matches
from .dixon_coles import DixonColesModel
from .team_strength import TeamStrengthModel
from .tournament_data import STAGE_NAMES, all_teams
from .tournament_simulator import TournamentSimulator


STAGE_ORDER = ["group", "r32", "r16", "qf", "sf", "final", "winner"]


@dataclass
class SimulationSummary:
    n_simulations: int
    winner_probabilities: pd.DataFrame
    first_second_probabilities: pd.DataFrame
    winner_runner_up_pairs: pd.DataFrame
    stage_probabilities: pd.DataFrame
    expected_goals_per_match: float
    top_paths: pd.DataFrame


class MonteCarloEngine:
    def __init__(
        self,
        config: SimulationConfig,
        refresh_external: bool = False,
        results_before_date: str | None = None,
    ):
        self.config = config
        self.refresh_external = refresh_external
        features = build_team_features(
            refresh_external=refresh_external,
            config=config,
            results_before_date=results_before_date,
        )
        self.strength_model = TeamStrengthModel(
            config, features=features, refresh_external=False
        )
        historical = fetch_historical_matches()
        self.model = DixonColesModel(
            self.strength_model, config, historical_matches=historical
        )
        self.simulator = TournamentSimulator(self.model)
        self._calibrate_to_market_if_enabled(features)

    def _calibrate_to_market_if_enabled(self, features: pd.DataFrame) -> None:
        cfg = self.config
        if not cfg.calibrate_to_market or not cfg.iterative_market_calibration:
            return

        if cfg.verbose:
            print("Calibrating strengths to betting market odds...")

        df = features.set_index("team")
        target = fill_missing_market_probs(
            teams=list(df.index),
            market_probs=df["market_prob"],
            elo=df["elo"],
        )

        def simulate_fn(rng, strengths):
            self.strength_model.set_strengths(strengths)
            return self.simulator.simulate(rng).winner

        adjusted = iterative_strength_adjustment(
            strengths=self.strength_model._strengths,
            target_probs=target,
            simulate_fn=simulate_fn,
            n_iterations=cfg.calibration_iterations,
            n_sims_per_iter=cfg.calibration_sims_per_iter,
            seed=cfg.random_seed,
        )
        self.strength_model.set_strengths(adjusted)

    def run(self) -> SimulationSummary:
        cfg = self.config
        rng = np.random.default_rng(cfg.random_seed)
        teams = all_teams()

        winner_counts = {team: 0 for team in teams}
        runner_up_counts = {team: 0 for team in teams}
        podium_pair_counts: dict[tuple[str, str], int] = {}
        stage_counts = {team: {stage: 0 for stage in STAGE_ORDER} for team in teams}
        total_goals = 0
        total_matches = 0
        path_counts: dict[str, int] = {}

        for i in range(cfg.n_simulations):
            if cfg.verbose and i > 0 and i % max(1, cfg.n_simulations // 10) == 0:
                print(f"  Completed {i:,} / {cfg.n_simulations:,} simulations...")

            result = self.simulator.simulate(rng)
            winner_counts[result.winner] += 1
            runner_up_counts[result.runner_up] += 1
            pair = (result.winner, result.runner_up)
            podium_pair_counts[pair] = podium_pair_counts.get(pair, 0) + 1
            total_goals += result.total_goals
            total_matches += result.match_count

            for team, stage in result.stages_reached.items():
                stage_idx = STAGE_ORDER.index(stage)
                for s in STAGE_ORDER[1 : stage_idx + 1]:
                    stage_counts[team][s] += 1

            if result.winner in {
                "Spain",
                "France",
                "England",
                "Brazil",
                "Argentina",
                "Germany",
                "Portugal",
            }:
                path = " -> ".join(
                    [
                        result.winner,
                        result.stages_reached.get(result.winner, "winner"),
                    ]
                )
                path_counts[path] = path_counts.get(path, 0) + 1

        n = cfg.n_simulations
        winner_df = pd.DataFrame(
            [
                {
                    "team": team,
                    "wins": winner_counts[team],
                    "win_probability": winner_counts[team] / n,
                }
                for team in teams
            ]
        ).sort_values("win_probability", ascending=False)

        first_second_df = pd.DataFrame(
            [
                {
                    "team": team,
                    "p_first": winner_counts[team] / n,
                    "p_second": runner_up_counts[team] / n,
                    "p_podium": (winner_counts[team] + runner_up_counts[team]) / n,
                    "first_place_finishes": winner_counts[team],
                    "second_place_finishes": runner_up_counts[team],
                }
                for team in teams
            ]
        ).sort_values("p_first", ascending=False)

        pairs_df = pd.DataFrame(
            [
                {
                    "winner": w,
                    "runner_up": r,
                    "count": c,
                    "probability": c / n,
                }
                for (w, r), c in podium_pair_counts.items()
            ]
        ).sort_values("probability", ascending=False)

        stage_rows = []
        for team in teams:
            row = {"team": team}
            for stage in STAGE_ORDER:
                if stage == "group":
                    continue
                row[f"p_{stage}"] = stage_counts[team][stage] / n
            stage_rows.append(row)
        stage_df = pd.DataFrame(stage_rows).sort_values("p_winner", ascending=False)

        paths_df = pd.DataFrame(
            [{"path": k, "count": v, "probability": v / n} for k, v in path_counts.items()]
        )
        if not paths_df.empty:
            paths_df = paths_df.sort_values("probability", ascending=False).head(15)

        expected_gpg = total_goals / total_matches if total_matches else 0.0

        return SimulationSummary(
            n_simulations=n,
            winner_probabilities=winner_df,
            first_second_probabilities=first_second_df,
            winner_runner_up_pairs=pairs_df,
            stage_probabilities=stage_df,
            expected_goals_per_match=expected_gpg,
            top_paths=paths_df,
        )

    def save_results(self, summary: SimulationSummary) -> None:
        out = self.config.output_dir
        out.mkdir(parents=True, exist_ok=True)
        summary.winner_probabilities.to_csv(out / "winner_probabilities.csv", index=False)
        summary.first_second_probabilities.to_csv(
            out / "first_second_probabilities.csv", index=False
        )
        summary.winner_runner_up_pairs.to_csv(
            out / "winner_runner_up_pairs.csv", index=False
        )
        summary.stage_probabilities.to_csv(out / "stage_probabilities.csv", index=False)
        if not summary.top_paths.empty:
            summary.top_paths.to_csv(out / "top_paths.csv", index=False)

        with open(out / "summary.txt", "w", encoding="utf-8") as f:
            f.write(f"World Cup 2026 Monte Carlo Simulation\n")
            f.write(f"Simulations: {summary.n_simulations:,}\n")
            f.write(
                f"Expected goals per match: {summary.expected_goals_per_match:.2f}\n\n"
            )
            f.write("Top 10 First / Second Place Probabilities:\n")
            for _, row in summary.first_second_probabilities.head(10).iterrows():
                f.write(
                    f"  {row['team']:<22} "
                    f"1st:{row['p_first'] * 100:5.2f}%  "
                    f"2nd:{row['p_second'] * 100:5.2f}%  "
                    f"podium:{row['p_podium'] * 100:5.2f}%\n"
                )
            f.write("\nTop 10 Winner / Runner-up Pairs:\n")
            for _, row in summary.winner_runner_up_pairs.head(10).iterrows():
                f.write(
                    f"  {row['winner']} / {row['runner_up']}: "
                    f"{row['probability'] * 100:.2f}%\n"
                )
            f.write("\nStage Reach Probabilities (Top 10):\n")
            for _, row in summary.stage_probabilities.head(10).iterrows():
                f.write(f"  {row['team']:<22}")
                for stage in ("r32", "r16", "qf", "sf", "final", "winner"):
                    col = f"p_{stage}"
                    if col in row:
                        f.write(f" {stage}:{row[col] * 100:5.1f}%")
                f.write("\n")