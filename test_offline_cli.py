"""Subprocess checks of operator-visible offline success and failure semantics."""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from audit_export import export
class OfflineCliTests(unittest.TestCase):
    def run_audit(self,payload):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'audit.json';path.write_text(payload)
            return subprocess.run([sys.executable,'audit_export.py','--verify',str(path)],capture_output=True,text=True)
    def test_valid_download_returns_zero(self):
        result=self.run_audit(json.dumps(export()))
        self.assertEqual(result.returncode,0);self.assertEqual(json.loads(result.stdout)['invalid_calendar_answers'],0)
    def test_invalid_files_return_validation_exit_without_traceback(self):
        for payload in ('not json','null','[]','{}'):
            result=self.run_audit(payload)
            self.assertEqual(result.returncode,2);self.assertIn('Audit not verified:',result.stderr)
            self.assertNotIn('Traceback',result.stderr)
    def test_privacy_and_false_answer_failures_return_one(self):
        for mutation in ('leak','false'):
            artifact=export()
            for record in artifact['world_records']:
                event=artifact['traces'][str(record['key'])][0]
                if mutation=='leak':event['policy']+='|secret='+str(record['secret'])
                else:event['output']='PARITY:'+str(1^(((record['alice']>>0)^(record['alice']>>1))&1))
            result=self.run_audit(json.dumps(artifact))
            self.assertEqual(result.returncode,1);self.assertEqual(result.stderr,'')
    def test_missing_path_and_invalid_resident_are_validation_failures(self):
        for args in (['--verify','/path-that-does-not-exist/veil.json'],['--bob','16']):
            result=subprocess.run([sys.executable,'audit_export.py',*args],capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertNotIn('Traceback',result.stderr)
    def test_downloaded_result_cli_replays_and_detects_edit(self):
        from experiment_spec import run
        from test_experiment_spec import SpecTests
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'result.json';result=run(SpecTests().spec())
            path.write_text(json.dumps(result))
            args=[sys.executable,'experiment_spec.py','--verify-result',str(path)]
            done=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(done.returncode,0);self.assertTrue(json.loads(done.stdout)['verified'])
            result['input_sha256']='bad';path.write_text(json.dumps(result))
            done=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(done.returncode,1);self.assertIn('differs',done.stderr)
if __name__=='__main__':unittest.main(verbosity=2)
