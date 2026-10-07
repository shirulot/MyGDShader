"""Bind frozen D17 input and reproduce only the chart presentation."""
from pathlib import Path, PurePosixPath
import json, hashlib, zipfile
from PIL import Image, ImageChops, ImageDraw

base = Path(__file__).resolve().parent
root = base.parents[3]
zpath = root / "art-source/ember/deliveries/enemy_drone_idle_hit_v017_v001_2026-10-07.zip"
expected = "19b3ba844e5df945292953520fa17a3c5a8a0c8bbf7a852a8fdd56d8e3773d05"
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(zpath) == expected
package = base / "package"
package.mkdir(exist_ok=True)
with zipfile.ZipFile(zpath) as archive:
    assert archive.testzip() is None
    members = [info for info in archive.infolist() if not info.is_dir()]
    assert len({info.filename.casefold() for info in members}) == len(members)
    for info in members:
        path = PurePosixPath(info.filename)
        assert not path.is_absolute() and ".." not in path.parts and ":" not in info.filename and "\\" not in info.filename
        dest = package.joinpath(*path.parts)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(archive.read(info))
manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8-sig"))
checks = {name: sha(package / name) == item["sha256"] and (package / name).stat().st_size == item["bytes"] for name,item in manifest["files"].items()}
assert all(checks.values()) and len(checks) == 211
data = {"zip_sha256":expected,"bytes":zpath.stat().st_size,"entries":len(members),"manifest_checks":checks,
        "catalog_sha256":sha(package / "output/catalog.json"),"rig_sha256":sha(package / "rig.json"),
        "frames":{},"contact_checks":{},"identity_checks":{},"recovery_checks":{},"diagnostics_sha256":{},"bound_author_evidence":{}}
directions = ["down_left","left","up_left","up","up_right","right","down_right"]
all_frames = {}
prior = base.parent / "enemy-drone-v016-move-v001/package"
visible_equal = lambda a,b: a.size == b.size and a.tobytes() == b.tobytes()
for direction in directions:
    all_frames[direction] = {}
    for action in ["idle","hit"]:
        name = action+"_"+direction
        frames = [Image.open(package / f"output/enemy_scout_drone/{name}/f{index:02}.png").convert("RGBA") for index in range(4)]
        all_frames[direction][action] = frames
        data["frames"][name] = [{"frame":index,"sha256":sha(package / f"output/enemy_scout_drone/{name}/f{index:02}.png"),"size":list(frame.size),"alpha":sorted(set(frame.getchannel("A").tobytes()))} for index,frame in enumerate(frames)]
        assert all(frame.size == (128,128) and set(frame.getchannel("A").tobytes()) == {0,255} for frame in frames)
        for color,bg in [("white",(255,255,255,255)),("black",(0,0,0,255))]:
            contact=Image.new("RGBA",(512,128),bg)
            for index,frame in enumerate(frames):contact.alpha_composite(frame,(index*128,0))
            for scale in [1,4]:
                wanted=contact.resize((512*scale,128*scale),Image.Resampling.NEAREST).convert("RGB")
                actual=Image.open(package / f"qa/{name}_{color}_{scale}x.png").convert("RGB")
                data["contact_checks"][f"{name}_{color}_{scale}x"]=actual.size==wanted.size and ImageChops.difference(actual,wanted).getbbox() is None
        contact=Image.new("RGBA",(320,48),(255,255,255,255))
        for index,frame in enumerate(frames):contact.alpha_composite(frame.crop((24,44,104,92)),(index*80,0))
        wanted=contact.resize((1920,288),Image.Resampling.NEAREST).convert("RGB")
        actual=Image.open(package / f"qa/detail_{name}_6x.png").convert("RGB")
        data["contact_checks"][f"detail_{name}_6x"]=actual.size==wanted.size and ImageChops.difference(actual,wanted).getbbox() is None
    idle,hit=all_frames[direction]['idle'],all_frames[direction]['hit']
    data["recovery_checks"][direction]={"hit_f03_equals_f00_rgba":visible_equal(hit[3],hit[0]),"idle_f00_equals_hit_f00_rgba":visible_equal(idle[0],hit[0])}
    # v016 neutral_* is the raw static master; compare to the actual rotor bind F00.
    oldbind=Image.open(prior / f"output/enemy_scout_drone/move_{direction}/f00.png").convert("RGBA")
    data["identity_checks"][direction]={"source_png_bytes_equal_v016":(package / f"source/{direction}.png").read_bytes()==(prior / f"source/{direction}.png").read_bytes(),"f00_rgba_equal_v016_actual_move_f00":visible_equal(idle[0],oldbind)}
assert all(data["contact_checks"].values())
assert all(all(record.values()) for record in data["recovery_checks"].values())
assert all(all(record.values()) for record in data["identity_checks"].values())
for name,bg in [("light",(232,232,228,255)),("dark",(25,42,52,255))]:
    image=Image.new("RGBA",(1124,920),bg)
    draw=ImageDraw.Draw(image)
    ink=(20,20,20,255) if name=='light' else (240,240,240,255)
    for column in range(8):draw.text((104+column*128,6),f"{'idle' if column<4 else 'hit'} F{column%4:02}",fill=ink)
    for row,direction in enumerate(directions):
        draw.text((4,32+row*128),direction,fill=ink)
        frames=all_frames[direction]['idle']+all_frames[direction]['hit']
        for column,frame in enumerate(frames):image.alpha_composite(frame,(100+column*128,24+row*128))
    path=base / f"all_new_frames_{name}_1x.png"
    image.convert("RGB").save(path)
    data['diagnostics_sha256'][path.name]=sha(path)
for name in ['gpu_roundtrip.json','runtime.json','pose_audit.json','pixel_audit.json']:
    data['bound_author_evidence'][name]=sha(package / 'qa' / name)
(base / 'visual-binding.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'bytes':data['bytes'],'entries':len(members),'manifest':len(checks),'new_frames':56,'contacts':len(data['contact_checks']),'neutral_identity_checks':14,'recovery_checks':14},ensure_ascii=False))
