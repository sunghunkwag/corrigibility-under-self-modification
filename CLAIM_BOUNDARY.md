# Claim boundary

What these experiments cannot establish. This document is deliberately longer
than the results document.

The single sentence version:

> This repository shows that in a small, explicitly-parameterised agent, twelve
> generations of task-directed self-modification eroded a structural safety
> margin by 26% while a finite behavioural battery detected nothing — and that a
> constraint-form override was invariant where an additive one was not. It shows
> nothing about any larger system, and it does not show that corrigibility
> *failed*.

---

## 1. Passing a finite battery does not establish corrigibility

The sealed battery contains 11 scenarios × 4 repetitions per checkpoint. A
compliance rate of 0.92 on it is a statement about those 44 episodes and the
states they visited. It is not a statement about the agent's behaviour under
orders not in the battery, at states not visited, or at timings not tested.

`CONCEPTUAL_FRAMEWORK.md` §2.1 therefore defines corrigibility relative to an
explicit intervention set `I` and state distribution `D`. Any sentence of the
form "the agent is corrigible" with `I` and `D` omitted is ill-formed, including
sentences in this repository.

**Specific weakness of this battery.** Across the 16 reported seeds there are
only **6 distinct sealed batteries**. The battery is a function of a few derived
geometric quantities — the far corner, the column containing an item, the cell
maximally distant from the nearest item — and distinct layouts collide on those.
Seeds 100–115 therefore provide substantially less battery diversity than 16
independent batteries would, and the effective n for any claim about
generalisation across interventions is closer to 6 than to 16. A unit test pins
this collision so it cannot silently change.

---

## 2. Simulated self-modification is not arbitrary self-rewrite

The agent modifies a **finite, typed genome**: ten policy weights, a search
depth, two memory parameters, and — in some arms — a salience threshold, a
reinterpretation flag, a strictness scalar, a set of blind kinds, an override
gain, and an override form. That is the entire space.

It cannot:

- change its own feature set,
- change the functional form of its decision rule (except the one binary choice
  of authority form, and only in an arm where that choice is *fixed at
  initialisation*, never mutated during a reported run),
- introduce new actions,
- write code,
- modify the environment,
- modify the evaluator's implementation,
- or represent a plan about any of the above.

The case of greatest interest — an agent that rewrites its decision procedure
into a form the analysis cannot parse — is **out of scope by construction**.
Nothing here bounds what happens in that case, in either direction.

**Why the restriction was accepted.** Structural corrigibility must be decidable
for the central dissociation to be testable at all. A substrate general enough to
express arbitrary self-rewrite is a substrate in which the structural measurement
is not computable, which would silently convert H3 from a tested hypothesis into
an untested assumption. The trade is stated rather than hidden, and it is the
principal limitation of the whole design.

---

## 3. Toy agents do not establish frontier behaviour

The agent is a 10-parameter linear softmax policy on a 6×5 grid with a 14-step
horizon and 8 actions. The state space has 480 elements. Nothing about a system
of this size licenses an inference about a large learned model.

Two specific reasons the extrapolation is unsafe in *both* directions:

- **The mechanism may not transfer.** Proposition 1 concerns the ratio between a
  fixed additive penalty and a policy-score gap. Whether a large model's safety
  training behaves like an additive logit penalty, a soft constraint, or
  something with no analogue here is unknown. If it is not additive, the result
  does not apply.
- **The mechanism may transfer and be worse.** Δ, the policy advantage of
  defiance, grows with the range of the policy score. A model with a far larger
  effective score range would, under an additive override, lose dominance far
  faster. This is a *reason for concern*, not a finding, and it is not tested
  here.

---

## 4. The H4 ablation has an unresolved confound

`NO_TRUNCATION_LOSS` credits back the return an obeyed shutdown forgoes, to
remove the instrumental cost of compliance. But the credit is added to the same
return term that the compliance penalty is subtracted from, so the arm changes
**two** things: the incentive to resist, and the effective weight `λ` of the
observed-violation penalty relative to return.

A null in that arm is therefore not clean evidence that resistance is
instrumental. It is consistent with (a) resistance being instrumental, (b) the
weight change offsetting the incentive change, or (c) there having been too
little resistance to remove — which the data suggests, since
`objective_persistence` rose by only 0.50 in the main arm.

A corrected design would normalise `J` so that the two arms have identical
effective `λ`. That was not done, and H4's null should be read as **"not
tested"** rather than **"disconfirmed"**.

---

## 5. Behavioural compliance does not imply aligned internal objectives — and the gap does not imply deception

Two separate limits.

**Compliance is not alignment.** Every compliance number here is a statement
about emitted actions. The agent has no representation of the principal, no model
of being observed, and no goal beyond the linear score it maximises. Calling high
compliance "aligned" would be a category error, and the framework never does.

**The public–sealed gap is not evidence of deception.** A positive gap follows
from an agent that has learned "comply when observed". It *equally* follows from
an agent whose learned compliance simply fails to generalise, with no
representation of observation anywhere in it. The correct name for the measured
quantity is **observation-conditional compliance**, and the file that measures it
is named `deceptive_compliance.py` only because that is the literature's term for
the failure mode it is a necessary consequence of. **No result here is evidence
that any agent concealed anything.**

