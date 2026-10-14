import json,unittest
from fractions import Fraction
from dataclasses import asdict
from engine import Controller,World,make_worlds,scheduling_policies
from oracle import audit

class EvidenceTests(unittest.TestCase):
    def test_input_types_rejected(self):
        for w in (World(0,-1,0,0),World(0,16,0,0),World(0,0,0,True),World(0,0,0,0,True),World('0',0,0,0),World(0,0,0,0,.5)):
            with self.assertRaises(ValueError):Controller((w,))
        with self.assertRaises(ValueError):Controller(make_worlds(),complete='false')
    def test_slot_boundary(self):
        for count in (0,5,True,'4'):
            for fn in (make_worlds,scheduling_policies):
                with self.assertRaises(ValueError):fn(count)
    def test_refusal_evidence_shows_composition_risk(self):
        c=Controller(make_worlds());c.step(117,'parity')
        e=c.evidence('slot1')
        self.assertEqual(e['selected_policy'],'uniform-refusal')
        self.assertFalse(e['requested_supported'])
        self.assertEqual({x['protected_support'] for x in e['requested_cells']},{'0','1'})
        self.assertEqual(e['selected_cells'][0]['protected_support'],'1/2')
    def test_evidence_does_not_mutate_ledger(self):
        c=Controller(make_worlds());before=c.dump();c.evidence('schedule');self.assertEqual(c.dump(),before)
    def test_classwide_evidence_included_in_observer_trace(self):
        worlds=make_worlds();traces={}
        for w in worlds:
            c=Controller(worlds);events=[]
            for request in ('parity','slot1','schedule'):
                # Evidence is observable: serialize it into the policy identity field.
                evidence=json.dumps(c.evidence(request),sort_keys=True)
                event=c.step(w.key,request);event={**event,'policy':event['policy']+'|'+evidence}
                events.append(event)
            traces[w.key]=events
        result=audit([asdict(w) for w in worlds],traces,Fraction(0))
        self.assertEqual(result['prefix_violation_cells'],0)
    def test_incomplete_evidence_no_guarantee(self):
        c=Controller(make_worlds(),complete=False);e=c.evidence('slot1')
        self.assertFalse(e['requested_supported']);self.assertEqual(e['selected_policy'],'uniform-unknown')

if __name__=='__main__':unittest.main(verbosity=2)
