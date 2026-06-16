# World Cup 2026 Match Predictions

Daily match-by-match forecasts using the market-calibrated Dixon-Coles model (Elo + squad value + xG + recent form + club chemistry + injuries + match events + per-match odds blend + in-tournament form, anchored to betting odds).

**Updated**: June 16, 2026 (auto-generated)

*Source: `simulations/data/match_predictions_log.csv` · Regenerate: `python -m wc2026_monte_carlo predict`*

---

## Prediction Performance

- **Matches evaluated**: 16
- **Winner accuracy**: 43.8%
- **3-way accuracy**: 43.8%
- **Mean Brier (3-way)**: 0.6447

### By confidence tier

| Tier | N | Winner accuracy | 3-way accuracy |
|------|---|-----------------|----------------|
| Moderate | 6 | 50.0% | 50.0% |
| Low | 10 | 40.0% | 40.0% |

## June 17, 2026 — Match Predictions

### Match 21: Portugal vs DR Congo

- Kickoff: 1:00 PM EDT | NRG Stadium
- Group K
- xG: 1.97 — 1.05
- P(Portugal win): 57.9%
- P(Draw): 25.3%
- P(DR Congo win): 16.8%
- Predicted winner: **Portugal** (Moderate confidence)
- Most likely score: 2-1 (10.4%)

### Match 22: England vs Croatia

- Kickoff: 4:00 PM EDT | AT&T Stadium
- Group L
- xG: 2.11 — 0.99
- P(England win): 55.8%
- P(Draw): 25.6%
- P(Croatia win): 18.6%
- Predicted winner: **England** (Moderate confidence)
- Most likely score: 2-0 (10.3%)

### Match 23: Ghana vs Panama

- Kickoff: 7:00 PM EDT | BMO Field
- Group L
- xG: 1.89 — 1.09
- P(Ghana win): 50.2%
- P(Draw): 27.7%
- P(Panama win): 22.1%
- Predicted winner: **Ghana** (Low confidence)
- Most likely score: 1-1 (11.0%)

### Match 24: Uzbekistan vs Colombia

- Kickoff: 10:00 PM EDT | Estadio Azteca
- Group K
- xG: 2.50 — 0.77
- P(Uzbekistan win): 57.0%
- P(Draw): 21.8%
- P(Colombia win): 21.2%
- Predicted winner: **Uzbekistan** (Moderate confidence)
- Most likely score: 2-0 (12.5%)

---

## Completed Results

### June 15, 2026

| Match | Result | Model pick | Correct? |
|-------|--------|------------|----------|
| Saudi Arabia vs Uruguay | 1–1 | Saudi Arabia (42%) | ✗ |
| Spain vs Cape Verde | 0–0 | Spain (63%) | ✗ |
| Iran vs New Zealand | 2–2 | Iran (58%) | ✗ |
| Belgium vs Egypt | 1–1 | Belgium (49%) | ✗ |

### June 14, 2026

| Match | Result | Model pick | Correct? |
|-------|--------|------------|----------|
| Ivory Coast vs Ecuador | 1–0 | Ivory Coast (60%) | ✓ |
| Germany vs Curaçao | 7–1 | Germany (55%) | ✓ |
| Netherlands vs Japan | 2–2 | Netherlands (45%) | ✗ |
| Sweden vs Tunisia | 5–1 | Sweden (53%) | ✓ |

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