import unittest,json
from fractions import Fraction
from dataclasses import asdict
from engine import Controller,make_worlds
from oracle import audit
class AlternativesTests(unittest.TestCase):
    def test_excludes_direct_protected_question(self):
        c=Controller(make_worlds());self.assertNotIn('slot0',{x['request'] for x in c.alternatives()})
    def test_refusal_still_has_schedulable_alternative(self):
        c=Controller(tuple(w for w in make_worlds() if w.bob==5));c.step(117,'parity');c.step(117,'slot1')
        self.assertIn('schedule',{x['request'] for x in c.alternatives()})
    def test_suggestions_are_observable_oracle_checked(self):
        domain=make_worlds();traces={}
        for w in domain:
            c=Controller(domain);events=[]
            for request in ('parity','slot1','schedule'):
                out=c.step(w.key,request);out={**out,'policy':out['policy']+'|suggestions='+json.dumps(c.alternatives(),sort_keys=True)};events.append(out)
            traces[w.key]=events
        self.assertEqual(audit([asdict(w) for w in domain],traces,Fraction(0))['prefix_violation_cells'],0)
    def test_incomplete_has_no_suggestions(self):self.assertEqual(Controller(make_worlds(),complete=False).alternatives(),[])
if __name__=='__main__':unittest.main(verbosity=2)
