import unittest
from engine import Controller,make_worlds,Policy
class CacheTests(unittest.TestCase):
    def test_matches_uncached_outputs_across_steps(self):
        class Uncached(Controller):
            def partitions(self,p):
                cells={}
                for w in self.compatible:cells.setdefault(p.output(w),[]).append(w)
                return cells
        for bob in range(16):
            domain=tuple(w for w in make_worlds() if w.bob==bob)
            for w in domain:
                a=Controller(domain);b=Uncached(domain)
                for request in ('parity','slot0','slot1','slot2','slot3','schedule'):
                    self.assertEqual(a.evidence(request),b.evidence(request))
                    self.assertEqual(a.step(w.key,request),b.step(w.key,request))
    def test_cache_bounded(self):
        c=Controller(make_worlds())
        for i in range(300):c.partitions(Policy('variant'+str(i),'refuse'))
        self.assertLessEqual(len(c._partition_cache),256)
    def test_external_mapping_edit_cannot_poison_cache(self):
        c=Controller(make_worlds());p=Policy('x','bit1');cells=c.partitions(p);cells.clear()
        self.assertEqual(sum(map(len,c.partitions(p).values())),256)
    def test_compatible_class_is_cache_key(self):
        c=Controller(make_worlds());before=c.partitions(Policy('one','bit1'))
        c.step(117,'parity');after=c.partitions(Policy('one','bit1'))
        self.assertEqual(sum(map(len,before.values())),256)
        self.assertEqual(sum(map(len,after.values())),128)
if __name__=='__main__':unittest.main(verbosity=2)
