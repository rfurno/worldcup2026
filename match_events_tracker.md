# Match Events Tracker — World Cup 2026

Post-match discipline, suspensions, injuries, and form signals that may affect **future** predictions.  
FIFA rules ([BBC Sport](https://www.bbc.com/sport/football/articles/cd95xz5xndlo)): **straight red or second yellow = 1-match ban**; **two yellows across matches = 1-match ban**; yellows reset after group stage.

**Updated**: June 12, 2026 (after Group A Matchday 1)

---

## June 11, 2026 — Group A

### Mexico 2–0 South Africa

| Player | Team | Event | Next-match impact | Source |
|--------|------|-------|-------------------|--------|
| César Montes | Mexico | Red card 90+2′ (DOGSO) | **Suspended** vs South Korea (Jun 18) | [BBC](https://www.bbc.com/sport/football/articles/cd95xz5xndlo), [NYT Athletic](https://www.nytimes.com/athletic/7352092/2026/06/11/mexico-world-cup-south-africa-quinones-red-cards/) |
| Sphephelo Sithole | South Africa | Red card 49′ (DOGSO) | **Suspended** vs Czechia (Jun 18) | BBC, NYT Athletic |
| Themba Zwane | South Africa | Red card 73′ (violent conduct) | **Suspended** vs Czechia (Jun 18) | BBC, NYT Athletic |
| Brian Gutiérrez | Mexico | Yellow 23′ | On **1 yellow** — second triggers ban | Wikipedia match report |
| Nkosinathi Sibisi | South Africa | Yellow 74′ | On **1 yellow** | Wikipedia match report |
| Julián Quiñones | Mexico | 2 goals, MOTM-level display | **Form boost** — breakout WC star | [NYT Athletic](https://www.nytimes.com/athletic/7352092/2026/06/11/mexico-world-cup-south-africa-quinones-red-cards/) |
| Raúl Jiménez | Mexico | WC goal, emotional comeback | **Form boost** | NYT Athletic |
| Ronwen Williams | South Africa | Error on opener, risky distribution | **Form concern** | [NYT Athletic](https://www.nytimes.com/athletic/7352092/2026/06/11/mexico-world-cup-south-africa-quinones-red-cards/) |
| Gilberto Mora | Mexico | Sub 66′, bright cameo | Minor positive depth signal | Wikipedia |

**Team notes**
- South Africa finished with **9 men** — depth and defensive structure severely tested for next fixture.
- Mexico lose captain/center-back Montes for Korea clash; Quiñones/Jiménez elevate attack profile.

---

### South Korea 2–1 Czechia

| Player | Team | Event | Next-match impact | Source |
|--------|------|-------|-------------------|--------|
| Lee Gi-hyuk | South Korea | Yellow 90+6′ | On **1 yellow** | [ESPN](https://www.espn.com/soccer/match/_/gameId/760414/czechia-south-korea) |
| Hwang In-beom | South Korea | Goal + assist, injury comeback | **Form boost** | [Korea Herald](https://www.koreaherald.com/article/10770701) |
| Oh Hyeon-gyu | South Korea | Winning goal; played with fever (38°C) | **Form boost** but monitor fitness | Korea Herald |
| Kim Seung-gyu | South Korea | Match-saving saves | **Form boost** (GK) | Korea Herald, Czech coach praise |
| Son Heung-min | South Korea | Quiet first half, 6 shots | Neutral — depth concern if form dips | ESPN match stats |
| Ladislav Krejčí | Czechia | Opener, captain | Scored but team lost lead | [Al Jazeera](https://www.aljazeera.com/sports/2026/6/12/south-korea-vs-czechia-world-cup-2026-oh-hyeon-gyu-hwang-in-beom) |
| Matej Kovář | Czechia | 6 saves, 2.30 xGC | **Form boost** despite loss | ESPN |

**Pre-tournament injuries** (tracked in `injury_tracker.md`, not duplicated in `match_events.csv`): Cho Yu-min out; Bae Jun-ho monitoring.

**Team notes**
- No suspensions for either side before Matchday 2.
- Korea's comeback morale + Hwang/Oh/Kim form upgrades; Czechia competitive but vulnerable after late collapse.

---

## Upcoming fixtures affected (Group A, Jun 18)

| Match | Key absences / risks |
|-------|----------------------|
| **Mexico vs South Korea** | Mexico: **Montes suspended**. Korea: Lee Gi-hyuk on 1 yellow; Oh fitness monitor. |
| **Czechia vs South Africa** | South Africa: **Sithole + Zwane suspended**; Sibisi on 1 yellow; Williams confidence shaken. |

---

## Model integration

Structured data: `simulations/data/match_events.csv`  
Parser: `wc2026_monte_carlo.match_availability` → `availability_multiplier` + `form_adjustment` merged into team features before predictions.

*Evaluate impact: `python -m wc2026_monte_carlo.evaluate_predictions --show-availability`*