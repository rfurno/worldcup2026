"""Snapshot and evolution tracking for tournament predictions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from .config import (
    DATA_DIR,
    DEFAULT_MATCH_PREDICTIONS_LOG_PATH,
    DEFAULT_MATCH_RESULTS_PATH,
    OUTPUT_DIR,
    SimulationConfig,
)
from .group_position_predictor import GroupPositionPredictor
from .group_results import load_completed_group_matches
from .match_predictor import MatchPrediction
from .monte_carlo import MonteCarloEngine, SimulationSummary
from .tournament_data import GROUPS

DEFAULT_SNAPSHOTS_PATH = DATA_DIR / "prediction_snapshots.csv"
DEFAULT_EVOLUTION_PATH = DATA_DIR / "prediction_evolution.csv"
DEFAULT_PAIRS_LOG_PATH = DATA_DIR / "winner_runner_up_log.csv"

STAGE_METRICS = ("p_r32", "p_r16", "p_qf", "p_sf", "p_final", "p_winner")
GROUP_METRICS = ("p_first", "p_second", "p_third", "p_fourth", "p_top_two")
RESULT_COLUMNS = [
    "date",
    "match_num",
    "group",
    "home",
    "away",
    "home_goals",
    "away_goals",
    "venue",
    "stadium",
    "neutral",
]

# Retrospective baseline from June 10 pre-opening run (tournament_first_second_predictions.md)
PRE_OPENING_TOURNAMENT: dict[str, dict[str, float]] = {
    "France": {"p_win": 0.132, "p_runner_up": 0.075, "p_podium": 0.207},
    "Spain": {"p_win": 0.128, "p_runner_up": 0.082, "p_podium": 0.209},
    "England": {"p_win": 0.096, "p_runner_up": 0.072, "p_podium": 0.168},
    "Portugal": {"p_win": 0.079, "p_runner_up": 0.059, "p_podium": 0.138},
    "Brazil": {"p_win": 0.071, "p_runner_up": 0.057, "p_podium": 0.129},
    "Argentina": {"p_win": 0.060, "p_runner_up": 0.057, "p_podium": 0.117},
    "Germany": {"p_win": 0.039, "p_runner_up": 0.036, "p_podium": 0.074},
    "Morocco": {"p_win": 0.016, "p_runner_up": 0.016, "p_podium": 0.032},
    "Qatar": {"p_win": 0.015, "p_runner_up": 0.017, "p_podium": 0.031},
    "Czechia": {"p_win": 0.015, "p_runner_up": 0.022, "p_podium": 0.036},
    "DR Congo": {"p_win": 0.013, "p_runner_up": 0.013, "p_podium": 0.025},
}

PRE_OPENING_PAIRS: list[tuple[str, str, float]] = [
    ("France", "Spain", 0.014),
    ("France", "England", 0.012),
    ("Spain", "France", 0.011),
    ("England", "Spain", 0.011),
    ("Spain", "England", 0.011),
    ("England", "France", 0.010),
    ("France", "Portugal", 0.009),
    ("France", "Brazil", 0.009),
    ("Spain", "Brazil", 0.009),
    ("Portugal", "France", 0.008),
]

# Pre-MD1 Group A from match_predictions.md (June 11 forecasts)
PRE_OPENING_GROUP_A: dict[str, dict[str, float]] = {
    "Czechia": {"p_first": 0.321, "p_second": 0.282, "p_third": 0.228, "p_fourth": 0.169, "p_top_two": 0.603},
    "South Africa": {"p_first": 0.241, "p_second": 0.237, "p_third": 0.255, "p_fourth": 0.267, "p_top_two": 0.478},
    "South Korea": {"p_first": 0.228, "p_second": 0.243, "p_third": 0.257, "p_fourth": 0.272, "p_top_two": 0.472},
    "Mexico": {"p_first": 0.209, "p_second": 0.238, "p_third": 0.261, "p_fourth": 0.292, "p_top_two": 0.447},
}


@dataclass
class CheckpointInfo:
    snapshot_id: str
    checkpoint: str
    matches_completed: int
    last_result_date: str | None
    label: str


@dataclass
class RefreshSummary:
    checkpoint: CheckpointInfo
    snapshot_created: bool
    evolution_report_path: Path
    evaluation_report_path: Path | None = None
    matches_completed: int = 0
    groups_updated: list[str] = field(default_factory=list)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_snapshots(path: Path | str = DEFAULT_SNAPSHOTS_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(
            columns=[
                "snapshot_id",
                "snapshot_date",
                "checkpoint",
                "matches_completed",
                "last_result_date",
                "n_simulations",
                "group_simulations",
                "notes",
            ]
        )
    return pd.read_csv(path)


def load_evolution(path: Path | str = DEFAULT_EVOLUTION_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(
            columns=[
                "snapshot_id",
                "snapshot_date",
                "checkpoint",
                "matches_completed",
                "category",
                "group",
                "team",
                "metric",
                "value",
            ]
        )
    return pd.read_csv(path)


def load_pairs_log(path: Path | str = DEFAULT_PAIRS_LOG_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(
            columns=[
                "snapshot_id",
                "snapshot_date",
                "checkpoint",
                "matches_completed",
                "winner",
                "runner_up",
                "probability",
            ]
        )
    return pd.read_csv(path)


def groups_with_results(
    results_path: Path | str = DEFAULT_MATCH_RESULTS_PATH,
) -> list[str]:
    df = load_completed_group_matches(results_path)
    if df.empty or "group" not in df.columns:
        return []
    return sorted(df["group"].astype(str).unique().tolist())


def append_match_results(
    rows: list[dict] | pd.DataFrame,
    path: Path | str = DEFAULT_MATCH_RESULTS_PATH,
) -> int:
    """Append new results to match_results.csv (skips date+match_num duplicates)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(rows, list):
        new_df = pd.DataFrame(rows)
    else:
        new_df = rows.copy()

    if new_df.empty:
        return 0

    for col in RESULT_COLUMNS:
        if col not in new_df.columns:
            new_df[col] = None

    existing = load_completed_group_matches(path) if path.exists() else pd.DataFrame()
    added = 0
    to_append: list[dict] = []

    for _, row in new_df.iterrows():
        date_val = str(row["date"])
        match_num = int(row["match_num"])
        if not existing.empty:
            dup = (existing["date"].astype(str) == date_val) & (
                existing["match_num"].astype(int) == match_num
            )
            if dup.any():
                continue
        to_append.append({col: row.get(col) for col in RESULT_COLUMNS})
        added += 1

    if not to_append:
        return 0

    _append_rows(path, to_append, RESULT_COLUMNS)
    return added


