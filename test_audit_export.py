import json,unittest
from audit_export import export,verify
class AuditExportTests(unittest.TestCase):
    def test_each_resident_initial_knowledge(self):
        for bob in range(16):
            result=verify(export(bob))
            self.assertEqual(result['prefix_violation_cells'],0)
            self.assertEqual(result['invalid_meetings'],0)
    def test_negative_control_observable_evidence_leaks(self):
        artifact=export()
        secrets={str(w['key']):w['secret'] for w in artifact['world_records']}
        for key,events in artifact['traces'].items():events[0]['policy']+='|secret='+str(secrets[key])
        self.assertGreater(verify(artifact)['prefix_violation_cells'],0)
    def test_missing_world_trace_rejected(self):
        artifact=export();artifact['traces'].pop(next(iter(artifact['traces'])))
        with self.assertRaises(ValueError):verify(artifact)
    def test_model_edit_rejected(self):
        artifact=export();artifact['world_records'][0]['secret']^=1
        with self.assertRaises(ValueError):verify(artifact)
    def test_dialogue_download_verifies_through_same_cli(self):
        from dialog import create,ask,audit_dialogue
        state=create()
        for text in ('one prep window','late prep availability'):state,_=ask(state,text)
        self.assertEqual(verify(audit_dialogue(state))['prefix_violation_cells'],0)
        self.assertEqual(verify(audit_dialogue(create()))['prefix_violation_cells'],0)
    def test_malformed_and_unequal_depth_rejected(self):
        for mutate in (lambda a:a['world_records'].clear(),
                       lambda a:a['world_records'].append(a['world_records'][0]),
                       lambda a:a['traces'][next(iter(a['traces']))].pop(),
                       lambda a:a['traces'][next(iter(a['traces']))].append(None),
                       lambda a:a.update(budget='2')):
            artifact=export();mutate(artifact)
            with self.assertRaises(ValueError):verify(artifact)
    def test_negative_prior_weights_rejected(self):
        a=export();a['world_records'][0]['weight']=-1
        with self.assertRaises(ValueError):verify(a)
    def test_dialogue_declared_model_edit_rejected(self):
        from dialog import create,audit_dialogue
        a=audit_dialogue(create());a['world_records'][0]['secret']^=1
        with self.assertRaises(ValueError):verify(a)
    def test_dialogue_budget_metadata_consistency(self):
        from dialog import create,audit_dialogue
        a=audit_dialogue(create());a['public_configuration']['budget']='1/2'
        with self.assertRaises(ValueError):verify(a)
    def test_invalid_public_configuration_metadata_rejected(self):
        from dialog import create,audit_dialogue
        for field,value in (('protected_slot',True),('public_prior',[0,1]),('public_costs',[0,1,2,True])):
            artifact=audit_dialogue(create());artifact['public_configuration'][field]=value
            with self.assertRaises(ValueError):verify(artifact)
    def test_invalid_earlier_meeting_not_hidden_by_valid_final_meeting(self):
        from oracle import audit
        from fractions import Fraction
        records=[{'key':0,'alice':4,'bob':4,'secret':0,'weight':1}]
        trace={0:[{'request':'schedule','policy':'test','output':output}
                  for output in ('MEETING:0','MEETING:2')]}
        result=audit(records,trace,Fraction(0))
        self.assertEqual(result['invalid_meetings'],1)
        self.assertEqual(result['completed'],1)
    def test_malformed_meeting_outputs_count_as_invalid_without_crashing(self):
        from oracle import audit
        from fractions import Fraction
        records=[{'key':0,'alice':15,'bob':15,'secret':0,'weight':1}]
        for output in ('MEETING:-1','MEETING:4','MEETING:abc','MEETING:','MEETING:0:1'):
            trace={0:[{'request':'schedule','policy':'test','output':output}]}
            self.assertEqual(audit(records,trace,Fraction(0))['invalid_meetings'],1)
    def test_dialogue_metadata_must_match_world_fact_and_weights(self):
        from dialog import create,audit_dialogue
        for field,value in (('protected_slot',1),('public_prior',[3,1])):
            artifact=audit_dialogue(create())
            artifact['public_configuration'][field]=value
            with self.assertRaisesRegex(ValueError,'disagree'):verify(artifact)
    def test_required_audit_integrity_fields_cannot_be_omitted(self):
        from dialog import create,audit_dialogue
        for field in ('model_hash','public_configuration'):
            artifact=audit_dialogue(create());del artifact[field]
            with self.assertRaises(ValueError):verify(artifact)
    def test_dialogue_domain_relabel_rejected_even_with_recomputed_hash(self):
        import hashlib
        from dialog import create,audit_dialogue
        artifact=audit_dialogue(create())
        artifact['world_records'][0]['bob']=6
        artifact['model_hash']=hashlib.sha256(json.dumps(artifact['world_records'],sort_keys=True).encode()).hexdigest()
        with self.assertRaisesRegex(ValueError,'complete observer-conditioned'):verify(artifact)
    def test_invalid_rational_budget_rejected_cleanly(self):
        for budget in ('1/0','0/0',True,0.5,'1'*33):
            artifact=export();artifact['budget']=budget
            with self.assertRaises(ValueError):verify(artifact)
    def test_file_roundtrip(self):
        self.assertEqual(verify(export()),verify(json.loads(json.dumps(export()))))
if __name__=='__main__':unittest.main(verbosity=2)
