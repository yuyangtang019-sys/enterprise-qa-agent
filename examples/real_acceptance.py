"""Real DeepSeek acceptance. User may input key privately in their own terminal."""
import argparse
from run_artifacts import new_run
import getpass
import json
import os
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from enterprise_qa.agent import run
from enterprise_qa.knowledge import Knowledge
from enterprise_qa.models.deepseek import DeepSeekModel
from enterprise_qa.tracing import save
from acceptance_checks import business_checks

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--prompt-key',action='store_true',help='Input key privately in your own terminal')
    args=parser.parse_args()
    if args.prompt_key:
        os.environ['DEEPSEEK_API_KEY']=getpass.getpass('DeepSeek API key (hidden, memory only): ')
    model=DeepSeekModel()
    out=new_run(ROOT,'cli',['normal','conflict','outside','paraphrase','followup','tool-retry','tool-failure','mutation'],[])
    data=ROOT/'data/knowledge.json'
    cases=[('normal','上海出差住宿上限？',{},'answered'),('conflict','单笔采购两万元需要谁审批？',{},'conflict_unresolved'),('outside','生育津贴有多少？',{},'insufficient_evidence'),('paraphrase','去上海住酒店最多能报多少钱？',{},'answered'),('followup','那北京呢',{},'answered'),('tool-retry','远程VPN是否必须启用双因素认证？遗失认证设备怎么办？',{'read:SECURITY':1},'answered'),('tool-failure','远程VPN是否必须启用双因素认证？',{'read:SECURITY':-1},'tool_failure')]
    results=[]; normal=None
    for name,q,failures,expected in cases:
        history=[{'question':'上海出差住宿上限？','answer':normal['result']['answer'],'dataset_digest':normal['dataset_digest']}] if name=='followup' else []
        trace=run(model,Knowledge(data,failures),q,history,max_steps=12)
        save(out/(name+'.json'),trace)
        if name=='normal': normal=trace
        check_name={'conflict':'conflict-pressure','tool-retry':'retry','tool-failure':'persistent'}.get(name,name)
        checks=business_checks(check_name,trace)
        checks['expected_outcome']=trace['result']['outcome']==expected
        results.append({'name':name,'expected':expected,'actual':trace['result']['outcome'],'status':trace['result']['task_status'],'checks':checks,'passed':all(checks.values())})
        print(name,trace['result']['task_status'],trace['result']['outcome'],flush=True)
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'data.json'; p.write_text(data.read_text(encoding='utf-8').replace('600元','720元'),encoding='utf-8')
        t=run(model,Knowledge(p),'上海出差住宿上限？',[{'question':'上海出差住宿上限？','answer':normal['result']['answer'],'dataset_digest':normal['dataset_digest']}],max_steps=12)
        save(out/'mutation.json',t)
        results.append({'name':'mutation','passed':'720' in t['result']['answer'] and normal['dataset_digest']!=t['dataset_digest']})
    save(out/'evaluation.json',{'mode':'real','provider':model.provider,'requested_model':model.requested_model,'api_model':model.name,'results':results,'note':'自动结果仅初筛，须人工核验语义支持和冲突查证；别名不能锁定后端快照。'})
    from run_artifacts import complete
    return 0 if complete(out,results) else 1

if __name__=='__main__': raise SystemExit(main())
