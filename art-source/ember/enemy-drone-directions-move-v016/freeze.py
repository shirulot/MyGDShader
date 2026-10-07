"""Freeze the six new drone movement directions, preserving approved down and SE bytes."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT.parent/'enemy-drone-directions-move-v016-review-v001'
ZIP=ROOT.parent/'deliveries/enemy_drone_eight_moves_v016_v001_2026-10-07.zip'
WEB=ROOT.parent/'enemy-sequences-v001/previews/drone-eight-moves-v016-v001'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not PACKAGE.exists() and not ZIP.exists() and not WEB.exists(),'Frozen version exists'
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
for name in ['pixel_audit.json','gpu_roundtrip.json','runtime.json','rotor_audit.json']:
    report=json.loads((ROOT/'qa'/name).read_text(encoding='utf-8'))
    assert report['status']=='PASS' and report['catalog_sha256']==sha(ROOT/'output/catalog.json')
PACKAGE.mkdir()
def copy(source,relative):
    destination=PACKAGE/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,destination)
for name in ['project.godot','preview.gd','preview.tscn','rig.gd','rig.json',
             'pilot_fan_body.gdshader','pilot_fan.gdshader','export.gd','verify.gd','capture.gd',
             'pixel_audit.py','rotor_audit.py','inspect_rotors.gd','previews/index.html']:
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
(PACKAGE/'README.md').write_text('''# 侦察机八向移动 v016 / review v001

申请六个新方向移动，共6条48帧。down与down_right两条16帧原样复制既有通过版本。八向共64帧，其它四类动作不在本批。128×128/root(64,104)/Nearest/8帧8FPS loop。

六方向的机壳、风筒、支架、短探头均直接使用已通过s004静态原图。只有两处风口换入已通过v011的固定转子和井底；每个椭圆半径(6.5,4.5)，中性绑定改变177或178点，全部在风口内。源/绑定同ROI对照见qa/six_direction_source_bind_4x.png。

转子先在自身平面旋转，再做椭圆投影；每帧11.25度、八帧90度，与四叶转子的循环周期一致。解剖右侧恒正转、左侧恒反转，按方向追踪到屏幕上的近/远轴；不是左右精灵镜像。中心取原生图的轮毂像素中心，列于rig.json。后向是(85.5,64.5)/(41.5,64.5)，侧向沿同一x64.5、y57.5/72.5分布。机体只有固定1px悬浮，轴距及外壳不变。

qa/rotor_audit.json逐帧扣除声明悬浮：48新帧全部Alpha与母版一致，风口外可见RGBA零差；透明画布边界的隐藏RGB不参与该可见差统计。12个轴心八帧颜色各自恒定。完整原生八帧与共同ROI见qa/rotors_*_6x.png。

打开project.godot运行实际AnimatedSprite2D，八方向保持同相位切换，可暂停单步、8FPS/1FPS、1×/4×和深浅底，对照原down。64帧PNG/atlas/嵌入TRES一致；48新帧两底96次GPU对照零差；16实际播放器覆盖八帧与循环，8方向保持frame3/progress.375。以上技术自检不代替TA视觉审查，六条新动画状态仍PENDING_TA_REVIEW。

独立运行/导出只使用本包rig.json和source。provenance中s004登记供追踪先前静态制作，不是需要执行的外部依赖。本包不使用v011-r1探头实验。
''',encoding='utf-8')
files=sorted(p for p in PACKAGE.rglob('*') if p.is_file())
manifest={'status':'PENDING_TA_REVIEW','new_clips':6,'new_frames':48,'preserved_clips':2,'files':{
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
         'url':'http://127.0.0.1:6106/drone-eight-moves-v016-v001/index.html',
         'web_hashes':{p.relative_to(WEB).as_posix():sha(p) for p in WEB.rglob('*') if p.is_file()}}
(ROOT/'qa/submission_receipt_v001.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='web_hashes'}))