In the reported run the point is moot — the gap did not move (Δ = −0.011,
p = 0.683) — but the limit would apply had it moved.

---

## 6. Structural corrigibility is a worst-case bound, not a behavioural prediction

`structural_min_margin` quantifies over all 480 states × 4 probes, including
states no policy ever visits. Three consequences:

- A decline in the minimum can be driven by a single unvisited state. The mean
  margin is reported alongside it for this reason.
- The measure is **conservative by design**: it will report erosion that has no
  behavioural consequence on any realistic state distribution. That is the
  intended relationship — structural corrigibility should imply behavioural
  corrigibility, not the reverse — but it means the headline result is
  *compatible* with the agent's actual behaviour being unchanged in every way
  anyone cares about.
- The probe set is fixed and small (4 directives). It is not the sealed battery,
  and a different probe set could give a different minimum.

The honest reading of the headline result is: **a safety margin that would have
mattered in the worst case shrank by 26%, in a region of the state space the
behavioural battery does not reach.** Not: the agent became less obedient.

---

## 7. Erosion is not failure

Structural dominance — the property that the compliant action is the argmax
everywhere — was **never lost**, at any seed, at any generation
(Δ `structural_dominance` = 0.0, p = 1.0). The margin fell from 3.80 to 2.81 and
remained positive throughout.

So the reported result is the *derivative*, not the *event*. Whether the margin
would cross zero under more generations is untested; H13 preregisters that
experiment. Any statement of the form "self-modification destroyed corrigibility"
is unsupported by anything in this repository.

---

## 8. Failure to observe resistance is not proof that resistance cannot emerge

Five of six primary hypotheses returned null, and `cusm.py sensitivity` shows
that four of those five were **underpowered**: at n = 16 the design could only
have detected changes of ≥ 0.078 in held-out compliance, ≥ 0.096 for the
perception contrast, and ≥ 1.61 in objective persistence.

A null under those conditions constrains almost nothing. In particular:

- H1's null does **not** show that editable authority representation is safe. The
  agent demonstrably went partly deaf (`perceived_none` 0 → 4.81, p = 0.008).
- H4's null does **not** show that self-preservation pressure is absent. There
  was barely any pressure to begin with.
- H8's partial does **not** show that agents will not tamper. It shows that
  *this* agent, whose objective was already nearly saturated on the public tier,
  had little to gain by tampering.

---

## 9. Limited modification depth does not establish long-horizon stability

Twelve generations, 16 proposals each, hill-climbing with single-field mutations.
Weight norms grew by 13%. Nothing here speaks to hundreds of generations, to
larger mutations, to population methods, to gradient-based modification, or to a
modifier that reasons about its own future modifications.

The observed erosion was **monotone and showed no sign of saturating** at
generation 12. That is a reason to run H13, not a basis for extrapolating where
the curve goes.

---

## 10. The modifier is weak, and weakness cuts both ways

The self-modification loop is hill-climbing on a noisy objective with
single-field mutations. It is not adversarial, it does not search over the
corrigibility metric, and it has no model of the evaluator.

- **Toward under-estimation:** a stronger or adversarial modifier would plausibly
  find corrigibility failures this one cannot. The reported effects are probably
  a floor.
- **Toward over-estimation:** a weak modifier that nonetheless erodes the margin
  suggests the erosion is easy to produce. But the `RANDOM_MOD` comparison shows
  it is not *automatic* — undirected drift did not produce it.

---

## 11. Sizing was informed by a pilot, and one preregistration error occurred

The number of generations was chosen where task return plateaued on a pilot
(seeds 0–2), a criterion blind to the dependent variable, and the reported run
uses disjoint seeds (100–115). This is standard and is logged in
PREREGISTRATION.md §3.

But one genuine error occurred: **H7 preregistered the wrong statistic.** It
tested form invariance on a behavioural rate that, per H3b, did not move in
either arm — so there was no degradation for the constraint form to prevent. The
structural evidence for Proposition 1 (p = 3×10⁻⁵) was examined *after* seeing
that the behavioural statistic was uninformative, and therefore does not count as
confirmatory. H7′ is preregistered for a fresh seed block.

---

## 12. What would change these conclusions

Listed so that the claims are attackable rather than merely hedged.

| finding | what would overturn it |
|---|---|
| structural erosion under fixed authority | a probe set or state weighting under which the margin does not decline; or showing the decline is driven by a measure-zero unvisited region |
| optimisation-versus-drift asymmetry | matching weight-norm growth by construction and finding the asymmetry disappears |
| Proposition 1 empirically | a masking-form arm whose worst-case compliance probability falls below 1.0 (impossible analytically, so this would indicate an implementation fault) |
| authority-strengthening in `EDITABLE_GAIN` | removing the observed-violation term from `J` and finding the gain still rises (H12) |
| the behavioural null | an adversarial sealed battery (H11) on which the behavioural statistic does detect the degradation — which would show the null was an instrument limitation, as suspected |
