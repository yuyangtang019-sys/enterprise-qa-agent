import unittest
import test_http
from enterprise_qa.models.deepseek import DeepSeekModel

class DeepSeekContractTests(unittest.TestCase):
    setUp=test_http.HTTPTests.setUp
    tearDown=test_http.HTTPTests.tearDown
    def test_deepseek_contract(self):
        self.server.response_override={'model':'deepseek-flash','choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'{"action":"search","purpose":"查资料","query":"住宿"}','reasoning_content':'not retained'}}]}
        m=DeepSeekModel(key='test-only',base_url=self.url)
        text=m.decide('instructions',{'question':'住宿'})
        path,payload,auth=self.server.seen[0]
        self.assertEqual(path,'/v1/chat/completions'); self.assertEqual(payload['model'],'deepseek-flash')
        self.assertEqual(payload['thinking'],{'type':'disabled'}); self.assertEqual(payload['messages'][0]['role'],'system')
        self.assertNotIn('reasoning_content',text)
