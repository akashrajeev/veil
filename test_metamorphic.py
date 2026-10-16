"""Finite-model invariance checks, not real-prior or arbitrary-policy proofs."""
import random,unittest
from fractions import Fraction
from engine import World,make_worlds
from preference_lab import PreferenceController
class MetamorphicTests(unittest.TestCase):
    def domains(self):
        rng=random.Random(71026)
        for _ in range(12):
            bob=rng.randrange(16);protected=rng.randrange(4);weights=(rng.randint(1,9),rng.randint(1,9))
            domain=tuple(World(w.key,w.alice,w.bob,(w.alice>>protected)&1,weights[(w.alice>>protected)&1])
                         for w in make_worlds() if w.bob==bob)
            yield domain,tuple(rng.randrange(20) for _ in range(4)),rng.choice((Fraction(0),Fraction(1,4),Fraction(1,2)))
    def test_global_prior_scaling_preserves_outputs_and_posteriors(self):
        for domain,costs,budget in self.domains():
            scaled=tuple(World(w.key,w.alice,w.bob,w.secret,w.weight*7) for w in domain)
            for actual in domain:
                a=PreferenceController(domain,costs,budget);b=PreferenceController(scaled,costs,budget)
                for request in ('slot2','parity','slot1','schedule','slot3','unsupported'):
                    self.assertEqual(a.step(actual.key,request),b.step(actual.key,request))
                    self.assertEqual(a.support(a.compatible),b.support(b.compatible))
    def test_world_relabeling_and_order_preserve_public_events(self):
        for domain,costs,budget in self.domains():
            relabeled=tuple(World(w.key+10000,w.alice,w.bob,w.secret,w.weight) for w in reversed(domain))
            for actual in domain:
                a=PreferenceController(domain,costs,budget);b=PreferenceController(relabeled,costs,budget)
                for request in ('slot3','parity','slot1','schedule'):
                    self.assertEqual(a.step(actual.key,request),b.step(actual.key+10000,request))
                    self.assertEqual(a.support(a.compatible),b.support(b.compatible))
    def test_positive_cost_scaling_preserves_restricted_optimum(self):
        for domain,costs,budget in self.domains():
            a=PreferenceController(domain,costs,budget);b=PreferenceController(domain,tuple(x*3 for x in costs),budget)
            self.assertEqual(a.choose('schedule'),b.choose('schedule'))
            for actual in domain:
                x=PreferenceController(domain,costs,budget);y=PreferenceController(domain,tuple(c*3 for c in costs),budget)
                for request in ('parity','slot1','schedule'):
                    self.assertEqual(x.step(actual.key,request),y.step(actual.key,request))
    def test_complementing_protected_fact_preserves_decisions(self):
        for domain,costs,budget in self.domains():
            complement=tuple(World(w.key,w.alice,w.bob,1-w.secret,w.weight) for w in domain)
            for actual in domain:
                a=PreferenceController(domain,costs,budget);b=PreferenceController(complement,costs,budget)
                for request in ('slot2','parity','slot1','schedule'):
                    self.assertEqual(a.step(actual.key,request),b.step(actual.key,request))
                    self.assertEqual(a.support(a.compatible)+b.support(b.compatible),1)
    def test_wider_initial_budget_cannot_reduce_supported_scheduling_success(self):
        for domain,costs,_ in self.domains():
            last=-1
            for budget in (Fraction(0),Fraction(1,8),Fraction(1,4),Fraction(1,2),Fraction(1)):
                c=PreferenceController(domain,costs,budget);policy=c.choose('schedule')
                success=sum(w.weight for w in domain if policy.output(w).startswith('MEETING:'))
                self.assertGreaterEqual(success,last);last=success
if __name__=='__main__':unittest.main(verbosity=2)
