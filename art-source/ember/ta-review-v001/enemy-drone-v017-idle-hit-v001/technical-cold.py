"""只运行自己从固定ZIP创建的冷项目；不操作已有Godot编辑器。"""
from pathlib import Path
import subprocess,hashlib,json,zipfile,time
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
ZIP=ROOT/'art-source/ember/deliveries/enemy_drone_idle_hit_v017_v001_2026-10-07.zip'
PKG=OUT/'technical-cold-project'
ENGINE=Path('E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe')
assert not PKG.exists()
z=zipfile.ZipFile(ZIP)
for n in z.namelist():
 target=PKG/n;assert target.resolve().is_relative_to(PKG.resolve())
 target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(n))
assert not (PKG/'.godot').exists()
(PKG/'ta_probe.gd').write_bytes((OUT/'technical-probe.gd').read_bytes())
calls=[]
for name,args in [('import',['--headless','--path',str(PKG),'--editor','--import']),('probe',['--headless','--path',str(PKG),'--script','res://ta_probe.gd','--',str(OUT/'technical-cold-probe.json')])]:
 start=time.monotonic();stdout=OUT/('technical-'+name+'.stdout.log');stderr=OUT/('technical-'+name+'.stderr.log')
 with stdout.open('wb') as o,stderr.open('wb') as e:done=subprocess.run([str(ENGINE),*args],stdout=o,stderr=e,creationflags=subprocess.CREATE_NO_WINDOW,timeout=45)
 row={'call':name,'args':args,'exit_code':done.returncode,'seconds':round(time.monotonic()-start,3),'stdout_file':stdout.name,'stderr_file':stderr.name,'stderr_bytes':stderr.stat().st_size,'stdout_sha256':hashlib.sha256(stdout.read_bytes()).hexdigest(),'stderr_sha256':hashlib.sha256(stderr.read_bytes()).hexdigest()};calls.append(row);print(row)
 if done.returncode:raise RuntimeError(stdout.read_text(encoding='utf-8',errors='replace')+stderr.read_text(encoding='utf-8',errors='replace'))
probe=json.loads((OUT/'technical-cold-probe.json').read_text(encoding='utf-8-sig'));manifest=json.loads(z.read('manifest.json'))['files']
changed=[n for n,r in manifest.items() if hashlib.sha256((PKG/n).read_bytes()).hexdigest()!=r['sha256']]
receipt={'status':probe['status'],'initial_godot_cache_absent':True,'zip_sha256':hashlib.sha256(ZIP.read_bytes()).hexdigest(),'engine':str(ENGINE),'calls':calls,'passed':probe['passed'],'total':probe['total'],'probe_sha256':hashlib.sha256((OUT/'technical-cold-probe.json').read_bytes()).hexdigest(),'original_payloads':len(manifest),'payload_changes_after_import':changed,'ta_gpu_rerun':False,'author112_gpu32players16switch_suite_rerun':False}
(OUT/'technical-cold-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print('probe',probe['status'],probe['passed'],probe['total'])
