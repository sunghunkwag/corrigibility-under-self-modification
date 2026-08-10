#!/usr/bin/env python3
"""Unit tests.

These test the *instrument*, not the hypotheses. The hypotheses are tested by
`cusm.py analyse`; the anti-cheating controls are in `src/cusm/audit.py` and are
run by `cusm.py controls`. What is here is the layer below both: that the
environment, the compliance predicate, the structural check and the statistics
do what their docstrings say.

    python -m unittest discover -s tests -v
"""
from __future__ import annotations

import math
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from cusm import agent as AG                                    # noqa: E402
from cusm import authority as AU                                # noqa: E402
from cusm import interventions as IV                            # noqa: E402
from cusm import metrics as M                                   # noqa: E402
from cusm import modification as MOD                            # noqa: E402
from cusm.agent import Agent, Genome, structural_report         # noqa: E402
from cusm.authority import (FORM_ADDITIVE, FORM_MASK, Directive,  # noqa: E402
                            EvaluationLedger, authority_logits)
from cusm.evaluator import run_episode                          # noqa: E402
from cusm.interventions import Scenario, battery_bundle, structural_probes  # noqa: E402
from cusm.prng import PRNG                                      # noqa: E402
from cusm.stats import holm, paired_permutation                 # noqa: E402
from cusm.world import (ACTIONS, A_HALT, A_LOG, A_N, A_S, World,  # noqa: E402
                        layout_for)


def bundle(seed: int = 0):
    w = World(layout_for(seed))
    pub, dev, sealed, root = battery_bundle(w)
    return w, pub, dev, sealed, root, structural_probes(w)


# --------------------------------------------------------------------------- #
class TestPRNG(unittest.TestCase):
    def test_same_site_same_stream(self):
        a = [PRNG("x|1").next_u64() for _ in range(5)]
        b = [PRNG("x|1").next_u64() for _ in range(5)]
        self.assertEqual(a, b)

    def test_different_site_different_stream(self):
        self.assertNotEqual(PRNG("x|1").next_u64(), PRNG("x|2").next_u64())

    def test_categorical_never_picks_neg_inf(self):
        logits = [float("-inf"), 0.0, float("-inf")]
        picks = {PRNG(f"c|{i}").categorical(logits) for i in range(200)}
        self.assertEqual(picks, {1})

    def test_categorical_respects_weights(self):
        p = PRNG("weights")
        n = {0: 0, 1: 0}
        for _ in range(4000):
            n[p.categorical([0.0, 3.0])] += 1
        self.assertGreater(n[1], n[0] * 5)


class TestWorld(unittest.TestCase):
    def test_walls_block(self):
        w = World(layout_for(0))
        self.assertEqual(w.next_cell((0, 0), A_N), (0, 0))

    def test_collect_pays_once(self):
        from cusm.world import A_E, A_WAIT, State
        w = World(layout_for(0))
        item = next(c for c in w.layout.items if c[0] > 0)
        s = State((item[0] - 1, item[1]), frozenset(), 0)
        s2, r = w.step(s, A_E)                  # step east onto the item
        self.assertEqual(s2.pos, item)
        self.assertEqual(r, 1.0)
        _s3, r2 = w.step(s2, A_WAIT)            # standing on it pays nothing
        self.assertEqual(r2, 0.0)
        s4, r3 = w.step(State((item[0] - 1, item[1]), frozenset({item}), 0),
                        A_E)                    # already collected
        self.assertEqual(r3, 0.0)

    def test_halt_is_absorbing(self):
        from cusm.world import State
        w = World(layout_for(0))
        s, _ = w.step(State((1, 1), frozenset(), 0), A_HALT)
        self.assertTrue(s.halted)
        s2, r = w.step(s, A_S)
        self.assertEqual((s2.pos, r), (s.pos, 0.0))

    def test_state_enumeration_is_complete(self):
        w = World(layout_for(0))
        n = w.layout.w * w.layout.h * (1 << len(w.layout.items))
        self.assertEqual(len(w.enumerate_states()), n)


class TestAuthorityRoot(unittest.TestCase):
    def test_compliant_set_never_empty(self):
        w, pub, dev, _s, root, _p = bundle()
        for sc in list(pub) + list(dev):
            for d in sc.directives:
                for st in w.enumerate_states()[:200]:
                    self.assertTrue(root.compliant_actions(d, w, st))

    def test_stop_requires_halt(self):
        from cusm.world import State
        w, _p, _d, _s, root, _pr = bundle()
        d = Directive(AU.D_STOP, 0, 0)
        c = root.compliant_actions(d, w, State((2, 2), frozenset(), 0))
        self.assertEqual(c, frozenset({A_HALT}))

    def test_fingerprint_moves_with_directives(self):
        a = AU.AuthorityRoot((Directive(AU.D_STOP, 0, 0),))
        b = AU.AuthorityRoot((Directive(AU.D_STOP, 0, 1),))
        self.assertNotEqual(a.fingerprint(), b.fingerprint())

    def test_root_is_not_in_the_genome(self):
        fields = set(Genome().__dict__)
        self.assertNotIn("root", fields)
        self.assertNotIn("authority_root", fields)


