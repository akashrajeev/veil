"""Unit tests for the v5 joint multi-window protection contract."""
import json, tempfile, unittest
from fractions import Fraction
from pathlib import Path

import dialog, dialog_store
from joint_engine import joint_worlds, JointController
import engine
import mcp_server as m


class JointWorldsTest(unittest.TestCase):
    def test_product_prior_weights(self):
        ws = joint_worlds(5, (0, 1), ((1, 3), (2, 1)))
        self.assertEqual(len(ws), 16)
        by_alice = {w.alice: w for w in ws}
        # alice with bit0=1 (free), bit1=0 (busy): weight 3*2=6
        self.assertEqual(by_alice[1].weight, 6)
        self.assertEqual(by_alice[1].secret, 1)
    def test_rejects_bad_slots(self):
        with self.assertRaises(ValueError):
            joint_worlds(5, (0, 0), ((1, 1), (1, 1)))
        with self.assertRaises(ValueError):
            joint_worlds(5, (0, 1, 2), ((1, 1),) * 3)


class JointControllerTest(unittest.TestCase):
    def test_parity_negative_control(self):
        domain = joint_worlds(5, (0, 1), ((1, 1), (1, 1)))
        joint = JointController(domain, k=2)
        self.assertFalse(joint.safe(engine.PARITY))
        m0 = engine.Controller([engine.World(w.key, w.alice, w.bob, w.alice & 1, 1) for w in domain], Fraction(0))
        m1 = engine.Controller([engine.World(w.key, w.alice, w.bob, (w.alice >> 1) & 1, 1) for w in domain], Fraction(0))
        self.assertTrue(m0.safe(engine.PARITY))
        self.assertTrue(m1.safe(engine.PARITY))
    def test_unprotected_slot_answer_preserves_joint(self):
        domain = joint_worlds(5, (0, 1), ((1, 1), (1, 1)))
        c = JointController(domain, k=2)
        c.step(7 * 16 + 5, 'slot2')
        self.assertEqual(c.joint_support(c.compatible), c.baseline)
    def test_protected_slot_direct_ask_refused(self):
        domain = joint_worlds(5, (0, 1), ((1, 1), (1, 1)))
        c = JointController(domain, k=2)
        self.assertEqual(c.choose('slot0').kind, 'refuse')
        self.assertEqual(c.choose('slot1').kind, 'refuse')
    def test_ledger_roundtrip(self):
        domain = joint_worlds(5, (0, 1), ((1, 1), (1, 1)))
        c = JointController(domain, k=2)
        c.step(7 * 16 + 5, 'slot2')
        c2 = JointController.load(domain, c.dump(), factory=lambda w, b: JointController(w, budget=b, k=2))
        self.assertEqual([str(x) for x in c2.joint_support(c2.compatible)],
                         [str(x) for x in c.joint_support(c.compatible)])


class JointDialogTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
    def test_create_restore_roundtrip(self):
        st = dialog_store.initialize(self.d/'j.json', alice=7, protected_slots=[0, 1], priors=((1, 3), (1, 1)))
        self.assertEqual(st['joint_support'], ['1/8', '3/8', '1/8', '3/8'])
        r = dialog_store.advance(self.d/'j.json', 'is alice free for dinner', st['generation'], st['events'])
        self.assertEqual(r['result']['observation']['policy'], 'alice-slot2-availability')
        self.assertEqual(r['joint_support'], ['1/8', '3/8', '1/8', '3/8'])
    def test_xor_refused_through_store(self):
        st = dialog_store.initialize(self.d/'j.json', alice=7, protected_slots=[0, 1])
        r = dialog_store.advance(self.d/'j.json', 'can alice cover exactly one of the two prep windows', st['generation'], st['events'])
        self.assertEqual(r['result']['observation']['output'], 'NEEDS_PRIVATE_DECISION')
    def test_model_mismatch_rejected(self):
        st = dialog_store.initialize(self.d/'j.json', alice=7, protected_slots=[0, 1])
        env = json.loads((self.d/'j.json').read_text())
        env['state']['model'] = '0' * 64
        (self.d/'j.json').write_text(json.dumps(env))
        with self.assertRaises(ValueError):
            dialog_store.status(self.d/'j.json')
    def test_v4_sessions_unaffected(self):
        st = dialog_store.initialize(self.d/'v4.json', alice=7, protected=0, prior=(1, 3))
        self.assertEqual(st['protected_support'], '3/4')


class JointMcpSurfaceTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
    def call(self, s, name, args, surface):
        r = m.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                      'params': {'name': name, 'arguments': args}}, s, surface)['result']
        return r
    def test_start_validates_joint_args(self):
        s = m.Session(self.d/'a.json')
        for args in ({'protected_windows': ['early prep', 'early prep']},
                     {'protected_windows': ['early prep', 'late prep', 'dinner']},
                     {'protected_window': 'early prep', 'protected_windows': ['late prep']},
                     {'protected_windows': ['early prep'], 'priors': [[1, 1], [1, 1]]},
                     {'protected_windows': ['early prep'], 'prior': [1, 1]},
                     {'priors': [[1, 1]]}):
            r = m.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                          'params': {'name': 'veil_start_household', 'arguments': args}}, s, 'operator')
            self.assertTrue(r.get('error') or r['result']['isError'], args)
    def test_operator_surface_sees_joint_not_assistant(self):
        s = m.Session(self.d/'b.json', alice=7)
        self.call(s, 'veil_start_household', {'protected_windows': ['early prep', 'late prep']}, 'operator')
        op = self.call(s, 'veil_operator_view', {}, 'operator')['structuredContent']
        self.assertEqual(op['protected_windows'], ['early prep', 'late prep'])
        self.assertEqual(len(op['joint_support']), 4)
        st = self.call(s, 'veil_status', {}, 'assistant')['structuredContent']
        self.assertNotIn('joint_support', st)
        self.assertNotIn('protected_windows', st)
    def test_joint_guard_admits_safe_and_refuses_xor(self):
        s = m.Session(self.d/'c.json', alice=7)
        self.call(s, 'veil_start_household', {'protected_windows': ['early prep', 'late prep']}, 'operator')
        ok = self.call(s, 'veil_ask', {'text': 'is alice free for cleanup'}, 'assistant')['structuredContent']
        self.assertNotEqual(ok['output'], 'REFUSED')
        no = self.call(s, 'veil_ask', {'text': 'can alice cover exactly one of the two prep windows'}, 'assistant')['structuredContent']
        self.assertEqual(no['output'], 'REFUSED')


if __name__ == '__main__':
    unittest.main()
