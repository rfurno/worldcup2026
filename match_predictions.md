# World Cup 2026 Match Predictions

Daily match-by-match forecasts using the market-calibrated Dixon-Coles model (Elo + squad value + xG + recent form + club chemistry + injuries + match events + per-match odds blend + in-tournament form, anchored to betting odds).

**Updated**: June 14, 2026 (auto-generated)

*Source: `simulations/data/match_predictions_log.csv` · Regenerate: `python -m wc2026_monte_carlo predict`*

---

## Prediction Performance

- **Matches evaluated**: 8
- **Winner accuracy**: 50.0%
- **3-way accuracy**: 50.0%
- **Mean Brier (3-way)**: 0.6256

### By confidence tier

| Tier | N | Winner accuracy | 3-way accuracy |
|------|---|-----------------|----------------|
| Moderate | 3 | 66.7% | 66.7% |
| Low | 5 | 40.0% | 40.0% |

## June 15, 2026 — Match Predictions

### Match 13: Saudi Arabia vs Uruguay

- Kickoff: 6:00 PM EDT | Hard Rock Stadium
- Group H
- xG: 1.99 — 1.03
- P(Saudi Arabia win): 41.8%
- P(Draw): 26.4%
- P(Uruguay win): 31.7%
- Predicted winner: **Saudi Arabia** (Low confidence)
- Most likely score: 2-1 (10.4%)

### Match 14: Spain vs Cape Verde

- Kickoff: 12:00 PM EDT | Mercedes-Benz Stadium
- Group H
- xG: 2.00 — 1.06
- P(Spain win): 62.9%
- P(Draw): 23.0%
- P(Cape Verde win): 14.1%
- Predicted winner: **Spain** (Moderate confidence)
- Most likely score: 2-1 (10.4%)

### Match 15: Iran vs New Zealand

- Kickoff: 9:00 PM EDT | SoFi Stadium
- Group G
- xG: 2.03 — 1.01
- P(Iran win): 58.0%
- P(Draw): 25.3%
- P(New Zealand win): 16.7%
- Predicted winner: **Iran** (Moderate confidence)
- Most likely score: 2-1 (10.3%)

### Match 16: Belgium vs Egypt

- Kickoff: 3:00 PM EDT | Lumen Field
- Group G
- xG: 1.52 — 1.33
- P(Belgium win): 48.5%
- P(Draw): 27.3%
- P(Egypt win): 24.2%
- Predicted winner: **Belgium** (Low confidence)
- Most likely score: 1-1 (12.2%)

---

## Completed Results

### June 13, 2026

| Match | Result | Model pick | Correct? |
|-------|--------|------------|----------|
| Haiti vs Scotland | 0–1 | Haiti (53%) | ✗ |
| Australia vs Turkey | 2–0 | Australia (51%) | ✓ |
| Brazil vs Morocco | 1–1 | Brazil (53%) | ✗ |
| Qatar vs Switzerland | 1–1 | Qatar (58%) | ✗ |

### June 12, 2026

| Match | Result | Model pick | Correct? |
|-------|--------|------------|----------|
| Canada vs Bosnia and Herzegovina | 1–1 | Bosnia and Herzegovina (44%) | ✗ |
| United States vs Paraguay | 4–1 | United States (57%) | ✓ |

### June 11, 2026

| Match | Result | Model pick | Correct? |
|-------|--------|------------|----------|
| Mexico vs South Africa | 2–0 | Mexico (47%) | ✓ |
| South Korea vs Czechia | 2–1 | South Korea (60%) | ✓ |

---

*Workflow: `add-results` after matches · `predict` before the next day*