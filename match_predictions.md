# World Cup 2026 Match Predictions

Daily match-by-match forecasts using the market-calibrated Dixon-Coles model (Elo + squad value + xG + recent form + club chemistry + injuries, anchored to betting odds).

**Updated**: June 11, 2026 (forecasts for June 12)

---

## June 12, 2026 — Groups B & D (Matchday 1)

Second day of the tournament. Two fixtures: Canada hosts Group B in Toronto; USA opens Group D in Los Angeles.

### Match 3: Canada vs Bosnia and Herzegovina

| Field | Detail |
|-------|--------|
| **Date** | June 12, 2026 |
| **Kickoff** | 3:00 PM EDT (UTC−4) |
| **Venue** | BMO Field, Toronto |
| **Group** | B |
| **Context** | Canada co-host; first competitive meeting between the sides. |

**Model prediction**

| Outcome | Probability |
|---------|-------------|
| Canada win | 32.3% |
| Draw | 23.5% |
| Bosnia and Herzegovina win | **44.2%** |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | Canada 1.45 — Bosnia 1.73 |
| Most likely scoreline | **1-1** (10.3%) |
| Other likely scores | 1-2 (9.2%), 2-1 (7.5%), 0-1 (7.1%), 2-2 (6.5%) |
| Predicted winner | **Bosnia and Herzegovina** (slight edge) |
| Confidence | Low |

**Key factors**
- Host advantage at BMO Field, but calibrated model still favors Bosnia on xG (1.73 vs 1.45)
- Bosnia stronger on Elo/squad depth; Džeko, Kolašinac, Pjanić (`squad_clubs.csv`)
- Canada relies on Davies, David, Larin — competitive but outgunned in model blend
- Draw live at ~24%; Canada upset path ~32%

**Recommendation**: **Bosnia and Herzegovina or Draw** — don't assume host boost wins it. Canada double-chance (win or draw) for safer play at reduced value.

---

## Group B — Full Standings Probabilities (50k sims)

| Team | P(1st) | P(2nd) | P(Top 2) | P(3rd) | P(4th) |
|------|--------|--------|----------|--------|--------|
| Switzerland | **31.5%** | 29.2% | **60.8%** | 25.3% | 13.9% |
| Bosnia and Herzegovina | 29.9% | 26.1% | 56.1% | 24.1% | 19.8% |
| Qatar | 28.2% | 27.5% | 55.6% | 24.5% | 19.9% |
| Canada | 10.4% | 17.2% | 27.5% | 26.1% | 46.4% |

**Most likely 1st–2nd pairings:** Qatar/Switzerland (13.7%), Bosnia/Qatar (12.7%), Switzerland/Bosnia (12.6%), Switzerland/Qatar (11.7%), Bosnia/Switzerland (11.7%)

**Note**: Group B is tight among Switzerland, Bosnia, and Qatar. Canada only ~28% to finish top two despite co-hosting.

---

### Match 4: United States vs Paraguay

| Field | Detail |
|-------|--------|
| **Date** | June 12, 2026 |
| **Kickoff** | 9:00 PM EDT (UTC−4) |
| **Venue** | SoFi Stadium, Los Angeles |
| **Group** | D |
| **Context** | USA co-host; Paraguay qualified via CONMEBOL. |

**Model prediction**

| Outcome | Probability |
|---------|-------------|
| United States win | **57.4%** |
| Draw | 20.8% |
| Paraguay win | 21.8% |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | United States 2.14 — Paraguay 1.26 |
| Most likely scoreline | **2-1** (9.4%) |
| Other likely scores | 1-1 (9.0%), 2-0 (7.6%), 1-0 (7.1%), 3-1 (6.9%) |
| Predicted winner | **United States** |
| Confidence | Moderate |

**Key factors**
- Host advantage at SoFi; USA clear xG edge (2.14 vs 1.26)
- Pulisic, Musah, McKennie, Adams in squad (`squad_clubs.csv`)
- Paraguay competitive but model rates upset at ~22%
- Most likely score 2-1 aligns with USA as moderate favorite

**Recommendation**: **United States to win** — stronger pick than Canada's opener. USA or Draw for safer play.

---

## Group D — Full Standings Probabilities (50k sims)

