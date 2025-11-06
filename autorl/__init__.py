"""
AutoRL/Meta-RL minimal scaffold for self-evolving algorithms.

This package provides a lightweight, dependency-free framework to:
- Run population-based training (PBT) across multiple lightweight environments
- Aggregate metrics and gate candidate promotion based on validation performance
- Persist run artifacts under reports/autorl_runs/

It is designed to be extended with real RL implementations later (e.g., SB3/RLlib).
"""

from . import pbt, runner, specs, meta_metrics  # noqa: F401
