"""
Two-command tournament workflow.

predict      — forecast tomorrow's (or a given date's) fixtures
add-results  — record scores, collect events, re-simulate, evaluate
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from .config import SimulationConfig
from .match_event_collector import collect_events_for_new_results, regenerate_events_tracker
from .model_factory import clear_model_cache
from .prediction_markdown import update_match_predictions_md
from .prediction_tracker import append_match_results, log_match_predictions, refresh_after_results
from .results_markdown import update_match_results_md


@dataclass
class PredictSummary:
    target_date: str
    matches_predicted: int
    logged: int
    markdown_path: Path


@dataclass
class AddResultsSummary:
    results_added: int
    events_added: int
    events_tracker_path: Path
    checkpoint: str
    snapshot_created: bool
    evolution_report_path: Path
    evaluation_report_path: Path | None
    predictions_markdown_path: Path
    results_markdown_path: Path


def run_predict(
    target: date | None = None,
    *,
    config: SimulationConfig | None = None,
) -> PredictSummary:
    """
    Predict fixtures for *target* (default: tomorrow).

    Uses the full model stack:
    - Elo, squad value, club xG + international xG, recent form, club chemistry
    - Betting markets (tournament winner odds + per-match 1X2 blend)
    - Injuries (injury_tracker.md) + post-match events (cards, suspensions,
      form boosts/concerns via match_events.csv / supplements)
    - In-tournament form from completed results
    - Dixon-Coles with tuned draw correlation, MD1 draw bump, draw-aware picks
    - Optional lineup signals and external simulation ensemble
    """
    from .match_predictor import MatchPredictor
    from .predict_matches import FIXTURES_BY_DATE, fixtures_for, format_prediction

    if target is None:
        target = date.today() + timedelta(days=1)

    fixtures = fixtures_for(target)
    if not fixtures:
        raise ValueError(f"No fixtures scheduled for {target.isoformat()}")

    cfg = config or SimulationConfig(verbose=False)
    predictor = MatchPredictor(cfg)

    print(f"# Match Predictions — {target.strftime('%B %d, %Y')}\n")
    predictions = []
    enriched: list[dict] = []
    for fixture in fixtures:
        row = {**fixture, "date": target.isoformat()}
        enriched.append(row)
        pred = predictor.predict(
            row["home"],
            row["away"],
            venue=row.get("venue"),
            neutral=row.get("neutral", False),
            match_date=target.isoformat(),
            match_num=row.get("match"),
            matchday=1,
        )
        predictions.append(pred)
        print(format_prediction(row, pred))
        print()

    logged = log_match_predictions(enriched, predictions, snapshot_date=target.isoformat())
    if logged:
        print(f"Logged {logged} prediction(s) → match_predictions_log.csv\n")

    md_path = update_match_predictions_md(
        target_dates=[target.isoformat()],
        live_fixtures=enriched,
        live_predictions=predictions,
        live_date=target.isoformat(),
    )
    print(f"Updated {md_path}\n")

    return PredictSummary(
        target_date=target.isoformat(),
        matches_predicted=len(predictions),
        logged=logged,
        markdown_path=md_path,
    )


def run_add_results(
    results: list[dict] | None = None,
    *,
    config: SimulationConfig | None = None,
    simulations: int = 10_000,
    group_simulations: int = 10_000,
    seed: int = 42,
    force_snapshot: bool = False,
) -> AddResultsSummary:
    """
    Record match result(s) and refresh the full post-match pipeline:

    1. Append to match_results.csv (skipped when *results* is empty)
    2. Scrape Wikipedia + sports media injuries + merge match_events_supplement.csv
    3. Regenerate match_events_tracker.md
    4. Re-simulate tournament, snapshot, evaluate predictions
    5. Update match-results.md and match_predictions.md
    """
    added = 0
    if results:
        added = append_match_results(results)
        if added:
            print(f"Added {added} result(s) → match_results.csv")
        else:
            print("No new results added (duplicate or empty).")

    clear_model_cache()

    events_added = collect_events_for_new_results()
    tracker_path = regenerate_events_tracker()
    if events_added:
        print(f"Collected {events_added} event(s) → match_events.csv")
    print(f"Events tracker: {tracker_path}")

    cfg = config or SimulationConfig(
        n_simulations=simulations,
        random_seed=seed,
        verbose=True,
    )

    summary = refresh_after_results(
        config=cfg,
        force=force_snapshot,
        run_evaluation=True,
        group_simulations=group_simulations,
    )

    print()
    print(f"Checkpoint: {summary.checkpoint.label}")
    print(f"Matches completed: {summary.matches_completed}")
    if summary.groups_updated:
        print(f"Groups updated: {', '.join(summary.groups_updated)}")
    print(
        f"Snapshot created: {'yes' if summary.snapshot_created else 'no (already exists)'}"
    )
    print(f"Evolution report: {summary.evolution_report_path}")
    if summary.evaluation_report_path:
        print(f"Evaluation report: {summary.evaluation_report_path}")

    results_md = update_match_results_md()
    preds_md = update_match_predictions_md()
    print(f"Results markdown: {results_md}")
    print(f"Predictions markdown: {preds_md}")

    return AddResultsSummary(
        results_added=added,
        events_added=events_added,
        events_tracker_path=tracker_path,
        checkpoint=summary.checkpoint.label,
        snapshot_created=summary.snapshot_created,
        evolution_report_path=summary.evolution_report_path,
        evaluation_report_path=summary.evaluation_report_path,
        predictions_markdown_path=preds_md,
        results_markdown_path=results_md,
    )


def fixture_meta_for_result(
    match_date: str,
    match_num: int,
) -> dict | None:
    """Look up venue/stadium/neutral from the official fixture list."""
    from .predict_matches import FIXTURES_BY_DATE

    for fixture in FIXTURES_BY_DATE.get(match_date, []):
        if int(fixture["match"]) == int(match_num):
            return fixture
    return None