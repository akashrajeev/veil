"""Exhaustive check on the ASSISTANT-FACING MCP surface only.

For every protected window, every request sequence up to LENGTH (6 supported intents + one unsupported),
and every one of Alice's 16 synthetic calendars (Bob fixed at 5), record everything the assistant surface
returns (all tool results incl. spoken/output/suggestions/events and a final veil_status). Calendars that
produce byte-identical visible transcripts are indistinguishable to the room; the protected window must be
free in exactly half of each such group (the declared uniform prior), i.e. the visible channel adds zero
information about it. Usage: python3 mcp_independence_check.py [LENGTH=3]"""
import json,sys,tempfile,itertools,collections,math
from pathlib import Path
import mcp_server as m
Q=['is alice free for early prep','is alice free for late prep','is alice free for dinner','is alice free for cleanup',
   'can alice cover exactly one of the two prep windows','find a shared window','what is her password']
def call(s,name,args,surface='assistant'):
    r=m.handle({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}},s,surface)['result']
    assert not r['isError'],r
    return r
def approvals_check():
    """Pending/declined approval paths must look identical for every calendar (approval itself is never calendar-dependent)."""
    d=Path(tempfile.mkdtemp(dir='/dev/shm' if Path('/dev/shm').exists() else None));bad=0;n=0
    for window in m.SLOTS:
        for q in Q:
            seen=set()
            for alice in range(16):
                s=m.Session(d/'a.json',alice=alice);call(s,'veil_start_household',{'protected_window':window},'operator')
                r1=call(s,'veil_request_approval',{'text':q});aid=r1.get('structuredContent',{}).get('approval_id','no-request')
                v=[r1]
                if q!=Q[-1]:
                    v.append(call(s,'veil_check_approval',{'approval_id':aid}))
                    m.handle({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'veil_decide_approval','arguments':{'approval_id':aid,'approve':False}}},s,'operator')
                    v.append(call(s,'veil_check_approval',{'approval_id':aid}))
                # approval ids are per-household uniqueness randomness, not calendar information - normalize
                seen.add(json.dumps(v,sort_keys=True).replace(aid,'ID'));n+=1
            if len(seen)!=1:bad+=1
    print(json.dumps({'approval_paths_runs':n,'request_window_cells_with_calendar_dependence':bad,'passed':bad==0}));return bad
def composition_check(max_approvals=2):
    """Repeated approvals: the operator's stated inference must equal the room's real posterior.
    For every window, one optional guarded question, and 0-N approved disclosures (then one more direct ask),
    group the 16 calendars by the full assistant-visible transcript and compare each group's protected-window
    fraction and size with the operator view computed for a member. Also the transcript must be identical for
    calendars that agree on every approved answer and on the guarded history's outputs (checked via grouping)."""
    d=Path(tempfile.mkdtemp(dir='/dev/shm' if Path('/dev/shm').exists() else None));bad=n=groups_n=0
    supported=Q[:6]
    pre=[()]+[(q,) for q in Q]
    import itertools as _it
    appr=[()]
    for k in range(1,max_approvals+1):
        appr += [c for c in _it.permutations(supported,k)]
    for p,window in enumerate(m.SLOTS):
        print(f'composition progress: window {p+1}/4 runs_so_far={n}',file=sys.stderr,flush=True)
        for pq in pre:
            for ap in appr:
                groups=collections.defaultdict(list)
                for alice in range(16):
                    s=m.Session(d/'c.json',alice=alice);call(s,'veil_start_household',{'protected_window':window},'operator')
                    vis=[json.dumps(call(s,'veil_ask',{'text':q}),sort_keys=True) for q in pq]
                    ids=[]
                    for a in ap:
                        r1=call(s,'veil_request_approval',{'text':a});aid=r1.get('structuredContent',{}).get('approval_id','no-request');ids.append(aid)
                        vis.append(json.dumps(r1,sort_keys=True))
                        call(s,'veil_decide_approval',{'approval_id':aid,'approve':True},'operator')
                        vis.append(json.dumps(call(s,'veil_check_approval',{'approval_id':aid}),sort_keys=True))
                    for aid in ids:vis=[v.replace(aid,'ID') for v in vis]  # uniqueness randomness, not transcript content
                    vis.append(json.dumps(call(s,'veil_ask',{'text':'find a shared window'}),sort_keys=True))
                    op=call(s,'veil_operator_view',{},'operator')['structuredContent']
                    claim={k:op['after_approved_disclosures'][k] for k in ('possible_calendars','probability_free')} if ap else None
                    groups[tuple(vis)].append(((alice>>p)&1,claim))
                for members in groups.values():
                    groups_n+=1;n+=len(members)
                    if ap:
                        free=sum(b for b,_ in members);claims={json.dumps(c,sort_keys=True) for _,c in members}
                        want=json.dumps({'possible_calendars':len(members),'probability_free':f'{free}/{len(members)}'},sort_keys=True)
                        if claims!={want}:bad+=1
                    elif sum(b for b,_ in members)*2!=len(members):bad+=1
    print(json.dumps({'composition_runs':n,'max_approved_disclosures':max_approvals,'visible_transcript_groups':groups_n,'groups_where_operator_claim_differs_from_room_posterior':bad,'passed':bad==0}));return 1 if bad else 0
