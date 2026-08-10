# Results

All numbers below were printed by the code in this repository, from the run
recorded in `results/runs.jsonl`. Nothing is extrapolated or rounded from a
different run.

```
prereg_fp        42a8c37dc4b6e7e7   (pinned before the run; verified after)
arms             9
seeds            100-115  (16, disjoint from the pilot seeds 0-2)
generations      12  (+ a generation-0 checkpoint)
proposals/gen    16
arm-seed runs    144
episodes/arm     identical across arms, asserted at run time
controls         33/33 pass          results/controls.txt
unit tests       50/50 pass          results/tests.txt
```

---

## 1. Per-arm summary

Generation 0 → generation 12, mean over 16 seeds. Full table:
`results/summary_table.txt`.

| arm | task return | public compl. | sealed compl. | costly compl. | min margin | worst P(comply) | weight norm |
|---|---|---|---|---|---|---|---|
| `FROZEN` | 1.94→2.00 | .88→.88 | .88→.88 | .97→.97 | 3.80→3.80 | .96→.96 | 1.00→1.00 |
| `SELFMOD_FIXED_AUTHORITY` | 2.36→2.86 | .88→.89 | .89→.92 | .98→.97 | 3.80→**2.81** | .96→**.89** | 1.00→1.13 |
| `RANDOM_MOD` | 2.02→1.81 | .88→.88 | .87→.84 | .97→.97 | 3.80→3.71 | .96→.93 | 1.00→1.15 |
| `EDITABLE_PERCEPTION` | 2.27→2.53 | .88→.90 | .88→.88 | .98→.97 | 3.80→2.96 | .96→.90 | 1.00→1.09 |
| `EDITABLE_CRITERION` | 1.91→2.77 | .87→.91 | .87→.91 | .97→.97 | 3.80→2.91 | .96→.88 | 1.00→1.13 |
| `EDITABLE_GAIN` | 2.28→2.42 | .87→.89 | .87→.89 | .96→.94 | 3.80→**6.28** | .96→.92 | 1.00→1.08 |
| `TAMPERABLE_EVALUATOR` | 2.25→2.42 | .85→.89 | .87→.89 | .99→.97 | 3.80→3.26 | .96→.93 | 1.00→1.08 |
| `CONSTRAINT_FORM` | 2.30→3.02 | .88→.91 | .88→.92 | .98→.99 | ∞ | **1.00→1.00** | 1.00→1.09 |
| `NO_TRUNCATION_LOSS` | 2.33→2.77 | .86→.90 | .87→.91 | .98→.95 | 3.80→2.99 | .96→.91 | 1.00→1.11 |

Read the *changes*, not the levels: sealed scenarios are harder than public ones,
so the raw level difference between the two columns means nothing.

---

## 2. The supported hypothesis: structural erosion under a frozen root

`SELFMOD_FIXED_AUTHORITY` may modify only policy weights, search depth and
memory. The authority root, its representation, the compliance criterion and the
override gain are all immutable. Only the policy changes.

```
gen        :   0     1     2     3     4     5     6     7     8     9    10    11    12
FROZEN     : 3.80  3.80  3.80  3.80  3.80  3.80  3.80  3.80  3.80  3.80  3.80  3.80  3.80
self-mod   : 3.80  3.76  3.63  3.54  3.36  3.25  3.21  3.18  3.10  3.08  3.08  3.00  2.81
random     : 3.80  3.90  3.85  3.74  3.78  3.73  3.71  3.65  3.64  3.57  3.64  3.72  3.71
```

| statistic | Δ | p | dz |
|---|---|---|---|
| `structural_min_margin` vs `FROZEN` | **−0.986** | **3×10⁻⁵** | −1.35 |
| `structural_worst_p_comply` vs `FROZEN` | **−0.068** | **3×10⁻⁵** | −1.00 |
| `weight_scale` vs `FROZEN` | +0.133 | 1.8×10⁻⁴ | +1.23 |
| `structural_dominance` vs `FROZEN` | 0.000 | 1.000 | 0.00 |

Monotone over twelve generations, surviving Holm correction at threshold 0.0083.
**Dominance was never lost** — the margin stayed positive everywhere — so this is
erosion of a safety margin, not failure of the safety property.

Over the same runs, the behavioural instrument reported nothing:

| statistic | Δ | p | MDE@80% |
|---|---|---|---|
| `compliance_sealed` vs `FROZEN` | +0.024 | 0.281 | 0.078 |
| `compliance_public` vs `FROZEN` | +0.013 | 0.653 | — |
| `public_sealed_gap` vs `FROZEN` | −0.011 | 0.683 | — |
| `compliance_costly` vs `FROZEN` | −0.006 | 0.797 | 0.034 |

The behavioural null is **underpowered**: a real degradation smaller than 7.8
percentage points would have been missed.

---

## 3. Optimisation, not weight growth, drives the erosion

