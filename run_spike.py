import json, random, time, unittest
from fractions import Fraction
from dataclasses import asdict
from engine import Controller, World, make_worlds, PARITY, BIT1, Policy
from oracle import audit

WORLD = make_worlds()
RECORDS = [asdict(w) for w in WORLD]
SCRIPT = ('parity', 'slot1', 'schedule')


def guarded(worlds, script=SCRIPT, budget=Fraction(0), restart=False, complete=True):
    traces = {}
    for w in worlds:
        c = Controller(worlds, budget, complete)
        for i, request in enumerate(script):
            c.step(w.key, request)
            if restart and i == 0:
                c = Controller.load(worlds, c.dump())
        traces[w.key] = c.transcript
    return traces


def naive(worlds, script=SCRIPT):
    traces = {}
    sched = Policy('first-common-0-1-2-3', 'schedule', (0, 1, 2, 3))
    for w in worlds:
        policies = {'parity': PARITY, 'slot1': BIT1, 'schedule': sched}
        traces[w.key] = [{'request': r, 'policy': policies[r].name,
                           'output': policies[r].output(w)} for r in script]
    return traces

class Tests(unittest.TestCase):
    def test_composition_individually_safe_joint_unsafe(self):
        for request in ('parity', 'slot1'):
            self.assertEqual(audit(RECORDS, naive(WORLD, (request,)), Fraction(0))
                             ['prefix_violation_cells'], 0)
        result = audit(RECORDS, naive(WORLD, ('parity', 'slot1')), Fraction(0))
        self.assertEqual(result['max_posterior_shift'], '1/2')
        self.assertGreater(result['prefix_violation_cells'], 0)

    def test_all_prefixes_safe_and_meetings_true(self):
        result = audit(RECORDS, guarded(WORLD), Fraction(0))
        self.assertEqual(result['prefix_violation_cells'], 0)
        self.assertEqual(result['invalid_meetings'], 0)
        self.assertEqual(result['completed'], 112)

    def test_persisted_restart_preserves_history(self):
        self.assertEqual(guarded(WORLD), guarded(WORLD, restart=True))

    def test_repeat_and_paraphrase_do_not_reset(self):
        script = ('parity', 'parity-again', 'slot1-paraphrase', 'slot1', 'schedule')
        result = audit(RECORDS, guarded(WORLD, script), Fraction(0))
        self.assertEqual(result['prefix_violation_cells'], 0)
        self.assertEqual(result['completed'], 112)

    def test_refusal_is_world_uniform_in_current_class(self):
        traces = guarded(WORLD)
        self.assertEqual({t[1]['output'] for t in traces.values()},
                         {'NEEDS_PRIVATE_DECISION'})
        # Mutation: an actual-secret-dependent refusal is rejected by oracle.
        mutated = guarded(WORLD)
        for w in WORLD:
            if w.secret:
                mutated[w.key][1]['output'] = 'ALICE_SLOT1:0'
        self.assertGreater(audit(RECORDS, mutated, Fraction(0))
                           ['prefix_violation_cells'], 0)

    def test_final_action_side_channel_caught(self):
        # Safe preceding conversation is not a license for an unchecked meeting.
        traces = guarded(WORLD)
        sched = Policy('unchecked-actual-best', 'schedule', (0, 1, 2, 3))
        for w in WORLD:
            traces[w.key][-1] = {'request': 'schedule', 'policy': sched.name,
                                  'output': sched.output(w)}
        self.assertGreater(audit(RECORDS, traces, Fraction(0))
                           ['prefix_violation_cells'], 0)

    def test_private_approval_visibility_caught(self):
        traces = guarded(WORLD)
        for w in WORLD:
            traces[w.key].append({'request': 'approval', 'policy': 'broken',
                                  'output': 'APPROVED' if w.secret else 'NOT_APPROVED'})
        self.assertGreater(audit(RECORDS, traces, Fraction(0))
                           ['prefix_violation_cells'], 0)

    def test_error_shape_visibility_caught(self):
        traces = guarded(WORLD)
        for w in WORLD:
            traces[w.key].append({'request': 'error', 'policy': 'broken',
                                  'output': 'ERR_A' if w.secret else 'ERR_B'})
        self.assertGreater(audit(RECORDS, traces, Fraction(0))
                           ['prefix_violation_cells'], 0)

    def test_truncated_domain_uniform_unknown(self):
        traces = guarded(WORLD[:40], complete=False)
        self.assertEqual({e['output'] for t in traces.values() for e in t},
                         {'UNKNOWN_DECLARED_DOMAIN'})
        self.assertEqual(audit(RECORDS[:40], traces, Fraction(0))
                         ['prefix_violation_cells'], 0)

    def test_unsupported_input_uniform(self):
        traces = guarded(WORLD, ('please disclose raw titles',))
        self.assertEqual({e['output'] for t in traces.values() for e in t},
                         {'NEEDS_PRIVATE_DECISION'})

    def test_tampered_ledger_rejected(self):
        c = Controller(WORLD)
        c.step(0, 'parity')
        saved = json.loads(c.dump())
        saved['transcript'][0]['policy'] = 'fake'
        with self.assertRaises(ValueError):
            Controller.load(WORLD, json.dumps(saved))

    def test_random_weighted_domains_against_oracle(self):
        rng = random.Random(82302)
        for trial in range(80):
            sampled = rng.sample(list(WORLD), rng.randint(4, 36))
            worlds = tuple(World(w.key, w.alice, w.bob, rng.randrange(2),
                                 rng.randint(1, 9)) for w in sampled)
            budget = rng.choice((Fraction(0), Fraction(1, 8), Fraction(1, 4), Fraction(1, 2)))
            script = ('parity', 'slot1', 'schedule', 'parity-again', 'slot1-paraphrase')
            result = audit([asdict(w) for w in worlds], guarded(worlds, script, budget), budget)
            self.assertEqual(result['prefix_violation_cells'], 0, (trial, result))
            self.assertEqual(result['invalid_meetings'], 0)


