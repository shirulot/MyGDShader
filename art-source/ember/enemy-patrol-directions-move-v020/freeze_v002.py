"""Freeze the four-direction candidate; unused profile-leg studies are excluded."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT.parent/'enemy-patrol-directions-move-v020-review-v002'
ZIP=ROOT.parent/'deliveries/enemy_patrol_four_moves_v020_v002_2026-10-07.zip'
WEB=ROOT.parent/'enemy-sequences-v001/previews/patrol-four-moves-v020-v002'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not any(p.exists() for p in [PACKAGE,ZIP,WEB]),'Frozen version exists'
for name in ['pixel_audit.json','gpu_roundtrip.json','runtime.json','pose_audit.json']:
    report=json.loads((ROOT/'qa'/name).read_text(encoding='utf-8'))
    assert report['status']=='PASS' and report['catalog_sha256']==sha(ROOT/'output/catalog.json')
PACKAGE.mkdir()
def copy(source,relative):
    target=PACKAGE/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
for name in ['project.godot','rig.gd','rig.json','masked_part.gdshader','export.gd','verify.gd','capture.gd','preview.gd','preview.tscn','pixel_audit.py','pose_audit.py','ownership_audit.py','inspect_actions.gd','previews/index.html']:
    copy(ROOT/name,name)
for direction in ['down','down_left','left','up_left','up','up_right','right','down_right']:
    copy(ROOT/'source'/f'{direction}.png',f'source/{direction}.png')
for folder in ['output','reference','qa']:
    for path in (ROOT/folder).rglob('*'):
        if path.is_file() and path.suffix in ['.png','.tres','.json'] and 'receipt' not in path.name:copy(path,path.relative_to(ROOT))
W=ROOT.parent/'enemy-eight-directions-v013'
for name in ['source/turnarounds/enemy_patrol_remaining_five_v004.png','source/turnarounds/enemy_patrol_calibration_v002.png','prompts/enemy_patrol_remaining_five_v004.txt','prompts/enemy_patrol_calibration_v002.txt','static_preflight_v002_patrol/registration.json','calibration_registration_v002.json']:
    copy(W/name,Path('provenance')/name)
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
receipt=dict(static_review='art-source/ember/ta-review-v002/enemy-patrol-v013-s002/review-static.md',static_zip_sha256='28951089e1403c65f6a8446aed5f049fdba704809175da36a391c6c5fa1e99a1',
             down_zip_sha256='42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe',down_right_zip_sha256='c7cf9683604740953a48d43b6fd2fbf7cd5d11767ee3af1fbc65171d4493dd21',
             source_png_hashes={p.name:sha(p) for p in (PACKAGE/'source').glob('*.png')},new_actions=[c['action'] for c in catalog['clips'] if c['status']=='PENDING_TA_REVIEW'])
(PACKAGE/'SOURCE_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
(PACKAGE/'README.md').write_text('''# 巡逻机四个新移动方向 v020 / review v002

v002只修NE：原浅甲源区归回刚性body，left_thigh仅含x57..58/y80..84十个暗蓝源像素；左右腿的甲片/靴子按实际接缝唯一分区，四方向均零实体重复归属。无新生成、无RGB改写。NE八帧共334像素次RGBA变化，其余40帧PNG与五atlas字节保持。详见qa/ownership_revision_v002.json。\n\n本批仅申请SW/NW/N/NE四条移动、32新帧。原down和已过SE保留原PNG/atlas，合计六条48帧。纯W/E尚未制作，预览明确显示静态母稿，不计动作；其隐藏远腿研究没有混入本包。

128×128/root(64,104)/Nearest，8帧8FPS循环。四个新方向来自已过S002固定母图，不镜像、不逐帧生图、无逐帧裁剪/居中/缩放。新四向的中性绑定逐RGBA等母图；移动F0是跨步姿态，不能把F0当成中性绑定。每个方向只用自己原母图，零新增绘制像素。

双腿沿原down/SE解剖相位交替支撑与抬脚，左右深度投影随朝向变化。膝盖护板、黄铜铰链和靴子为刚体；短蓝灰连杆按实际可见接缝端点映射，弥合与刚性护板的连接，不把护板一起拉长。共享骨长仅用于步态求解，不用于改动母图比例。工具/夹爪显式留给body，工具区域所有实体RGB随body保持原色/原位关系。所有定义在rig.json中一次注册。

自检：48帧PNG/atlas/TRES一致，二值Alpha/单连通/边界；4套bind为0差；32组支撑脚落点、刚性护板/靴子、连杆端点、工具源像素检查通过。64新深浅GPU回对+16旧TRES共80条。12个AnimatedSprite2D以8FPS与1FPS走完8帧并循环；8个方向选择验证，6条动作保留相位，W/E明确退回未制作静态。

qa/detail_move_*_4x.png为固定共同ROI、4×2八帧联系图，另有深浅1×/4×全画布联系图。打开project.godot可运行实际双栏播放；export.gd可直接从本包rig.json和源图重现。本包是候选，技术自检不替代总监视觉验收。
''',encoding='utf-8')
files=sorted(p for p in PACKAGE.rglob('*') if p.is_file())
manifest=dict(status='PENDING_TA_REVIEW',new_clips=4,new_frames=32,preserved_clips=2,files={p.relative_to(PACKAGE).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in files})
(PACKAGE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for p in files+[PACKAGE/'manifest.json']:archive.write(p,p.relative_to(PACKAGE).as_posix())
with zipfile.ZipFile(ZIP) as archive:
    for name,item in manifest['files'].items():assert hashlib.sha256(archive.read(name)).hexdigest()==item['sha256']
WEB.mkdir();shutil.copy2(PACKAGE/'previews/index.html',WEB/'index.html');shutil.copy2(PACKAGE/'output/catalog.json',WEB/'catalog.json')
for folder in ['output','reference']:
    for p in (PACKAGE/folder).rglob('*.png'):
        target=WEB/p.relative_to(PACKAGE);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
delivery=dict(zip=str(ZIP),zip_sha256=sha(ZIP),bytes=ZIP.stat().st_size,payload_count=len(files),catalog_sha256=sha(PACKAGE/'output/catalog.json'),url='http://127.0.0.1:6106/patrol-four-moves-v020-v002/index.html',web_hashes={p.relative_to(WEB).as_posix():sha(p) for p in WEB.rglob('*') if p.is_file()})
(ROOT/'qa/submission_receipt_v002.json').write_text(json.dumps(delivery,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in delivery.items() if k!='web_hashes'}))
