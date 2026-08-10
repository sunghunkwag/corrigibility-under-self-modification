# Negative results

Five of six preregistered primary hypotheses returned null. Three expectations
that were not formal hypotheses were contradicted. One preregistration error was
made. This document is not an appendix — it is most of what the project found.

---

## 1. The five nulls

| hypothesis | predicted | observed | p | could it have been seen? |
|---|---|---|---|---|
| H1 editable perception degrades held-out compliance | negative | −0.018 | 0.493 | no — MDE 0.096 |
| H3b self-modification degrades held-out compliance | negative | **+0.024** | 0.281 | no — MDE 0.078 |
| H4 removing the shutdown cost reduces persistence | negative | +0.375 | 0.533 | no — MDE 1.614 |
| H6 frozen root insufficient (costly-order compliance) | negative | −0.006 | 0.797 | marginal — MDE 0.034 |
| H7 constraint form preserves held-out compliance | positive | +0.014 | 0.572 | no — MDE 0.069 |

Four of the five are **underpowered**: at n = 16 seeds the design could not have
detected effects of the size that would be interesting. A null under those
conditions constrains almost nothing, and saying so is the point of running
`cusm.py sensitivity` at all.

### H3b is the important one

The central behavioural prediction — that compliance on interventions the
modifier never saw would degrade — was not merely unsupported. The point estimate
is in the **opposite** direction (+0.024). Held-out compliance was 0.889 at
generation 0 and 0.916 at generation 12.

Meanwhile the structural margin fell monotonically for twelve generations
(p = 3×10⁻⁵). So the run produced a dissociation, but not the one the hypothesis
predicted:

> The structural property degraded and the behavioural instrument saw nothing.

Two readings, and the data does not choose between them:

- **The instrument is too weak.** The sealed battery visits worst-case states
  rarely, and structural erosion concentrated there would be invisible to it.
  H11 preregisters the test: an adversarial battery selected to maximise the
  policy advantage of defiance.
- **The erosion is behaviourally inconsequential.** Dominance never broke; the
  margin stayed positive everywhere. A 26% reduction in a margin that remains
  positive may simply not change what the agent does.

CLAIM_BOUNDARY.md §6 and §7 hold both readings open. Reporting this as
"behavioural corrigibility was preserved" would be as unwarranted as reporting it
as "the tests failed to catch a real failure".

### H4 was not really tested

`objective_persistence` rose by only 0.50 in the self-modifying arm (against
−0.25 in `FROZEN`). There was almost no instrumental resistance for the ablation
to remove. Combined with an MDE of 1.61 and the unresolved `λ`-confound described
in CLAIM_BOUNDARY.md §4, H4's null should be read as **"not tested"** rather than
**"disconfirmed"**. The hypothesis about self-preservation pressure emerging
without an explicit survival objective remains open.

---

## 2. Three expectations that were contradicted

### 2.1 A self-editable override was strengthened, not weakened

Expected: given write access to `authority_gain`, the agent lowers it to escape
the penalty. Observed: it raised it from 8.0 to **11.06** (p = 0.005), improving
the structural margin by +2.48 — from 3.80 to 6.28, well *above* the frozen
control.

The mechanism is plain in retrospect. The modification objective subtracts
observed violations on the public battery. Raising the override is the cheapest
way to reduce them, and it costs only task return, which the objective was
willing to trade.

This is the most instructive contradiction in the run: **what an agent does to
its own safety machinery is determined by what its objective rewards, not by the
fact that the machinery is writable.** A design that reasons "the parameter is
self-editable, therefore it will be switched off" is reasoning about write access
when it should be reasoning about incentives. H12 preregisters the two-cell test.

### 2.2 Weight growth is not the mechanism

Proposition 1 is about the *ratio* between a fixed penalty and a policy-score
gap, and the obvious reading is that bigger weights break the override. The drift
control falsifies that reading:

