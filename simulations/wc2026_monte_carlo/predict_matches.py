"""Fixture list and formatting; CLI delegates to workflow.predict."""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

from .group_position_predictor import GroupPositionPredictor

# Official matchday fixtures (FIFA schedule)
FIXTURES_BY_DATE: dict[str, list[dict]] = {
    "2026-06-11": [
        {
            "home": "Mexico",
            "away": "South Africa",
            "venue": "Mexico City",
            "kickoff": "1:00 PM CDT",
            "stadium": "Estadio Azteca",
            "group": "A",
            "match": 1,
            "neutral": False,
        },
        {
            "home": "South Korea",
            "away": "Czechia",
            "venue": "Guadalajara",
            "kickoff": "8:00 PM CDT",
            "stadium": "Estadio Akron",
            "group": "A",
            "match": 2,
            "neutral": True,
        },
    ],
    "2026-06-12": [
        {
            "home": "Canada",
            "away": "Bosnia and Herzegovina",
            "venue": "Toronto",
            "kickoff": "3:00 PM EDT",
            "stadium": "BMO Field",
            "group": "B",
            "match": 3,
            "neutral": False,
        },
        {
            "home": "United States",
            "away": "Paraguay",
            "venue": "Los Angeles",
            "kickoff": "6:00 PM PDT",
            "stadium": "SoFi Stadium",
            "group": "D",
            "match": 4,
            "neutral": False,
        },
    ],
    "2026-06-14": [
        {
            "home": "Germany",
            "away": "Curaçao",
            "venue": "Houston",
            "kickoff": "12:00 PM CDT",
            "stadium": "NRG Stadium",
            "group": "E",
            "match": 10,
            "neutral": True,
        },
        {
            "home": "Netherlands",
            "away": "Japan",
            "venue": "Dallas",
            "kickoff": "3:00 PM CDT",
            "stadium": "AT&T Stadium",
            "group": "F",
            "match": 11,
            "neutral": True,
        },
        {
            "home": "Ivory Coast",
            "away": "Ecuador",
            "venue": "Philadelphia",
            "kickoff": "7:00 PM EDT",
            "stadium": "Lincoln Financial Field",
            "group": "E",
            "match": 9,
            "neutral": True,
        },
        {
            "home": "Sweden",
            "away": "Tunisia",
            "venue": "Monterrey",
            "kickoff": "8:00 PM CDT",
            "stadium": "Estadio BBVA",
            "group": "F",
            "match": 12,
            "neutral": True,
        },
    ],
    "2026-06-15": [
        {
            "home": "Spain",
            "away": "Cape Verde",
            "venue": "Atlanta",
            "kickoff": "12:00 PM EDT",
            "stadium": "Mercedes-Benz Stadium",
            "group": "H",
            "match": 14,
            "neutral": True,
        },
        {
            "home": "Belgium",
            "away": "Egypt",
            "venue": "Seattle",
            "kickoff": "3:00 PM EDT",
            "stadium": "Lumen Field",
            "group": "G",
            "match": 16,
            "neutral": True,
        },
        {
            "home": "Saudi Arabia",
            "away": "Uruguay",
            "venue": "Miami",
            "kickoff": "6:00 PM EDT",
            "stadium": "Hard Rock Stadium",
            "group": "H",
            "match": 13,
            "neutral": True,
        },
        {
            "home": "Iran",
            "away": "New Zealand",
            "venue": "Los Angeles",
            "kickoff": "9:00 PM EDT",
            "stadium": "SoFi Stadium",
            "group": "G",
            "match": 15,
            "neutral": True,
        },
    ],
    "2026-06-16": [
        {
            "home": "France",
            "away": "Senegal",
            "venue": "New York",
            "kickoff": "3:00 PM EDT",
            "stadium": "MetLife Stadium",
            "group": "I",
            "match": 17,
            "neutral": True,
        },
        {
            "home": "Iraq",
            "away": "Norway",
            "venue": "Boston",
            "kickoff": "6:00 PM EDT",
            "stadium": "Gillette Stadium",
            "group": "I",
            "match": 18,
            "neutral": True,
        },
        {
            "home": "Argentina",
            "away": "Algeria",
            "venue": "Kansas City",
            "kickoff": "9:00 PM EDT",
            "stadium": "Arrowhead Stadium",
            "group": "J",
            "match": 19,
            "neutral": True,
        },
        {
            "home": "Austria",
            "away": "Jordan",
            "venue": "San Francisco",
            "kickoff": "9:00 PM PDT",
            "stadium": "Levi's Stadium",
            "group": "J",
            "match": 20,
            "neutral": True,
        },
    ],
    "2026-06-17": [
        {
            "home": "Portugal",
            "away": "DR Congo",
            "venue": "Houston",
            "kickoff": "1:00 PM EDT",
            "stadium": "NRG Stadium",
            "group": "K",
            "match": 21,
            "neutral": True,
        },
        {
            "home": "England",
            "away": "Croatia",
            "venue": "Dallas",
            "kickoff": "4:00 PM EDT",
            "stadium": "AT&T Stadium",
            "group": "L",
            "match": 22,
            "neutral": True,
        },
        {
            "home": "Ghana",
            "away": "Panama",
            "venue": "Toronto",
            "kickoff": "7:00 PM EDT",
            "stadium": "BMO Field",
            "group": "L",
            "match": 23,
            "neutral": True,
        },
        {
            "home": "Uzbekistan",
            "away": "Colombia",
            "venue": "Mexico City",
            "kickoff": "10:00 PM EDT",
            "stadium": "Estadio Azteca",
            "group": "K",
            "match": 24,
            "neutral": True,
        },
    ],
    "2026-06-13": [
        {
            "home": "Qatar",
            "away": "Switzerland",
            "venue": "San Francisco",
            "kickoff": "12:00 PM PDT",
            "stadium": "Levi's Stadium",
            "group": "B",
            "match": 8,
            "neutral": True,
        },
        {
            "home": "Brazil",
            "away": "Morocco",
            "venue": "New York",
            "kickoff": "6:00 PM EDT",
            "stadium": "MetLife Stadium",
            "group": "C",
            "match": 7,
            "neutral": True,
        },
        {
            "home": "Haiti",
            "away": "Scotland",
            "venue": "Boston",
            "kickoff": "9:00 PM EDT",
            "stadium": "Gillette Stadium",
            "group": "C",
            "match": 5,
            "neutral": True,
        },
        {
            "home": "Australia",
            "away": "Turkey",
            "venue": "Vancouver",
            "kickoff": "9:00 PM PDT",
            "stadium": "BC Place",
            "group": "D",
            "match": 6,
            "neutral": True,
        },
    ],
}


