"""Seeded invalid JSON-shape mutations, not security certification."""
import random,json
from test_experiment_spec import SpecTests
from experiment_spec import run

def sweep(seed=90241,count=500):
    rng=random.Random(seed);rejected=0
    bad=(None,True,False,[],{},'',-1,10**8,'not-json')
    for i in range(count):
        spec=SpecTests().spec()
        target=rng.choice(('root','world','requests','actual_key','budget','public_costs'))
        value=rng.choice(bad)
        if target=='root':spec=value
        elif target=='world':spec['worlds'][rng.randrange(len(spec['worlds']))]=value
        elif target=='requests':spec['requests']=[value]
        elif target=='actual_key':spec['actual_key']=value
        elif target=='budget':spec['budget']=value
        else:spec['public_costs']=value
        try:run(spec)
        except (ValueError,TypeError):rejected+=1
        else:raise AssertionError(('invalid mutation accepted',i,target,value))
    return {'seed':seed,'mutations':count,'rejected':rejected,'scope':'sampled malformed synthetic model inputs, not penetration audit'}
if __name__=='__main__':print(json.dumps(sweep(),indent=2))
