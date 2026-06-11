# Additional Data Sources for Monte Carlo Simulation - World Cup 2026

This document lists recommended external data sources to enhance the Monte Carlo (MC) simulation for predicting match outcomes and the overall World Cup 2026 winner. These complement our internal project data (injury_tracker.md, player_tracker.md, betting_sites_odds.md, winner_odds_table.md, etc.).

Integrate these into the simulation for:
- Base team/player strengths
- Historical calibration (Dixon-Coles or Poisson parameters)
- Dynamic adjustments (injuries, form, venue)
- Blending with market probabilities
- Full tournament simulation (groups + knockouts with tiebreakers/penalties)

## Core Team & Match Data Sources

### 1. Elo Ratings & Team Strength
- **Primary**: eloratings.net (current international Elo ratings)
- **Historical**: Kaggle dataset "international-football-results-from-1872-to-2017" (or updated forks)
- **Usage**: Base attack/defense parameters. Blend with our betting odds (e.g., 70% Elo + 30% market-implied). Update dynamically with recent results.
- **Why valuable**: Transparent, updates after every match, proven in many WC models.

### 2. Player & Squad Valuation
- **Primary**: Transfermarkt.com (market values, detailed squads, positions, ages, national team caps/goals)
- **Alternative**: FBref or Wikipedia for rosters
- **Usage**: Compute team strength as sum/average of top players or use individual ratings. Adjust for our injury_tracker.md (e.g., reduce strength if key player injured).
- **Why valuable**: Captures squad depth and star power beyond simple team Elo.

### 2.5 Player Club Affiliation & Same-Nationality Clusters (Chemistry)
- **Primary Sources**:
  - **Transfermarkt** (Best): Filter players by nationality to see club distribution. Excellent for identifying clusters (e.g., multiple Brazilians at one club).
  - **FBref**: Player stats combined with current club and national team data.
  - **Sofascore / FotMob**: Good for current squad composition and same-club nationality tracking.
- **Usage in MC Simulation**:
  - Detect when 2+ players from the same national team play at the same club.
  - Apply a **chemistry/synergy bonus** to team strength or individual player ratings.
  - Use club form of same-nationality groups as a proxy for international chemistry and form.
  - Correlate injury risk and performance among players at the same club.
- **Why valuable**: Players from the same national team who play together at club level often develop better understanding, which can translate to international matches. This is especially relevant for teams like Brazil, France, Argentina, and Portugal.

### 3. Historical Match Results & Head-to-Head
- **Primary**: Kaggle "international-football-results-from-1872-to-2017" + recent updates from FBref or Wikipedia
- **H2H & Recent Form**: WorldFootball.net, Soccerway, or our opening_fixtures_predictions.md extended with historical data
- **Usage**: Calibrate Dixon-Coles or Poisson model parameters (attack, defense, home advantage, time decay). Include in MC for realistic variance.

### 4. Advanced Metrics (xG, xA, etc.)
- **Primary**: FBref.com (expected goals, expected assists, progressive passes/carries, defensive actions)
- **Advanced**: StatsBomb or Opta event data (if accessible via API or public summaries)
- **Usage**: Improve goal scoring distributions. Use xG to adjust Poisson means for current form.
- **Why valuable**: More predictive than raw results for recent performance.

## Contextual & Dynamic Factors

### 5. Betting Markets & Prediction Markets
- **Primary**: Our betting_sites_odds.md + live odds from FanDuel, bet365, DraftKings
- **Crowd Wisdom**: Polymarket or PredictIt (current probabilities for winner, paths)
- **Usage**: Blend with Elo for hybrid strength ratings. Use as calibration target or for implied probabilities in MC.
- **Why valuable**: Markets aggregate information quickly (injuries, form, news) and ranked highest in our historical accuracy review.

### 6. Venue, Travel & Environmental Data
- **Sources**: FIFA official schedule/venues, Google Maps or travel APIs for distances/time zones, weather APIs (OpenWeatherMap) for match-day conditions
- **Usage**: Apply home advantage modifiers, fatigue penalties for long travel (especially important in 48-team expanded format across North America).
- **Why valuable**: Accounts for real-world logistical impacts ignored in pure stats models.

### 7. Injury & Player Availability (Enhance our existing tracker)
- **Primary**: ESPN injury tracker, Transfermarkt injury news, club reports
- **Detailed**: Recovery timelines, probability models
- **Usage**: Dynamic multipliers in team strength (e.g., -10-20% for missing key players like Rodrygo). Update from our injury_tracker.md before each sim run.
- **Why valuable**: Critical for accurate pre-tournament and in-tournament adjustments.

## Modeling Frameworks & Calibration

### 8. Dixon-Coles / Bivariate Poisson Models
- **References**: Original Dixon & Coles 1997 paper; implementations on GitHub (e.g., dashee87/football or similar Python/R ports)
- **Usage**: Core match outcome model (better handles low scores and draw correlation than independent Poisson). Calibrate parameters on historical data from #3.
- **Enhancement**: Combine with xG from #4 for hybrid model.

### 9. Other Proven WC Models for Reference/Blending
- DTAI Analytics Lab (KU Leuven) – Often outperforms bookies in historical WC predictions
- Open GitHub repos: Hicruben/world-cup-2026-prediction-model (Elo + Dixon-Coles + MC)
- Nate Silver / PELE model outputs (for comparison)

## Integration Recommendations for MC Simulation
- **Data Pipeline**: Scrape or download CSVs from above sources → Parse into pandas DataFrames.
- **Strength Calculation**: Base = Elo + Transfermarkt squad value + xG form. Adjust with injury_tracker and recent results.
- **Match Simulator**: Dixon-Coles or Poisson with parameters from historical data. Add venue/travel modifiers.
- **Tournament Simulator**: Simulate all groups (using real groups from FIFA), then full knockout bracket with tiebreakers (GD, goals scored, H2H, penalties modeled probabilistically).
- **Outputs**: Winner probabilities, probability of reaching each stage, expected path for each team.
- **Runs**: 10,000 – 50,000 full tournament simulations for stable probabilities.
- **Validation**: Backtest on 2018/2022 using our historical_source_accuracy.md insights.

These sources will make the simulation significantly more accurate and robust than basic models, leveraging both statistical rigor and real-time contextual data.

Update this file as new sources or data become available during the tournament.