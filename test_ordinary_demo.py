import unittest,json
from pathlib import Path
from fractions import Fraction
from experiment_spec import run
class OrdinaryDemoTests(unittest.TestCase):
    def test_individually_safe_together_leak_and_uniform_fallback(self):
        spec=json.loads((Path(__file__).parent/'examples/ordinary-questions-correlated.json').read_text())
        records=spec['worlds']
        def support(cell):return Fraction(sum(w['secret'] for w in cell),len(cell))
        for slot in (1,2):
            for bit in (0,1):self.assertEqual(support([w for w in records if (w['alice']>>slot)&1==bit]),Fraction(1,2))
        for first in (0,1):
            for second in (0,1):
                cell=[w for w in records if ((w['alice']>>1)&1)==first and ((w['alice']>>2)&1)==second]
                self.assertIn(support(cell),(0,1))
        r=run(spec);self.assertEqual(r['actual_trace'][1]['observation']['output'],'NEEDS_PRIVATE_DECISION')
        self.assertEqual(r['actual_trace'][-1]['observation']['output'],'MEETING:3')
        self.assertEqual(r['observed']['prefix_violation_cells'],0)
        self.assertEqual(r['observed']['invalid_meetings'],0)
if __name__=='__main__':unittest.main(verbosity=2)
