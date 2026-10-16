import unittest,json
from dataclasses import asdict
from fractions import Fraction
from engine import Controller,World,make_worlds
from oracle import audit
from dialog import create,ask,audit_dialogue
class AvailabilityTests(unittest.TestCase):
    def test_protected_slot_directly_refused(self):
        labels=['early prep','late prep','dinner','cleanup']
        for protected in range(4):
            state=create(protected=protected);state,result=ask(state,'is alice free for '+labels[protected])
            self.assertEqual(result['observation']['output'],'NEEDS_PRIVATE_DECISION')
            self.assertEqual(result['protected_support'],'1/2')
    def test_all_four_queries_composition_oracle(self):
        for protected in range(4):
            worlds=tuple(World(w.key,w.alice,w.bob,(w.alice>>protected)&1) for w in make_worlds())
            traces={}
            for w in worlds:
                c=Controller(worlds);events=[]
                for r in ('slot0','slot1','slot2','slot3','parity','schedule'):
                    e=json.dumps(c.evidence(r),sort_keys=True);out=c.step(w.key,r)
                    events.append({**out,'policy':out['policy']+'|'+e})
                traces[w.key]=events
            result=audit([asdict(w) for w in worlds],traces,Fraction(0))
            self.assertEqual(result['prefix_violation_cells'],0);self.assertEqual(result['invalid_meetings'],0)
    def test_new_query_history_restores(self):
        state=create();state,_=ask(state,'cleanup availability');state=json.loads(json.dumps(state))
        state,result=ask(state,'dinner availability');self.assertEqual(result['events'],2)
        self.assertEqual(audit_dialogue(state)['observed']['prefix_violation_cells'],0)
if __name__=='__main__':unittest.main(verbosity=2)
