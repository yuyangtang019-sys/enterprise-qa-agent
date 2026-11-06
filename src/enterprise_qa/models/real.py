import json
import os
import time
import urllib.request
import urllib.error
from urllib.parse import urlsplit

class RealModel:
    mode = 'real'
    provider = 'OpenAI Responses API'
    def __init__(self, key=None, model=None, base_url=None, timeout=30, retries=1):
        self.key = key or os.getenv('OPENAI_API_KEY')
        self.name = model or os.getenv('OPENAI_MODEL')
        self.base_url = (base_url or os.getenv('OPENAI_BASE_URL') or 'https://api.openai.com/v1').rstrip('/')
        if not self.key or not self.name:
            raise ValueError('Real mode requires OPENAI_API_KEY and OPENAI_MODEL; no automatic Mock fallback')
        u = urlsplit(self.base_url)
        if u.username or u.password or u.query or u.fragment or (u.scheme != 'https' and not (u.scheme=='http' and u.hostname in {'127.0.0.1','localhost'})):
            raise ValueError('Endpoint must use HTTPS (HTTP loopback allowed for tests)')
        if not 0 <= retries <= 2 or not 0 < timeout <= 120:
            raise ValueError('Invalid retry or timeout bound')
        self.timeout, self.retries, self.attempts = timeout, retries, 0
        self.error_code = None

    def payload(self,instructions,state):
        return {'model':self.name,'instructions':instructions,'input':json.dumps(state,ensure_ascii=False),'store':False,'max_output_tokens':3000}

    endpoint = '/responses'

    def extract(self,data):
        if data.get('status') != 'completed':
            raise ValueError('Incomplete model response')
        return ''.join(c['text'] for o in data.get('output',[]) if o.get('type')=='message' for c in o.get('content',[]) if c.get('type')=='output_text')

    def decide(self, instructions, state):
        self.error_code = None
        payload = json.dumps(self.payload(instructions,state)).encode()
        for i in range(self.retries+1):
            self.attempts = i+1
            req = urllib.request.Request(self.base_url+self.endpoint,data=payload,headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
            try:
                # Reject redirects to avoid forwarding credentials to a different endpoint.
                class NoRedirect(urllib.request.HTTPRedirectHandler):
                    def redirect_request(self, *args, **kwargs):
                        return None
                with urllib.request.build_opener(NoRedirect).open(req,timeout=self.timeout) as r:
                    data = json.loads(r.read(2_000_001))
                self.response_model = data.get('model')
                text = self.extract(data)
                if not text or len(text)>30000:
                    raise ValueError('Missing or oversized model action')
                return text
            except urllib.error.HTTPError as e:
                self.error_code = 'authentication_failed' if e.code in {401,403} else 'http_'+str(e.code)
                e.close()
                if e.code not in {429,500,502,503,504} or i == self.retries:
                    raise RuntimeError('Model HTTP failure') from None
            except (TimeoutError, urllib.error.URLError):
                self.error_code = 'transport_timeout_or_unavailable'
                if i == self.retries:
                    raise RuntimeError('Model transport failure') from None
            time.sleep(min(0.2 * (2**i), 1))