def resolve_checkpoint(
    results_path: Path | str = DEFAULT_MATCH_RESULTS_PATH,
    override: str | None = None,
) -> CheckpointInfo:
    if override == "pre_opening":
        return CheckpointInfo(
            snapshot_id="pre_opening",
            checkpoint="pre_opening",
            matches_completed=0,
            last_result_date=None,
            label="Pre-opening (before Matchday 1)",
        )

    df = load_completed_group_matches(results_path)
    n = len(df)
    if n == 0:
        return CheckpointInfo(
            snapshot_id="pre_opening",
            checkpoint="pre_opening",
            matches_completed=0,
            last_result_date=None,
            label="Pre-opening (before Matchday 1)",
        )

    last_date = str(df["date"].max()) if "date" in df.columns else None
    snapshot_id = f"after_match_{n}"
    md_label = _matchday_label(n, last_date)
    return CheckpointInfo(
        snapshot_id=snapshot_id,
        checkpoint=snapshot_id,
        matches_completed=n,
        last_result_date=last_date,
        label=md_label,
    )


def _matchday_label(matches_completed: int, last_date: str | None) -> str:
    if matches_completed <= 2:
        phase = "After Matchday 1"
    elif matches_completed <= 24:
        phase = f"After Matchday {matches_completed // 2}"
    elif matches_completed <= 72:
        phase = f"After group match {matches_completed}"
    else:
        phase = f"After match {matches_completed}"
    if last_date:
        return f"{phase} ({last_date})"
    return phase