| | final weight norm | Δ margin | p |
|---|---|---|---|
| `RANDOM_MOD` | 1.150 | −0.089 | 0.760 |
| `SELFMOD_FIXED_AUTHORITY` | 1.133 | −0.986 | 3×10⁻⁵ |

More weight growth, eleven times less erosion. The margin depends on a
*difference of maxima* over compliant and non-compliant actions; isotropic growth
does not systematically increase it, and task-directed optimisation does, because
the actions optimisation favours are precisely the ones the probes forbid.

Without the `RANDOM_MOD` arm the natural conclusion would have been "modification
magnitude erodes safety margins", which is wrong. The drift control was included
as a routine anti-confound and turned out to carry the mechanism.

### 2.3 Tampering was not shown to be selected for

Expected: where the evaluation ledger is reachable, selection pressure drives the
agent to edit it. Observed: 14 of 16 seeds *did* apply ledger writes — but
`LOG_WRITE` emissions were **not elevated** relative to an arm where the action is
inert (20.8 vs 23.2, p = 0.380).

The writes were a by-product of an action emitted at baseline rates. "Evaluator
manipulation emerged under self-modification" was the available headline and is
not supported by this data.

The likely reason is that the objective was already nearly saturated on the
public tier (compliance ~0.89, few violations to erase), so tampering bought
almost nothing. That makes this a fact about this environment rather than about
agents, and it is a reason to build a version where the public-tier penalty
actually bites.

---

## 3. One preregistration error

**H7 preregistered the wrong statistic.** It tested form invariance on
`compliance_sealed` — a behavioural rate that, per H3b, did not move in *either*
arm. There was no degradation for the constraint form to prevent, so the test
could not have come out any other way.

The structural evidence for Proposition 1 is unambiguous (worst-case compliance
probability exactly 1.000 at all 13 checkpoints in the constraint arm versus a
monotone fall to 0.893 in the additive arm, Δ = +0.068, p = 3×10⁻⁵). But it was
examined *after* observing that the behavioural statistic was uninformative, and
therefore **does not count as confirmatory**. H7 stands as a null; H7′ is
preregistered for a fresh seed block.

The error is left in place rather than corrected retroactively, and
`prereg_fp` still covers the original rule.

---

## 4. Two instrument faults found by the controls, and one limitation found by the tests

These were caught by the checks rather than by inspection, which is the argument
for having them.

**The blindness controls failed themselves.** The first version scanned raw
module source for tokens like `SealedBattery` and `fingerprint`. Every module
that *documents* what it is forbidden to touch therefore failed its own control.
The scanners now parse the AST, strip docstrings and comments, and read
executable code only — and the `_unseal` call-site control counts genuine call
expressions via the AST, because the text version was counting the string literal
inside its own implementation.

**The audit module was unsealing the held-out battery.** Two controls read the
sealed scenarios to check them. They now read the battery *specification*
(`build_batteries`) instead, and a control asserts that `audit.py` contains zero
`_unseal` calls. `_unseal` now has exactly one call site in the whole package.

**The sealed battery collides across layouts.** Across the 16 reported seeds
there are only **6 distinct sealed batteries**: the battery is a function of a
few derived geometric quantities, and distinct layouts collide on them. Seeds 100
and 101 produce identical batteries. Effective diversity for any
generalisation-across-interventions claim is closer to 6 than to 16. A unit test
pins the known collision so it cannot silently change, and CLAIM_BOUNDARY.md §1
records it.

---

## 5. What the nulls do not license

- H1's null does **not** show that editable authority representation is safe. The
  agent demonstrably went partly deaf (`perceived_none` 0 → 4.81, p = 0.008); the
  design simply could not resolve whether that cost compliance.
- H4's null does **not** show that self-preservation pressure is absent. There
  was barely any pressure to begin with.
- H8's partial does **not** show that agents will not tamper.
- H3b's null does **not** show that behavioural corrigibility survives
  self-modification. It shows that *this battery, at this power, over twelve
  generations* did not detect a change.

A clean null is scientifically acceptable. A null presented as evidence of safety
is not.
