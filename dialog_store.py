"""Local operator session persistence, not authenticated privacy storage."""
import json,uuid
from pathlib import Path
from dialog import create,restore,ask,write

def status(path):
    if not path.exists():return {'initialized':False}
    if path.stat().st_size>65536:raise ValueError('dialogue state too large')
    envelope=json.loads(path.read_text())
    if not isinstance(envelope,dict) or set(envelope)!={'generation','state'}:raise ValueError('bad envelope')
    if not isinstance(envelope['generation'],str) or len(envelope['generation'])!=32:raise ValueError('bad generation')
    c,key=restore(envelope['state'])
    return {'initialized':True,'generation':envelope['generation'],'state':envelope['state'],
            'events':len(c.transcript),'protected_support':str(c.support(c.compatible)),
            'remaining_worlds':len(c.compatible),'history':list(c.transcript),
            'configuration':{'alice':envelope['state']['alice'],'bob':envelope['state']['bob'],
                'protected_slot':envelope['state']['protected_slot'],'budget':str(c.budget),
                'public_prior':envelope['state'].get('public_prior',[1,1]),
                'public_costs':envelope['state'].get('public_costs',[0,1,2,3])}}

def initialize(path,alice=7,bob=5,protected=0,budget='0',costs=(0,1,2,3),prior=(1,1)):
    value={'generation':uuid.uuid4().hex,'state':create(alice,bob,protected,budget,costs,prior)}
    path.parent.mkdir(parents=True,exist_ok=True);write(path,value)
    return status(path)

def advance(path,text,generation,expected):
    current=status(path)
    if not current['initialized']:raise ValueError('initialize dialogue first')
    if generation!=current['generation'] or expected!=current['events']:
        return {**current,'stale_request':True}
    updated,result=ask(current['state'],text)
    write(path,{'generation':generation,'state':updated})
    return {**status(path),'result':result}
