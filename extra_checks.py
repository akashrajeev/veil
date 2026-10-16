import random, json
from fractions import Fraction
from dataclasses import asdict
from engine import World, Controller, make_worlds
from oracle import audit_audiences
from run_spike import guarded

rng = random.Random(923123)
base = make_worlds()
checks = 0
for trial in range(60):
    selected = rng.sample(list(base), rng.randint(16,80))
    worlds = tuple(World(w.key, w.alice, w.bob, rng.randrange(2), rng.randint(1,5))
                   for w in selected)
    budget = rng.choice((Fraction(0), Fraction(1,8), Fraction(1,4)))
    traces = {}
    for w in worlds:
        c = Controller(tuple(x for x in worlds if x.bob == w.bob), budget)
        for request in ('parity','slot1','schedule','slot1-paraphrase'):
            c.step(w.key, request)
        traces[w.key] = c.transcript
    groups = audit_audiences([asdict(w) for w in worlds], traces, budget, 'bob')
    assert all(g['prefix_violation_cells'] == 0 for g in groups)
    assert all(g['invalid_meetings'] == 0 for g in groups)
    assert all(g['invalid_calendar_answers'] == 0 for g in groups)
    checks += len(groups)

# Public-prior-only protection can fail with private side information:
# Bob's slot0 availability correlates with Alice parity; global parity output
# preserves secret marginal, but conditioned on Bob bit reveals secret.
worlds = tuple(World(a*16+b, a, b, a&1)
               for a in range(16) for b in range(16)
               if (b&1) == ((a>>1)&1))
records = [asdict(w) for w in worlds]
global_traces = guarded(worlds, ('parity',))
global_result = audit_audiences(records, global_traces, Fraction(0), 'bob')
assert any(g['prefix_violation_cells'] for g in global_result)
resident_traces = {}
for w in worlds:
    c = Controller(tuple(x for x in worlds if x.bob == w.bob))
    c.step(w.key,'parity')
    resident_traces[w.key] = c.transcript
resident_result = audit_audiences(records, resident_traces, Fraction(0), 'bob')
assert all(g['prefix_violation_cells'] == 0 for g in resident_result)
out = {'weighted_audience_trials':60, 'audience_sequence_checks':checks,
       'violations':0, 'invalid_calendar_answers':0, 'known_calendar_negative_control':{
       'worlds':len(worlds),
       'global_prior_only_violation_cells':sum(g['prefix_violation_cells'] for g in global_result),
       'audience_conditioned_violation_cells':sum(g['prefix_violation_cells'] for g in resident_result)}}
with open('extra-measurements.json','w') as f: json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
