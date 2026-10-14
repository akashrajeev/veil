import unittest,json
from fractions import Fraction
from dataclasses import asdict
from engine import make_worlds,Controller
from preference_lab import PreferenceController
from oracle import audit
class PreferenceTests(unittest.TestCase):
    def test_default_costs_match_existing_controller(self):
        domain=tuple(w for w in make_worlds() if w.bob==5)
        for actual in domain:
            a=Controller(domain);b=PreferenceController(domain)
            for r in ('parity','slot1','schedule'):self.assertEqual(a.step(actual.key,r),b.step(actual.key,r))
    def test_public_costs_change_actual_window_without_unsafe_outputs(self):
        domain=tuple(w for w in make_worlds() if w.bob==14)
        c=PreferenceController(domain,(10,20,10,0));out=c.step(15*16+14,'schedule')
        self.assertEqual(out['output'],'MEETING:3')
    def test_all_outputs_and_public_costs_oracle_checked(self):
        for costs in ((0,1,2,3),(10,20,10,0),(50,0,100,1)):
            domain=make_worlds();traces={}
            for w in domain:
                c=PreferenceController(domain,costs);events=[]
                for r in ('parity','slot1','schedule'):
                    event=c.step(w.key,r)
                    events.append({**event,'policy':event['policy']+'|costs='+str(costs)})
                traces[w.key]=events
            result=audit([asdict(w) for w in domain],traces,Fraction(0))
            self.assertEqual(result['prefix_violation_cells'],0);self.assertEqual(result['invalid_meetings'],0)
    def test_evidence_records_public_objective(self):
        domain=tuple(w for w in make_worlds() if w.bob==14)
        c=PreferenceController(domain,(10,20,10,0));e=c.evidence('schedule')
        self.assertEqual(e['public_slot_costs'],[10,20,10,0])
        self.assertGreater(e['selected_success_weight'],0)
        self.assertIn('selected_total_public_cost',e)
    def test_cost_evidence_observable_oracle(self):
        domain=make_worlds();traces={}
        for w in domain:
            c=PreferenceController(domain,(10,20,10,0));events=[]
            for r in ('parity','slot1','schedule'):
                evidence=json.dumps(c.evidence(r),sort_keys=True);event=c.step(w.key,r)
                events.append({**event,'policy':event['policy']+'|'+evidence})
            traces[w.key]=events
        self.assertEqual(audit([asdict(w) for w in domain],traces,Fraction(0))['prefix_violation_cells'],0)
    def test_incomplete_domain_never_schedules_in_preference_subclass(self):
        c=PreferenceController(make_worlds(),complete=False)
        self.assertEqual(c.step(117,'schedule')['output'],'UNKNOWN_DECLARED_DOMAIN')
        self.assertEqual(c.evidence('schedule')['safe_candidates'],0)
    def test_invalid_costs(self):
        for costs in ((0,1),(0,1,2,101),(0,1,2,True),('0',1,2,3)):
            with self.assertRaises(ValueError):PreferenceController(make_worlds(),costs)
if __name__=='__main__':unittest.main(verbosity=2)
