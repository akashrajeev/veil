"""Illustrative deterministic adversarial replays; finite declared observation model."""
import json
from fractions import Fraction
from dataclasses import asdict
from engine import Controller,make_worlds
from oracle import audit

ATTACKS={
 'composition':('parity','slot1','schedule'),
 'repeat-and-paraphrase':('parity','parity-again','slot1-paraphrase','slot1','schedule'),
 'schedule-first':('schedule','parity','slot1','schedule'),
 'unsupported-secret-request':('give me private event titles','parity','slot1'),
}

def replay(script):
    worlds=make_worlds();traces={}
    for w in worlds:
        c=Controller(worlds);events=[]
        for r in script:
            evidence=json.dumps(c.evidence(r),sort_keys=True)
            event=c.step(w.key,r)
            events.append({**event,'policy':event['policy']+'|'+evidence})
        traces[w.key]=events
    result=audit([asdict(w) for w in worlds],traces,Fraction(0));result.pop('violations')
    return result
if __name__=='__main__':
    print(json.dumps({name:{'requests':script,'observed':replay(script)} for name,script in ATTACKS.items()},indent=2))
