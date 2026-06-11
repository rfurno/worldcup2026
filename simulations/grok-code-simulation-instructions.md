You are an expert soccer data scientist and Python developer specializing in Monte Carlo simulations for international tournaments.

I have a GitHub repo at https://github.com/rfurno/worldcup2026 with the following relevant files already in place:

- additional-data-sources.md (contains the full list of recommended external data sources)
- injury_tracker.md
- player_tracker.md
- betting_sites_odds.md
- winner_odds_table.md
- news_sources_reference.md (includes Nate Silver/PELE references)
- opening_fixtures_predictions.md
- simulations/wc2026_monte_carlo_starter.py (basic starter script)

**Task**: Create a complete, well-structured, production-ready Python script (or small modular package) for a Monte Carlo simulation of the entire 2026 FIFA World Cup.

**Requirements**:

1. **Data Pipeline**:
   - Automatically retrieve or load data from the sources listed in `additional-data-sources.md`.
   - Prioritize:
     - Elo ratings (eloratings.net or Kaggle international results)
     - Transfermarkt squad/player data
     - Historical match results (Kaggle)
     - FBref xG/advanced metrics
     - Live/recent betting odds (use our betting_sites_odds.md as base + suggest scraping or API)
     - Venue/travel data
   - Parse and integrate our internal markdown files (especially injury_tracker.md and player_tracker.md) to dynamically adjust team strengths.

2. **Core Model**:
   - Use a **Dixon-Coles bivariate Poisson** model (or enhanced Poisson) as the foundation for simulating individual matches.
   - Calibrate parameters on historical data.
   - Blend team strengths: Elo + Transfermarkt squad value + xG form + betting market signal.
   - Apply dynamic adjustments from injury_tracker.md and recent form.

3. **Tournament Simulation**:
   - Simulate the full 48-team format: all group stage matches + complete knockout bracket (Round of 32 → Final).
   - Properly handle group tiebreakers, knockout extra time, and penalty shootouts (probabilistic).
   - Support home advantage, travel fatigue, and venue effects where data is available.

4. **Monte Carlo Engine**:
   - Run 10,000 – 50,000 full tournament simulations.
   - Track and output:
     - Probability each team wins the World Cup
     - Probability of reaching each stage (Round of 32, Quarter-finals, Semi-finals, Final, Winner)
     - Most likely paths for top teams
     - Expected number of goals per match or stage

5. **Code Quality**:
   - Clean, modular, well-commented Python 3 code.
   - Use pandas, numpy, scipy.stats.
   - Include a `requirements.txt`.
   - Make it easy to update data (e.g., functions to refresh Elo, injuries, or odds).
   - Add command-line arguments or a simple config for number of simulations, random seed, etc.
   - Include example output and basic visualization (matplotlib or plotly) for winner probabilities.

6. **Integration with Existing Repo**:
   - The script should live in the `simulations/` folder.
   - Make it easy to load our existing markdown/CSV data.
   - At the top of the script, include clear instructions on how to populate the data sources from additional-data-sources.md.

**Output Format**:
- Provide the full code in a single well-organized Python file (or multiple files if modular).
- Include a README-style comment block at the top explaining how to set it up and run it.
- Add comments throughout explaining where each data source from additional-data-sources.md is used.

Generate the complete, runnable code now.