"""CLI to generate match predictions for a given date."""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

from .group_position_predictor import GroupPositionPredictor
from .match_predictor import MatchPredictor

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
    parser = argparse.ArgumentParser(description="Predict World Cup matches for a date")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date (YYYY-MM-DD). Default: tomorrow.",
    )
    parser.add_argument(
        "--group-positions",
        action="store_true",
        help="Include full group first/second place probabilities",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Append match predictions to match_predictions_log.csv",
    )
    args = parser.parse_args(argv)

    if args.date:
        target = date.fromisoformat(args.date)
    else:
        target = date.today() + timedelta(days=1)

    fixtures = fixtures_for(target)
    if not fixtures:
        print(f"No fixtures loaded for {target.isoformat()}")
        return 1

    predictor = MatchPredictor()
    print(f"# Match Predictions — {target.strftime('%B %d, %Y')}\n")
    predictions = []
    for fixture in fixtures:
        fixture = {**fixture, "date": target.isoformat()}
        pred = predictor.predict(
            fixture["home"],
            fixture["away"],
            venue=fixture.get("venue"),
            neutral=fixture.get("neutral", False),
        )
        predictions.append(pred)
        print(format_prediction(fixture, pred))
        print()

    if args.log:
        from .prediction_tracker import log_match_predictions

        logged = log_match_predictions(fixtures, predictions, snapshot_date=target.isoformat())
        if logged:
            print(f"Logged {logged} match prediction(s) to match_predictions_log.csv\n")

    groups = sorted({f["group"] for f in fixtures})
    if args.group_positions or groups:
        group_predictor = GroupPositionPredictor()
        for group in groups:
            summary = group_predictor.predict_group(group)
            print(format_group_positions(summary))
            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())