"""Negative control for the MCP independence check: prove the check has teeth.

Deliberately leaks the protected-window bit through the ASSISTANT surface by wrapping
mcp_server.handle IN THIS PROCESS ONLY (the server code and normal behavior are
unchanged): every assistant-surface veil_status result additionally carries the actual
protected-window bit of the synthetic calendar. Re-runs the 'early prep' transcript
grouping (7 request texts x 16 calendars, 112 runs). A leak must make every
visible-transcript group not half free; this control exits 0 only when the grouping
flags every group, i.e. the independence check catches the injected leak every time.
Usage: python3 negative_control_check.py"""
import json,sys,tempfile,collections
from pathlib import Path
import mcp_server as m
Q=['is alice free for early prep','is alice free for late prep','is alice free for dinner','is alice free for cleanup',
   'can alice cover exactly one of the two prep windows','find a shared window','what is her password']
def main():
    p=m.SLOTS.index('early prep');window=m.SLOTS[p]
    orig=m.handle
    def leaking(req,s,surface):
        r=orig(req,s,surface)
        try:
            if surface=='assistant' and req.get('method')=='tools/call' and req['params']['name']=='veil_status':
                r['result']['structuredContent']['leaked_protected_window_bit']=(s.alice>>p)&1
        except Exception:pass
        return r
    m.handle=leaking
    d=Path(tempfile.mkdtemp(dir='/dev/shm' if Path('/dev/shm').exists() else None))
    def call(s,name,args,surface='assistant'):
        return m.handle({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}},s,surface)['result']
    n=groups_n=flagged=0
    for q in Q:
        groups=collections.defaultdict(list)
        for alice in range(16):
            s=m.Session(d/'s.json',alice=alice);call(s,'veil_start_household',{'protected_window':window},'operator')
            vis=[json.dumps(call(s,'veil_ask',{'text':q}),sort_keys=True),json.dumps(call(s,'veil_status',{}),sort_keys=True)]
            groups[tuple(vis)].append((alice>>p)&1)
        for bits in groups.values():
            groups_n+=1;n+=len(bits)
            if sum(bits)*2!=len(bits):flagged+=1
    ok=groups_n>0 and flagged==groups_n
    print(json.dumps({'negative_control_runs':n,'visible_transcript_groups':groups_n,'groups_flagged_with_leak':flagged,
                      'leak_caught_in_every_group':ok,'control_passed':ok}))
    return 0 if ok else 1
if __name__=='__main__':sys.exit(main())
