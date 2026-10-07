"""完整冻结ZIP隔离冷导入；只加入TA探针，不修改提交载荷。"""
from pathlib import Path
import json,hashlib,subprocess,time
OUT=Path(__file__).resolve().parent;P=OUT/'technical-cold-load'
ENGINE='E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe'
assert not (P/'.godot').exists()
(P/'ta_probe.gd').write_bytes((OUT/'ta_probe.gd').read_bytes())
calls=[]
for name,args in [('import',['--headless','--editor','--import','--quit']),('probe',['--headless','--script','res://ta_probe.gd'])]:
 start=time.monotonic();o=OUT/f'technical-cold-{name}.stdout.log';e=OUT/f'technical-cold-{name}.stderr.log'
 with o.open('wb')as of,e.open('wb')as ef:
  run=subprocess.run([ENGINE,'--path',str(P),*args],stdout=of,stderr=ef,creationflags=subprocess.CREATE_NO_WINDOW,timeout=120)
 calls.append({'call':name,'exit_code':run.returncode,'seconds':round(time.monotonic()-start,3),'stderr_bytes':e.stat().st_size})
 if run.returncode:raise RuntimeError(o.read_text(encoding='utf-8',errors='replace')+e.read_text(encoding='utf-8',errors='replace'))
result=json.loads((OUT/'technical-cold-result.json').read_text());files=json.loads((P/'manifest.json').read_text())['files']
changes=[n for n,r in files.items()if hashlib.sha256((P/n).read_bytes()).hexdigest()!=r['sha256']]
assert not changes
receipt={'status':result['status'],'calls':calls,'initial_cache_absent':True,'complete_zip':True,'payloads':len(files),'payload_changes':changes,'cells':len(result['cells']),'switches':len(result['switches']),'players':len(result['players']),'gpu_replayed':False}
(OUT/'technical-cold-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt))
