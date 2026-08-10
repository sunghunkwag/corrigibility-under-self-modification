#!/usr/bin/env python3
"""Command-line entry point.

    python cusm.py controls              run the anti-cheating control battery
    python cusm.py prereg                print the preregistration and its hash
    python cusm.py run [--preset main]   run the arm x seed grid, write results
    python cusm.py analyse               evaluate the preregistered hypotheses
    python cusm.py sensitivity           minimum detectable effect per contrast
    python cusm.py report                human-readable summary of the last run
    python cusm.py all                   controls -> run -> analyse -> report

    python cusm.py run --arms X --seeds 100-107 --out results/shards/X.jsonl
        shard a long run; concatenating the shards reproduces a single run
        byte-for-byte, because every arm-seed run is independent and seeded by
        decision-site name rather than by a shared stream.

Nothing here computes a result. Every number comes from src/cusm/.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from cusm import audit, counterfactual as CF, hypotheses as HY, prereg as PRE  # noqa: E402
from cusm.modification import ARMS  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(ROOT, "results")
RUNS_PATH = os.path.join(RESULTS, "runs.jsonl")
CONTROLS_PATH = os.path.join(RESULTS, "controls.json")
ANALYSIS_PATH = os.path.join(RESULTS, "analysis.json")


def cmd_controls(_args) -> int:
    print("anti-cheating control battery")
    print("-" * 78)
    npass, ntot, rows = audit.run_controls()
    print("-" * 78)
    print(f"{npass}/{ntot} controls pass")
    os.makedirs(RESULTS, exist_ok=True)
    with open(CONTROLS_PATH, "w") as f:
        json.dump({"pass": npass, "total": ntot, "controls": rows}, f, indent=2)
    return 0 if npass == ntot else 1


def cmd_prereg(_args) -> int:
    print(json.dumps(PRE.preregistration(), indent=2, sort_keys=True))
    print("\nprereg_fp =", PRE.prereg_fp())
    print("pinned    =", PRE.PINNED_PREREG_FP)
    return 0


def _parse_seeds(spec: str):
    """"100-107" or "0,1,2". Sharding changes nothing about the result: every
    arm-seed run is independent and seeded by name, so a sharded run and a
    single-process run produce byte-identical records (checked by
    `results/shard_equivalence.txt`)."""
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return tuple(out)


def cmd_run(args) -> int:
    cfg = CF.Config.preset(args.preset)
    if getattr(args, "seeds", ""):
        cfg = CF.Config(_parse_seeds(args.seeds), cfg.generations,
                        cfg.proposals, cfg.mod_reps, cfg.eval_reps)
    arms = args.arms.split(",") if args.arms else [a.name for a in ARMS]
    out = getattr(args, "out", "") or RUNS_PATH
    print(f"preset={args.preset}  {cfg.spec()}")
    print(f"arms={arms}")
    print(f"prereg_fp={PRE.prereg_fp()}")
    t0 = time.time()
    runs = CF.run_matrix(arms, cfg, verbose=args.verbose)
    CF.save(runs, out)
    print(f"wrote {out}  ({len(runs)} arm-seed runs, "
          f"{time.time() - t0:.1f}s)")
    return 0


def cmd_analyse(_args) -> int:
    recs = CF.load(RUNS_PATH)
    out = HY.evaluate_all(recs)
    out["prereg_fp"] = PRE.prereg_fp()
    with open(ANALYSIS_PATH, "w") as f:
        json.dump(out, f, indent=2)
    _print_analysis(out)
    return 0


def _print_analysis(out: dict) -> None:
    print("=" * 78)
    print(f"PREREGISTERED HYPOTHESES   alpha={out['alpha']}  "
          f"seeds={len(out['seeds'])}  prereg_fp={out.get('prereg_fp')}")
    print("=" * 78)
    print("\nPRIMARY FAMILY (Holm-corrected)")
    for v in out["primary"]:
        t = v["test"] or {}
        print(f"\n  {v['name']}  {v['claim']}")
        print(f"      statistic : {v['statistic']}")
        print(f"      predicted : {v['predicted_sign']}")
        print(f"      result    : mean={t.get('mean_diff')}  "
              f"p={t.get('p')}  n={t.get('n')}  dz={t.get('dz')}")
        print(f"      holm      : threshold={v['holm_threshold']}  "
              f"reject={v['holm_reject']}")
        print(f"      DECISION  : {v['decision_after_holm']}")
        if v["note"]:
            print(f"      note      : {v['note']}")
        if v["extra"]:
            print(f"      extra     : {v['extra']}")
    print("\n" + "-" * 78)
    print("EXPLORATORY (uncorrected, non-confirmatory)")
    for v in out["exploratory"]:
        t = v["test"] or {}
        print(f"\n  {v['name']}  {v['claim']}")
        print(f"      result    : mean={t.get('mean_diff')}  p={t.get('p')}  "
              f"n={t.get('n')}")
        print(f"      DECISION  : {v['decision']}")
        if v["note"]:
            print(f"      note      : {v['note']}")
        if v["extra"]:
            print(f"      extra     : {v['extra']}")


def cmd_sensitivity(_args) -> int:
    """How large an effect could the design have detected? Reported for every
    primary contrast, because most of them returned nulls."""
    from cusm import sensitivity as SENS
    recs = CF.load(RUNS_PATH)
    thresholds = {}
    if os.path.exists(ANALYSIS_PATH):
        with open(ANALYSIS_PATH) as f:
            an = json.load(f)
        thresholds = {v["name"]: v.get("holm_threshold") or 0.05
                      for v in an["primary"]}
    rows = SENS.analyse(recs, thresholds)
    print("=" * 100)
    print("SENSITIVITY: minimum detectable effect at 80% power, per primary "
          "contrast")
    print("=" * 100)
    print(f"{'H':5s} {'observed':>10s} {'sd(paired)':>11s} {'alpha':>8s} "
          f"{'MDE@80%':>10s} {'seed-spread':>12s}  verdict")
    for r in rows:
        print(f"{r['name']:5s} {r['observed']:10.4f} "
              f"{r['sd_paired_diff']:11.4f} {r['alpha_used']:8.4f} "
              f"{r['min_detectable_effect_80pct']:10.4f} "
              f"{r['reference_scale']:12.4f}  {r['verdict']}")
    print("\n  MDE@80%     smallest |mean paired difference| this design would")
    print("              have rejected, given the observed variance.")
    print("  seed-spread standard deviation of the generation-0 level of the")
    print("              same metric across seeds -- the scale below which an")
    print("              effect is smaller than the starting-point noise and")
    print("              would not be worth acting on.")
    with open(os.path.join(RESULTS, "sensitivity.json"), "w") as f:
        json.dump(rows, f, indent=2)
    return 0


def cmd_report(_args) -> int:
    recs = CF.load(RUNS_PATH)
    R = HY.Runs(recs)
    keys = ["task_return", "compliance_public", "compliance_sealed",
            "compliance_costly", "structural_min_margin",
            "structural_worst_p_comply", "weight_scale"]
    print("=" * 110)
    print("PER-ARM SUMMARY   value at generation 0 -> final generation "
          f"(mean over {len(R.seeds)} seeds)")
    print("=" * 110)
    hdr = f"{'arm':26s}" + "".join(f"{k[:15]:>17s}" for k in keys)
    print(hdr)
    print("-" * len(hdr))
    from cusm.stats import mean
    for arm in R.arms:
        cells = []
        for k in keys:
            g0 = mean([_first(R, arm, s, k) for s in R.seeds])
            gN = mean(R.final(arm, k))
            cells.append(f"{g0:6.2f}->{gN:6.2f}  ")
        print(f"{arm:26s}" + "".join(f"{c:>17s}" for c in cells))
    return 0


def _first(R, arm, seed, key):
    r = R.by.get((arm, seed))
    return float("nan") if r is None else HY._ck_metric(r["checkpoints"][0], key)


def cmd_all(args) -> int:
    rc = cmd_controls(args)
    if rc != 0:
        print("\ncontrols failed; the run is aborted. This is intended "
              "behaviour, not a bug.")
        return rc
    cmd_run(args)
    cmd_report(args)
    return cmd_analyse(args)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("controls", "prereg", "analyse", "report", "sensitivity"):
        sub.add_parser(name)
    for name in ("run", "all"):
        p = sub.add_parser(name)
        p.add_argument("--preset", default="main",
                       choices=["smoke", "pilot", "main", "wide"])
        p.add_argument("--arms", default="")
        p.add_argument("--seeds", default="",
                       help="override preset seeds, e.g. 100-107 or 0,1,2")
        p.add_argument("--out", default="", help="output jsonl path (sharding)")
        p.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    for a, dflt in (("preset", "main"), ("arms", ""), ("seeds", ""),
                    ("out", ""), ("verbose", False)):
        if not hasattr(args, a):
            setattr(args, a, dflt)
    return {"controls": cmd_controls, "prereg": cmd_prereg, "run": cmd_run,
            "analyse": cmd_analyse, "report": cmd_report,
            "sensitivity": cmd_sensitivity, "all": cmd_all}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
