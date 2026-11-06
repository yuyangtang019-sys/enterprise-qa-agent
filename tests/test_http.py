import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
import unittest
from test_agent import DATA
from enterprise_qa.models.real import RealModel
from enterprise_qa.agent import run
from enterprise_qa.knowledge import Knowledge

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_POST(self):
        payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.seen.append((self.path,payload,self.headers.get('Authorization')))
        code=self.server.codes.pop(0) if self.server.codes else 200
        if self.server.delay: time.sleep(self.server.delay)
        response={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps({'action':'ask_user','purpose':'明确城市','question':'哪个城市？','reason':'缺少范围'})}]}]}
        if self.server.response_override is not None:
            response=self.server.response_override
        body=json.dumps(response if code==200 else {'error':'never expose raw server error'}).encode()
        try:
            self.send_response(code); self.end_headers(); self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError): pass

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.server.codes=[]; self.server.seen=[]; self.server.delay=0; self.server.response_override=None
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.url='http://127.0.0.1:'+str(self.server.server_port)+'/v1'
    def tearDown(self): self.server.shutdown(); self.server.server_close(); self.thread.join()
    def model(self,**kw): return RealModel(key='test-only-not-a-real-key',model='contract-model',base_url=self.url,**kw)
    def test_wire_contract(self):
        m=self.model(); t=run(m,Knowledge(DATA),'住宿')
        self.assertEqual(t['result']['task_status'],'awaiting_user')
        path,payload,auth=self.server.seen[0]
        self.assertEqual(path,'/v1/responses'); self.assertEqual(auth,'Bearer test-only-not-a-real-key')
        self.assertEqual(payload['model'],'contract-model'); self.assertFalse(payload['store'])
        self.assertIn('question',json.loads(payload['input'])); self.assertIn('search',payload['instructions'])
    def test_retry_429(self):
        self.server.codes=[429,200]; m=self.model(); m.decide('system',{'question':'q'}); self.assertEqual(m.attempts,2)
    def test_retry_503(self):
        self.server.codes=[503,200]; m=self.model(); m.decide('s',{}); self.assertEqual(m.attempts,2)
    def test_auth_no_retry(self):
        for status in [401,403]:
            self.server.codes=[status]; m=self.model(); t=run(m,Knowledge(DATA),'q')
            self.assertEqual(m.attempts,1); self.assertEqual(t['steps'][0]['observation']['error']['code'],'authentication_failed')
            self.assertIn('权限',t['result']['gaps'][0]); self.assertNotIn('raw server',json.dumps(t))
    def test_retry_exhausted(self):
        self.server.codes=[500,500]; m=self.model(); t=run(m,Knowledge(DATA),'q')
        self.assertEqual(m.attempts,2); self.assertEqual(t['result']['outcome'],'tool_failure')
    def test_timeout(self):
        self.server.delay=0.15; m=self.model(timeout=0.02,retries=0)
        with self.assertRaises(RuntimeError): m.decide('s',{})
        self.assertEqual(m.attempts,1)
    def test_endpoint_security(self):
        for url in ['http://example.com/v1','https://user:pass@example.com/v1','https://example.com/v1?key=x']:
            with self.assertRaises(ValueError): RealModel(key='test',model='test',base_url=url)
    def test_incomplete_response(self):
        self.server.response_override={'status':'incomplete','output':[]}
        t=run(self.model(),Knowledge(DATA),'q')
        self.assertEqual(t['result']['task_status'],'incomplete')
    def test_invalid_json_action_observation(self):
        self.server.response_override={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'not JSON'}]}]}
        t=run(self.model(),Knowledge(DATA),'q',max_steps=2)
        self.assertEqual(t['result']['outcome'],'step_limit')
        self.assertEqual(len(self.server.seen),2)
        second=json.loads(self.server.seen[1][1]['input'])
        self.assertEqual(second['steps'][0]['observation']['error']['code'],'invalid_action_or_citation')

if __name__=='__main__': unittest.main()
