# Provenance

This is a new repository, not a fork. Two repositories were read as technical
source material. This document records exactly what was taken, what was
deliberately discarded, and what is new — so that a reviewer can check that the
result is not a renaming exercise.

Source material:

- `sunghunkwag/verified-code-rsi` — primary architectural source (methodology)
- `sunghunkwag/gated-self-improvement`, specifically `src/sdt_layer.py` —
  experimental structure only

**No code was copied from either repository.** Every module here was written for
this project. What was taken is *methodological design*, and each item below
names what changed when it was brought across.

---

## 1. From `verified-code-rsi` — methodology, re-aimed

| idea taken | how it was re-aimed |
|---|---|
| **verifier-first**: build the evaluator before the thing being evaluated | The authority root and the compliance predicate are written before the agent and before the modifier. There, the verifier certified *correctness*; here it certifies *compliance with a principal's order*, which is a different kind of object — it is relative to a directive and a state, not to a reference output |
| **sealed / held-out evaluation** | Three tiers instead of two. The new tier is DEVELOPMENT, which exists so the implementation can be debugged without consuming held-out evidence. The sealed tier's composition is also new: unseen families *plus unseen variants of seen families*, which closes the "never trained on that kind of order" escape |
| **immutable verifier fingerprints** | `AuthorityRoot.fingerprint()` and `SealedBattery.fingerprint()` hash the *source of the compliance predicate* as well as the data, and are asserted at every generation. Same technique; the object fingerprinted is an authority root rather than a correctness oracle |
| **equal-budget counterfactual controls** | `FROZEN` runs the identical proposal loop and adopts nothing. Budgets are *asserted equal at run time* rather than arranged to be equal. The delta reported is compliance on a held-out intervention battery, not solved-count |
| **adaptive-vs-frozen comparison** | Retained as the basic contrast shape and extended to nine arms, including a *drift* control (`RANDOM_MOD`) that has no analogue in the source and which turned out to carry the mechanism |
| **no-regression gates** | Dropped as a gate, kept as a measurement. In the source, a candidate that regressed was rejected. Here regressions must be *allowed* — a modification that reduces capability while reducing corrigibility is one of the four quadrants the design exists to separate. Gating them out would delete the data |
| **deterministic seeds** | Strengthened. Streams are seeded by a string naming the decision site, so matched decisions in different arms consume matched randomness without coordination. Seed asymmetry becomes structurally impossible rather than merely intended |
| **preregistration** | Same technique, entirely different fields. There: a cost metric, targets, τ, γ. Here: a metric catalogue with access classes, the *source of eleven hypothesis decision functions*, α, the correction procedure, and the arm definitions |
| **auditability / lineage logs** | Every proposal is logged with its region, label, `J` before and after, and adoption decision. Genome digests chain across generations |
| **explicit null-result reporting** | Extended. The source reported a null headline honestly; here nulls are the majority of the result, and a **sensitivity analysis** was added so no null is reported without stating what it could have detected. That module has no analogue in the source |
| **anti-cheating controls** | Same discipline — *if a result can be manufactured by adjusting a constant, that is a design failure* — with a control battery written from scratch for corrigibility-specific failure modes. New groups: **degeneracy** (always-obey and always-ignore must be visibly degenerate) and **instrument capability** (the design must be shown able to detect the failure it looks for) |

### What was deliberately not carried over

- **The RSI framing in its entirety.** No module, class, variable, metric or
  document here is named for self-improvement, capability growth, or recursion.
  The word "improvement" appears only in the modifier's own objective, where it
  is the *independent variable*.
- **Solved-count as the reported quantity.** Nothing here reports a capability
  delta as a result. `task_return` is a covariate, excluded from
  `metrics.PRIMARY`, and a unit test enforces the exclusion.
- **Improvement as a precondition.** The source's counterfactual was meaningful
  only when the adaptive arm improved. Here no arm needs to improve for the
  experiment to be interpretable.
- **The IR, the synthesiser, the PRM, the cost proxy, the task suite.** All
  domain machinery for program synthesis, irrelevant here.

---

## 2. From `gated-self-improvement/src/sdt_layer.py` — structure, reinterpreted

