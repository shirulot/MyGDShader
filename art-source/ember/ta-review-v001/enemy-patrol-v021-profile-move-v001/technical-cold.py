"""使用完整 ZIP 隔离副本及原导入设置执行最小资源/W/E CPU 读回。"""
from pathlib import Path
import json,hashlib,subprocess,time
OUT=Path(__file__).resolve().parent;P=OUT/'technical-cold-load'
ENGINE=Path('E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe')
assert not (P/'.godot').exists()
calls=[]
for name,args in [('import',['--headless','--path',str(P),'--editor','--import']),('probe',['--headless','--path',str(P),'--script','res://ta_probe.gd'])]:
    start=time.monotonic();stdout=OUT/f'technical-cold-{name}.stdout.log';stderr=OUT/f'technical-cold-{name}.stderr.log'
    with stdout.open('wb') as o,stderr.open('wb') as e:
        result=subprocess.run([str(ENGINE),*args],stdout=o,stderr=e,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
    calls.append({'call':name,'exit_code':result.returncode,'seconds':round(time.monotonic()-start,3),'stdout':stdout.name,'stderr':stderr.name,'stderr_bytes':stderr.stat().st_size})
    if result.returncode:raise RuntimeError(stdout.read_text(encoding='utf-8',errors='replace')+stderr.read_text(encoding='utf-8',errors='replace'))
probe=json.loads((OUT/'technical-minimal-cold-load.json').read_text());m=json.loads((P/'manifest.json').read_text())['files']
changes=[f for f,r in m.items() if hashlib.sha256((P/f).read_bytes()).hexdigest()!=r['sha256']]
assert not changes
receipt={'status':probe['status'],'initial_cache_absent':True,'complete_zip_copy':True,'payload_count':len(m),'payload_changes':changes,'calls':calls,'replayed_gpu':False,'replayed_player_matrix':False}
(OUT/'technical-cold-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt))