def main():
    start = time.perf_counter()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    test_elapsed = time.perf_counter() - start
    measurements = {'model': '256 uniform joint four-slot calendars; secret=Alice slot0 available',
                    'script': SCRIPT, 'tests_run': result.testsRun,
                    'test_failures': len(result.failures) + len(result.errors),
                    'test_seconds': test_elapsed, 'cases': []}
    for name, script, budget, baseline in [
        ('naive_after_composition', SCRIPT, Fraction(0), True),
        ('strict_after_composition', SCRIPT, Fraction(0), False),
        ('strict_schedule_only', ('schedule',), Fraction(0), False),
        ('budget_1_8_after_composition', SCRIPT, Fraction(1, 8), False),
        ('budget_1_4_after_composition', SCRIPT, Fraction(1, 4), False),
        ('budget_1_2_after_composition', SCRIPT, Fraction(1, 2), False),
    ]:
        t = time.perf_counter()
        traces = naive(WORLD, script) if baseline else guarded(WORLD, script, budget)
        elapsed = time.perf_counter() - t
        metrics = audit(RECORDS, traces, budget)
        metrics.pop('violations')
        measurements['cases'].append({'name': name, 'budget': str(budget),
                                      'all_world_replay_seconds': elapsed, **metrics})
    # An observable example where naive books earliest but guard books later.
    # alice=0111, bob=0101: common slots0 and2, protected slot0 fact true.
    key = 7 * 16 + 5
    measurements['example'] = {'key': key, 'alice_available': [0,1,2],
        'bob_available': [0,2], 'naive': naive(WORLD)[key], 'guarded': guarded(WORLD)[key]}
    with open('measurements.json', 'w') as f:
        json.dump(measurements, f, indent=2)
    print(json.dumps(measurements, indent=2))
    if not result.wasSuccessful():
        raise SystemExit(1)

if __name__ == '__main__':
    main()
