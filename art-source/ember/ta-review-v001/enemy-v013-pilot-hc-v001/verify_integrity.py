"""固定包只读技术核验；只在此审查目录解包和保存证据。"""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from PIL import Image
import hashlib, io, json, math

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "art-source/ember/enemy-eight-directions-v013-pilot-hc-v001"
PACKAGE = OUT / "package"
ZIP = ROOT / "art-source/ember/deliveries/enemy_eight_directions_v013_pilot_hc_v001_2026-10-06.zip"
UNITS = ["enemy_tracked_heavy", "enemy_cutter"]
def sha(data): return hashlib.sha256(data).hexdigest()
def load(path): return json.loads(path.read_text(encoding="utf-8-sig"))
def img(path): return Image.open(path).convert("RGBA")
def resolve(path): return PACKAGE / path.removeprefix("res://")
report = {}
assert sha(ZIP.read_bytes()) == "5db52757c74fc537b3f45d87abdbab8c58e5d8fcd3cf6366153f7b32ef98b9ef"
with ZipFile(ZIP) as z:
    names = z.namelist()
    assert len(names) == len(set(names)) == 121
    for name in names:
        pure = PurePosixPath(name)
        assert not pure.is_absolute() and ".." not in pure.parts and ":" not in name and "\\" not in name
        assert not ((z.getinfo(name).external_attr >> 16) & 0o170000) == 0o120000
    assert z.testzip() is None
    manifest = json.loads(z.read("manifest.json"))
    assert len(manifest) == 120
    assert {m["path"] for m in manifest} | {"manifest.json"} == set(names)
    members = []
    for item in manifest:
        data = z.read(item["path"])
        assert len(data) == item["bytes"] and sha(data) == item["sha256"]
        assert (SOURCE / item["path"]).read_bytes() == data
        members.append({**item, "zip_and_frozen_source_match": True})
    assert (SOURCE / "manifest.json").read_bytes() == z.read("manifest.json")
    for name in names:
        target = PACKAGE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(z.read(name))
report["archive"] = {"sha256": sha(ZIP.read_bytes()), "bytes": ZIP.stat().st_size, "entries": 121, "payload": 120, "crc_path_duplicate_checks": "PASS", "manifest_sha256": sha((PACKAGE / "manifest.json").read_bytes()), "members": members}
rig = load(PACKAGE / "pilot_rigs.json")
catalog = load(PACKAGE / "output/pilot_catalog_v013.json")
assert rig["enabled_pilot_units"] == UNITS
assert set(rig["paused_for_static_revision"]) == {"enemy_patrol", "enemy_scout_drone"}
assert [c["unit"] for c in catalog["clips"]] == UNITS
assert catalog["root"] == rig["root"] == [64,104] and catalog["canvas"] == rig["canvas"] == [128,128]
assert catalog["rig_spec_sha256"] == sha((PACKAGE / "pilot_rigs.json").read_bytes())
assert catalog["rig_script_sha256"] == sha((PACKAGE / "pilot_rig.gd").read_bytes())
assert sorted(p.name for p in (PACKAGE / "output").glob("*_pilot_v013.tres")) == sorted(u+"_pilot_v013.tres" for u in UNITS)
report["pilot_scope"] = {"enabled": UNITS, "paused": rig["paused_for_static_revision"], "no_paused_unit_pilot_tres": True, "root": [64,104], "canvas": [128,128]}
report["frames"] = []
for clip in catalog["clips"]:
    assert clip["action"] == "move_down_right" and clip["fps"] == 8 and clip["loop"] and clip["frame_count"] == 8
    atlas = img(resolve(clip["atlas"]))
    assert atlas.size == (1024,128) and sha(resolve(clip["atlas"]).read_bytes()) == clip["atlas_sha256"]
    assert sha(resolve(clip["tres"]).read_bytes()) == clip["tres_sha256"]
    for index in range(8):
        path = PACKAGE / f"output/{clip['unit']}/move_down_right/f{index:02}.png"
        frame = img(path)
        assert frame.size == (128,128)
        assert sha(path.read_bytes()) == clip["frame_hashes"][index]
        assert atlas.crop((index*128,0,(index+1)*128,128)).tobytes() == frame.tobytes()
        alpha = set(frame.getchannel("A").getdata())
        assert alpha <= {0,255}
        bbox = frame.getchannel("A").getbbox()
        assert 0 < bbox[0] and 0 < bbox[1] and bbox[2] < 128 and bbox[3] < 128
        pose = clip["poses"][index]
        assert pose["root"] == [64,104] and pose["frame"] == index and pose["unit"] == clip["unit"]
        report["frames"].append({"unit":clip["unit"],"frame":index,"sha256":sha(path.read_bytes()),"atlas_full_rgba_zero_diff":True,"size":[128,128],"alpha":sorted(alpha),"bbox_diagnostic_only":bbox})
    # 深浅1x/4x联系图只核实际导出帧的像素绑定。
    for bg, color in [("white",(255,255,255,255)),("black",(0,0,0,255))]:
        expected = Image.new("RGBA",atlas.size,color)
        expected.alpha_composite(atlas)
        assert expected.tobytes() == img(PACKAGE/f"qa/{clip['unit']}_move_{bg}_1x.png").tobytes()
        assert expected.resize((4096,512),Image.Resampling.NEAREST).tobytes() == img(PACKAGE/f"qa/{clip['unit']}_move_{bg}_4x.png").tobytes()

