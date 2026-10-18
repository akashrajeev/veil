"""Private loopback-only MCP lab. Never use the synthetic operator UI with real input."""
import argparse
import json
import os
from pathlib import Path
import secrets
from typing import Any
from calendar_guard import CalendarGuard

def create_app(guard, token, port=8766):
    from mcp.server.fastmcp import FastMCP
    from starlette.responses import Response
    if not isinstance(token,str) or len(token)<32:
        raise ValueError('set a random VEIL_LAB_TOKEN of at least 32 characters')
    mcp=FastMCP('Veil real-input lab',host='127.0.0.1',port=port,json_response=True,
                stateless_http=True,log_level='WARNING')

    @mcp.tool(structured_output=True)
    def calendar_windows() -> dict[str, Any]:
        """List four PUBLIC candidate windows and provenance. No availability bits."""
        return guard.public_windows()

    @mcp.tool(structured_output=True)
    def calendar_availability(window: int) -> dict[str, Any]:
        """Ask if the owner is free in a public window 0..3; guard may refuse."""
        if type(window) is not int or not 0<=window<=3: raise ValueError('window must be 0..3')
        return guard.ask('slot'+str(window))

    @mcp.tool(structured_output=True)
    def calendar_find_window() -> dict[str, Any]:
        """Find a guard-safe window under the public observer test assumption. Does not book."""
        return guard.ask('schedule')

    @mcp.tool(structured_output=True)
    def calendar_prep_parity() -> dict[str, Any]:
        """Ask exactly-one-free across public windows 0 and 1; joint guard may refuse."""
        return guard.ask('parity')

    inner=mcp.streamable_http_app()
    class PrivateApp:
        async def __call__(self,scope,receive,send):
            if scope['type']=='http':
                headers=dict(scope.get('headers',[]))
                supplied=headers.get(b'authorization',b'').decode('latin1')
                if not secrets.compare_digest(supplied,'Bearer '+token):
                    await Response(status_code=401)(scope,receive,send); return
            await inner(scope,receive,send)
    return PrivateApp()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--snapshot',required=True);p.add_argument('--state',required=True)
    p.add_argument('--port',type=int,default=8766)
    a=p.parse_args()
    guard=CalendarGuard(json.loads(Path(a.snapshot).read_text()),a.state)
    app=create_app(guard,os.environ.get('VEIL_LAB_TOKEN'),a.port)
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=a.port,log_level='warning',access_log=False)
