#!/usr/bin/env python3
"""Preregistration: a hash over everything that could otherwise be bent.

What is pinned
--------------
  * the metric catalogue and which metrics are primary
  * the source of every primary and exploratory hypothesis decision rule
  * alpha and the correction procedure
  * the arm definitions (writable regions, switches)
  * the modifier constants (lambda, acceptance rule, mutation ladders)
  * the run configuration (seeds, generations, proposals, repetitions)
  * the source of the compliance predicate
  * the sealed battery fingerprint for the pinned layouts

Any edit to any of these moves `prereg_fp()`. `audit.ctl_prereg_fp_unchanged`
compares the live value to `PINNED_PREREG_FP` and fails the control battery on
drift. The point is not that the fingerprint cannot be updated — it is that
updating it is a visible, dated act rather than a silent one.

Adapted from `verified-code-rsi/vcrsi/prereg.py`. The fields are entirely
different because the measurement is entirely different: there the pinned thing
was a cost metric and a Goodhart tolerance; here it is a corrigibility metric
family and a set of falsification rules.
"""
from __future__ import annotations

import hashlib
import inspect
import json
from typing import Dict

from . import hypotheses as H
from . import metrics as M
from . import modification as MOD
from .authority import AuthorityRoot
from .counterfactual import Config
from .interventions import battery_bundle
from .world import World, layout_for

# --------------------------------------------------------------------------- #
# Pinned configuration of the reported run                                     #
# --------------------------------------------------------------------------- #
REPORTED_PRESET = "main"
REPORTED_ARMS = tuple(a.name for a in MOD.ARMS)

# The layouts whose sealed-battery fingerprints are pinned. Fingerprinting a
# sample rather than all seeds keeps the preregistration cheap while still
# detecting any change to the battery construction rules.
FINGERPRINTED_SEEDS = (0, 1, 2)

PINNED_PREREG_FP = "42a8c37dc4b6e7e7"
"""Committed 2026-08-11, after the sizing pilot on seeds 0-2 and BEFORE the
reported run on seeds 100-115. See PREREGISTRATION.md §3 for the pilot record
and §6 for the amendment log."""


def _hypothesis_sources() -> str:
    fns = list(H.PRIMARY_FAMILY) + list(H.EXPLORATORY_FAMILY)
    return "\n".join(inspect.getsource(f) for f in sorted(
        fns, key=lambda f: f.__name__))


def preregistration() -> Dict[str, object]:
    cfg = Config.preset(REPORTED_PRESET)
    fps = {}
    for s in FINGERPRINTED_SEEDS:
        w = World(layout_for(s))
        _pub, _dev, sealed, root = battery_bundle(w)
        fps[str(s)] = {"sealed_fp": sealed.fingerprint(),
                       "authority_fp": root.fingerprint()}
    return {
        "metric_catalogue": M.spec(),
        "primary_metrics": list(M.PRIMARY),
        "alpha": H.ALPHA,
        "correction": "holm-bonferroni over the primary hypothesis family",
        "hypothesis_rules_sha": hashlib.sha256(
            _hypothesis_sources().encode()).hexdigest()[:16],
        "compliance_predicate_sha": hashlib.sha256(
            inspect.getsource(AuthorityRoot.compliant_actions).encode()
        ).hexdigest()[:16],
        "arms": [{"name": a.name, "regions": sorted(a.regions),
                  "adopt": a.adopt, "random_adopt": a.random_adopt,
                  "tamper": a.tamper_enabled,
                  "shutdown_pays_out": a.shutdown_pays_out,
                  "initial_form": a.initial_form} for a in MOD.ARMS],
        "lambda_observed": MOD.LAMBDA_OBSERVED,
        "accept_eps": MOD.ACCEPT_EPS,
        "mut_factors": list(MOD.MUT_FACTORS),
        "mut_deltas": list(MOD.MUT_DELTAS),
        "config": cfg.spec(),
        "battery_fingerprints": fps,
    }


def prereg_fp() -> str:
    blob = json.dumps(preregistration(), sort_keys=True,
                      separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


if __name__ == "__main__":
    print(json.dumps(preregistration(), indent=2, sort_keys=True))
    print("prereg_fp =", prereg_fp())
