import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import server


def urlopen(req, port):
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


class RealDemoPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(('127.0.0.1', 8765), server.Handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def post(self, path, body):
        req = urllib.request.Request(f'http://127.0.0.1:{self.port}{path}',
                                     data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'})
        try:
            return urlopen(req, self.port)
        except urllib.error.HTTPError as e:
            return {'_status': e.code, **json.loads(e.read())}

    def test_page_served(self):
        with urllib.request.urlopen(f'http://127.0.0.1:{self.port}/real', timeout=10) as r:
            html = r.read().decode()
        self.assertIn('real public schedule feeds', html)
        self.assertIn('declared assumptions', html)

    def test_cases_listed_with_provenance(self):
        with urllib.request.urlopen(f'http://127.0.0.1:{self.port}/api/real/cases', timeout=10) as r:
            d = json.loads(r.read())
        names = {c['name'] for c in d['cases']}
        self.assertIn('fosdem-2026-sunday', names)
        for c in d['cases']:
            self.assertTrue(c['source_url'].startswith('https://'))

    def test_select_and_ask_truthfully(self):
        d = self.post('/api/real/select', {'case': 'f1-las-vegas-2026'})
        self.assertEqual(len(d['windows']), 4)
        self.assertEqual(d['source'], 'real-public-ics')
        # Windows 0 and 1 are jointly protected at zero disclosure budget:
        # individual answers would shift the joint distribution, so refuse.
        for i in (0, 1):
            d = self.post('/api/real/ask', {'case': 'f1-las-vegas-2026', 'request': f'slot{i}'})
            self.assertEqual(d['answer'], 'NEEDS_PRIVATE_DECISION')
        # Unprotected windows 2 and 3 are answered truthfully (f1 mask is 12).
        for i, bit in ((2, 1), (3, 1)):
            d = self.post('/api/real/ask', {'case': 'f1-las-vegas-2026', 'request': f'slot{i}'})
            self.assertEqual(d['answer'], f'ALICE_SLOT{i}:{bit}')
        d = self.post('/api/real/ask', {'case': 'f1-las-vegas-2026', 'request': 'schedule'})
        self.assertTrue(d['answer'].startswith('MEETING:'))

    def test_unknown_case_and_request_rejected(self):
        self.assertEqual(self.post('/api/real/select', {'case': 'nosuch'})['_status'], 400)
        self.assertEqual(self.post('/api/real/select', {'case': '../etc'})['_status'], 400)
        self.assertEqual(self.post('/api/real/ask', {'case': 'f1-las-vegas-2026', 'request': 'dump'})['_status'], 400)

    def test_ledger_persists_across_guard_reload(self):
        self.post('/api/real/select', {'case': 'epl-2026-10-17'})
        d1 = self.post('/api/real/ask', {'case': 'epl-2026-10-17', 'request': 'slot2'})
        self.assertEqual(d1['answer'], 'ALICE_SLOT2:0')  # unprotected window, busy in the real feed
        server.REAL_GUARDS.pop('epl-2026-10-17', None)  # simulate restart
        d = self.post('/api/real/ask', {'case': 'epl-2026-10-17', 'request': 'slot3'})
        self.assertEqual(d['answer'], 'ALICE_SLOT3:0')  # unprotected window, busy in the real feed
        self.assertGreaterEqual(d['events'], 2)  # both requests recorded in the ledger


if __name__ == '__main__':
    unittest.main()