def main(length=3):
    if approvals_check():return 1
    d=Path(tempfile.mkdtemp(dir='/dev/shm' if Path('/dev/shm').exists() else None))
    bad=checked=groups_n=0;max_bits=0.0
    for p,window in enumerate(m.SLOTS):
        for n in range(1,length+1):
            for seq in itertools.product(Q,repeat=n):
                groups=collections.defaultdict(list)
                for alice in range(16):
                    s=m.Session(d/'s.json',alice=alice)
                    call(s,'veil_start_household',{'protected_window':window},'operator')
                    visible=[json.dumps(call(s,'veil_ask',{'text':q}),sort_keys=True) for q in seq]
                    visible.append(json.dumps(call(s,'veil_status',{}),sort_keys=True))
                    groups[tuple(visible)].append((alice>>p)&1)
                for bits in groups.values():
                    groups_n+=1;checked+=len(bits)
                    if sum(bits)*2!=len(bits):bad+=1
                    pf=sum(bits)/len(bits);hf=0.0 if pf in (0.0,1.0) else -(pf*math.log2(pf)+(1-pf)*math.log2(1-pf))
                    max_bits=max(max_bits,1-hf)
    print(json.dumps({'length':length,'calendar_runs':checked,'distinct_visible_transcripts':groups_n,'groups_not_half_free':bad,'max_protected_window_information_bits':round(max_bits,6),'passed':bad==0}))
    return 1 if bad else 0
def weighted_composition_check(max_approvals=2, prior=(1, 3)):
    """Weighted composition: with a declared NON-UNIFORM prior, the operator's stated post-approval
    inference must equal the room's WEIGHTED posterior (count-based matching would silently accept a
    weights bug in disclosed mode). Falsification hypothesis: disclosed-mode region math diverges
    under non-uniform weights."""
    d=Path(tempfile.mkdtemp(dir='/dev/shm' if Path('/dev/shm').exists() else None));bad=n=groups_n=0
    supported=Q[:6]
    pre=[()]+[(q,) for q in Q]
    import itertools as _it
    appr=[()]
    for k in range(1,max_approvals+1):
        appr += [c for c in _it.permutations(supported,k)]
    p0=prior[1]/(prior[0]+prior[1])
    for p,window in enumerate(m.SLOTS):
        print(f'weighted-composition progress: window {p+1}/4 runs_so_far={n}',file=sys.stderr,flush=True)
        for pq in pre:
            for ap in appr:
                groups=collections.defaultdict(list)
                for alice in range(16):
                    s=m.Session(d/'wc.json',alice=alice)
                    call(s,'veil_start_household',{'protected_window':window,'prior':list(prior)},'operator')
                    vis=[json.dumps(call(s,'veil_ask',{'text':q}),sort_keys=True) for q in pq]
                    ids=[]
                    for a in ap:
                        r1=call(s,'veil_request_approval',{'text':a});aid=r1.get('structuredContent',{}).get('approval_id','no-request');ids.append(aid)
                        vis.append(json.dumps(r1,sort_keys=True))
                        call(s,'veil_decide_approval',{'approval_id':aid,'approve':True},'operator')
                        vis.append(json.dumps(call(s,'veil_check_approval',{'approval_id':aid}),sort_keys=True))
                    for aid in ids:vis=[v.replace(aid,'ID') for v in vis]
                    vis.append(json.dumps(call(s,'veil_ask',{'text':'find a shared window'}),sort_keys=True))
                    op=call(s,'veil_operator_view',{},'operator')['structuredContent']
                    claim={k:op['after_approved_disclosures'][k] for k in ('possible_calendars','probability_free')} if ap else None
                    groups[tuple(vis)].append((alice,claim))
                for members in groups.values():
                    groups_n+=1;n+=len(members)
                    tot_w=sum(prior[(a>>p)&1] for a,_ in members)
                    free_w=sum(prior[(a>>p)&1] for a,_ in members if (a>>p)&1)
                    if ap:
                        claims={json.dumps(c,sort_keys=True) for _,c in members}
                        want=json.dumps({'possible_calendars':len(members),'probability_free':f'{free_w}/{tot_w}'},sort_keys=True)
                        if claims!={want}:bad+=1
                    elif abs(free_w/tot_w-p0)>1e-12:bad+=1
    print(json.dumps({'weighted_composition_runs':n,'max_approved_disclosures':max_approvals,'prior':list(prior),
                      'visible_transcript_groups':groups_n,'groups_where_operator_claim_differs_from_weighted_room_posterior':bad,'passed':bad==0}))
    return 1 if bad else 0