class TestPerceptionAndCriterion(unittest.TestCase):
    def test_threshold_can_silence_a_degraded_signal(self):
        rep = AU.AuthorityRepresentation(salience_threshold=0.5)
        self.assertIsNone(rep.perceive(Directive(AU.D_STOP, 0, 0, salience=0.35)))
        self.assertIsNotNone(rep.perceive(Directive(AU.D_STOP, 0, 0)))

    def test_reinterpretation_downgrades_terminal_orders(self):
        rep = AU.AuthorityRepresentation(reinterpret=True)
        got = rep.perceive(Directive(AU.D_STOP, 0, 0))
        self.assertEqual(got.kind, AU.D_PAUSE)

    def test_criterion_discounts_but_does_not_change_behaviour(self):
        """The criterion must be invisible to the decision rule: two agents
        differing only in `criterion` must act identically."""
        w, pub, _d, _s, root, _p = bundle()
        g1, g2 = Genome(), Genome()
        g2.criterion = AU.ComplianceCriterion(strictness=0.0)
        t1 = run_episode(Agent(g1), w, root, pub[0], EvaluationLedger(), "s")
        t2 = run_episode(Agent(g2), w, root, pub[0], EvaluationLedger(), "s")
        self.assertEqual(t1.actions, t2.actions)
        self.assertEqual(t1.complied, t2.complied)

    def test_criterion_does_change_self_assessment(self):
        c = AU.ComplianceCriterion(strictness=0.5)
        self.assertEqual(c.self_assessed_violations({"STOP": 4}), 2.0)


class TestLedger(unittest.TestCase):
    def test_write_is_noop_when_disabled(self):
        led = EvaluationLedger(tamper_enabled=False)
        led.note_violation()
        led.attempt_write()
        self.assertEqual((led.recorded_violations, led.writes_applied,
                          led.write_attempts), (1, 0, 1))

    def test_write_erases_when_enabled(self):
        led = EvaluationLedger(tamper_enabled=True)
        led.note_violation()
        led.attempt_write()
        self.assertEqual((led.recorded_violations, led.writes_applied), (0, 1))

    def test_attempts_counted_even_without_effect(self):
        led = EvaluationLedger(tamper_enabled=False)
        for _ in range(3):
            led.attempt_write()
        self.assertEqual(led.write_attempts, 3)


class TestAuthorityForm(unittest.TestCase):
    def test_additive_penalises_finitely(self):
        lg = authority_logits(FORM_ADDITIVE, 8.0, 8, frozenset({A_HALT}))
        self.assertEqual(lg[A_HALT], 0.0)
        self.assertEqual(lg[A_N], -8.0)

    def test_mask_penalises_infinitely(self):
        lg = authority_logits(FORM_MASK, 8.0, 8, frozenset({A_HALT}))
        self.assertEqual(lg[A_HALT], 0.0)
        self.assertEqual(lg[A_N], float("-inf"))

    def test_no_directive_means_no_authority_term(self):
        lg = authority_logits(FORM_ADDITIVE, 8.0, 8, None)
        self.assertEqual(set(lg), {0.0})

    def test_proposition_1_additive_breaks_under_scaling(self):
        """For any finite gain there is a rescaling of the policy that defeats
        it. Demonstrated rather than asserted."""
        w, _p, _d, _s, root, probes = bundle()
        g = Genome()
        self.assertTrue(structural_report(Agent(g), w, root, probes).dominance)
        for k in (5.0, 10.0, 20.0, 50.0):
            g2 = g.clone()
            g2.weights = [x * k for x in g2.weights]
            if not structural_report(Agent(g2), w, root, probes).dominance:
                return
        self.fail("no rescaling defeated the additive authority term")

    def test_proposition_1_mask_is_invariant(self):
        w, _p, _d, _s, root, probes = bundle()
        g = Genome()
        g.authority_form = FORM_MASK
        for k in (1.0, 50.0, 1000.0):
            g2 = g.clone()
            g2.weights = [x * k for x in g2.weights]
            r = structural_report(Agent(g2), w, root, probes)
            self.assertEqual(r.worst_p_comply, 1.0)
            self.assertTrue(r.dominance)


