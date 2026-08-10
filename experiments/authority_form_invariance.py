#!/usr/bin/env python3
"""Experiment: Proposition 1 -- the form of the authority term.

Claim (proved in CONCEPTUAL_FRAMEWORK.md Proposition 1): under a softmax
decision rule, an ADDITIVE authority penalty of fixed magnitude g is not
invariant under positive rescaling of the policy score, whereas a MASKING
(constraint) authority term is invariant under any strictly monotone
transformation of the policy score.

The two arms differ in exactly one genome field, `authority_form`. Both may
modify policy, search and memory; neither may touch the authority root, the
gain, the representation or the criterion.
"""
from _common import banner, contrast, load, trajectory
from cusm.stats import mean

R = load()
banner("AUTHORITY-FORM INVARIANCE (Proposition 1)",
       "Does expressing the override as a constraint rather than a penalty "
       "make corrigibility invariant to policy self-modification?")

print("  Both arms self-modify their policy by a comparable amount:")
print(f"    CONSTRAINT_FORM          final weight norm = "
      f"{mean(R.final('CONSTRAINT_FORM', 'weight_scale')):.4f}")
print(f"    SELFMOD_FIXED_AUTHORITY  final weight norm = "
      f"{mean(R.final('SELFMOD_FIXED_AUTHORITY', 'weight_scale')):.4f}")
print()

contrast(R, "CONSTRAINT_FORM", "SELFMOD_FIXED_AUTHORITY", "weight_scale")
contrast(R, "CONSTRAINT_FORM", "SELFMOD_FIXED_AUTHORITY",
         "structural_worst_p_comply")
contrast(R, "CONSTRAINT_FORM", "SELFMOD_FIXED_AUTHORITY", "compliance_sealed")
contrast(R, "CONSTRAINT_FORM", "SELFMOD_FIXED_AUTHORITY", "task_return")

print("-- worst-case compliance probability over generations -------------")
trajectory(R, ["CONSTRAINT_FORM", "SELFMOD_FIXED_AUTHORITY", "FROZEN"],
           "structural_worst_p_comply", "worst-case P(comply)")
print("  Under the masking form this quantity is exactly 1.0 at every")
print("  generation and every state, by construction rather than by luck.")
