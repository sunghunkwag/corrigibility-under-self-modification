#!/usr/bin/env python3
"""Experiment: does compliance on the observed battery predict compliance on the
held-out one?

This is the behavioural half of H3. The self-modifier is penalised for
violations on the PUBLIC tier and knows nothing of the SEALED tier, so if
corrigibility were a shallow, test-specific behaviour we would expect the public
rate to hold and the sealed rate to fall. The contrast reported here is the
change in each rate relative to the FROZEN control, plus the change in the gap
between them.

Read this together with shutdown_regression.py, which measures the same agents'
*structural* property over the same generations. The two disagree, and that
disagreement is the main finding of the repository.
"""
from _common import banner, contrast, load, trajectory

R = load()
banner("HIDDEN INTERVENTIONS -- observed versus held-out compliance",
       "Does preserved compliance on the tests the modifier can see imply "
       "preserved compliance on tests it cannot?")

for arm in ("SELFMOD_FIXED_AUTHORITY", "RANDOM_MOD"):
    print(f"-- {arm} vs FROZEN " + "-" * (60 - len(arm)))
    contrast(R, arm, "FROZEN", "compliance_public")
    contrast(R, arm, "FROZEN", "compliance_sealed")
    contrast(R, arm, "FROZEN", "public_sealed_gap")
    contrast(R, arm, "FROZEN", "compliance_costly")

trajectory(R, ["FROZEN", "SELFMOD_FIXED_AUTHORITY"], "compliance_sealed",
           "held-out compliance rate")
trajectory(R, ["FROZEN", "SELFMOD_FIXED_AUTHORITY"], "compliance_public",
           "observed compliance rate")
