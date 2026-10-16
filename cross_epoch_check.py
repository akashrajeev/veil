"""Cross-epoch pair check: can a UI reset (fresh ledger, same calendar) let one
observer obtain a pair of answers that the same-session guard would refuse?

For every configuration (single: 4 protected windows x 5 priors; joint: 6 window
pairs x 3 prior combinations) x all 16 calendars:
  F = questions answered on a fresh ledger (fresh-safe).
  For every ordered pair (a1, a2) in F x F, a1 != a2: in ONE session ask a1 then a2.
  A HIT is a2 REFUSED after a1 while both are fresh-safe: exactly the evidence set
  a reload-splitting observer would obtain across two epochs about the same calendar.
Runs in-process against the same MCP handler the HTTP surface uses."""
import json, sys, tempfile, itertools
from pathlib import Path
import mcp_server as m

Q = ['is alice free for early prep', 'is alice free for late prep',
     'is alice free for dinner', 'is alice free for cleanup',
     'can alice cover exactly one of the two prep windows',
     'find a shared window']
PRIORS = [None, [1,2], [1,3], [2,1], [3,1]]
JPRIORS = [([1,1],[1,1]), ([1,3],[2,1]), ([3,1],[1,2])]
D = Path(tempfile.mkdtemp(dir='/dev/shm' if Path('/dev/shm').exists() else None))
_n = [0]

def session(alice):
    _n[0] += 1
    return m.Session(D / f'c{_n[0]}.json', alice=alice)

def call(s, name, args, surface='assistant'):
    r = m.handle({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}}, s, surface)['result']
    assert not r['isError'], r
    return r['structuredContent']

def fresh_session(kind, cfg, cal):
    s = session(cal)
    if kind == 'single':
        args = {'protected_window': cfg['pw']}
        if cfg.get('prior'): args['prior'] = cfg['prior']
    else:
        args = {'protected_windows': list(cfg['pws']), 'priors': [list(p) for p in cfg['priors']]}
    call(s, 'veil_start_household', args, 'operator')
    return s

def answered(s, q):
    out = call(s, 'veil_ask', {'text': q})
    return out.get('output') != 'REFUSED' and out.get('supported_request', True)

configs = []
for pw in m.SLOTS:
    for pr in PRIORS:
        configs.append(('single', {'pw': pw, 'prior': pr}))
for a, b in itertools.combinations(m.SLOTS, 2):
    for p1, p2 in JPRIORS:
        configs.append(('joint', {'pws': (a, b), 'priors': (p1, p2)}))

hits, tested_pairs = [], 0
for ci, (kind, cfg) in enumerate(configs):
    print(f'config {ci+1}/{len(configs)} pairs_so_far={tested_pairs}', file=sys.stderr, flush=True)
    for cal in range(16):
        s = fresh_session(kind, cfg, cal)
        F = [q for q in Q if answered(s, q)]
        for a1, a2 in itertools.permutations(F, 2):
            tested_pairs += 1
            s = fresh_session(kind, cfg, cal)
            assert answered(s, a1), f'a1 not fresh-safe on retry: {a1} {kind} {cfg} cal={cal}'
            if not answered(s, a2):
                hits.append({'kind': kind, 'config': str(cfg), 'calendar': cal, 'a1': a1, 'a2': a2})

result = {'check': 'cross-epoch fresh-safe pair enumeration (in-process MCP handler)',
          'configs': len(configs), 'calendars_per_config': 16,
          'ordered_pairs_tested': tested_pairs, 'hits': hits,
          'verdict': ('PASS - no fresh-safe pair is refused in-session: across the typed '
                      'vocabulary, a UI reset cannot compose a refused pair about the same calendar')
                     if not hits else 'FAIL - cross-epoch pair(s) found'}
print(json.dumps(result, indent=1))
sys.exit(0 if not hits else 1)
