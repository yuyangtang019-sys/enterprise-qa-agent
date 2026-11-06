"""Bounded, extractive claims. No arbitrary model prose is rendered as verified facts."""
import hashlib
import json
import re
from decimal import Decimal

GAPS={'missing_policy':'缺少所问主题的制度资料。','missing_scope':'缺少适用范围或城市信息。','conflict':'制度存在冲突，需向制度负责人确认适用关系。','tool_failure':'原文工具不可用，任务未完成。','missing_detail':'现有原文没有所需细节。'}

def facts(observation):
    result=[]
    d=observation['document']
    patterns=[r'(?P<subject>[^。！？\n，；]+?)住宿上限(?P<basis>每晚)(?P<value>\d+(?:\.\d+)?)元[。！？]',r'(?P<subject>报销)期限为(?P<value>\d+(?:\.\d+)?)天[。！？]']
    for pattern in patterns:
        for m in re.finditer(pattern,observation['text']):
            fid=hashlib.sha256(json.dumps([observation['dataset_digest'],d['document_id'],d['version'],observation['fragment_id'],m.start(),m.end()]).encode()).hexdigest()[:16]
            result.append({'fact_id':fid,'document_id':d['document_id'],'fragment_id':observation['fragment_id'],'version':d['version'],'dataset_digest':observation['dataset_digest'],'source_quote':m.group(),'span':[m.start(),m.end()],'subject':m['subject'],'attribute':'住宿上限' if '住宿' in m.group() else '报销期限','value':m['value'],'unit':'元' if '住宿' in m.group() else '天','basis':m.groupdict().get('basis') or '期限','scope':d['scope'],'effective_date':d['effective_date'],'status':d['status']})
    return result

def render(action,evidence,digest):
    if action['answer']!='': raise ValueError('structured_finish_requires_empty_answer')
    if action['outcome']!='answered' and not action['gaps']: raise ValueError('gap_required')
    cs=action['citations']; lookup={c['citation_id']:c for c in cs}
    if len(lookup)!=len(cs): raise ValueError('duplicate_citation')
    for c in cs:
        e=evidence.get((c['document_id'],c['fragment_id']))
        if not e or e['dataset_digest']!=digest or c['version']!=e['document']['version'] or c['quote'] not in e['text']: raise ValueError('citation_not_read')
        # Whole sentences/whole fragments prevent dropping a negation prefix.
        start=e['text'].find(c['quote']); end=start+len(c['quote'])
        if (start and e['text'][start-1] not in '。！？\n') or (end<len(e['text']) and c['quote'][-1] not in '。！？\n'): raise ValueError('quote_requires_sentence_boundary')
    allfacts={f['fact_id']:f for e in evidence.values() for f in facts(e)}
    lines=[]; calculations=[]; used=set()
    for claim in action['claims']:
        kind=claim.get('type')
        if kind=='quote' and set(claim)=={'type','citation_id'}:
            c=lookup[claim['citation_id']]; e=evidence[(c['document_id'],c['fragment_id'])]; d=e['document']
            lines.append(f"{d['title']}（{d['document_id']}，版本{d['version']}，范围{d['scope']}）：{c['quote']}[{c['citation_id']}]")
            used.add(c['citation_id'])
        elif kind=='replacement' and set(claim)=={'type','citation_id','source_document_id','target_document_id'}:
            c=lookup[claim['citation_id']]; e=evidence[(c['document_id'],c['fragment_id'])]
            source,target=claim['source_document_id'],claim['target_document_id']
            if source!=c['document_id'] or target not in e['document']['supersedes'] or not re.search(r'(?:^|[。！？])本制度替代 '+re.escape(target)+r'。',c['quote']): raise ValueError('replacement_direction_unsupported')
            lines.append(f"{source} 替代 {target}。[{c['citation_id']}]"); used.add(c['citation_id'])
        elif kind=='arithmetic' and set(claim)=={'type','operation','left_fact_id','right_fact_id','expected_value'}:
            left,right=allfacts[claim['left_fact_id']],allfacts[claim['right_fact_id']]
            for f in (left,right):
                matches=[c['citation_id'] for c in cs if c['document_id']==f['document_id'] and c['fragment_id']==f['fragment_id'] and f['source_quote'] in c['quote']]
                if not matches: raise ValueError('operand_not_cited')
                used.update(matches)
            if any(left[k]!=right[k] for k in ('attribute','unit','basis','scope','effective_date','status')): raise ValueError('incompatible_operands')
            if left['fact_id']==right['fact_id']: raise ValueError('distinct_operand_facts_required')
            op=claim['operation']; a,b=Decimal(left['value']),Decimal(right['value'])
            value=a+b if op=='sum' else a-b if op=='difference' else None
            if value is None or value!=Decimal(str(claim['expected_value'])): raise ValueError('arithmetic_mismatch')
            lines.append(f"依据引文计算：{left['subject']} {left['value']}{left['unit']} {'+' if op=='sum' else '-'} {right['subject']} {right['value']}{right['unit']} = {value}{left['unit']}（{'合计' if op=='sum' else '左项减右项，保留方向'}）。"+''.join('['+x+']' for x in sorted(used)))
            calculations.append({'operation':op,'left_fact_id':left['fact_id'],'right_fact_id':right['fact_id'],'amount':str(value),'unit':left['unit']})
        else: raise ValueError('invalid_claim')
    if used!=set(lookup): raise ValueError('unused_citation')
    if action['outcome'] in {'answered','conflict_unresolved'} and not lines: raise ValueError('claims_required')
    if action['outcome']=='conflict_unresolved': lines.append(GAPS['conflict'])
    gaps=[GAPS[g] for g in action['gaps']]
    if not lines: lines.append('资料不足。' if action['outcome']!='tool_failure' else GAPS['tool_failure'])
    return '\n'.join(lines),gaps,calculations
