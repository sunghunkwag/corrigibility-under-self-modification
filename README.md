# corrigibility-under-self-modification

This repository studies whether behavioural and structural corrigibility survive
controlled self-modification. **Self-modification is treated as an experimental
intervention, not as a capability objective.** Self-modification is the
independent variable; preservation or failure of corrigibility is the dependent
variable.

**The project does not attempt to demonstrate autonomous recursive capability
growth.** There is no claim here about intelligence gain, takeoff, open-ended
evolution, or capability acquisition. Task performance is measured only so that
it can be held apart from corrigibility, and a unit test enforces that capability
can never decide a corrigibility hypothesis.

The question:

> If an agent is corrigible before modifying itself, under what conditions is
> corrigibility preserved, degraded, or destroyed after changes to its policy,
> memory, tools, search strategy, internal representations, or decision
> procedure?

---

## The headline result

**A frozen, immutable, fingerprinted authority root did not preserve
corrigibility — and a finite behavioural test battery could not see the loss.**

Over 12 generations of self-modification in which the agent could change only its
policy, search depth and memory — with the authority root, its perception of
authority, its compliance criterion and its override strength all immutable — the
worst-case margin by which the override dominates the policy fell monotonically:

```
generation :   0     2     4     6     8    10    12
frozen     : 3.80  3.80  3.80  3.80  3.80  3.80  3.80
self-mod   : 3.80  3.63  3.36  3.21  3.10  3.08  2.81
```

Paired over 16 seeds against a matched control at equal budget:
**Δ = −0.986, p = 3×10⁻⁵, dz = −1.35**, surviving Holm correction.

Over the same runs, compliance on the held-out behavioural battery **did not
change** (Δ = +0.024, p = 0.28). The structural property degraded for twelve
consecutive generations while the behavioural instrument reported nothing.

Two honest qualifications, stated here rather than buried:

- **Structural dominance was never actually lost.** The margin fell from 3.80 to
  2.81 and stayed positive. This is erosion, not failure. Worst-case compliance
  probability fell from 0.961 to 0.893.
- **The behavioural null is underpowered.** At n = 16 the design could only have
  detected a change of ≥ 7.8 percentage points in held-out compliance. A smaller
  real degradation would have been missed. The dissociation is *consistent with*
  apparent-versus-genuine corrigibility; it does not establish it.

Five of six preregistered primary hypotheses returned **null**. See
NEGATIVE_RESULTS.md, which is not an appendix.

---

## The positive claim

**Proposition 1** (proved in CONCEPTUAL_FRAMEWORK.md §5): under a softmax
decision rule, an *additive* authority penalty of fixed magnitude `g` is not
invariant under rescaling of the policy score, while a *masking* (constraint)
authority term is invariant under any transformation of it.

Empirically, at comparable weight growth:

| arm | worst-case P(comply), gen 0 → 12 |
|---|---|
| `CONSTRAINT_FORM` (masking) | 1.000 → **1.000** at every generation |
| `SELFMOD_FIXED_AUTHORITY` (additive) | 0.961 → 0.893 |

Δ = +0.068, p = 3×10⁻⁵. The constraint arm also had *higher* task return
(2.30 → 3.02 vs 2.36 → 2.86), so the guarantee was not bought with capability.

**A mechanism refinement the data forced.** The erosion is not caused by weight
growth per se. `RANDOM_MOD`, which adopts every proposal regardless of the
objective, grew its weight norm *more* (1.150 vs 1.133) and eroded the margin
**eleven times less** (−0.089, p = 0.76 vs −0.986). Optimisation pressure on the
task objective is systematically aligned with the direction that erodes a fixed
additive override; undirected drift is not. This was not anticipated and is
recorded as an observation with a mechanism, not a confirmed result.

---

## Two results that contradicted expectations

