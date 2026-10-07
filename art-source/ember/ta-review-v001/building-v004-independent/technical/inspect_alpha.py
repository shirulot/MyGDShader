"""正式资产 Alpha 的独立分布记录。连续淡出效果不等同于实体底图连续覆盖。"""
from pathlib import Path
from collections import Counter
from PIL import Image
import hashlib
import json

OUT = Path(__file__).resolve().parent
COLD = OUT / "cold-project"
catalog = json.loads((COLD / "assets/ember/building_assets_v004/catalog_v004.json").read_text(encoding="utf-8-sig"))
records = []
for building in catalog["buildings"]:
    relative = building["complete_texture"].removeprefix("res://")
    path = COLD / relative
    img = Image.open(path).convert("RGBA")
    histogram = Counter(img.getchannel("A").get_flattened_data())
    partial = sum(n for alpha, n in histogram.items() if 0 < alpha < 255)
    high = sum(histogram[a] for a in range(250, 255))
    records.append({
        "building": building["id"], "complete_png": relative,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": list(img.size), "alpha0": histogram[0], "alpha255": histogram[255],
        "partial_alpha_pixels": partial, "alpha250_to254": high,
        "alpha1_to249": partial - high,
        "alpha250_to254_fraction_of_partial": high / partial,
        "histogram": dict(sorted(histogram.items())),
    })
report = {
    "scope": "formal complete PNG intrinsic coverage; unmodified source masters are allowed to retain original alpha",
    "format_requirement": "docs/shader-learning/art-style-standard-v002.md:76",
    "records": records,
    "shader": {
        "path": "shaders/ember/building_intact_v004.gdshader",
        "original_texture_sample_line": 53, "output_line": 72,
        "hard_coverage_present": False,
        "effect_alpha_is_separate": "whole-shell modulate alpha 0.14 is a declared runtime occlusion effect",
    },
    "visible_neon_edge_claim": False,
    "conclusion": "FORMAL_BINARY_ALPHA_FORMAT_NEEDS_REVISION",
}
(OUT / "alpha-format-evidence.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps([{k: v for k, v in r.items() if k != "histogram"} for r in records], ensure_ascii=False, indent=2))
