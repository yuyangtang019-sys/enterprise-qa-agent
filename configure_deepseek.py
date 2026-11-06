"""Run privately in your terminal; never paste API keys into chat or shell commands."""
import getpass
from pathlib import Path

def main():
    key=getpass.getpass('DeepSeek API key (hidden): ').strip()
    if not key or any(c.isspace() for c in key):
        raise SystemExit('Invalid key format; nothing saved.')
    target=Path(__file__).resolve().parent/'.env.local'
    target.write_text('DEEPSEEK_API_KEY='+key+'\nDEEPSEEK_MODEL=deepseek-flash\nDEEPSEEK_BASE_URL=https://api.deepseek.com\n',encoding='utf-8')
    print('Saved local configuration to .env.local (Git ignored). Key is never printed.')

if __name__=='__main__': main()
