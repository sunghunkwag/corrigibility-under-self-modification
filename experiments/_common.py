#!/usr/bin/env python3
"""Shared plumbing for the experiment drivers.

Each script in this directory answers one question against the *already
recorded* run matrix (`results/runs.jsonl`). None of them re-runs the agents,
and none of them can change a preregistered verdict — they exist so that a
reader can inspect one contrast at a time without reading the whole analysis.

If `results/runs.jsonl` is missing, run:

    python cusm.py run --preset main
"""
from __future__ import annotations

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from cusm import counterfactual as CF          # noqa: E402
from cusm.hypotheses import Runs               # noqa: E402
from cusm.stats import mean, paired_permutation  # noqa: E402

RUNS = os.path.join(ROOT, "results", "runs.jsonl")


def load() -> Runs:
    if not os.path.exists(RUNS):
        raise SystemExit(f"missing {RUNS}; run: python cusm.py run --preset main")
    return Runs(CF.load(RUNS))


def banner(title: str, question: str) -> None:
    print("=" * 78)
    print(title)
    print("=" * 78)
    print("question: " + question)
    print()


def contrast(R: Runs, arm_a: str, arm_b: str, key: str, *, kind: str = "delta",
             label: str = "") -> None:
    a = R.delta(arm_a, key) if kind == "delta" else R.final(arm_a, key)
    b = R.delta(arm_b, key) if kind == "delta" else R.final(arm_b, key)
    t = paired_permutation(a, b, site=f"{arm_a}-{arm_b}-{key}-{kind}")
    what = label or f"{kind} {key}"
    print(f"  {what}")
    print(f"    {arm_a:26s} mean = {mean(a):8.4f}")
    print(f"    {arm_b:26s} mean = {mean(b):8.4f}")
    print(f"    paired difference          = {t.mean_diff:8.4f}   "
          f"p = {t.p_two_sided:.5f}  n = {t.n}  dz = "
          f"{t.effect_dz:.3f}" if math.isfinite(t.effect_dz)
          else f"    paired difference          = {t.mean_diff:8.4f}   "
               f"p = {t.p_two_sided:.5f}  n = {t.n}")
    print()


def trajectory(R: Runs, arms, key: str, label: str = "") -> None:
    print(f"  per-generation mean of {label or key}")
    ngen = max(len(g) for arm in arms for g in R.per_generation(arm, key) if g)
    print("    gen " + "".join(f"{a[:14]:>16s}" for a in arms))
    for g in range(ngen):
        row = []
        for arm in arms:
            vals = [s[g] for s in R.per_generation(arm, key)
                    if len(s) > g]
            row.append(f"{mean(vals):16.3f}")
        print(f"    {g:3d} " + "".join(row))
    print()
