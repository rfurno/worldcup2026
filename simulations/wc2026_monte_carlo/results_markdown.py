"""Auto-generate match-results.md from match_results.csv."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from .config import DEFAULT_MATCH_RESULTS_PATH, MATCH_RESULTS_MD_PATH
from .group_results import load_completed_group_matches
from .predict_matches import FIXTURES_BY_DATE


def _fmt_date_header(iso_date: str) -> str:
    return date.fromisoformat(iso_date).strftime("%B %d, %Y")


def _fixture_lookup() -> dict[tuple[str, int], dict]:
    lookup: dict[tuple[str, int], dict] = {}
    for day, fixtures in FIXTURES_BY_DATE.items():
        for fixture in fixtures:
            lookup[(day, fixture["match"])] = {**fixture, "date": day}
    return lookup


def update_match_results_md(
    results_path: Path | str = DEFAULT_MATCH_RESULTS_PATH,
    output_path: Path | str = MATCH_RESULTS_MD_PATH,
) -> Path:
    output_path = Path(output_path)
    results = load_completed_group_matches(results_path)
    fixtures = _fixture_lookup()
    today = date.today().isoformat()

    lines = [
        "# World Cup 2026 Match Results",
        "",
        "Official results for completed group-stage matches.",
        "",
        f"**Updated**: {_fmt_date_header(today)} (auto-generated from "
        "`simulations/data/match_results.csv`)",
        "",
        "*Add results: `python -m wc2026_monte_carlo add-results ...`*",
        "",
        "---",
        "",
    ]

    if results.empty:
        lines.append("_No completed matches yet._")
    else:
        for day in sorted(results["date"].astype(str).unique(), reverse=True):
            day_df = results[results["date"].astype(str) == day].sort_values("match_num")
            groups = ", ".join(sorted(day_df["group"].astype(str).unique()))
            lines.append(f"## {_fmt_date_header(day)} — Group(s) {groups}")
            lines.append("")
            lines.append("| Match | Home | Away | Score | Group | Venue |")
            lines.append("|-------|------|------|-------|-------|-------|")
            for _, row in day_df.iterrows():
                key = (day, int(row["match_num"]))
                meta = fixtures.get(key, {})
                venue = row.get("venue") or meta.get("venue") or "—"
                score = f"{int(row['home_goals'])}–{int(row['away_goals'])}"
                lines.append(
                    f"| {int(row['match_num'])} | {row['home']} | {row['away']} | "
                    f"{score} | {row['group']} | {venue} |"
                )
            lines.append("")

    lines.extend(
        [
            "---",
            "",
            "*Data: `simulations/data/match_results.csv`*",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path