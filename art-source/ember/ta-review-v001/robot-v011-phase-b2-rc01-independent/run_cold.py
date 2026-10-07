"""从固定ZIP创建自己的冷包，原工程与作者缓存不参与本轮验证。"""
from pathlib import Path
import subprocess, hashlib, json, zipfile, time
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
ZIP=ROOT/'art-source/ember/deliveries/robot_eight_way_v011_phase_b2_rc01_2026-10-07.zip'
PKG=OUT/'cold-project'
ENGINE=Path('E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe')
assert not PKG.exists(), 'Do not reuse an imported project as cold evidence.'
z=zipfile.ZipFile(ZIP)
for item in z.infolist():
 target=PKG/item.filename
 assert target.resolve().is_relative_to(PKG.resolve())
 if item.is_dir():target.mkdir(parents=True,exist_ok=True)
 else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(item))
project=PKG/'godot-walk-review'
assert not (project/'.godot').exists()
(project/'ta_probe.gd').write_bytes((OUT/'probe_cold.gd').read_bytes())
spec=json.loads((PKG/'walk-batch-metadata.json').read_text(encoding='utf-8-sig'))
for c in spec['clips']:
 for frame in c['frames']:frame['absolute_file']=str((PKG/frame['file']).resolve())
(OUT/'cold-spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
calls=[]
for name,args in [('import',['--headless','--path',str(project),'--editor','--import']),('probe',['--headless','--path',str(project),'--script','res://ta_probe.gd','--',str(OUT/'cold-spec.json'),str(OUT/'cold-probe.json')])]:
 start=time.monotonic();stdout=OUT/(name+'.stdout.log');stderr=OUT/(name+'.stderr.log')
 with stdout.open('wb') as o,stderr.open('wb') as e:
  proc=subprocess.run([str(ENGINE),*args],stdout=o,stderr=e,creationflags=subprocess.CREATE_NO_WINDOW,timeout=45)
 row={'call':name,'args':args,'exit_code':proc.returncode,'seconds':round(time.monotonic()-start,3),'stdout_file':stdout.name,'stderr_file':stderr.name,'stderr_bytes':stderr.stat().st_size,'stdout_sha256':hashlib.sha256(stdout.read_bytes()).hexdigest(),'stderr_sha256':hashlib.sha256(stderr.read_bytes()).hexdigest()}
 calls.append(row);print(row)
 if proc.returncode:raise RuntimeError(stdout.read_text(encoding='utf-8',errors='replace')+stderr.read_text(encoding='utf-8',errors='replace'))
probe=json.loads((OUT/'cold-probe.json').read_text(encoding='utf-8-sig'))
manifest=json.loads(z.read('sha256-manifest.json'))['files'];same=[]
for r in manifest:
 if hashlib.sha256((PKG/r['file']).read_bytes()).hexdigest()!=r['sha256']:same.append(r['file'])
receipt={'status':probe['status'],'initial_godot_cache_absent':True,'zip_sha256':hashlib.sha256(ZIP.read_bytes()).hexdigest(),'engine':str(ENGINE),'calls':calls,'independent_checks_passed':probe['passed'],'independent_checks_total':probe['total'],'probe_sha256':hashlib.sha256((OUT/'cold-probe.json').read_bytes()).hexdigest(),'original_payloads':len(manifest),'payload_mismatches_after_import':same,'ta_gpu_rerun':False,'author144_gpu_or_8direction2loop64turn_suite_rerun':False}
(OUT/'cold-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print('probe',probe['status'],probe['passed'],probe['total'])
