# World Cup 2026 Match Predictions

Daily match-by-match forecasts using the market-calibrated Dixon-Coles model (Elo + recent form + xG + injuries, anchored to betting odds).

**Updated**: June 10, 2026 (post-calibration model)

---

## June 11, 2026 — Group A (Matchday 1)

Opening day of the tournament. Two Group A fixtures in Mexico.

### Match 1: Mexico vs South Africa

| Field | Detail |
|-------|--------|
| **Date** | June 11, 2026 |
| **Kickoff** | 1:00 PM CDT (UTC−6) |
| **Venue** | Estadio Azteca, Mexico City |
| **Group** | A |
| **Context** | Tournament opener; Mexico co-host. Last met at 2010 WC opener (1-1). |

**Model prediction**

| Outcome | Probability |
|---------|-------------|
| Mexico win | **45.1%** |
| Draw | 23.1% |
| South Africa win | 31.8% |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | Mexico 1.79 — South Africa 1.47 |
| Most likely scoreline | **1-1** (10.1%) |
| Other likely scores | 2-1 (9.5%), 1-2 (8.3%), 2-2 (7.6%) |
| Predicted winner | **Mexico** (slight edge) |
| Confidence | Low |

**Key factors**
- Host advantage at Azteca, but calibrated model sees a tighter contest than early forecasts
- South Africa competitive on xG (1.47) — not a walkover
- 2010 opener ended 1-1 at same venue; draw is live at ~23%
- Mexico key players fit: Ochoa, Álvarez, Giménez (`player_tracker.md`)

**Recommendation**: Mexico to edge it, but **draw or South Africa** are real outcomes. Avoid heavy Mexico handicap.

---

### Match 2: South Korea vs Czechia

| Field | Detail |
|-------|--------|
| **Date** | June 11, 2026 |
| **Kickoff** | 8:00 PM CDT (UTC−6) |
| **Venue** | Estadio Akron, Zapopan (Guadalajara) |
| **Group** | A |
| **Context** | Neutral venue. Czechia qualified via UEFA Path D. |

**Model prediction** *(neutral venue)*

| Outcome | Probability |
|---------|-------------|
| South Korea win | **61.3%** |
| Draw | 21.1% |
| Czechia win | 17.7% |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | South Korea 2.04 — Czechia 1.00 |
| Most likely scoreline | **2-0** (10.0%) |
| Other likely scores | 2-1 (9.5%), 1-0 (8.5%), 1-1 (8.2%) |
| Predicted winner | **South Korea** |
| Confidence | Moderate |

**Key factors**
- Son Heung-min, Kim Min-jae, Lee Kang-in all fit (`player_tracker.md`)
- Korea superior xG edge (2.04 vs 1.00) at neutral site
- Czechia defensive but outgunned; upset path ~18%

**Recommendation**: **South Korea to win** — clearest pick of the day. Korea or Draw for safer play.

---

## Group A — Full Standings Probabilities (50k sims)

| Team | P(1st) | P(2nd) | P(Top 2) | P(3rd) | P(4th) |
|------|--------|--------|----------|--------|--------|
| Czechia | **32.2%** | 28.4% | **60.6%** | 23.1% | 16.4% |
| South Korea | 24.6% | 25.3% | 49.8% | 25.3% | 24.9% |
| South Africa | 24.2% | 23.8% | 48.0% | 25.3% | 26.7% |
| Mexico | 19.1% | 22.6% | 41.6% | 26.4% | 32.0% |

**Most likely 1st–2nd pairings:** Korea/Czechia (11.6%), Czechia/Korea (11.0%), Czechia/Mexico (10.7%)

**Note**: Calibrated model rates Group A as wide open — Czechia slight group-favorite despite Korea winning tomorrow's head-to-head. Mexico only ~42% to finish top two.

---

## June 11 Summary

| Match | Prediction | xG | Confidence |
|-------|------------|-----|------------|
| Mexico vs South Africa | **Mexico** (45%) | 1.79–1.47 | Low — draw live |
| South Korea vs Czechia | **South Korea** (61%) | 2.04–1.00 | Moderate |

---

*Regenerate: `python -m wc2026_monte_carlo.predict_matches --date 2026-06-11`*