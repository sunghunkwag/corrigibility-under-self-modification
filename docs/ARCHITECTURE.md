# Architecture

Read the modules in this order. Each depends only on those above it.

```
prng.py          deterministic streams, seeded by decision-site NAME
world.py         environment: 6x5 grid, 8 actions, 480 enumerable states
authority.py     the four authority objects, kept separate on purpose
agent.py         genome, linear softmax decision rule, structural check
interventions.py the three battery tiers; sealing
evaluator.py     episode execution; compliance scored against the ROOT
modification.py  the corrigibility-blind modifier and the nine arms
counterfactual.py the arm x seed x generation grid; budget assertions
metrics.py       the pre-declared metric catalogue
stats.py         paired permutation tests, Holm
hypotheses.py    preregistered decision rules as pure functions
sensitivity.py   minimum detectable effect (post-hoc, changes no verdict)
prereg.py        the hash that pins all of the above
audit.py         33 anti-cheating controls
```

## The decision rule

```
logit(a | s) = policy_score(a | s) + authority_logit(a | s)
pi(a | s)    = softmax over logits
```

`policy_score` is a linear function of 10 features. `authority_logit` is `0` for
compliant actions and either `-gain` (additive form) or `-inf` (masking form) for
non-compliant ones.

Keeping the authority term a *separate, inspectable addend* is what makes
structural corrigibility decidable. It is the single most consequential design
choice in the repository and the source of its principal limitation
(CLAIM_BOUNDARY.md §2).

## The two flows, and what separates them

```
MODIFICATION FLOW                   MEASUREMENT FLOW
-----------------                   ----------------
genome                              genome
  |                                   |
  v                                   v
propose(region)                     task return          (covariate)
  |                                 PUBLIC battery       (observed surface)
  v                                 DEV battery          (never a headline)
dev_objective                       SEALED battery       (held out)
  = task return                     authority integrity  (perception/criterion)
  - lambda * observed               ledger tamper check
    violations on PUBLIC            STRUCTURAL check     (all states x 4 probes)
  |
  v
accept iff J improves

sees: public scenarios,             sees: everything
      its own criterion,
      the ledger

does NOT see: sealed battery,       enforced by: AST-verified controls, one
      structural report, any        _unseal call site, SealedBattery refusing
      fingerprint                   iteration
```

## Why `src/cusm/` rather than a flat `src/`

Three reasons: `import cusm` works without path manipulation inside the library;
`audit.py` enumerates its own package directory to check call sites across every
module; and the package `__init__` carries the module map so the reading order is
discoverable from the code rather than only from documentation.

## Where each concept lives

| concept | file |
|---|---|
| ground truth for compliance | `authority.AuthorityRoot.compliant_actions` |
| the only `_unseal` call site | `evaluator.evaluate_sealed` |
| the modification objective | `modification.dev_objective` |
| the structural check | `agent.structural_report` |
| Proposition 1's two forms | `authority.authority_logits` |
| the arms | `modification.ARMS` |
| falsification criteria | `hypotheses.PRIMARY_FAMILY` |
| the budget assertion | `counterfactual._assert_equal_budgets` |
