"""Loopback HTTP API; no client-specified paths, endpoints, or credentials."""
import argparse
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .agent import run
from .knowledge import Knowledge
from .models.deepseek import DeepSeekModel
from .tracing import redact

MAX_BODY=32768

def unique_object(pairs):
    result={}
    for k,v in pairs:
        if k in result: raise ValueError('duplicate_key')
        result[k]=v
    return result

def parse_input(body,test_mode=False):
    d=json.loads(body,object_pairs_hook=unique_object)
    if type(d) is not dict or not set(d)<= {'question','history','session_id','max_steps','fault'}:
        raise ValueError('unknown_fields_or_body_type')
    q=d.get('question')
    if type(q) is not str or not 0<len(q.strip())<=2000: raise ValueError('invalid_question')
    n=d.get('max_steps',12)
    if type(n) is not int or not 1<=n<=20: raise ValueError('invalid_max_steps')
    sid=d.get('session_id')
    if 'session_id' in d and (type(sid) is not str or not re.fullmatch('[A-Za-z0-9_-]{1,64}',sid)):
        raise ValueError('invalid_session_id')
    if sid and 'history' in d: raise ValueError('history_and_session_exclusive')
    history=d.get('history',[])
    if type(history) is not list or len(history)>20: raise ValueError('invalid_history')
    normalized=[]
    for h in history:
        if type(h) is not dict or not {'question','answer'}<=set(h) or not set(h)<={'question','answer','dataset_digest'}:
            raise ValueError('invalid_history_item')
        if any(type(v) is not str or len(v)>6000 for v in h.values()): raise ValueError('invalid_history_value')
        normalized.append({**h,'dataset_digest':h.get('dataset_digest','untrusted-client-history')})
    failures={}
    if 'fault' in d:
        f=d['fault']
        if not test_mode: raise PermissionError('fault_injection_disabled')
        if type(f) is not dict or set(f)!={'document_id','count'} or type(f['document_id']) is not str or not re.fullmatch('[A-Z][A-Z0-9-]{0,63}',f['document_id']) or type(f['count']) is not int or f['count'] not in {-1,1,2}:
            raise ValueError('invalid_fault')
        failures={'read:'+f['document_id']:f['count']}
    return q,normalized,sid,n,failures

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def setup(self):
        super().setup(); self.connection.settimeout(10)
    def send_json(self,status,payload):
        body=json.dumps(redact(payload),ensure_ascii=False).encode('utf-8')
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','no-store'); self.end_headers()
        try: self.wfile.write(body)
        except OSError: pass
    def do_GET(self):
        if self.path!='/health': return self.send_json(404,{'error':'not_found'})
        self.send_json(200,{'status':'ok','mode':'real','provider':'DeepSeek','test_mode':self.server.test_mode})
    def do_PUT(self): self.send_json(405,{'error':'method_not_allowed'})
    do_DELETE=do_PUT
    do_PATCH=do_PUT
    def do_POST(self):
        if self.path!='/ask': return self.send_json(404,{'error':'not_found'})
        if self.headers.get('Transfer-Encoding'): return self.send_json(400,{'error':'transfer_encoding_not_supported'})
        if self.headers.get_content_type()!='application/json': return self.send_json(415,{'error':'application_json_required'})
        size=self.headers.get('Content-Length')
        if size is None: return self.send_json(411,{'error':'content_length_required'})
        try: size=int(size)
        except ValueError: return self.send_json(400,{'error':'invalid_content_length'})
        if not 0<size<=MAX_BODY: return self.send_json(413,{'error':'body_limit'})
        try:
            body=self.rfile.read(size)
            if len(body)!=size: raise ValueError('short_body')
            q,h,sid,steps,failures=parse_input(body,self.server.test_mode)
        except PermissionError: return self.send_json(403,{'error':'fault_injection_disabled'})
        except (ValueError,UnicodeError,TimeoutError): return self.send_json(400,{'error':'invalid_request'})
        try:
            # Bounded in-memory sessions; serializes updates to preserve turn order.
            with self.server.session_lock:
                if sid and sid not in self.server.sessions and len(self.server.sessions)>=100:
                    return self.send_json(429,{'error':'session_capacity'})
                history=list(self.server.sessions.get(sid,[])) if sid else h
                trace=run(self.server.model_factory(),Knowledge(self.server.data,failures),q,history,steps)
                if sid:
                    self.server.sessions[sid]=(history+[{'question':q,'answer':trace['result']['answer'],'dataset_digest':trace['final_dataset_digest']}])[-20:]
            self.send_json(200,{'result':trace['result'],'trace':trace})
        except Exception:
            self.send_json(503,{'error':'service_unavailable','message':'检查本地配置或稍后重试；服务不自动使用Mock。'})

def create_server(data,port=0,test_mode=False,model_factory=DeepSeekModel):
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.test_mode=test_mode; server.data=data; server.model_factory=model_factory
    server.sessions={}; server.session_lock=threading.Lock()
    return server

def main():
    from pathlib import Path
    p=argparse.ArgumentParser(); p.add_argument('--port',type=int,default=8765); p.add_argument('--test-mode',action='store_true')
    a=p.parse_args(); server=create_server(Path(__file__).resolve().parents[2]/'data/knowledge.json',a.port,a.test_mode)
    print('Real DeepSeek API listening on http://127.0.0.1:'+str(server.server_port),flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
