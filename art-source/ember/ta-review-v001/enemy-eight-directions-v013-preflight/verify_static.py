"""只读静态预检，固定候选四输入和其确实绑定的32neutral。无引擎/行为/动作审批。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from collections import Counter
import hashlib
import json
import re
from PIL import Image, ImageChops

ROOT = Path("E:/dev/shader/godot-shader/godot-shader-simple")
SOURCE = ROOT / "art-source/ember/enemy-eight-directions-v013"
INPUT = SOURCE / "static_preflight_v001"
OUT = Path(__file__).resolve().parent
BOUND = OUT / "bound"
BOUND.mkdir(parents=True, exist_ok=True)
def sha(data): return hashlib.sha256(data).hexdigest()
def image(data): return Image.open(BytesIO(data)).convert("RGBA")
def bbox_xywh(img):
    bbox = img.getchannel("A").getbbox()
    return [bbox[0], bbox[1], bbox[2]-bbox[0], bbox[3]-bbox[1]] if bbox else [0, 0, 0, 0]
names = ["eight_direction_masters_black_4x.png", "eight_direction_masters_white_4x.png",
         "registration.json", "master_catalog_v013.json"]
inputs = {n: (INPUT / n).read_bytes() for n in names}
for name, data in inputs.items(): (BOUND / name).write_bytes(data)
catalog = json.loads(inputs["master_catalog_v013.json"].decode("utf-8-sig"))
registration = json.loads(inputs["registration.json"].decode("utf-8-sig"))
report = {"scope": "32 neutral static first-gate evidence only; no action or style acceptance",
    "inputs": [{"path": name, "bytes": len(data), "sha256": sha(data)} for name, data in inputs.items()],
    "catalog_registration_sha_matches": sha(inputs["registration.json"]) == catalog["registration_sha256"],
    "current_registration_matches_bound": (SOURCE / "registration.json").read_bytes() == inputs["registration.json"],
    "masters": [], "changes": [], "baseline_down": [], "contact_sheets": []}
rows = catalog["masters"]
assert len(rows) == 32 and len({(r["unit"], r["direction"]) for r in rows}) == 32
expected_order = [(unit, direction) for unit in catalog["units"] for direction in catalog["directions"]]
assert [(r["unit"], r["direction"]) for r in rows] == expected_order
raws = {}
for row in rows:
    relative = row["path"].removeprefix("res://")
    path = SOURCE / relative
    raw = path.read_bytes()
    actual = sha(raw)
    raws[(row["unit"], row["direction"])] = raw
    img = image(raw)
    alpha = Counter(img.getchannel("A").get_flattened_data())
    bbox = bbox_xywh(img)
    declared = [int(v) for v in re.findall(r"\d+", row["bounds"])]
    data = {"unit": row["unit"], "direction": row["direction"], "path": relative,
        "catalog_sha256": row["sha256"], "current_sha256": actual, "matches_catalog": actual == row["sha256"],
        "size": list(img.size), "bbox_xywh": bbox, "declared_bbox_xywh": declared,
        "bbox_matches_catalog": bbox == declared, "alpha_histogram": dict(sorted(alpha.items())),
        "visible_pixels": sum(n for a, n in alpha.items() if a > 0),
        "partial_alpha_pixels": sum(n for a, n in alpha.items() if 0 < a < 255)}
    report["masters"].append(data)
    if actual != row["sha256"]:
        report["changes"].append({"path": relative, "expected": row["sha256"], "current": actual})
all_bound = not report["changes"]
report["neutral_snapshot_written"] = all_bound
if all_bound:
    for row in rows:
        target = BOUND / row["path"].removeprefix("res://")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raws[(row["unit"], row["direction"])])

# 原v012已通过固定包：只核四idle首帧，不重复20动作120帧。
baseline_zip = ROOT / "art-source/ember/deliveries/enemy_sequences_v012_2026-10-06.zip"
baseline_sha = sha(baseline_zip.read_bytes())
assert baseline_sha == "42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe"
report["v012_fixed_zip_sha256"] = baseline_sha
baseline_declared = json.loads((SOURCE / "approved_down_baseline.json").read_text(encoding="utf-8-sig"))
report["v013_baseline_declaration_sha256"] = sha((SOURCE / "approved_down_baseline.json").read_bytes())
with ZipFile(baseline_zip) as z:
    recipe_raw = z.read("assembly_recipe.json")
    recipe = json.loads(recipe_raw.decode("utf-8-sig"))
    prior = json.loads((ROOT / "art-source/ember/ta-review-v001/enemy-v012-independent/final-package-binding.json").read_text(encoding="utf-8-sig"))
    prior_hash = next(r["sha256"] for r in prior["checked_manifest"] if r["path"] == "assembly_recipe.json")
    assert sha(recipe_raw) == prior_hash
    report["v012_recipe_sha256"] = sha(recipe_raw)
    for row in (r for r in rows if r["direction"] == "down"):
        unit = row["unit"]
        neutral_raw = raws[(unit, "down")]
        approved_relative = next(u["approved_down"] for u in registration["units"] if u["unit"] == unit).removeprefix("res://")
        approved_raw = (SOURCE / approved_relative).read_bytes()
        clip = next(c for c in recipe["clips"] if c["unit"] == unit and c["action"] == "idle_down")
        declared = next(c for c in baseline_declared["clips"] if c["unit"] == unit and c["action"] == "idle_down")
        atlas_raw = z.read(clip["atlas"].removeprefix("res://"))
        atlas = image(atlas_raw)
        first = atlas.crop((0, 0, 128, 128))
        rgba_equal = first.tobytes() == image(neutral_raw).tobytes()
        item = {"unit": unit, "neutral_sha256": sha(neutral_raw), "source_approved_down_sha256": sha(approved_raw),
            "source_approved_down_bytes_equal": neutral_raw == approved_raw,
            "v012_idle_frame0_png_sha256": clip["frame_hashes"][0],
            "v013_baseline_declaration_matches_fixed_recipe": declared["frame_hashes"][0] == clip["frame_hashes"][0],
            "neutral_png_hash_matches_v012_frame0": sha(neutral_raw) == clip["frame_hashes"][0],
            "v012_idle_atlas_sha256": sha(atlas_raw),
            "v012_atlas_hash_matches_recipe": sha(atlas_raw) == clip["atlas_sha256"],
            "v012_atlas_frame0_full_rgba_equal": rgba_equal}
        report["baseline_down"].append(item)
        target = BOUND / "baseline-source-approved-down" / (unit + ".png")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(approved_raw)

# Godot先在1x深浅底blend，再Nearest4x。Pillow用整数round；Godot若截断可能有1级RGB差。
if all_bound:
    for background in ["black", "white"]:
        contact = image(inputs["eight_direction_masters_" + background + "_4x.png"])
        assert contact.size == (4096, 2048)
        bg = (0, 0, 0, 255) if background == "black" else (255, 255, 255, 255)
        cells = []
        for index, row in enumerate(rows):
            neutral = image(raws[(row["unit"], row["direction"])])
            expected = Image.alpha_composite(Image.new("RGBA", (128, 128), bg), neutral)
            x, y = (index % 8)*512, (index // 8)*512
            actual4 = contact.crop((x, y, x+512, y+512))
            actual1 = actual4.resize((128, 128), Image.Resampling.NEAREST)
            nearest_exact = actual4.tobytes() == actual1.resize((512, 512), Image.Resampling.NEAREST).tobytes()
            maximum = 0
            different = 0
            changed_over1 = 0
            for actual, expect in zip(actual1.get_flattened_data(), expected.get_flattened_data()):
                delta = max(abs(actual[c] - expect[c]) for c in range(3))
                maximum = max(maximum, delta)
                if delta: different += 1
                if delta > 1: changed_over1 += 1
            cells.append({"unit": row["unit"], "direction": row["direction"],
                "nearest_4x_blocks_exact": nearest_exact, "rgb_different_native_pixels": different,
                "maximum_rgb_delta": maximum, "native_pixels_over1_delta": changed_over1,
                "opaque_background_alpha": actual1.getchannel("A").getextrema() == (255, 255)})
        report["contact_sheets"].append({"background": background, "cells": cells,
            "rounding_contract": "Pillow integer-rounded alpha over black/white; RGB absolute delta <=1 acceptable for Godot truncation, 4x blocks exact"})
        # 原联系图直接裁，不重排/修色/重生成；每单位前4/后4列各一张，便于4x逐格看。
        for row_index, unit in enumerate(catalog["units"]):
            for start, label in [(0, "first4"), (2048, "last4")]:
                target = OUT / "diagnostic-crops" / (unit + "_" + label + "_" + background + "_4x.png")
                target.parent.mkdir(parents=True, exist_ok=True)
                contact.crop((start, row_index*512, start+2048, (row_index+1)*512)).save(target)

report["source_inputs_unchanged_after_check"] = all((INPUT/n).read_bytes() == data for n, data in inputs.items())
report["current_outputs_unchanged_after_check"] = all((SOURCE/r["path"].removeprefix("res://")).read_bytes() == raws[(r["unit"],r["direction"])] for r in rows)
baseline_ok = all(all(v for k, v in row.items() if isinstance(v, bool)) for row in report["baseline_down"])
contacts_ok = all(c["nearest_4x_blocks_exact"] and c["native_pixels_over1_delta"] == 0 and c["opaque_background_alpha"]
    for sheet in report["contact_sheets"] for c in sheet["cells"]) if all_bound else False
report["status"] = "STATIC_PREFLIGHT_BINDING_PASS" if (
    all_bound and baseline_ok and contacts_ok and report["catalog_registration_sha_matches"]
    and report["current_registration_matches_bound"]
    and report["source_inputs_unchanged_after_check"] and report["current_outputs_unchanged_after_check"]
    and all(r["bbox_matches_catalog"] and r["size"] == [128,128] for r in report["masters"])) else "STATIC_PREFLIGHT_BINDING_REQUIRES_ATTENTION"
(OUT / "integrity.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "changes": report["changes"],
    "partial_alpha_counts": sorted(set(r["partial_alpha_pixels"] for r in report["masters"])),
    "contact_rgb_different_pixels": [sum(c["rgb_different_native_pixels"] for c in s["cells"]) for s in report["contact_sheets"]],
    "contact_max_delta": [max(c["maximum_rgb_delta"] for c in s["cells"]) for s in report["contact_sheets"]],
    "baseline_down": report["baseline_down"]}, ensure_ascii=False, indent=2))
