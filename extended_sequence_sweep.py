"""All length-three request orders for a seven-intent resident-conditioned model."""
from itertools import product
from dataclasses import asdict
from fractions import Fraction
import json,time
from engine import Controller,make_worlds
from oracle import audit
REQUESTS=('parity','slot0','slot1','slot2','slot3','schedule','unsupported')
def run(bobs=range(16)):
    # Each sequence independently starts from Bob-known-calendar prior. This
    # extends vocabulary, not long-horizon or all possible-prior completeness.
    start=time.perf_counter();checks=traces_count=0
    for bob in bobs:
        domain=tuple(w for w in make_worlds() if w.bob==bob)
        for script in product(REQUESTS,repeat=3):
            traces={}
            for w in domain:
                c=Controller(domain);events=[]
                for request in script:
                    evidence=json.dumps(c.evidence(request),sort_keys=True);event=c.step(w.key,request)
                    events.append({**event,'policy':event['policy']+'|'+evidence})
                traces[w.key]=events
            observed=audit([asdict(w) for w in domain],traces,Fraction(0))
            assert observed['prefix_violation_cells']==0,(bob,script)
            assert observed['invalid_meetings']==0
            assert observed['invalid_calendar_answers']==0
            checks+=1;traces_count+=len(domain)
    return {'vocabulary':REQUESTS,'depth':3,'request_sequences':343,'resident_classes':len(bobs),
            'class_sequence_checks':checks,'world_traces':traces_count,
            'violation_cells':0,'invalid_meetings':0,'invalid_calendar_answers':0,'elapsed_seconds':time.perf_counter()-start}
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--from-bob',type=int,default=0);parser.add_argument('--to-bob',type=int,default=16);args=parser.parse_args()
    if not 0<=args.from_bob<args.to_bob<=16:parser.error('resident range must satisfy0<=from<to<=16')
    print(json.dumps(run(range(args.from_bob,args.to_bob)),indent=2))