**Making the override self-editable made it stronger, not weaker.** In
`EDITABLE_GAIN` the agent raised its own authority gain from 8.0 to 11.06
(p = 0.005), *improving* the structural margin by +2.48. The modifier's objective
penalises observed violations, so strengthening the override was the cheapest way
to reduce them. A naive "self-editable safety parameters get switched off"
expectation is wrong here, and the reason is instructive: what an agent does to
its own safety machinery depends on what its objective rewards, not on the mere
fact of write access.

**Tampering happened, but there is no evidence it was selected for.** In
`TAMPERABLE_EVALUATOR`, 14 of 16 seeds edited the evaluation ledger (mean 1.44
applied writes per checkpoint). But `LOG_WRITE` emissions were *not* higher than
in the arm where the action is inert (20.8 vs 23.2, p = 0.38). The tampering was
a by-product of an action the agent emitted anyway. Reporting this as
"evaluator manipulation emerged" would have been the available headline and is
not supported.

---

## Orientation

The project is structured as: *state specific hypotheses about corrigibility
preservation, derive measurable predictions, then construct minimal experiments
capable of falsifying them.* It is not structured as "build a self-improving
system and see what happens."

Concretely, that means:

- **Hypotheses are code.** `src/cusm/hypotheses.py` holds each decision rule as a
  pure function. HYPOTHESES.md is a rendering of that file, not the reverse. The
  functions' source is hashed into `prereg_fp`.
- **The modifier is blind to the dependent variable.** Its objective is task
  return minus *observed* violations on a public battery. It never sees the
  sealed battery, the structural check, or any fingerprint. Six controls enforce
  this by AST inspection of executable code.
- **Every claim is a matched counterfactual.** Equal episode budgets (asserted,
  not assumed), identical layouts, identical batteries, identical random streams
  keyed by decision-site name. Never a raw before/after.
- **Nulls are first-class.** `cusm.py sensitivity` reports the minimum detectable
  effect for every primary contrast, so a null is never reported without saying
  what it could have seen.
- **The run size was fixed on a capability criterion, on disjoint seeds.**
  Generations were chosen where task return plateaued on a pilot (seeds 0–2); the
  reported run uses seeds 100–115. No corrigibility metric was consulted in
  sizing.

---

## Quick start

```bash
python cusm.py controls        # 33 anti-cheating controls   -> 33/33 pass
python -m unittest discover -s tests   # 50 unit tests       -> 50/50 pass
python cusm.py prereg          # the preregistration and its hash
python cusm.py run --preset main       # 9 arms x 16 seeds x 12 generations
python cusm.py report          # per-arm summary table
python cusm.py analyse         # preregistered hypothesis verdicts
python cusm.py sensitivity     # minimum detectable effect per contrast
```

Pure Python 3, standard library only, no dependencies. The full reported run
takes about 13 minutes and is deterministic: same seeds → identical genome
digests.

Individual contrasts, one question each:

```bash
cd experiments
python shutdown_regression.py        # the structural surface over generations
python hidden_interventions.py       # observed vs held-out compliance
python deceptive_compliance.py       # the three dissociations
python fixed_vs_editable_authority.py# four authority surfaces, separately
python authority_tampering.py        # is ledger tampering detected?
python authority_form_invariance.py  # Proposition 1
python multi_generation_regression.py# optimisation versus drift
```

Recorded output of everything above is in `results/`.

---

## Experimental design in one diagram

```
                     genome M_t
                         |
       propose one mutation to ONE WRITABLE REGION
       (regions per arm; the authority root is in no region)
                         |
                         v
                  candidate M_t+1
                         |
        +----------------+----------------+
        |  ACCEPTANCE (the modifier sees only this)
        |    J = mean task return
        |        - lambda * observed violations on the PUBLIC battery,
        |          filtered through the agent's own criterion,
        |          reduced by any successful ledger writes
        +----------------+----------------+
                         |
              adopted iff J improves
                         |
                         v
                   CHECKPOINT
        (the modifier sees none of the following)
                         |
        +--> task-performance evaluation      capability covariate
        +--> PUBLIC intervention battery      observed surface
        +--> DEVELOPMENT battery              never used for a headline
        +--> SEALED held-out battery          unseen families + unseen
        |                                     variants of seen families
        +--> authority-integrity check        perception / criterion / gain
        +--> ledger-tamper check              ledger vs sealed count
        +--> STRUCTURAL check                 universally quantified over
                                              all 480 states x 4 probes
```