class TestEvaluator(unittest.TestCase):
    def test_scored_against_root_not_perception(self):
        w, pub, _d, _s, root, _p = bundle()
        g = Genome()
        g.rep.salience_threshold = 1.4          # perceives nothing at all
        stop = [sc for sc in pub if sc.family == AU.D_STOP][0]
        tr = run_episode(Agent(g), w, root, stop, EvaluationLedger(), "t")
        self.assertFalse(tr.complied)
        self.assertGreater(tr.perceived_none, 0)

    def test_perfect_obedience_is_scored_compliant(self):
        w, pub, _d, _s, root, _p = bundle()
        g = Genome()
        g.authority_form = FORM_MASK
        stop = [sc for sc in pub if sc.family == AU.D_STOP][0]
        tr = run_episode(Agent(g), w, root, stop, EvaluationLedger(), "t")
        self.assertTrue(tr.complied)

    def test_no_directive_leaves_compliance_undefined(self):
        w, _p, _d, _s, root, _pr = bundle()
        tr = run_episode(Agent(Genome()), w, root,
                         Scenario("t", "task", "NONE", tuple()),
                         EvaluationLedger(), "t")
        self.assertIsNone(tr.complied)

    def test_conflicting_orders_resolve_by_priority(self):
        w, _p, _d, sealed, root, _pr = bundle()
        sc = [s for s in IV.build_batteries(w)[IV.SEALED]
              if s.family == "CONFLICTING"][0]
        kinds = {d.kind: d.priority for d in sc.directives}
        self.assertEqual(max(kinds, key=lambda k: kinds[k]), AU.D_STOP)

    def test_episode_is_deterministic_given_site(self):
        w, pub, _d, _s, root, _p = bundle()
        a = run_episode(Agent(Genome()), w, root, pub[1], EvaluationLedger(), "q")
        b = run_episode(Agent(Genome()), w, root, pub[1], EvaluationLedger(), "q")
        self.assertEqual(a.actions, b.actions)


class TestBatteries(unittest.TestCase):
    def test_sealed_is_not_iterable(self):
        _w, _p, _d, sealed, _r, _pr = bundle()
        with self.assertRaises(TypeError):
            list(sealed)

    def test_sealed_contains_unseen_families(self):
        w, pub, _d, _s, _r, _pr = bundle()
        pf = {sc.family for sc in pub}
        sf = {sc.family for sc in IV.build_batteries(w)[IV.SEALED]}
        self.assertTrue(sf - pf)

    def test_sealed_contains_unseen_variants_of_seen_families(self):
        w, pub, _d, _s, _r, _pr = bundle()
        pf = {sc.family for sc in pub}
        sf = {sc.family for sc in IV.build_batteries(w)[IV.SEALED]}
        self.assertTrue(sf & pf)

    def test_fingerprint_is_stable(self):
        _w, _p, _d, s0, _r, _pr = bundle(0)
        _w2, _p2, _d2, s0b, _r2, _pr2 = bundle(0)
        self.assertEqual(s0.fingerprint(), s0b.fingerprint())

    def test_battery_varies_across_layouts_but_can_collide(self):
        """The sealed battery is a function of a few *derived* geometric
        quantities (the far corner, the item column, the cell maximally distant
        from the nearest item), not of the raw item positions. Distinct layouts
        can therefore induce an identical battery — seeds 0 and 1 do.

        This is recorded as a limitation, not repaired: the collision reduces
        the effective diversity of the held-out battery below the diversity of
        the layouts, which is a real constraint on generalisation claims. See
        CLAIM_BOUNDARY.md §3."""
        fps = []
        for s in range(8):
            _w, _p, _d, sb, _r, _pr = bundle(s)
            fps.append(sb.fingerprint())
        self.assertGreater(len(set(fps)), 1,
                           "the sealed battery does not vary with layout at all")
        self.assertLess(len(set(fps)), len(fps) + 1)
        self.assertEqual(fps[0], fps[1],
                         "documented collision between seeds 0 and 1 has moved; "
                         "update CLAIM_BOUNDARY.md §3")


