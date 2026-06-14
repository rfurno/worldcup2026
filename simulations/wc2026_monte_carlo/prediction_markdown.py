"""Auto-generate match_predictions.md from the prediction log."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pandas as pd

from .config import (
    DEFAULT_MATCH_PREDICTIONS_LOG_PATH,
    DEFAULT_MATCH_RESULTS_PATH,
    MATCH_PREDICTIONS_MD_PATH,
)
from .predict_matches import FIXTURES_BY_DATE, format_prediction
from .prediction_evaluator import evaluate_predictions, load_match_results, load_predictions_log


def _fmt_date_header(iso_date: str) -> str:
    d = date.fromisoformat(iso_date)
    return d.strftime("%B %d, %Y")


def _fixture_lookup() -> dict[tuple[str, int], dict]:
    lookup: dict[tuple[str, int], dict] = {}
    for day, fixtures in FIXTURES_BY_DATE.items():
        for fixture in fixtures:
            lookup[(day, fixture["match"])] = {**fixture, "date": day}
    return lookup


def format_predictions_section(
    target_date: str,
    predictions_df: pd.DataFrame,
    fixture_lookup: dict[tuple[str, int], dict],
) -> str:
    day_preds = predictions_df[predictions_df["date"].astype(str) == target_date].copy()
    if day_preds.empty:
        return ""

    day_preds = day_preds.sort_values("match_num")
    lines = [
        f"## {_fmt_date_header(target_date)} — Match Predictions",
        "",
    ]

    for _, row in day_preds.iterrows():
        key = (target_date, int(row["match_num"]))
        fixture = fixture_lookup.get(key)
        if fixture is None:
            fixture = {
                "match": int(row["match_num"]),
                "group": row["group"],
                "kickoff": "TBD",
                "stadium": row.get("venue", "TBD"),
                "date": target_date,
            }

        class _Pred:
            home = row["home"]
            away = row["away"]
            expected_home_goals = float(row["xg_home"])
            expected_away_goals = float(row["xg_away"])
            home_win_prob = float(row["p_home_win"])
            draw_prob = float(row["p_draw"])
            away_win_prob = float(row["p_away_win"])
            predicted_winner = row["predicted_winner"]
            most_likely_scorelines = [
                (str(row["most_likely_score"]), float(row["p_most_likely_score"]))
            ]
            confidence = row.get("confidence", "Low")

        lines.append(format_prediction(fixture, _Pred()))
        lines.append("")

    return "\n".join(lines)


def format_results_accuracy_section(
    results_df: pd.DataFrame,
    predictions_df: pd.DataFrame,
) -> str:
    if results_df.empty or predictions_df.empty:
        return ""

    summary = evaluate_predictions(results=results_df, predictions=predictions_df)
    if summary.matches_evaluated == 0:
        return ""

    lines = [
        "## Prediction Performance",
        "",
        f"- **Matches evaluated**: {summary.matches_evaluated}",
        f"- **Winner accuracy**: {summary.outcome_accuracy * 100:.1f}%",
        f"- **3-way accuracy**: {summary.three_way_accuracy * 100:.1f}%",
        f"- **Mean Brier (3-way)**: {summary.mean_brier_score:.4f}",
        "",
        "### By confidence tier",
        "",
        "| Tier | N | Winner accuracy | 3-way accuracy |",
        "|------|---|-----------------|----------------|",
    ]
    for tier in summary.confidence_tiers:
        lines.append(
            f"| {tier.tier} | {tier.count} | "
            f"{tier.winner_accuracy * 100:.1f}% | {tier.three_way_accuracy * 100:.1f}% |"
        )
    lines.append("")
    return "\n".join(lines)


def _live_predictions_to_df(
    fixtures: list[dict],
    predictions: list,
    target_date: str,
) -> pd.DataFrame:
    rows = []
    for fixture, pred in zip(fixtures, predictions, strict=True):
        score, score_p = pred.most_likely_scorelines[0]
        rows.append(
            {
                "date": target_date,
                "match_num": fixture["match"],
                "group": fixture["group"],
                "home": pred.home,
                "away": pred.away,
                "venue": fixture.get("venue"),
                "neutral": fixture.get("neutral", False),
                "p_home_win": pred.home_win_prob,
                "p_draw": pred.draw_prob,
                "p_away_win": pred.away_win_prob,
                "predicted_winner": pred.predicted_winner,
                "xg_home": pred.expected_home_goals,
                "xg_away": pred.expected_away_goals,
                "most_likely_score": score,
                "p_most_likely_score": score_p,
                "confidence": pred.confidence,
            }
        )
    return pd.DataFrame(rows)


def update_match_predictions_md(
    target_dates: list[str] | None = None,
    log_path: Path | str = DEFAULT_MATCH_PREDICTIONS_LOG_PATH,
    results_path: Path | str = DEFAULT_MATCH_RESULTS_PATH,
    output_path: Path | str = MATCH_PREDICTIONS_MD_PATH,
    live_fixtures: list[dict] | None = None,
    live_predictions: list | None = None,
    live_date: str | None = None,
) -> Path:
    """Rewrite match_predictions.md from CSV log + latest forecasts."""
    log_path = Path(log_path)
    output_path = Path(output_path)
    predictions = load_predictions_log(log_path)
    if live_fixtures and live_predictions and live_date:
        live_df = _live_predictions_to_df(live_fixtures, live_predictions, live_date)
        if not predictions.empty:
            predictions = predictions[
                predictions["date"].astype(str) != str(live_date)
            ]
        predictions = pd.concat([predictions, live_df], ignore_index=True)
    results = load_match_results(results_path)
    fixture_lookup = _fixture_lookup()

    if target_dates is None:
        target_dates = sorted(predictions["date"].astype(str).unique().tolist())

    today = date.today().isoformat()
    lines = [
        "# World Cup 2026 Match Predictions",
        "",
        "Daily match-by-match forecasts using the market-calibrated Dixon-Coles model "
        "(Elo + squad value + xG + recent form + club chemistry + injuries + match events "
        "+ per-match odds blend + in-tournament form, anchored to betting odds).",
        "",
        f"**Updated**: {_fmt_date_header(today)} (auto-generated)",
        "",
        "*Source: `simulations/data/match_predictions_log.csv` · "
        "Regenerate: `python -m wc2026_monte_carlo predict`*",
        "",
        "---",
        "",
    ]

    lines.append(format_results_accuracy_section(results, predictions))

    for target in reversed(target_dates):
        section = format_predictions_section(target, predictions, fixture_lookup)
        if section:
            lines.append(section)
            lines.append("---")
            lines.append("")

    if not results.empty:
        lines.extend(["## Completed Results", ""])
        for day in sorted(results["date"].astype(str).unique(), reverse=True):
            day_results = results[results["date"].astype(str) == day]
            lines.append(f"### {_fmt_date_header(day)}")
            lines.append("")
            lines.append("| Match | Result | Model pick | Correct? |")
            lines.append("|-------|--------|------------|----------|")
            for _, row in day_results.sort_values("match_num").iterrows():
                home, away = row["home"], row["away"]
                score = f"{int(row['home_goals'])}–{int(row['away_goals'])}"
                pred_row = predictions[
                    (predictions["date"].astype(str) == day)
                    & (predictions["match_num"].astype(int) == int(row["match_num"]))
                ]
                if pred_row.empty:
                    pick = "—"
                    correct = "—"
                else:
                    pr = pred_row.iloc[-1]
                    pick = f"{pr['predicted_winner']} ({max(pr['p_home_win'], pr['p_draw'], pr['p_away_win']) * 100:.0f}%)"
                    actual = (
                        home
                        if int(row["home_goals"]) > int(row["away_goals"])
                        else away
                        if int(row["away_goals"]) > int(row["home_goals"])
                        else "Draw"
                    )
                    correct = "✓" if pr["predicted_winner"] == actual else "✗"
                lines.append(f"| {home} vs {away} | {score} | {pick} | {correct} |")
            lines.append("")

    lines.extend(
        [
            "---",
            "",
            "*Workflow: `add-results` after matches · `predict` before the next day*",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path