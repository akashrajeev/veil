"""Exhaust all 256 binary secret assignments on one declared 8-world domain.
Does not prove all possible calendar domains, priors or multi-secret behavior.
"""
import unittest
from dataclasses import asdict
from fractions import Fraction
from engine import Controller, World
from oracle import audit

class SecretFunctions(unittest.TestCase):
    def test_every_binary_labeling_on_eight_worlds(self):
        base=[(a,b) for a in range(4) for b in (1,2)]
        for truth_table in range(256):
            worlds=tuple(World(i,a,b,(truth_table>>i)&1) for i,(a,b) in enumerate(base))
            traces={}
            for w in worlds:
                c=Controller(worlds)
                for r in ('parity','slot1','schedule','parity-again'):
                    c.step(w.key,r)
                traces[w.key]=c.transcript
            result=audit([asdict(w) for w in worlds],traces,Fraction(0))
            self.assertEqual(result['prefix_violation_cells'],0,truth_table)
            self.assertEqual(result['invalid_meetings'],0,truth_table)

if __name__=='__main__':unittest.main(verbosity=2)
