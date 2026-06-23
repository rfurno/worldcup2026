"""
Backtest tournament-form blend strategies on logged WC 2026 predictions.

Re-predicts each fixture using only results available before kickoff day.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

import pandas as pd

from .config import (
    DEFAULT_MATCH_PREDICTIONS_LOG_PATH,
    DEFAULT_MATCH_RESULTS_PATH,
    SimulationConfig,
)
from .match_predictor import MatchPredictor
from .model_factory import clear_model_cache
from .prediction_evaluator import _actual_outcome, _three_way_correct
from .tournament_form import resolve_tournament_form_blend


@dataclass(frozen=True)
class BlendMode:
    name: str
    dynamic: bool
    static_blend: float = 0.30
    wc_recent_form: bool = True
    blend_override: float | None = None


MODES: tuple[BlendMode, ...] = (
    BlendMode("legacy_static_30", dynamic=False, static_blend=0.30, wc_recent_form=False),
    BlendMode("static_30_wc_form", dynamic=False, static_blend=0.30, wc_recent_form=True),
    BlendMode("static_40_wc_form", dynamic=False, static_blend=0.40, wc_recent_form=True),
    BlendMode("dynamic_wc_form", dynamic=True, wc_recent_form=True),
)


def _load_eval_frame(
    results_path: str,
    predictions_path: str,
) -> pd.DataFrame:
    results = pd.read_csv(results_path)
    preds = pd.read_csv(predictions_path)
    merged = results.merge(
        preds,
        on=["date", "match_num", "home", "away"],
        how="inner",
        suffixes=("_result", "_pred"),
    )
    merged["date"] = merged["date"].astype(str)
    merged["actual_outcome"] = merged.apply(
        lambda r: _actual_outcome(
            int(r["home_goals"]),
            int(r["away_goals"]),
            str(r["home"]),
            str(r["away"]),
        ),
        axis=1,
    )
    return merged.sort_values(["date", "match_num"])


def _config_for_mode(mode: BlendMode) -> SimulationConfig:
    cfg = SimulationConfig(verbose=False)
    cfg.iterative_market_calibration = False
    cfg.use_dynamic_tournament_form_blend = mode.dynamic
    cfg.tournament_form_blend = mode.static_blend
    cfg.use_wc_recent_form = mode.wc_recent_form
    return cfg


def _matchday(match_num: int) -> int:
    if match_num <= 16:
        return 1
    if match_num <= 32:
        return 2
    return 3


def _predict_batch(
    mode: BlendMode,
    batch: pd.DataFrame,
    before_date: str,
    results_subset: pd.DataFrame,
) -> tuple[list[bool], float]:
    cfg = _config_for_mode(mode)
    clear_model_cache()
    override = mode.blend_override
    if not mode.dynamic and mode.blend_override is None:
        override = mode.static_blend

    predictor = MatchPredictor(
        cfg,
        results_before_date=before_date,
        tournament_form_blend_override=override if not mode.dynamic else None,
    )
    blend_used = resolve_tournament_form_blend(
        cfg,
        results=results_subset,
        override=override if not mode.dynamic else None,
    )

    correct: list[bool] = []
    for _, row in batch.iterrows():
        venue = row.get("venue_pred") or row.get("venue_result")
        venue = str(venue) if pd.notna(venue) else None
        neutral = str(row.get("neutral", "false")).lower() in {"true", "1", "yes"}
        pred = predictor.predict(
            str(row["home"]),
            str(row["away"]),
            venue=venue,
            neutral=neutral,
            match_date=str(row["date"]),
            match_num=int(row["match_num"]),
            matchday=_matchday(int(row["match_num"])),
        )
        correct.append(_three_way_correct(pred.predicted_winner, str(row["actual_outcome"])))

    return correct, blend_used


def run_backtest(
    results_path: str = str(DEFAULT_MATCH_RESULTS_PATH),
    predictions_path: str = str(DEFAULT_MATCH_PREDICTIONS_LOG_PATH),
) -> pd.DataFrame:
    merged = _load_eval_frame(results_path, predictions_path)
    all_results = pd.read_csv(results_path)

    rows: list[dict] = []
    for mode in MODES:
        hits = 0
        total = 0
        blend_samples: list[float] = []

        for date, batch in merged.groupby("date", sort=True):
            before_date = str(date)
            results_subset = all_results[all_results["date"].astype(str) < before_date]
            batch_correct, blend_used = _predict_batch(
                mode, batch, before_date, results_subset
            )
            hits += sum(batch_correct)
            total += len(batch_correct)
            blend_samples.append(blend_used)

        rows.append(
            {
                "mode": mode.name,
                "matches": total,
                "winner_correct": hits,
                "winner_accuracy": hits / total if total else 0.0,
                "avg_blend_weight": sum(blend_samples) / len(blend_samples) if blend_samples else 0.0,
            }
        )

    return pd.DataFrame(rows)


def format_backtest_report(summary: pd.DataFrame) -> str:
    lines = [
        "# Tournament-form blend backtest",
        "",
        "Point-in-time re-predictions using results strictly before each match day.",
        "",
        "| Mode | Matches | Correct | Accuracy | Avg blend w |",
        "|------|---------|---------|----------|-------------|",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['mode']} | {int(row['matches'])} | {int(row['winner_correct'])} | "
            f"{row['winner_accuracy'] * 100:.1f}% | {row['avg_blend_weight']:.2f} |"
        )
    best = summary.loc[summary["winner_accuracy"].idxmax()]
    lines.extend(
        [
            "",
            f"**Best mode:** `{best['mode']}` ({best['winner_accuracy'] * 100:.1f}% winner accuracy)",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backtest tournament-form blend strategies")
    parser.add_argument("--results", type=str, default=str(DEFAULT_MATCH_RESULTS_PATH))
    parser.add_argument("--predictions", type=str, default=str(DEFAULT_MATCH_PREDICTIONS_LOG_PATH))
    parser.add_argument(
        "--output",
        type=str,
        default="simulations/output/tournament_form_backtest.md",
    )
    args = parser.parse_args(argv)

    summary = run_backtest(args.results, args.predictions)
    report = format_backtest_report(summary)
    print(report)

    from pathlib import Path

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report + "\n", encoding="utf-8")
    print(f"\nSaved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())