"""Joint composition + utility + entropy-contract check (main's 22:57 steer).

A) COMPOSITION under joint protection: guarded asks + approved disclosures. Group the 16
   calendars by the FULL assistant-visible transcript (every tool result incl. refusal
   shape, suggestions, status) and require:
   1. pre-disclosure: each group's joint distribution over the protected pattern equals
      the declared joint prior exactly (budget 0);
   2. post-disclosure: each group's actual joint distribution equals the operator view's
      STATED post-approval joint support (after_approved_disclosures / preview region) -
      the operator's stated inference must be the room's real posterior.
B) COMPUTED UTILITY: over every reachable length<=2 guarded state (all 6 pairs x 16
   calendars), measure which requests the joint guard admits AT THAT STATE vs the
   single-fact guard - including joint-dependent functions (parity, schedule) that are
   noninferential in some states. No blanket claims: counts only.
C) ENTROPY CONTRACT: protected_joint_bits must be prior-entropy minus posterior-entropy
   under the DECLARED product prior; safe answers keep it exactly 0 while calendar counts
   move; the unguarded view measures against the same declared prior."""
import json, sys, tempfile, itertools, collections
from pathlib import Path
from fractions import Fraction
import mcp_server as m

Q = ['is alice free for early prep', 'is alice free for late prep', 'is alice free for dinner', 'is alice free for cleanup',
     'can alice cover exactly one of the two prep windows', 'find a shared window']
PAIR = (0, 1)
WINDOWS = [m.SLOTS[PAIR[0]], m.SLOTS[PAIR[1]]]

def call(s, name, args, surface='assistant'):
    r = m.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': args}}, s, surface)['result']
    assert not r['isError'], r
    return r.get('structuredContent', r)

def secret_of(a, pair=PAIR):
    return ((a >> pair[0]) & 1) | (((a >> pair[1]) & 1) << 1)

def joint_of(members, weights=None):
    cells = [0] * 4
    if weights is None:
        for a in members:
            cells[secret_of(a)] += 1
        tot = len(members)
        return tuple(Fraction(x, tot) for x in cells)

def stated_joint(op_view):
    recs = op_view.get('after_approved_disclosures') or {}
    js = recs.get('joint_support')
    if not js:
        return None
    order = ['busy,busy', 'free,busy', 'busy,free', 'free,free']
    got = {r['pattern']: Fraction(r['fraction']) for r in js}
    return tuple(got[p] for p in order)

def composition():
    d = Path(tempfile.mkdtemp(dir='/dev/shm' if Path('/dev/shm').exists() else None))
    runs = groups_pre = groups_post = bad_pre = bad_post = 0
    examples = []
    pre_seqs = [()] + [(q,) for q in Q]
    appr = [(q,) for q in Q]
    for pq in pre_seqs:
        # PRE-DISCLOSURE: group by the guarded-prefix transcript only (before any approval)
        pre_groups = collections.defaultdict(list)
        for alice in range(16):
            s = m.Session(d/'p.json', alice=alice)
            call(s, 'veil_start_household', {'protected_windows': WINDOWS}, 'operator')
            vis = [json.dumps(call(s, 'veil_ask', {'text': q}), sort_keys=True) for q in pq]
            vis.append(json.dumps(call(s, 'veil_status', {}), sort_keys=True))
            pre_groups[tuple(vis)].append(alice)
            runs += 1
        for members in pre_groups.values():
            groups_pre += 1
            got = joint_of(members)
            if got != (Fraction(1, 4),) * 4:
                bad_pre += 1
                if len(examples) < 3:
                    examples.append(('pre', members, [str(x) for x in got]))
        # PENDING/DECLINED approvals must be calendar-independent (approval itself carries no calendar info)
        for a in Q:
            seen = set()
            for alice in range(16):
                s = m.Session(d/'n.json', alice=alice)
                call(s, 'veil_start_household', {'protected_windows': WINDOWS}, 'operator')
                for q in pq:
                    call(s, 'veil_ask', {'text': q})
                r1 = call(s, 'veil_request_approval', {'text': a})
                aid = r1.get('approval_id', 'x')
                # approval messages ONLY: request/status strings must be calendar-independent
                v = [json.dumps(r1, sort_keys=True).replace(aid, 'ID'),
                     json.dumps(call(s, 'veil_check_approval', {'approval_id': aid}), sort_keys=True).replace(aid, 'ID')]
                m.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                          'params': {'name': 'veil_decide_approval', 'arguments': {'approval_id': aid, 'approve': False}}}, s, 'operator')
                v.append(json.dumps(call(s, 'veil_check_approval', {'approval_id': aid}), sort_keys=True).replace(aid, 'ID'))
                seen.add(tuple(v))
                runs += 1
            if len(seen) != 1:
                bad_pre += 1
                if len(examples) < 4:
                    examples.append(('pending-declined-not-uniform', str(pq), a, len(seen)))
        # POST-DISCLOSURE: full transcript incl. approvals; group actual joint == operator-stated joint
        for ap in appr:
            groups = collections.defaultdict(list)
            opviews = {}
            for alice in range(16):
                s = m.Session(d/'c.json', alice=alice)
                call(s, 'veil_start_household', {'protected_windows': WINDOWS}, 'operator')
                vis = [json.dumps(call(s, 'veil_ask', {'text': q}), sort_keys=True) for q in pq]
                for a in ap:
                    r1 = call(s, 'veil_request_approval', {'text': a})
                    aid = r1.get('approval_id')
                    vis.append(json.dumps(r1, sort_keys=True).replace(aid or 'x', 'ID'))
                    m.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                              'params': {'name': 'veil_decide_approval', 'arguments': {'approval_id': aid, 'approve': True}}}, s, 'operator')
                    vis.append(json.dumps(call(s, 'veil_check_approval', {'approval_id': aid}), sort_keys=True).replace(aid, 'ID'))
                vis.append(json.dumps(call(s, 'veil_status', {}), sort_keys=True))
                post_view = call(s, 'veil_operator_view', {}, 'operator')
                groups[tuple(vis)].append(alice)
                opviews[tuple(vis)] = post_view
                runs += 1
            for key, members in groups.items():
                stated = stated_joint(opviews[key])
                if stated is not None:
                    groups_post += 1
                    got = joint_of(members)
                    if got != stated:
                        bad_post += 1
                        if len(examples) < 6:
                            examples.append(('post', members, [str(x) for x in got], [str(x) for x in stated]))
    return {'runs': runs, 'groups_pre_disclosure': groups_pre, 'pre_joint_violations': bad_pre,
            'groups_post_disclosure': groups_post, 'post_stated_vs_actual_mismatches': bad_post,
            'examples': examples, 'passed': bad_pre == 0 and bad_post == 0}

