import json
from pathlib import Path

def load(path):
    if not path or not Path(path).exists():
        return []
    h = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(h, list) or len(h) > 20 or any(not isinstance(x, dict) or set(x) != {'question','answer','dataset_digest'} or any(type(v) is not str or len(v)>12000 for v in x.values()) for x in h):
        raise ValueError('Invalid session')
    return h

def append(path, history, question, result, digest):
    if path:
        from .tracing import save
        save(path, (history + [{'question':question,'answer':result['answer'],'dataset_digest':digest}])[-20:])
