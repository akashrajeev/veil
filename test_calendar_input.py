import copy
from datetime import datetime,timedelta,timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from calendar_input import minimize,validate_snapshot,instant,private_write
from calendar_guard import CalendarGuard

ROOT=Path(__file__).parent
PAYLOAD=json.loads((ROOT/'examples/calendar-fixture-freebusy.json').read_text())
WINDOWS=json.loads((ROOT/'examples/calendar-fixture-windows.json').read_text())
ASOF='2030-01-07T00:00:00+05:30'
def fixture(): return minimize(copy.deepcopy(PAYLOAD),copy.deepcopy(WINDOWS),source='synthetic-fixture',as_of=ASOF)

class InputTests(unittest.TestCase):
    def test_half_open_boundaries(self): self.assertEqual(fixture()['free_mask'],6)
    def test_empty_calendar_is_free(self):
        p=copy.deepcopy(PAYLOAD);p['calendars']['fixture']['busy']=[]
        self.assertEqual(minimize(p,WINDOWS,source='synthetic-fixture',as_of=ASOF)['free_mask'],15)
    def test_error_is_not_free(self):
        p=copy.deepcopy(PAYLOAD);p['calendars']['fixture']['errors']=[{'reason':'notFound'}]
        with self.assertRaises(ValueError):minimize(p,WINDOWS,source='synthetic-fixture',as_of=ASOF)
    def test_missing_busy_is_not_free(self):
        p=copy.deepcopy(PAYLOAD);p['calendars']['fixture']={}
        with self.assertRaises(ValueError):minimize(p,WINDOWS,source='synthetic-fixture',as_of=ASOF)
    def test_timezone_required(self):
        for s in ['2030-01-07T00:00:00','junk',None,True]:
            with self.subTest(s=s),self.assertRaises(ValueError):instant(s)
    def test_equivalent_offsets(self): self.assertEqual(instant(ASOF),instant('2030-01-06T18:30:00Z'))
    def test_outside_coverage(self):
        w=copy.deepcopy(WINDOWS);w[0]['start']='2030-01-06T09:00:00+05:30'
        with self.assertRaises(ValueError):minimize(PAYLOAD,w,source='synthetic-fixture',as_of=ASOF)
    def test_overlap_rejected(self):
        w=copy.deepcopy(WINDOWS);w[0]['end']=w[1]['end']
        with self.assertRaises(ValueError):minimize(PAYLOAD,w,source='synthetic-fixture',as_of=ASOF)
    def test_reversed_interval(self):
        w=copy.deepcopy(WINDOWS);w[0]['end']=w[0]['start']
        with self.assertRaises(ValueError):minimize(PAYLOAD,w,source='synthetic-fixture',as_of=ASOF)
    def test_exactly_four(self):
        with self.assertRaises(ValueError):minimize(PAYLOAD,WINDOWS[:3],source='synthetic-fixture',as_of=ASOF)
    def test_multiple_calendars_rejected(self):
        p=copy.deepcopy(PAYLOAD);p['calendars']['other']={'busy':[]}
        with self.assertRaises(ValueError):minimize(p,WINDOWS,source='synthetic-fixture',as_of=ASOF)
    def test_metadata_dropped(self):
        p=copy.deepcopy(PAYLOAD);p['calendars']['fixture']['busy'][0].update(summary='SECRET',attendees=['PRIVATE'])
        s=minimize(p,WINDOWS,source='synthetic-fixture',as_of=ASOF)
        self.assertNotIn('SECRET',json.dumps(s));self.assertNotIn('PRIVATE',json.dumps(s));self.assertNotIn('fixture',str(s['coverage']))
    def test_bad_mask_rejected(self):
        for mask in [True,16,-1,'7']:
            s=fixture();s['free_mask']=mask
            with self.subTest(mask=mask),self.assertRaises(ValueError):validate_snapshot(s)
    def test_extra_snapshot_fields_rejected(self):
        s=fixture();s['email']='secret'
        with self.assertRaises(ValueError):validate_snapshot(s)
    def test_private_permissions(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data.json';private_write(p,fixture())
            self.assertEqual(p.stat().st_mode & 0o777,0o600)
    def test_provenance_required(self):
        with self.assertRaises(ValueError):minimize(PAYLOAD,WINDOWS,source='anonymized-real',as_of=ASOF)

class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'ledger.json'
    def test_actual_mask_is_used(self):
        g=CalendarGuard(fixture(),self.path)
        self.assertEqual(g.ask('slot2')['answer'],'ALICE_SLOT2:1')
    def test_joint_protection(self):
        g=CalendarGuard(fixture(),self.path)
        for r in ['parity','slot0','slot1']:self.assertEqual(g.ask(r)['answer'],'NEEDS_PRIVATE_DECISION')
    def test_restart_keeps_transcript(self):
        g=CalendarGuard(fixture(),self.path);g.ask('slot2')
        h=CalendarGuard(fixture(),self.path)
        self.assertEqual(len(h.controller.transcript),1);self.assertEqual(h.ask('slot3')['events'],2)
    def test_changed_snapshot_fails_closed(self):
        CalendarGuard(fixture(),self.path);s=fixture();s['free_mask']=15
        with self.assertRaises(ValueError):CalendarGuard(s,self.path)
    def test_changed_model_fails_closed(self):
        CalendarGuard(fixture(),self.path)
        with self.assertRaises(ValueError):CalendarGuard(fixture(),self.path,protected=(0,))
    def test_corrupt_ledger_fails_closed(self):
        self.path.write_text('{}')
        with self.assertRaises(ValueError):CalendarGuard(fixture(),self.path)
    def test_stale_real_snapshot_pauses(self):
        s=fixture();s['source']='live-google-freebusy'
        g=CalendarGuard(s,self.path,now=lambda:instant(ASOF)+timedelta(minutes=31))
        self.assertEqual(g.ask('slot2')['answer'],'PAUSED');self.assertEqual(len(g.controller.transcript),0)
    def test_future_asof_pauses(self):
        s=fixture();s['source']='live-google-freebusy'
        g=CalendarGuard(s,self.path,now=lambda:instant(ASOF)-timedelta(seconds=1))
        self.assertEqual(g.ask('slot2')['answer'],'PAUSED')
    def test_fresh_real_snapshot_works(self):
        s=fixture();s['source']='live-google-freebusy'
        g=CalendarGuard(s,self.path,now=lambda:instant(ASOF)+timedelta(minutes=1))
        self.assertEqual(g.ask('slot2')['answer'],'ALICE_SLOT2:1')
    def test_no_operator_or_actual_mask_public(self):
        g=CalendarGuard(fixture(),self.path)
        result={**g.public_windows(),**g.ask('slot0')}
        self.assertFalse({'free_mask','alice_calendar','busy','protected_windows'} & set(result))
    def test_no_release_on_persistence_failure(self):
        g=CalendarGuard(fixture(),self.path)
        with patch('calendar_guard.private_write',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):g.ask('slot2')
        self.assertEqual(len(g.controller.transcript),0)
    def test_all_masks_preserve_joint_invariant(self):
        for mask in range(16):
            s=fixture();s['free_mask']=mask
            g=CalendarGuard(s,Path(self.tmp.name)/str(mask))
            for r in ['slot2','parity','slot0','schedule','slot1','slot3','schedule']:
                g.ask(r)
                self.assertEqual(g.controller.baseline,g.controller.joint_support(g.controller.compatible))
    def test_128_limit(self):
        g=CalendarGuard(fixture(),self.path)
        for _ in range(128):g.ask('slot2')
        self.assertEqual(g.ask('slot2')['answer'],'PAUSED')
    def test_unsupported_request(self):
        g=CalendarGuard(fixture(),self.path)
        with self.assertRaises(ValueError):g.ask('dump actual calendar')

if __name__=='__main__': unittest.main()