| Team | P(1st) | P(2nd) | P(Top 2) | P(3rd) | P(4th) |
|------|--------|--------|----------|--------|--------|
| Turkey | **34.5%** | 27.8% | **62.2%** | 22.4% | 15.4% |
| United States | 30.0% | 28.1% | 58.1% | 24.0% | 17.9% |
| Paraguay | 19.5% | 23.0% | 42.5% | 26.8% | 30.7% |
| Australia | 16.0% | 21.1% | 37.1% | 26.8% | 36.1% |

**Most likely 1st–2nd pairings:** Turkey/United States (16.2%), United States/Turkey (13.0%), Turkey/Paraguay (9.6%), United States/Paraguay (9.4%), Turkey/Australia (8.6%)

**Note**: Turkey slight group-favorite despite USA winning tomorrow's opener. USA ~58% to finish top two.

---

## June 12 Summary

| Match | Prediction | xG | Confidence |
|-------|------------|-----|------------|
| Canada vs Bosnia and Herzegovina | **Bosnia** (44%) | 1.45–1.73 | Low — draw live |
| United States vs Paraguay | **United States** (57%) | 2.14–1.26 | Moderate |

**Next fixtures (June 13):** Qatar vs Switzerland, Brazil vs Morocco, Haiti vs Scotland, Australia vs Turkey

---

## June 11, 2026 — Group A (Matchday 1) *(completed)*

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
| Mexico win | **46.6%** |
| Draw | 22.9% |
| South Africa win | 30.5% |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | Mexico 1.83 — South Africa 1.44 |
| Most likely scoreline | **1-1** (10.0%) |
| Other likely scores | 2-1 (8.9%), 1-2 (7.3%), 1-0 (6.9%), 2-2 (6.6%) |
| Predicted winner | **Mexico** (slight edge) |
| Confidence | Low |

**Key factors**
- Host advantage at Azteca, but calibrated model sees a tight contest
- South Africa competitive on xG (1.44) — not a walkover
- 2010 opener ended 1-1 at same venue; draw live at ~23%
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
| South Korea win | **60.0%** |
| Draw | 21.5% |
| Czechia win | 18.6% |

| Metric | Value |
|--------|-------|
| Expected goals (xG) | South Korea 1.99 — Czechia 1.02 |
| Most likely scoreline | **1-1** (10.0%) |
| Other likely scores | 2-1 (10.0%), 2-0 (9.8%), 1-0 (9.8%), 3-1 (6.8%) |
| Predicted winner | **South Korea** |
| Confidence | Moderate |

**Key factors**
- Son Heung-min, Kim Min-jae, Lee Kang-in all fit (`player_tracker.md`)
- Korea superior xG edge (1.99 vs 1.02) at neutral site
- Czechia defensive but outgunned; upset path ~19%

**Recommendation**: **South Korea to win** — clearest pick of the day. Korea or Draw for safer play.

---

## Group A — Full Standings Probabilities (50k sims)

| Team | P(1st) | P(2nd) | P(Top 2) | P(3rd) | P(4th) |
|------|--------|--------|----------|--------|--------|
| Czechia | **32.1%** | 28.2% | **60.3%** | 22.8% | 16.9% |
| South Africa | 24.1% | 23.7% | 47.8% | 25.5% | 26.7% |
| South Korea | 22.8% | 24.3% | 47.2% | 25.7% | 27.2% |
| Mexico | 20.9% | 23.8% | 44.7% | 26.1% | 29.2% |

**Most likely 1st–2nd pairings:** Czechia/Mexico (11.3%), Czechia/South Africa (10.5%), Korea/Czechia (10.3%), Czechia/Korea (10.3%), South Africa/Czechia (9.3%)

**Note**: Calibrated model rates Group A as wide open — Czechia slight group-favorite despite Korea winning the June 11 head-to-head. Mexico ~45% to finish top two.

---

## June 11 Summary

| Match | Prediction | xG | Confidence |
|-------|------------|-----|------------|
| Mexico vs South Africa | **Mexico** (47%) | 1.83–1.44 | Low — draw live |
| South Korea vs Czechia | **South Korea** (60%) | 1.99–1.02 | Moderate |

---

*Regenerate: `python -m wc2026_monte_carlo.predict_matches --date 2026-06-12`*