"""Publish an immutable review snapshot and bind its exact bytes to the localhost player."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT.parent/'enemy-heavy-directions-move-v014-review-v002'
ZIP=ROOT.parent/'deliveries/enemy_heavy_eight_moves_v014_v002_2026-10-07.zip'
WEB=ROOT.parent/'enemy-sequences-v001/previews/heavy-eight-moves-v014-v002'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert not PACKAGE.exists() and not ZIP.exists() and not WEB.exists(),'Frozen destination exists'
catalog=json.loads((ROOT/'output/catalog.json').read_text())
for filename in ['pixel_audit.json','gpu_roundtrip.json','runtime.json','tread_source_audit.json']:
    qa=json.loads((ROOT/'qa'/filename).read_text())
    assert qa['status']=='PASS' and qa['catalog_sha256']==sha(ROOT/'output/catalog.json')
PACKAGE.mkdir()

def copy(path,relative):
    target=PACKAGE/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,target)

for name in ['project.godot','preview.gd','preview.tscn','rig.gd','rig.json','tread_flow.gdshader',
             'masked_part.gdshader','export.gd','verify.gd','capture.gd','pixel_audit.py','audit_tread_sources.py','inspect_treads.gd','previews/index.html']:
    copy(ROOT/name,name)
for folder in ['source','output','reference','qa']:
    for path in (ROOT/folder).rglob('*'):
        if path.is_file() and path.suffix in ['.png','.tres','.json'] and 'receipt' not in path.name:
            copy(path,path.relative_to(ROOT))
previous=ROOT.parent/'enemy-eight-directions-v013'
for filename in ['source/turnarounds/enemy_tracked_heavy_eight_views_v001.png','prompts/enemy_tracked_heavy_eight_views_v001.txt','registration.json']:
    copy(previous/filename,Path('provenance')/filename)
receipt={'static_review':'art-source/ember/ta-review-v001/enemy-eight-directions-v013-preflight/review-static-preflight-v001.md',
         'down_zip_sha256':'42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe',
         'down_right_zip_sha256':'5db52757c74fc537b3f45d87abdbab8c58e5d8fcd3cf6366153f7b32ef98b9ef',
         'source_png_hashes':{p.name:sha(p) for p in (ROOT/'source').glob('*.png')},
         'new_actions':[x['action'] for x in catalog['clips'] if x['status']=='PENDING_TA_REVIEW']}
(PACKAGE/'SOURCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
(PACKAGE/'README.md').write_text('''# 重装机八向移动 v014 / review v002

v002仅修正N左履带采样域：从x28..43缩到x31..41，y85..100不变，16px周期/每帧2px不变。透明源RGB进入实体的次数由33降为0；原N左窗口之外RGBA差0，全部Alpha差0，N帧0不变。其余7条动作PNG/atlas与v001字节一致。修订证据qa/tread_source_audit.json；总监原问题记录位于enemy-heavy-v014-move-v001。

本批申请六个新方向移动共48帧。down与down_right两条/16帧保留既有通过文件，独立哈希验证不变。8向共64帧不是8条新增通过。其它idle/attack/hit/death不在本批申请内。

128×128、root(64,104)、Nearest、8帧8FPS loop。六方向均来自已过静态母版，每方向只使用一个固定源图。ownership遮罩将履带框和侧部装甲留在接地支架上；中央壳体只在F2/F6做1px悬挂升降。帧0绑定与各方向源图RGBA零差。

履带运动是受窗口限制的原图像素循环采样，周期16、每帧2px；外轮廓和Alpha不变。正侧面的上、下履带段相反流向，圆形轮盖保持固定；未制作轮盖旋转。后向的履带端面使用相反流向。rig.json明确列出每个方向的支撑点、遮罩和窗口。无逐帧生图、无整图镜像、无逐帧bbox缩放或居中。

打开project.godot运行实际AnimatedSprite2D；输出output/enemy_tracked_heavy_move_v014.tres含8条移动。预览方向切换保留frame与frame_progress；可暂停单步、8FPS/1FPS、1倍/4倍和深浅底。同画布正向对照为原通过帧。qa包含64帧像素检查、48新帧在两底共96次live rig/PNG GPU零差、64个嵌入帧一致、16个实际播放器完整循环，以及8次方向相位切换。履带共同ROI位于qa/treads_*_4x.png。

所有技术自检只验证固定资源与运行行为，最终动作视觉结论待技术美术总监审查。本包导出入口export.gd读取冻结rig.json即可运行；上游build_spec.py依赖历史包，因此不作为独立入口包含。
''',encoding='utf-8')
files=sorted(p for p in PACKAGE.rglob('*') if p.is_file())
manifest={'status':'PENDING_TA_REVIEW','new_clips':6,'new_frames':48,'preserved_clips':2,'files':{
    p.relative_to(PACKAGE).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in files}}
(PACKAGE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for path in files+[PACKAGE/'manifest.json']:archive.write(path,path.relative_to(PACKAGE).as_posix())
with zipfile.ZipFile(ZIP) as archive:
    for name,data in manifest['files'].items():assert hashlib.sha256(archive.read(name)).hexdigest()==data['sha256']
WEB.mkdir()
shutil.copy2(PACKAGE/'previews/index.html',WEB/'index.html')
shutil.copy2(PACKAGE/'output/catalog.json',WEB/'catalog.json')
for folder in ['output','reference']:
    for path in (PACKAGE/folder).rglob('*.png'):
        target=WEB/path.relative_to(PACKAGE)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
receipt={'zip':str(ZIP),'zip_sha256':sha(ZIP),'bytes':ZIP.stat().st_size,'payload_count':len(files),
         'catalog_sha256':sha(PACKAGE/'output/catalog.json'),'new_actions':receipt['new_actions'],
         'url':'http://127.0.0.1:6106/heavy-eight-moves-v014-v002/index.html',
         'web_hashes':{p.relative_to(WEB).as_posix():sha(p) for p in WEB.rglob('*') if p.is_file()}}
(ROOT/'qa/submission_receipt_v002.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='web_hashes'}))
