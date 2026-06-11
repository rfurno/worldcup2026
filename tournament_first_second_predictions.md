# World Cup 2026 — First & Second Place Probabilities

Tournament-wide podium probabilities from the Monte Carlo simulation (full 48-team bracket, 10,000 runs).  
**Baseline date**: June 10, 2026 | **Model**: Dixon-Coles, **calibrated to betting market odds**

Compare with `winner_odds_table.md` and `betting_sites_odds.md`.

---

## Top Contenders — P(1st) / P(2nd) vs Market

| Team | Model P(1st) | Market P(Win) | Δ | Model P(2nd) | Model P(Podium) |
|------|--------------|---------------|---|--------------|-----------------|
| France | **13.2%** | 17.0% | −3.8 pp | 7.5% | 20.7% |
| Spain | **12.8%** | 17.7% | −4.9 pp | 8.2% | 20.9% |
| England | **9.6%** | 13.3% | −3.8 pp | 7.2% | 16.8% |
| Portugal | **7.9%** | 11.8% | −3.9 pp | 5.9% | 13.8% |
| Brazil | **7.1%** | 10.5% | −3.4 pp | 5.7% | 12.9% |
| Argentina | **6.0%** | 10.0% | −4.0 pp | 5.7% | 11.7% |
| Germany | **3.9%** | 6.7% | −2.8 pp | 3.6% | 7.4% |

**Note**: Model is calibrated toward books; remaining gap (~3–5 pp on favourites) reflects tournament knockout variance and unquoted tail teams absorbing probability mass.

**Ranking**: Model has France ≈ Spain > England — market has Spain > France > England. Same teams, close ordering.

---

## Most Likely Winner / Runner-up Pairs

| Winner | Runner-up | Probability |
|--------|-----------|-------------|
| France | Spain | 1.4% |
| France | England | 1.2% |
| Spain | France | 1.1% |
| England | Spain | 1.1% |
| Spain | England | 1.1% |
| England | France | 1.0% |
| France | Portugal | 0.9% |
| France | Brazil | 0.9% |
| Spain | Brazil | 0.9% |
| Portugal | France | 0.8% |

Final pairings are more spread out than pre-calibration — consistent with a flatter market-implied field.

---

## All 48 Teams (P(1st) / P(2nd))

| Team | P(1st) | P(2nd) | P(Podium) |
|------|--------|--------|-----------|
| France | 13.2% | 7.5% | 20.7% |
| Spain | 12.8% | 8.2% | 20.9% |
| England | 9.6% | 7.2% | 16.8% |
| Portugal | 7.9% | 5.9% | 13.8% |
| Brazil | 7.1% | 5.7% | 12.9% |
| Argentina | 6.0% | 5.7% | 11.7% |
| Germany | 3.9% | 3.6% | 7.4% |
| Morocco | 1.6% | 1.6% | 3.2% |
| Qatar | 1.5% | 1.7% | 3.1% |
| Czechia | 1.5% | 2.2% | 3.6% |
| DR Congo | 1.3% | 1.3% | 2.5% |
| *Remaining 37 teams* | <1.3% each | <1.3% each | <2.5% each |

Full CSV: `simulations/output/first_second_probabilities.csv`

---

## Calibration Method

1. **Market anchor** (90%) — log-odds from FanDuel/bet365 winner odds in `betting_sites_odds.md`
2. **Statistical blend** (10%) — Elo, squad value, xG, player tracker
3. **Soft injury adjustment** — 40% of raw injury penalty (books already price injuries)
4. **Iterative tuning** — 10 × 4,000 tournament runs adjust strengths until win rates converge on market targets
5. **Strength temperature** (0.42) — compresses favourite dominance in knockout bracket

**Regenerate**:
```bash
cd simulations && source .venv/bin/activate
python -m wc2026_monte_carlo --simulations 10000 --seed 42
```