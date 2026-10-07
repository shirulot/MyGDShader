"""合并机器人修正版目录；旧版保持只读，20个姿态和8个动画ID保持兼容。"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
PROOF = Path(__file__).resolve().parent
TARGET = ROOT / "assets/ember/characters/robot/robot_frames_catalog_v002.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    original_path = ROOT / "assets/ember/characters/robot/robot_frames_catalog_v001.json"
    catalog = copy.deepcopy(read(original_path))
    record_path = PROOF / "repair-record-v002.json"
    record = read(record_path)
    repairs = {f["id"]: f for f in record["frames"]}
    assert len(repairs) == 16
    # 复用原生规则计算实际尺寸/色板/脚底；不会调用旧脚本的生成或标注写入函数。
    generator_path = ROOT / "art-source/ember/batch-02-robot/tools/finish_robot_frames.py"
    spec = importlib.util.spec_from_file_location("robot_original_measurement", generator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    changed_frames = []
    for frame in catalog["frames"]:
        if frame["state"] == "walk":
            new_path = ROOT / (frame["file"].removeprefix("res://").replace("_v001.png", "_v002.png"))
            repair = repairs[frame["id"]]
            assert new_path.is_file(), new_path
            assert sha(new_path) == repair["new_sha256"], frame["id"]
            frame["file"] = "res://" + new_path.relative_to(ROOT).as_posix()
            frame["sha256"] = sha(new_path)
            frame["status"] = "NATIVE_FRAME_V002_REPAIR_GENERATED"
            frame["source_use"] = "EDITABLE_NATIVE_RIG_AND_ANNOTATION_REPAIR_OF_V001"
            frame["finishing_record"] = "art-source/ember/robot-repair-v002/repair-record-v002.json"
            frame["finishing_record_frame_id"] = frame["id"]
            annotation_path = PROOF / "annotations" / f"walk_{frame['direction']}_f{frame['frame_index']:02d}.json"
            frame["runtime_windows"] = read(annotation_path)["runtime_windows"]
            frame["repair_changed_pixels"] = repair["changed_pixel_count"]
            if repair["changed_pixel_count"] > 0:
                changed_frames.append(frame["id"])
        path = ROOT / frame["file"].removeprefix("res://")
        assert sha(path) == frame["sha256"]
        with Image.open(path) as image:
            frame["measurement"] = module.measure(image.convert("RGBA"), frame["state"])
    sheet_path = ROOT / "assets/ember/characters/robot/robot_animations_v002.png"
    sheet = Image.open(sheet_path).convert("RGBA")
    assert sheet.size == (320, 384)
    for frame in catalog["frames"]:
        x, y = frame["coord"]
        source = Image.open(ROOT / frame["file"].removeprefix("res://")).convert("RGBA")
        assert sheet.crop((x * 64, y * 96, (x + 1) * 64, (y + 1) * 96)).tobytes() == source.tobytes()
    catalog["sheet"]["texture"] = "res://" + sheet_path.relative_to(ROOT).as_posix()
    catalog["sheet"]["sha256"] = sha(sheet_path)
    # 目录记录实际生成事实；最终视觉/引擎合格结论由独立验收报告承载，不循环修改SHA。
    catalog.update({"date": "2026-10-04", "revision": "v002", "status": "NATIVE_ROBOT_20_FRAMES_V002_REPAIR_GENERATED",
        "scope": "C01 repair: four original idle PNGs reused unchanged; sixteen versioned walk PNGs and one atlas; no new art units or collect action",
        "new_frames_in_batch": 16, "pixel_changed_frame_count": len(changed_frames), "pixel_changed_frames": changed_frames,
        "repair_record": record_path.relative_to(ROOT).as_posix(), "repair_record_sha256": sha(record_path),
        "supersedes": "res://assets/ember/characters/robot/robot_frames_catalog_v001.json",
        "supersedes_catalog_sha256": sha(original_path),
        "art_review": "art-source/ember/robot-repair-v002/independent-repair-review.json",
        "acceptance_report": "art-source/ember/robot-repair-v002/final-acceptance.json"})
    dependencies = {record_path.relative_to(ROOT).as_posix(): sha(record_path), generator_path.relative_to(ROOT).as_posix(): sha(generator_path)}
    for folder in (PROOF / "annotations", PROOF / "finished-frames"):
        for path in folder.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                dependencies[path.relative_to(ROOT).as_posix()] = sha(path)
    new_generator = PROOF / "tools/generate_repair.py"
    dependencies[new_generator.relative_to(ROOT).as_posix()] = sha(new_generator)
    catalog["repair_dependency_sha256"] = dependencies
    TARGET.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Robot v002 catalog: 20 frames / 16 walk revisions / {len(changed_frames)} pixel-changed frames / {len(dependencies)} bound dependencies")


if __name__ == "__main__":
    main()
