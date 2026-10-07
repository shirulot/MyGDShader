"""TA 独立核对已安装字节、导入缓存、保护记录和预览映射；只写本审核目录。"""
from pathlib import Path
import hashlib, json, re, zipfile, subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
QA = REPO / 'art-source/ember/enemy-sequences-eight-directions-v027/qa'
TARGET = REPO / 'assets/ember/characters/enemies_v003'
WEB = REPO / 'art-source/ember/enemy-sequences-v001/previews'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
errors = []
def check(ok, label):
    if not ok: errors.append(label)

package = REPO / 'art-source/ember/deliveries/enemy_sequences_eight_directions_v027_v001_2026-10-07.zip'
check(sha(package) == 'aba87363a03247ab5069dc2d21dac9544a29e200932d86f0d7aa2a8a12e91826', 'fixed ZIP')
with zipfile.ZipFile(package) as z:
    names = [n for n in z.namelist() if n.startswith('output/') and not n.endswith('/')]
    for n in names:
        p = TARGET / n.removeprefix('output/')
        check(p.is_file() and p.read_bytes() == z.read(n), 'installed payload '+n)
check(len(names)==1157, 'payload count')
submission = read(QA / 'installation_submission_receipt_v001.json')
for record in submission['evidence'].values():
    check(sha(REPO/record['path'])==record['sha256'], 'receipt '+record['path'])
for record in submission['import_settings']:
    check(sha(REPO/record['path'])==record['sha256'], 'import metadata '+record['path'])
imports = read(QA/'installed_import_receipt.json')['records']
for record in imports:
    text = (REPO/record['path']).with_suffix('.png.import').read_text()
    check('source_file="res://'+record['path']+'"' in text, 'source path '+record['path'])
    for key,value in [('compress/mode','0'),('detect_3d/compress_to','0'),('mipmaps/generate','false'),('process/fix_alpha_border','false'),('process/premult_alpha','false')]:
        check(bool(re.search('^'+re.escape(key)+'='+value+'$',text,re.M)),key+' '+record['path'])
    for c in record['cache']:
        check(sha(REPO/c['path'])==c['sha256'], 'cache '+c['path'])
    check('path="res://'+record['cache'][0]['path']+'"' in text,'cache route '+record['path'])
check(len(imports)==1152,'import count')
before = read(QA/'protected_files_before_install.json')
after = read(QA/'installation_protection_receipt.json')
for path, original in before['files'].items():
    p=REPO/path
    actual={'sha256':sha(p),'bytes':p.stat().st_size}
    check(actual==original==after['files'][path]['after']==after['files'][path]['before'], 'protected '+path)
for path,h in before['current_preview_before'].items():
    check(sha(WEB/'review-v012-before-v027-2026-10-07'/path)==h, 'legacy preview '+path)
frozen = REPO/'art-source/ember/enemy-sequences-eight-directions-v027-review-v001'
fixedweb = WEB/'enemy-eight-directions-v027-v001'
webfiles=[p for p in fixedweb.rglob('*') if p.is_file()]
for p in webfiles:
    q=WEB/'review-current'/p.relative_to(fixedweb)
    check(q.is_file() and p.read_bytes()==q.read_bytes(),'current preview '+str(p.relative_to(fixedweb)))
check(len(webfiles)==1154,'web count')
# 重用先前独立探针中逐帧检查逻辑，改为主项目 res:// 的已安装路径。
prior=(HERE.parent/'enemy-v027-unified-v001/ta_probe.gd').read_text(encoding='utf-8')
probe=prior.split(' var preview:Node2D=')[0].replace('res://output/','res://assets/ember/characters/enemies_v003/')
probe+=' var result={"status":"PASS" if errors.is_empty() else "FAIL","cells":cells,"errors":errors,"scope":"Actual main-project res paths; headless resource RGBA, region and timing validation; no GPU or gameplay test."}\n'
probe+=' FileAccess.open("'+(HERE/'resource-load.json').as_posix()+'",FileAccess.WRITE).store_string(JSON.stringify(result,"  "))\n print("TA_INSTALLED ",result.status," cells=",cells.size())\n quit(0 if errors.is_empty() else 1)\n'
(HERE/'probe.gd').write_text(probe,encoding='utf-8')
with (HERE/'load.stdout.log').open('wb') as out,(HERE/'load.stderr.log').open('wb') as err:
    run=subprocess.run([r'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe','--headless','--path',str(REPO),'--script',str(HERE/'probe.gd')],stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW,timeout=45)
check(run.returncode==0,'engine exit')
if (HERE/'resource-load.json').exists():
    result=read(HERE/'resource-load.json');check(result['status']=='PASS' and len(result['cells'])==960,'actual resource load')
else: check(False,'missing load result')
report=dict(status='PASS' if not errors else 'FAIL',payload_count=len(names),import_count=len(imports),protected_count=len(before['files']),web_files=len(webfiles),errors=errors,engine_exit=run.returncode)
(HERE/'technical-installation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
