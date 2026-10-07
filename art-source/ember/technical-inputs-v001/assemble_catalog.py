"""合并三组已实际生成的输入，不改变底图或制作方元数据。"""
from pathlib import Path
import hashlib
import json
from collections import Counter
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
PROOF = Path(__file__).resolve().parent
GROUPS = ("basic", "object-masks", "surfaces")
EXPECTED = {"D01": 5, "D02": 2, "D03": 2, "D04": 2, "D05": 1, "D06": 2,
            "D07": 2, "D08": 10, "D09": 3, "D10": 4, "D11": 6, "D12": 1}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assets, dependencies = [], {}
    for group in GROUPS:
        source = PROOF / group / "catalog.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        dependencies[source.relative_to(ROOT).as_posix()] = sha(source)
        for original in data["assets"]:
            entry = dict(original)
            path = ROOT / entry["file"].removeprefix("res://")
            assert path.is_file() and sha(path) == entry["sha256"], entry["id"]
            with Image.open(path) as image:
                assert list(image.size) == entry["canvas"], entry["id"]
                assert image.mode == entry["mode"], entry["id"]
            entry["producer_catalog"] = "res://" + source.relative_to(ROOT).as_posix()
            entry["mipmaps"] = entry["manifest_id"] in ("D11", "D12")
            entry["runtime_sampler"] = {
                "preview_filter": "Nearest with Mipmaps" if entry["manifest_id"] == "D11" else "Nearest",
                "recommendation_scope": "Producer LINEAR/filter notes are sampling recommendations; the supplied pixel-art preview and material use this runtime filter",
                "grass_weight": "No wind material is supplied; choose linear/nearest explicitly in your future sampler" if entry["manifest_id"] == "D12" else None}
            # Detect=0 会在编辑器使用法线/粗糙度图后自动修改导入设置。
            # 交付策略显式覆盖制作方历史建议，保留 RGB 和参数的原始数值。
            entry["import_policy"] = {"compression": "Lossless", "normal_map_compression": "Disabled",
                "roughness_processing": "Disabled", "detect_3d_compression": "Disabled",
                "godot_import_values": {"compress/mode": 0, "compress/normal_map": 2,
                    "roughness/mode": 1, "detect_3d/compress_to": 0},
                "supersedes_producer_import_recommendations": True,
                "fix_alpha_border": False, "premult_alpha": False, "normal_map_invert_y": False}
            # 常量参数、Mask、Normal和权重必须保持线性数值，颜色采样由使用者显式标记。
            entry.setdefault("sampling", "linear data; single channel .r; no source_color for data")
            assets.append(entry)
    assert Counter(a["manifest_id"] for a in assets) == Counter(EXPECTED)
    assert len({a["id"] for a in assets}) == 40
    assert len({a["file"] for a in assets}) == 40
    for group in GROUPS:
        for path in (PROOF / group).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                dependencies[path.relative_to(ROOT).as_posix()] = sha(path)
    catalog = {"schema_version": 1, "date": "2026-10-04", "status": "TECHNICAL_40_GENERATED_PENDING_GODOT",
        "art_units": 123, "technical_inputs": 40, "physical_pngs": 40,
        "scene_layout_masks": {"actual_count": 0, "budget_upper_bound": 30,
            "status": "LAYOUT_DEPENDENT", "reason": "现有布局未登记实际水面、露天降雨和热区；不以预算伪造图"},
        "assets": sorted(assets, key=lambda a: (a["manifest_id"], a["id"])),
        "producer_dependency_sha256": dependencies}
    target = ROOT / "assets/ember/data/technical_inputs_catalog_v001.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"40 inputs / 40 PNGs / {len(dependencies)} producer dependencies")

if __name__ == "__main__":
    main()
