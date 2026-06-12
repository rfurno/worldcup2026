"""Evaluate match predictions against actual results."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .config import (
    DEFAULT_MATCH_PREDICTIONS_LOG_PATH,
    DEFAULT_MATCH_RESULTS_PATH,
    OUTPUT_DIR,
    SimulationConfig,
)
from .match_predictor import MatchPredictor


@dataclass
class MatchEvaluation:
    date: str
    match_num: int
    home: str
    away: str
    actual_score: str
    actual_outcome: str
    predicted_winner: str
    outcome_correct: bool
    p_home_win: float
    p_draw: float
    p_away_win: float
    p_actual_outcome: float
    brier_score: float
    log_loss: float
    xg_home: float
    xg_away: float
    xg_home_error: float
    xg_away_error: float
    most_likely_score: str
    p_most_likely_score: float
    p_actual_score: float
    actual_score_rank: int | None


@dataclass
class EvaluationSummary:
    matches_evaluated: int
    outcome_accuracy: float
    mean_brier_score: float
    mean_log_loss: float
    mean_xg_error: float
    mean_actual_outcome_prob: float
    mean_actual_score_prob: float
    match_evaluations: list[MatchEvaluation] = field(default_factory=list)


def load_match_results(path: Path | str = DEFAULT_MATCH_RESULTS_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_predictions_log(
    path: Path | str = DEFAULT_MATCH_PREDICTIONS_LOG_PATH,
) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _actual_outcome(home_goals: int, away_goals: int, home: str, away: str) -> str:
    if home_goals > away_goals:
        return home
    if away_goals > home_goals:
        return away
    return "Draw"


def _outcome_index(outcome: str, home: str, away: str) -> int:
    if outcome == home:
        return 0
    if outcome == "Draw":
        return 1
    return 2


def _brier_score(probs: tuple[float, float, float], actual_idx: int) -> float:
    labels = [0, 0, 0]
    labels[actual_idx] = 1
    return sum((p - y) ** 2 for p, y in zip(probs, labels, strict=True))


def _log_loss(probs: tuple[float, float, float], actual_idx: int) -> float:
    p = max(probs[actual_idx], 1e-15)
    return -math.log(p)


def _score_probability(
    predictor: MatchPredictor,
    home: str,
    away: str,
    venue: str | None,
    neutral: bool,
    home_goals: int,
    away_goals: int,
) -> tuple[float, int | None, list[tuple[str, float]]]:
    saved_ha = predictor.config.home_advantage
    if neutral:
        from .match_predictor import NEUTRAL_HOME_ADVANTAGE

        predictor.config.home_advantage = NEUTRAL_HOME_ADVANTAGE
    try:
        lam_h, lam_a = predictor.model.expected_rates(home, away, venue)
        matrix = predictor.model.score_matrix(lam_h, lam_a, max_goals=8)
        actual_prob = float(matrix[home_goals, away_goals])

        flat: list[tuple[str, float]] = []
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                flat.append((f"{i}-{j}", float(matrix[i, j])))
        flat.sort(key=lambda x: -x[1])
        rank = next(
            (idx + 1 for idx, (score, _) in enumerate(flat) if score == f"{home_goals}-{away_goals}"),
            None,
        )
        return actual_prob, rank, flat[:10]
    finally:
        predictor.config.home_advantage = saved_ha


def evaluate_predictions(
    results: pd.DataFrame | None = None,
    predictions: pd.DataFrame | None = None,
    config: SimulationConfig | None = None,
    recompute_score_probs: bool = True,
) -> EvaluationSummary:
    """Compare logged predictions to recorded results."""
    results_df = results if results is not None else load_match_results()
    preds_df = predictions if predictions is not None else load_predictions_log()

    if results_df.empty or preds_df.empty:
        return EvaluationSummary(
            matches_evaluated=0,
            outcome_accuracy=0.0,
            mean_brier_score=0.0,
            mean_log_loss=0.0,
            mean_xg_error=0.0,
            mean_actual_outcome_prob=0.0,
            mean_actual_score_prob=0.0,
        )

    predictor = MatchPredictor(config or SimulationConfig(verbose=False)) if recompute_score_probs else None
    evaluations: list[MatchEvaluation] = []

    merged = results_df.merge(
        preds_df,
        on=["date", "match_num", "home", "away"],
        how="inner",
        suffixes=("_result", "_pred"),
    )

    for _, row in merged.iterrows():
        home_goals = int(row["home_goals"])
        away_goals = int(row["away_goals"])
        home = str(row["home"])
        away = str(row["away"])
        actual = _actual_outcome(home_goals, away_goals, home, away)
        predicted = str(row["predicted_winner"])

        probs = (
            float(row["p_home_win"]),
            float(row["p_draw"]),
            float(row["p_away_win"]),
        )
        actual_idx = _outcome_index(actual, home, away)

        venue = row.get("venue_pred") or row.get("venue")
        venue = str(venue) if pd.notna(venue) else None
        neutral = str(row.get("neutral", "false")).lower() in {"true", "1", "yes"}

        p_actual_score = 0.0
        score_rank = None
        if predictor is not None:
            p_actual_score, score_rank, _ = _score_probability(
                predictor,
                home,
                away,
                venue,
                neutral,
                home_goals,
                away_goals,
            )

        evaluations.append(
            MatchEvaluation(
                date=str(row["date"]),
                match_num=int(row["match_num"]),
                home=home,
                away=away,
                actual_score=f"{home_goals}-{away_goals}",
                actual_outcome=actual,
                predicted_winner=predicted,
                outcome_correct=predicted == actual,
                p_home_win=probs[0],
                p_draw=probs[1],
                p_away_win=probs[2],
                p_actual_outcome=probs[actual_idx],
                brier_score=_brier_score(probs, actual_idx),
                log_loss=_log_loss(probs, actual_idx),
                xg_home=float(row["xg_home"]),
                xg_away=float(row["xg_away"]),
                xg_home_error=abs(float(row["xg_home"]) - home_goals),
                xg_away_error=abs(float(row["xg_away"]) - away_goals),
                most_likely_score=str(row["most_likely_score"]),
                p_most_likely_score=float(row["p_most_likely_score"]),
                p_actual_score=p_actual_score,
                actual_score_rank=score_rank,
            )
        )

    if not evaluations:
        return EvaluationSummary(
            matches_evaluated=0,
            outcome_accuracy=0.0,
            mean_brier_score=0.0,
            mean_log_loss=0.0,
            mean_xg_error=0.0,
            mean_actual_outcome_prob=0.0,
            mean_actual_score_prob=0.0,
        )

    n = len(evaluations)
    return EvaluationSummary(
        matches_evaluated=n,
        outcome_accuracy=sum(e.outcome_correct for e in evaluations) / n,
        mean_brier_score=sum(e.brier_score for e in evaluations) / n,
        mean_log_loss=sum(e.log_loss for e in evaluations) / n,
        mean_xg_error=sum(e.xg_home_error + e.xg_away_error for e in evaluations) / n,
        mean_actual_outcome_prob=sum(e.p_actual_outcome for e in evaluations) / n,
        mean_actual_score_prob=sum(e.p_actual_score for e in evaluations) / n,
        match_evaluations=evaluations,
    )


def format_evaluation_report(summary: EvaluationSummary) -> str:
    lines = [
        "# Prediction Evaluation Report",
        "",
        f"**Matches evaluated**: {summary.matches_evaluated}",
        "",
        "## Aggregate metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Outcome accuracy (predicted winner) | **{summary.outcome_accuracy * 100:.1f}%** |",
        f"| Mean Brier score (3-way) | {summary.mean_brier_score:.4f} |",
        f"| Mean log loss | {summary.mean_log_loss:.4f} |",
        f"| Mean xG total error (|xG−goals| per team) | {summary.mean_xg_error:.2f} |",
        f"| Mean P(actual outcome) | {summary.mean_actual_outcome_prob * 100:.1f}% |",
        f"| Mean P(actual scoreline) | {summary.mean_actual_score_prob * 100:.1f}% |",
        "",
        "## Match-by-match",
        "",
    ]

    for e in summary.match_evaluations:
        correct = "✓" if e.outcome_correct else "✗"
        lines.extend(
            [
                f"### {e.home} vs {e.away} ({e.date})",
                "",
                f"- **Actual**: {e.actual_score} ({e.actual_outcome})",
                f"- **Predicted winner**: {e.predicted_winner} {correct}",
                f"- **Outcome probs**: {e.home} {e.p_home_win * 100:.1f}% | Draw {e.p_draw * 100:.1f}% | {e.away} {e.p_away_win * 100:.1f}%",
                f"- **P(actual outcome)**: {e.p_actual_outcome * 100:.1f}%",
                f"- **Brier / log loss**: {e.brier_score:.4f} / {e.log_loss:.4f}",
                f"- **xG vs goals**: {e.xg_home:.2f}–{e.xg_away:.2f} predicted vs {e.actual_score} actual "
                f"(errors {e.xg_home_error:.2f}, {e.xg_away_error:.2f})",
                f"- **Scoreline**: most likely {e.most_likely_score} ({e.p_most_likely_score * 100:.1f}%) | "
                f"actual P={e.p_actual_score * 100:.1f}%"
                + (f" (rank #{e.actual_score_rank})" if e.actual_score_rank else ""),
                "",
            ]
        )

    return "\n".join(lines)


def save_evaluation(
    summary: EvaluationSummary,
    output_dir: Path = OUTPUT_DIR,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "prediction_evaluation.md"
    csv_path = output_dir / "prediction_evaluation.csv"

    report_path.write_text(format_evaluation_report(summary), encoding="utf-8")

    rows = [
        {
            "date": e.date,
            "match_num": e.match_num,
            "home": e.home,
            "away": e.away,
            "actual_score": e.actual_score,
            "actual_outcome": e.actual_outcome,
            "predicted_winner": e.predicted_winner,
            "outcome_correct": e.outcome_correct,
            "p_actual_outcome": e.p_actual_outcome,
            "brier_score": e.brier_score,
            "log_loss": e.log_loss,
            "xg_home_error": e.xg_home_error,
            "xg_away_error": e.xg_away_error,
            "p_actual_score": e.p_actual_score,
            "actual_score_rank": e.actual_score_rank,
        }
        for e in summary.match_evaluations
    ]
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    return report_path, csv_path