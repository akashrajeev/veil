import json,tempfile,threading,unittest,urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
import mcp_server

def rq(i,m,p=None):
    d={'jsonrpc':'2.0','id':i,'method':m}
    if p is not None:d['params']=p
    return d

class McpProtocol(unittest.TestCase):
    def setUp(self):self.s=mcp_server.Session(Path(tempfile.mkdtemp())/'s.json')
    def test_initialize_negotiates_spec_version(self):
        r=mcp_server.handle(rq(1,'initialize',{'protocolVersion':'2025-11-25'}),self.s)['result']
        self.assertEqual(r['protocolVersion'],'2025-11-25');self.assertIn('tools',r['capabilities'])
        r=mcp_server.handle(rq(1,'initialize',{'protocolVersion':'1999-01-01'}),self.s)['result']
        self.assertEqual(r['protocolVersion'],'2025-11-25')
    def test_notification_has_no_response(self):
        self.assertIsNone(mcp_server.handle({'jsonrpc':'2.0','method':'notifications/initialized'},self.s))
    def test_tools_list_schemas_and_surface_separation(self):
        tools=mcp_server.handle(rq(2,'tools/list'),self.s)['result']['tools']
        self.assertEqual({t['name'] for t in tools},{'veil_ask','veil_status','veil_request_approval','veil_check_approval'})
        ops=mcp_server.handle(rq(2,'tools/list'),self.s,'operator')['result']['tools']
        self.assertEqual({t['name'] for t in ops},{'veil_start_household','veil_ask','veil_status','veil_operator_view','veil_request_approval','veil_check_approval','veil_decide_approval'})
        for t in tools+ops:self.assertEqual(t['inputSchema']['type'],'object')
        for n in ('veil_operator_view','veil_start_household','veil_decide_approval'):
            r=mcp_server.handle(rq(3,'tools/call',{'name':n,'arguments':{}}),self.s)
            self.assertEqual(r['error']['code'],-32602)
    def test_unknown_method_and_tool(self):
        self.assertEqual(mcp_server.handle(rq(3,'nope'),self.s)['error']['code'],-32601)
        self.assertEqual(mcp_server.handle(rq(4,'tools/call',{'name':'x'}),self.s)['error']['code'],-32602)
        self.assertEqual(mcp_server.handle({'id':1},self.s)['error']['code'],-32600)
    def test_bad_arguments_are_tool_errors(self):
        r=mcp_server.handle(rq(5,'tools/call',{'name':'veil_ask','arguments':{}}),self.s)['result']
        self.assertTrue(r['isError'])
        r=mcp_server.handle(rq(6,'tools/call',{'name':'veil_start_household','arguments':{'protected_window':'noon'}}),self.s,'operator')['result']
        self.assertTrue(r['isError'])
    def call(self,t):
        return mcp_server.handle(rq(9,'tools/call',{'name':'veil_ask','arguments':{'text':t}}),self.s)['result']
    def test_guard_holds_probability_across_a_conversation(self):
        mcp_server.handle(rq(1,'tools/call',{'name':'veil_start_household','arguments':{'protected_window':'early prep'}}),self.s,'operator')
        first=self.call('is alice free for early prep')
        self.assertEqual(first['structuredContent']['output'],'REFUSED')
        for t in ['is alice free for late prep','find a shared window','is alice free for dinner']:
            r=self.call(t);self.assertFalse(r['isError'])
            op=mcp_server.handle(rq(1,'tools/call',{'name':'veil_operator_view','arguments':{}}),self.s,'operator')['result']['structuredContent']
            self.assertEqual(op['observer_probability_protected_window_free'],'1/2')
            self.assertEqual(op['with_veil_information_bits']['protected_window_bits'],0.0)
    def test_assistant_facing_results_do_not_leak_unguarded_view(self):
        self.call('is alice free for early prep');r=self.call('is alice free for late prep')
        self.assertEqual(set(r['structuredContent']),{'scope','events','spoken','output','supported_request'})
        st=mcp_server.handle(rq(1,'tools/call',{'name':'veil_status','arguments':{}}),self.s)['result']['structuredContent']
        self.assertEqual(set(st),{'scope','events'})
        op=mcp_server.handle(rq(1,'tools/call',{'name':'veil_operator_view','arguments':{}}),self.s,'operator')['result']['structuredContent']
        self.assertEqual(op['without_veil']['probability_free'].split('/')[0],op['without_veil']['probability_free'].split('/')[1])
    def test_unguarded_counterfactual_matches_independent_bruteforce(self):
        reqs=['slot0','slot1','schedule']
        for t in ['is alice free for early prep','is alice free for late prep','find a shared window']:self.call(t)
        op=mcp_server.handle(rq(1,'tools/call',{'name':'veil_operator_view','arguments':{}}),self.s,'operator')['result']['structuredContent']['without_veil']
        def ans(r,a,b=5):
            if r=='slot0':return a&1
            if r=='slot1':return (a>>1)&1
            return next((k for k in range(4) if ((a&b)>>k)&1),None)
        alive=[a for a in range(16) if all(ans(r,a)==ans(r,7) for r in reqs)]
        self.assertEqual(op['possible_calendars'],len(alive))
        self.assertEqual(op['probability_free'],f"{sum(a&1 for a in alive)}/{len(alive)}")
        import math
        f=sum(a&1 for a in alive);n=len(alive);p=f/n
        h=0.0 if p in (0.0,1.0) else -(p*math.log2(p)+(1-p)*math.log2(1-p))
        self.assertEqual(op['information_bits'],{'protected_window_bits':round(1-h,3),'calendar_bits':round(4-math.log2(n),3),'protected_window_prior_bits':1.0,'calendar_prior_bits':4.0})
    def op(self,name,args):
        return mcp_server.handle(rq(1,'tools/call',{'name':name,'arguments':args}),self.s,'operator')['result']
    def asst(self,name,args):
        return mcp_server.handle(rq(1,'tools/call',{'name':name,'arguments':args}),self.s)['result']
    def test_approval_lifecycle_and_limits(self):
        self.op('veil_start_household',{'protected_window':'early prep'})
        r=self.asst('veil_request_approval',{'text':'is alice free for early prep'})['structuredContent']
        self.assertEqual(r['status'],'pending');self.assertNotIn('Alice is',r['spoken'])
        aid=r['approval_id']
        self.assertEqual(self.asst('veil_check_approval',{'approval_id':aid})['structuredContent']['status'],'pending')
        self.assertTrue(self.asst('veil_check_approval',{'approval_id':'no-such-id'})['isError'])
        self.assertTrue(self.asst('veil_request_approval',{'text':'what is her password'})['structuredContent']['supported_request'] is False)
        self.assertTrue(self.op('veil_decide_approval',{'approval_id':aid,'approve':'yes'})['isError'])
        self.op('veil_decide_approval',{'approval_id':aid,'approve':False})
        c=self.asst('veil_check_approval',{'approval_id':aid})['structuredContent'];self.assertEqual(c['spoken'],'Alice declined.')
        self.assertTrue(self.op('veil_decide_approval',{'approval_id':aid,'approve':True})['isError'])
        self.assertFalse(self.asst('veil_ask',{'text':'is alice free for late prep'})['isError'])
        self.assertTrue(self.asst('veil_ask',{'text':'is alice free for late prep'})['structuredContent']['spoken'].startswith('Alice is'))
    def test_approved_disclosure_preview_matches_bruteforce_and_pauses_direct_answers(self):
        self.op('veil_start_household',{'protected_window':'early prep'})
        self.call('is alice free for late prep')
        aid=self.asst('veil_request_approval',{'text':'is alice free for early prep'})['structuredContent']['approval_id']
        pv=self.op('veil_operator_view',{})['structuredContent']['pending_previews'][0]['if_approved']
        self.assertEqual({k:pv[k] for k in('possible_calendars','probability_free')},{'possible_calendars':4,'probability_free':'4/4'});self.assertEqual(len(pv['alive_calendars']),4)
        self.assertEqual(pv['information_bits'],{'protected_window_bits':1.0,'calendar_bits':2.0,'protected_window_prior_bits':1.0,'calendar_prior_bits':4.0})
        self.op('veil_decide_approval',{'approval_id':aid,'approve':True})
        self.assertEqual(self.asst('veil_check_approval',{'approval_id':aid})['structuredContent']['spoken'],'Alice agreed: she is free for early prep.')
        ad=self.op('veil_operator_view',{})['structuredContent']['after_approved_disclosures'];self.assertEqual({k:ad[k] for k in('possible_calendars','probability_free')},{'possible_calendars':4,'probability_free':'4/4'})
        self.assertEqual(ad['information_bits'],{'protected_window_bits':1.0,'calendar_bits':2.0,'protected_window_prior_bits':1.0,'calendar_prior_bits':4.0})
        r=self.call('find a shared window')['structuredContent']
        self.assertEqual(r['output'],'REFUSED');self.assertIn('approval',r['spoken'])
    def test_unapproved_paths_are_calendar_independent(self):
        outs=set()
        for alice in range(16):
            s=mcp_server.Session(Path(tempfile.mkdtemp())/'z.json',alice=alice);s.start('dinner')
            aid=s.request_approval('is alice free for dinner')['approval_id']
            v=[s.check_approval(aid)]
            s.decide(aid,False);v.append(s.check_approval(aid))
            # the id is per-household uniqueness randomness, not calendar information - normalize it out
            outs.add(json.dumps(v,sort_keys=True).replace(str(aid),'ID'))
        self.assertEqual(len(outs),1)
    def test_pending_request_goes_stale_when_conversation_advances(self):
        self.op('veil_start_household',{'protected_window':'early prep'})
        self.call('is alice free for late prep')
        r=self.asst('veil_request_approval',{'text':'is alice free for dinner'})['structuredContent']
        self.assertEqual(r['status'],'pending');aid=r['approval_id']
        self.call('is alice free for early prep')
        c=self.asst('veil_check_approval',{'approval_id':aid})['structuredContent']
        self.assertEqual(c['status'],'stale');self.assertIn('stale',c['spoken'])
        self.assertTrue(self.op('veil_decide_approval',{'approval_id':aid,'approve':True})['isError'])
    def test_pending_request_goes_stale_after_another_approval(self):
        self.op('veil_start_household',{'protected_window':'early prep'})
        a1=self.asst('veil_request_approval',{'text':'is alice free for dinner'})['structuredContent']['approval_id']
        self.op('veil_decide_approval',{'approval_id':a1,'approve':True})
        a2=self.asst('veil_request_approval',{'text':'is alice free for late prep'})['structuredContent']['approval_id']
        a3=self.asst('veil_request_approval',{'text':'is alice free for early prep'})['structuredContent']['approval_id']
        self.assertEqual(len({a1,a2,a3}),3)
        self.op('veil_decide_approval',{'approval_id':a2,'approve':True})
        c=self.asst('veil_check_approval',{'approval_id':a3})['structuredContent']
        self.assertEqual(c['status'],'stale')
        self.assertTrue(self.op('veil_decide_approval',{'approval_id':a3,'approve':True})['isError'])
    def test_request_decided_on_unchanged_conversation_is_not_stale(self):
        self.op('veil_start_household',{'protected_window':'early prep'})
        aid=self.asst('veil_request_approval',{'text':'is alice free for dinner'})['structuredContent']['approval_id']
        self.assertEqual(self.asst('veil_check_approval',{'approval_id':aid})['structuredContent']['status'],'pending')
        self.assertEqual(self.op('veil_decide_approval',{'approval_id':aid,'approve':True})['structuredContent']['status'],'approved')
        self.assertEqual(self.asst('veil_check_approval',{'approval_id':aid})['structuredContent']['status'],'approved')
    def test_stale_request_discloses_nothing_and_guard_continues(self):
        self.op('veil_start_household',{'protected_window':'early prep'})
        self.call('is alice free for late prep')
        self.asst('veil_request_approval',{'text':'is alice free for dinner'})
        self.call('is alice free for early prep')
        self.asst('veil_check_approval',{'approval_id':self.op('veil_operator_view',{})['structuredContent']['approvals'][0]['approval_id']})
        op=self.op('veil_operator_view',{})['structuredContent']
        self.assertEqual(op['approvals'][0]['status'],'stale')
        self.assertEqual(op['observer_probability_protected_window_free'],'1/2')
        self.assertEqual(op['with_veil_information_bits']['protected_window_bits'],0.0)
    def test_reset_clears_requests_and_old_ids_cannot_alias_new_ones(self):
        self.op('veil_start_household',{'protected_window':'early prep'})
        old_id=self.asst('veil_request_approval',{'text':'is alice free for dinner'})['structuredContent']['approval_id']
        self.op('veil_start_household',{'protected_window':'early prep'})
        new_id=self.asst('veil_request_approval',{'text':'is alice free for dinner'})['structuredContent']['approval_id']
        self.assertNotEqual(old_id,new_id)
        self.assertTrue(self.asst('veil_check_approval',{'approval_id':old_id})['isError'])
        self.assertTrue(self.op('veil_decide_approval',{'approval_id':old_id,'approve':True})['isError'])
        self.assertEqual(self.asst('veil_check_approval',{'approval_id':new_id})['structuredContent']['status'],'pending')
        self.assertEqual(self.op('veil_decide_approval',{'approval_id':new_id,'approve':True})['structuredContent']['status'],'approved')
    def test_reconnect_new_session_has_no_memory_of_old_requests(self):
        self.op('veil_start_household',{'protected_window':'early prep'})
        self.asst('veil_request_approval',{'text':'is alice free for dinner'})
        aid=self.op('veil_operator_view',{})['structuredContent']['approvals'][0]['approval_id']
        fresh=mcp_server.Session(Path(tempfile.mkdtemp())/'s2.json')
        r=mcp_server.handle(rq(2,'tools/call',{'name':'veil_check_approval','arguments':{'approval_id':aid}}),fresh)['result']
        self.assertTrue(r['isError'])
    def test_start_household_accepts_a_scenario_calendar(self):
        r=self.op('veil_start_household',{'protected_window':'dinner','alice_calendar':5})
        sc=r['structuredContent'];self.assertEqual(sc['alice_calendar'],5)
        self.assertEqual(self.call('is alice free for dinner')['structuredContent']['output'],'REFUSED')
        op=self.op('veil_operator_view',{})['structuredContent']
        self.assertEqual(op['alice_calendar'],5)
        reqs=['slot2']
        def ans(r,a,b=5):
            if r=='slot2':return (a>>2)&1
        alive=[a for a in range(16) if ans('slot2',a)==ans('slot2',5)]
        wv=op['without_veil']
        self.assertEqual(wv['possible_calendars'],len(alive))
        self.assertEqual(wv['probability_free'],f"{sum((a>>2)&1 for a in alive)}/{len(alive)}")
    def test_declared_nonuniform_prior_flows_through(self):
        r=self.op('veil_start_household',{'protected_window':'dinner','alice_calendar':5,'prior':[1,3]})
        sc=r['structuredContent']
        self.assertEqual(sc['observer_probability_protected_window_free'],'3/4')
        wb=sc['with_veil_information_bits']
        self.assertEqual(wb['protected_window_bits'],0.0)
        self.assertEqual(wb['protected_window_prior_bits'],0.811)
        self.assertEqual(wb['calendar_prior_bits'],3.811)
        nb=sc['without_veil']['information_bits']
        self.assertEqual(nb['protected_window_prior_bits'],0.811)
        self.assertEqual(sc['prior'],[1,3])
        r=self.op('veil_start_household',{'prior':[9,9]})
        self.assertFalse(r['isError']);self.assertEqual(r['structuredContent']['observer_probability_protected_window_free'],'1/2')
        for bad in ([0,3],[1,10],[-1,3],[1],[1,2,3],[1,'3'],[1,True],[1.5,3],'13',None,True,False,{}):
            self.assertTrue(self.op('veil_start_household',{'prior':bad})['isError'],bad)
    def test_start_household_rejects_bad_calendar_and_defaults_to_seven(self):
        for bad in (16,-1,'x',7.5,True,False,None):
            self.assertTrue(self.op('veil_start_household',{'alice_calendar':bad})['isError'])
        r=mcp_server.handle(rq(3,'tools/call',{'name':'veil_start_household','arguments':{'alice_calendar':5}}),self.s)
        self.assertEqual(r['error']['code'],-32602)
        sc=self.op('veil_start_household',{'protected_window':'early prep'})['structuredContent']
        self.assertEqual(sc['alice_calendar'],7)
    def test_stale_and_decided_requests_do_not_occupy_the_pending_queue(self):
        self.op('veil_start_household',{'protected_window':'early prep'})
        for i in range(8):
            r=self.asst('veil_request_approval',{'text':'is alice free for dinner'})['structuredContent']
            self.assertEqual(r['status'],'pending')
        self.assertTrue(self.asst('veil_request_approval',{'text':'is alice free for dinner'})['isError'])
        # a decline frees the queue slot immediately
        self.op('veil_decide_approval',{'approval_id':self.op('veil_operator_view',{})['structuredContent']['approvals'][0]['approval_id'],'approve':False})
        r=self.asst('veil_request_approval',{'text':'is alice free for dinner'})['structuredContent']
        self.assertEqual(r['status'],'pending')
        self.assertTrue(self.asst('veil_request_approval',{'text':'is alice free for dinner'})['isError'])
        self.call('is alice free for late prep')  # conversation advances: all 8 go stale
        op=self.op('veil_operator_view',{})['structuredContent']
        self.assertEqual({a['status'] for a in op['approvals']},{'stale','declined'})
        for i in range(8):
            r=self.asst('veil_request_approval',{'text':'is alice free for dinner'})['structuredContent']
            self.assertEqual(r['status'],'pending')
        self.assertTrue(self.asst('veil_request_approval',{'text':'is alice free for dinner'})['isError'])
    def test_record_limit_bounds_retained_history(self):
        self.op('veil_start_household',{'protected_window':'early prep'})
        for cycle in range(8):
            for i in range(8):
                self.asst('veil_request_approval',{'text':'is alice free for dinner'})
            self.call('is alice free for late prep')
        r=self.asst('veil_request_approval',{'text':'is alice free for dinner'})
        self.assertTrue(r['isError'])
        self.assertIn('record limit',r['content'][0]['text'])
        op=self.op('veil_operator_view',{})['structuredContent']
        self.assertEqual(len(op['approvals']),64)
    def test_unsupported_text_refused_with_suggestions(self):
        r=self.call('what is her password')['structuredContent']
        self.assertFalse(r['supported_request']);self.assertTrue(r['suggestions'])
    def test_only_if_uninitialized_ensure_contract(self):
        op=lambda args: mcp_server.handle(rq(9,'tools/call',{'name':'veil_start_household','arguments':args}),self.s,'operator')['result']['structuredContent']
        r=op({'protected_window':'early prep','only_if_uninitialized':True})
        self.assertNotEqual(r.get('already_running'),True)
        gen=json.load(open(self.s.path))['generation']
        self.call('is alice free for dinner')
        r=op({'protected_windows':['early prep','late prep'],'only_if_uninitialized':True})
        self.assertTrue(r['already_running']);self.assertEqual(r['events'],1)
        self.assertEqual(json.load(open(self.s.path))['generation'],gen)
        v=mcp_server.handle(rq(10,'tools/call',{'name':'veil_operator_view','arguments':{}}),self.s,'operator')['result']['structuredContent']
        self.assertNotIn('protected_windows',v)
        r=op({'protected_window':'dinner'})
        self.assertNotEqual(json.load(open(self.s.path))['generation'],gen)
    def test_only_if_uninitialized_must_be_boolean(self):
        r=mcp_server.handle(rq(11,'tools/call',{'name':'veil_start_household','arguments':{'protected_window':'dinner','only_if_uninitialized':'yes'}}),self.s,'operator')
        self.assertTrue(r['result']['isError'])
    def test_status_before_start_and_after(self):
        r=mcp_server.handle(rq(1,'tools/call',{'name':'veil_status','arguments':{}}),self.s)['result']['structuredContent']
        self.assertFalse(r['initialized'])
        self.call('find a shared window')
        r=mcp_server.handle(rq(1,'tools/call',{'name':'veil_status','arguments':{}}),self.s)['result']['structuredContent']
        self.assertEqual(r['events'],1);self.assertIn('Synthetic',r['scope'])
    def test_spoken_text_promises_no_unbuilt_action(self):
        r=self.call('is alice free for early prep')
        self.assertNotIn('ask Alice',json.dumps(r))

