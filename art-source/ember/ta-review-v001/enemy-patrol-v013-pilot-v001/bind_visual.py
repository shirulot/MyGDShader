"""封存实际审查图；只生成诊断联系图，不修改动画像素。"""
from pathlib import Path,PurePosixPath
from zipfile import ZipFile
from PIL import Image,ImageDraw
import hashlib,json
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
P=OUT/"package"
Z=ROOT/"art-source/ember/deliveries/enemy_eight_directions_v013_pilot_patrol_v001_2026-10-06.zip"
def sha(data):return hashlib.sha256(data).hexdigest()
assert sha(Z.read_bytes())=="c7cf9683604740953a48d43b6fd2fbf7cd5d11767ee3af1fbc65171d4493dd21"
with ZipFile(Z) as z:
    names=z.namelist();assert len(names)==len(set(names)) and z.testzip() is None
    for n in names:
        path=PurePosixPath(n)
        assert not path.is_absolute() and ".." not in path.parts and ":" not in n and "\\" not in n
        assert ((z.getinfo(n).external_attr>>16)&0o170000)!=0o120000
        target=P/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(n))
spec=json.loads((P/"pilot_rigs.json").read_text())
unit=next(u for u in spec["units"] if u["unit"]=="enemy_patrol")
assert sha((P/unit["source"].removeprefix("res://")).read_bytes())=="e1916f467c4493bab2b95b57b558f18ab2090c45721c48cff590422139cb93f2"
frames=[Image.open(P/f"output/enemy_patrol/move_down_right/f{i:02}.png").convert("RGBA") for i in range(8)]
down=Image.open(P/"reference/enemy_patrol/move_down.png").convert("RGBA")
reference=[down.crop((i*128,0,(i+1)*128,128)) for i in range(8)]
diagnostic=OUT/"diagnostics";diagnostic.mkdir(exist_ok=True)
for bg,color in [("light",(255,255,255,255)),("dark",(0,0,0,255))]:
    # 4列2行共同128画布，保留所有透明格；不会按bbox齐脚底。
    native=Image.new("RGBA",(512,256),color)
    for i,frame in enumerate(frames):native.alpha_composite(frame,((i%4)*128,(i//4)*128))
    native.save(diagnostic/f"patrol_se_all8_{bg}_1x.png")
    native.resize((2048,1024),Image.Resampling.NEAREST).save(diagnostic/f"patrol_se_all8_{bg}_4x.png")
    # 每个同相位组先down后SE，两行各4组；4x只放大，保持共同root。
    comparison=Image.new("RGBA",(1024,256),color)
    for i,(old,new) in enumerate(zip(reference,frames)):
        x=(i%4)*256;y=(i//4)*128
        comparison.alpha_composite(old,(x,y));comparison.alpha_composite(new,(x+128,y))
    comparison.resize((4096,1024),Image.Resampling.NEAREST).save(diagnostic/f"patrol_down_se_same_phase_{bg}_4x.png")
binding={"zip_sha256":sha(Z.read_bytes()),"zip_bytes":Z.stat().st_size,"zip_files":len(names),"source_sha256":sha((P/unit["source"].removeprefix("res://")).read_bytes()),"frame_hashes":[sha((P/f"output/enemy_patrol/move_down_right/f{i:02}.png").read_bytes()) for i in range(8)],"reference_move_sha256":sha((P/"reference/enemy_patrol/move_down.png").read_bytes()),"author_leg_roi":{"path":"qa/patrol_se_eight_legs_8x.png","sha256":sha((P/"qa/patrol_se_eight_legs_8x.png").read_bytes()),"size":Image.open(P/"qa/patrol_se_eight_legs_8x.png").size},"diagnostics":{f.name:sha(f.read_bytes()) for f in diagnostic.glob("*.png")},"scope":"visual bound input; not approval from hashes or GPU"}
(OUT/"visual-binding.json").write_text(json.dumps(binding,indent=2),encoding="utf-8")
print(json.dumps({"zip_files":len(names),"legs_roi":binding["author_leg_roi"]["size"],"source":binding["source_sha256"]}))
