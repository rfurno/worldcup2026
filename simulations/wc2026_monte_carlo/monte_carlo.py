"""Monte Carlo engine: run N full tournaments and aggregate probabilities."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

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
    stage_probabilities: pd.DataFrame
    expected_goals_per_match: float
    top_paths: pd.DataFrame


class MonteCarloEngine:
    def __init__(self, config: SimulationConfig, refresh_external: bool = False):
        self.config = config
        self.refresh_external = refresh_external
        features = build_team_features(refresh_external=refresh_external)
        self.strength_model = TeamStrengthModel(
            config, features=features, refresh_external=False
        )
        historical = fetch_historical_matches()
        self.model = DixonColesModel(
            self.strength_model, config, historical_matches=historical
        )
        self.simulator = TournamentSimulator(self.model)

    def run(self) -> SimulationSummary:
        cfg = self.config
        rng = np.random.default_rng(cfg.random_seed)
        teams = all_teams()

        winner_counts = {team: 0 for team in teams}
        stage_counts = {team: {stage: 0 for stage in STAGE_ORDER} for team in teams}
        total_goals = 0
        total_matches = 0
        path_counts: dict[str, int] = {}

        for i in range(cfg.n_simulations):
            if cfg.verbose and i > 0 and i % max(1, cfg.n_simulations // 10) == 0:
                print(f"  Completed {i:,} / {cfg.n_simulations:,} simulations...")

            result = self.simulator.simulate(rng)
            winner_counts[result.winner] += 1
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
            stage_probabilities=stage_df,
            expected_goals_per_match=expected_gpg,
            top_paths=paths_df,
        )

    def save_results(self, summary: SimulationSummary) -> None:
        out = self.config.output_dir
        out.mkdir(parents=True, exist_ok=True)
        summary.winner_probabilities.to_csv(out / "winner_probabilities.csv", index=False)
        summary.stage_probabilities.to_csv(out / "stage_probabilities.csv", index=False)
        if not summary.top_paths.empty:
            summary.top_paths.to_csv(out / "top_paths.csv", index=False)

        with open(out / "summary.txt", "w", encoding="utf-8") as f:
            f.write(f"World Cup 2026 Monte Carlo Simulation\n")
            f.write(f"Simulations: {summary.n_simulations:,}\n")
            f.write(
                f"Expected goals per match: {summary.expected_goals_per_match:.2f}\n\n"
            )
            f.write("Top 10 Winner Probabilities:\n")
            for _, row in summary.winner_probabilities.head(10).iterrows():
                f.write(
                    f"  {row['team']:<22} {row['win_probability'] * 100:5.2f}%\n"
                )
            f.write("\nStage Reach Probabilities (Top 10):\n")
            for _, row in summary.stage_probabilities.head(10).iterrows():
                f.write(f"  {row['team']:<22}")
                for stage in ("r32", "r16", "qf", "sf", "final", "winner"):
                    col = f"p_{stage}"
                    if col in row:
                        f.write(f" {stage}:{row[col] * 100:5.1f}%")
                f.write("\n")