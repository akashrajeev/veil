"""Seeded adaptive public request policy; requests depend only on visible prefix."""
import random,json,time,hashlib
from dataclasses import asdict
from fractions import Fraction
from engine import World,make_worlds
from preference_lab import PreferenceController
from oracle import audit

REQUESTS=('parity','slot0','slot1','slot2','slot3','schedule','unsupported')
def run(seed=7781,trials=64,depth=8):
    rng=random.Random(seed);total=0;start=time.perf_counter()
    for trial in range(trials):
        bob=rng.randrange(16);protected=rng.randrange(4);prior=(rng.randint(1,9),rng.randint(1,9))
        costs=tuple(rng.randrange(20) for _ in range(4));budget=rng.choice((Fraction(0),Fraction(1,4),Fraction(1,2)))
        worlds=tuple(World(w.key,w.alice,w.bob,(w.alice>>protected)&1,prior[(w.alice>>protected)&1]) for w in make_worlds() if w.bob==bob)
        salt=rng.randrange(100000);traces={}
        for w in worlds:
            c=PreferenceController(worlds,costs,budget);events=[]
            for step in range(depth):
                # Hash only the PUBLIC accumulated observation, never actual world.
                public=json.dumps(events,sort_keys=True)+'|'+str(salt)+'|'+str(step)
                digest=int(hashlib.sha256(public.encode()).hexdigest()[:8],16)
                request=REQUESTS[digest%len(REQUESTS)]
                evidence=json.dumps(c.evidence(request),sort_keys=True);event=c.step(w.key,request)
                events.append({**event,'policy':event['policy']+'|'+evidence})
            traces[w.key]=events
        result=audit([asdict(w) for w in worlds],traces,budget)
        assert result['prefix_violation_cells']==0,(trial,result)
        assert result['invalid_meetings']==0
        assert result['invalid_calendar_answers']==0
        total+=len(worlds)
    return {'seed':seed,'trials':trials,'depth':depth,'world_traces':total,
            'violation_cells':0,'invalid_meetings':0,'invalid_calendar_answers':0,'seconds':time.perf_counter()-start,
            'scope':'finite sampled resident-prior models; publicly adaptive requests, not arbitrary adversaries'}
if __name__=='__main__':print(json.dumps(run(),indent=2))
