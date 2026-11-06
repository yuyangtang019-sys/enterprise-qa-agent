import argparse
import json
from pathlib import Path
from .knowledge import Knowledge
from .agent import run
from .models.mock import MockModel
from .models.real import RealModel
from .models.deepseek import DeepSeekModel
from .tracing import save
from . import session

def main():
    p = argparse.ArgumentParser(description='企业知识问答Agent；Mock仅验证流程')
    p.add_argument('question',nargs='?')
    p.add_argument('--mode',choices=['real','mock'],default='real')
    p.add_argument('--provider',choices=['deepseek','openai'],default='deepseek')
    p.add_argument('--data',default=str(Path(__file__).resolve().parents[2]/'data'/'knowledge.json'))
    p.add_argument('--trace',default='examples/latest-trace.json')
    p.add_argument('--session')
    p.add_argument('--chat',action='store_true')
    p.add_argument('--max-steps',type=int,default=8)
    p.add_argument('--fail-read',help='Mock only: document ID')
    p.add_argument('--fail-count',type=int,default=1,help='-1 means persistent')
    args = p.parse_args()
    try:
        if args.fail_read and args.mode != 'mock':
            raise ValueError('Fault injection requires explicit Mock mode')
        if args.fail_count == 0 or args.fail_count < -1:
            raise ValueError('fail-count must be positive or -1')
        model = MockModel() if args.mode=='mock' else DeepSeekModel() if args.provider=='deepseek' else RealModel()
        kb = Knowledge(args.data,{'read:'+args.fail_read:args.fail_count} if args.fail_read else {})
        history = session.load(args.session)
        q = args.question
        turn = 0
        while True:
            if q is None:
                if not args.chat:
                    p.error('question is required unless --chat')
                q = input('问题（/quit退出）> ')
            if q == '/quit':
                return 0
            trace = run(model,kb,q,history,args.max_steps)
            target = args.trace if turn == 0 else str(Path(args.trace).with_name(Path(args.trace).stem+f'-{turn}'+Path(args.trace).suffix))
            save(target,trace)
            print(json.dumps({'mode':model.mode,'notice':'MOCK：仅流程模拟，非真实模型效果' if model.mode=='mock' else '真实模型','result':trace['result'],'trace':target},ensure_ascii=False,indent=2))
            session.append(args.session,history,q,trace['result'],kb.digest)
            history = (history+[{'question':q,'answer':trace['result']['answer'],'dataset_digest':kb.digest}])[-20:]
            if not args.chat:
                return 0 if trace['result']['task_status']!='incomplete' else 2
            turn += 1
            q = None
    except (ValueError,OSError,EOFError):
        print('配置或输入错误：DeepSeek需要DEEPSEEK_API_KEY；OpenAI需要OPENAI_API_KEY和OPENAI_MODEL。请检查参数、数据或会话文件。不自动降级为Mock。')
        return 2
