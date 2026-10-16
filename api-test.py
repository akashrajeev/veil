import urllib.request, urllib.error, json
URL='http://127.0.0.1:8765'
def call(path,method='GET',headers=None,data=None):
    request=urllib.request.Request(URL+path,method=method,headers=headers or {},data=data)
    try:
        with urllib.request.urlopen(request) as r: return r.status,json.load(r)
    except urllib.error.HTTPError as e: return e.code,json.load(e)
assert call('/api/reset','POST')[0]==200
assert call('/api/next','POST',{'Origin':'https://example.invalid'})[0]==403
assert call('/api/next','POST',{'Host':'example.invalid'})[0]==403
assert call('/api/next','POST',data=b'bad')[0]==400
assert call('/api/state')[1]['step']==0
assert call('/api/next','POST',data=b'{"expected_step":0}')[1]['step']==1
assert call('/api/next','POST',data=b'{"expected_step":0}')[1]['step']==1
assert call('/api/reset','POST')[1]['step']==0
for step in range(1,4):
    code,data=call('/api/next','POST');assert code==200 and data['step']==step
assert call('/api/next','POST')[1]['step']==3
assert call('/unknown')[0]==404
assert call('/unknown','POST')[0]==404
print('API checks pass: progression, end idempotency, origin/host/body restrictions, unknown routes.')