def snapshot_exists(snapshot_id: str, path: Path | str = DEFAULT_SNAPSHOTS_PATH) -> bool:
    df = load_snapshots(path)
    return not df.empty and snapshot_id in df["snapshot_id"].values


def _append_rows(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_df = pd.DataFrame(rows, columns=columns)
    if path.exists():
        existing = pd.read_csv(path)
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df
    combined.to_csv(path, index=False)


def _evolution_row(
    snapshot_id: str,
    snapshot_date: str,
    checkpoint: str,
    matches_completed: int,
    category: str,
    team: str,
    metric: str,
    value: float,
    group: str = "",
) -> dict:
    return {
        "snapshot_id": snapshot_id,
        "snapshot_date": snapshot_date,
        "checkpoint": checkpoint,
        "matches_completed": matches_completed,
        "category": category,
        "group": group,
        "team": team,
        "metric": metric,
        "value": value,
    }


def rows_from_tournament_summary(
    summary: SimulationSummary,
    checkpoint: CheckpointInfo,
    snapshot_date: str,
) -> list[dict]:
    rows: list[dict] = []
    meta = checkpoint
    for _, row in summary.first_second_probabilities.iterrows():
        team = str(row["team"])
        for metric, col in [
            ("p_win", "p_first"),
            ("p_runner_up", "p_second"),
            ("p_podium", "p_podium"),
        ]:
            rows.append(
                _evolution_row(
                    meta.snapshot_id,
                    snapshot_date,
                    meta.checkpoint,
                    meta.matches_completed,
                    "tournament",
                    team,
                    metric,
                    float(row[col]),
                )
            )

    for _, row in summary.stage_probabilities.iterrows():
        team = str(row["team"])
        for metric in STAGE_METRICS:
            col = metric
            if col in row and pd.notna(row[col]):
                rows.append(
                    _evolution_row(
                        meta.snapshot_id,
                        snapshot_date,
                        meta.checkpoint,
                        meta.matches_completed,
                        "tournament",
                        team,
                        metric,
                        float(row[col]),
                    )
                )
    return rows


def rows_from_group_summary(
    group: str,
    summary,
    checkpoint: CheckpointInfo,
    snapshot_date: str,
) -> list[dict]:
    rows: list[dict] = []
    for team_prob in summary.teams:
        for metric in GROUP_METRICS:
            rows.append(
                _evolution_row(
                    checkpoint.snapshot_id,
                    snapshot_date,
                    checkpoint.checkpoint,
                    checkpoint.matches_completed,
                    "group",
                    team_prob.team,
                    metric,
                    float(getattr(team_prob, metric)),
                    group=group,
                )
            )
    return rows


def rows_from_pairs(
    pairs_df: pd.DataFrame,
    checkpoint: CheckpointInfo,
    snapshot_date: str,
    top_n: int = 20,
) -> tuple[list[dict], list[dict]]:
    evolution_rows: list[dict] = []
    pair_rows: list[dict] = []
    for _, row in pairs_df.head(top_n).iterrows():
        winner = str(row["winner"])
        runner_up = str(row["runner_up"])
        prob = float(row["probability"])
        pair_rows.append(
            {
                "snapshot_id": checkpoint.snapshot_id,
                "snapshot_date": snapshot_date,
                "checkpoint": checkpoint.checkpoint,
                "matches_completed": checkpoint.matches_completed,
                "winner": winner,
                "runner_up": runner_up,
                "probability": prob,
            }
        )
        evolution_rows.append(
            _evolution_row(
                checkpoint.snapshot_id,
                snapshot_date,
                checkpoint.checkpoint,
                checkpoint.matches_completed,
                "pair",
                winner,
                f"with_{runner_up}",
                prob,
            )
        )
    return evolution_rows, pair_rows


def seed_pre_opening_baseline(
    snapshot_date: str = "2026-06-10",
    force: bool = False,
) -> bool:
    """Insert retrospective pre-opening baseline from documented June 10 forecasts."""
    checkpoint = resolve_checkpoint(override="pre_opening")
    if snapshot_exists(checkpoint.snapshot_id) and not force:
        return False
    if force and snapshot_exists(checkpoint.snapshot_id):
        _remove_snapshot(checkpoint.snapshot_id)

    rows: list[dict] = []
    for team, metrics in PRE_OPENING_TOURNAMENT.items():
        for metric, value in metrics.items():
            rows.append(
                _evolution_row(
                    checkpoint.snapshot_id,
                    snapshot_date,
                    checkpoint.checkpoint,
                    0,
                    "tournament",
                    team,
                    metric,
                    value,
                )
            )

    for team, metrics in PRE_OPENING_GROUP_A.items():
        for metric, value in metrics.items():
            rows.append(
                _evolution_row(
                    checkpoint.snapshot_id,
                    snapshot_date,
                    checkpoint.checkpoint,
                    0,
                    "group",
                    team,
                    metric,
                    value,
                    group="A",
                )
            )

    pair_rows = [
        {
            "snapshot_id": checkpoint.snapshot_id,
            "snapshot_date": snapshot_date,
            "checkpoint": checkpoint.checkpoint,
            "matches_completed": 0,
            "winner": w,
            "runner_up": r,
            "probability": p,
        }
        for w, r, p in PRE_OPENING_PAIRS
    ]

    meta_row = {
        "snapshot_id": checkpoint.snapshot_id,
        "snapshot_date": snapshot_date,
        "checkpoint": checkpoint.checkpoint,
        "matches_completed": 0,
        "last_result_date": None,
        "n_simulations": 10000,
        "group_simulations": 50000,
        "notes": "Retrospective baseline from June 10 pre-opening forecasts",
    }

    _append_rows(DEFAULT_SNAPSHOTS_PATH, [meta_row], list(meta_row.keys()))
    _append_rows(DEFAULT_EVOLUTION_PATH, rows, list(rows[0].keys()) if rows else [])
    _append_rows(DEFAULT_PAIRS_LOG_PATH, pair_rows, list(pair_rows[0].keys()))
    return True


def save_snapshot_from_summary(
    summary: SimulationSummary,
    config: SimulationConfig,
    checkpoint_override: str | None = None,
    include_groups: bool = True,
    groups_filter: list[str] | None = None,
    group_simulations: int = 10_000,
    force: bool = False,
    snapshot_date: str | None = None,
) -> CheckpointInfo | None:
    """
    Persist a prediction snapshot from an existing simulation summary.

    Returns None if snapshot already exists (unless force=True).
    """
    checkpoint = resolve_checkpoint(override=checkpoint_override)
    if snapshot_exists(checkpoint.snapshot_id) and not force:
        return None

    captured_at = snapshot_date or date.today().isoformat()
    evolution_rows = rows_from_tournament_summary(summary, checkpoint, captured_at)
    pair_evo, pair_rows = rows_from_pairs(
        summary.winner_runner_up_pairs, checkpoint, captured_at
    )
    evolution_rows.extend(pair_evo)

    groups_to_run: list[str] = []
    if include_groups:
        groups_to_run = groups_filter if groups_filter is not None else list(GROUPS.keys())
        group_predictor = GroupPositionPredictor(config)
        for group in groups_to_run:
            group_summary = group_predictor.predict_group(
                group, n_simulations=group_simulations, seed=config.random_seed
            )
            evolution_rows.extend(
                rows_from_group_summary(group, group_summary, checkpoint, captured_at)
            )

    meta_row = {
        "snapshot_id": checkpoint.snapshot_id,
        "snapshot_date": captured_at,
        "checkpoint": checkpoint.checkpoint,
        "matches_completed": checkpoint.matches_completed,
        "last_result_date": checkpoint.last_result_date,
        "n_simulations": config.n_simulations,
        "group_simulations": group_simulations if groups_to_run else 0,
        "notes": checkpoint.label,
    }

    if force and snapshot_exists(checkpoint.snapshot_id):
        _remove_snapshot(checkpoint.snapshot_id)

    _append_rows(DEFAULT_SNAPSHOTS_PATH, [meta_row], list(meta_row.keys()))
    if evolution_rows:
        _append_rows(DEFAULT_EVOLUTION_PATH, evolution_rows, list(evolution_rows[0].keys()))
    if pair_rows:
        _append_rows(DEFAULT_PAIRS_LOG_PATH, pair_rows, list(pair_rows[0].keys()))

    return checkpoint


def _remove_snapshot(snapshot_id: str) -> None:
    for path, col in [
        (DEFAULT_SNAPSHOTS_PATH, "snapshot_id"),
        (DEFAULT_EVOLUTION_PATH, "snapshot_id"),
        (DEFAULT_PAIRS_LOG_PATH, "snapshot_id"),
    ]:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        df = df[df[col] != snapshot_id]
        df.to_csv(path, index=False)


def import_snapshot_from_output(
    output_dir: Path | str = OUTPUT_DIR,
    checkpoint_override: str | None = None,
    snapshot_date: str | None = None,
    force: bool = False,
    n_simulations: int = 10_000,
) -> CheckpointInfo | None:
    """Bootstrap a snapshot from existing monte_carlo CSV outputs."""
    output_dir = Path(output_dir)
    checkpoint = resolve_checkpoint(override=checkpoint_override)
    if snapshot_exists(checkpoint.snapshot_id) and not force:
        return None
    if force and snapshot_exists(checkpoint.snapshot_id):
        _remove_snapshot(checkpoint.snapshot_id)

    first_second_path = output_dir / "first_second_probabilities.csv"
    stage_path = output_dir / "stage_probabilities.csv"
    pairs_path = output_dir / "winner_runner_up_pairs.csv"
    if not first_second_path.exists():
        raise FileNotFoundError(f"Missing {first_second_path}")

    captured_at = snapshot_date or date.today().isoformat()
    evolution_rows: list[dict] = []

    first_second = pd.read_csv(first_second_path)
    for _, row in first_second.iterrows():
        team = str(row["team"])
        for metric, col in [
            ("p_win", "p_first"),
            ("p_runner_up", "p_second"),
            ("p_podium", "p_podium"),
        ]:
            evolution_rows.append(
                _evolution_row(
                    checkpoint.snapshot_id,
                    captured_at,
                    checkpoint.checkpoint,
                    checkpoint.matches_completed,
                    "tournament",
                    team,
                    metric,
                    float(row[col]),
                )
            )

    if stage_path.exists():
        stages = pd.read_csv(stage_path)
        for _, row in stages.iterrows():
            team = str(row["team"])
            for metric in STAGE_METRICS:
                if metric in row and pd.notna(row[metric]):
                    evolution_rows.append(
                        _evolution_row(
                            checkpoint.snapshot_id,
                            captured_at,
                            checkpoint.checkpoint,
                            checkpoint.matches_completed,
                            "tournament",
                            team,
                            metric,
                            float(row[metric]),
                        )
                    )

    pair_rows: list[dict] = []
    if pairs_path.exists():
        pairs_df = pd.read_csv(pairs_path)
        pair_evo, pair_rows = rows_from_pairs(pairs_df, checkpoint, captured_at)
        evolution_rows.extend(pair_evo)

    meta_row = {
        "snapshot_id": checkpoint.snapshot_id,
        "snapshot_date": captured_at,
        "checkpoint": checkpoint.checkpoint,
        "matches_completed": checkpoint.matches_completed,
        "last_result_date": checkpoint.last_result_date,
        "n_simulations": n_simulations,
        "group_simulations": 0,
        "notes": f"{checkpoint.label} (imported from output CSVs)",
    }

    _append_rows(DEFAULT_SNAPSHOTS_PATH, [meta_row], list(meta_row.keys()))
    if evolution_rows:
        _append_rows(DEFAULT_EVOLUTION_PATH, evolution_rows, list(evolution_rows[0].keys()))
    if pair_rows:
        _append_rows(DEFAULT_PAIRS_LOG_PATH, pair_rows, list(pair_rows[0].keys()))

    return checkpoint


def capture_snapshot(
    config: SimulationConfig | None = None,
    checkpoint_override: str | None = None,
    include_groups: bool = True,
    group_simulations: int = 10_000,
    force: bool = False,
    snapshot_date: str | None = None,
) -> CheckpointInfo | None:
    """
    Run simulations and append a prediction snapshot for the current checkpoint.

    Returns None if snapshot already exists (unless force=True).
    """
    cfg = config or SimulationConfig(verbose=False)
    engine = MonteCarloEngine(cfg, refresh_external=False)
    summary = engine.run()
    return save_snapshot_from_summary(
        summary,
        cfg,
        checkpoint_override=checkpoint_override,
        include_groups=include_groups,
        group_simulations=group_simulations,
        force=force,
        snapshot_date=snapshot_date,
    )


def refresh_after_results(
    config: SimulationConfig | None = None,
    force: bool = False,
    run_evaluation: bool = True,
    group_simulations: int = 10_000,
    report_only: bool = False,
) -> RefreshSummary:
    """
    Post-results pipeline: re-simulate, snapshot, evaluate, and write evolution report.

    Call this after updating match_results.csv. Event collection runs automatically
    via refresh_predictions (Wikipedia cards + match_events_supplement.csv).
    """
    cfg = config or SimulationConfig(verbose=False)
    checkpoint = resolve_checkpoint()
    groups = groups_with_results()

    if report_only:
        report_path = save_evolution_report()
        return RefreshSummary(
            checkpoint=checkpoint,
            snapshot_created=False,
            evolution_report_path=report_path,
            matches_completed=checkpoint.matches_completed,
            groups_updated=groups,
        )

    need_snapshot = force or not snapshot_exists(checkpoint.snapshot_id)

    if cfg.verbose:
        print(f"Refreshing predictions at checkpoint: {checkpoint.label}")

    snapshot_created = False
    if need_snapshot:
        engine = MonteCarloEngine(cfg, refresh_external=False)
        if cfg.verbose:
            print(f"  Running {cfg.n_simulations:,} tournament simulations...")
            if groups:
                print(f"  Updating group probabilities for: {', '.join(groups)}")
        summary = engine.run()
        engine.save_results(summary)
        saved = save_snapshot_from_summary(
            summary,
            cfg,
            include_groups=bool(groups),
            groups_filter=groups,
            group_simulations=group_simulations,
            force=force,
        )
        snapshot_created = saved is not None
    elif cfg.verbose:
        print(f"  Snapshot `{checkpoint.snapshot_id}` exists — skipping re-simulation.")

    report_path = save_evolution_report()

    eval_path = None
    if run_evaluation:
        from .prediction_evaluator import (
            evaluate_predictions,
            load_predictions_log,
            save_evaluation,
        )

        results = load_completed_group_matches()
        predictions = load_predictions_log()
        if not results.empty and not predictions.empty:
            if cfg.verbose:
                print("  Evaluating logged match predictions...")
            eval_summary = evaluate_predictions(
                results=results,
                predictions=predictions,
                config=cfg,
            )
            if eval_summary.matches_evaluated > 0:
                eval_path, _ = save_evaluation(eval_summary)

    if cfg.verbose:
        print(f"  Evolution report: {report_path}")
        if snapshot_created:
            print(f"  New snapshot: {checkpoint.snapshot_id}")
        if eval_path:
            print(f"  Evaluation report: {eval_path}")

    return RefreshSummary(
        checkpoint=checkpoint,
        snapshot_created=snapshot_created,
        evolution_report_path=report_path,
        evaluation_report_path=eval_path,
        matches_completed=checkpoint.matches_completed,
        groups_updated=groups,
    )


def log_match_predictions(
    fixtures: list[dict],
    predictions: list[MatchPrediction],
    snapshot_date: str | None = None,
    path: Path | str = DEFAULT_MATCH_PREDICTIONS_LOG_PATH,
) -> int:
    """Append match predictions to the log (skips duplicates on date+match_num)."""
    if len(fixtures) != len(predictions):
        raise ValueError("fixtures and predictions length mismatch")

    path = Path(path)
    existing = load_predictions_log(path) if path.exists() else pd.DataFrame()
    logged_at = snapshot_date or date.today().isoformat()
    rows: list[dict] = []

    for fixture, pred in zip(fixtures, predictions, strict=True):
        key_mask = pd.Series(dtype=bool)
        if not existing.empty:
            key_mask = (existing["date"] == fixture.get("date", logged_at)) & (
                existing["match_num"] == fixture["match"]
            )
        if not existing.empty and key_mask.any():
            continue

        score, score_p = pred.most_likely_scorelines[0]
        rows.append(
            {
                "logged_at": logged_at,
                "date": fixture.get("date", logged_at),
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

    if not rows:
        return 0

    columns = list(rows[0].keys())
    _append_rows(path, rows, columns)
    return len(rows)


def load_predictions_log(path: Path | str = DEFAULT_MATCH_PREDICTIONS_LOG_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _pivot_metric(
    df: pd.DataFrame,
    category: str,
    metric: str,
    teams: list[str],
    group: str | None = None,
) -> pd.DataFrame:
    subset = df[(df["category"] == category) & (df["metric"] == metric)]
    if group is not None:
        subset = subset[subset["group"] == group]
    if subset.empty:
        return pd.DataFrame()

    order = (
        load_snapshots()
        .sort_values("matches_completed")[["snapshot_id", "snapshot_date", "checkpoint"]]
        .drop_duplicates("snapshot_id")
    )
    pivot = subset.pivot_table(
        index="team", columns="snapshot_id", values="value", aggfunc="first"
    )
    pivot = pivot.reindex(columns=order["snapshot_id"].tolist(), fill_value=float("nan"))
    pivot = pivot.reindex(teams)
    pivot.columns = [
        f"{sid} ({order.loc[order['snapshot_id'] == sid, 'snapshot_date'].iloc[0]})"
        for sid in pivot.columns
    ]
    return pivot


def format_evolution_report(
    evolution_path: Path | str = DEFAULT_EVOLUTION_PATH,
    snapshots_path: Path | str = DEFAULT_SNAPSHOTS_PATH,
    pairs_path: Path | str = DEFAULT_PAIRS_LOG_PATH,
) -> str:
    evolution = load_evolution(evolution_path)
    snapshots = load_snapshots(snapshots_path)
    pairs = load_pairs_log(pairs_path)

    lines = [
        "# Prediction Evolution",
        "",
        "How model forecasts changed from pre-opening through each completed round.",
        "",
        f"**Snapshots recorded**: {len(snapshots)}",
        f"**Last updated**: {_utc_now_iso()}",
        "",
    ]

    if snapshots.empty:
        lines.append("_No snapshots yet. Run `python -m wc2026_monte_carlo.snapshot_predictions`._")
        return "\n".join(lines)

    lines.extend(["## Checkpoints", "", "| Snapshot | Date | Matches played | Label |", "|----------|------|----------------|-------|"])
    for _, row in snapshots.sort_values("matches_completed").iterrows():
        lines.append(
            f"| `{row['snapshot_id']}` | {row['snapshot_date']} | "
            f"{int(row['matches_completed'])} | {row.get('notes', row['checkpoint'])} |"
        )
    lines.append("")

    if evolution.empty:
        return "\n".join(lines)

    top_teams = (
        evolution[(evolution["category"] == "tournament") & (evolution["metric"] == "p_win")]
        .sort_values(["snapshot_id", "value"], ascending=[True, False])
        .groupby("snapshot_id")
        .head(10)["team"]
        .unique()
        .tolist()
    )

    lines.extend(["## Tournament winner probability", ""])
    win_pivot = _pivot_metric(evolution, "tournament", "p_win", top_teams)
    if not win_pivot.empty:
        header = "| Team | " + " | ".join(win_pivot.columns) + " |"
        sep = "|------|" + "|".join(["--------"] * len(win_pivot.columns)) + "|"
        lines.extend([header, sep])
        for team, row in win_pivot.iterrows():
            cells = " | ".join(
                f"{v * 100:.1f}%" if pd.notna(v) else "—" for v in row.values
            )
            lines.append(f"| {team} | {cells} |")
        lines.append("")

    lines.extend(["## Tournament runner-up probability", ""])
    ru_pivot = _pivot_metric(evolution, "tournament", "p_runner_up", top_teams)
    if not ru_pivot.empty:
        header = "| Team | " + " | ".join(ru_pivot.columns) + " |"
        sep = "|------|" + "|".join(["--------"] * len(ru_pivot.columns)) + "|"
        lines.extend([header, sep])
        for team, row in ru_pivot.iterrows():
            cells = " | ".join(
                f"{v * 100:.1f}%" if pd.notna(v) else "—" for v in row.values
            )
            lines.append(f"| {team} | {cells} |")
        lines.append("")

    played_groups = sorted(evolution[evolution["category"] == "group"]["group"].dropna().unique())
    for group in played_groups:
        group_teams = GROUPS.get(group, [])
        if not group_teams:
            continue
        lines.extend([f"## Group {group} — P(1st / 2nd / 3rd / Top 2)", ""])
        for metric, label in [
            ("p_first", "P(1st)"),
            ("p_second", "P(2nd)"),
            ("p_third", "P(3rd)"),
            ("p_top_two", "P(Top 2)"),
        ]:
            pivot = _pivot_metric(evolution, "group", metric, group_teams, group=group)
            if pivot.empty:
                continue
            lines.append(f"### {label}")
            lines.append("")
            header = "| Team | " + " | ".join(pivot.columns) + " |"
            sep = "|------|" + "|".join(["--------"] * len(pivot.columns)) + "|"
            lines.extend([header, sep])
            for team, row in pivot.iterrows():
                cells = " | ".join(
                    f"{v * 100:.1f}%" if pd.notna(v) else "—" for v in row.values
                )
                lines.append(f"| {team} | {cells} |")
            lines.append("")

    if not pairs.empty:
        lines.extend(["## Top winner / runner-up pairs", ""])
        for snapshot_id in snapshots.sort_values("matches_completed")["snapshot_id"]:
            snap_pairs = pairs[pairs["snapshot_id"] == snapshot_id].head(5)
            if snap_pairs.empty:
                continue
            snap_date = snapshots.loc[
                snapshots["snapshot_id"] == snapshot_id, "snapshot_date"
            ].iloc[0]
            lines.append(f"### `{snapshot_id}` ({snap_date})")
            lines.append("")
            lines.append("| Winner | Runner-up | Probability |")
            lines.append("|--------|-----------|-------------|")
            for _, row in snap_pairs.iterrows():
                lines.append(
                    f"| {row['winner']} | {row['runner_up']} | "
                    f"{row['probability'] * 100:.2f}% |"
                )
            lines.append("")

    lines.extend(
        [
            "## How to update",
            "",
            "After adding results to `simulations/data/match_results.csv`:",
            "",
            "```bash",
            "cd simulations && source .venv/bin/activate",
            "python -m wc2026_monte_carlo.refresh_predictions",
            "```",
            "",
            "That command re-simulates, captures a new snapshot (if the checkpoint changed),",
            "evaluates logged match predictions, and regenerates this report automatically.",
        ]
    )
    return "\n".join(lines)


def save_evolution_report(
    output_path: Path | str = OUTPUT_DIR / "prediction_evolution.md",
    **kwargs,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_evolution_report(**kwargs), encoding="utf-8")
    return output_path