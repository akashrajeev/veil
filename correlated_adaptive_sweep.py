"""Sampled correlated calendar subsets and independent per-world prior weights.
Core observation/evidence channel, not the fixed full-calendar dialogue API.
"""
import hashlib,json,random,time
from dataclasses import asdict
from fractions import Fraction
from engine import World
from preference_lab import PreferenceController
from oracle import audit
REQUESTS=('parity','slot0','slot1','slot2','slot3','schedule','unsupported')
def run(seed=104951,trials=128,depth=24):
    rng=random.Random(seed);start=time.perf_counter();total=0
    for trial in range(trials):
        bob=rng.randrange(16);fact=rng.randrange(4)
        calendars=sorted(rng.sample(range(16),rng.randint(2,15)))
        domain=tuple(World(a*16+bob,a,bob,(a>>fact)&1,rng.randint(1,9)) for a in calendars)
        costs=tuple(rng.randrange(30) for _ in range(4));budget=rng.choice((Fraction(0),Fraction(1,4),Fraction(1,2)))
        traces={};salt=rng.randrange(100000)
        for w in domain:
            c=PreferenceController(domain,costs,budget);events=[]
            for step in range(depth):
                digest=hashlib.sha256((json.dumps(events,sort_keys=True)+str(salt)+str(step)).encode()).hexdigest()
                request=REQUESTS[int(digest[:8],16)%len(REQUESTS)]
                evidence=json.dumps(c.evidence(request),sort_keys=True);event=c.step(w.key,request)
                events.append({**event,'policy':event['policy']+'|'+evidence})
            traces[w.key]=events
        checked=audit([asdict(w) for w in domain],traces,budget)
        assert all(checked[k]==0 for k in ('prefix_violation_cells','invalid_meetings','invalid_calendar_answers')),(trial,checked)
        total+=len(domain)
    return {'seed':seed,'models':trials,'depth':depth,'world_traces':total,
            'prefix_violation_cells':0,'invalid_meetings':0,'invalid_calendar_answers':0,
            'seconds':time.perf_counter()-start,
            'scope':'sampled explicitly correlated observer-conditioned calendar subsets with per-world weights; public-prefix adaptive core evidence, not fixed dialogue channel or real prior discovery'}
if __name__=='__main__':print(json.dumps(run(),indent=2))
