"""Sampled weighted adaptive dialogue including every returned result field.
Public requests depend on visible results only, never actual calendar bits.
Operator-only stored state/configuration is not a protected recipient channel.
"""
import hashlib,json,random,time
from dataclasses import asdict
from fractions import Fraction
from dialog import create,ask,worlds
from oracle import audit
REQUESTS=('one prep window','early prep availability','late prep availability','dinner availability','cleanup availability','find a time for us','unsupported command')
def run(seed=102723,trials=32,depth=16):
    rng=random.Random(seed);start=time.perf_counter();total=0
    for trial in range(trials):
        bob=rng.randrange(16);protected=rng.randrange(4);prior=(rng.randint(1,9),rng.randint(1,9))
        costs=tuple(rng.randrange(30) for _ in range(4));budget=rng.choice(('0','1/4','1/2'));salt=rng.randrange(100000)
        domain=worlds(bob,protected,prior);traces={}
        for w in domain:
            state=create(w.alice,bob,protected,budget,costs,prior);events=[]
            for step in range(depth):
                public=json.dumps(events,sort_keys=True)+'|'+str(salt)+'|'+str(step)
                index=int(hashlib.sha256(public.encode()).hexdigest()[:8],16)%len(REQUESTS)
                text=REQUESTS[index]
                state,result=ask(json.loads(json.dumps(state)),text)
                event=result['observation']
                events.append({'request':text,'policy':'full-dialogue-result|'+json.dumps(result,sort_keys=True),'output':event['output']})
            traces[w.key]=events
        checked=audit([asdict(w) for w in domain],traces,Fraction(budget))
        assert checked['prefix_violation_cells']==0,(trial,checked)
        assert checked['invalid_meetings']==0
        assert checked['invalid_calendar_answers']==0
        total+=len(domain)
    return {'seed':seed,'trials':trials,'depth':depth,'world_traces':total,
            'prefix_violation_cells':0,'invalid_meetings':0,'invalid_calendar_answers':0,
            'seconds':time.perf_counter()-start,
            'scope':'sampled declared weighted one-observer/one-fact sessions, full result fields and public-prefix adaptive requests; no arbitrary adversary proof'}
if __name__=='__main__':print(json.dumps(run(),indent=2))
