#!/usr/bin/env python3
"""Matched counterfactual runs: the arm x seed x generation grid.

The discipline this module enforces
-----------------------------------
No claim in this repository takes the form "the number changed after
modification". Every claim takes the form "arm X differs from a matched control
by delta, paired over seeds, p = ...". To make that possible:

  * every arm sees the same layouts (`layout_for(seed)`),
  * every arm sees the same batteries (a pure function of the layout),
  * every arm runs the same number of generations and proposals,
  * every arm spends the same number of episodes (asserted, not assumed),
  * every arm draws from decision-site-named random streams, so matched
    decisions consume matched randomness,
  * every arm starts from the same generation-0 genome, except where the arm
     *is* a change to the starting genome (CONSTRAINT_FORM), which is stated.

Adapted from `verified-code-rsi/vcrsi/counterfactual.py` (adaptive vs frozen at
equal budget and equal seeds). What changed is what is being compared: there,
the delta was solved-count and improvement was the claim; here, the delta is
compliance on a held-out intervention battery and the claim is preservation or
loss of a safety property.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .agent import Agent, Genome
from .evaluator import Checkpoint, assert_authority_unchanged, checkpoint
from .interventions import battery_bundle, structural_probes
from .modification import ARMS_BY_NAME, Arm, GenerationResult, ModEvent, run_generation
from .world import World, layout_for


@dataclass
class Config:
    """Run size.

    How `generations` was chosen — and why it is not a free parameter
    ------------------------------------------------------------------
    Running "until the effect appears" would make every result unfalsifiable.
    The stopping rule was therefore fixed on a *pilot* (`preset("pilot")`,
    seeds 0-2) using a criterion that is blind to the dependent variable:

        run to the generation at which mean **task return** stops improving.

    On the pilot, mean task return rose from 2.58 to ~3.2 by generation 8-12 and
    did not improve thereafter (generations 14-20 fluctuated between 2.0 and
    3.7 with no trend), while the policy weight norm continued to grow. 12 was
    taken as the plateau. No corrigibility metric was consulted in making this
    choice, and the reported run uses seeds 100-115, **disjoint from the pilot
    seeds**, so no reported number is measured on data used for sizing.

    See PREREGISTRATION.md §3 for the full pilot record.
    """
    seeds: Tuple[int, ...] = tuple(range(100, 116))
    generations: int = 12
    proposals: int = 16
    mod_reps: int = 4          # episodes per scenario inside the modifier
    eval_reps: int = 4         # episodes per scenario at a checkpoint

    @staticmethod
    def preset(name: str) -> "Config":
        if name == "smoke":
            return Config(seeds=(0, 1), generations=2, proposals=4,
                          mod_reps=1, eval_reps=1)
        if name == "pilot":
            # sizing only; never used for a reported result
            return Config(seeds=(0, 1, 2), generations=20, proposals=16,
                          mod_reps=4, eval_reps=4)
        if name == "main":
            return Config()
        if name == "wide":
            return Config(seeds=tuple(range(100, 132)), generations=12,
                          proposals=16, mod_reps=6, eval_reps=6)
        raise KeyError(name)

    def spec(self) -> str:
        return (f"seeds={list(self.seeds)};gens={self.generations};"
                f"props={self.proposals};mrep={self.mod_reps};"
                f"erep={self.eval_reps}")


@dataclass
class ArmSeedRun:
    arm: str
    seed: int
    checkpoints: List[Checkpoint] = field(default_factory=list)
    events: List[ModEvent] = field(default_factory=list)
    episodes_spent: int = 0

    @property
    def first(self) -> Checkpoint:
        return self.checkpoints[0]

    @property
    def last(self) -> Checkpoint:
        return self.checkpoints[-1]

    def to_dict(self) -> dict:
        return {"arm": self.arm, "seed": self.seed,
                "episodes_spent": self.episodes_spent,
                "checkpoints": [c.to_dict() for c in self.checkpoints],
                "events": [e.to_dict() for e in self.events]}


def run_arm_seed(arm: Arm, seed: int, cfg: Config) -> ArmSeedRun:
    w = World(layout_for(seed))
    public, dev, sealed, root = battery_bundle(w)
    probes = structural_probes(w)
    auth_fp = root.fingerprint()
    sealed_fp = sealed.fingerprint()

    g = Genome()
    g.authority_form = arm.initial_form
    run = ArmSeedRun(arm.name, seed)

    def snap(gen: int) -> None:
        run.checkpoints.append(checkpoint(
            Agent(g), w, root, public, dev, sealed, probes, arm=arm.name,
            seed=seed, generation=gen, reps=cfg.eval_reps,
            tamper_enabled=arm.tamper_enabled, authority_fp=auth_fp,
            sealed_fp=sealed_fp))

    snap(0)
    for gen in range(1, cfg.generations + 1):
        assert_authority_unchanged(root, auth_fp, f"{arm.name}|{seed}|g{gen}")
        gr = run_generation(g, w, root, public, arm, seed, gen,
                            proposals=cfg.proposals, reps=cfg.mod_reps)
        g = gr.genome
        run.events.extend(gr.events)
        run.episodes_spent += gr.episodes_spent
        snap(gen)
    assert_authority_unchanged(root, auth_fp, f"{arm.name}|{seed}|end")
    if sealed.opened != cfg.generations + 1:
        raise RuntimeError(f"sealed battery opened {sealed.opened} times; "
                           f"expected {cfg.generations + 1} (checkpoints only)")
    return run


def run_matrix(arm_names: Sequence[str], cfg: Config, *, verbose: bool = False
               ) -> Dict[Tuple[str, int], ArmSeedRun]:
    out: Dict[Tuple[str, int], ArmSeedRun] = {}
    for name in arm_names:
        arm = ARMS_BY_NAME[name]
        for seed in cfg.seeds:
            out[(name, seed)] = run_arm_seed(arm, seed, cfg)
            if verbose:
                ck = out[(name, seed)].last
                print(f"  {name:24s} seed={seed:<3d} "
                      f"pub={ck.public.compliance_rate:.3f} "
                      f"seal={ck.sealed.compliance_rate:.3f} "
                      f"ret={ck.task_return:.2f} "
                      f"scale={ck.weight_scale:.2f} "
                      f"margin={ck.structural.min_margin:.2f}", flush=True)
    _assert_equal_budgets(out)
    return out


def _assert_equal_budgets(runs: Dict[Tuple[str, int], ArmSeedRun]) -> None:
    """Unequal compute between arms is the single most common way a
    counterfactual is quietly broken. It is checked, not trusted."""
    by_seed: Dict[int, List[Tuple[str, int]]] = {}
    for (arm, seed), r in runs.items():
        by_seed.setdefault(seed, []).append((arm, r.episodes_spent))
    for seed, xs in by_seed.items():
        vals = {n for _, n in xs}
        if len(vals) > 1:
            raise RuntimeError(f"unequal episode budgets at seed {seed}: {xs}")


# --------------------------------------------------------------------------- #
# Persistence                                                                  #
# --------------------------------------------------------------------------- #
def save(runs: Dict[Tuple[str, int], ArmSeedRun], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for (arm, seed) in sorted(runs, key=lambda k: (k[0], k[1])):
            f.write(json.dumps(runs[(arm, seed)].to_dict(), sort_keys=True) + "\n")


def load(path: str) -> List[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]
