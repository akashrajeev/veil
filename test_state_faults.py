"""Restored-history/envelope fault controls, not authenticated storage proof."""
import unittest,json,tempfile,random
from pathlib import Path
from dialog import create,restore,ask,write
from dialog_store import initialize,status
from engine import Controller

class StateFaultTests(unittest.TestCase):
    def test_long_unsupported_history_remains_safe_after_restore(self):
        state=create(prior=(1,3))
        for _ in range(120):state,_=ask(state,'unsupported command')
        state=json.loads(json.dumps(state));c,key=restore(state)
        self.assertEqual(len(c.transcript),120);self.assertEqual(str(c.support(c.compatible)),'3/4')
    def test_event_limit_refuses_without_changing_valid_state(self):
        state=create()
        for _ in range(128):state,_=ask(state,'unsupported command')
        before=json.dumps(state,sort_keys=True)
        with self.assertRaisesRegex(ValueError,'event limit'):ask(state,'find a time for us')
        self.assertEqual(json.dumps(state,sort_keys=True),before)
        self.assertEqual(len(restore(state)[0].transcript),128)
    def test_failed_atomic_replace_preserves_previous_checkpoint(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'state.json';write(path,{'old':True})
            with patch('pathlib.Path.replace',side_effect=OSError('synthetic replace failure')):
                with self.assertRaises(OSError):write(path,{'new':True})
            self.assertEqual(json.loads(path.read_text()),{'old':True})
    def test_session_envelope_mutations_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'state.json';initialize(path);base=json.loads(path.read_text())
            for value in (None,[],{}, {'generation':'x','state':base['state']}, {'generation':3,'state':base['state']}, {**base,'extra':1}):
                path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):status(path)
    def test_invalid_ledger_roots_rejected_cleanly(self):
        for value in ('null','[]',3,'{}'):
            state=create();state['ledger']=value
            with self.assertRaises(ValueError):restore(state)
    def test_restored_request_order_matches_original(self):
        state=create();sequence=['cleanup availability','one prep window','late prep availability','find a time for us']
        for text in sequence:state,_=ask(state,text)
        before=restore(state)[0].dump();after=restore(json.loads(json.dumps(state)))[0].dump()
        self.assertEqual(before,after)
    def test_weighted_session_fact_and_prior_tampering_rejected(self):
        for field,value in (('public_prior',[3,1]),('protected_slot',1),('public_costs',[3,2,1,0])):
            state=create();state[field]=value
            with self.assertRaises(ValueError):restore(state)
if __name__=='__main__':unittest.main(verbosity=2)
