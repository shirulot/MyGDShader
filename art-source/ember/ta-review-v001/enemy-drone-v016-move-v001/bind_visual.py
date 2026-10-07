"""Bind the submitted ZIP and make fixed-canvas visual diagnostics only."""
from pathlib import Path, PurePosixPath
import hashlib, json, zipfile
from PIL import Image, ImageChops, ImageDraw

base = Path(__file__).resolve().parent
root = base.parents[3]
zpath = root / "art-source/ember/deliveries/enemy_drone_eight_moves_v016_v001_2026-10-07.zip"
expected = "fde467201be49929e894d000dcad974bb49854b752f3341eef0ef04610c4ba9a"
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
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(archive.read(info))
manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8-sig"))
checks = {name: sha(package / name) == item["sha256"] and (package / name).stat().st_size == item["bytes"] for name, item in manifest["files"].items()}
assert all(checks.values()) and len(checks) == 163
data = {"zip_sha256": expected, "bytes": zpath.stat().st_size, "entries": len(members), "manifest_checks": checks,
        "catalog_sha256": sha(package / "output/catalog.json"), "rig_sha256": sha(package / "rig.json"),
        "frames": {}, "contact_checks": {}, "diagnostics_sha256": {}, "bound_author_evidence": {}}
directions = ["down_left", "left", "up_left", "up", "up_right", "right"]
all_frames = {}
for direction in directions:
    name = "move_" + direction
    frames = [Image.open(package / "output/enemy_scout_drone" / name / f"f{index:02}.png").convert("RGBA") for index in range(8)]
    all_frames[direction] = frames
    data["frames"][name] = [{"frame": index, "sha256": sha(package / "output/enemy_scout_drone" / name / f"f{index:02}.png"), "size": list(frame.size), "alpha": sorted(set(frame.getchannel("A").tobytes()))} for index, frame in enumerate(frames)]
    assert all(frame.size == (128,128) and set(frame.getchannel("A").tobytes()) == {0,255} for frame in frames)
    for color, bg in [("white", (255,255,255,255)), ("black", (0,0,0,255))]:
        sheet = Image.new("RGBA", (512,256), bg)
        for index, frame in enumerate(frames): sheet.alpha_composite(frame, ((index%4)*128,(index//4)*128))
        for scale in [1,4]:
            expected_image = sheet.resize((512*scale,256*scale),Image.Resampling.NEAREST).convert("RGB")
            actual = Image.open(package / "qa" / f"{name}_{color}_{scale}x.png").convert("RGB")
            data["contact_checks"][f"{name}_{color}_{scale}x"] = actual.size == expected_image.size and ImageChops.difference(actual,expected_image).getbbox() is None
    roi = Image.new("RGBA", (320,96), (255,255,255,255))
    for index, frame in enumerate(frames): roi.alpha_composite(frame.crop((24,44,104,92)), ((index%4)*80,(index//4)*48))
    expected_roi = roi.resize((1920,576),Image.Resampling.NEAREST).convert("RGB")
    actual_roi = Image.open(package / "qa" / f"rotors_{direction}_6x.png").convert("RGB")
    data["contact_checks"][f"rotors_{direction}_6x"] = actual_roi.size == expected_roi.size and ImageChops.difference(actual_roi,expected_roi).getbbox() is None
assert all(data["contact_checks"].values())
# Original canvas, identical placement, labels outside it. No bbox recentering.
for name, bg in [("light", (232,232,228,255)), ("dark", (25,42,52,255))]:
    image = Image.new("RGBA", (1124,792), bg)
    draw = ImageDraw.Draw(image)
    ink = (20,20,20,255) if name == "light" else (240,240,240,255)
    for index in range(8): draw.text((104+index*128,6),f"F{index:02}",fill=ink)
    for row, direction in enumerate(directions):
        draw.text((4,32+row*128),direction,fill=ink)
        for index, frame in enumerate(all_frames[direction]): image.alpha_composite(frame,(100+index*128,24+row*128))
    path = base / f"all_new_frames_{name}_1x.png"
    image.convert("RGB").save(path)
    data["diagnostics_sha256"][path.name] = sha(path)
for name in ["gpu_roundtrip.json","runtime.json","rotor_audit.json","pixel_audit.json"]:
    data["bound_author_evidence"][name] = sha(package / "qa" / name)
(base / "visual-binding.json").write_text(json.dumps(data, indent=2, ensure_ascii=False),encoding="utf-8")
print(json.dumps({"bytes":data["bytes"],"entries":len(members),"manifest":len(checks),"frames":48,"contact_checks":len(data["contact_checks"])},ensure_ascii=False))
