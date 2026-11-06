"""Explicit deterministic simulator. Never evidence of real model quality."""
import re

def action(name, **kw):
    return {'action': name, 'purpose': '离线模拟：根据当前观察选择动作', **kw}

class MockModel:
    mode = 'mock'
    provider = 'offline simulator (NOT a language model)'
    name = 'observation-driven-mock-v1'
    def decide(self, instructions, state):
        a=self._decide(instructions,state)
        if a['action']=='finish':
            a['answer']=''
            a['claims']=[{'type':'quote','citation_id':c['citation_id']} for c in a['citations']]
            a['gaps']=[] if a['outcome']=='answered' else ['tool_failure' if a['outcome']=='tool_failure' else 'conflict' if a['outcome']=='conflict_unresolved' else 'missing_policy']
        return a
    def _decide(self, instructions, state):
        q = state['question']
        history = state['history']
        if '那北京' in q and history:
            q = history[-1]['question'] + ' 北京'
        steps = state['steps']
        reads = [s['observation'] for s in steps if s['observation'].get('ok') and s['observation'].get('tool')=='read']
        searched = [s for s in steps if s['action'] and s['action']['action']=='search']
        if steps and not steps[-1]['observation']['ok']:
            last = steps[-1]
            fails = sum(not s['observation']['ok'] for s in steps)
            if fails < 2 and last['action'] and last['action']['action'] in {'search','read'}:
                return dict(last['action'])
            return action('finish', outcome='tool_failure', answer='资料工具持续失败，无法确认答案。', citations=[], gaps=['原文未能读取，请稍后重试。'])
        topic = 'travel' if any(w in q for w in ['住宿','酒店','住酒店']) else 'purchase' if any(w in q for w in ['采购','审批']) else 'security' if any(w in q for w in ['双因素','远程','VPN']) else None
        if topic == 'travel' and not any(w in q for w in ['上海','北京']):
            return action('ask_user', question='请问出差城市是上海还是北京？', reason='需要城市以确认住宿限额。')
        query = {'travel':'差旅住宿','purchase':'采购审批','security':'远程双因素'}.get(topic,q)
        if not searched:
            return action('search', query=query)
        if topic is None:
            if len(searched)<2:
                return action('search', query='生育 医疗 津贴 报销' if '生育' in q else q+' 制度 适用范围')
            return action('finish', outcome='insufficient_evidence', answer='知识库没有足够资料回答该问题。', citations=[], gaps=['缺少该主题的正式制度及适用范围。'])
        wanted = {'travel':['TRAVEL-OLD','TRAVEL-NEW'],'purchase':['PROCUREMENT','FINANCE','RESOLUTION'],'security':['SECURITY']}[topic]
        ids = {e['document']['document_id'] for e in reads}
        # Only IDs observed in search results may be read by this simulator.
        hits = {h['document_id']:h for s in searched for h in s['observation'].get('hits',[])}
        for doc in wanted:
            if doc not in ids and doc in hits:
                return action('read',document_id=doc,fragment_id=hits[doc]['fragment_ids'][0])
        if any(doc not in ids for doc in wanted):
            if len(searched)<2:
                return action('search',query='冲突 优先 采购审批' if topic=='purchase' else query+' 替代')
            return action('finish',outcome='insufficient_evidence',answer='未找到完整的适用资料。',citations=[],gaps=['相关制度或优先关系缺失。'])
        def citation(e, number, quote=None):
            return {'citation_id':'C'+str(number),'document_id':e['document']['document_id'],'version':e['document']['version'],'fragment_id':e['fragment_id'],'quote':quote or e['text']}
        if topic == 'travel':
            e = next(e for e in reads if e['document']['document_id']=='TRAVEL-NEW')
            city = '北京' if '北京' in q else '上海'
            match = re.search(city+r'住宿上限[^。]*。',e['text'])
            if not match:
                return action('finish',outcome='insufficient_evidence',answer='现有原文未包含城市限额。',citations=[],gaps=['缺少城市限额。'])
            return action('finish',outcome='answered',answer=match.group()+'[C1] 本制度明确替代旧版。[C2]',citations=[citation(e,1,match.group()),citation(e,2,'本制度替代 TRAVEL-OLD。')],gaps=[])
        if topic == 'purchase':
            cs = [citation(e,i+1) for i,e in enumerate(reads)]
            return action('finish',outcome='conflict_unresolved',answer='同一范围采购审批存在冲突，当前资料未规定优先关系，请联系制度负责人确认。'+''.join('['+c['citation_id']+']' for c in cs),citations=cs,gaps=['缺少书面裁决或明确替代关系。'])
        e = reads[-1]
        return action('finish',outcome='answered',answer=e['text']+'[C1]',citations=[citation(e,1)],gaps=[])
