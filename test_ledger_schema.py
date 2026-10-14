import json,unittest
from engine import Controller,make_worlds

class LedgerSchema(unittest.TestCase):
    def test_wrong_root_schema(self):
        for value in (None,[],{}, {'budget':'0','complete':True,'transcript':[],'extra':1}):
            with self.assertRaises(ValueError):Controller.load(make_worlds(),json.dumps(value))
    def test_wrong_event_schema(self):
        c=Controller(make_worlds());c.step(117,'parity');base=json.loads(c.dump())
        for event in (None,[],{}, {'request':'parity','policy':'calendar-parity-0-1','output':'PARITY:0','extra':1},
                      {'request':1,'policy':'x','output':'x'}):
            data={**base,'transcript':[event]}
            with self.assertRaises(ValueError):Controller.load(make_worlds(),json.dumps(data))
    def test_saved_limits(self):
        with self.assertRaises(ValueError):Controller.load(make_worlds(),' '*65537)
        for field,value in [('transcript',[{}]*129),('budget','1'*65),('budget',0)]:
            data=json.loads(Controller(make_worlds()).dump());data[field]=value
            with self.assertRaises(ValueError):Controller.load(make_worlds(),json.dumps(data))
    def test_zero_denominator_budget_raises_value_error(self):
        for value in ('1/0','0/0'):
            with self.assertRaises(ValueError):Controller(make_worlds(),value)
            data=json.loads(Controller(make_worlds()).dump());data['budget']=value
            with self.assertRaises(ValueError):Controller.load(make_worlds(),json.dumps(data))
    def test_restored_events_copied(self):
        c=Controller(make_worlds());c.step(117,'parity');r=Controller.load(make_worlds(),c.dump())
        self.assertEqual(c.dump(),r.dump());self.assertIsNot(c.transcript[0],r.transcript[0])
if __name__=='__main__':unittest.main(verbosity=2)
