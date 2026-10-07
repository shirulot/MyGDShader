"""记录制作负责人已经完成的首批原生视觉审查，不编辑任何 PNG。

首批4种地板现在位于通用atlas；机器人只完成原授权的朝下待机1帧。
源文件/输出文件哈希把本次审查限定到实际版本，重做不会自动获得通过。
"""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
FINISH = ROOT / "art-source/ember/batch-01/pixel-finish-v001"
records = json.loads((FINISH / "finishing-record.json").read_text(encoding="utf-8"))
layout_path = FINISH / "object-layout-v001.json"
layout = json.loads(layout_path.read_text(encoding="utf-8"))
layout_by_id = {item["id"]: item for item in layout["assets"]}
if len(layout_by_id) != 2 or set(layout_by_id) != {item["id"] for item in records}:
    raise SystemExit("窗口与分层记录必须完整覆盖本批两个对象")
for item in records:
    output = ROOT / item["output"]
    if hashlib.sha256((ROOT / item["source"]).read_bytes()).hexdigest() != item["source_sha256"]:
        raise SystemExit("原始母稿已变更，不能复用本次审查")
    item["output_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    # 窗口位置来自对这个确切PNG版本的只读审查；换图后必须重新核对坐标。
    object_layout = layout_by_id[item["id"]]
    if item["output"] != object_layout["file"] or item["output_sha256"] != object_layout["sha256"]:
        raise SystemExit("对象PNG与已审查的窗口/分层版本不一致，不能复用本次记录")
    item["runtime_layout"] = {key: value for key, value in object_layout.items()
                              if key not in {"id", "file", "sha256", "canvas"}}
    item["visual_status"] = "PRODUCER_VISUAL_REVIEW_PASS"
(FINISH / "finishing-record.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
# 保留原数值测量，只补充同一来源的窗口、静帧和分层约定。
measurements_path = FINISH / "measurements.json"
measurements = json.loads(measurements_path.read_text(encoding="utf-8"))
records_by_id = {item["id"]: item for item in records}
for item in measurements["assets"]:
    item["runtime_layout"] = records_by_id[item["id"]]["runtime_layout"]
measurements["layout_metadata_source"] = str(layout_path.relative_to(ROOT)).replace("\\", "/")
measurements_path.write_text(json.dumps(measurements, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
catalog_path = ROOT / "assets/ember/environment/tilesets/ember_tiles_catalog_v001.json"
catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
ground = next(atlas for atlas in catalog["atlases"] if atlas["id"] == "ground_details")
floor_units = [{"id": tile["id"], "texture": ground["texture"], "atlas_coord": tile["coord"],
                "native_size": [32, 32], "status": "PRODUCER_VISUAL_REVIEW_PASS"}
               for tile in ground["tiles"] if tile["category"] == "T01"]
report = {
    "date": "2026-10-04", "timezone": "Asia/Irkutsk",
    "status": "FIRST_BATCH_NATIVE_6_OF_6_ART_REVIEW_PASS",
    "first_batch_art_units": 6, "native_object_pngs": 2,
    "floor_units_in_atlas": floor_units,
    "object_units": [{"id": item["id"], "file": item["output"], "sha256": item["output_sha256"]} for item in records],
    "robot_animation_completed": "1 of 20 frames; downward idle only",
    "producer_review": ["原生与整数2倍对象轮廓、原生4倍统一地板比例", "锚点、Alpha、16色及静止中性窗口",
                        "四地板3×3自身平铺与全部16类型相邻"],
    "independent_object_review": "art-source/ember/batch-01/pixel-finish-v001/validation-objects-independent.json",
    "object_layout_metadata": "art-source/ember/batch-01/pixel-finish-v001/object-layout-v001.json",
    "native_scale_board": "art-source/ember/references/batch01_native_scale_v002.png",
    "scale_board_scope": "机器人、采能站与地板；未包含尚未生成的门及控制台，不宣称完整R01。",
    "total_completed_art_units": 64, "full_art_budget": 123, "remaining_art_units": 59,
    "scope": "素材交付；没有自动补其余角色帧或替换现有游戏场景。",
}
(FINISH / "acceptance-v001.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"first_batch_completed": 6, "total_completed_art_units": 64, "remaining": 59}, ensure_ascii=False))
