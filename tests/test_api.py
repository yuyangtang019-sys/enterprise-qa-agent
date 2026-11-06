import json
import threading
import urllib.request
import urllib.error
import unittest
from test_agent import DATA, Script
from enterprise_qa.http_api import create_server, parse_input
from enterprise_qa.models.mock import action
from enterprise_qa.agent import run as strict_run
def run(*args, **kwargs):
    kwargs.setdefault("allow_legacy", True)  # historical v1 protocol regression only
    return strict_run(*args, **kwargs)
from enterprise_qa.knowledge import Knowledge

class APITests(unittest.TestCase):
    def test_input_boundaries(self):
        for d in [{'question':False},{'question':'x','max_steps':False},{'question':'x','history':None},{'question':'x','session_id':1},{'question':'x','base_url':'evil'},{'question':'x','fault':{'document_id':'SECURITY','count':True}}]:
            with self.subTest(d=d),self.assertRaises(ValueError): parse_input(json.dumps(d),True)
    def test_fault_permission(self):
        with self.assertRaises(PermissionError): parse_input(json.dumps({'question':'x','fault':{}}),False)
    def test_session_roundtrip_and_isolation(self):
        server=create_server(DATA,model_factory=lambda:Script([action('ask_user',question='哪个城市？',reason='缺城市')]))
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        url='http://127.0.0.1:'+str(server.server_port)
        try:
            for sid,expected in [('a',0),('a',1),('b',0)]:
                request=urllib.request.Request(url+'/ask',data=json.dumps({'question':'住宿','session_id':sid}).encode(),headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(request) as r: t=json.loads(r.read())['trace']
                self.assertEqual(len(t['history']),expected)
            bad=urllib.request.Request(url+'/ask',data=b'{',headers={'Content-Type':'application/json'})
            with self.assertRaises(urllib.error.HTTPError) as cm: urllib.request.urlopen(bad)
            self.assertEqual(cm.exception.code,400); cm.exception.close()
            with urllib.request.urlopen(url+'/health') as r: self.assertEqual(r.status,200)
        finally: server.shutdown(); server.server_close(); thread.join()
    def test_unresolved_read_cannot_claim_completed(self):
        model=Script([action('read',document_id='SECURITY',fragment_id='p1'),action('finish',outcome='insufficient_evidence',answer='资料不足',citations=[],gaps=['读取失败']),action('finish',outcome='tool_failure',answer='工具失败',citations=[],gaps=['原文不可用'])])
        t=run(model,Knowledge(DATA,{'read:SECURITY':-1}),'远程安全')
        self.assertEqual(t['steps'][1]['observation']['error']['code'],'unresolved_read_failure_use_tool_failure')
        self.assertEqual(t['result']['task_status'],'incomplete')
    def test_unrelated_read_does_not_hide_failure(self):
        model=Script([action('read',document_id='SECURITY',fragment_id='p1'),action('read',document_id='LEAVE',fragment_id='p1'),action('finish',outcome='insufficient_evidence',answer='缺少安全制度',citations=[],gaps=['读取失败']),action('finish',outcome='tool_failure',answer='安全原文不可用',citations=[],gaps=['读取失败'])])
        t=run(model,Knowledge(DATA,{'read:SECURITY':-1}),'远程安全')
        self.assertEqual(t['steps'][2]['observation']['error']['code'],'unresolved_read_failure_use_tool_failure')
        self.assertEqual(t['result']['task_status'],'incomplete')
    def test_selftest_rejects_empty_success_response(self):
        import sys
        from pathlib import Path
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'examples'))
        from http_selftest import response_checks
        self.assertFalse(all(response_checks('normal',200,{},business=True).values()))
        self.assertFalse(all(response_checks('normal',200,{'result':{},'trace':{}},business=True).values()))
    def test_history_check_distinguishes_rejection_from_adoption(self):
        import sys
        from pathlib import Path
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'examples'))
        from http_selftest import fake_history_rejected
        self.assertTrue(fake_history_rejected('上海600元。历史9999元未见原文支持，不予采用。'))
        self.assertFalse(fake_history_rejected('上海住宿上限9999元。'))

if __name__=='__main__': unittest.main()
