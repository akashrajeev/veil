import unittest
from dataclasses import asdict
from engine import World,make_worlds
from experiment_spec import run,verify_result
class SpecTests(unittest.TestCase):
    def spec(self):return {'worlds':[asdict(w) for w in make_worlds() if w.bob==5],
                         'actual_key':117,'requests':['parity','slot1','schedule'],'budget':'0','public_costs':[0,1,2,3]}
    def test_normal_declared_experiment(self):
        r=run(self.spec());self.assertEqual(r['observed']['prefix_violation_cells'],0)
        self.assertEqual(r['actual_trace'][-1]['observation']['output'],'MEETING:2')
    def test_correlated_domain_conditioned_before_run(self):
        s=self.spec();s['worlds']=[asdict(World(a*16+5,a,5,a&1)) for a in range(16) if (a>>1)&1]
        r=run(s);self.assertEqual(r['actual_trace'][0]['observation']['output'],'NEEDS_PRIVATE_DECISION')
    def test_unknown_keys_and_executable_content_rejected(self):
        for mutation in ({'script':'os.remove(*)'},{'url':'https://example.invalid'}):
            s=self.spec();s.update(mutation)
            with self.assertRaises(ValueError):run(s)
    def test_invalid_request_type_rejected(self):
        s=self.spec();s['requests']=[{}]
        with self.assertRaises(ValueError):run(s)
    def test_known_initial_fact_warned_not_called_secret(self):
        s=self.spec();s['worlds']=[w for w in s['worlds'] if w['secret']==1]
        r=run(s);self.assertTrue(r['prior_already_determines_fact'])
        self.assertEqual(r['initial_protected_support'],'1')
        self.assertIn('unknown initially',r['note'])
    def test_numeric_ambiguous_budget_rejected(self):
        for budget in (True,0.5,0,[], '1'*33, '1/0', '0/0'):
            s=self.spec();s['budget']=budget
            with self.assertRaises(ValueError):run(s)
    def test_result_keeps_independent_input_for_exact_rerun(self):
        import json
        original=self.spec();result=run(original)
        replay=run(json.loads(json.dumps(result['input_spec'])))
        self.assertEqual(result,replay)
        original['worlds'][0]['weight']=8
        self.assertEqual(result['input_spec']['worlds'][0]['weight'],1)
    def test_input_fingerprint_changes_with_declared_prior(self):
        original=self.spec();first=run(original)
        original['worlds'][0]['weight']=2
        self.assertNotEqual(first['input_sha256'],run(original)['input_sha256'])
    def test_downloaded_result_verifies_by_exact_replay(self):
        result=run(self.spec());self.assertTrue(verify_result(result)['verified'])
        result['observed']['invalid_meetings']=1
        with self.assertRaisesRegex(ValueError,'differs'):verify_result(result)
    def test_downloaded_input_fingerprint_edit_rejected(self):
        result=run(self.spec());result['input_sha256']='0'*64
        with self.assertRaises(ValueError):verify_result(result)
    def test_actual_not_in_domain(self):
        s=self.spec();s['actual_key']=10000
        with self.assertRaises(ValueError):run(s)
if __name__=='__main__':unittest.main(verbosity=2)