def fixtures_for(target: date) -> list[dict]:
    return FIXTURES_BY_DATE.get(target.isoformat(), [])


def format_prediction(fixture: dict, pred) -> str:
    lines = [
        f"### Match {fixture['match']}: {pred.home} vs {pred.away}",
        "",
        f"- Kickoff: {fixture['kickoff']} | {fixture['stadium']}",
        f"- Group {fixture['group']}",
        f"- xG: {pred.expected_home_goals:.2f} — {pred.expected_away_goals:.2f}",
        f"- P({pred.home} win): {pred.home_win_prob * 100:.1f}%",
        f"- P(Draw): {pred.draw_prob * 100:.1f}%",
        f"- P({pred.away} win): {pred.away_win_prob * 100:.1f}%",
        f"- Predicted winner: **{pred.predicted_winner}** ({pred.confidence} confidence)",
        f"- Most likely score: {pred.most_likely_scorelines[0][0]} ({pred.most_likely_scorelines[0][1] * 100:.1f}%)",
    ]
    return "\n".join(lines)


def format_group_positions(summary) -> str:
    lines = [
        f"## Group {summary.group} — First/Second Place Probabilities",
        "",
        "| Team | P(1st) | P(2nd) | P(Top 2) | P(3rd) | P(4th) |",
        "|------|--------|--------|----------|--------|--------|",
    ]
    for t in summary.teams:
        lines.append(
            f"| {t.team} | {t.p_first * 100:.1f}% | {t.p_second * 100:.1f}% | "
            f"{t.p_top_two * 100:.1f}% | {t.p_third * 100:.1f}% | {t.p_fourth * 100:.1f}% |"
        )
    lines.extend(["", "**Most likely 1st–2nd pairings**", ""])
    for first, second, prob in summary.most_likely_top_two_pairs[:5]:
        lines.append(f"- {first} / {second}: {prob * 100:.1f}%")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="[deprecated] Use: python -m wc2026_monte_carlo predict",
    )
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--group-positions", action="store_true")
    args = parser.parse_args(argv)

    from .workflow import run_predict

    target = (
        date.fromisoformat(args.date)
        if args.date
        else date.today() + timedelta(days=1)
    )
    try:
        run_predict(target)
    except ValueError as exc:
        print(exc)
        return 1

    if args.group_positions:
        fixtures = fixtures_for(target)
        groups = sorted({f["group"] for f in fixtures})
        predictor = GroupPositionPredictor()
        for group in groups:
            print(format_group_positions(predictor.predict_group(group)))
            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())