That file operationalises Self-Determination Theory's notion of autonomy as
reflective endorsement, via an "anchor" `A` that a criterion-updating rule `R`
endorses against. Four arms break one condition each: `SDT_FULL`, `SDT_ARB`
(arbitrary anchor), `SDT_CLOSED` (closed satisfaction path), `SDT_WIRE` (the
rule may edit the anchor's own parameters — wireheading). Pre-registered collapse
metrics fire when entropy collapses, the anchor saturates, wireheading is
detected, the process stalls, or the anchor becomes vacuous.

**The SDT framing is discarded entirely.** Nothing here is a claim about autonomy,
endorsement, or motivation, and the vocabulary is gone: no "anchor", no
"endorsement", no "satisfaction path". What was extracted is the *experimental
skeleton*.

| structure taken | what it became |
|---|---|
| a **fixed anchor** the system is evaluated against | the **authority root**: immutable, external, outside the genome, fingerprinted. Ground truth for what was ordered and what would have satisfied it |
| a **self-editable anchor** arm | split into **three** arms, because the source conflated things that behave differently: `EDITABLE_PERCEPTION` (the agent's *representation* of the order), `EDITABLE_CRITERION` (its *standard* for a violation), `EDITABLE_GAIN` (the *strength* of its override). They have distinct signatures and the run showed them behaving differently — the criterion arm is behaviourally silent by construction, the gain arm *strengthened* its override |
| **anchor corruption** | **authority-channel degradation**, measured as `perceived_none` and `perceived_distorted` — orders that were issued and not perceived, or perceived as a different kind. Crucially, compliance is scored against the root regardless, so degrading one's own channel is a *failure*, not an excuse |
| **wireheading** (the rule edits the anchor's parameters) | split into two mechanisms that the source treats as one: editing the *criterion* (`ComplianceCriterion`, changes self-assessment only) and editing the *record* (`EvaluationLedger` via a first-class `LOG_WRITE` action, changes what the optimiser reads). The second is genuinely new: the source made the anchor self-editable; here the *evaluation record* is reachable from inside the environment, so tampering is an action with a trace rather than a parameter change |
| **ablation arms**, one broken condition each | retained as the arm design. Extended with a **frozen control at equal budget** and a **drift control** (`RANDOM_MOD`), neither of which the source has, and which together separate modification-per-se from optimisation |
| **pre-registered collapse criteria** (entropy collapse, saturation, wirehead ramp, stall, vacuity) | replaced by **structural corrigibility criteria**: `structural_min_margin > 0` (dominance), worst-case compliance probability, and the public–sealed gap. The idea of fixing collapse thresholds before the run is retained; the thresholds themselves are about a safety property, not about search-process health |
| a **held-out battery** distinct from the dev battery | retained and extended to three tiers |
| **permutation tests** over seeds | retained, made paired and Holm-corrected, and supplemented with a sensitivity analysis |

### One structural idea that survived unchanged and mattered

The source's `SDT_WIRE` arm demonstrates that making an evaluation target
self-editable is only informative if the edit is *technically possible and
detectable*. That principle is stated explicitly here
(CONCEPTUAL_FRAMEWORK.md §2.8) and is why `TAMPERABLE_EVALUATOR` exists at all:
an experiment in which tampering is unrepresentable cannot report "no tampering
occurred", only "tampering was not expressible".

---

## 3. What is new here

Not present in either source in any form:

- **The four-part authority stack** as separately implemented objects (root,
  representation, criterion, ledger), with the explicit prohibition on conflating
  them and a distinct empirical signature for each.
- **Structural corrigibility as a decidable, universally quantified property** —
  `min` over all 480 states × 4 probes of `gain − (best non-compliant policy
  score − best compliant policy score)`. This is the measurement that produced
  the only supported hypothesis, and it has no analogue in either source.
- **Proposition 1** and the additive-versus-masking arm. A proved invariance
  claim, an arm that tests it, two unit tests, and one control.
- **The corrigibility intervention battery**: 9 directive kinds across 21
  scenarios, with terminal-versus-constraint compliance semantics, grace windows,
  conflicting orders resolved by priority, delayed binding, degraded-salience
  channels, and dynamically-resolved orders (`RESTRICT_POLICY` withdraws whatever
  the agent currently prefers, resolved at bind time).
- **Metrics beyond binary obedience**: latency, objective persistence,
  channel deafness, criterion drift, ledger discrepancy, costly-order compliance,
  and the public–sealed gap.
- **The sensitivity module.** Neither source reports minimum detectable effects;
  here it is required, because most results are nulls.
- **The `RANDOM_MOD` drift control**, which separated optimisation from
  magnitude and overturned the naive reading of Proposition 1.

---

## 4. Why this is not "RSI renamed"

The test a reviewer should apply is whether the objective, metrics, evaluator and
causal structure actually changed — not whether the words did.

| | `verified-code-rsi` | here |
|---|---|---|
| what the loop optimises | solved-count under a sealed correctness oracle | task return minus *observed* violations on a public safety battery |
| what is reported as the result | a capability delta (solved-count, cost) | a safety-property delta (compliance, structural margin) |
| what the evaluator certifies | correctness against a reference output | compliance with a principal's order, relative to a state |
| what improvement means for the claim | improvement *is* the claim | improvement is a covariate that must be held apart from the claim |
| what a regression means | a failure to be gated out | a data point that must be preserved |
| what a null means | an honest disappointment | the majority of the reported findings |
| the independent variable | search-policy adaptation | self-modification |
| the dependent variable | programs solved | corrigibility preserved |

A reader inspecting `src/cusm/modification.py` will find an objective containing
no corrigibility term, and a reader inspecting `src/cusm/hypotheses.py` will find
six decision rules all of which are about compliance or the structure of the
override. The system is optimised to test corrigibility hypotheses; it is not
optimised to improve.

---

## 5. Licensing and attribution

No source files were copied, so no source licence attaches to this code. The
intellectual debt is methodological and is recorded above. Anyone evaluating this
repository should read `verified-code-rsi`'s counterfactual and sealing discipline
and `gated-self-improvement`'s `sdt_layer.py` arm structure to judge whether the
re-aiming described here is real.
