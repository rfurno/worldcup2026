# World Cup 2026 Match Predictions

Daily match-by-match forecasts using the market-calibrated Dixon-Coles model (Elo + squad value + xG + recent form + club chemistry + injuries + match events, anchored to betting odds).

**Updated**: June 13, 2026 (forecasts for June 13–14)

*Source: `simulations/data/match_predictions_log.csv` · Regenerate: `python -m wc2026_monte_carlo.predict_matches --date YYYY-MM-DD --log`*

---

## June 14, 2026 — Groups D, E & F (Matchday 1)

Five fixtures. Australia vs Turkey kicks off last in Vancouver (FIFA schedule: **June 14**, not June 13).

### Match 6: Australia vs Turkey

| Field | Detail |
|-------|--------|
| **Date** | June 14, 2026 |
| **Kickoff** | 9:00 PM PDT (UTC−7) |
| **Venue** | BC Place, Vancouver |
| **Group** | D |
| **Context** | Neutral site. USA beat Paraguay 4–1 on June 12; Turkey still group favorite. |

**Model prediction**

| Outcome | Probability |
|---------|-------------|
| Australia win | **50.7%** |
| Draw | 24.0% |
| Turkey win | 25.3% |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | Australia 1.73 — Turkey 1.16 |
| Most likely scoreline | **1-1** (11.1%) |
| Other likely scores | 2-1 (9.5%), 1-0 (9.4%), 2-0 (8.4%), 1-2 (6.5%) |
| Predicted winner | **Australia** |
| Confidence | Low |

**Recommendation**: Coin-flip game — lean Australia on xG, but Turkey can absolutely take points.

---

### Match 9: Ivory Coast vs Ecuador

| Field | Detail |
|-------|--------|
| **Date** | June 14, 2026 |
| **Kickoff** | 7:00 PM EDT (UTC−4) |
| **Venue** | Lincoln Financial Field, Philadelphia |
| **Group** | E |

**Model prediction**

| Outcome | Probability |
|---------|-------------|
| Ivory Coast win | **54.2%** |
| Draw | 23.0% |
| Ecuador win | 22.8% |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | Ivory Coast 1.84 — Ecuador 1.12 |
| Most likely scoreline | **1-1** (10.6%) |
| Predicted winner | **Ivory Coast** |
| Confidence | Low |

---

### Match 10: Germany vs Curaçao

| Field | Detail |
|-------|--------|
| **Date** | June 14, 2026 |
| **Kickoff** | 12:00 PM CDT (UTC−5) |
| **Venue** | NRG Stadium, Houston |
| **Group** | E |

**Model prediction**

| Outcome | Probability |
|---------|-------------|
| Germany win | **54.4%** |
| Draw | 22.9% |
| Curaçao win | 22.7% |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | Germany 1.85 — Curaçao 1.12 |
| Most likely scoreline | **1-1** (10.5%) |
| Predicted winner | **Germany** |
| Confidence | Low |

---

### Match 11: Netherlands vs Japan

| Field | Detail |
|-------|--------|
| **Date** | June 14, 2026 |
| **Kickoff** | 3:00 PM CDT (UTC−5) |
| **Venue** | AT&T Stadium, Dallas |
| **Group** | F |

**Model prediction**

| Outcome | Probability |
|---------|-------------|
| Netherlands win | **47.5%** |
| Draw | 24.5% |
| Japan win | 28.0% |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | Netherlands 1.65 — Japan 1.21 |
| Most likely scoreline | **1-1** (11.3%) |
| Predicted winner | **Netherlands** |
| Confidence | Low |

**Note**: Effectively a toss-up — Japan win probability nearly matches the Dutch edge.

---

### Match 12: Sweden vs Tunisia

| Field | Detail |
|-------|--------|
| **Date** | June 14, 2026 |
| **Kickoff** | 8:00 PM CDT (UTC−5) |
| **Venue** | Estadio BBVA, Monterrey |
| **Group** | F |

**Model prediction**

