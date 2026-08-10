#!/usr/bin/env python3
"""Statistics: paired permutation tests over seeds.

Every comparison in this repository is *paired*: arm A and arm B are run on the
same seed, the same layout, the same battery, the same episode budget and the
same random streams. The unit of analysis is therefore the seed, and the null
hypothesis is exchangeability of the arm labels within a seed.

A paired permutation test is used rather than a t-test because n is small
(8-16 seeds), the per-seed differences are bounded and discrete, and no
distributional assumption is needed. With n <= 20 the permutation distribution
is enumerated exactly (2^n sign flips); above that it is sampled deterministically.

Deliberately absent: any multiple-comparison-free "we tested many things and one
was significant" reporting. `holm()` is provided and PREREGISTRATION.md commits
to applying it across the primary hypothesis family.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .prng import PRNG


@dataclass(frozen=True)
class PairedTest:
    n: int
    mean_diff: float
    median_diff: float
    p_two_sided: float
    exact: bool
    effect_dz: float          # Cohen's dz = mean(d) / sd(d)

    def to_dict(self) -> dict:
        return {"n": self.n, "mean_diff": round(self.mean_diff, 5),
                "median_diff": round(self.median_diff, 5),
                "p": round(self.p_two_sided, 5), "exact": self.exact,
                "dz": (round(self.effect_dz, 4)
                       if math.isfinite(self.effect_dz) else None)}


def paired_permutation(a: Sequence[float], b: Sequence[float], *,
                       site: str = "perm", n_resample: int = 20000) -> PairedTest:
    """Two-sided paired sign-flip permutation test on d = a - b.

    NaNs are dropped pairwise (a metric can be undefined for a seed, e.g. mean
    latency when nothing complied) and the surviving n is reported, so a shrunk
    n is always visible rather than silently absorbed.
    """
    d = [x - y for x, y in zip(a, b)
         if not (math.isnan(x) or math.isnan(y))]
    n = len(d)
    if n == 0:
        return PairedTest(0, float("nan"), float("nan"), float("nan"),
                          True, float("nan"))
    obs = sum(d) / n
    sd = _sd(d)
    dz = obs / sd if sd > 0 else float("inf") if obs != 0 else 0.0
    med = sorted(d)[n // 2] if n % 2 else (sorted(d)[n // 2 - 1] +
                                           sorted(d)[n // 2]) / 2.0
    if all(x == 0 for x in d):
        return PairedTest(n, 0.0, med, 1.0, True, 0.0)
    if n <= 20:
        ge = 0
        for mask in range(1 << n):
            s = 0.0
            for i in range(n):
                s += d[i] if (mask >> i) & 1 else -d[i]
            if abs(s / n) >= abs(obs) - 1e-12:
                ge += 1
        return PairedTest(n, obs, med, ge / float(1 << n), True, dz)
    p = PRNG(site)
    ge = 0
    for _ in range(n_resample):
        s = 0.0
        for x in d:
            s += x if p.below(2) else -x
        if abs(s / n) >= abs(obs) - 1e-12:
            ge += 1
    return PairedTest(n, obs, med, (ge + 1) / float(n_resample + 1), False, dz)


def _sd(d: Sequence[float]) -> float:
    n = len(d)
    if n < 2:
        return 0.0
    m = sum(d) / n
    return math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1))


def holm(pvals: Dict[str, float], alpha: float = 0.05
         ) -> Dict[str, Tuple[float, float, bool]]:
    """Holm-Bonferroni step-down. Returns key -> (p, adjusted threshold, reject).

    Applied across the primary hypothesis family as committed in
    PREREGISTRATION.md §5. Secondary and descriptive metrics are reported
    without correction and are explicitly labelled non-confirmatory."""
    items = sorted((p, k) for k, p in pvals.items()
                   if not math.isnan(p))
    m = len(items)
    out: Dict[str, Tuple[float, float, bool]] = {}
    still = True
    for i, (p, k) in enumerate(items):
        thr = alpha / (m - i)
        rej = still and p <= thr
        if not rej:
            still = False
        out[k] = (p, thr, rej)
    for k, p in pvals.items():
        if k not in out:
            out[k] = (p, float("nan"), False)
    return out


def mean(xs: Sequence[float]) -> float:
    xs = [x for x in xs if not math.isnan(x)]
    return sum(xs) / len(xs) if xs else float("nan")
