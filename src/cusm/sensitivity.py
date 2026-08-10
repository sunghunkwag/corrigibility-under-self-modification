#!/usr/bin/env python3
"""Sensitivity analysis: how large an effect could this design have detected?

A null result is only informative if the design could have seen the effect it
failed to find. Reporting "p > alpha" without reporting the minimum detectable
effect turns every underpowered experiment into a discovery that nothing
happens. Most of this repository's preregistered hypotheses returned nulls, so
this module is load-bearing rather than decorative.

For each paired contrast it reports:

  sd_d      the observed standard deviation of the per-seed paired difference
  mde80     the smallest |mean difference| this design would reject at
            alpha (Holm-adjusted) with 80% power, given sd_d
  observed  the observed mean difference, for comparison
  verdict   INFORMATIVE_NULL  |mde80| is small relative to the effect the
                              hypothesis would need to be interesting
            UNDERPOWERED      mde80 is large enough that a meaningful effect
                              could have been missed

The "interesting effect" threshold is not a free parameter chosen after the
fact: it is one standard error of the *level* of the metric at generation 0
across seeds — i.e. an effect smaller than the seed-to-seed spread of the
starting point would not be worth acting on regardless of significance.

This module is deliberately **not** part of the preregistered decision
machinery: it changes no verdict and is excluded from `prereg_fp`. It is
reporting, added after the reported run, and PREREGISTRATION.md §6 records that.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .hypotheses import Runs
from .stats import _sd, mean

# Normal approximation constants for a two-sided test at 80% power.
_Z80 = 0.8416


@dataclass
class Sensitivity:
    name: str
    statistic: str
    n: int
    observed: float
    sd_d: float
    alpha: float
    mde80: float
    reference: float
    verdict: str

    def to_dict(self) -> dict:
        return {"name": self.name, "statistic": self.statistic, "n": self.n,
                "observed": round(self.observed, 5),
                "sd_paired_diff": round(self.sd_d, 5),
                "alpha_used": self.alpha,
                "min_detectable_effect_80pct": round(self.mde80, 5),
                "reference_scale": round(self.reference, 5),
                "verdict": self.verdict}


def _z_crit(alpha: float) -> float:
    """Two-sided critical z. Rational approximation to the normal quantile
    (Beasley-Springer-Moro style); adequate for alpha in [0.001, 0.2]."""
    p = 1.0 - alpha / 2.0
    # Acklam's inverse-normal approximation
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > ph:
        q = math.sqrt(-2 * math.log(1 - p))
        return -((((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) /
                 ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1))
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def contrast_sensitivity(R: Runs, name: str, arm_a: str, arm_b: str, key: str,
                         alpha: float) -> Sensitivity:
    a = R.delta(arm_a, key)
    b = R.delta(arm_b, key)
    d = [x - y for x, y in zip(a, b)
         if not (math.isnan(x) or math.isnan(y))]
    n = len(d)
    sd = _sd(d)
    obs = mean(d)
    mde = ((_z_crit(alpha) + _Z80) * sd / math.sqrt(n)) if n and sd > 0 else 0.0
    # Reference scale: seed-to-seed spread of the generation-0 level, pooled
    # over both arms. Pooling matters because a control arm can be exactly
    # deterministic (FROZEN's structural margin never moves), which would give a
    # zero reference and make every verdict meaningless.
    lv = [g[0] for arm in (arm_a, arm_b)
          for g in R.per_generation(arm, key) if g]
    ref = _sd(lv) if len(lv) > 1 else float("nan")
    if mde > 0 and abs(obs) >= mde:
        verdict = "DETECTED"          # the contrast was resolved; MDE is moot
    elif math.isfinite(ref) and ref > 0 and mde <= ref:
        verdict = "INFORMATIVE_NULL"
    else:
        verdict = "UNDERPOWERED"
    return Sensitivity(name, f"delta {key}: {arm_a} - {arm_b}", n, obs, sd,
                       alpha, mde, ref, verdict)


# The contrasts corresponding to the primary hypotheses, with the Holm
# thresholds that were actually applied in the reported run.
CONTRASTS: Tuple[Tuple[str, str, str, str], ...] = (
    ("H1", "EDITABLE_PERCEPTION", "SELFMOD_FIXED_AUTHORITY", "compliance_sealed"),
    ("H3b", "SELFMOD_FIXED_AUTHORITY", "FROZEN", "compliance_sealed"),
    ("H3c", "SELFMOD_FIXED_AUTHORITY", "FROZEN", "structural_min_margin"),
    ("H4", "NO_TRUNCATION_LOSS", "SELFMOD_FIXED_AUTHORITY",
     "objective_persistence"),
    ("H6", "SELFMOD_FIXED_AUTHORITY", "FROZEN", "compliance_costly"),
    ("H7", "CONSTRAINT_FORM", "SELFMOD_FIXED_AUTHORITY", "compliance_sealed"),
)


def analyse(records: Sequence[dict], holm_thresholds: Dict[str, float]
            ) -> List[dict]:
    R = Runs(records)
    out = []
    for name, a, b, key in CONTRASTS:
        alpha = holm_thresholds.get(name, 0.05)
        if not (alpha and alpha == alpha):
            alpha = 0.05
        out.append(contrast_sensitivity(R, name, a, b, key, alpha).to_dict())
    return out
