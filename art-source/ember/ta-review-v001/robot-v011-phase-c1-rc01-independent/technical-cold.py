"""独立从固定ZIP建冷工程；只运行headless导入与自有C1小探针。"""
from pathlib import Path
import subprocess,hashlib,json,zipfile,time
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
ZIP=ROOT/'art-source/ember/deliveries/robot_eight_way_v011_phase_c1_rc01_2026-10-07.zip';PKG=OUT/'technical-cold-project-r1'
ENGINE=Path('E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe')
assert not PKG.exists()
# 保存首次TA探针的类型声明错误日志；新冷项目验证修正后的自有探针。
for log in ['technical-import.stdout.log','technical-import.stderr.log','technical-probe.stdout.log','technical-probe.stderr.log']:
 if (OUT/log).is_file():(OUT/log.replace('technical-','technical-initial-')).write_bytes((OUT/log).read_bytes())
z=zipfile.ZipFile(ZIP)
for n in z.namelist():
 target=PKG/n;assert target.resolve().is_relative_to(PKG.resolve());target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(n))
project=PKG/'godot-action-review';assert not (project/'.godot').exists()
(project/'ta_probe.gd').write_bytes((OUT/'technical-probe.gd').read_bytes())
calls=[]
for name,args in [('import',['--headless','--path',str(project),'--editor','--import']),('probe',['--headless','--path',str(project),'--script','res://ta_probe.gd','--',str(OUT/'technical-cold-probe.json')])]:
 start=time.monotonic();stdout=OUT/('technical-'+name+'.stdout.log');stderr=OUT/('technical-'+name+'.stderr.log')
 with stdout.open('wb') as o,stderr.open('wb') as e:done=subprocess.run([str(ENGINE),*args],stdout=o,stderr=e,creationflags=subprocess.CREATE_NO_WINDOW,timeout=45)
 row={'call':name,'args':args,'exit_code':done.returncode,'seconds':round(time.monotonic()-start,3),'stdout_file':stdout.name,'stderr_file':stderr.name,'stderr_bytes':stderr.stat().st_size,'stdout_sha256':hashlib.sha256(stdout.read_bytes()).hexdigest(),'stderr_sha256':hashlib.sha256(stderr.read_bytes()).hexdigest()};calls.append(row);print(row)
 if done.returncode:raise RuntimeError(stdout.read_text(encoding='utf-8',errors='replace')+stderr.read_text(encoding='utf-8',errors='replace'))
probe=json.loads((OUT/'technical-cold-probe.json').read_text(encoding='utf-8-sig'));manifest=json.loads(z.read('sha256-manifest.json'))['files']
changed=[r['file'] for r in manifest if hashlib.sha256((PKG/r['file']).read_bytes()).hexdigest()!=r['sha256']]
receipt={'status':probe['status'],'initial_godot_cache_absent':True,'zip_sha256':hashlib.sha256(ZIP.read_bytes()).hexdigest(),'engine':str(ENGINE),'calls':calls,'passed':probe['passed'],'total':probe['total'],'probe_sha256':hashlib.sha256((OUT/'technical-cold-probe.json').read_bytes()).hexdigest(),'original_payloads':len(manifest),'payload_changes_after_import':changed,'ta_gpu_rerun':False,'author30_gpu_and_two_loop_suite_rerun':False,'actual_collect_to_idle0':probe['finish_state']}
(OUT/'technical-cold-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8');print('probe',probe['status'],probe['passed'],probe['total'])
