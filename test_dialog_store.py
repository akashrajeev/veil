import unittest,tempfile
from pathlib import Path
from dialog_store import initialize,status,advance
class DialogStoreTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'state.json'
    def tearDown(self):self.tmp.cleanup()
    def test_uninitialized(self):self.assertFalse(status(self.path)['initialized'])
    def test_stale_duplicate_ask_does_not_advance(self):
        s=initialize(self.path);advance(self.path,'one prep window',s['generation'],0)
        duplicate=advance(self.path,'one prep window',s['generation'],0)
        self.assertEqual(duplicate['events'],1);self.assertTrue(duplicate['stale_request'])
    def test_old_generation_after_restart_ignored(self):
        old=initialize(self.path);new=initialize(self.path)
        r=advance(self.path,'late prep availability',old['generation'],0)
        self.assertEqual(r['events'],0);self.assertEqual(r['generation'],new['generation'])
    def test_response_fixture_is_operator_data_not_private_channel(self):
        s=initialize(self.path)
        self.assertEqual(s['state']['alice'],7)
        self.assertEqual(s['state']['bob'],5)
        self.assertIn('state',s)
    def test_bound_configuration_visible_and_stable(self):
        s=initialize(self.path,15,14,1,'1/4',(10,20,10,0),(1,3))
        self.assertEqual(s['configuration']['budget'],'1/4')
        self.assertEqual(s['configuration']['public_prior'],[1,3])
        result=advance(self.path,'find a time for us',s['generation'],0)
        self.assertEqual(result['configuration'],s['configuration'])
    def test_composition_persists(self):
        s=initialize(self.path);a=advance(self.path,'one prep window',s['generation'],0)
        b=advance(self.path,'late prep availability',s['generation'],1)
        self.assertEqual(b['result']['observation']['output'],'NEEDS_PRIVATE_DECISION')
        self.assertEqual(status(self.path)['events'],2)
if __name__=='__main__':unittest.main(verbosity=2)