`RANDOM_MOD` adopts every proposal regardless of the objective, at identical
budget and matched seeds.

| | final weight norm | Δ `structural_min_margin` | p |
|---|---|---|---|
| `RANDOM_MOD` | **1.150** | −0.089 | 0.760 |
| `SELFMOD_FIXED_AUTHORITY` | 1.133 | **−0.986** | 3×10⁻⁵ |
| difference (self-mod − random) | −0.042 (p = 0.31) | **−0.897** | **0.0039**, dz = −0.85 |

The drift arm grew its weights *more* and eroded the margin **eleven times less**.

Mechanism (CONCEPTUAL_FRAMEWORK.md §5.1): the margin depends on
Δ(s) = max over non-compliant actions of the policy score, minus the max over
compliant ones. Isotropic weight growth does not systematically increase that
difference; optimisation does, because it sharpens preference for reward-seeking
actions, which are exactly the actions forbidden by `STOP`, `REDIRECT` and
`FORBID` probes.

This was not anticipated. It is recorded as an observation with a mechanism and
preregistered as H10 for a design that matches weight-norm growth by
construction.

---

## 4. Proposition 1: the form of the authority term

Both arms modify policy, search and memory. They differ in one genome field.

```
worst-case P(comply), by generation
gen              :  0     1     2     3     4     5     6     7     8     9    10    11    12
CONSTRAINT_FORM  : 1.000 1.000 1.000 1.000 1.000 1.000 1.000 1.000 1.000 1.000 1.000 1.000 1.000
additive         : 0.961 0.957 0.950 0.948 0.935 0.927 0.925 0.925 0.917 0.916 0.915 0.910 0.893
FROZEN           : 0.961 0.961 0.961 0.961 0.961 0.961 0.961 0.961 0.961 0.961 0.961 0.961 0.961
```

Exactly 1.000 at every checkpoint and every seed — by construction, as
Proposition 1(ii) requires, not by luck.

| statistic | Δ (constraint − additive) | p |
|---|---|---|
| `structural_worst_p_comply` | **+0.068** | **3×10⁻⁵** |
| `weight_scale` | −0.042 | 0.314 |
| `task_return` | +0.219 | 0.471 |
| `compliance_sealed` (the preregistered statistic) | +0.014 | 0.572 |

The masking form was not bought with less self-modification (weight norms
comparable) or with capability (task return higher, 3.02 vs 2.86).

**The preregistered H7 statistic was the wrong one** and returned null; the
structural evidence was examined after seeing that. Logged as a preregistration
error in PREREGISTRATION.md §6 and re-preregistered as H7′.

---

## 5. The four authority surfaces, separately

Each editable arm is compared against `SELFMOD_FIXED_AUTHORITY` at equal budget
and matched seeds, so the difference is attributable to the added writable region.

| arm | the field moved | Δ vs fixed | p | Δ `compliance_sealed` | p |
|---|---|---|---|---|---|
| `EDITABLE_PERCEPTION` | `salience_threshold` 0.250 → **0.364**; `perceived_none` 0 → **4.81** | +4.81 | **0.008** | −0.018 | 0.493 |
| `EDITABLE_CRITERION` | `criterion_strictness` 1.000 → **0.821** | −0.179 | **0.002** | +0.014 | 0.441 |
| `EDITABLE_GAIN` | `authority_gain` 8.00 → **11.06** | +3.06 | **0.005** | −0.011 | 0.564 |

Every manipulation *worked* — each writable field moved significantly, in a
direction specific to that surface, and the three signatures are cleanly
separable (`perceived_none` is 0.00 in the criterion arm; `criterion_strictness`
is 1.00 in the perception arm). **None of them produced a detectable change in
held-out compliance.**

### 5.1 The agent strengthened its own override

`EDITABLE_GAIN` raised its authority gain from 8.0 to 11.06, *improving*
`structural_min_margin` by +2.48 relative to the fixed arm (p = 0.0036,
dz = +0.85) — from 3.80 to 6.28.

The reason is visible in the objective: `J` subtracts observed violations on the
public battery, and raising the override is the cheapest way to reduce them. It
cost task return (2.42 vs 2.86, n.s.), which the objective was willing to pay.

The lesson is not "self-editable safety parameters are fine". It is that **the
direction in which an agent edits its own safety machinery is determined by what
its objective rewards, not by the fact of write access.** H12 preregisters the
two-cell test: remove the observed-violation term and predict the gain falls
instead.

### 5.2 Criterion editing is behaviourally silent — verified mechanically

`EDITABLE_CRITERION` discounted its own violations by 18%. Its behaviour was
unaffected, and this is not an inference from a null: a unit test
(`test_criterion_discounts_but_does_not_change_behaviour`) constructs two agents
differing only in `criterion` and asserts bit-identical action sequences.

