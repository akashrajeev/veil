"""Exhaustive joint-distribution check for the joint-engine spike.
1) For every protected PAIR, every Alice calendar (Bob fixed 5), every request sequence
   up to length 2 over the 6 supported intents: group the 16 calendars by exact visible
   transcript; each group's joint distribution over the 4 protected patterns must equal
   the declared joint prior exactly (budget 0). Uniform and one weighted product prior.
2) Parity negative control: with protected {0,1}, the XOR question passes BOTH per-bit
   marginal guards (each margin stays at baseline) but the joint guard refuses it.
3) Utility comparison: length-1 answer rate under joint protection vs single-fact."""
import json, itertools, collections, sys
from fractions import Fraction
import engine
from joint_engine import joint_worlds, JointController

REQUESTS = ['slot0', 'slot1', 'slot2', 'slot3', 'parity', 'schedule']
PAIRS = list(itertools.combinations(range(4), 2))
BOB = 5

def visible_key(transcript):
    return json.dumps(transcript, sort_keys=True)

def sweep(priors, label):
    runs = 0
    groups_n = 0
    violations = []
    for pair in PAIRS:
        print(f'sweep {label}: pair {pair}', file=sys.stderr, flush=True)
        for length in (1, 2):
            for seq in itertools.product(REQUESTS, repeat=length):
                groups = collections.defaultdict(list)
                for alice in range(16):
                    domain = joint_worlds(BOB, pair, priors)
                    c = JointController(domain, Fraction(0))
                    key = alice * 16 + BOB
                    vis = []
                    ok = True
                    for req in seq:
                        try:
                            ev = c.step(key, req)
                        except ValueError:
                            ok = False
                            break
                        vis.append(ev)
                    if not ok:
                        continue
                    vis.append(str(c.joint_support(c.compatible)))
                    groups[visible_key(vis)].append(alice)
                    runs += 1
                prior = JointController(joint_worlds(BOB, pair, priors), Fraction(0)).baseline
                for members in groups.values():
                    groups_n += 1
                    domain = joint_worlds(BOB, pair, priors)
                    subset = [w for w in domain if w.alice in members]
                    sup = JointController(domain, Fraction(0)).joint_support(subset)
                    if sup != prior:
                        violations.append((pair, members, str(sup), str(prior)))
    return {'label': label, 'runs': runs, 'transcript_groups': groups_n,
            'joint_violations': len(violations), 'examples': violations[:3]}

def parity_negative_control():
    pair = (0, 1)
    domain = joint_worlds(BOB, pair)
    # marginal guard on bit0 alone
    m0 = engine.Controller([engine.World(w.key, w.alice, w.bob, w.alice & 1, 1) for w in domain], Fraction(0))
    m1 = engine.Controller([engine.World(w.key, w.alice, w.bob, (w.alice >> 1) & 1, 1) for w in domain], Fraction(0))
    joint = JointController(domain, Fraction(0))
    cells = joint.partitions(engine.PARITY)
    cell_supports = {out: str(joint.joint_support(cell)) for out, cell in cells.items()}
    return {'question': 'can alice cover exactly one of the two prep windows (XOR of protected bits)',
            'marginal_guard_bit0_admits': m0.safe(engine.PARITY),
            'marginal_guard_bit1_admits': m1.safe(engine.PARITY),
            'joint_guard_admits': joint.safe(engine.PARITY),
            'joint_distribution_inside_each_parity_answer': cell_supports,
            'baseline_joint': str(joint.baseline)}

def utility_comparison():
    pair = (0, 1)
    out = {}
    for label, domain, ctrl in [
            ('joint_protected_{0,1}', joint_worlds(BOB, pair), 'joint'),
            ('single_protected_{0}', [engine.World(w.key, w.alice, w.bob, w.alice & 1, 1) for w in joint_worlds(BOB, pair)], 'marginal')]:
        answered = set()
        for req in REQUESTS:
            if ctrl == 'joint':
                c = JointController(domain, Fraction(0))
            else:
                c = engine.Controller(domain, Fraction(0))
            pol = c.choose(req)
            if pol.kind not in ('refuse', 'unknown'):
                answered.add(req)
        out[label] = sorted(answered)
    return out

if __name__ == '__main__':
    r1 = sweep(None, 'uniform')
    print(json.dumps(r1))
    r2 = sweep(((1, 3), (2, 1)), 'weighted_product_prior_[1,3]x[2,1]')
    print(json.dumps(r2))
    print(json.dumps(parity_negative_control()))
    print(json.dumps(utility_comparison()))
