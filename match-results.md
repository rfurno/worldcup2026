# World Cup 2026 Match Results

Official results for completed group-stage matches. Sources: [FIFA](https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/scores-fixtures), [Wikipedia Group A](https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_A).

**Updated**: June 13, 2026

---

## June 11, 2026 — Group A (Matchday 1)

### Match 1: Mexico 2–0 South Africa

| Field | Detail |
|-------|--------|
| **Date** | June 11, 2026 |
| **Kickoff** | 1:00 PM CDT |
| **Venue** | Estadio Azteca, Mexico City |
| **Group** | A |
| **Attendance** | 80,824 |

| | Mexico | South Africa |
|---|--------|--------------|
| **Goals** | Quiñones 9′, Jiménez 67′ | — |
| **Result** | **W** | **L** |

**Notes**: South Africa finished with nine men (Sithole 49′, Zwane 73′); Mexico's Montes sent off 90+2′. Mexico's first World Cup opener win since 1998.

---

### Match 2: South Korea 2–1 Czechia

| Field | Detail |
|-------|--------|
| **Date** | June 11, 2026 |
| **Kickoff** | 8:00 PM CDT |
| **Venue** | Estadio Akron, Guadalajara |
| **Group** | A |
| **Attendance** | 44,985 |

| | South Korea | Czechia |
|---|-------------|---------|
| **Goals** | Hwang 67′, Oh 80′ | Krejčí 59′ |
| **Result** | **W** | **L** |

**Notes**: Czechia led until the 67th minute; South Korea comeback. Son Heung-min started; Korea controlled possession.

---

## Group A standings (after Matchday 1)

| Pos | Team | Pld | W | D | L | GF | GA | GD | Pts |
|-----|------|-----|---|---|---|----|----|-----|-----|
| 1 | Mexico | 1 | 1 | 0 | 0 | 2 | 0 | +2 | 3 |
| 2 | South Korea | 1 | 1 | 0 | 0 | 2 | 1 | +1 | 3 |
| 3 | Czechia | 1 | 0 | 0 | 1 | 1 | 2 | −1 | 0 |
| 4 | South Africa | 1 | 0 | 0 | 1 | 0 | 2 | −2 | 0 |

---

## June 12, 2026 — Groups B & D (Matchday 1)

### Match 3: Canada 1–1 Bosnia and Herzegovina

| Field | Detail |
|-------|--------|
| **Date** | June 12, 2026 |
| **Kickoff** | 3:00 PM EDT |
| **Venue** | BMO Field, Toronto |
| **Group** | B |

| | Canada | Bosnia and Herzegovina |
|---|--------|------------------------|
| **Goals** | Larin 78′ | Lukic 21′ |
| **Result** | **D** | **D** |

**Notes**: Bosnia led through Jovo Lukic; Cyle Larin equalized after coming off the bench. Canada's first-ever World Cup point.

---

### Match 4: United States 4–1 Paraguay

| Field | Detail |
|-------|--------|
| **Date** | June 12, 2026 |
| **Kickoff** | 6:00 PM PDT |
| **Venue** | SoFi Stadium, Los Angeles |
| **Group** | D |

| | United States | Paraguay |
|---|---------------|----------|
| **Goals** | Bobadilla 7′ (o.g.), Balogun 31′, 45+5′, Reyna 90+8′ | Maurício 73′ |
| **Result** | **W** | **L** |

**Notes**: Folarin Balogun brace on his World Cup debut; Giovanni Reyna sealed it in stoppage time.

---

## June 12 Summary

| Match | Score | Winner |
|-------|-------|--------|
| Canada vs Bosnia and Herzegovina | **1–1** | Draw |
| United States vs Paraguay | **4–1** | United States |

---

## June 11 Summary

| Match | Score | Winner |
|-------|-------|--------|
| Mexico vs South Africa | **2–0** | Mexico |
| South Korea vs Czechia | **2–1** | South Korea |

---

## Model evaluation (June 11)

| Metric | Value |
|--------|-------|
| Predicted winner accuracy | **2/2 (100%)** |
| Mean Brier score | 0.336 |
| Mean log loss | 0.637 |
| Mean xG error (per team) | 0.82 goals |

- Mexico 2–0: winner correct; model expected tighter game (xG 1.83–1.44, modal score 1–1)
- South Korea 2–1: winner correct; actual scoreline was joint-most-likely at ~10%

Full report: `simulations/output/prediction_evaluation.md`

---

*Data: `simulations/data/match_results.csv` | After adding results: `python -m wc2026_monte_carlo.refresh_predictions` (auto-collects cards/injuries/form into `match_events.csv`)*