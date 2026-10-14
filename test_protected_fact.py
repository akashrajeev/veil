import unittest
from scenario_lab import run_scenario,comparison
class ProtectedFactTests(unittest.TestCase):
    def test_each_single_fact_oracle_checked(self):
        for protected in range(4):
            for alice,bob in ((7,5),(15,15),(1,1),(3,12),(0,0)):
                for r in comparison(alice,bob,protected_slot=protected).values():
                    self.assertEqual(r['observer_metrics']['prefix_violation_cells'],0)
                    self.assertEqual(r['observer_metrics']['invalid_meetings'],0)
                    self.assertEqual(r['protected_slot'],protected)
    def test_protected_late_prep_refuses_single_disclosure(self):
        r=run_scenario(7,5,protected_slot=1)
        self.assertEqual(r['trace'][1]['output'],'NEEDS_PRIVATE_DECISION')
        self.assertEqual(r['final_support'],'1/2')
    def test_unsupported_fact_selection_rejected(self):
        for protected in (4,-1,True,'0'):
            with self.assertRaises(ValueError):run_scenario(7,5,protected_slot=protected)
if __name__=='__main__':unittest.main(verbosity=2)