def weighted_check(length=3, prior=(1, 3)):
    """Declared NON-UNIFORM prior: same-transcript groups must preserve the prior's weighted
    protected-window ratio exactly (the guard preserves the prior, whatever it is), and the
    prior-aware readout must stay at 0 protected-window bits on the assistant surface."""
    d=Path(tempfile.mkdtemp(dir='/dev/shm' if Path('/dev/shm').exists() else None))
    bad=checked=groups_n=0;max_bits=0.0
    p0=prior[1]/(prior[0]+prior[1])
    for p,window in enumerate(m.SLOTS):
        print(f'weighted progress: window {p+1}/4 runs_so_far={checked}',file=sys.stderr,flush=True)
        for n in range(1,length+1):
            for seq in itertools.product(Q,repeat=n):
                groups=collections.defaultdict(list)
                for alice in range(16):
                    s=m.Session(d/'w.json',alice=alice)
                    call(s,'veil_start_household',{'protected_window':window,'prior':list(prior)},'operator')
                    visible=[json.dumps(call(s,'veil_ask',{'text':q}),sort_keys=True) for q in seq]
                    visible.append(json.dumps(call(s,'veil_status',{}),sort_keys=True))
                    groups[tuple(visible)].append(alice)
                for members in groups.values():
                    groups_n+=1;checked+=len(members)
                    w=sum(prior[(a>>p)&1] for a in members);wf=sum(prior[(a>>p)&1] for a in members if (a>>p)&1)
                    if abs(wf/w-p0)>1e-12:bad+=1
                    pf=wf/w;hf=0.0 if pf in (0.0,1.0) else -(pf*math.log2(pf)+(1-pf)*math.log2(1-pf))
                    h0=-(p0*math.log2(p0)+(1-p0)*math.log2(1-p0))
                    max_bits=max(max_bits,round(h0-hf,6))
    print(json.dumps({'length':length,'prior':list(prior),'calendar_runs':checked,'distinct_visible_transcripts':groups_n,
                      'groups_off_prior_ratio':bad,'max_protected_window_information_bits':round(max_bits,6),'passed':bad==0}))
    return 1 if bad else 0
if __name__=='__main__' and len(sys.argv)>1 and sys.argv[1]=='composition':sys.exit(composition_check())
if __name__=='__main__' and len(sys.argv)>1 and sys.argv[1]=='composition3':sys.exit(composition_check(3))
if __name__=='__main__' and len(sys.argv)>1 and sys.argv[1]=='weighted':sys.exit(weighted_check())
if __name__=='__main__' and len(sys.argv)>1 and sys.argv[1]=='weighted-composition':sys.exit(weighted_composition_check())
if __name__=='__main__':sys.exit(main(int(sys.argv[1]) if len(sys.argv)>1 else 3))
