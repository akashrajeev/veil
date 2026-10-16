"""Seeded free-dialogue roundtrip equivalence under fixed public parameters."""
import json,random,unittest
from dialog import create,ask,restore
class RestartEquivalenceTests(unittest.TestCase):
    def test_serialized_restart_before_every_request_preserves_full_result(self):
        rng=random.Random(93344)
        requests=('one prep window','early prep availability','late prep availability','dinner availability','cleanup availability','find a time for us','unsupported command')
        for trial in range(24):
            alice=rng.randrange(16);bob=rng.randrange(16);protected=rng.randrange(4)
            costs=tuple(rng.randrange(25) for _ in range(4));prior=(rng.randint(1,9),rng.randint(1,9));budget=rng.choice(('0','1/4','1/2'))
            direct=create(alice,bob,protected,budget,costs,prior);restarted=json.loads(json.dumps(direct))
            for _ in range(16):
                text=rng.choice(requests)
                direct,a=ask(direct,text)
                restarted,b=ask(json.loads(json.dumps(restarted)),text)
                self.assertEqual(a,b,(trial,text));self.assertEqual(direct,restarted)
            self.assertEqual(restore(direct)[0].dump(),restore(restarted)[0].dump())
if __name__=='__main__':unittest.main(verbosity=2)
