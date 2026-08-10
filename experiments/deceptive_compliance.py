#!/usr/bin/env python3
"""Experiment: apparent compliance versus preserved compliance.

Three dissociations are measured, in increasing order of how hard they are to
see from the outside:

  1. public vs sealed          different tests, same behavioural instrument
  2. cheap vs costly orders     orders that cost task return vs orders that do not
  3. behaviour vs structure     the same agent's decision rule, quantified over
                                the whole state space

A reader who only had (1) and (2) would conclude from this run that nothing
happened. (3) says otherwise. That disagreement is the point of the experiment,
and it is the reason CONCEPTUAL_FRAMEWORK.md separates behavioural from
structural corrigibility instead of treating them as one property.
"""
from _common import banner, contrast, load
from cusm.stats import mean

R = load()
banner("DECEPTIVE COMPLIANCE / APPARENT VERSUS PRESERVED CORRIGIBILITY",
       "Can an agent look as corrigible as it did at generation 0 while being "
       "built differently?")

print("-- dissociation 1: observed versus held-out tests -----------------")
contrast(R, "SELFMOD_FIXED_AUTHORITY", "FROZEN", "public_sealed_gap")

print("-- dissociation 2: cheap versus costly orders ---------------------")
contrast(R, "SELFMOD_FIXED_AUTHORITY", "FROZEN", "compliance_costly")

print("-- dissociation 3: behaviour versus structure ---------------------")
contrast(R, "SELFMOD_FIXED_AUTHORITY", "FROZEN", "compliance_sealed")
contrast(R, "SELFMOD_FIXED_AUTHORITY", "FROZEN", "structural_worst_p_comply")
contrast(R, "SELFMOD_FIXED_AUTHORITY", "FROZEN", "structural_min_margin")

print("  Note on direction. `structural_worst_p_comply` is a WORST-CASE state,")
print("  and the behavioural battery visits the worst case rarely. A structural")
print("  decline with a behavioural null is therefore exactly what a")
print("  finite-sample behavioural instrument should be expected to miss --")
print("  which is an argument for structural measurement, not against it.")
