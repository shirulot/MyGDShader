"""c002固定静态证据审查，生产只读；无需引擎。"""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from collections import Counter
from io import BytesIO
import hashlib
import json
from PIL import Image, ImageChops

ROOT = Path("E:/dev/shader/godot-shader/godot-shader-simple")
OUT = Path(__file__).resolve().parent
PACKAGE = OUT / "package"
ZIP = ROOT / "art-source/ember/deliveries/enemy_calibration_v013_c002_2026-10-06.zip"
EXPECTED = "d4b327e220a049a81114994fe05cd9cdf7c02502d1703693c523ef70c4c9e0d7"
def sha(raw): return hashlib.sha256(raw).hexdigest()
def image(raw): return Image.open(BytesIO(raw)).convert("RGBA")
def load(z, name): return json.loads(z.read(name).decode("utf-8-sig"))
assert sha(ZIP.read_bytes()) == EXPECTED
report = {"zip_sha256": EXPECTED, "zip_bytes": ZIP.stat().st_size, "members": []}
with ZipFile(ZIP) as z:
    assert z.testzip() is None
    infos = [r for r in z.infolist() if not r.is_dir()]
    assert len(infos) == len({r.filename for r in infos})
    for item in infos:
        name = item.filename
        parsed = PurePosixPath(name)
        assert not parsed.is_absolute() and "\\" not in name and ":" not in name and ".." not in parsed.parts
        target = (PACKAGE / name).resolve()
        assert target.is_relative_to(PACKAGE.resolve())
        raw = z.read(item)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        report["members"].append({"path": name, "bytes": len(raw), "sha256": sha(raw), "crc32": f"{item.CRC:08x}"})
    report["entries"] = len(infos)
    report["crc_all_pass"] = True
