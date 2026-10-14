"""No expensive child tests needed to check the verification runner contract."""
import io,subprocess,sys,unittest
from contextlib import redirect_stdout,redirect_stderr
from unittest.mock import patch
import verify_all
class VerificationRunnerTests(unittest.TestCase):
    def invoke(self,args,response):
        stdout=io.StringIO();stderr=io.StringIO()
        with patch.object(sys,'argv',['verify_all.py',*args]),patch('verify_all.subprocess.run',side_effect=response) as child,redirect_stdout(stdout),redirect_stderr(stderr):
            code=verify_all.main()
        return code,stdout.getvalue(),stderr.getvalue(),child.call_count
    def test_failed_child_stops_without_pass_claim(self):
        response=lambda *a,**k:subprocess.CompletedProcess(a[0],3,'details','failure')
        code,out,err,count=self.invoke([],response)
        self.assertEqual(code,3);self.assertEqual(count,1);self.assertNotIn('"passed": true',out);self.assertIn('failure',err)
    def test_timeout_stops_with_explicit_nonpass(self):
        def timeout(*a,**k):raise subprocess.TimeoutExpired(a[0],1)
        code,out,err,count=self.invoke([],timeout)
        self.assertEqual(code,124);self.assertEqual(count,1);self.assertIn('"passed": false',out)
    def test_full_runs_exact_advertised_job_set(self):
        response=lambda *a,**k:subprocess.CompletedProcess(a[0],0,'','OK')
        code,out,err,count=self.invoke(['--full'],response)
        self.assertEqual(code,0);self.assertEqual(count,4);self.assertIn('"passed": true',out)
    def test_invalid_timeout_rejected_before_children(self):
        with patch.object(sys,'argv',['verify_all.py','--timeout-seconds','0']),patch('verify_all.subprocess.run') as child,redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):verify_all.main()
            child.assert_not_called()
if __name__=='__main__':unittest.main(verbosity=2)
