"""Stronger oracle check with Bob's own calendar as initial knowledge.
Adaptive request is a deterministic public function of the observed prefix.
"""
import json, time
from fractions import Fraction
from dataclasses import asdict
from itertools import product
from engine import Controller, World, make_worlds, PARITY, BIT1, Policy
from oracle import audit_audiences
from run_spike import naive, guarded

worlds = make_worlds()
records = [asdict(w) for w in worlds]

def resident_guarded(budget=Fraction(0), adaptive=False):
    traces = {}
    timings = []
    for w in worlds:
        known = tuple(x for x in worlds if x.bob == w.bob)
        c = Controller(known, budget)
        requests = ['parity', 'slot1', 'schedule']
        for i in range(3):
            request = requests[i]
            if adaptive and i == 1:
                request = ('slot1-paraphrase' if c.transcript[-1]['output'] == 'PARITY:0'
                           else 'schedule')
            t = time.perf_counter()
            c.step(w.key, request)
            timings.append((time.perf_counter() - t) * 1000)
        traces[w.key] = c.transcript
    return traces, timings

results = []
for name in ['naive', 'guard_original_prior', 'guard_resident_prior', 'guard_adaptive',
             'guard_half_budget']:
    budget = Fraction(1,2) if name == 'guard_half_budget' else Fraction(0)
    timings = []
    if name == 'naive':
        traces = naive(worlds)
    elif name == 'guard_original_prior':
        traces = guarded(worlds)
    else:
        traces, timings = resident_guarded(budget, name == 'guard_adaptive')
    cells = audit_audiences(records, traces, budget, 'bob')
    violations = sum(x['prefix_violation_cells'] for x in cells)
    if name.startswith('guard'):
        assert violations == 0
        assert all(x['invalid_meetings'] == 0 for x in cells)
        assert all(x['invalid_calendar_answers'] == 0 for x in cells)
    results.append({'name': name, 'completed': sum(x['completed'] for x in cells),
        'audience_groups': len(cells), 'prefix_violation_cells': violations,
        'max_posterior_shift': str(max(Fraction(x['max_posterior_shift']) for x in cells)),
        'invalid_meetings': sum(x['invalid_meetings'] for x in cells),
        'invalid_calendar_answers': sum(x['invalid_calendar_answers'] for x in cells),
        'median_step_ms': sorted(timings)[len(timings)//2] if timings else None,
        'max_step_ms': max(timings) if timings else None})

# Exhaustively replay all 3^4 request sequences in all 256 worlds using Bob's
# known-calendar prior. Schedule, parity, bit1 can be repeated in any order.
checks = 0
traces_count = 0
start = time.perf_counter()
for script in product(('parity', 'slot1', 'schedule'), repeat=4):
    traces = {}
    for w in worlds:
        c = Controller(tuple(x for x in worlds if x.bob == w.bob))
        for request in script:
            c.step(w.key, request)
        traces[w.key] = c.transcript
    groups = audit_audiences(records, traces, Fraction(0), 'bob')
    assert all(x['prefix_violation_cells'] == 0 and x['invalid_meetings'] == 0 and x['invalid_calendar_answers'] == 0
               for x in groups), script
    checks += len(groups)
    traces_count += len(traces)

output = {'audience_results': results, 'exhaustive': {
    'request_sequences': 81, 'steps_per_sequence': 4, 'world_traces': traces_count,
    'audience_sequence_checks': checks, 'violation_cells': 0, 'invalid_calendar_answers':0,
    'elapsed_seconds': time.perf_counter() - start}}
with open('audience-measurements.json','w') as f:
    json.dump(output, f, indent=2)
print(json.dumps(output, indent=2))
