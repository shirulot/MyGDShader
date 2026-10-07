"""Freeze an immutable attack/death candidate with local reproduction inputs."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT.parent/'enemy-drone-attack-death-v018-review-v001'
ZIP=ROOT.parent/'deliveries/enemy_drone_attack_death_v018_v001_2026-10-07.zip'
WEB=ROOT.parent/'enemy-sequences-v001/previews/drone-attack-death-v018-v001'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not any(p.exists() for p in [PACKAGE,ZIP,WEB]),'Frozen version exists'
for name in ['pixel_audit.json','gpu_roundtrip.json','runtime.json','pose_audit.json']:
    report=json.loads((ROOT/'qa'/name).read_text(encoding='utf-8'))
    assert report['status']=='PASS' and report['catalog_sha256']==sha(ROOT/'output/catalog.json')
PACKAGE.mkdir()
def copy(source,relative):
    target=PACKAGE/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
for path in ROOT.iterdir():
    if path.is_file() and path.suffix in ['.gd','.gdshader','.godot','.tscn','.json','.py'] and path.name not in ['freeze.py','build.py']:
        copy(path,path.name)
copy(ROOT/'previews/index.html','previews/index.html')
for folder in ['source','output','reference','qa']:
    for path in (ROOT/folder).rglob('*'):
        if path.is_file() and path.suffix in ['.png','.json','.tres'] and 'receipt' not in path.name:
            copy(path,path.relative_to(ROOT))
W=ROOT.parent/'enemy-eight-directions-v013'
copy(W/'static_preflight_s004_drone/manifest.json','provenance/s004_manifest.json')
copy(W/'static_registration_drone_s004.json','provenance/s004_registration.json')
copy(ROOT.parent/'enemy-drone-actions-v011/source/rotor_well_prompt.txt','provenance/rotor_well_prompt.txt')
copy(ROOT.parent/'enemy-drone-idle-hit-v017-review-v001/SOURCE_RECEIPT.json','SOURCE_RECEIPT.json')
(PACKAGE/'README.md').write_text('''# 侦察机八向攻击、死亡 v018 / review v001

申请七新向 × attack/death：14条98帧。另两条正向14帧严格保留v012原文件。128×128/root(64,104)/Nearest。attack6帧10FPS、death8帧10FPS，均单次播放。

母版沿用通过的s004及v011固定四叶转子，不使用v011-r1。中性绑定只替换风口内177/178点，外部RGBA相同。

攻击沿用v011下探节奏：bodyY[0,0,1,2,1,0]，f03释放；SW/SE露出的短探头从同一母版注册局部TIP，在固定套筒前叠合伸缩[0,0,1,2,1,0]，不改写源RGB。侧面与背面保持近风筒/机壳遮挡，不凭空增加探头。首末帧完全复位。

本批死亡采用刚性机体坠落：传感灯断电、双转子角[0,25,42,52,58,60,60,60]逐步停止，壳体、风筒和杆维持固定刚性关系。与旧down的3px风筒局部下折不同，新方向不制作未校准的隐藏杆折叠。每方向仅按已固定静态最低边计算一次到地面104的落差，逐帧取[0,.125,1/3,7/12,5/6,1,1,1]；不缩放或按每帧bbox重新归一。最后三帧残骸保持。该动作设计差异明确提交TA判断，不继承其他批次艺术PASS。

112帧PNG/atlas/内嵌SpriteFrames像素一致，二值Alpha/单连通/安全边界；98新帧黑白196次GPU零差+14旧TRES记录。32个AnimatedSprite2D覆盖全部帧且单次finished停在末帧；16次同相位切向。pose_audit独立核实际PNG：8向攻击首末一致，8向死亡单调落地且底边104、最后三帧一致。完整深浅1×/4×及共同ROI已生成。

export.gd使用本包本地rig/source可复现；verify.gd和capture.gd分别验证像素与真实播放。网页及Godot预览提供正常/1FPS、1×/4×、深浅底、逐帧和重播。本冻结包为待审候选。
''',encoding='utf-8')
files=sorted(p for p in PACKAGE.rglob('*') if p.is_file())
manifest=dict(status='PENDING_TA_REVIEW',new_clips=14,new_frames=98,preserved_clips=2,files={p.relative_to(PACKAGE).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in files})
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
receipt=dict(zip=str(ZIP),zip_sha256=sha(ZIP),bytes=ZIP.stat().st_size,payload_count=len(files),catalog_sha256=sha(PACKAGE/'output/catalog.json'),url='http://127.0.0.1:6106/drone-attack-death-v018-v001/index.html',web_hashes={p.relative_to(WEB).as_posix():sha(p) for p in WEB.rglob('*') if p.is_file()})
(ROOT/'qa/submission_receipt_v001.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='web_hashes'}))
