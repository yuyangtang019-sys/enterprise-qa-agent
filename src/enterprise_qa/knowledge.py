import math
from collections import Counter
from .claims import facts
import hashlib
import json
import re
from pathlib import Path
from .protocol import error

def grams(s):
    s = re.sub(r'\s+', '', s.lower())
    return {s[i:i+2] for i in range(max(0, len(s)-1))}

class Knowledge:
    def __init__(self, path, failures=None):
        self.path = Path(path)
        self.failures = dict(failures or {})
        self.refresh()

    def refresh(self):
        raw = self.path.read_bytes()
        self.digest = hashlib.sha256(raw).hexdigest()
        docs = json.loads(raw)
        self.docs = {d['document_id']: d for d in docs}
        if len(docs) != len(self.docs):
            raise ValueError('Duplicate document ID')
        for d in docs:
            for key in ('version','effective_date','scope','status','supersedes','fragments','title'):
                if key not in d:
                    raise ValueError('Missing document metadata')
            if not d['fragments'] or any(not isinstance(v, str) or not v for v in d['fragments'].values()):
                raise ValueError('Invalid fragments')

    def execute(self, action):
        tool = action['action']
        key = tool + ':' + action.get('document_id', '*')
        key = key if key in self.failures else tool + ':*'
        count = self.failures.get(key, 0)
        if count:
            if count > 0:
                self.failures[key] -= 1
            return error(tool, 'injected_unavailable', True)
        if tool == 'search':
            query=action['query']; q=grams(query); rows=[]
            for d in self.docs.values():
                for fid,text in d['fragments'].items():
                    searchable=d['title']+' '+d['scope']+' '+text
                    rows.append((d,fid,text,grams(searchable),Counter(searchable.lower())))
            ranked=[]
            for route in (0,1):
                scored=[]
                for i,(_,_,_,g,counts) in enumerate(rows):
                    score=len(q & g) if route==0 else sum((1+math.log(counts[c]))*math.log(1+len(rows)/(1+sum(c in r[4] for r in rows))) for c in set(query.lower()) if c in counts)
                    if score>0: scored.append((i,score))
                ranked.append(sorted(scored,key=lambda x:(-x[1],rows[x[0]][0]['document_id'],rows[x[0]][1])))
            merged={}
            for route,ranking in enumerate(ranked):
                for rank,(i,score) in enumerate(ranking,1):
                    entry=merged.setdefault(i,{'rrf':0,'routes':{}}); entry['rrf']+=1/(60+rank); entry['routes'][str(route)]={'rank':rank,'score':score}
            indices=sorted(merged,key=lambda i:(-merged[i]['rrf'],rows[i][0]['document_id'],rows[i][1]))
            hits=[]
            for i in indices:
                d,fid,text,_,_=rows[i]
                hits.append({'document_id':d['document_id'],'version':d['version'],'title':d['title'],'scope':d['scope'],'status':d['status'],'effective_date':d['effective_date'],'supersedes':d['supersedes'],'fragment_ids':[fid],'summary':text[:180],'score':merged[i]['rrf'],'ranking':merged[i]['routes']})
            offset=action.get('offset',0)
            if offset and action.get('dataset_digest')!=self.digest: return error(tool,'pagination_digest_required_or_changed')
            if offset>=len(hits) and offset: return error(tool,'offset_out_of_range')
            page=hits[offset:offset+6]
            return {'ok':True,'tool':tool,'hits':page,'total_candidates':len(hits),'has_more':offset+6<len(hits),'next_offset':offset+6 if offset+6<len(hits) else None,'dataset_digest':self.digest,'related_candidates':[h for h in hits if h not in page and any(h['scope']==p['scope'] or h['document_id'] in p['supersedes'] or p['document_id'] in h['supersedes'] for p in page)][:12]}
        d = self.docs.get(action['document_id'])
        if not d or action['fragment_id'] not in d['fragments']:
            return error(tool, 'not_found')
        observation={'ok': True, 'tool': tool, 'document': {k:v for k,v in d.items() if k != 'fragments'}, 'fragment_id': action['fragment_id'], 'text': d['fragments'][action['fragment_id']], 'dataset_digest': self.digest}

        observation['numeric_facts']=facts(observation)
        return observation
