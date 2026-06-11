# World Cup 2026 Match Predictions

Daily match-by-match forecasts using the Dixon-Coles model (Elo + market odds + squad value + xG + injury adjustments). Updated before each matchday.

**Baseline date**: June 10, 2026

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
| Mexico win | **79.8%** |
| Draw | 13.5% |
| South Africa win | 6.7% |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | Mexico 3.01 — South Africa 0.84 |
| Most likely scoreline | **3-0** (9.9%) |
| Other likely scores | 2-0 (9.7%), 3-1 (8.3%), 2-1 (8.2%) |
| Predicted winner | **Mexico** |
| Confidence | High |

**Key factors**
- Mexico host advantage at Azteca (+ home + co-host boost)
- South Africa weaker squad depth and lower Elo (1810 vs 1950)
- Mexico key players fit: Ochoa, Álvarez, Giménez (see `player_tracker.md`)
- South Africa rely on Foster/Mokoena; limited attacking firepower vs top sides
- 2010 opener was a draw, but Mexico are stronger at home in 2026

**Recommendation**: Mexico to win comfortably. Lean **Mexico -1.5** on handicap; avoid draw/no-draw at short odds.

---

### Match 2: South Korea vs Czechia

| Field | Detail |
|-------|--------|
| **Date** | June 11, 2026 |
| **Kickoff** | 8:00 PM CDT (UTC−6) |
| **Venue** | Estadio Akron, Zapopan (Guadalajara) |
| **Group** | A |
| **Context** | Neutral venue (neither team is a host). Czechia qualified via UEFA Path D. |

**Model prediction** *(neutral venue — neither team is a host)*

| Outcome | Probability |
|---------|-------------|
| South Korea win | **63.0%** |
| Draw | 22.7% |
| Czechia win | 14.3% |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | South Korea 2.07 — Czechia 0.91 |
| Most likely scoreline | **2-0** (11.2%) |
| Other likely scores | 2-1 (10.2%), 1-1 (9.8%), 1-0 (9.0%) |
| Predicted winner | **South Korea** |
| Confidence | Moderate |

**Key factors**
- Son Heung-min, Kim Min-jae, Lee Kang-in all fit (`player_tracker.md`)
- Czechia competitive but lower Elo and xG form; playoff momentum offset by squad gap
- Neutral-site fixture in Mexico — reduced home edge for Korea (designated home team only)
- Korea beat Czechia 2-1 in a 2016 friendly; stronger Asian side in 2026 cycle
- Draw plausible (~23%) given Czech defensive organization and neutral site

**Recommendation**: South Korea to win, but draw risk is meaningful. **South Korea or Draw** is the safer play.

---

## June 11 Summary

| Match | Prediction | xG | Confidence |
|-------|------------|-----|------------|
| Mexico vs South Africa | **Mexico win** | 3.01–0.84 | High |
| South Korea vs Czechia | **South Korea win** | 2.07–0.91 | Moderate |

**Group A outlook after Matchday 1**: If both favorites win, Mexico likely top the group on GD; South Korea and Czechia meet later with qualification pressure rising. South Africa will need points from Korea/Czechia fixtures to stay in third-place contention.

---

*Generated from `simulations/wc2026_monte_carlo` Dixon-Coles model. Re-run with `python -m wc2026_monte_carlo.predict_matches` after injury/odds updates.*