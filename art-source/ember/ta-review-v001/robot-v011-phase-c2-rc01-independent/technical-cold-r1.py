"""从固定 ZIP 完整新建无缓存隔离目录，保留首次 TA 拷贝缺 import 配置的失败证据。"""
from pathlib import Path
from zipfile import ZipFile
import json, hashlib, subprocess, time

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
ZIP=ROOT/'art-source/ember/deliveries/robot_eight_way_v011_phase_c2_rc01_2026-10-07.zip'
PKG=OUT/'technical-cold-package-r1'
ENGINE=Path('E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe')
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(ZIP.read_bytes())=='e0a5fe91bcd62509d0f342e45334ce34cf374ebea1ac0203162d9b90f79b5643'
assert not PKG.exists()
z=ZipFile(ZIP)
for n in z.namelist():
    f=PKG/n
    assert f.resolve().is_relative_to(PKG.resolve())
    f.parent.mkdir(parents=True,exist_ok=True)
    f.write_bytes(z.read(n))
project=PKG/'godot-full-review'
assert not (project/'.godot').exists()
probe=(OUT/'technical-cold-probe.gd').read_text(encoding='utf-8').replace('res://../technical-minimal-cold-load.json','res://../../technical-minimal-cold-load-r1.json')
(project/'ta_minimal_load.gd').write_text(probe,encoding='utf-8')
calls=[]
for name,args in [('import',['--headless','--path',str(project),'--editor','--import']),('probe',['--headless','--path',str(project),'--script','res://ta_minimal_load.gd'])]:
    start=time.monotonic()
    stdout=OUT/f'technical-cold-r1-{name}.stdout.log'
    stderr=OUT/f'technical-cold-r1-{name}.stderr.log'
    with stdout.open('wb') as o,stderr.open('wb') as e:
        result=subprocess.run([str(ENGINE),*args],stdout=o,stderr=e,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
    calls.append({'call':name,'args':args,'exit_code':result.returncode,'seconds':round(time.monotonic()-start,3),'stdout':stdout.name,'stderr':stderr.name,'stderr_bytes':stderr.stat().st_size})
    if result.returncode:
        raise RuntimeError(stdout.read_text(encoding='utf-8',errors='replace')+stderr.read_text(encoding='utf-8',errors='replace'))
manifest=json.loads(z.read('sha256-manifest.json'))['files']
changes=[r['file'] for r in manifest if sha((PKG/r['file']).read_bytes())!=r['sha256']]
result=json.loads((OUT/'technical-minimal-cold-load-r1.json').read_text(encoding='utf-8'))
receipt={'status':result['status'],'source_zip_sha256':sha(ZIP.read_bytes()),'initial_godot_cache_absent':True,'original_payload_count':len(manifest),'payload_changes_after_import':changes,'calls':calls,'probe_sha256':sha((OUT/'technical-minimal-cold-load-r1.json').read_bytes()),'reason_for_repeat':'Initial TA selected-file cold copy omitted the delivered .png.import file; it auto-created fix_alpha_border=true instead of delivered false. All initial logs/FAIL JSON retained. R1 extracts all payloads from ZIP and uses original import settings.','replayed_gpu':False,'replayed_full_switch_matrix':False}
assert not changes
(OUT/'technical-cold-r1-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
