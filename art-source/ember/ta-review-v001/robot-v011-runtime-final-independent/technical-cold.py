"""TA 自有冷解压/导入/实际入口验证，仅改新建的独立审查副本。"""
from pathlib import Path,PurePosixPath
from zipfile import ZipFile
import subprocess,json,hashlib,time
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
archive=ROOT/'art-source/ember/deliveries/robot_eight_way_v011_final_2026-10-07.zip'
package=OUT/'technical-cold-runtime-r2'
engine=Path('E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe')
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(archive.read_bytes())=='8dc65a715b41b2c61a09eb6e2afbcd31134db60228f4b3081a0a39e4d153f4bb'
assert not package.exists()
with ZipFile(archive) as z:
    manifest=json.loads(z.read('sha256-manifest.json'))['files']
    for info in z.infolist():
        if info.is_dir():continue
        parts=PurePosixPath(info.filename)
        assert not parts.is_absolute() and '..' not in parts.parts and ':' not in info.filename
        dst=package.joinpath(*parts.parts);dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(z.read(info))
assert not (package/'.godot').exists()
(package/'ta_runtime_probe.gd').write_bytes((OUT/'technical-runtime-probe.gd').read_bytes())
commands=[('import',['--headless','--path',str(package),'--editor','--import','--quit']),('entry',['--path',str(package),'--position','-32000,-32000','--resolution','960x640','--rendering-method','gl_compatibility','--script','res://ta_runtime_probe.gd'])]
calls=[]
for name,args in commands:
    stdout=OUT/f'technical-cold-r2-{name}.stdout.log';stderr=OUT/f'technical-cold-r2-{name}.stderr.log'
    start=time.monotonic()
    with stdout.open('wb') as o,stderr.open('wb') as e:
        p=subprocess.run([str(engine),*args],stdout=o,stderr=e,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
    calls.append({'call':name,'exit_code':p.returncode,'seconds':round(time.monotonic()-start,3),'stderr_bytes':stderr.stat().st_size,'args':args,'stdout':stdout.name,'stderr':stderr.name})
    if p.returncode:
        (OUT/'technical-cold-failed.json').write_text(json.dumps(calls,indent=2),encoding='utf-8')
        raise RuntimeError(stdout.read_text(encoding='utf-8',errors='replace')+stderr.read_text(encoding='utf-8',errors='replace'))
changes=[f['file'] for f in manifest if sha((package/f['file']).read_bytes())!=f['sha256']]
result=json.loads((OUT/'technical-runtime-entry.json').read_text(encoding='utf-8'))
assert result['status']=='PASS' and not changes
receipt={'status':'PASS','zip_sha256':sha(archive.read_bytes()),'fresh_cache_absent_before_import':True,'original_payload_files':len(manifest),'payload_changes_after_engine':changes,'calls':calls,'probe_sha256':sha((OUT/'technical-runtime-probe.gd').read_bytes()),'result_sha256':sha((OUT/'technical-runtime-entry.json').read_bytes()),'screenshot_sha256':sha((OUT/'technical-entry-collect.png').read_bytes()),'scope':'New real runtime main scene, all24/112 imported frame readback, two natural loops and one collected clip; no repeat of source224GPU matrix'}
(OUT/'technical-cold-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':receipt['status'],'calls':calls,'payload_changes':changes,'entry_result':result},ensure_ascii=False))