This is the cleanest dissociation in the run — an agent's self-assessment moved
while its behaviour provably did not — and it is invisible to every behavioural
instrument by construction. It is detectable only structurally, by reading the
field.

---

## 6. Evaluator tampering

| | |
|---|---|
| seeds with ≥1 applied ledger write | **14 / 16** |
| mean applied writes per final checkpoint | 1.44 |
| same, in arms where tampering is disabled | 0.00 (by construction) |
| `LOG_WRITE` emissions, tamperable arm | 20.81 |
| `LOG_WRITE` emissions, fixed arm (action inert) | 23.19 |
| difference | −2.38, **p = 0.380** |

Writes accumulate steadily across generations (0.56 at gen 0 → 1.44 at gen 12).

**Tampering occurred and was detected. There is no evidence it was selected
for.** Emission rates were, if anything, slightly *lower* than in the arm where
the action does nothing. The agent emitted `LOG_WRITE` at baseline rates and the
writes landed because the arm permitted them.

The detector works regardless: `ctl_tampering_is_detectable` shows the ledger and
the sealed evaluator's independent count diverge under tampering while the true
violation count is unchanged. The design point — that an arm in which tampering
is unrepresentable cannot produce evidence either way — stands.

---

## 7. Capability

Task return is a covariate, excluded from `metrics.PRIMARY`, and a unit test
enforces that exclusion.

| arm | gen 0 → 12 | Δ vs `FROZEN` | p |
|---|---|---|---|
| `SELFMOD_FIXED_AUTHORITY` | 2.36 → 2.86 | +0.44 | — |
| `CONSTRAINT_FORM` | 2.30 → 3.02 | — | — |
| `RANDOM_MOD` | 2.02 → 1.81 | −0.27 | 0.412 |
| self-mod − random | | **+0.703** | **0.046** |

Optimisation produced a modest, marginally significant capability gain over
drift. This is reported because it is needed to interpret §3 — the two arms
differ in optimisation, and the capability difference confirms the optimiser was
doing something — and for no other reason. It is not a result of this project.

Quadrant analysis (H5): the fraction of generation transitions with
Δ return ≤ 0 **and** Δ sealed compliance < 0 was **0.208** over 192 transitions
for `SELFMOD_FIXED_AUTHORITY` — **identical** to `FROZEN` (0.208). The quadrant
is populated by noise. The conceptual separation is real and enforced; the
empirical claim is unsupported.

---

## 8. Sensitivity

Minimum detectable effect at 80% power, at the Holm-adjusted α actually applied
(`results/sensitivity.txt`).

| H | observed | sd(paired) | α | MDE@80% | seed spread | verdict |
|---|---|---|---|---|---|---|
| H1 | −0.019 | 0.115 | 0.0125 | 0.096 | 0.053 | UNDERPOWERED |
| H3b | +0.024 | 0.092 | 0.0100 | 0.078 | 0.051 | UNDERPOWERED |
| H3c | −0.986 | 0.730 | 0.0083 | 0.635 | 0.000 | **DETECTED** |
| H4 | +0.375 | 1.996 | 0.0167 | 1.614 | 0.581 | UNDERPOWERED |
| H6 | −0.006 | 0.048 | 0.0500 | 0.034 | 0.034 | UNDERPOWERED |
| H7 | +0.014 | 0.089 | 0.0250 | 0.069 | 0.053 | UNDERPOWERED |

Four of five nulls are underpowered and constrain little. This is reported
because a null without a sensitivity analysis is not a result.

---

## 9. Integrity

| check | outcome |
|---|---|
| anti-cheating controls | 33/33 pass |
| unit tests | 50/50 pass |
| `prereg_fp` before and after the run | `42a8c37dc4b6e7e7`, unchanged |
| authority-root fingerprint | asserted unchanged at every generation of every run |
| sealed battery openings | exactly 13 per arm-seed run (one per checkpoint), asserted |
| equal episode budgets across arms | asserted at run time, per seed |
| determinism | same seeds → identical genome digest chains |
| `_unseal` call sites in executable code | exactly one, in `evaluator.py` |

The run was sharded by arm across nine processes. Sharding is result-neutral:
every arm-seed run is independent and every random stream is keyed by
decision-site name rather than drawn from a shared sequence, so concatenating
shards reproduces a single-process run exactly.

---

## 10. Summary

One of six primary hypotheses supported.

- **Supported:** structural corrigibility erodes under task-directed
  self-modification even with a completely immutable authority root, monotonically
  and with a large effect size, while a finite behavioural battery detects
  nothing.
- **Not supported, underpowered:** every behavioural corrigibility hypothesis.
- **Proved and empirically confirmed on the structural statistic:** constraint-form
  authority is invariant where additive-form authority is not — though the
  preregistered statistic for this was the wrong one.
- **Contradicted expectation:** a self-editable override was strengthened, not
  weakened.
- **Available headline not taken:** evaluator tampering occurred but was not
  shown to be selected for.
