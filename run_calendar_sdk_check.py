"""Private end-to-end check. Prints only aggregate pass status, never calendar windows/mask."""
import argparse
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
import urllib.request
import urllib.error
from calendar_mcp_client import run

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--snapshot',required=True);p.add_argument('--state',required=True)
    a=p.parse_args()
    token=secrets.token_hex(32)
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    root=Path(__file__).parent
    with tempfile.TemporaryFile() as log:
        proc=subprocess.Popen([sys.executable,str(root/'calendar_mcp_server.py'),'--snapshot',a.snapshot,'--state',a.state,'--port',str(port)],
            env={**os.environ,'VEIL_LAB_TOKEN':token},stdout=log,stderr=log)
        try:
            url=f'http://127.0.0.1:{port}/mcp'
            for _ in range(100):
                if proc.poll() is not None: raise RuntimeError('server failed; inspect private local log')
                try:urllib.request.urlopen(url,timeout=.1)
                except urllib.error.HTTPError as e:
                    if e.code==401:break
                except OSError:time.sleep(.05)
            else:raise RuntimeError('server not ready')
            result=asyncio.run(run(url,token))
            if any(x['result']['answer']=='PAUSED' for x in result['outputs']):raise RuntimeError('snapshot stale or conversation exhausted')
            # Verify truthful live outputs against the private bitset without printing it.
            snapshot=json.loads(Path(a.snapshot).read_text())
            mask=snapshot['free_mask']
            for item in result['outputs']:
                answer=item['result']['answer']
                if answer.startswith('ALICE_SLOT'):
                    index,value=answer[len('ALICE_SLOT'):].split(':')
                    assert int(value)==((mask>>int(index))&1)
                elif answer.startswith('MEETING:'):
                    assert (mask>>int(answer.split(':')[1]))&1
            print(json.dumps({'passed':True,'protocol':result['protocol'],'tool_count':result['tool_count'],
                'calls':result['calls'],'source':snapshot['source'],'private_data_printed':False}))
        finally:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
if __name__=='__main__':main()
