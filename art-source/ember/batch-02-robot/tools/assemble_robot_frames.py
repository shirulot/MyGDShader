"""组装已整理的20帧及图集；--promote要求本次视觉审查和自动验收通过。

原朝下待机只读，其他帧按PNG原字节复制；组装图集不增加艺术单元数。
默认写art-source工作目录，未审查的图像不会自动进入正式assets。
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
from PIL import Image


BATCH = Path(__file__).resolve().parents[1]
ROOT = BATCH.parents[2]
PRODUCTION = ROOT / "assets/ember/characters/robot"
ORIGINAL_SHA = "c65f68455554edb03aea0a7b7b3cea6e1a779fa9d5aa49cba9b4aa5c4f6fbfff"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--promote", action="store_true", help="按已审查哈希复制正式帧、图集和目录")
    args = parser.parse_args()
    plan = json.loads((BATCH / "planned-catalog-v001.json").read_text(encoding="utf-8"))
    catalog = copy.deepcopy(plan)
    original = PRODUCTION / "robot_idle_down_v001.png"
    if digest(original) != ORIGINAL_SHA:
        raise SystemExit("原朝下待机已变更，停止组装")
    old_layout = json.loads((ROOT / "art-source/ember/batch-01/pixel-finish-v001/object-layout-v001.json").read_text(encoding="utf-8"))
    down_layout = next(item for item in old_layout["assets"] if item["id"] == "C01")
    sources, notes = {}, {}
    # 先确认输入齐全；缺一帧时不保存半成品图集。
    missing = []
    for frame in catalog["frames"]:
        is_original = frame["id"] == "robot_idle_down"
        source = original if is_original else BATCH / "finished-frames" / (frame["id"] + "_v001.png")
        note = source.with_suffix(".finish.json")
        if not source.is_file() or (not is_original and not note.is_file()):
            missing.append(frame["id"])
        else:
            sources[frame["id"]] = source
            if not is_original:
                notes[frame["id"]] = json.loads(note.read_text(encoding="utf-8"))
    if missing:
        raise SystemExit("尚缺已整理帧/来源记录：" + ", ".join(missing))
    atlas = Image.new("RGBA", (320, 384), (0, 0, 0, 0))
    for frame in catalog["frames"]:
        frame_id = frame["id"]
        source = sources[frame_id]
        with Image.open(source) as im:
            rgba = im.convert("RGBA")
            if rgba.size != (64, 96):
                raise SystemExit("输入必须是64×96：" + frame_id)
            # paste完整RGBA，保留包括透明像素在内的逐像素一致性。
            col, row = frame["coord"]
            atlas.paste(rgba, (col * 64, row * 96))
        frame["sha256"] = digest(source)
        frame["file"] = "res://" + relative(source)
        frame["status"] = "NATIVE_CANDIDATE_VISUAL_REVIEW_REQUIRED"
        if frame_id == "robot_idle_down":
            frame["source_use"] = "EXISTING_ACCEPTED_FRAME_UNCHANGED"
            frame["runtime_windows"] = down_layout["windows"]
        else:
            note = notes[frame_id]
            if note.get("output_sha256") != frame["sha256"]:
                raise SystemExit("整理记录与帧像素哈希不一致：" + frame_id)
            mother = ROOT / note["source"]
            annotation = ROOT / note["annotation"]
            if digest(mother) != note["source_sha256"] or digest(annotation) != note["annotation_sha256"]:
                raise SystemExit("母稿或原生标注与整理版本不一致：" + frame_id)
            for dependency in note["dependencies"]:
                if digest(ROOT / dependency["path"]) != dependency["sha256"]:
                    raise SystemExit("整理所用idle/rig已变更：" + frame_id)
            frame["source_use"] = note["source_use"]
            frame["finishing_record"] = relative(source.with_suffix(".finish.json"))
            frame["runtime_windows"] = note["runtime_windows"]
            frame["measurement"] = note["measurement"]
        frame["emitter_points"] = []
        frame["emission_baked"] = False
        frame["layering"] = "single_flattened_rgba_frame; native rig masks are editable source annotations, not runtime component layers"
        frame["tiling"] = "NONE_OBJECT_SPRITE"
    atlas_path = BATCH / "robot_animations_native_v001.png"
    atlas.save(atlas_path)
    catalog["status"] = "NATIVE_CANDIDATES_VISUAL_REVIEW_REQUIRED"
    catalog["sheet"]["texture"] = "res://" + relative(atlas_path)
    catalog["sheet"]["sha256"] = digest(atlas_path)
    catalog["anchor_convention"] = "固定虚拟脚底原点(32,80)，idle可见底边80；walk抬脚允许可见底边78..80，画布/节点offset不随帧改变。"
    catalog["new_frames_in_batch"] = 19
    candidate_path = BATCH / "frames-catalog-v001.json"
    save_json(candidate_path, catalog)
    if args.promote:
        review = json.loads((BATCH / "art-review-v001.json").read_text(encoding="utf-8"))
        validation = json.loads((BATCH / "validation-frames-v001.json").read_text(encoding="utf-8"))
        expected_hashes = {frame["id"]: frame["sha256"] for frame in catalog["frames"]}
        # 验收报告也必须对应当前输入，避免复用旧版的通过布尔值。
        measured_hashes = {frame["id"]: frame["sha256"] for frame in validation.get("frames", [])}
        if (review.get("status") != "ROBOT_20_FRAME_VISUAL_REVIEW_PASS"
                or review.get("frame_sha256") != expected_hashes
                or measured_hashes != expected_hashes
                or validation.get("sheet", {}).get("sha256") != catalog["sheet"]["sha256"]
                or not validation.get("automated_png_and_catalog_checks_passed")):
            raise SystemExit("缺少绑定这20帧的视觉/自动验收通过记录，不能推广")
        # 已存在但不同的同版本新帧需要先解决版本冲突，避免静默覆盖。
        for frame in catalog["frames"]:
            target = PRODUCTION / (frame["id"] + "_v001.png")
            if target.exists() and digest(target) != frame["sha256"]:
                raise SystemExit("正式同版本帧已不同，停止覆盖：" + frame["id"])
        PRODUCTION.mkdir(parents=True, exist_ok=True)
        for frame in catalog["frames"]:
            target = PRODUCTION / (frame["id"] + "_v001.png")
            if frame["id"] != "robot_idle_down":
                shutil.copyfile(sources[frame["id"]], target)
            frame["file"] = "res://" + relative(target)
            frame["status"] = "NATIVE_FRAME_ART_REVIEW_PASS"
        target_atlas = PRODUCTION / "robot_animations_v001.png"
        shutil.copyfile(atlas_path, target_atlas)
        catalog["sheet"]["texture"] = "res://" + relative(target_atlas)
        catalog["status"] = "NATIVE_ROBOT_20_FRAMES_ART_REVIEW_PASS"
        catalog["art_review"] = relative(BATCH / "art-review-v001.json")
        save_json(PRODUCTION / "robot_frames_catalog_v001.json", catalog)
    if digest(original) != ORIGINAL_SHA:
        raise SystemExit("原朝下待机意外改变")
    print(json.dumps({"native_frames": 20, "new_frames": 19, "promoted": args.promote,
                      "atlas": relative(atlas_path), "original_down_idle_unchanged": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
