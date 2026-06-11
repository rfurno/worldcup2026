# Additional Data Sources

## Elo Ratings & Team Strength (Core input)
Sources: eloratings.net, ClubElo, or Kaggle "international-football-results-from-1872-to-2017" (updated versions available).
Why: Transparent, history-based baseline. Blend with our betting_sites_odds.md (market forward-looking signal) and player_tracker.md (individual contributions).
Usage in MC: Scale attack/defense parameters; adjust dynamically for injuries (e.g., -8–15% strength multiplier for key absences like Rodrygo).

## Player-Level & Squad Data
Sources: Transfermarkt (market values, detailed squads, ages, positions), FBref/StatsBomb/Opta (xG, xA, progressive actions, defensive metrics).
Why: Our player_tracker.md is a great start—expand with granular stats for "star power" multipliers or injury-adjusted lineups.
Bonus: FIFA official squads + recent friendlies/qualifiers for current form.

## Historical Match Results & H2H
Sources: Kaggle international results dataset, Wikipedia match histories, WorldFootball.net or Soccerway.
Why: Calibrate Poisson/Dixon-Coles parameters (attack/defense strengths, time-weighting for recency). Include H2H trends and venue-specific performance.

## Advanced Metrics & xG Models
Sources: FBref (expected goals), StatsBomb or Opta (detailed event data), The Analyst/Opta supercomputer outputs.
Why: Improves goal distribution realism over basic Poisson. Many top models (including DTAI) use these and have historically outperformed bookies in sim metrics.

## Betting Markets & Prediction Markets (for Blending/Calibration)
Sources: Our betting_sites_odds.md + live odds (FanDuel, bet365), Polymarket/PredictIt (crowd wisdom on winner paths).
Why: Markets are often the most accurate aggregate (ranked #1 in our historical review). Use as priors or to blend with Elo (e.g., 60% Elo + 40% market).

## Contextual & Environmental Factors
Sources: FIFA schedule/venues (travel distance, time zones, altitude for some stadiums), weather APIs (for specific matches), injury probability models or detailed timelines (beyond our ESPN-based tracker).
Why: Home advantage, fatigue, and weather meaningfully shift probabilities in expanded 48-team format.

## Proven Model Frameworks (for Implementation)
Dixon-Coles (bivariate Poisson extension) – Handles goal correlation and low scores better than independent Poisson.
Examples: dashee87 GitHub implementations, or open WC models on GitHub (e.g., Hicruben/world-cup-2026-prediction-model uses Elo → Dixon-Coles → MC).