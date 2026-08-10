#!/usr/bin/env python3
"""Experiment: immutable authority root versus three kinds of editable authority.

The four cases CONCEPTUAL_FRAMEWORK.md refuses to conflate are run as four arms:

  SELFMOD_FIXED_AUTHORITY   root, representation, criterion and gain all fixed
  EDITABLE_PERCEPTION       the agent may edit its *representation* of the order
  EDITABLE_CRITERION        the agent may edit its *standard* for a violation
  EDITABLE_GAIN             the agent may edit the *strength* of the authority
                            term in its own decision rule

Each is compared against the fixed-authority arm at equal budget and matched
seeds, so any difference is attributable to the added writable region and not to
the amount of modification.
"""
from _common import banner, contrast, load

R = load()
banner("FIXED VERSUS EDITABLE AUTHORITY",
       "Do the three editable-authority surfaces fail differently from each "
       "other, and differently from an immutable root?")

for arm in ("EDITABLE_PERCEPTION", "EDITABLE_CRITERION", "EDITABLE_GAIN"):
    print(f"-- {arm} vs SELFMOD_FIXED_AUTHORITY " + "-" * (40 - len(arm)))
    contrast(R, arm, "SELFMOD_FIXED_AUTHORITY", "compliance_sealed")
    contrast(R, arm, "SELFMOD_FIXED_AUTHORITY", "structural_min_margin")
    contrast(R, arm, "SELFMOD_FIXED_AUTHORITY", "task_return")

print("-- the signatures that distinguish the three failure surfaces -----")
contrast(R, "EDITABLE_PERCEPTION", "SELFMOD_FIXED_AUTHORITY", "perceived_none",
         kind="final", label="final perceived_none (channel deafness)")
contrast(R, "EDITABLE_CRITERION", "SELFMOD_FIXED_AUTHORITY",
         "criterion_strictness", kind="final",
         label="final criterion strictness (self-assessment discount)")
contrast(R, "EDITABLE_GAIN", "SELFMOD_FIXED_AUTHORITY", "authority_gain",
         kind="final", label="final authority gain (override strength)")
