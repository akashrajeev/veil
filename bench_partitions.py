import time,json
from engine import Controller,make_worlds
class Uncached(Controller):
    def partitions(self,p):
        cells={}
        for w in self.compatible:cells.setdefault(p.output(w),[]).append(w)
        return cells

def measure(cls,repetitions=200):
    domain=tuple(w for w in make_worlds() if w.bob==5);c=cls(domain)
    start=time.perf_counter()
    outputs=[c.evidence('schedule') for _ in range(repetitions)]
    return time.perf_counter()-start,outputs
if __name__=='__main__':
    cached,a=measure(Controller);uncached,b=measure(Uncached);assert a==b
    print(json.dumps({'repetitions':200,'world_class':16,'cached_seconds':cached,
                     'uncached_seconds':uncached,'speedup':uncached/cached,
                     'exact_evidence_match':True,'scope':'one local microbenchmark, not production SLA'},indent=2))
