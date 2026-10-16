"""Tiny real MCP client: initialize, list tools, call them over Streamable HTTP.
Usage: python3 mcp_client_demo.py [http://127.0.0.1:8765/mcp] (server must be running)."""
import json,sys,urllib.request
URL=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8765/mcp'
_id=[0]
def rpc(method,params=None,notify=False):
    body={'jsonrpc':'2.0','method':method}
    if params is not None:body['params']=params
    if not notify:_id[0]+=1;body['id']=_id[0]
    req=urllib.request.Request(URL,json.dumps(body).encode(),{'Content-Type':'application/json','Accept':'application/json, text/event-stream','MCP-Protocol-Version':'2025-11-25'})
    with urllib.request.urlopen(req,timeout=10) as r:
        raw=r.read();return json.loads(raw) if raw else None
def main():
    init=rpc('initialize',{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'veil-demo-client','version':'0.1'}})
    print('server:',init['result']['serverInfo']['name'],'protocol',init['result']['protocolVersion'])
    rpc('notifications/initialized',notify=True)
    print('tools:',[t['name'] for t in rpc('tools/list')['result']['tools']])
    def call(n,a):
        r=rpc('tools/call',{'name':n,'arguments':a})['result'];sc=r.get('structuredContent',{})
        print(f"> {a.get('text',n)}\n  Veil: {r['content'][0]['text']}\n  events={sc.get('events')}")
    for t in ['is alice free for early prep','is alice free for late prep','find a shared window']:call('veil_ask',{'text':t})
    print('--- simulated approval lifecycle (assistant surface only) ---')
    call('veil_ask',{'text':'is alice free for early prep'})
    r=rpc('tools/call',{'name':'veil_request_approval','arguments':{'text':'is alice free for early prep'}})['result']
    aid=r['structuredContent']['approval_id']
    print(f"> (asks Alice to approve, simulated) approval_id={aid}")
    def check():
        c=rpc('tools/call',{'name':'veil_check_approval','arguments':{'approval_id':aid}})['result']
        print(f"  check: status={c['structuredContent']['status']} - {c['content'][0]['text']}")
        return c['structuredContent']['status']
    check()
    print('> (the room keeps talking before Alice decides)')
    call('veil_ask',{'text':'is alice free for dinner'})
    assert check()=='stale','expected the request to be stale after the conversation moved'
    print('  the stale request can never be approved; Bob would ask again on the current conversation.')
    r2=rpc('tools/call',{'name':'veil_request_approval','arguments':{'text':'is alice free for early prep'}})['result']
    print(f"> re-asked: approval_id={r2['structuredContent']['approval_id']} status={r2['structuredContent']['status']}")
    print('  Alice decides on the SIMULATED operator panel (/alexa) or the token-gated operator endpoint; this client is the assistant surface only.')
main()