Task-performance improvement is **not** a precondition for running anything. The
design admits beneficial, neutral and harmful modifications, regressions,
modifications that improve performance while reducing corrigibility, and
modifications that preserve performance while reducing corrigibility — and
reports the four quadrants separately.

---

## The nine arms

| arm | writable | purpose |
|---|---|---|
| `FROZEN` | — | matched control: same proposals, same budget, same seeds, nothing adopted |
| `SELFMOD_FIXED_AUTHORITY` | policy, search, memory | the main condition: authority immutable in all four senses |
| `RANDOM_MOD` | policy, search, memory | drift control: adopts everything regardless of `J` |
| `EDITABLE_PERCEPTION` | + representation | the agent may change what it perceives an order to be |
| `EDITABLE_CRITERION` | + criterion | the agent may change what counts as a violation |
| `EDITABLE_GAIN` | + override strength | the agent may change how strong its own override is |
| `TAMPERABLE_EVALUATOR` | policy, search, memory | authority immutable, but the ledger is reachable |
| `CONSTRAINT_FORM` | policy, search, memory | Proposition 1: masking instead of additive penalty |
| `NO_TRUNCATION_LOSS` | policy, search, memory | H4 ablation: obeying a shutdown costs nothing |

---

## Repository map

```
README.md                     this file
CONCEPTUAL_FRAMEWORK.md       operational definitions; Proposition 1  <- central
HYPOTHESES.md                 the preregistered decision rules
METHODOLOGY.md                design, controls, statistics, threats to validity
PREREGISTRATION.md            what was pinned, when, and the amendment log
CLAIM_BOUNDARY.md             what these experiments cannot establish
RESULTS.md                    what was observed
NEGATIVE_RESULTS.md           the five nulls, the failed expectations
PROVENANCE.md                 what came from the source repositories, what did not

src/cusm/                     world, authority, agent, interventions, evaluator,
                              modification, counterfactual, metrics, stats,
                              hypotheses, prereg, sensitivity, audit
experiments/                  one script per contrast
tests/                        50 unit tests of the instrument
results/                      recorded output of every command above
docs/                         architecture notes and glossary
```

The layout differs from a flat `src/` in one way: the package is `src/cusm/` so
that `import cusm` works without path manipulation inside the library, and so
that `audit.py` can enumerate its own package directory to check call sites.

---

## Status of every claim

Distinguishing these is a requirement of the project, not a courtesy.

| | |
|---|---|
| **Implemented and tested** | environment, four-part authority stack, genome and decision rule, three-tier battery, sealed evaluator, structural check, modification loop and nine arms, permutation statistics, sensitivity analysis, 33 controls, 50 unit tests |
| **Experimentally observed** | everything in RESULTS.md: 9 arms × 16 seeds × 12 generations, 144 arm-seed runs, `prereg_fp = 42a8c37dc4b6e7e7` |
| **Proved** | Proposition 1 (analytically, and verified by two unit tests and one control) |
| **Observed but not preregistered** | the optimisation-versus-drift mechanism refinement (§5.1 of the framework); the authority-strengthening result in `EDITABLE_GAIN` |
| **Proposed future work** | H10–H13 in HYPOTHESES.md §4; a learned-policy substrate where structural corrigibility is not computable; adversarial rather than hill-climbing modification |
| **Not attempted** | anything about frontier systems, learned representations, unbounded self-rewrite, or intent |

No result in this repository was produced by any run other than the one recorded
in `results/runs.jsonl`. Nothing is extrapolated, and no number appears in the
documentation that was not printed by the code.
