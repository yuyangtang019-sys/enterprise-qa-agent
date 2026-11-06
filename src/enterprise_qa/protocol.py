import json
import re

SCHEMAS = {
    'search': {'query': str},
    'read': {'document_id': str, 'fragment_id': str},
    'ask_user': {'question': str, 'reason': str},
    'finish': {'outcome': str, 'answer': str, 'citations': list, 'gaps': list},
}
OUTCOMES = {'answered', 'insufficient_evidence', 'conflict_unresolved', 'tool_failure'}

def validate(raw):
    a = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(a, dict) or a.get('action') not in SCHEMAS:
        raise ValueError('Unknown action')
    fields = {'action': str, 'purpose': str, **SCHEMAS[a['action']]}
    if a['action']=='finish' and 'claims' in a:
        fields['claims']=list
    if a['action']=='search' and 'offset' in a:
        fields['offset']=int
    if a['action']=='search' and 'dataset_digest' in a: fields['dataset_digest']=str
    if set(a) != set(fields):
        raise ValueError('Missing or unknown action fields')
    for k, t in fields.items():
        if type(a[k]) is not t:
            raise ValueError('Invalid field type: ' + k)
        if t is str and not (k=='answer' and 'claims' in a and a[k]=='') and not 0 < len(a[k].strip()) <= (6000 if k == 'answer' else 500):
            raise ValueError('Empty or oversized field: ' + k)
    if a['action']=='search' and 'offset' in a and not 0<=a['offset']<=1000: raise ValueError('invalid_offset')
    if a['action'] == 'finish':
        if 'claims' in a and (len(a['claims'])>12 or any(type(c) is not dict for c in a['claims'])): raise ValueError('invalid_claims')
        if a['outcome'] not in OUTCOMES or len(a['citations']) > 12 or len(a['gaps']) > 12:
            raise ValueError('Invalid finish outcome or list limits')
        if any(type(g) is not str or not 0 < len(g) <= 500 for g in a['gaps']):
            raise ValueError('Invalid gap')
        for c in a['citations']:
            if not isinstance(c, dict) or set(c) != {'citation_id','document_id','version','fragment_id','quote'}:
                raise ValueError('Invalid citation fields')
            if any(type(v) is not str or not 0 < len(v) <= 2000 for v in c.values()):
                raise ValueError('Invalid citation values')
            if not re.fullmatch(r'C[1-9][0-9]*', c['citation_id']):
                raise ValueError('Invalid citation marker')
    return a

def error(tool, code, retryable=False):
    return {'ok': False, 'tool': tool, 'error': {'code': code, 'message': code, 'retryable': retryable}}
