import unittest
from engine import Controller,Policy,World,make_worlds
from fractions import Fraction
from dialog import create,ask
class TruthfulQueryTests(unittest.TestCase):
    def test_every_emitted_slot_answer_matches_actual_world(self):
        for slot in range(4):
            p=Policy('availability','availability',(slot,))
            for w in make_worlds():
                self.assertEqual(int(p.output(w).split(':')[1]),(w.alice>>slot)&1)
    def test_weighted_open_dialogue_answers_truthfully(self):
        labels=['early prep','late prep','dinner','cleanup']
        for alice in range(16):
            state=create(alice,15,0,'1/2',prior=(1,3))
            for slot,label in enumerate(labels):
                state,result=ask(state,'is alice free for '+label)
                output=result['observation']['output']
                if output.startswith('ALICE_SLOT'):
                    self.assertEqual(int(output.split(':')[1]),(alice>>slot)&1)
    def test_weighted_prior_bound_never_means_false_answers(self):
        for alice in range(16):
            state=create(alice,15,0,'0',prior=(3,1))
            state,result=ask(state,'early prep availability')
            self.assertEqual(result['observation']['output'],'NEEDS_PRIVATE_DECISION')
            self.assertEqual(result['protected_support'],'1/4')
    def test_independent_observer_catches_false_and_malformed_calendar_replies(self):
        from oracle import audit
        record={'key':0,'alice':5,'bob':15,'secret':1,'weight':1}
        for output in ('ALICE_SLOT0:0','ALICE_SLOT1:1','ALICE_SLOT4:1','ALICE_SLOT0:maybe','PARITY:0','PARITY:2'):
            result=audit([record],{0:[{'request':'test','policy':'test','output':output}]},Fraction(1))
            self.assertEqual(result['invalid_calendar_answers'],1,output)
    def test_independent_observer_accepts_truthful_bits_parity_and_refusal(self):
        from oracle import audit
        for w in make_worlds():
            outputs=['ALICE_SLOT'+str(slot)+':'+str((w.alice>>slot)&1) for slot in range(4)]
            outputs+=['PARITY:'+str(((w.alice>>0)^(w.alice>>1))&1),'NEEDS_PRIVATE_DECISION']
            result=audit([dict(key=w.key,alice=w.alice,bob=w.bob,secret=w.secret,weight=1)],
                         {w.key:[{'request':'test','policy':'test','output':output} for output in outputs]},Fraction(1))
            self.assertEqual(result['invalid_calendar_answers'],0)
    def test_offline_verifier_counts_false_calendar_answer_even_when_bound_safe(self):
        from audit_export import export,verify
        artifact=export()
        for key,events in artifact['traces'].items():
            alice=next(w['alice'] for w in artifact['world_records'] if str(w['key'])==key)
            events[0]['output']='PARITY:'+str(1^(((alice>>0)^(alice>>1))&1))
        self.assertGreater(verify(artifact)['invalid_calendar_answers'],0)
if __name__=='__main__':unittest.main(verbosity=2)
