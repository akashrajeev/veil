"""Find truthful ordinary availability queries that compose under a DECLARED
correlated prior. Discovery tool only, not evidence of a real household prior.
"""
from itertools import combinations
from fractions import Fraction
import json

def support(calendars,secret_slot=0):return Fraction(sum((a>>secret_slot)&1 for a in calendars),len(calendars))
def cells(calendars,slots):
    groups={}
    for a in calendars:groups.setdefault(tuple((a>>s)&1 for s in slots),[]).append(a)
    return groups

def find():
    for size in range(4,9):
        for domain in combinations(range(16),size):
            baseline=support(domain)
            if baseline!=Fraction(1,2):continue
            for first,second in combinations((1,2,3),2):
                if not all(support(c)==baseline for c in cells(domain,(first,)).values()):continue
                if not all(support(c)==baseline for c in cells(domain,(second,)).values()):continue
                if any(support(c)!=baseline for c in cells(domain,(first,second)).values()):
                    return {'declared_alice_calendars':domain,'protected_slot':0,'questions':[first,second],
                            'initial_support':str(baseline),'individual_cells':{
                            str(s):{str(k):str(support(c)) for k,c in cells(domain,(s,)).items()} for s in (first,second)},
                            'joint_cells':{str(k):str(support(c)) for k,c in cells(domain,(first,second)).items()},
                            'scope':'synthetic correlated prior; no evidence this describes real calendars'}
if __name__=='__main__':print(json.dumps(find(),indent=2))
