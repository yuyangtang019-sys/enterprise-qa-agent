import json
import os
import re
from pathlib import Path

def redact(value):
    if isinstance(value, dict):
        return {k: redact(v) for k,v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        for name in ('OPENAI_API_KEY','DEEPSEEK_API_KEY'):
            secret = os.getenv(name)
            if secret:
                value = value.replace(secret, '[REDACTED]')
        value = re.sub(r'(?i)Bearer\s+\S+|sk-[A-Za-z0-9_-]+', '[REDACTED]', value)
    return value

def save(path, trace):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(redact(trace), ensure_ascii=False, indent=2), encoding='utf-8')
