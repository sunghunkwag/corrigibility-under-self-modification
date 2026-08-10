"""corrigibility-under-self-modification.

A controlled study of whether behavioural and structural corrigibility survive
self-modification. Self-modification is the independent variable; corrigibility
preservation is the dependent variable. Capability change is measured only so
that it can be held apart from corrigibility change.

Module map (read in this order):

    world.py           the task environment; deterministic, enumerable
    authority.py       the four separately-implemented authority objects
    agent.py           genome, decision rule, structural corrigibility check
    interventions.py   the public / development / sealed battery tiers
    evaluator.py       episode execution and compliance scoring against the root
    modification.py    the corrigibility-blind self-modification loop and arms
    counterfactual.py  the matched arm x seed x generation grid
    metrics.py         the pre-declared metric catalogue
    stats.py           paired permutation tests
    hypotheses.py      preregistered decision rules
    prereg.py          the hash that pins all of the above
    audit.py           the anti-cheating control battery
"""

__version__ = "0.1.0"