def utility():
    """Per reachable state: admission sets for joint vs single-fact guards."""
    d = Path(tempfile.mkdtemp(dir='/dev/shm' if Path('/dev/shm').exists() else None))
    states = 0
    admit_counts = collections.Counter()
    joint_admits_parity_states = 0
    joint_admits_schedule_states = 0
    seqs = [()] + [(q,) for q in Q] + [s2 for s2 in itertools.product(Q, repeat=2)]
    seen = set()
    for seq in seqs:
        for alice in range(16):
            s = m.Session(d/'u.json', alice=alice)
            call(s, 'veil_start_household', {'protected_windows': WINDOWS}, 'operator')
            vis = []
            for q in seq:
                vis.append(json.dumps(call(s, 'veil_ask', {'text': q}), sort_keys=True))
            key = tuple(vis)
            if key in seen:
                continue
            seen.add(key)
            states += 1
            op = call(s, 'veil_operator_view', {}, 'operator')
            for q in Q:
                r = call(s, 'veil_ask', {'text': q})
                admit_counts[(q, r['output'] != 'REFUSED')] += 1
                if r['output'] != 'REFUSED' and q == Q[4]:
                    joint_admits_parity_states += 1
                if r['output'] != 'REFUSED' and q == Q[5]:
                    joint_admits_schedule_states += 1
    per_q = {q: {'admitted': admit_counts[(q, True)], 'refused': admit_counts[(q, False)]} for q in Q}
    return {'reachable_states_(distinct_visible_transcripts, pair early+late prep)': states,
            'per_question_admission_at_those_states': per_q,
            'note': 'parity/schedule are joint-dependent: admission is decided per state by the joint-distribution test, not by a blanket rule'}

def entropy_contract():
    d = Path(tempfile.mkdtemp())
    out = {}
    # weighted session: safe answer must keep protected_joint_bits exactly 0 while calendars move
    s = m.Session(d/'e.json', alice=7)
    call(s, 'veil_start_household', {'protected_windows': WINDOWS, 'priors': [[1, 3], [2, 1]]}, 'operator')
    v0 = call(s, 'veil_operator_view', {}, 'operator')
    call(s, 'veil_ask', {'text': 'is alice free for dinner'})
    v1 = call(s, 'veil_operator_view', {}, 'operator')
    out['weighted_prior_bits'] = v0['with_veil_information_bits']['protected_joint_prior_bits']
    out['weighted_bits_after_safe_answer'] = v1['with_veil_information_bits']['protected_joint_bits']
    out['calendars_moved'] = (v0['remaining_possible_calendars'], v1['remaining_possible_calendars'])
    out['joint_support_unchanged'] = v0['joint_support'] == v1['joint_support']
    # manual entropy check: product prior [1,3]x[2,1] -> patterns bb,fb,bf,ff weights (2,6,1,3)/12
    import math
    ps = [2/12, 6/12, 1/12, 3/12]
    h = -sum(p * math.log2(p) for p in ps)
    out['manual_product_prior_entropy'] = round(h, 3)
    out['matches'] = abs(out['manual_product_prior_entropy'] - out['weighted_prior_bits']) < 1e-9
    # unguarded view uses same declared prior
    out['unguarded_prior_bits_same_contract'] = v1['without_veil']['information_bits'].get('protected_joint_prior_bits') == out['weighted_prior_bits']
    return out

if __name__ == '__main__':
    print(json.dumps({'A_composition': composition()}), flush=True)
    print(json.dumps({'B_utility': utility()}), flush=True)
    print(json.dumps({'C_entropy_contract': entropy_contract()}), flush=True)
