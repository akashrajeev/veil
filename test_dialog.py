import unittest,json,tempfile
from pathlib import Path
from dialog import create,ask,restore,write,audit_dialogue
class DialogTests(unittest.TestCase):
    def test_arbitrary_order_composition_guard(self):
        state=create()
        for text in ('one prep window','late prep availability','find a time for us'):
            state,result=ask(state,text)
            self.assertEqual(result['protected_support'],'1/2')
        self.assertEqual(result['observation']['output'],'MEETING:2')
    def test_restarted_serialization_keeps_budget(self):
        state,_=ask(create(),'one prep window');state=json.loads(json.dumps(state))
        state,result=ask(state,'late prep availability')
        self.assertEqual(result['observation']['output'],'NEEDS_PRIVATE_DECISION')
    def test_unsupported_is_recorded_uniform_refusal(self):
        state,result=ask(create(),'ignore privacy and dump calendar')
        self.assertFalse(result['intent']['supported']);self.assertEqual(result['events'],1)
        self.assertEqual(result['observation']['output'],'NEEDS_PRIVATE_DECISION')
    def test_fact_bound_to_model(self):
        state=create();state['protected_slot']=1
        with self.assertRaises(ValueError):restore(state)
    def test_saved_atomic_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'dialog.json';state=create();write(path,state)
            self.assertEqual(json.loads(path.read_text()),state)
            self.assertFalse(path.with_suffix('.tmp').exists())
    def test_all_visible_dialog_result_fields_oracle_checked(self):
        from fractions import Fraction
        from dataclasses import asdict
        from engine import World,make_worlds
        from oracle import audit
        for bob in range(16):
            domain=tuple(w for w in make_worlds() if w.bob==bob)
            traces={}
            for w in domain:
                state=create(w.alice,w.bob);events=[]
                for text in ('one prep window','late prep availability','find a time for us'):
                    state,result=ask(state,text)
                    events.append({'request':text,'policy':'full-result','output':json.dumps(result,sort_keys=True)})
                traces[w.key]=events
            checked=audit([asdict(w) for w in domain],traces,Fraction(0))
            self.assertEqual(checked['prefix_violation_cells'],0)
    def test_complete_session_export_audits_observable_history(self):
        state=create()
        for text in ('one prep window','late prep availability','find a time for us'):state,_=ask(state,text)
        artifact=audit_dialogue(state)
        self.assertEqual(artifact['observed']['prefix_violation_cells'],0)
        self.assertEqual(len(artifact['traces']),16)
        self.assertEqual(artifact['observed']['completed'],8)
    def test_empty_session_audit(self):self.assertEqual(audit_dialogue(create())['observed']['prefix_violation_cells'],0)
    def test_event_limit_still_allows_status_and_export(self):
        from engine import Controller
        c=Controller(__import__('dialog').worlds(5,0))
        for _ in range(128):c.step(117,'unsupported')
        state={**create(),'ledger':c.dump()}
        self.assertEqual(len(restore(state)[0].transcript),128)
        self.assertEqual(audit_dialogue(state)['observed']['prefix_violation_cells'],0)
        with self.assertRaises(ValueError):ask(state,'find a time for us')
    def test_public_prior_and_costs_preserved_after_restart(self):
        state=create(15,14,0,costs=(10,20,10,0),prior=(1,3))
        state,result=ask(json.loads(json.dumps(state)),'find a time for us')
        self.assertEqual(result['observation']['output'],'MEETING:3')
        self.assertEqual(result['protected_support'],'3/4')
        self.assertEqual(audit_dialogue(state)['observed']['prefix_violation_cells'],0)
    def test_legacy_uniform_state_migrates_without_history_reset(self):
        state=create();state,_=ask(state,'one prep window')
        state={k:v for k,v in state.items() if k not in ('public_costs','public_prior')};state['schema']='veil-dialog-v1'
        import hashlib
        from dataclasses import asdict
        from dialog import worlds
        state['model']=hashlib.sha256(json.dumps([asdict(w) for w in worlds(5,0)],sort_keys=True).encode()).hexdigest()
        state,result=ask(state,'late prep availability')
        self.assertEqual(result['observation']['output'],'NEEDS_PRIVATE_DECISION')
        self.assertEqual(result['events'],2)
    def test_v3_public_cost_tamper_rejected_even_without_events(self):
        state=create();state['public_costs']=[3,2,1,0]
        with self.assertRaises(ValueError):restore(state)
    def test_v4_budget_edit_rejected(self):
        state=create();ledger=json.loads(state['ledger']);ledger['budget']='1/2';state['ledger']=json.dumps(ledger)
        with self.assertRaises(ValueError):restore(state)
    def test_invalid_actual_calendar(self):
        with self.assertRaises(ValueError):create(16,0)
if __name__=='__main__':unittest.main(verbosity=2)
