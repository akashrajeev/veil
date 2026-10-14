"""Independent exhaustive supported-policy optimizer for weighted public scenarios."""
import unittest,random
from itertools import permutations
from fractions import Fraction
from engine import World,make_worlds
from preference_lab import PreferenceController

class WeightedOptimumTests(unittest.TestCase):
    def test_seeded_weighted_public_cost_optimum(self):
        rng=random.Random(7493)
        orders=[o for n in range(1,5) for o in permutations(range(4),n)]
        for trial in range(100):
            bob=rng.randrange(16);fact=rng.randrange(4);odds=(rng.randint(1,9),rng.randint(1,9))
            costs=tuple(rng.randrange(50) for _ in range(4));budget=rng.choice((Fraction(0),Fraction(1,4),Fraction(1,2)))
            domain=tuple(World(w.key,w.alice,w.bob,(w.alice>>fact)&1,odds[(w.alice>>fact)&1]) for w in make_worlds() if w.bob==bob)
            actual=rng.choice(domain);c=PreferenceController(domain,costs,budget)
            for request in rng.sample(['parity','slot0','slot1','slot2','slot3'],2):c.step(actual.key,request)
            compatible=c.compatible;initial=Fraction(sum(w.secret*w.weight for w in domain),sum(w.weight for w in domain))
            candidates=[]
            for order in orders:
                cells={};weight=cost=0
                for w in compatible:
                    slot=next((s for s in order if w.alice&w.bob&(1<<s)),None)
                    cells.setdefault(slot,[]).append(w)
                    if slot is not None:weight+=w.weight;cost+=costs[slot]*w.weight
                safe=all(abs(Fraction(sum(w.secret*w.weight for w in cell),sum(w.weight for w in cell))-initial)<=budget for cell in cells.values())
                if safe:candidates.append((-weight,cost,'first-common-'+'-'.join(map(str,order))))
            expected=min(candidates)[2] if candidates else 'uniform-refusal'
            self.assertEqual(c.choose('schedule').name,expected,trial)
if __name__=='__main__':unittest.main(verbosity=2)
