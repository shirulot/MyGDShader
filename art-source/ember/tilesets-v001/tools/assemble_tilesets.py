"""把已整理的单块原生 PNG 按稳定坐标装为三套 atlas。

装配不插值、不改色、不增加空格为瓦片。先输出 art-source 候选供检查；
只有显式 --promote 才把同样的字节复制到生产目录并写生产坐标目录。
运行前须先执行三个 finish_* 脚本，之后用只读验收器与视觉拼接图审核。
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys

from PIL import Image


ROOT = Path(__file__).resolve().parents[4]
BATCH = ROOT / "art-source/ember/tilesets-v001"
PLANNED = json.loads((BATCH / "planned-catalog-v001.json").read_text(encoding="utf-8"))
PALETTE = {tuple(bytes.fromhex(value)) for value in (
    "101820", "182631", "2B3E4B", "4D6470", "829BA3", "BECBC4", "7B4D35", "B77C4B",
    "E2B77A", "51C5C2", "E5A44B", "E65B4A", "566B78", "203A4B", "406B78", "ECE9D8")}
CATALOG = copy.deepcopy(PLANNED)
CATALOG["status"] = "NATIVE_ASSEMBLED_REQUIRES_ART_REVIEW"
CATALOG["native_pixel_scale"] = 1
NATIVE = BATCH / "native-atlases"
NATIVE.mkdir(parents=True, exist_ok=True)
records = []

for atlas in CATALOG["atlases"]:
    group = atlas["id"]
    tiles_dir = BATCH / "finished-tiles" / group
    record_path = tiles_dir / "finish-record.json"
    if not record_path.is_file():
        raise SystemExit(f"像素整理记录未完成：{group}")
    group_records = json.loads(record_path.read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in group_records}
    if len(by_id) != len(atlas["tiles"]):
        raise SystemExit(f"实际单块数量不匹配：{group}")
    image = Image.new("RGBA", tuple(atlas["planned_size"]))
    for tile in atlas["tiles"]:
        tile_id = tile["id"]
        if tile_id not in by_id:
            raise SystemExit(f"缺少单块整理记录：{tile_id}")
        source_path = tiles_dir / f"{tile_id}.png"
        source = Image.open(source_path).convert("RGBA")
        if source.size != (32, 32):
            raise SystemExit(f"单块并非原生32×32：{tile_id}")
        for pixel in source.get_flattened_data():
            if pixel[3] not in (0, 255) or (pixel[3] > 0 and pixel[:3] not in PALETTE):
                raise SystemExit(f"单块Alpha/调色板不合格：{tile_id}")
            if tile["alpha_mode"] == "opaque" and pixel[3] != 255:
                raise SystemExit(f"地板含透明像素：{tile_id}")
        x, y = tile["coord"]
        # 整块复制 RGBA，无 premultiplied Alpha 或 blend 舍入。
        image.paste(source, (x * 32, y * 32))
        record = by_id[tile_id]
        tile["interfaces"] = record["interfaces"]
        tile.pop("interfaces_status", None)
        tile["status"] = "NATIVE_ASSEMBLED_REQUIRES_ART_REVIEW"
        tile["pixel_finish_record"] = record_path.relative_to(ROOT).as_posix()
        if "layout_topology" in record:
            tile["layout_topology"] = record["layout_topology"]
        records.append(record)
    filename = f"{group}_v001.png"
    output = NATIVE / filename
    image.save(output)
    atlas["texture"] = "res://" + output.relative_to(ROOT).as_posix()
    atlas["size"] = atlas.pop("planned_size")
    atlas["sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()

candidate_catalog = BATCH / "native-catalog-v001.json"
candidate_catalog.write_text(json.dumps(CATALOG, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(BATCH / "pixel-finish-record.json").write_text(json.dumps({
    "date": "2026-10-04", "method": "AI_ASSISTED_NATIVE_PIXEL_FINISH",
    "authorization_context": "用户在已提出脚本像素整理方案后回复继续，按当前方案执行。",
    "masters_unchanged": True, "native_tile_size": [32, 32], "tile_count": len(records),
    "tiles": records,
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if "--promote" in sys.argv:
    # 根代理在只读自动检查与连接图人工审阅后调用，不将候选自动视为合格。
    validation_path = BATCH / "validation-native-atlases.json"
    if not validation_path.is_file():
        raise SystemExit("缺少原生atlas验收报告，拒绝进入生产目录")
    report = json.loads(validation_path.read_text(encoding="utf-8"))
    if report.get("automated_png_and_catalog_checks_passed") is not True or report.get("interface_metadata_complete") is not True:
        raise SystemExit("原生atlas自动规则尚未通过，拒绝进入生产目录")
    production = ROOT / "assets/ember/environment/tilesets"
    production.mkdir(parents=True, exist_ok=True)
    for atlas in CATALOG["atlases"]:
        filename = f"{atlas['id']}_v001.png"
        shutil.copyfile(NATIVE / filename, production / filename)
        atlas["texture"] = "res://" + (production / filename).relative_to(ROOT).as_posix()
        for tile in atlas["tiles"]:
            tile["status"] = "NATIVE_PIXEL_FINISHED_ART_REVIEWED"
    CATALOG["status"] = "NATIVE_PIXEL_FINISHED_ART_REVIEWED"
    (production / "ember_tiles_catalog_v001.json").write_text(json.dumps(CATALOG, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(json.dumps({"native_atlases": len(CATALOG["atlases"]), "native_tiles": len(records),
                  "promoted": "--promote" in sys.argv}, ensure_ascii=False))
