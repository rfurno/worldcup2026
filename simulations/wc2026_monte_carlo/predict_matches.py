"""CLI to generate match predictions for a given date."""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

from .match_predictor import MatchPredictor

# Official Group A Matchday 1 fixtures (June 11, 2026)
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Predict World Cup matches for a date")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date (YYYY-MM-DD). Default: tomorrow.",
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
    for fixture in fixtures:
        pred = predictor.predict(
            fixture["home"],
            fixture["away"],
            venue=fixture.get("venue"),
            neutral=fixture.get("neutral", False),
        )
        print(format_prediction(fixture, pred))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())