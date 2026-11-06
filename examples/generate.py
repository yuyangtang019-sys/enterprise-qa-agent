"""Execute reproducible offline scenarios and data mutation, never handwrite traces."""
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from enterprise_qa.agent import run
from enterprise_qa.knowledge import Knowledge
from enterprise_qa.models.mock import MockModel
from enterprise_qa.tracing import save

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/knowledge.json'

def main():
    scenarios=[('01-normal','上海出差住宿上限？',{},None,'answered'),('02-conflict','采购两万元需要谁审批？',{},None,'conflict_unresolved'),('03-outside','生育津贴有多少？',{},None,'insufficient_evidence'),('04-paraphrase','去上海住酒店最多能报多少',{},None,'answered'),('05-followup','那北京呢',{},[{'question':'上海住宿上限','answer':'历史回答不作为证据','dataset_digest':'old'}],'answered'),('06-tool-retry','远程双因素如何设置',{'read:SECURITY':1},None,'answered'),('07-tool-failure','远程双因素如何设置',{'read:SECURITY':-1},None,'tool_failure'),('08-clarification','住宿上限',{},None,'insufficient_evidence'),('09-limit','上海住宿',{},None,'step_limit')]
    summary=[]
    for name,q,f,h,expected in scenarios:
        t=run(MockModel(),Knowledge(DATA,f),q,h,2 if name=='09-limit' else 8)
        assert t['result']['outcome']==expected,(name,t)
        save(ROOT/'examples'/(name+'.json'),t)
        summary.append({'name':name,'input':q,'expected':expected,'actual':t['result']['outcome'],'status':t['result']['task_status'],'steps':len(t['steps']),'path':[s['action']['action'] for s in t['steps']]})
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'knowledge.json'; p.write_bytes(DATA.read_bytes()); kb=Knowledge(p)
        a=run(MockModel(),kb,'上海住宿')
        p.write_text(p.read_text(encoding='utf-8').replace('600元','720元'),encoding='utf-8')
        b=run(MockModel(),kb,'上海住宿',[{'question':'上海住宿','answer':a['result']['answer'],'dataset_digest':a['dataset_digest']}])
        assert '720' in b['result']['answer'] and a['dataset_digest']!=b['dataset_digest']
        save(ROOT/'examples/10-mutation-before.json',a); save(ROOT/'examples/10-mutation-after.json',b)
    save(ROOT/'examples/evaluation.json',{'mode':'mock','warning':'流程验证，不是真实模型质量评估','acceptance_status':'historical engineering evidence only; superseded by required real DeepSeek acceptance','cases':summary,'passed':len(summary),'mutation':'passed: 600 -> 720, fresh read and changed digest'})
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
