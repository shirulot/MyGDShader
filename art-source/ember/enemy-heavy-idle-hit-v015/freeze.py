"""Publish an immutable review snapshot and bind its exact bytes to the localhost player."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT.parent/'enemy-heavy-idle-hit-v015-review-v001'
ZIP=ROOT.parent/'deliveries/enemy_heavy_idle_hit_v015_v001_2026-10-07.zip'
WEB=ROOT.parent/'enemy-sequences-v001/previews/heavy-idle-hit-v015-v001'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert not PACKAGE.exists() and not ZIP.exists() and not WEB.exists(),'Frozen destination exists'
catalog=json.loads((ROOT/'output/catalog.json').read_text())
for filename in ['pixel_audit.json','gpu_roundtrip.json','runtime.json']:
    qa=json.loads((ROOT/'qa'/filename).read_text())
    assert qa['status']=='PASS' and qa['catalog_sha256']==sha(ROOT/'output/catalog.json')
PACKAGE.mkdir()

def copy(path,relative):
    target=PACKAGE/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,target)

for name in ['project.godot','preview.gd','preview.tscn','rig.gd','rig.json','tread_flow.gdshader',
             'masked_part.gdshader','export.gd','verify.gd','capture.gd','pixel_audit.py','inspect_mounts.gd','previews/index.html']:
    copy(ROOT/name,name)
for folder in ['source','output','reference','qa']:
    for path in (ROOT/folder).rglob('*'):
        if path.is_file() and path.suffix in ['.png','.tres','.json']:
            copy(path,path.relative_to(ROOT))
previous=ROOT.parent/'enemy-eight-directions-v013'
for filename in ['source/turnarounds/enemy_tracked_heavy_eight_views_v001.png','prompts/enemy_tracked_heavy_eight_views_v001.txt','registration.json']:
    copy(previous/filename,Path('provenance')/filename)
receipt={'static_review':'art-source/ember/ta-review-v001/enemy-eight-directions-v013-preflight/review-static-preflight-v001.md',
         'down_zip_sha256':'42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe',
         'se_first_gate_zip_sha256':'5db52757c74fc537b3f45d87abdbab8c58e5d8fcd3cf6366153f7b32ef98b9ef',
         'source_png_hashes':{p.name:sha(p) for p in (ROOT/'source').glob('*.png')},
         'new_actions':[x['action'] for x in catalog['clips'] if x['status']=='PENDING_TA_REVIEW']}
(PACKAGE/'SOURCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
(PACKAGE/'README.md').write_text('# 重装机八向待机与受击 v015 / review v001\n\n本批申请七个新方向×待机、受击两类，共14条56帧。另有idle_down/hit_down两条8帧从已通过v012原样复制。移动、攻击、死亡不在本批申请内。\n\n128×128 / root(64,104) / Nearest。idle四帧4FPS循环；hit四帧12FPS单次。动作数据沿用已通过v007正向：idle机身[0,0]/[0,-1]/[0,0]/[0,1]；hit机身[0,0]/[-2,1]/[1,0]/[0,0]，表示屏幕左侧受击回弹，履带支撑固定、相位为0。所有方向均使用已通过的固定静态母版，没有逐帧生图、精灵镜像或按bbox缩放。\n\n受击位移比移动大。已修正部件切线，避免把顶部壳体的一小列分给固定履带；安装处使用原纹理的隐藏重叠区（x半径3/y半径1，y60..98），覆盖在移动壳体之后。只定义源区域归属，不补画RGB；所有中性绑定与源图RGBA零差。修后64帧均单连通、无孤立条纹，安装区共同ROI见qa/mount_*_6x.png。此批安装座修订不改变先前固定移动提交。\n\n打开project.godot运行实际AnimatedSprite2D；idle循环，hit触发一次并保持恢复帧。方向切换保留frame/frame_progress。浏览器与Godot均提供正常/1FPS、1倍/4倍、深浅底、单步及重播。本包输出的SpriteFrames包含16条动作，已通过正向可同相位对照。\n\n作者技术自检：64帧PNG/atlas/内嵌SpriteFrames一致；56新帧在黑白两底共112次live rig/PNG GPU零差；32个实际播放器覆盖全四帧，idle至少一圈，hit恰一次finished且停第4帧，16次方向切换保持相位。技术自检不代表TA艺术通过，当前PENDING_TA_REVIEW。\n\n独立导出入口export.gd读取本包rig.json与source即可复现。七向来源登记和源稿位于provenance；既有正向及初始SE移动门槛版本哈希记于SOURCE_RECEIPT.json，SE移动不作为本批动画载荷。\n',encoding='utf-8')
files=sorted(p for p in PACKAGE.rglob('*') if p.is_file())
manifest={'status':'PENDING_TA_REVIEW','new_clips':14,'new_frames':56,'preserved_clips':2,'files':{
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
         'url':'http://127.0.0.1:6106/heavy-idle-hit-v015-v001/index.html',
         'web_hashes':{p.relative_to(WEB).as_posix():sha(p) for p in WEB.rglob('*') if p.is_file()}}
(ROOT/'qa/submission_receipt_v001.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='web_hashes'}))
