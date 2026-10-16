"""Exhaustive JOINT-distribution check on the ASSISTANT-FACING MCP surface.
For every protected PAIR of windows, every request sequence up to length 3 (6 supported
intents + one unsupported), and every one of Alice's 16 calendars (Bob fixed at 5), record
everything the assistant surface returns. Calendars producing byte-identical visible
transcripts are indistinguishable to the room; each group's JOINT distribution over the 4
protected patterns must equal the declared joint prior exactly (budget 0).
Weighted config repeats lengths<=2 with declared priors [1,3]x[2,1] (product prior)."""
import json, sys, tempfile, itertools, collections
from pathlib import Path
from fractions import Fraction
import mcp_server as m

def weight_of(a, pair, priors):
    """Group distributions are WEIGHT-normalized: each calendar carries its declared
    product-prior weight. Under uniform priors every weight is 1, so the oracle
    reduces to the calendar headcount used before the 2026-10-15 consolidation."""
    w = 1
    for i, slot in enumerate(pair):
        w *= priors[i][(a >> slot) & 1]
    return w

Q = ['is alice free for early prep', 'is alice free for late prep', 'is alice free for dinner', 'is alice free for cleanup',
     'can alice cover exactly one of the two prep windows', 'find a shared window', 'what is her password']
PAIRS = list(itertools.combinations(range(4), 2))

def call(s, name, args, surface='assistant'):
    r = m.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': args}}, s, surface)['result']
    assert not r['isError'], r
    return r

def run(label, priors, max_len):
    d = Path(tempfile.mkdtemp(dir='/dev/shm' if Path('/dev/shm').exists() else None))
    runs = groups_n = bad = 0
    examples = []
    k = 2
    # declared joint prior = product of per-window priors
    ptot = 1
    for pr in priors:
        ptot *= pr[0] + pr[1]
    prior = []
    for p in range(1 << k):
        num = 1
        for i in range(k):
            num *= priors[i][(p >> i) & 1]
        prior.append(Fraction(num, ptot))
    seqs = []
    for n in range(1, max_len + 1):
        seqs += list(itertools.product(Q, repeat=n))
    for pi, pair in enumerate(PAIRS):
        windows = [m.SLOTS[pair[0]], m.SLOTS[pair[1]]]
        print(f'{label} progress: pair {pi+1}/6 {windows} runs_so_far={runs}', file=sys.stderr, flush=True)
        for seq in seqs:
            groups = collections.defaultdict(list)
            for alice in range(16):
                s = m.Session(d/'j.json', alice=alice)
                call(s, 'veil_start_household', {'protected_windows': windows, 'priors': [list(p) for p in priors]}, 'operator')
                vis = [json.dumps(call(s, 'veil_ask', {'text': q}), sort_keys=True) for q in seq]
                vis.append(json.dumps(call(s, 'veil_status', {}), sort_keys=True))
                groups[tuple(vis)].append(alice)
                runs += 1
            for members in groups.values():
                groups_n += 1
                cells = [0] * (1 << k)
                for a in members:
                    secret = ((a >> pair[0]) & 1) | (((a >> pair[1]) & 1) << 1)
                    cells[secret] += weight_of(a, pair, priors)
                tot = sum(cells)
                got = tuple(Fraction(x, tot) for x in cells)
                if got != tuple(prior):
                    bad += 1
                    if len(examples) < 3:
                        examples.append((windows, seq[:2], [str(x) for x in got], [str(x) for x in prior]))
    return {'label': label, 'runs': runs, 'transcript_groups': groups_n,
            'groups_with_joint_deviation': bad, 'examples': examples, 'passed': bad == 0}

if __name__ == '__main__':
    t0 = __import__('time').time()
    r1 = run('uniform_length<=3', ((1, 1), (1, 1)), 3)
    print(json.dumps(r1), flush=True)
    r2 = run('weighted_[1,3]x[2,1]_length<=2_weight-normalized', ((1, 3), (2, 1)), 2)
    print(json.dumps(r2), flush=True)
    print(json.dumps({'elapsed_seconds': round(__import__('time').time() - t0, 1)}))
