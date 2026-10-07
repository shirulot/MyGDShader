"""Independent full unzip cold load; original import settings are preserved."""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
import json
import hashlib
import subprocess
import time

out=Path(__file__).resolve().parent
root=out.parents[3]
archive=root/'art-source/ember/deliveries/robot_eight_way_v011_phase_c2_rc02_2026-10-07.zip'
package=out/'technical-cold-package'
engine=Path('E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe')
sha=lambda b:hashlib.sha256(b).hexdigest()
expected='64a3a18625dccc2fc1bde35ae44388a7acfb92ddb9aa4c83db811d2e5c10aa1b'
assert sha(archive.read_bytes())==expected
assert not package.exists()
with ZipFile(archive) as z:
    for info in z.infolist():
        if info.is_dir():continue
        name=PurePosixPath(info.filename)
        assert not name.is_absolute() and '..' not in name.parts and ':' not in info.filename
        p=package.joinpath(*name.parts)
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(z.read(info))
    manifest=json.loads(z.read('sha256-manifest.json'))['files']
project=package/'godot-full-review'
assert not (project/'.godot').exists()
assert (project/'assets/robot_eight_way_actions_atlas_v011.png.import').exists()
probe=(out.parent/'robot-v011-phase-c2-rc01-independent/technical-cold-probe.gd').read_text(encoding='utf-8')
probe=probe.replace('for direction:int in [0,4,6]:','for direction:int in [7]:')
probe=probe.replace('actual S/N/E collect','actual SE collect')
probe=probe.replace('res://../technical-minimal-cold-load.json','res://../../technical-minimal-cold-load.json')
(out/'technical-cold-probe.gd').write_text(probe,encoding='utf-8')
(project/'ta_minimal_load.gd').write_text(probe,encoding='utf-8')
calls=[]
for name,args in [('import',['--headless','--path',str(project),'--editor','--import']),('probe',['--headless','--path',str(project),'--script','res://ta_minimal_load.gd'])]:
    start=time.monotonic()
    stdout=out/f'technical-cold-{name}.stdout.log';stderr=out/f'technical-cold-{name}.stderr.log'
    with stdout.open('wb') as o,stderr.open('wb') as e:
        proc=subprocess.run([str(engine),*args],stdout=o,stderr=e,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
    calls.append({'call':name,'exit_code':proc.returncode,'seconds':round(time.monotonic()-start,3),'args':args,'stdout':stdout.name,'stderr':stderr.name,'stderr_bytes':stderr.stat().st_size})
    if proc.returncode:raise RuntimeError(stdout.read_text(encoding='utf-8',errors='replace')+stderr.read_text(encoding='utf-8',errors='replace'))
changed=[r['file'] for r in manifest if sha((package/r['file']).read_bytes())!=r['sha256']]
result=json.loads((out/'technical-minimal-cold-load.json').read_text(encoding='utf-8'))
assert not changed and result['status']=='PASS'
receipt={'status':result['status'],'source_zip_sha256':expected,'initial_godot_cache_absent':True,'original_import_settings_preserved':True,'original_payload_count':len(manifest),'payload_changes_after_import':changed,'calls':calls,'probe_sha256':sha((out/'technical-cold-probe.gd').read_bytes()),'result_sha256':sha((out/'technical-minimal-cold-load.json').read_bytes()),'replayed_gpu':False,'replayed_full_switch_matrix':False}
(out/'technical-cold-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
