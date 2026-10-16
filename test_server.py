import json, tempfile, unittest
from pathlib import Path
import server
from engine import Controller

class ServerTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.old=server.PATH
        server.PATH=Path(self.folder.name)/'state.json'
    def tearDown(self):
        server.PATH=self.old
        self.folder.cleanup()
    def test_initial_observer_knowledge(self):
        s=server.snapshot(server.load())
        self.assertEqual(s['worlds'],16)
        self.assertEqual(s['sides']['guarded']['probability'],.5)
    def test_save_load_matches_actual_trace(self):
        c=server.load()
        for r in server.REQUESTS: c.step(server.ACTUAL.key,r)
        before=server.snapshot(c)
        server.save(c)
        self.assertEqual(server.snapshot(server.load()),before)
        self.assertEqual(before['sides']['naive']['probability'],1)
        self.assertEqual(before['sides']['guarded']['probability'],.5)
        self.assertEqual(before['sides']['guarded']['events'][-1]['output'],'MEETING:2')
    def test_model_version_mismatch(self):
        server.save(Controller(server.KNOWN))
        data=json.loads(server.PATH.read_text());data['model']='different'
        server.PATH.write_text(json.dumps(data))
        with self.assertRaises(ValueError): server.load()
    def test_invalid_saved_output(self):
        c=server.load();c.step(server.ACTUAL.key,'parity');server.save(c)
        data=json.loads(server.PATH.read_text());ledger=json.loads(data['ledger'])
        ledger['transcript'][0]['output']='secret injected';data['ledger']=json.dumps(ledger)
        server.PATH.write_text(json.dumps(data))
        with self.assertRaises(ValueError): server.load()
    def test_malformed_json_rejected(self):
        server.PATH.write_text('broken')
        with self.assertRaises(json.JSONDecodeError): server.load()
    def test_budget_tamper_rejected(self):
        server.save(Controller(server.KNOWN))
        data=json.loads(server.PATH.read_text());ledger=json.loads(data['ledger'])
        ledger['budget']='1/2';data['ledger']=json.dumps(ledger)
        server.PATH.write_text(json.dumps(data))
        with self.assertRaises(ValueError): server.load()
    def test_impossible_actual_transcript_rejected(self):
        c=Controller(server.KNOWN);c.step(21,'parity');server.save(c)
        with self.assertRaises(ValueError): server.load()
    def test_changed_request_sequence_rejected(self):
        c=Controller(server.KNOWN);c.step(server.ACTUAL.key,'slot1');server.save(c)
        with self.assertRaises(ValueError): server.load()
    def test_atomic_save(self):
        server.save(server.load())
        self.assertTrue(server.PATH.exists())
        self.assertFalse(server.PATH.with_suffix('.tmp').exists())
    def test_failed_guided_replace_preserves_previous_checkpoint(self):
        from unittest.mock import patch
        c=server.load();server.save(c);previous=server.PATH.read_bytes()
        c.step(server.ACTUAL.key,'parity')
        with patch('pathlib.Path.replace',side_effect=OSError('synthetic replace failure')):
            with self.assertRaises(OSError):server.save(c)
        self.assertEqual(server.PATH.read_bytes(),previous)
        self.assertEqual(len(server.load().transcript),0)
    def test_guided_checkpoint_flushes_before_replacement(self):
        from unittest.mock import patch
        calls=[]
        import os
        original=os.fsync
        def recorded(fd):calls.append('fsync');return original(fd)
        with patch('dialog.os.fsync',side_effect=recorded):server.save(server.load())
        self.assertEqual(calls,['fsync'])
if __name__=='__main__': unittest.main(verbosity=2)
