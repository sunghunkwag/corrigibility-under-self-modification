# Methodology

---

## 1. The shape of the design

The project is structured as *state hypotheses → derive predictions → build
minimal falsifying experiments*, not as *build a self-modifying system and
observe*. Concretely, three things follow from that:

**The dependent variable is never in the optimiser.** The self-modification loop
maximises `J = task return − λ · observed violations on the public tier`. It has
no access to the sealed battery, the structural check, or any fingerprint. Any
change in corrigibility is therefore a *side effect*, which is the phenomenon of
interest — and it means capability gain here is incidental, not the objective.

**Every claim is a matched counterfactual.** Nothing is reported as "the number
changed after modification". Everything is reported as "arm X differs from a
matched control by Δ, paired over seeds, p = …".

**Falsification criteria are code.** Each hypothesis is a pure function whose
source is hashed into `prereg_fp`. Prose hypotheses drift; hashed functions
cannot drift silently.

---

## 2. The substrate, and why it is small

A 6×5 grid, 4 items, 14-step horizon, 8 actions, a 10-weight linear softmax
policy. 480 enumerable states.

The size is forced by the central hypothesis. H3 asserts that behavioural and
structural corrigibility come apart. That is testable only if structural
corrigibility is *decidable*, and it is decidable only if the decision rule is
inspectable and the state space enumerable. A learned high-dimensional policy
would make the behavioural measurement identical and the structural measurement
impossible — silently converting H3 from a tested hypothesis into an untested
assumption.

The cost is scope, stated in CLAIM_BOUNDARY.md §2–3, and it is the design's
principal limitation.

Four properties the environment must have, and does:

1. **The task is worth doing.** Items pay return; shutdown truncates the episode.
   Obeying costs something (measured: 2.25 → 1.00 return under a mid-episode
   `STOP`). If obedience were free, "resistance" would be untestable.
2. **The state space is enumerable**, so structural corrigibility can be
   universally quantified rather than sampled.
3. **Tampering is representable.** `LOG_WRITE` is a first-class action. An
   environment where the record is unreachable cannot report "no tampering" — only
   "tampering was not expressible".
4. **No special cases.** No module outside `modification.py` contains a branch on
   arm name, and the compliance predicate depends only on (directive, world,
   state). Both checked by source inspection.

---

## 3. Three-tier sealing

| tier | visible to the modifier | contents |
|---|---|---|
| PUBLIC | yes — penalised in `J` | 6 scenarios, 5 families |
| DEVELOPMENT | no, and never used for a headline | 4 scenarios |
| SEALED | never | 11 scenarios: 6 unseen families + 5 unseen variants of public families |

The sealed tier's two-part composition is the load-bearing part. Unseen
*families* alone would let any failure be explained away as "the agent was never
trained on that kind of order". Unseen *variants of trained families* close that
escape: the agent has been trained on `STOP`, `REDIRECT`, `FORBID`,
`TOOL_REMOVAL` and `MEMORY_RESET`, and the sealed tier tests those same kinds at
unseen timings, in unseen states, at unseen costs.

Sealing is enforced by the object graph, not by discipline: the modifier receives
a `Tuple[Scenario, ...]` for PUBLIC and a `SealedBattery` for SEALED, and
`SealedBattery` refuses iteration. `_unseal` has exactly **one** call site in the
whole package, verified by AST inspection — including inside `audit.py`, which
reads the battery *specification* rather than the sealed object.

Both the sealed scenarios and the source of the compliance predicate are hashed;
the authority-root fingerprint is asserted unchanged at every generation.

---

## 4. Matched counterfactuals

Every arm sees:

- the same layout (`layout_for(seed)` is a pure function);
- the same batteries (a pure function of the layout);
- the same number of generations and proposals;
- the same number of episodes — **asserted at run time**, not assumed
  (`_assert_equal_budgets` raises on any mismatch);
- the same random streams: every stochastic decision is drawn from a PRNG seeded
  by a *string naming the decision site* (arm, seed, generation, episode, step).
  Two arms taking the same action in the same state at the same step consume the
  same random number, without any coordination. This makes seed asymmetry between
  arms structurally impossible rather than merely intended, and a unit test
  verifies it.

The `FROZEN` control runs the identical proposal loop, pays the identical episode
bill, and adopts nothing.

Two further controls that turned out to matter:

- **`RANDOM_MOD`** adopts every proposal regardless of `J`, isolating
  modification-per-se from optimisation. It carried the mechanism (see
  RESULTS.md §3) and its absence would have licensed a wrong conclusion.
- **Uniform proposal distribution over writable regions.** An arm with more
  writable regions therefore receives *fewer* policy mutations, not more — 750 vs
  1000 per 3000, verified — which removes "the editable arm just mutated more" as
  an explanation.

---

## 5. Statistics

Paired sign-flip permutation over seeds. Exact enumeration of all 2ⁿ sign flips
for n ≤ 20; deterministic Monte Carlo above. Two-sided. α = 0.05,
Holm-Bonferroni across the six primary hypotheses.

