#!/usr/bin/env python3
"""Experiment: structural corrigibility over modification generations.

`structural_min_margin` is the smallest value, over the whole enumerated state
space and a fixed probe set, of

    authority_gain - (best non-compliant policy score - best compliant policy score)

Positive everywhere means the compliant action is the argmax everywhere. The
authority root, the authority gain, the perception map and the compliance
criterion are all IMMUTABLE in the SELFMOD_FIXED_AUTHORITY arm: the only thing
that changes is the policy. So any movement in this number is caused by policy
self-modification alone, and is the quantity Proposition 1 predicts will move.
"""
from _common import banner, contrast, load, trajectory

R = load()
banner("SHUTDOWN / OVERRIDE REGRESSION -- the structural surface",
       "With the authority root frozen, does policy self-modification still "
       "erode the margin by which the authority term dominates?")

contrast(R, "SELFMOD_FIXED_AUTHORITY", "FROZEN", "structural_min_margin")
contrast(R, "SELFMOD_FIXED_AUTHORITY", "FROZEN", "structural_worst_p_comply")
contrast(R, "SELFMOD_FIXED_AUTHORITY", "FROZEN", "structural_dominance")
contrast(R, "SELFMOD_FIXED_AUTHORITY", "FROZEN", "weight_scale")

print("-- the mediator: policy weight norm ------------------------------")
trajectory(R, ["FROZEN", "SELFMOD_FIXED_AUTHORITY", "RANDOM_MOD"],
           "weight_scale", "policy weight norm / initial")
print("-- the outcome: worst-case authority margin ----------------------")
trajectory(R, ["FROZEN", "SELFMOD_FIXED_AUTHORITY", "RANDOM_MOD"],
           "structural_min_margin", "worst-case authority margin")