| Outcome | Probability |
|---------|-------------|
| Sweden win | **58.8%** |
| Draw | 21.8% |
| Tunisia win | 19.4% |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | Sweden 1.96 — Tunisia 1.04 |
| Most likely scoreline | **1-1** (10.0%) |
| Predicted winner | **Sweden** |
| Confidence | Moderate |

---

## Group D — Standings Probabilities *(after USA 4–1 Paraguay)*

| Team | P(1st) | P(2nd) | P(Top 2) | P(3rd) | P(4th) |
|------|--------|--------|----------|--------|--------|
| Turkey | **39.9%** | 27.7% | **67.6%** | 18.1% | 14.3% |
| United States | 28.8% | 32.6% | 61.4% | 27.2% | 11.4% |
| Australia | 22.5% | 22.8% | 45.4% | 24.8% | 29.9% |
| Paraguay | 8.8% | 16.9% | 25.6% | 30.0% | 44.4% |

**Most likely 1st–2nd pairings:** Turkey/United States (22.3%), United States/Turkey (13.8%), Turkey/Australia (13.5%), Australia/Turkey (11.8%)

---

## Group E — Standings Probabilities *(pre–Matchday 1)*

| Team | P(1st) | P(2nd) | P(Top 2) | P(3rd) | P(4th) |
|------|--------|--------|----------|--------|--------|
| Germany | **42.7%** | 26.3% | **69.0%** | 18.7% | 12.3% |
| Ecuador | 23.9% | 27.0% | 50.8% | 25.3% | 23.9% |
| Ivory Coast | 16.9% | 23.7% | 40.6% | 28.0% | 31.4% |
| Curaçao | 16.5% | 23.0% | 39.5% | 28.1% | 32.4% |

**Most likely 1st–2nd pairings:** Germany/Ecuador (16.0%), Germany/Curaçao (13.6%), Germany/Ivory Coast (13.2%)

---

## Group F — Standings Probabilities *(pre–Matchday 1)*

| Team | P(1st) | P(2nd) | P(Top 2) | P(3rd) | P(4th) |
|------|--------|--------|----------|--------|--------|
| Tunisia | **38.8%** | 27.6% | **66.4%** | 19.9% | 13.6% |
| Netherlands | 28.2% | 28.3% | 56.5% | 24.2% | 19.3% |
| Sweden | 17.3% | 22.3% | 39.6% | 27.5% | 32.9% |
| Japan | 15.7% | 21.8% | 37.5% | 28.3% | 34.2% |

**Most likely 1st–2nd pairings:** Tunisia/Netherlands (17.7%), Netherlands/Tunisia (13.0%), Tunisia/Japan (10.7%)

---

## June 14 Summary

| Match | Prediction | xG | Confidence |
|-------|------------|-----|------------|
| Ivory Coast vs Ecuador | **Ivory Coast** (54%) | 1.84–1.12 | Low |
| Germany vs Curaçao | **Germany** (54%) | 1.85–1.12 | Low |
| Sweden vs Tunisia | **Sweden** (59%) | 1.96–1.04 | Moderate |
| Australia vs Turkey | **Australia** (51%) | 1.73–1.16 | Low |
| Netherlands vs Japan | **Netherlands** (48%) | 1.65–1.21 | Low |

---

## June 13, 2026 — Groups B & C (Matchday 1)

Three fixtures today. Australia vs Turkey is **not** on this date.

### Match 8: Qatar vs Switzerland

| Field | Detail |
|-------|--------|
| **Date** | June 13, 2026 |
| **Kickoff** | 12:00 PM PDT (UTC−7) |
| **Venue** | Levi's Stadium, San Francisco |
| **Group** | B |

**Model prediction**

| Outcome | Probability |
|---------|-------------|
| Qatar win | **58.0%** |
| Draw | 22.1% |
| Switzerland win | 19.9% |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | Qatar 1.94 — Switzerland 1.04 |
| Most likely scoreline | **1-1** (10.2%) |
| Predicted winner | **Qatar** |
| Confidence | Moderate |

---

### Match 7: Brazil vs Morocco

| Field | Detail |
|-------|--------|
| **Date** | June 13, 2026 |
| **Kickoff** | 6:00 PM EDT (UTC−4) |
| **Venue** | MetLife Stadium, New York |
| **Group** | C |