class McpClientDemo(unittest.TestCase):
    def test_demo_client_runs_the_lifecycle_against_a_live_server(self):
        import server, subprocess, sys
        store = server.STORE / 'mcp-dialog.json'
        if store.exists(): store.unlink()  # isolate: the demo auto-initializes a fresh household
        server.MCP = mcp_server.Session(store)
        try: httpd = ThreadingHTTPServer(('127.0.0.1', 8765), server.Handler)
        except OSError: raise unittest.SkipTest('port 8765 busy')
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            out = subprocess.run([sys.executable, 'mcp_client_demo.py', 'http://127.0.0.1:8765/mcp'],
                                 capture_output=True, text=True, timeout=60, cwd=str(server.ROOT))
            self.assertEqual(out.returncode, 0, out.stderr)
            for frag in ('protocol 2025-11-25', 'veil_request_approval', 'status=pending', 'status=stale', 're-asked'):
                self.assertIn(frag, out.stdout)
        finally:
            httpd.shutdown(); httpd.server_close()

class McpHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import server
        cls.server=server;server.MCP=mcp_server.Session(Path(tempfile.mkdtemp())/'m.json')
        try:cls.httpd=ThreadingHTTPServer(('127.0.0.1',8765),server.Handler)
        except OSError:raise unittest.SkipTest('port 8765 busy')
        threading.Thread(target=cls.httpd.serve_forever,daemon=True).start()
    @classmethod
    def tearDownClass(cls):cls.httpd.shutdown();cls.httpd.server_close()
    def post(self,body,origin=None,raw=None):
        h={'Content-Type':'application/json'}
        if origin:h['Origin']=origin
        req=urllib.request.Request('http://127.0.0.1:8765/mcp',raw if raw is not None else json.dumps(body).encode(),h)
        try:
            with urllib.request.urlopen(req,timeout=5) as r:return r.status,r.read()
        except urllib.error.HTTPError as e:return e.code,e.read()
    def test_roundtrip_notification_and_errors(self):
        c,b=self.post(rq(1,'tools/list'));self.assertEqual(c,200);self.assertEqual(len(json.loads(b)['result']['tools']),4)
        c,b=self.post({'jsonrpc':'2.0','method':'notifications/initialized'});self.assertEqual((c,b),(202,b''))
        c,_=self.post(None,raw=b'{bad');self.assertEqual(c,400)
        c,_=self.post([rq(1,'ping')]);self.assertEqual(c,400)
        c,_=self.post(rq(1,'ping'),origin='http://evil.example');self.assertEqual(c,403)
    def test_operator_endpoint_requires_token(self):
        req=urllib.request.Request('http://127.0.0.1:8765/mcp-operator',json.dumps(rq(1,'tools/list')).encode(),{'Content-Type':'application/json'})
        with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(req,timeout=5)
        self.assertEqual(e.exception.code,403)
        req=urllib.request.Request('http://127.0.0.1:8765/mcp-operator',json.dumps(rq(1,'tools/list')).encode(),{'Content-Type':'application/json','X-Veil-Operator':self.server.OPERATOR_TOKEN})
        with urllib.request.urlopen(req,timeout=5) as r:self.assertEqual(len(json.loads(r.read())['result']['tools']),7)
    def test_session_header_protocol_header_and_delete(self):
        def raw(body,headers=None,method='POST'):
            h={'Content-Type':'application/json'};h.update(headers or {})
            req=urllib.request.Request('http://127.0.0.1:8765/mcp',json.dumps(body).encode() if body is not None else None,h,method=method)
            try:
                with urllib.request.urlopen(req,timeout=5) as r:return r.status,dict(r.headers),r.read()
            except urllib.error.HTTPError as e:return e.code,dict(e.headers),e.read()
        c,h,_=raw(rq(1,'initialize',{'protocolVersion':'2025-11-25'}));self.assertEqual(c,200);sid=h['Mcp-Session-Id']
        self.assertEqual(raw(rq(2,'ping'),{'Mcp-Session-Id':sid,'MCP-Protocol-Version':'2025-11-25'})[0],200)
        self.assertEqual(raw(rq(2,'ping'),{'Mcp-Session-Id':'nope'})[0],404)
        self.assertEqual(raw(rq(2,'ping'),{'MCP-Protocol-Version':'1999-01-01'})[0],400)
        self.assertEqual(raw(None,{'Mcp-Session-Id':sid},'DELETE')[0],200)
        self.assertEqual(raw(rq(2,'ping'),{'Mcp-Session-Id':sid})[0],404)
    def test_get_not_allowed(self):
        try:urllib.request.urlopen('http://127.0.0.1:8765/mcp',timeout=5)
        except urllib.error.HTTPError as e:self.assertEqual(e.code,405)

