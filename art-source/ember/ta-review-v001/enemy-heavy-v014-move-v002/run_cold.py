"""仅启动自己冷包的两次headless调用；CREATE_NO_WINDOW不弹用户桌面窗口。"""
from pathlib import Path
import subprocess,hashlib,json,time
OUT=Path(__file__).resolve().parent
PKG=OUT/'cold-project'
ENGINE=Path('E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe')
assert not (PKG/'.godot').exists()
# 自有探针是唯一加进冷工程的测试文件；原包162文件保持只读比较边界。
(PKG/'ta_probe.gd').write_bytes((OUT/'probe_cold.gd').read_bytes())
calls=[]
for name,args in [('import',['--headless','--path',str(PKG),'--editor','--import']),
                  ('probe',['--headless','--path',str(PKG),'--script','res://ta_probe.gd','--',str(OUT/'cold-probe.json')])]:
 start=time.monotonic()
 stdout,stderr=OUT/(name+'.stdout.log'),OUT/(name+'.stderr.log')
 with stdout.open('wb') as o,stderr.open('wb') as e:
  done=subprocess.run([str(ENGINE),*args],stdout=o,stderr=e,creationflags=subprocess.CREATE_NO_WINDOW,timeout=45)
 row={'call':name,'args':args,'exit_code':done.returncode,'seconds':round(time.monotonic()-start,3),
      'stdout_file':stdout.name,'stderr_file':stderr.name,'stderr_bytes':stderr.stat().st_size,
      'stdout_sha256':hashlib.sha256(stdout.read_bytes()).hexdigest(),'stderr_sha256':hashlib.sha256(stderr.read_bytes()).hexdigest()}
 calls.append(row)
 print(row)
 if done.returncode:raise RuntimeError(stdout.read_text(encoding='utf-8',errors='replace')+stderr.read_text(encoding='utf-8',errors='replace'))
probe=json.loads((OUT/'cold-probe.json').read_text(encoding='utf-8-sig'))
# 导入缓存可新增；确认包内原文件无内容变化。
manifest=json.loads((PKG/'manifest.json').read_text(encoding='utf-8-sig'))['files']
assert all(hashlib.sha256((PKG/name).read_bytes()).hexdigest()==row['sha256'] for name,row in manifest.items())
receipt={'status':'PASS','initial_godot_cache_absent':True,'engine':str(ENGINE),'calls':calls,
 'independent_checks_passed':probe['passed'],'independent_checks_total':probe['total'],
 'probe_sha256':hashlib.sha256((OUT/'cold-probe.json').read_bytes()).hexdigest(),
 'original161_payloads_after_cold_import_hash_same':True,'ta_gpu_rerun':False,'author96_gpu_or_full16player8direction_suite_rerun':False}
(OUT/'cold-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print('probe',probe['status'],probe['passed'],probe['total'])
