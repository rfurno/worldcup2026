#!/usr/bin/env python3
"""
Starter entry point for the World Cup 2026 Monte Carlo simulation.

Delegates to the full package. Run from the simulations/ directory::

    python wc2026_monte_carlo_starter.py --simulations 10000

Or as a module::

    python -m wc2026_monte_carlo --simulations 10000
"""

from wc2026_monte_carlo.cli import main

if __name__ == "__main__":
    raise SystemExit(main())