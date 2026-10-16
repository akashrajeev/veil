"""Independent restricted-vocabulary optimality check, not arbitrary-protocol proof."""
import unittest
from itertools import permutations
from fractions import Fraction
from engine import Controller,make_worlds

class RestrictedOptimality(unittest.TestCase):
    def test_selected_schedule_matches_independent_candidate_enumeration(self):
        # Independently construct and score every ordered nonempty subset.
        orders=[o for n in range(1,5) for o in permutations(range(4),n)]
        for bob in range(16):
            worlds=tuple(w for w in make_worlds() if w.bob==bob)
            for a in (0,3,7,15):
                actual=next(w for w in worlds if w.alice==a)
                c=Controller(worlds);c.step(actual.key,'parity')
                compatible=c.compatible;baseline=Fraction(1,2)
                best=None
                for order in orders:
                    cells={};success=0;cost=0
                    for w in compatible:
                        out=next((i for i in order if w.alice&w.bob&(1<<i)),None)
                        cells.setdefault(out,[]).append(w)
                        if out is not None:success+=1;cost+=out
                    safe=all(Fraction(sum(w.secret for w in cell),len(cell))==baseline for cell in cells.values())
                    if safe:
                        candidate=(-success,cost,'first-common-'+'-'.join(map(str,order)))
                        best=min(best,candidate) if best else candidate
                chosen=c.choose('schedule')
                self.assertEqual(chosen.name,best[2] if best else 'uniform-refusal')
if __name__=='__main__':unittest.main(verbosity=2)
