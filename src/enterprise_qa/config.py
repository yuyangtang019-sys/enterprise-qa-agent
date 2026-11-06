import os
from pathlib import Path

def load_local():
    """Read only three allowlisted settings; environment takes precedence. No shell eval."""
    path=Path(__file__).resolve().parents[2]/'.env.local'
    if not path.exists(): return
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.lstrip().startswith('#'): continue
        name,sep,value=line.partition('=')
        if not sep or name not in {'DEEPSEEK_API_KEY','DEEPSEEK_MODEL','DEEPSEEK_BASE_URL'} or not value.strip():
            raise ValueError('Invalid local configuration')
        os.environ.setdefault(name,value.strip())
