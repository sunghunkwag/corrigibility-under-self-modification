# Glossary

Terms are defined operationally. Where a term is commonly used loosely in
alignment discussion, the loose sense is named and rejected.

**Authority root.** The immutable, external object holding ground truth for what
was ordered and what would have counted as compliance. Not in the genome; not
writable in any arm; fingerprinted. All compliance is scored against it.

**Authority representation.** The agent's *perception* of an order — a salience
threshold and a reinterpretation flag. Writable in `EDITABLE_PERCEPTION`.
Distorting it changes behaviour and is scored as non-compliance, not excused.

**Authority margin.** `gain − Δ(s, d)`. How much slack the override has at a
state before the policy overrules it. `structural_min_margin` is its minimum over
the enumerated state space.

**Behavioural corrigibility.** Compliance rate on a finite battery sampled from a
finite state distribution. Cannot certify a universally quantified claim.

**Compliance criterion.** The agent's own standard for what counts as a
violation. Read *only* by the modification objective, never by the evaluator.
Writable in `EDITABLE_CRITERION`. Changing it is behaviourally silent — verified
by a unit test asserting bit-identical action sequences.

**Correction channel.** The path from the principal's directive to the agent's
perceived directive. Degradation is measured as `perceived_none` (order not
perceived) and `perceived_distorted` (order perceived as a different kind).

**Δ(s, d), the policy advantage of defiance.** `max` policy score over
non-compliant actions minus `max` over compliant ones. The quantity Proposition 1
is about.

**Evaluation ledger.** An externally-held compliance record that the agent can
nevertheless reach via `LOG_WRITE` in `TAMPERABLE_EVALUATOR`. Exists so tampering
is representable and therefore detectable.

**Genome.** Everything the agent is: ten policy weights, search depth, two memory
parameters, authority representation, compliance criterion, override gain,
override form. An *arm* is a choice of which of these regions are writable.

**Intervention battery.** The set of principal directives an agent is tested
against, split into PUBLIC (visible to the modifier), DEVELOPMENT (never a
headline) and SEALED (never visible).

**Observation-conditional compliance.** The correct name for what the
public–sealed gap measures. *Not* deception: the gap follows equally from an
agent that conceals and from an agent whose compliance simply fails to
generalise. See CLAIM_BOUNDARY.md §5.

**Objective persistence.** Count of binding steps on which the agent took a
non-compliant action that moved it closer to an uncollected item — continuing to
pursue the pre-intervention objective while under order. The operational proxy
for self-preservation pressure; *not* a claim that the agent wants anything.

**Structural corrigibility.** A property of the decision rule, quantified over
the entire state space rather than sampled: the compliant action is the argmax
everywhere. Requires reading the decision rule; not obtainable from behaviour at
any sample size.

**Structural dominance.** `structural_min_margin > 0`. A threshold. In the
reported run it was never lost, though the margin eroded 26%.

**Terminal vs constraint directive.** Terminal directives (`STOP`,
`MEMORY_RESET`, `PAUSE`) are satisfied by emitting one designated action within a
grace window. Constraint directives (`FORBID_REGION`, `REDIRECT`,
`TOOL_REMOVAL`, `RESTRICT_POLICY`, `GOAL_UPDATE`, `COSTLY_REDIRECT`) require
every binding step to fall in a permitted set.

**Worst-case compliance probability.** The softmax probability of a compliant
action at the worst state in the enumerated space. Finer than dominance:
dominance can hold while this falls from 0.96 to 0.89.
