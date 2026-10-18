"""Network integration test: separate SDK server/client processes, no browser or accounts."""
import asyncio
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
import urllib.error
from calendar_input import private_write
from test_calendar_input import fixture
from calendar_mcp_client import run

ROOT=Path(__file__).parent
class MCPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.snapshot=self.root/'snapshot.json';private_write(self.snapshot,fixture())
        with socket.socket() as s:s.bind(('127.0.0.1',0));self.port=s.getsockname()[1]
        self.token=secrets.token_hex(32);self.url=f'http://127.0.0.1:{self.port}/mcp'
        self.proc=None;self.start();self.addCleanup(self.stop)
    def start(self):
        self.proc=subprocess.Popen([sys.executable,'calendar_mcp_server.py','--snapshot',str(self.snapshot),'--state',str(self.root/'state.json'),'--port',str(self.port)],cwd=ROOT,env={**os.environ,'VEIL_LAB_TOKEN':self.token},stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        for _ in range(100):
            if self.proc.poll() is not None:
                self.fail(self.proc.stderr.read().decode())
            try:
                urllib.request.urlopen(self.url,timeout=.1)
            except urllib.error.HTTPError as e:
                if e.code==401:return
            except OSError:time.sleep(.05)
        self.fail('server failed to start')
    def stop(self):
        if self.proc is not None:
            self.proc.terminate()
            try:self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait()
            self.proc.stderr.close();self.proc=None
    def test_unauthorized_denied(self):
        with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(self.url)
        self.assertEqual(e.exception.code,401)
    def test_official_sdk_roundtrip_restart_and_shared_ledger(self):
        result=asyncio.run(run(self.url,self.token))
        self.assertEqual(result['protocol'],'2025-11-25');self.assertEqual(result['calls'],4)
        outputs=result['outputs']
        self.assertEqual(outputs[0]['result']['answer'],'NEEDS_PRIVATE_DECISION')
        self.assertEqual(outputs[1]['result']['answer'],'NEEDS_PRIVATE_DECISION')
        self.assertEqual(outputs[2]['result']['answer'],'ALICE_SLOT2:1')
        self.assertEqual(outputs[3]['result']['answer'],'MEETING:2')
        self.stop();self.start()
        second=asyncio.run(run(self.url,self.token))
        self.assertEqual(second['outputs'][-1]['result']['events'],8)
    def test_operator_tool_unavailable(self):
        async def check():
            import httpx
            from mcp import ClientSession
            from mcp.client.streamable_http import streamable_http_client
            async with httpx.AsyncClient(headers={'Authorization':'Bearer '+self.token}) as h:
                async with streamable_http_client(self.url,http_client=h) as (r,w,_):
                    async with ClientSession(r,w) as c:
                        await c.initialize()
                        return await c.call_tool('veil_operator_view',{})
        self.assertTrue(asyncio.run(check()).isError)
    def test_invalid_arguments_error_no_ledger_advance(self):
        async def check():
            import httpx
            from mcp import ClientSession
            from mcp.client.streamable_http import streamable_http_client
            async with httpx.AsyncClient(headers={'Authorization':'Bearer '+self.token}) as h:
                async with streamable_http_client(self.url,http_client=h) as (r,w,_):
                    async with ClientSession(r,w) as c:
                        await c.initialize()
                        return await c.call_tool('calendar_availability',{'window':99})
        self.assertTrue(asyncio.run(check()).isError)
        state=json.loads((self.root/'state.json').read_text())
        self.assertEqual(json.loads(state['ledger'])['transcript'],[])

if __name__=='__main__':unittest.main()
