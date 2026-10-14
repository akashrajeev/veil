"""Policy and prior invariants independent of the consumer demo fixture."""
import unittest, random
from fractions import Fraction
from dataclasses import asdict
from engine import Controller, World, make_worlds, Policy
from oracle import audit

class Invariants(unittest.TestCase):
    def test_boundary_domain(self):
        with self.assertRaises(ValueError): Controller(())
        with self.assertRaises(ValueError): Controller(tuple(World(i,0,0,0) for i in range(257)))
        with self.assertRaises(ValueError): Controller((World(1,0,0,0),World(1,1,0,1)))
        with self.assertRaises(ValueError): Controller((World(1,0,0,0,0),))
    def test_invalid_budget(self):
        for value in (Fraction(-1,10),Fraction(11,10)):
            with self.assertRaises(ValueError): Controller(make_worlds(),value)
    def test_actual_key_outside_declared_domain(self):
        with self.assertRaises(ValueError): Controller(make_worlds()).step(1000,'schedule')
    def test_singleton_prior_not_fake_privacy(self):
        c=Controller((World(1,15,15,1),))
        self.assertEqual(c.baseline,1)
        c.step(1,'schedule')
        self.assertEqual(c.support(c.compatible),1)
    def test_constant_secret_never_false_leak(self):
        worlds=tuple(World(w.key,w.alice,w.bob,1) for w in make_worlds())
        c=Controller(worlds);c.step(117,'parity');c.step(117,'slot1')
        self.assertEqual(c.support(c.compatible),1)
    def test_world_order_does_not_change_selection(self):
        domain=list(make_worlds());random.Random(700).shuffle(domain)
        a=Controller(make_worlds());b=Controller(domain)
        for request in ('parity','slot1','schedule'):
            self.assertEqual(a.step(117,request),b.step(117,request))
    def test_repeated_schedule_is_stable(self):
        for w in make_worlds():
            c=Controller(make_worlds());first=c.step(w.key,'schedule')
            self.assertEqual(c.step(w.key,'schedule')['output'],first['output'])
        result=audit([asdict(x) for x in make_worlds()],
                     {x.key:self.trace_twice(x.key) for x in make_worlds()},Fraction(0))
        self.assertEqual(result['prefix_violation_cells'],0)
    @staticmethod
    def trace_twice(key):
        c=Controller(make_worlds());c.step(key,'schedule');c.step(key,'schedule')
        return c.transcript
    def test_oracle_detects_policy_selection_side_channel(self):
        worlds=make_worlds();traces={w.key:[{'request':'noop','policy':str(w.secret),'output':'same'}] for w in worlds}
        self.assertGreater(audit([asdict(w) for w in worlds],traces,Fraction(0))['prefix_violation_cells'],0)
    def test_known_fact_kept_as_known_not_zero(self):
        # Zero shift means unchanged prior, NOT absolute ignorance.
        worlds=(World(0,0,0,1,3),World(1,1,0,0,1))
        c=Controller(worlds);self.assertEqual(c.baseline,Fraction(3,4))
        self.assertEqual(c.step(0,'unsupported')['output'],'NEEDS_PRIVATE_DECISION')
        self.assertEqual(c.support(c.compatible),Fraction(3,4))

if __name__=='__main__': unittest.main(verbosity=2)
