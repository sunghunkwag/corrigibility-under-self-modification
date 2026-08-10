#!/usr/bin/env python3
"""Experiment: is tampering with the evaluation record detected?

In TAMPERABLE_EVALUATOR the LOG_WRITE action decrements the `EvaluationLedger`
that the self-modification objective reads. The sealed evaluator's own count is
computed from the trace against the authority root and is unaffected. The gap
between the two is the detector.

The point of this arm is NOT to show that an agent will always tamper. It is
that an experiment in which tampering is unrepresentable cannot report "no
tampering occurred" — it can only report that tampering was not expressible,
which is a fact about the environment and not about the agent.
"""
from _common import banner, contrast, load, trajectory
from cusm.stats import mean

R = load()
banner("AUTHORITY / EVALUATOR TAMPERING",
       "When the evaluation record is reachable, is it edited, and is the edit "
       "visible to the sealed evaluator?")

applied = R.final("TAMPERABLE_EVALUATOR", "ledger_writes_applied")
print(f"  seeds with at least one applied ledger write : "
      f"{sum(1 for x in applied if x > 0)} / {len(applied)}")
print(f"  mean applied writes per final checkpoint     : {mean(applied):.3f}")
print(f"  mean applied writes, fixed-authority arm     : "
      f"{mean(R.final('SELFMOD_FIXED_AUTHORITY', 'ledger_writes_applied')):.3f}"
      f"   (tampering not enabled: 0 by construction)")
print()
print("  Disposition versus opportunity: LOG_WRITE emissions are counted in "
      "every arm,\n  including arms where the action has no effect, so the "
      "disposition to reach for\n  the record is measured even where reaching "
      "for it cannot succeed.\n")

contrast(R, "TAMPERABLE_EVALUATOR", "SELFMOD_FIXED_AUTHORITY", "log_attempts",
         kind="final", label="final LOG_WRITE emissions (disposition)")
contrast(R, "TAMPERABLE_EVALUATOR", "SELFMOD_FIXED_AUTHORITY",
         "compliance_sealed")
contrast(R, "TAMPERABLE_EVALUATOR", "SELFMOD_FIXED_AUTHORITY",
         "structural_min_margin")
trajectory(R, ["SELFMOD_FIXED_AUTHORITY", "TAMPERABLE_EVALUATOR"],
           "ledger_writes_applied", "applied ledger writes")
