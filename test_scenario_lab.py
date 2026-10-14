import unittest
from scenario_lab import run_scenario,comparison,SCENARIOS
class ScenarioTests(unittest.TestCase):
    def test_dinner_safe_later_meeting(self):
        r=run_scenario(7,5);self.assertEqual(r['trace'][-1]['output'],'MEETING:2')
        self.assertEqual(r['final_support'],'1/2')
    def test_infeasible_not_called_scheduled(self):
        r=run_scenario(3,12);self.assertNotEqual(r['outcome'],'scheduled')
        self.assertEqual(r['actual_common_slots'],[])
    def test_public_budget_can_reveal_protected_fact(self):
        r=comparison(7,5);self.assertEqual(r['open']['final_support'],'1')
        self.assertEqual(r['strict']['final_support'],'1/2')
    def test_all_curated_options_oracle_pass(self):
        for spec in SCENARIOS.values():
            for r in comparison(spec['alice'],spec['bob']).values():
                self.assertEqual(r['observer_metrics']['prefix_violation_cells'],0)
                self.assertEqual(r['observer_metrics']['invalid_meetings'],0)
    def test_direct_does_not_invent_query_history(self):
        self.assertEqual(len(run_scenario(7,5,script='direct')['trace']),1)
    def test_prefix_trail_keeps_initial_bound_not_step_budget(self):
        strict=run_scenario(7,5);opened=run_scenario(7,5,'open')
        self.assertEqual([x['support'] for x in strict['trajectory']],['1/2']*4)
        self.assertEqual([x['support'] for x in opened['trajectory']],['1/2','1/2','1','1'])
        self.assertEqual(strict['trajectory'][-1]['worlds'],len(strict['possible_alice_calendars']))
    def test_baseline_custom_fact_prior_leak_visible(self):
        r=run_scenario(7,5,prior_odds=(1,3))
        self.assertEqual(r['final_support'],'3/4')
        self.assertEqual(r['unguarded_baseline']['final_support'],'1')
        self.assertGreater(r['unguarded_baseline']['observer_metrics']['prefix_violation_cells'],0)
    def test_safe_policy_can_miss_actual_common_window(self):
        r=run_scenario(1,1)
        self.assertEqual(r['actual_common_slots'],[0])
        self.assertEqual(r['trace'][-1]['output'],'NO_MEETING')
        self.assertEqual(r['outcome'],'no_supported_safe_plan')
        self.assertIn('not proof',r['note'])
    def test_result_reproduction_parameters_complete(self):
        r=run_scenario(7,5,prior_odds=(1,3),costs=(3,2,1,0))
        params=r['reproduce']
        repeated=run_scenario(params['alice'],params['bob'],params['budget'],params['script'],params['protected_slot'],params['public_costs'],params['public_prior_odds'])
        self.assertEqual(r,repeated)
    def test_bad_calendars_and_option(self):
        for args in ((16,0),(True,0),(-1,0),(0,'0')):
            with self.assertRaises(ValueError):run_scenario(*args)
        with self.assertRaises(ValueError):run_scenario(0,0,budget='private-approval')
if __name__=='__main__':unittest.main(verbosity=2)
