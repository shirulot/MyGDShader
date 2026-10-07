"""封装通用瓦片母稿或正式交付包；只读取 PNG，不绘制或编辑图片。

默认封装母稿与布局规格；--production 额外要求 62 块验收及 Godot 通过证据。
两种模式均保存母稿 Alpha/颜色测量，母稿测量本身不代表原生瓦片通过验收。
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import zipfile

from PIL import Image


ROOT = Path(__file__).resolve().parents[4]
BATCH = ROOT / "art-source/ember/tilesets-v001"
RECORD = json.loads((BATCH / "generation-record.json").read_text(encoding="utf-8"))
CATALOG = json.loads((BATCH / "planned-catalog-v001.json").read_text(encoding="utf-8"))
PRODUCTION = "--production" in sys.argv


def pixel_data(image: Image.Image):
    """兼容项目现有 Pillow；仅遍历像素，不编辑图片。"""
    # 较新运行时提供 get_flattened_data，旧版则使用等价的 getdata。
    reader = getattr(image, "get_flattened_data", None)
    return reader() if reader is not None else image.getdata()


# 每个来源必须与工具原始输出逐字节相同；检查不修复任何图像。
measurements = []
for item in RECORD["records"]:
    copied = ROOT / item["file"]
    original = Path(item["source"])
    digest = hashlib.sha256(copied.read_bytes()).hexdigest()
    if not original.is_file() or hashlib.sha256(original.read_bytes()).hexdigest() != digest:
        raise SystemExit(f"母稿来源校验失败：{item['id']}")
    if digest != item["sha256"]:
        raise SystemExit(f"母稿记录校验失败：{item['id']}")
    with Image.open(copied) as source:
        rgba = source.convert("RGBA")
        alpha = Counter(pixel_data(rgba.getchannel("A")))
        colors = {pixel[:3] for pixel in pixel_data(rgba) if pixel[3] > 0}
        measurements.append({
            "id": item["id"], "file": item["file"], "size": list(source.size),
            "visible_bbox": rgba.getchannel("A").getbbox(),
            "alpha_levels": len(alpha), "alpha_zero_pixels": alpha[0],
            "alpha_opaque_pixels": alpha[255],
            "partial_alpha_pixels": sum(count for value, count in alpha.items() if 0 < value < 255),
            "visible_rgb_colors": len(colors), "sha256": digest,
            "source_bytes_verified": True,
            "status": "MASTER_MEASUREMENT_ONLY_NOT_NATIVE_TILE_ACCEPTANCE",
        })

planned_counts = {atlas["id"]: len(atlas["tiles"]) for atlas in CATALOG["atlases"]}
if planned_counts != {"ground_details": 12, "structures": 26, "utilities": 24}:
    raise SystemExit(f"规划数量与原预算不一致：{planned_counts}")
all_ids = []
for atlas in CATALOG["atlases"]:
    coords = [tuple(tile["coord"]) for tile in atlas["tiles"]]
    all_ids.extend(tile["id"] for tile in atlas["tiles"])
    width, height = atlas["planned_size"]
    if len(set(coords)) != len(coords) or any(
        x < 0 or y < 0 or (x + 1) * 32 > width or (y + 1) * 32 > height for x, y in coords
    ):
        raise SystemExit(f"规划坐标重复或越界：{atlas['id']}")
if len(set(all_ids)) != len(all_ids):
    raise SystemExit("规划瓦片 ID 重复")
if RECORD["successful_outputs"] != len(measurements) or len(measurements) != 11:
    raise SystemExit("本轮母稿数量记录不一致")
report = {
    "date": "2026-10-04", "source_pngs_verified": 11,
    "planned_tile_counts": planned_counts, "planned_tiles": 62,
    "approved_production_tiles": RECORD.get("approved_production_tiles", 0) if PRODUCTION else 0,
    "scope": "只读母稿测量；不表示像素、接缝、美术或 Godot 资源验收通过。",
    "masters": measurements,
}
(BATCH / "master-measurements.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
if "--measure-only" in sys.argv:
    print(json.dumps({"source_pngs_verified": 11, "planned_tile_counts": planned_counts,
                      "approved_production_tiles": 0}, ensure_ascii=False, indent=2))
    raise SystemExit(0)

required = [
    ROOT / "docs/shader-learning/tilemap-reusable-tilesets.md",
    ROOT / "docs/shader-learning/resources.md",
    ROOT / "docs/shader-learning/asset-generation-manifest.csv",
    ROOT / "tools/build_ember_tilesets.gd",
    ROOT / "assets/ember/README.md",
]
for path in required:
    if not path.is_file():
        raise SystemExit(f"交付文档尚未完成：{path.relative_to(ROOT)}")

files = set(required)
files.update(path for path in BATCH.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
# 复用的是本项目上轮新生成的四种地板与设备配色参考，不引入旧美术。
previous = ROOT / "art-source/ember/batch-01"
for kind in ("clean", "worn", "grate", "wet"):
    files.add(previous / f"generated/floor_{kind}_master_v001.png")
files.add(previous / "generated/station_master_v001.png")
files.add(previous / "generation-record.json")
files.add(previous / "masters.sha256")
files.update(previous.glob("prompts/*.txt"))

if PRODUCTION:
    production = ROOT / "assets/ember/environment/tilesets"
    catalog_path = production / "ember_tiles_catalog_v001.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    validation_path = ROOT / "art-source/ember/tilesets/godot_validation_v001.json"
    godot_report = json.loads(validation_path.read_text(encoding="utf-8"))
    if godot_report.get("status") != "GODOT_RESOURCE_VALIDATED" or godot_report.get("tile_count") != 62:
        raise SystemExit("缺少Godot实际资源通过证据，不能封装为可用交付")
    if RECORD.get("approved_production_tiles") != 62:
        raise SystemExit("美术制作验收状态未确认62块")
    for atlas in catalog["atlases"]:
        png = ROOT / atlas["texture"].removeprefix("res://")
        if hashlib.sha256(png.read_bytes()).hexdigest() != atlas["sha256"]:
            raise SystemExit(f"生产PNG与验收版本不一致：{atlas['id']}")
    # .import保存UID和Lossless设置，Godot可在新项目中重建对应缓存。
    files.update(path for path in production.rglob("*") if path.is_file())
    files.add(ROOT / "scenes/ember/tileset_layout_sandbox.tscn")
    files.add(validation_path)
    files.add(ROOT / "art-source/ember/.gdignore")
    files.add(ROOT / "docs/shader-learning/art-generation-standard.md")
    # 同时带上原已授权首批的两个修正主体；4种地板已经包含在地面atlas里。
    files.add(ROOT / "assets/ember/characters/robot/robot_idle_down_v001.png")
    files.add(ROOT / "assets/ember/buildings/station/station_base_v001.png")
    files.add(ROOT / "art-source/ember/references/batch01_native_scale_v002.png")
    files.add(ROOT / "docs/shader-learning/asset-production-batch-01.md")
    files.update(path for path in previous.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    # 本次额外复核：只收入摘要、测量和日志，避免打包独立测试工程及其.godot缓存。
    audit = ROOT / "art-source/ember/audit-2026-10-04"
    if audit.is_dir():
        files.update(path for path in audit.iterdir() if path.is_file()
                     and path.suffix in {".json", ".log", ".txt"})

filename = "ember_reusable_tilesets_v001_2026-10-04.zip" if PRODUCTION else "ember_tileset_masters_2026-10-04.zip"
delivery = ROOT / "art-source/ember/deliveries" / filename
delivery.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(delivery, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(files):
        archive.write(path, path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(delivery) as archive:
    damaged = archive.testzip()
    if damaged:
        raise SystemExit(f"ZIP 完整性校验失败：{damaged}")
    names = archive.namelist()
    production_pngs = [name for name in names if name.startswith("assets/ember/") and name.endswith(".png")]
    if not PRODUCTION and production_pngs:
        raise SystemExit("母稿包不应混入尚未验收的生产 PNG")
    atlas_pngs = [name for name in production_pngs if name.startswith("assets/ember/environment/tilesets/")]
    if PRODUCTION and (len(atlas_pngs) != 3 or len(production_pngs) != 5):
        raise SystemExit("正式交付必须含三张生产atlas与首批两个原生主体")
    if PRODUCTION and len([name for name in names if name.endswith(".tres")]) != 4:
        raise SystemExit("正式交付必须包含三套独立TileSet与一套合并TileSet")
    new_masters = [name for name in names if name.startswith("art-source/ember/tilesets-v001/generated/")]
    if len(new_masters) != 11:
        raise SystemExit("本轮母稿未完整封装")
print(json.dumps({
    "archive": delivery.relative_to(ROOT).as_posix(), "bytes": delivery.stat().st_size,
    "files": len(names), "source_pngs_verified": 11, "planned_tiles": 62,
    "approved_production_tiles": 62 if PRODUCTION else 0,
    "production_png_files": 5 if PRODUCTION else 0,
    "completed_art_units_including_first_batch_objects": 64 if PRODUCTION else 0,
}, ensure_ascii=False, indent=2))