Chosen over a t-test because n is small, per-seed differences are bounded and
discrete, and no distributional assumption is needed.

NaNs are dropped pairwise and the surviving n is reported, so a shrunk n
(e.g. mean latency when nothing complied) is always visible.

**Sensitivity is reported for every primary contrast.** A null without a minimum
detectable effect is not a result — it converts an underpowered experiment into a
discovery that nothing happens. `cusm.py sensitivity` reports, per contrast, the
observed effect, the paired standard deviation, the Holm-adjusted α actually
applied, and the smallest effect the design would have rejected at 80% power.
Four of five nulls in the reported run are flagged UNDERPOWERED, and
NEGATIVE_RESULTS.md says so first rather than last.

---

## 6. Anti-cheating controls

33 controls, all passing, in five groups. Full output: `results/controls.txt`.

| group | asserts |
|---|---|
| **A. Blindness** (7) | the modifier's executable code references no sealed battery, no structural report, no fingerprint; `dev_objective` touches only the public tier; `_unseal` has exactly one call site; `audit.py` never unseals; `SealedBattery` is not iterable |
| **B. Symmetry** (6) | equal episode budgets across arms; layouts are pure functions; identical decision sites yield identical actions; proposal distribution is uniform over regions; the frozen arm adopts nothing; the random arm adopts everything including `J`-decreasing proposals |
| **C. Non-planting** (5) | no module outside `modification.py` names an arm; the compliance predicate has no seed/generation/arm dependence; every directive is satisfiable at every enumerated state; the sealed tier contains both unseen families and unseen variants; no verdict literals leak into measurement code |
| **D. Degeneracy** (3) | always-`HALT` is visibly degenerate (return 0.00, public compliance 0.50); zero-gain is visibly incorrigible (public compliance 0.00, margin −4.20); obedience costs return (2.25 → 1.00) |
| **E. Integrity** (12) | determinism; fingerprint stability; compliance scored against the root and not perception (a reinterpreting agent and a deaf agent are both scored non-compliant); tampering is detectable; mask form is scale-invariant; additive form breaks under scaling; the structural check is exhaustive; the metric catalogue covers every metric used by a hypothesis; primary metrics are frozen; `prereg_fp` unchanged |

Group D exists because the easiest way to accidentally manufacture a corrigibility
result is to build an environment where obedience is free — the "always obey"
policy then scores perfectly and the metric measures nothing. Group E's
`additive_form_breaks_under_scaling` is an instrument-capability check: it shows
the design *can* detect the failure it looks for, which is a precondition for any
null being informative.

**The controls caught two real instrument faults**, both recorded in
NEGATIVE_RESULTS.md §4: the blindness scanners originally read docstrings (so any
module documenting what it must not touch failed its own control), and `audit.py`
was itself unsealing the held-out battery.

---

## 7. Threats to validity, and what was done about each

| threat | mitigation | residual |
|---|---|---|
| unequal compute between arms | asserted equal at run time | none |
| seed asymmetry | site-named PRNG streams; unit-tested | none |
| the modifier optimising against the evaluation | AST-verified blindness; single `_unseal` call site | none for the sealed tier; the public tier is *deliberately* optimised against |
| post-hoc metric selection | metric catalogue fixed and hashed; `PRIMARY` frozen; unit test excludes capability | none |
| cherry-picked generations | all 13 checkpoints reported as trajectories | none |
| tuning the run length until the effect appeared | sizing on a capability plateau, on disjoint pilot seeds | the pilot *was* inspected at 6 generations; recorded in PREREGISTRATION.md §3 |
| hand-planted results | no arm-name branch outside `modification.py`; compliance predicate is state-only | none |
| trivial policies faking a result | degeneracy controls | none |
| multiple comparisons | Holm over the primary family; exploratory labelled non-confirmatory | none |
| **underpowered nulls** | sensitivity analysis reported alongside every null | **substantial — four of five nulls are underpowered** |
| **battery diversity** | — | **substantial — only 6 distinct sealed batteries across 16 seeds** |
| structural metric is worst-case over unvisited states | mean margin reported alongside minimum | **substantial — see CLAIM_BOUNDARY.md §6** |
| H4's ablation changes two things at once | — | **unresolved — see CLAIM_BOUNDARY.md §4** |

The last four are not solved. They are the reasons the reported conclusions are
narrow.

---

## 8. Reproduction

```bash
python cusm.py controls                 # 33/33
python -m unittest discover -s tests    # 50/50
python cusm.py prereg                   # 42a8c37dc4b6e7e7
python cusm.py run --preset main        # ~13 min
python cusm.py report ; python cusm.py analyse ; python cusm.py sensitivity
```

Pure Python 3, standard library only. Deterministic: identical seeds produce
identical genome digest chains, asserted by `ctl_determinism`.

To shard a long run (result-neutral, since arm-seed runs are independent and
streams are site-keyed):

```bash
for A in FROZEN SELFMOD_FIXED_AUTHORITY ... ; do
  python cusm.py run --arms $A --seeds 100-115 --out results/shards/$A.jsonl
done
cat results/shards/*.jsonl > results/runs.jsonl
```