**Model prediction**

| Outcome | Probability |
|---------|-------------|
| Brazil win | **53.3%** |
| Draw | 23.1% |
| Morocco win | 23.6% |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | Brazil 1.83 — Morocco 1.14 |
| Most likely scoreline | **1-1** (10.7%) |
| Predicted winner | **Brazil** |
| Confidence | Low |

**Key factors**: Rodrygo out (ACL); Estêvão monitoring per `injury_tracker.md`.

---

### Match 5: Haiti vs Scotland

| Field | Detail |
|-------|--------|
| **Date** | June 13, 2026 |
| **Kickoff** | 9:00 PM EDT (UTC−4) |
| **Venue** | Gillette Stadium, Boston |
| **Group** | C |

**Model prediction**

| Outcome | Probability |
|---------|-------------|
| Haiti win | **52.6%** |
| Draw | 23.4% |
| Scotland win | 24.0% |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | Haiti 1.80 — Scotland 1.15 |
| Most likely scoreline | **1-1** (10.7%) |
| Predicted winner | **Haiti** |
| Confidence | Low |

---

## Group B — Standings Probabilities *(after Canada 1–1 Bosnia)*

| Team | P(1st) | P(2nd) | P(Top 2) | P(3rd) | P(4th) |
|------|--------|--------|----------|--------|--------|
| Canada | 26.8% | **32.3%** | **59.1%** | 24.9% | 16.0% |
| Switzerland | **29.5%** | 19.0% | 48.5% | 25.7% | 25.8% |
| Bosnia and Herzegovina | 22.7% | 28.1% | 50.7% | 26.0% | 23.3% |
| Qatar | 21.1% | 20.6% | 41.6% | 23.4% | 35.0% |

**Most likely 1st–2nd pairings:** Canada/Bosnia and Herzegovina (13.3%), Bosnia/Canada (12.8%), Switzerland/Canada (12.1%)

---

## Group C — Standings Probabilities *(pre–Matchday 1)*

| Team | P(1st) | P(2nd) | P(Top 2) | P(3rd) | P(4th) |
|------|--------|--------|----------|--------|--------|
| Brazil | **48.2%** | 26.4% | **74.6%** | 16.2% | 9.2% |
| Scotland | 22.4% | 26.6% | 49.0% | 26.1% | 24.9% |
| Morocco | 16.0% | 24.3% | 40.3% | 27.9% | 31.8% |
| Haiti | 13.4% | 22.7% | 36.1% | 29.8% | 34.1% |

**Most likely 1st–2nd pairings:** Brazil/Scotland (17.7%), Brazil/Morocco (16.1%), Brazil/Haiti (14.5%)

---

## June 13 Summary

| Match | Prediction | xG | Confidence |
|-------|------------|-----|------------|
| Qatar vs Switzerland | **Qatar** (58%) | 1.94–1.04 | Moderate |
| Brazil vs Morocco | **Brazil** (53%) | 1.83–1.14 | Low |
| Haiti vs Scotland | **Haiti** (53%) | 1.80–1.15 | Low |

---

## June 12, 2026 — Groups B & D *(completed)*

| Match | Result | Pre-match pick |
|-------|--------|----------------|
| Canada 1–1 Bosnia and Herzegovina | Draw | Bosnia (44%) — **upset avoided**; Canada first WC point |
| United States 4–1 Paraguay | USA win | United States (57%) — **correct** |

*Post-match events logged: Pulisic injury monitor, Balogun form boost, Paraguay yellow-card accumulation (`match_events.csv`).*

---

## June 11, 2026 — Group A *(completed)*

| Match | Result | Pre-match pick |
|-------|--------|----------------|
| Mexico 2–0 South Africa | Mexico win | Mexico (47%) — **correct** |
| South Korea 2–1 Czechia | Korea win | South Korea (60%) — **correct** |

*Post-match events: Montes red (suspended), South Africa two reds, Korea form boosts (`match_events.csv`).*

---

*After adding results: `python -m wc2026_monte_carlo.refresh_predictions` then re-run `predict_matches --date … --log` and refresh this file.*