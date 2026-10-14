import unittest
from scenario_lab import run_scenario,comparison
class PriorLabTests(unittest.TestCase):
    def test_biased_initial_not_falsely_50(self):
        r=run_scenario(7,5,prior_odds=(1,3))
        self.assertEqual(r['initial_support'],'3/4')
        self.assertEqual(r['final_support'],'3/4')
    def test_all_declared_fact_prior_options(self):
        for fact in range(4):
            for odds in ((1,3),(3,1),(1,9)):
                for result in comparison(7,5,protected_slot=fact,prior_odds=odds).values():
                    self.assertEqual(result['observer_metrics']['prefix_violation_cells'],0)
                    self.assertEqual(result['observer_metrics']['invalid_meetings'],0)
    def test_weighted_evidence_support_not_counts(self):
        r=run_scenario(7,5,prior_odds=(1,3))
        self.assertEqual(r['decisions'][0]['initial_support'],'3/4')
    def test_invalid_prior_odds(self):
        for odds in ((0,1),(1,10),(1,True),(1,),('1',1)):
            with self.assertRaises(ValueError):run_scenario(7,5,prior_odds=odds)
if __name__=='__main__':unittest.main(verbosity=2)