baseline_zip = ROOT/"art-source/ember/deliveries/enemy_sequences_v012_2026-10-06.zip"
assert sha(baseline_zip.read_bytes()) == "42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe"
report["approved_down"] = []
baseline = load(PACKAGE/"approved_down_baseline.json")
with ZipFile(baseline_zip) as z:
    for unit in UNITS:
        old_entry = next(c for c in baseline["clips"] if c["unit"] == unit and c["action"] == "move_down")
        old_name = next(n for n in z.namelist() if n.endswith(f"/{unit}/move_down.png"))
        atlas_bytes = z.read(old_name)
        ref = PACKAGE/f"reference/{unit}/move_down.png"
        assert ref.read_bytes() == atlas_bytes and sha(atlas_bytes) == old_entry["atlas_sha256"]
        idle_name = next(n for n in z.namelist() if n.endswith(f"/{unit}/idle_down/f00.png"))
        old_idle = z.read(idle_name)
        for relative in [f"source/approved_down/{unit}.png", f"output/{unit}/neutral_down.png"]:
            assert (PACKAGE/relative).read_bytes() == old_idle
        report["approved_down"].append({"unit":unit,"reference_move_byte_equal_v012":True,"neutral_and_source_byte_equal_v012_idle_f00":True,"move_sha256":sha(atlas_bytes),"idle_f00_sha256":sha(old_idle)})

# 独立逐点差异，不引用作者的 changed_pixels/ pass_check。
report["bind_pose"] = []
for unit in UNITS:
    spec = next(u for u in rig["units"] if u["unit"] == unit)
    raw = img(resolve(spec["source"]))
    bind_path = PACKAGE/f"output/{unit}/rig_neutral_down_right.png"
    bind = img(bind_path)
    assert sha(resolve(spec["source"]).read_bytes()) == spec["source_sha256"]
    assert sha(bind_path.read_bytes()) == next(c for c in catalog["clips"] if c["unit"] == unit)["bind_sha256"]
    assert raw.size == bind.size == (128,128)
    changed = [[x,y] for y in range(128) for x in range(128) if raw.getpixel((x,y)) != bind.getpixel((x,y))]
    allowed = [(43,80,59,97),(71,77,86,96)] if unit == "enemy_cutter" else []
    outside = [p for p in changed if not any(x0<=p[0]<x1 and y0<=p[1]<y1 for x0,y0,x1,y1 in allowed)]
    assert not outside
    assert len(changed) == (83 if unit == "enemy_cutter" else 0)
    detail = [{"point":[x,y],"before":list(raw.getpixel((x,y))),"after":list(bind.getpixel((x,y)))} for x,y in changed]
    report["bind_pose"].append({"unit":unit,"changed_full_rgba_pixels":len(changed),"declared_front_regions_xyxy":allowed,"outside_change":outside,"protected_hull_tools_rear_armor_diff":0,"changes":detail})

registration = load(PACKAGE/"registration.json")
masters = load(PACKAGE/"output/master_catalog_v013.json")
assert masters["registration_sha256"] == sha((PACKAGE/"registration.json").read_bytes())
report["source_and_masters"] = []
for unit in UNITS:
    reg = next(u for u in registration["units"] if u["unit"] == unit)
    assert sha(resolve(reg["source"]).read_bytes()) == reg["source_sha256"]
    subset = [m for m in masters["masters"] if m["unit"] == unit]
    assert len(subset) == 8
    for m in subset:
        assert sha(resolve(m["path"]).read_bytes()) == m["sha256"]
        assert math.isclose(m["scale"],reg["common_scale"],rel_tol=1e-12)
    spec = next(u for u in rig["units"] if u["unit"] == unit)
    assert img(resolve(spec["source"])).tobytes() == img(PACKAGE/f"output/{unit}/neutral_down_right.png").tobytes()
    report["source_and_masters"].append({"unit":unit,"registered_master_rig_source_equal":True,"turnaround_sha256":reg["source_sha256"],"single_unit_scale":reg["common_scale"],"master_count":8,"hash_binding_only_no_generated_art_approval":True})

report["author_evidence"] = []
for relative in ["qa/pilot_gpu_roundtrip.json","qa/pilot_runtime.json","qa/pilot_pixel_audit.json"]:
    path = PACKAGE/relative
    data = load(path)
    assert data["catalog_sha256"] == sha((PACKAGE/"output/pilot_catalog_v013.json").read_bytes())
    assert data["status"] == "PASS"
    if relative.endswith("gpu_roundtrip.json"):
        assert len(data["records"]) == 32
        assert all(r["live_rig_vs_png_differing_channels"] == r["tres_vs_png_differing_channels"] == 0 for r in data["records"])
    if relative.endswith("runtime.json"):
        assert len(data["completed_loops"]) == len(data["seen_frames"]) == 8 and len(data["direction_switches"]) == 16
        assert all(len(frames) == 8 and set(frames) == set(range(8)) for frames in data["seen_frames"].values())
        assert all(item["pass"] for item in data["direction_switches"])
    report["author_evidence"].append({"path":relative,"sha256":sha(path.read_bytes()),"catalog_hash_match":True,"not_independent_execution":True})
report["status"] = "STATIC_TECHNICAL_PASS_PENDING_COLD_RESOURCE_CHECK"
(OUT/"integrity.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("BIND_PASS: archive120; frames16; atlases2; old down2; cutter bind83 inside declared regions; author evidence bound")
