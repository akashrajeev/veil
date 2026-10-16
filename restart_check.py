"""End-to-end server process restart checks (real HTTP server, real .state file).
Scenario A: single-window session - generation/events/config/alive/bits/guard behavior.
Scenario B: joint config + pending approval - session intact; approvals are memory-only
            (documented), so they do not survive restart.
Scenario C: approved disclosure - the post-disclosure pause must SURVIVE restart; if the
            pause lifts (direct answers resume), that is a finding, not a pass.
Each scenario: build state over the operator+assistant MCP surfaces, hard-kill the
process, restart, compare. Exit 1 if any scenario fails.
"""
import json, re, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
STATE = ROOT / '.state' / 'mcp-dialog.json'
BASE = 'http://127.0.0.1:8765'

def start_server():
    p = subprocess.Popen([sys.executable, 'server.py'], cwd=ROOT,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            urllib.request.urlopen(BASE + '/alexa', timeout=2); return p
        except Exception:
            time.sleep(0.2)
    p.terminate(); raise SystemExit('server did not come up')

def token():
    html = urllib.request.urlopen(BASE + '/alexa', timeout=5).read().decode()
    return re.search(r"X-Veil-Operator':'([a-f0-9]+)'", html).group(1)

def call(surface, name, args, tok=None):
    req = urllib.request.Request(BASE + surface,
        data=json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}}).encode(),
        headers={'Content-Type':'application/json', **({'X-Veil-Operator': tok} if surface == '/mcp-operator' else {})})
    r = json.loads(urllib.request.urlopen(req, timeout=10).read())
    assert not r['result'].get('isError'), r
    return r['result']['structuredContent']

def generation():
    return json.loads(STATE.read_text())['generation']

def cycle(build, verify):
    if STATE.exists(): STATE.unlink()
    p = start_server(); pre = build(token()); p.terminate(); p.wait()
    p = start_server(); post = verify(token()); p.terminate(); p.wait()
    return pre, post

def view_subset(tok, keys):
    ov = call('/mcp-operator', 'veil_operator_view', {}, tok)
    return {k: ov[k] for k in keys if k in ov}

def scenario_a():
    def build(tok):
        call('/mcp-operator', 'veil_start_household', {'protected_window': 'early prep', 'alice_calendar': 7, 'only_if_uninitialized': True}, tok)
        a1 = call('/mcp', 'veil_ask', {'text': 'is alice free for dinner'})
        r1 = call('/mcp', 'veil_ask', {'text': 'is alice free for early prep'})
        return {'answers': {'dinner': a1.get('spoken'), 'early_prep': r1.get('spoken')},
                'status': call('/mcp', 'veil_status', {}),
                'view': view_subset(tok, ('protected_window','alice_calendar','with_veil_alive_calendars','with_veil_information_bits','events')),
                'generation': generation()}
    def verify(tok):
        snap = {'status': call('/mcp', 'veil_status', {}),
                'view': view_subset(tok, ('protected_window','alice_calendar','with_veil_alive_calendars','with_veil_information_bits','events')),
                'generation': generation()}
        late = call('/mcp', 'veil_ask', {'text': 'is alice free for late prep'})
        r2 = call('/mcp', 'veil_ask', {'text': 'is alice free for early prep'})
        snap.update({'late': late.get('spoken'), 'early_prep': r2.get('spoken')})
        return snap
    pre, post = cycle(build, verify)
    checks = {'generation identical': pre['generation'] == post['generation'],
              'events identical': pre['status'].get('events') == post['status'].get('events'),
              'config identical': pre['view'] == post['view'],
              'refusal still uniform': post['early_prep'] == pre['answers']['early_prep'] == "I can't answer that.",
              'next answer deterministic': post['late'] in ("Alice is free for late prep.", "Alice is busy during late prep.")}
    return {'check': 'restart A: single-window session', 'pre': pre, 'post': post, 'checks': checks, 'passed': all(checks.values())}

def scenario_b():
    def build(tok):
        call('/mcp-operator', 'veil_start_household', {'protected_windows': ['early prep', 'late prep'], 'alice_calendar': 7, 'only_if_uninitialized': True}, tok)
        call('/mcp', 'veil_ask', {'text': 'is alice free for dinner'})
        r = call('/mcp', 'veil_ask', {'text': 'can alice cover exactly one of the two prep windows'})
        a = call('/mcp', 'veil_request_approval', {'text': 'can alice cover exactly one of the two prep windows'})
        ov = call('/mcp-operator', 'veil_operator_view', {}, tok)
        return {'xor': r.get('spoken'), 'approvals': [(x['request'], x['status']) for x in ov['approvals']],
                'view': {k: ov[k] for k in ('protected_windows','alice_calendar','events') if k in ov},
                'generation': generation()}
    def verify(tok):
        ov = call('/mcp-operator', 'veil_operator_view', {}, tok)
        return {'approvals': [(x['request'], x['status']) for x in ov['approvals']],
                'view': {k: ov[k] for k in ('protected_windows','alice_calendar','events') if k in ov},
                'generation': generation()}
    pre, post = cycle(build, verify)
    checks = {'joint config identical': pre['view'] == post['view'],
              'generation identical': pre['generation'] == post['generation'],
              'xor refused pre': pre['xor'] == "I can't answer that.",
              'pending approval existed pre': pre['approvals'] and pre['approvals'][0][1] == 'pending',
              'pending approval survives restart': post['approvals'] == pre['approvals']}
    return {'check': 'restart B: joint config + pending approval', 'pre': pre, 'post': post, 'checks': checks, 'passed': all(checks.values())}

def scenario_c():
    def build(tok):
        call('/mcp-operator', 'veil_start_household', {'protected_window': 'early prep', 'alice_calendar': 7, 'only_if_uninitialized': True}, tok)
        call('/mcp', 'veil_ask', {'text': 'is alice free for dinner'})
        call('/mcp', 'veil_ask', {'text': 'is alice free for early prep'})
        a = call('/mcp', 'veil_request_approval', {'text': 'is alice free for early prep'})
        call('/mcp-operator', 'veil_decide_approval', {'approval_id': a['approval_id'], 'approve': True}, tok)
        pause = call('/mcp', 'veil_ask', {'text': 'is alice free for cleanup'})
        return {'pause_answer': pause.get('spoken'), 'generation': generation(),
                'events': call('/mcp', 'veil_status', {}).get('events')}
    def verify(tok):
        events0 = call('/mcp', 'veil_status', {}).get('events')
        gen0 = generation()
        pause = call('/mcp', 'veil_ask', {'text': 'is alice free for cleanup'})
        ov = call('/mcp-operator', 'veil_operator_view', {}, tok)
        return {'pause_answer': pause.get('spoken'), 'approvals_post': [(x['request'], x['status']) for x in ov['approvals']],
                'generation': gen0, 'events': events0}
    pre, post = cycle(build, verify)
    checks = {'pre pause held': 'approval' in (pre['pause_answer'] or ''),
              'generation identical': pre['generation'] == post['generation'],
              'events identical': pre['events'] == post['events'],
              'post-disclosure pause SURVIVES restart': 'approval' in (post['pause_answer'] or '')}
    return {'check': 'restart C: approved-disclosure pause persistence', 'pre': pre, 'post': post, 'checks': checks, 'passed': all(checks.values())}

if __name__ == '__main__':
    results = [scenario_a(), scenario_b(), scenario_c()]
    out = {'check': 'server process stop/restart persistence (real HTTP server, .state file)',
           'scenarios': results, 'passed': all(r['passed'] for r in results)}
    print(json.dumps(out, indent=1))
    sys.exit(0 if out['passed'] else 1)