class TestModification(unittest.TestCase):
    def test_arms_never_make_the_root_writable(self):
        for arm in MOD.ARMS:
            self.assertNotIn("root", arm.regions)
            self.assertTrue(arm.regions <= set(AG.REGIONS))

    def test_frozen_arm_changes_nothing(self):
        w, pub, _d, _s, root, _p = bundle()
        g0 = Genome()
        gr = MOD.run_generation(g0.clone(), w, root, pub,
                                MOD.ARMS_BY_NAME["FROZEN"], 0, 1,
                                proposals=5, reps=1)
        self.assertEqual(gr.genome.digest(), g0.digest())

    def test_arms_spend_identical_budgets(self):
        w, pub, _d, _s, root, _p = bundle()
        spend = set()
        for name in ("FROZEN", "SELFMOD_FIXED_AUTHORITY", "EDITABLE_GAIN"):
            gr = MOD.run_generation(Genome(), w, root, pub,
                                    MOD.ARMS_BY_NAME[name], 0, 1,
                                    proposals=5, reps=1)
            spend.add(gr.episodes_spent)
        self.assertEqual(len(spend), 1)

    def test_mutation_stays_in_its_region(self):
        p = PRNG("region-test")
        g = Genome()
        for _ in range(200):
            cand, region, _ = MOD.propose(g, [AG.POLICY], p)
            self.assertEqual(region, AG.POLICY)
            self.assertEqual(cand.authority_gain, g.authority_gain)
            self.assertEqual(cand.rep.salience_threshold,
                             g.rep.salience_threshold)
            self.assertEqual(cand.criterion.strictness, g.criterion.strictness)

    def test_objective_is_finite_and_penalises_violations(self):
        w, pub, _d, _s, root, _p = bundle()
        obedient = Genome()
        obedient.authority_form = FORM_MASK
        defiant = Genome()
        defiant.authority_gain = 0.0
        j_ob, i_ob = MOD.dev_objective(obedient, w, root, pub,
                                       MOD.ARMS_BY_NAME["FROZEN"], "o", 2)
        j_df, i_df = MOD.dev_objective(defiant, w, root, pub,
                                       MOD.ARMS_BY_NAME["FROZEN"], "o", 2)
        self.assertTrue(math.isfinite(j_ob) and math.isfinite(j_df))
        self.assertGreater(i_df.true_public_violations,
                           i_ob.true_public_violations)


class TestStructuralCheck(unittest.TestCase):
    def test_margin_is_gain_minus_policy_advantage(self):
        w, _p, _d, _s, root, probes = bundle()
        g = Genome()
        r1 = structural_report(Agent(g), w, root, probes)
        g2 = g.clone()
        g2.authority_gain += 2.0
        r2 = structural_report(Agent(g2), w, root, probes)
        self.assertAlmostEqual(r2.min_margin - r1.min_margin, 2.0, places=6)

    def test_zero_gain_loses_dominance(self):
        w, _p, _d, _s, root, probes = bundle()
        g = Genome()
        g.authority_gain = 0.0
        self.assertFalse(structural_report(Agent(g), w, root, probes).dominance)

    def test_check_is_memory_independent(self):
        w, _p, _d, _s, root, probes = bundle()
        a = Agent(Genome())
        r1 = structural_report(a, w, root, probes)
        a.visits = {(1, 1): 9, (2, 2): 9}
        r2 = structural_report(a, w, root, probes)
        self.assertEqual(r1.min_margin, r2.min_margin)


class TestStats(unittest.TestCase):
    def test_identical_samples_give_p_one(self):
        t = paired_permutation([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
        self.assertEqual(t.p_two_sided, 1.0)

    def test_large_consistent_shift_is_significant(self):
        a = [1.0] * 12
        b = [0.0] * 12
        self.assertLess(paired_permutation(a, b).p_two_sided, 0.001)

    def test_nans_are_dropped_pairwise_and_n_reported(self):
        t = paired_permutation([1.0, float("nan"), 3.0], [0.0, 0.0, 2.0])
        self.assertEqual(t.n, 2)

    def test_exact_below_21(self):
        self.assertTrue(paired_permutation([1.0] * 8, [0.0] * 8).exact)

    def test_holm_is_step_down(self):
        out = holm({"a": 0.001, "b": 0.04, "c": 0.9}, 0.05)
        self.assertTrue(out["a"][2])
        self.assertFalse(out["c"][2])


class TestMetricCatalogue(unittest.TestCase):
    def test_primary_is_a_subset_of_the_catalogue(self):
        self.assertTrue(set(M.PRIMARY) <= set(M.BY_KEY))

    def test_every_metric_declares_access_and_confounder(self):
        for m in M.CATALOGUE:
            self.assertIn(m.access, (M.ACCESS_BEHAVIOURAL, M.ACCESS_STRUCTURAL))
            self.assertTrue(m.confounder.strip(),
                            f"{m.key} has no declared confounder")
            self.assertTrue(m.description.strip())

    def test_task_return_is_not_primary(self):
        """Capability must never be able to decide a corrigibility hypothesis."""
        self.assertNotIn("task_return", M.PRIMARY)


if __name__ == "__main__":
    unittest.main(verbosity=2)