class ApprovalPersistence(unittest.TestCase):
    """Approval records persist with the session envelope; legacy sessions fail closed."""
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.path = self.dir / 's.json'
        self.s = mcp_server.Session(self.path)
        self.s.start('early prep')
    def test_decided_approval_persists_and_pause_survives_restart(self):
        self.s.ask('is alice free for cleanup')
        aid = self.s.request_approval('is alice free for early prep')['approval_id']
        self.s.decide(aid, True)
        env = json.loads(self.path.read_text())
        self.assertEqual(len(env['approvals']), 1)
        self.assertEqual(env['approvals'][0]['status'], 'approved')
        again = mcp_server.Session(self.path)  # process restart
        r = again.ask('is alice free for cleanup')
        self.assertEqual(r['output'], 'REFUSED')
        self.assertIn('approval', r['spoken'])
        self.assertNotIn('legacy_approval_history', r)
        view = again.status(operator=True)
        self.assertEqual([(a['request'], a['status']) for a in view['approvals']], [('is alice free for early prep', 'approved')])
        self.assertFalse(view['legacy_approval_history'])
    def test_pending_survives_restart_then_goes_stale(self):
        aid = self.s.request_approval('is alice free for early prep')['approval_id']
        again = mcp_server.Session(self.path)
        self.assertEqual(again.status(operator=True)['approvals'][0]['status'], 'pending')
        again.ask('is alice free for cleanup')
        self.assertEqual(again.status(operator=True)['approvals'][0]['status'], 'stale')
        with self.assertRaises(ValueError): again.decide(aid, True)
        self.assertIn('approvals', json.loads(self.path.read_text()))
    def test_legacy_envelope_fails_closed(self):
        env = json.loads(self.path.read_text())
        env.pop('approvals')
        self.path.write_text(json.dumps(env))
        legacy = mcp_server.Session(self.path)
        r = legacy.ask('is alice free for early prep')
        self.assertEqual(r['output'], 'REFUSED')
        self.assertTrue(r['legacy_approval_history'])
        self.assertIn('not persisted', r['spoken'])
        # approvals still work on a legacy session and the marker persists
        aid = legacy.request_approval('is alice free for early prep')['approval_id']
        legacy.decide(aid, True)
        env = json.loads(self.path.read_text())
        self.assertTrue(env['legacy_approval_history'])
        still = mcp_server.Session(self.path)
        self.assertTrue(still.ask('is alice free for cleanup').get('legacy_approval_history'))
        # explicit new simulation clears the legacy fail-closed state
        still.start('dinner')
        self.assertNotEqual(still.ask('is alice free for early prep')['output'], 'REFUSED')
    def test_oversize_approval_records_rejected(self):
        env = json.loads(self.path.read_text())
        env['approvals'] = [{'id': 'x', 'request': 'r', 'text': 't', 'status': 'stale',
                             'events_at_request': 0, 'approved_at_request': 0}] * 65
        self.path.write_text(json.dumps(env))
        with self.assertRaises(ValueError):
            mcp_server.dialog_store.status(self.path)

if __name__=='__main__':unittest.main()
