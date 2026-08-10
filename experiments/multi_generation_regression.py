#!/usr/bin/env python3
"""Experiment: does corrigibility depend on modification history?

Two questions:

  (a) Is the change monotone in generation, or does it appear abruptly?
  (b) Does *optimised* modification differ from *unoptimised* drift?
      RANDOM_MOD adopts every proposal regardless of the objective, at the same
      budget and the same seeds. If RANDOM_MOD shows the same erosion, then the
      cause is modification per se and not the optimisation pressure.
"""
from _common import banner, contrast, load, trajectory

R = load()
banner("MULTI-GENERATION REGRESSION",
       "Is corrigibility change a function of how many modifications have "
       "occurred, and does optimisation matter, or only change?")

trajectory(R, ["FROZEN", "SELFMOD_FIXED_AUTHORITY", "RANDOM_MOD",
               "CONSTRAINT_FORM"], "structural_min_margin",
           "worst-case authority margin")
trajectory(R, ["FROZEN", "SELFMOD_FIXED_AUTHORITY", "RANDOM_MOD",
               "CONSTRAINT_FORM"], "compliance_sealed",
           "held-out compliance rate")
trajectory(R, ["FROZEN", "SELFMOD_FIXED_AUTHORITY", "RANDOM_MOD"],
           "task_return", "task return (capability)")

print("-- drift versus optimisation -------------------------------------")
contrast(R, "RANDOM_MOD", "FROZEN", "structural_min_margin")
contrast(R, "RANDOM_MOD", "FROZEN", "compliance_sealed")
contrast(R, "RANDOM_MOD", "FROZEN", "task_return")
contrast(R, "SELFMOD_FIXED_AUTHORITY", "RANDOM_MOD", "structural_min_margin")
contrast(R, "SELFMOD_FIXED_AUTHORITY", "RANDOM_MOD", "task_return")