with ZipFile(ZIP) as z:
    manifest = load(z, "manifest.json")
    assert len(manifest) == len({r["path"] for r in manifest}) == 19
    assert {r["path"] for r in manifest} | {"manifest.json"} == set(z.namelist())
    for item in manifest:
        raw = z.read(item["path"])
        assert len(raw) == item["bytes"] and sha(raw) == item["sha256"]
    report["manifest_payload_verified"] = 19
    catalog = load(z, "catalog.json")
    registration = load(z, "calibration_registration_v002.json")
    assert sha(z.read("calibration_registration_v002.json")) == catalog["registration_sha256"]
    assert catalog["columns"] == ["approved_down", "generated_front", "down_left", "down_right"]
    units = [u["unit"] for u in registration["units"]]
    assert units == ["enemy_patrol", "enemy_scout_drone"]
    report["catalog_registration_sha256"] = catalog["registration_sha256"]
    report["registration"] = []
    for unit in registration["units"]:
        source_path = "source/" + unit["source"].split("/")[-1]
        assert sha(z.read(source_path)) == unit["source_sha256"]
        source = image(z.read(source_path))
        scale = unit["common_scale"]
        assert 0 < scale < 1
        assert len(unit["views"]) == 3
        assert not any("scale" in view or "frame" in view for view in unit["views"])
        views = []
        for view in unit["views"]:
            r = view["source_rect"]
            assert r[0] >= 0 and r[1] >= 0 and r[0]+r[2] <= source.width and r[1]+r[3] <= source.height
            anchor = view["source_anchor"]
            views.append({"direction": view["direction"], "source_rect": r, "source_anchor": anchor,
                "derived_once_offset_xy": [64-anchor[0]*scale, unit["target_anchor_y"]-anchor[1]*scale]})
        report["registration"].append({"unit": unit["unit"], "source_path": source_path,
            "source_sha256": unit["source_sha256"], "source_size": list(source.size),
            "single_isotropic_scale": scale, "target_anchor": [64,unit["target_anchor_y"]],
            "anchor_definition": unit["anchor_definition"], "views": views,
            "scope": "declaration and field consistency verified; not independently re-rendered"})
    rows = catalog["rows"]
    assert len(rows) == 8
    assert [(r["unit"],r["view"]) for r in rows] == [(u,c) for u in units for c in catalog["columns"]]
    report["pngs"] = []
    imgs = []
    for row in rows:
        path = row["path"].removeprefix("res://calibration_check_v002/")
        raw = z.read(path)
        assert sha(raw) == row["sha256"]
        img = image(raw)
        assert img.size == (128,128)
        bbox = img.getchannel("A").getbbox()
        alpha = Counter(img.getchannel("A").get_flattened_data())
        if "registration" in row:
            view = next(v for u in registration["units"] if u["unit"] == row["unit"] for v in u["views"] if v["direction"] == row["view"])
            assert row["registration"] == view
        report["pngs"].append({"path": path, "sha256": sha(raw), "size": [128,128],
            "bbox_xywh": [bbox[0],bbox[1],bbox[2]-bbox[0],bbox[3]-bbox[1]],
            "alpha_histogram": dict(sorted(alpha.items())), "partial_alpha_pixels": sum(n for a,n in alpha.items() if 0<a<255)})
        imgs.append(img)
    baseline = ROOT / "art-source/ember/deliveries/enemy_sequences_v012_2026-10-06.zip"
    assert sha(baseline.read_bytes()) == "42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe"
    report["v012_fixed_zip_sha256"] = sha(baseline.read_bytes())
    report["old_down"] = []
    with ZipFile(baseline) as bz:
        recipe = load(bz, "assembly_recipe.json")
        for unit in units:
            clip = next(c for c in recipe["clips"] if c["unit"]==unit and c["action"]=="idle_down")
            raw = z.read(unit+"/approved_down.png")
            assert sha(raw) == clip["frame_hashes"][0]
            atlas_raw = bz.read(clip["atlas"].removeprefix("res://"))
            assert sha(atlas_raw) == clip["atlas_sha256"]
            assert image(atlas_raw).crop((0,0,128,128)).tobytes() == image(raw).tobytes()
            report["old_down"].append({"unit": unit, "sha256": sha(raw), "v012_frame0_hash_match": True, "v012_atlas_first_frame_full_rgba_equal": True})
    report["contact_sheets"] = []
    for bg in ["black","white"]:
        base = (0,0,0,255) if bg=="black" else (255,255,255,255)
        expected = Image.new("RGBA",(512,256),base)
        for index,img in enumerate(imgs):
            expected.paste(Image.alpha_composite(Image.new("RGBA",(128,128),base),img),((index%4)*128,(index//4)*128))
        actual = image(z.read("comparison_"+bg+"_1x.png"))
        actual4 = image(z.read("comparison_"+bg+"_4x.png"))
        assert actual.size == (512,256) and actual4.size == (2048,1024)
        diff = ImageChops.difference(expected,actual).convert("RGB")
        max_delta = max(b for a,b in diff.getextrema())
        over1 = sum(max(px)>1 for px in diff.get_flattened_data())
        exact_nearest = actual4.tobytes()==actual.resize((2048,1024),Image.Resampling.NEAREST).tobytes()
        assert max_delta <= 1 and over1 == 0 and exact_nearest
        report["contact_sheets"].append({"background":bg,"max_rgb_delta_vs_independent_alpha_composite":max_delta,
            "native_pixels_over1_delta":over1,"actual_4x_nearest_exact":exact_nearest})
        for index,unit in enumerate(units):
            # 使用整行固定128画布ROI；没有bbox移底或居中。
            row = actual.crop((0,index*128,512,(index+1)*128))
            for factor in [4,8]:
                dest = OUT/"diagnostics"/(unit+"_"+bg+"_"+str(factor)+"x.png")
                dest.parent.mkdir(parents=True,exist_ok=True)
                row.resize((512*factor,128*factor),Image.Resampling.NEAREST).save(dest)
report["status"] = "STATIC_INTEGRITY_PASS_ONLY"
report["scope"] = "two units x four 128 canvases, approved down + generated front/SW/SE; no style/action acceptance"
(OUT / "integrity-data.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k:report[k] for k in ["status","entries","manifest_payload_verified","contact_sheets","old_down"]},ensure_ascii=False,indent=2))
