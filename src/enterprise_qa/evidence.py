import re

def verify(action, evidence, digest):
    cs = action['citations']
    ids = [c['citation_id'] for c in cs]
    if len(set(ids)) != len(ids) or set(re.findall(r'\[(C[0-9]+)\]', action['answer'])) != set(ids):
        raise ValueError('Citation markers do not match')
    if action['outcome'] in {'answered','conflict_unresolved'} and not cs:
        raise ValueError('Answer requires read evidence')
    if action['outcome'] != 'answered' and not action['gaps']:
        raise ValueError('Non-answer requires evidence gaps')
    for sentence in re.split(r'[。！？\n]',action['answer']):
        if re.search(r'替代|取代|废止|代替',sentence) and not re.search(r'(?:未|无|没有|不能|不代表|不应)[^。]{0,15}(?:替代|取代|废止|代替)',sentence) and not any(re.search(r'替代|取代|废止|代替',c['quote']) for c in cs):
            raise ValueError('Replacement claim requires a supporting replacement quote')
    quoted_amounts=set(re.findall(r'(\d+)\s*元',' '.join(c['quote'] for c in cs)))
    derived=[]
    for sentence in re.split(r'[。！？\n]',action['answer']):
        if re.search(r'不予采用|不予采信|不采信|未经[^。]*支持|未见[^。]*支持',sentence):
            continue
        for amount in set(re.findall(r'(\d+)\s*元',sentence))-quoted_amounts:
            found=None
            for left in quoted_amounts:
                for right in quoted_amounts:
                    if left==right: continue
                    if re.search(r'比[^。]*(?:高|低)|相差|差额',sentence) and abs(int(left)-int(right))==int(amount):
                        found={'operation':'absolute_difference','operands':sorted([int(left),int(right)]),'amount':int(amount),'unit':'元'}
                    if re.search(r'合计|总计|总共',sentence) and int(left)+int(right)==int(amount):
                        found={'operation':'sum','operands':sorted([int(left),int(right)]),'amount':int(amount),'unit':'元'}
            if found is None: raise ValueError('Monetary claim requires a supporting amount quote')
            derived.append(found)
    for c in cs:
        e = evidence.get((c['document_id'], c['fragment_id']))
        if not e or e['dataset_digest'] != digest or c['version'] != e['document']['version'] or c['quote'] not in e['text']:
            raise ValueError('Citation not grounded in current successful read')
    return derived
