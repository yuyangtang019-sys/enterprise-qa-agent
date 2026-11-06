import json
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def new_run(root,kind,requested,expanded):
    path=root/'examples/runs'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:10])
    path.mkdir(parents=True)
    write(path/'manifest.json',{'kind':kind,'status':'incomplete','requested':requested,'expanded':expanded or requested,'executed':[],'skipped':expanded or requested,'mode':'real','dataset_digest':hashlib.sha256((root/'data/knowledge.json').read_bytes()).hexdigest(),'model':'deepseek-flash','max_steps':12})
    return path

def complete(path,records):
    manifest=json.loads((path/'manifest.json').read_text(encoding='utf-8'))
    manifest.update(status='completed' if records and all(r['passed'] for r in records) else 'failed',executed=[r['name'] for r in records])
    if not manifest['requested']: manifest['requested']=list(manifest['executed']); manifest['expanded']=list(manifest['executed'])
    manifest['skipped']=sorted(set(manifest['expanded'])-set(manifest['executed']))
    business=sum('trace' in r.get('response',{}) for r in records) if manifest['kind']=='http' else len(records)
    if manifest['kind']=='retrieval-stress': business=sum(r['name'].startswith('real-') for r in records)
    if manifest['skipped'] or len(manifest['executed'])!=len(set(manifest['executed'])): manifest['status']='failed'
    manifest.update(offline_checks=len(records)-business if manifest['kind']=='retrieval-stress' else 0,total=len(records),passed=sum(r['passed'] for r in records),business_cases=business,protocol_probes=len(records)-business if manifest['kind']=='http' else 0)
    write(path/'manifest.json',manifest)
    write(path.parents[1]/'latest-evaluation.json',{'run_directory':str(path.resolve()),'summary':manifest})

    return manifest['status']=='completed'
