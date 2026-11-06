import json
import os
from .real import RealModel

class DeepSeekModel(RealModel):
    provider = 'DeepSeek Chat Completions'
    endpoint = '/chat/completions'
    requested_model = 'DeepSeek-V4.1-Flash-1017'
    def __init__(self,key=None,model=None,base_url=None,**kwargs):
        from ..config import load_local
        if key is None:
            load_local()
        key = key or os.getenv('DEEPSEEK_API_KEY')
        if not key:
            raise ValueError('Set DEEPSEEK_API_KEY; never falls back to Mock')
        super().__init__(key=key,model=model or os.getenv('DEEPSEEK_MODEL') or 'deepseek-flash',base_url=base_url or os.getenv('DEEPSEEK_BASE_URL') or 'https://api.deepseek.com',**kwargs)

    def payload(self,instructions,state):
        return {'model':self.name,'messages':[{'role':'system','content':instructions},{'role':'user','content':json.dumps(state,ensure_ascii=False)}],'stream':False,'max_tokens':3000,'thinking':{'type':'disabled'},'response_format':{'type':'json_object'}}

    def extract(self,data):
        choices=data.get('choices',[])
        if not choices or choices[0].get('finish_reason') != 'stop':
            raise ValueError('Incomplete DeepSeek action')
        return choices[0]['message']['content']
