"""真实GPU入口仅在完整ZIP隔离副本；导入配置完整保留。"""
from pathlib import Path
import subprocess,time,json,hashlib
OUT=Path(__file__).resolve().parent;COLD=OUT/'technical-cold-load';P=COLD/'runtime'
assert not (P/'.godot').exists()
(P/'ta_probe.gd').write_bytes((OUT/'technical-cold-probe.gd').read_bytes())
engine='E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe'
calls=[]
for name,args in [('import',['--headless','--path',str(P),'--editor','--import','--quit']),('entry',['--path',str(P),'--position','-32000,-32000','--resolution','960x640','--rendering-method','gl_compatibility','--script','res://ta_probe.gd'])]:
    stdout,stderr=OUT/f'technical-cold-{name}.stdout.log',OUT/f'technical-cold-{name}.stderr.log';start=time.monotonic()
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
    with stdout.open('wb') as o,stderr.open('wb') as e:proc=subprocess.run([engine,*args],stdout=o,stderr=e,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW,startupinfo=startup)
    calls.append({'name':name,'exit_code':proc.returncode,'seconds':round(time.monotonic()-start,3),'stderr_bytes':stderr.stat().st_size,'args':args})
    if proc.returncode:
        (OUT/'technical-cold-failed.json').write_text(json.dumps(calls,indent=2));raise RuntimeError(stderr.read_text(encoding='utf-8',errors='replace'))
manifest=json.loads((COLD/'sha256-manifest.json').read_text())['files'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changes=[r['file'] for r in manifest if sha(COLD/r['file'])!=r['sha256']];result=json.loads((OUT/'technical-runtime-entry.json').read_text())
receipt={'status':result['status'],'complete_zip':True,'initial_cache_absent':True,'payloads':698,'payload_changes':changes,'calls':calls,'replayed_author64_gpu':False,'independent_gpu_samples':len(result['independent_gpu_samples']),'natural_collect_recoveries':len(result['recoveries'])}
(OUT/'technical-cold-receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt));assert receipt['status']=='PASS' and not changes
