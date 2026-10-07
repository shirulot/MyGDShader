"""封装当前83单元交付，保留v001历史包；只读生产PNG和来源。

必须已通过像素、美术与Godot验收。排除缓存/新工程副本/旧ZIP，避免重复计数。
包内MANIFEST为每个载荷文件的SHA256；包本身与CRC摘要写在包外，避免自引用。
"""
import hashlib
import json
from pathlib import Path
import zipfile

BATCH = Path(__file__).resolve().parents[1]
ROOT = BATCH.parents[2]
DELIVERIES = ROOT / "art-source/ember/deliveries"
ARCHIVE = DELIVERIES / "ember_assets_v002_2026-10-04.zip"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))

validation = read("art-source/ember/batch-02-robot/validation-production-v001.json")
catalog = read("assets/ember/characters/robot/robot_frames_catalog_v001.json")
review = read("art-source/ember/batch-02-robot/art-review-v001.json")
independent = read("art-source/ember/batch-02-robot/validation-frames-v001.json")
godot = read("art-source/ember/batch-02-robot/review/godot_validation_v001.json")
if (not validation.get("automated_png_and_catalog_checks_passed")
        or review.get("status") != "ROBOT_20_FRAME_VISUAL_REVIEW_PASS"
        or godot.get("status") != "GODOT_ROBOT_ANIMATION_VALIDATED"):
    raise SystemExit("缺少本批原生、视觉或实际Godot通过证据")
if (independent.get("independent_visual_review", {}).get("status") != "PASS"
        or not independent.get("independent_provenance_review", {}).get("passed")):
    raise SystemExit("独立20帧视觉/来源复核尚未通过")
delivery_proof = read("art-source/ember/batch-02-robot/review/godot-delivery-summary-v001.json")
if delivery_proof.get("status") != "GODOT_DELIVERY_AND_FRESH_REUSE_PASS":
    raise SystemExit("Godot最终执行摘要尚未通过")
fresh = read("art-source/ember/batch-02-robot/review/godot_fresh_validation_v001.json")
fresh_tiles = read("art-source/ember/batch-02-robot/review/godot_fresh_tileset_validation_v001.json")
fresh_copy = read("art-source/ember/batch-02-robot/review/godot-fresh-copy-manifest.json")
if (fresh.get("status") != "GODOT_ROBOT_ANIMATION_VALIDATED"
        or fresh_tiles.get("status") != "GODOT_RESOURCE_VALIDATED"
        or fresh_tiles.get("tile_count") != 62
        or fresh_copy.get("godot_cache_present_before_import") is not False
        or fresh_copy.get("autoload_present") is not False):
    raise SystemExit("缺少新工程、无原缓存的机器人与瓦片共同复用证据")
frame_hashes = {f["id"]: digest(ROOT / f["file"].removeprefix("res://")) for f in catalog["frames"]}
if (len(frame_hashes) != 20 or frame_hashes != review["frame_sha256"]
        or frame_hashes != {f["id"]: f["sha256"] for f in validation["frames"]}):
    raise SystemExit("当前20帧不对应验收版本")
if digest(ROOT / catalog["sheet"]["texture"].removeprefix("res://")) != catalog["sheet"]["sha256"]:
    raise SystemExit("atlas已改变")
for frame in catalog["frames"]:
    if frame["id"] == "robot_idle_down":
        continue
    note = read(frame["finishing_record"])
    if note["output_sha256"] != frame_hashes[frame["id"]]:
        raise SystemExit("整理记录对应的输出已变更：" + frame["id"])
    for path_key, hash_key in [("source", "source_sha256"), ("annotation", "annotation_sha256")]:
        if digest(ROOT / note[path_key]) != note[hash_key]:
            raise SystemExit("母稿/标注来源已变更：" + frame["id"])
    for dependency in note["dependencies"]:
        if digest(ROOT / dependency["path"]) != dependency["sha256"]:
            raise SystemExit("整理依赖已变更：" + frame["id"])
