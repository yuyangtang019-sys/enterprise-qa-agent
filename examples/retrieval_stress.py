"""Seeded, temporary corpus experiment. Original knowledge files are untouched."""
import json
import random
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from enterprise_qa.knowledge import Knowledge
from enterprise_qa.agent import run
from enterprise_qa.models.deepseek import DeepSeekModel
from enterprise_qa.tracing import save
from run_artifacts import new_run, complete

ROOT=Path(__file__).resolve().parents[1]
def main():
    rng=random.Random(20261106)
    docs=[]
    for i in range(14):
        docs.append({'document_id':'R'+str(rng.randrange(100000,999999)),'title':'报销期限制度' if i<2 else '报销期限参考资料','version':'2026-01-01','effective_date':'2026-01-01','status':'active','scope':'全体员工费用报销','supersedes':[],'fragments':{'p1':('报销期限为'+('30' if i==0 else '15')+'天。') if i<2 else '本资料提到报销期限，但不规定报销期限，请查正式制度。'}})
    targets={d['document_id'] for d in docs[:2]}; records=[]
    out=new_run(ROOT,'retrieval-stress',['permutation-0','permutation-1','permutation-2','real-conflict'],[])
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'data.json'
        for i in range(3):
            rng.shuffle(docs);path.write_text(json.dumps(docs,ensure_ascii=False),encoding='utf-8'); kb=Knowledge(path)
            ids=set();offset=0
            while True:
                o=kb.execute({'action':'search','query':'报销期限','offset':offset,'dataset_digest':kb.digest})
                ids.update(h['document_id'] for h in o['hits'])
                if not o['has_more']: break
                offset=o['next_offset']
            records.append({'name':'permutation-'+str(i),'passed':targets<=ids,'reached_documents':len(ids),'target_ids':sorted(targets)})
        t=run(DeepSeekModel(),Knowledge(path),'报销期限多久？请查证全部有效制度，不要仅凭日期选一个。',max_steps=12)
        save(out/'real-conflict.json',t)
        actual={c['document_id'] for c in t['result']['citations']}
        records.append({'name':'real-conflict','passed':t['result']['outcome']=='conflict_unresolved' and targets<=actual,'actions':[s['action'] for s in t['steps']]})
    save(out/'evaluation.json',{'records':records});complete(out,records)
    print(out,[(r['name'],r['passed']) for r in records])
    return 0 if all(r['passed'] for r in records) else 1
if __name__=='__main__': raise SystemExit(main())
