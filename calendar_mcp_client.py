"""Official SDK client: real Streamable HTTP, structured tool calls, no LLM/Alexa claim."""
import argparse
import asyncio
import json
import os
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def run(url, token):
    async with httpx.AsyncClient(headers={'Authorization':'Bearer '+token},timeout=30) as http:
        async with streamable_http_client(url,http_client=http) as (read,write,_):
            async with ClientSession(read,write) as session:
                init=await session.initialize()
                assert init.protocolVersion == '2025-11-25',init.protocolVersion
                tools=await session.list_tools()
                assert {t.name for t in tools.tools}=={'calendar_windows','calendar_availability','calendar_find_window','calendar_prep_parity'}
                outputs=[]
                for name,args in [('calendar_prep_parity',{}),('calendar_availability',{'window':0}),
                                  ('calendar_availability',{'window':2}),('calendar_find_window',{})]:
                    r=await session.call_tool(name,args)
                    if r.isError: raise RuntimeError('MCP tool failed')
                    outputs.append({'tool':name,'result':r.structuredContent})
                # Do not print personal windows or private outputs in normal mode.
                return {'protocol':init.protocolVersion,'tool_count':len(tools.tools),'calls':len(outputs),'outputs':outputs}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',default='http://127.0.0.1:8766/mcp')
    p.add_argument('--fixture-output',action='store_true',help='print tool outputs ONLY with a synthetic fixture server')
    a=p.parse_args();result=asyncio.run(run(a.url,os.environ['VEIL_LAB_TOKEN']))
    if not a.fixture_output: result.pop('outputs')
    print(json.dumps(result,indent=2))