source_pngs = 0
for folder, count in [("batch-01", 7), ("tilesets-v001", 11), ("batch-02-robot", 19)]:
    ledger = read(f"art-source/ember/{folder}/generation-record.json")
    records = ledger.get("records", ledger.get("assets", []))
    if len(records) != count:
        raise SystemExit("生成来源数量不一致：" + folder)
    for record in records:
        archived = ROOT / record["file"]
        if digest(archived) != record["sha256"]:
            raise SystemExit("母稿归档哈希改变：" + record["id"])
        original = Path(record["source"])
        if not original.is_file() or digest(original) != record["sha256"]:
            raise SystemExit("母稿归档与实际工具输出不一致：" + record["id"])
        source_pngs += 1

def permitted(path):
    relative = path.relative_to(ROOT)
    # 只过滤目录名，保留fresh验证摘要/日志文件供追踪。
    return (path.is_file() and not any(p in {".godot", "__pycache__"} or p.startswith("fresh-")
                                     for p in relative.parts[:-1])
            and path.suffix not in {".pyc", ".zip", ".tmp"})

files = set()
for directory in ["assets/ember", "scenes/ember", "art-source/ember/batch-01",
                  "art-source/ember/tilesets-v001", "art-source/ember/batch-02-robot",
                  "art-source/ember/references", "art-source/ember/tilesets"]:
    files.update(p for p in (ROOT / directory).rglob("*") if permitted(p))
for p in (ROOT / "art-source/ember/audit-2026-10-04").iterdir():
    if permitted(p):
        files.add(p)
for name in ["art-generation-standard.md", "asset-generation-manifest.csv", "resources.md",
             "asset-production-batch-01.md", "asset-production-batch-02-robot.md", "tilemap-reusable-tilesets.md"]:
    files.add(ROOT / "docs/shader-learning" / name)
for name in ["build_ember_tilesets.gd", "build_ember_robot_animation.gd"]:
    path = ROOT / "tools" / name
    files.add(path)
    if path.with_suffix(path.suffix + ".uid").is_file():
        files.add(path.with_suffix(path.suffix + ".uid"))
files.add(ROOT / "art-source/ember/.gdignore")
names = [p.relative_to(ROOT).as_posix() for p in sorted(files)]
png_count = sum(n.startswith("assets/ember/") and n.endswith(".png") for n in names)
tres_count = sum(n.startswith("assets/ember/") and n.endswith(".tres") for n in names)
scene_count = sum(n.startswith("scenes/ember/") and n.endswith(".tscn") for n in names)
if (png_count, tres_count, scene_count, source_pngs) != (25, 5, 2, 37):
    raise SystemExit(f"正式文件或来源数量不一致：{png_count}/{tres_count}/{scene_count}/{source_pngs}")
payload_manifest = {
    "date": "2026-10-04", "completed_art_units": 83, "remaining_art_units": 40,
    "tiles": 62, "robot_frames": 20, "station_objects": 1,
    "production_png_files": 25, "resource_files": 5, "editable_scenes": 2,
    "actual_archived_master_outputs": 37,
    "files": {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(files)}
}
DELIVERIES.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(files):
        archive.write(path, path.relative_to(ROOT).as_posix())
    archive.writestr("DELIVERY-MANIFEST.json", json.dumps(payload_manifest, ensure_ascii=False, indent=2)+"\n")
with zipfile.ZipFile(ARCHIVE) as archive:
    if archive.testzip() is not None or len(archive.namelist()) != len(set(archive.namelist())):
        raise SystemExit("ZIP损坏或有重复路径")
    for name, sha in payload_manifest["files"].items():
        if hashlib.sha256(archive.read(name)).hexdigest() != sha:
            raise SystemExit("ZIP内容与工作区不同：" + name)
summary = {"archive": ARCHIVE.relative_to(ROOT).as_posix(), "bytes": ARCHIVE.stat().st_size,
           "sha256": digest(ARCHIVE), "crc_passed": True, "payload_files": len(files),
           "archive_entries": len(files)+1, "all_payload_sha256_match": True,
           "production_png_files": png_count, "tres_files": tres_count, "scene_files": scene_count,
           "source_outputs_verified": source_pngs, "completed_art_units": 83, "remaining_art_units": 40}
ARCHIVE.with_suffix(".package.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
