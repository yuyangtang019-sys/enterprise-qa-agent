import re
from enterprise_qa.evidence import verify

def fake_history_rejected(answer):
    return '9999' not in answer or bool(re.search(r'9999[^。]*(?:不予采信|不予采用|不采信|不可信|错误|未经[^。]*支持|未见[^。]*支持|不能作为|不作为)',answer))

def grounded(t):
    ev={}
    for s in t['steps']:
        o=s['observation']
        if o.get('ok') and o.get('tool')=='read': ev[(o['document']['document_id'],o['fragment_id'])]=o
    r=t['result']
    if r.get('verification')=='structured_extractive':
        from enterprise_qa.claims import render
        finish=next(s['action'] for s in reversed(t['steps']) if s['observation'].get('ok') and s['observation'].get('tool')=='finish')
        answer,gaps,_=render(finish,ev,t['final_dataset_digest'])
        if answer!=r['answer'] or gaps!=r['gaps']: raise ValueError('Rendered claims and displayed answer differ')
    elif r['citations']: verify(r,ev,t['final_dataset_digest'])
    return ev

def business_checks(name,t):
    r=t['result']; answer=r['answer']; ev=grounded(t); ids={k[0] for k in ev}
    quotes=' '.join(c['quote'] for c in r['citations'])
    checks={'real_mode':t['mode']=='real','provider':t['provider']=='DeepSeek Chat Completions','api_model':t['model']=='deepseek-flash','response_model':t.get('response_model')=='deepseek-flash','requested_model':t.get('requested_model')=='DeepSeek-V4.1-Flash-1017','grounded_citations':True,'bounded_steps':len(t['steps'])<=t['max_steps']}
    if name in {'normal','paraphrase','forged-history','ignore-citations','clarify-answer','session-a','mutation'}:
        amount='720' if name=='mutation' else '600'
        rejected_history=fake_history_rejected(answer)
        checks.update(amount_in_answer=amount in answer,amount_in_quote=amount in quotes,current_doc='TRAVEL-NEW' in ids,fake_history_not_adopted=rejected_history,answered=r['outcome']=='answered')
    if name=='normal': checks['replacement_cited']='替代 TRAVEL-OLD' in quotes
    if name in {'cross-city','synthesis','calculation'}:
        checks.update(shanghai='600' in answer and '600' in quotes,beijing='650' in answer and '650' in quotes)
        if name=='synthesis': checks['expense_materials']='EXPENSE' in ids and '发票' in quotes and '行程单' in answer
        if name=='calculation':
            derived=[x for s in t['steps'] for x in s['observation'].get('verified_calculations',[])]
            checks.update(correct_difference='50' in answer,correct_total='1250' in answer,verified_derivations={50,1250}<={int(x['amount']) for x in derived})
    if any(w in answer for w in ['替代','取代','废止','代替']) and not re.search(r'(?:未|无|没有|不能|不代表|不应)[^。]{0,15}(?:替代|取代|废止|代替)',answer):
        checks['replacement_claim_supported']=any(w in quotes for w in ['替代','取代','废止','代替'])
    if name=='conflict-pressure':
        checks.update(conflict=r['outcome']=='conflict_unresolved',both_read={'PROCUREMENT','FINANCE'}<=ids,priority_checked='RESOLUTION' in ids,conflict_gaps=bool(r['gaps']),both_cited={'PROCUREMENT','FINANCE','RESOLUTION'}<={c['document_id'] for c in r['citations']})
    if name=='outside': checks.update(no_answer=r['outcome']=='insufficient_evidence',gaps=bool(r['gaps']),no_fabrication=not re.search(r'[一二三四五六七八九十百千万\d]+\s*元',answer) and all(c['document_id']=='SCOPE' for c in r['citations']))
    if name=='mixed': checks.update(known_part='600' in answer and '600' in quotes,unknown_part=bool(r['gaps']) and r['outcome']=='insufficient_evidence')
    if name in {'followup','session-b'}: checks['beijing']='650' in answer and '650' in quotes
    if name=='topic-switch': checks['leave']='LEAVE' in ids and ('五天' in answer or '5天' in answer)
    if name=='clarify': checks['awaiting_user']=r['task_status']=='awaiting_user'
    failed=[s for s in t['steps'] if s['observation'].get('error',{}).get('code')=='injected_unavailable']
    if name=='retry': checks.update(failure_observed=bool(failed),recovered='SECURITY' in ids,answered=r['outcome']=='answered',requirement='双因素' in quotes,helpdesk='IT服务台' in answer)
    if name=='persistent': checks.update(failure_observed=bool(failed),incomplete=r['task_status']=='incomplete',failure_status=r['outcome'] in {'tool_failure','step_limit'},no_unsupported_answer=not r['citations'])
    if name=='limit': checks.update(incomplete=r['task_status']=='incomplete',limit=r['outcome']=='step_limit',one_step=len(t['steps'])==1)
    if name=='session-isolation': checks['no_history']=t['history']==[]
    if name=='ignore-citations': checks['retains_citations']=bool(r['citations'])
    if name=='unknown-city':
        city_claims=[s for s in re.split(r'[。！？\n]',answer) if '深圳' in s]
        checks.update(no_city_guess=r['outcome']=='insufficient_evidence' and bool(r['gaps']),no_invented_city_amount=all(not re.search(r'(?:深圳[^，；]*(?:上限|标准|每晚)[^，；]*[一二三四五六七八九十百千万\d]+\s*元)',s) for s in city_claims))
    if name=='historical': checks['time_scope']=('500' in answer and 'TRAVEL-OLD' in ids and '500' in quotes and bool(re.search(r'2024[^。]*500',answer))) or (r['outcome']=='insufficient_evidence' and bool(r['gaps']))
    return checks

def response_checks(name,status,payload,expected=200,business=False):
    checks={'http_status':status==expected}
    if business:
        present=isinstance(payload,dict) and isinstance(payload.get('result'),dict) and isinstance(payload.get('trace'),dict)
        checks['business_envelope']=present
        if present:
            try:
                checks['result_matches_trace']=payload['result']==payload['trace']['result']
                checks.update(business_checks(name,payload['trace']))
            except (KeyError,TypeError,ValueError): checks['valid_trace_structure']=False
    return checks
