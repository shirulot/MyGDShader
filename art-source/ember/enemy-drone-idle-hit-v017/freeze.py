"""Freeze the six new drone movement directions, preserving approved down and SE bytes."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT.parent/'enemy-drone-idle-hit-v017-review-v001'
ZIP=ROOT.parent/'deliveries/enemy_drone_idle_hit_v017_v001_2026-10-07.zip'
WEB=ROOT.parent/'enemy-sequences-v001/previews/drone-idle-hit-v017-v001'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not PACKAGE.exists() and not ZIP.exists() and not WEB.exists(),'Frozen version exists'
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
for name in ['pixel_audit.json','gpu_roundtrip.json','runtime.json','pose_audit.json']:
    report=json.loads((ROOT/'qa'/name).read_text(encoding='utf-8'))
    assert report['status']=='PASS' and report['catalog_sha256']==sha(ROOT/'output/catalog.json')
PACKAGE.mkdir()
def copy(source,relative):
    destination=PACKAGE/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,destination)
for name in ['project.godot','preview.gd','preview.tscn','rig.gd','rig.json',
             'pilot_fan_body.gdshader','pilot_fan.gdshader','export.gd','verify.gd','capture.gd',
             'pixel_audit.py','pose_audit.py','inspect_actions.gd','previews/index.html']:
    copy(ROOT/name,name)
for folder in ['source','output','reference','qa']:
    for path in (ROOT/folder).rglob('*'):
        if path.is_file() and path.suffix in ['.png','.json','.tres'] and 'receipt' not in path.name:
            copy(path,path.relative_to(ROOT))
W=ROOT.parent/'enemy-eight-directions-v013'
copy(W/'static_preflight_s004_drone/manifest.json','provenance/s004_manifest.json')
copy(W/'static_registration_drone_s004.json','provenance/s004_registration.json')
copy(ROOT.parent/'enemy-drone-actions-v011/source/rotor_well_prompt.txt','provenance/rotor_well_prompt.txt')
receipt={'static_zip_sha256':'3a6dc8a5ab9c16dc5e71d083568768ff3cabefae2675d5385e552149acb79342',
         'static_review':'art-source/ember/ta-review-v001/enemy-drone-v013-s004/review-s004.md',
         'down_zip_sha256':'42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe',
         'se_zip_sha256':'2ef84aaa45b2970bf4db9c5abdf4f845f4d65be9878c97d929701d090d4e37f1',
         'rotor_zip_sha256':'13a4942d34d0ceabac7473c1689aa4784bc0c6f1555ff68817ed9d93159dab3e',
         'source_hashes':{p.name:sha(p) for p in (ROOT/'source').glob('*.png')}}
(PACKAGE/'SOURCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
(PACKAGE/'README.md').write_text('# 侦察机八向待机与受击 v017 / review v001\n\n申请七新向×idle/hit共14条56帧。另两条8帧为v012已过正向原文件。移动、攻击、死亡不在本批。128×128/root(64,104)/Nearest；idle4帧4FPS循环，hit4帧12FPS单次。\n\n每方向使用通过的s004机壳PNG和v011固定四叶转子、井底。源纹理/风口/双轴和方向旋转归属固定，不逐帧生成或镜像。中性绑定177/178点全部位于两风口，外部RGBA相同。动作参数只保留actions内的实际帧数/FPS/loop，已清理顶层遗留移动参数。\n\n动作沿用已通过v011：idle机体Y[0,-1,0,1]、转子角[0,22.5,45,67.5]；hit绕(64,67)整体roll[0,-6,3,0]度、转子角[0,15,8,0]，机壳/风筒/杆/探头为同一刚性变换。解剖左右叶片保持相反旋转。风口内依旧先叶片旋转后椭圆投影，再随整体roll。正侧面遮挡母版不变，不拉伸连接杆或整张精灵。\n\nqa/pose_audit.json核56个新位姿：机身变换为无缩放的正交旋转，两个风口轴间距恒定，所有八向hit F03与F00实际RGBA一致。新七向共同ROI见qa/detail_*_6x.png。原生旋转经Nearest栅格化，边界阶梯变化属于离散像素取样，视觉连贯性仍需TA独立判断。\n\n64PNG/atlas/内嵌SpriteFrames一致、二值Alpha单连通；56新帧黑白112次GPU回对零差；32个AnimatedSprite2D覆盖四帧，idle循环、hit恰一次finished并停恢复帧，16次方向切换保持frame2/progress.375。Godot和网页均有正常/1FPS、原生/4倍、深浅底、单步及重播。\n\n本固定包只提交候选，技术检查不替代TA艺术通过。export.gd独立读取本包rig.json和source即可复现，provenance记录静态与转子历史来源；不使用v011-r1探头实验。\n',encoding='utf-8')
files=sorted(p for p in PACKAGE.rglob('*') if p.is_file())
manifest={'status':'PENDING_TA_REVIEW','new_clips':14,'new_frames':56,'preserved_clips':2,'files':{
    p.relative_to(PACKAGE).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in files}}
(PACKAGE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for p in files+[PACKAGE/'manifest.json']:archive.write(p,p.relative_to(PACKAGE).as_posix())
with zipfile.ZipFile(ZIP) as archive:
    for name,data in manifest['files'].items():assert hashlib.sha256(archive.read(name)).hexdigest()==data['sha256']
WEB.mkdir()
shutil.copy2(PACKAGE/'previews/index.html',WEB/'index.html')
shutil.copy2(PACKAGE/'output/catalog.json',WEB/'catalog.json')
for folder in ['output','reference']:
    for path in (PACKAGE/folder).rglob('*.png'):
        destination=WEB/path.relative_to(PACKAGE)
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,destination)
receipt={'zip':str(ZIP),'zip_sha256':sha(ZIP),'bytes':ZIP.stat().st_size,'payload_count':len(files),
         'catalog_sha256':sha(PACKAGE/'output/catalog.json'),
         'url':'http://127.0.0.1:6106/drone-idle-hit-v017-v001/index.html',
         'web_hashes':{p.relative_to(WEB).as_posix():sha(p) for p in WEB.rglob('*') if p.is_file()}}
(ROOT/'qa/submission_receipt_v001.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='web_hashes'}))
