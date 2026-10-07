#!/usr/bin/env python3
"""只读验收 C01 的四方向 20 帧与对应图集，不生成、修复或保存图片。

本批目录格式由 planned-catalog-v001.json 定义：顶层 canvas / anchor /
bbox_limit / directions / palette，frames 是含 id、direction、state、
frame_index、file、coord、anchor、sha256 的列表；animations 明确帧序和
fps；sheet 明确 texture、size、columns、rows 及 frame_id -> coord。
图片路径使用 res:// 或项目相对路径。帧序是每方向 idle 一帧、walk f00..03。

--planning 只确认目录结构与已存在图片，允许尚未制作的 19 帧和图集缺失。
规划检查退出 0 不代表 PNG 或动画已完成。最终模式要求全部 20 帧、图集与
版本哈希完整；退出 0 仍只代表自动规则通过，不能代替动画视觉审查。

示例（从项目根目录运行）：
  python art-source/ember/batch-02-robot/tools/validate_robot_frames.py \
    --catalog art-source/ember/batch-02-robot/planned-catalog-v001.json --planning
  python art-source/ember/batch-02-robot/tools/validate_robot_frames.py \
    --catalog art-source/ember/batch-02-robot/frames-catalog-v001.json \
    --json art-source/ember/batch-02-robot/validation-frames-v001.json

仅 --json 写独立 JSON 报告。脚本使用长期存在的 getpixel / tobytes 等只读
Pillow API，兼容本机 Pillow 12.0，不依赖 get_flattened_data。
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

from PIL import Image


PROJECT = Path(__file__).resolve().parents[4]
CANVAS = [64, 96]
ANCHOR = [32, 80]
BBOX_LIMIT = [40, 64]
DIRECTIONS = ["down", "left", "right", "up"]
BASELINE_FILE = "assets/ember/characters/robot/robot_idle_down_v001.png"
BASELINE_SHA256 = "c65f68455554edb03aea0a7b7b3cea6e1a779fa9d5aa49cba9b4aa5c4f6fbfff"
PALETTE_HEX = (
    "#101820", "#182631", "#2B3E4B", "#4D6470", "#829BA3", "#BECBC4",
    "#7B4D35", "#B77C4B", "#E2B77A", "#51C5C2", "#E5A44B", "#E65B4A",
    "#566B78", "#203A4B", "#406B78", "#ECE9D8",
)
PALETTE = {tuple(bytes.fromhex(value[1:])) for value in PALETTE_HEX}
# 这三种运行状态由 Shader / 独立效果表达，不能烘焙进本批中性 base。
STATE_COLORS = {tuple(bytes.fromhex(value)) for value in ("51C5C2", "E5A44B", "E65B4A")}
MANUAL_CHECKS = [
    "四方向仍是同一机器人，比例、装甲、关节和原生像素尺度一致。",
    "上向可读为背面，左右可读为对应侧面，保持俯视三分之四正交视角。",
    "工具始终在解剖左前臂；遮挡合理，未因左右镜像换手或翻转左上光照。",
    "双腿交替接触/经过，支撑脚接地；动作不是整张站姿平移或局部噪点。",
    "臂腿反向摆动，工具受控；头身轻微起伏不改变世界锚点。",
    "逐帧、8 FPS 与末帧接首帧播放均无跳位、肢体增减、色块闪烁或滑步。",
    "待机进入/退出行走自然；窗口定位随姿势登记，背向遮挡不画成前窗。",
    "原生及整数 2 倍在透明、浅色、深色底上检查轮廓和 Alpha 描边。",
]


def rule(name: str, passed: bool, actual: object, expected: object) -> dict:
    return {"name": name, "passed": bool(passed), "actual": actual, "expected": expected}


def integer(value: object) -> bool:
    # bool 是 Python int 的子类，目录中的 true 不应被当作坐标 1。
    return isinstance(value, int) and not isinstance(value, bool)


def pair(value: object) -> bool:
    return isinstance(value, list) and len(value) == 2 and all(integer(v) and v >= 0 for v in value)


def valid_sha(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdefABCDEF" for c in value)


def resolve_file(value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("图片路径须为非空 res:// 或项目相对路径")
    path = PROJECT / value[6:] if value.startswith("res://") else Path(value)
    if not path.is_absolute():
        path = PROJECT / path
    resolved = path.resolve()
    if not resolved.is_relative_to(PROJECT):
        raise ValueError("图片路径不能越出项目目录")
    return resolved


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def spans(positions: list[int]) -> list[list[int]]:
    """把 y=79 候选接地点整理为半开区间；这并不能识别解剖意义上的脚。"""
    groups = []
    for position in positions:
        if groups and groups[-1][1] == position:
            groups[-1][1] += 1
        else:
            groups.append([position, position + 1])
    return groups


def foot_rule(state: str, bbox: list[int] | None, support_pixels_y79: int) -> dict:
    """虚拟锚点不随可见脚底移动；侧视远脚投影本来就高于近脚。

    idle 的近脚仍接到边界 80。walk 在近脚抬起至多 2 像素时允许可见
    底边界为 78..80；不能补假像素或拉长远脚来满足 y79。实际支撑腿/
    抬腿含义仍由逐帧 annotations 和视觉审查确认，不能仅用 bbox 推断。
    """
    bottom = None if bbox is None else bbox[3]
    walking = state == "walk"
    passed = (bottom is not None and 78 <= bottom <= 80) if walking else (bottom == 80 and support_pixels_y79 > 0)
    return rule("foot_projection_boundary", passed,
                {"state": state, "visible_bottom_boundary_y": bottom,
                 "opaque_pixels_at_y79": support_pixels_y79, "fixed_virtual_anchor": ANCHOR},
                "walk visible bottom 78..80; fixed anchor (32,80)" if walking else
                "idle visible bottom 80 with opaque contact pixels at y79; fixed anchor (32,80)")


def measure_frame(path: Path, declaration: dict, planning: bool) -> tuple[dict, list[tuple] | None]:
    """只读取解码后的 RGBA；透明像素的隐藏 RGB 也保留给图集精确比对。"""
    report = {"id": declaration["id"], "file": declaration["file"], "checks": []}
    checks = report["checks"]
    with Image.open(path) as opened:
        report.update(size=list(opened.size), source_mode=opened.mode, sha256=sha256(path))
        checks.append(rule("png_format", opened.format == "PNG", opened.format, "PNG"))
        checks.append(rule("native_canvas", list(opened.size) == CANVAS, list(opened.size), CANVAS))
        alpha_supported = "A" in opened.getbands() or "transparency" in opened.info
        checks.append(rule("real_alpha_channel", alpha_supported, alpha_supported, True))
        declared_sha = declaration.get("sha256")
        checks.append(rule("declared_sha256_present", planning or valid_sha(declared_sha), declared_sha, "64 hex characters in final mode"))
        if declared_sha is not None:
            checks.append(rule("declared_sha256_matches", valid_sha(declared_sha) and report["sha256"] == declared_sha.lower(), report["sha256"], declared_sha))
        # 错尺寸已失败，不遍历可能非常大的模型母稿，也不把它缩小后重新验收。
        if list(opened.size) != CANVAS:
            report["pixel_measurement_status"] = "SKIPPED_WRONG_NATIVE_CANVAS"
            return report, None
        rgba = opened.convert("RGBA")
        pixels = [rgba.getpixel((x, y)) for y in range(96) for x in range(64)]

    alpha = Counter(pixel[3] for pixel in pixels)
    colors = Counter(pixel[:3] for pixel in pixels if pixel[3] > 0)
    visible = [(index % 64, index // 64) for index, pixel in enumerate(pixels) if pixel[3] > 0]
    bbox = None if not visible else [min(x for x, _ in visible), min(y for _, y in visible),
                                    max(x for x, _ in visible) + 1, max(y for _, y in visible) + 1]
    subject_size = None if bbox is None else [bbox[2] - bbox[0], bbox[3] - bbox[1]]
    support = [x for x in range(64) if pixels[79 * 64 + x][3] == 255]
    off_palette = sum(count for color, count in colors.items() if color not in PALETTE)
    baked_state = sum(count for color, count in colors.items() if color in STATE_COLORS)
    report.update(
        bbox_exclusive=bbox, subject_size=subject_size, transparent_pixels=alpha[0],
        semi_transparent_pixels=sum(count for a, count in alpha.items() if 0 < a < 255),
        opaque_pixels=alpha[255], visible_rgb_color_count=len(colors),
        off_palette_pixels=off_palette, baked_state_color_pixels=baked_state,
        candidate_ground_support_x_spans=spans(support),
        visible_bottom_boundary_y=None if bbox is None else bbox[3],
        fixed_virtual_anchor=ANCHOR,
        visible_contact_at_anchor_boundary=bool(support),
        visible_centroid=None if not visible else [round(sum(x + 0.5 for x, _ in visible) / len(visible), 4),
                                                  round(sum(y + 0.5 for _, y in visible) / len(visible), 4)],
    )
    checks.extend([
        rule("nonempty_subject", bbox is not None, bbox, "visible subject"),
        rule("binary_alpha", set(alpha) <= {0, 255}, sorted(alpha), [0, 255]),
        rule("transparent_padding", alpha[0] > 0, alpha[0], "> 0"),
        rule("fixed_16_color_palette", off_palette == 0, off_palette, 0),
        rule("no_baked_runtime_state_colors", baked_state == 0, baked_state, 0),
        rule("bbox_maximum", subject_size is not None and subject_size[0] <= 40 and subject_size[1] <= 64, subject_size, BBOX_LIMIT),
        foot_rule(declaration.get("state", "idle"), bbox, len(support)),
    ])
    # x=12..51 是标准建议位置；不把姿势允许的横向轮廓变化误写成硬性标准。
    report["suggested_x_envelope_12_to_51"] = bbox is not None and 12 <= bbox[0] and bbox[2] <= 52
    return report, pixels


def motion_metrics(first: list[tuple], second: list[tuple]) -> dict:
    """量化每次切帧及回环；数字只提示差异，不能证明步态正确。"""
    union = sum(a[3] > 0 or b[3] > 0 for a, b in zip(first, second))
    intersection = sum(a[3] > 0 and b[3] > 0 for a, b in zip(first, second))
    changed = sum(a != b and (a[3] > 0 or b[3] > 0) for a, b in zip(first, second))
    # 完全刚体平移也会让哈希不同。直接比较坐标到颜色的映射，只作为审阅提示。
    first_visible = {(i % 64, i // 64): pixel for i, pixel in enumerate(first) if pixel[3] > 0}
    second_visible = {(i % 64, i // 64): pixel for i, pixel in enumerate(second) if pixel[3] > 0}
    translation = None
    if first_visible and len(first_visible) == len(second_visible):
        dx = min(x for x, _ in second_visible) - min(x for x, _ in first_visible)
        dy = min(y for _, y in second_visible) - min(y for _, y in first_visible)
        if all(second_visible.get((x + dx, y + dy)) == color for (x, y), color in first_visible.items()):
            translation = [dx, dy]
    return {"visible_rgba_changed_pixels": changed,
            "alpha_changed_pixels": sum(a[3] != b[3] for a, b in zip(first, second)),
            "silhouette_iou": round(intersection / union, 6) if union else None,
            "changed_visible_fraction": round(changed / union, 6) if union else 0.0,
            "exact_whole_subject_translation": translation}


def rigid_motion_rule(transitions: list[dict]) -> dict:
    """脚底投影放宽不允许改用整张站姿平移来假装步态。"""
    rigid_shifts = [t for t in transitions if t["exact_whole_subject_translation"] not in (None, [0, 0])]
    return rule("walk_not_whole_sprite_translation", not rigid_shifts,
                [{"from": t["from"], "to": t["to"], "translation": t["exact_whole_subject_translation"]} for t in rigid_shifts],
                "no exact nonzero translation of the complete subject between poses")


def validate(catalog: dict, catalog_path: Path, planning: bool) -> dict:
    checks, warnings = [], []
    report = {"generated_utc": datetime.now(timezone.utc).isoformat(), "catalog_path": str(catalog_path),
              "tool": "validate_robot_frames.py / Pillow / read-only pixel and catalog checks",
              "validator_sha256": sha256(Path(__file__)),
              "mode": "PLANNING_STRUCTURE_ONLY" if planning else "READ_ONLY_PNG_AND_CATALOG",
              "checks": checks, "warnings": warnings, "frames": [], "animations": [], "motion": [],
              "sheet": {}, "manual_review_required": MANUAL_CHECKS, "png_modified": False}
    baseline_path = PROJECT / BASELINE_FILE
    baseline_before = sha256(baseline_path)
    checks.append(rule("original_down_idle_sha_hard_lock", baseline_before == BASELINE_SHA256, baseline_before, BASELINE_SHA256))
    checks.extend([
        rule("canvas_contract", catalog.get("canvas") == CANVAS, catalog.get("canvas"), CANVAS),
        rule("anchor_contract", catalog.get("anchor") == ANCHOR, catalog.get("anchor"), ANCHOR),
        rule("bbox_limit_contract", catalog.get("bbox_limit") == BBOX_LIMIT, catalog.get("bbox_limit"), BBOX_LIMIT),
        rule("four_direction_order", catalog.get("directions") == DIRECTIONS, catalog.get("directions"), DIRECTIONS),
        rule("fixed_palette_declaration", isinstance(catalog.get("palette"), list) and len(catalog["palette"]) == 16
             and all(isinstance(v, str) for v in catalog["palette"]) and {v.upper() for v in catalog["palette"]} == set(PALETTE_HEX),
             catalog.get("palette"), "the exact registered 16 colors"),
    ])
    raw_frames = catalog.get("frames")
    checks.append(rule("twenty_declared_frames", isinstance(raw_frames, list) and len(raw_frames) == 20,
                       len(raw_frames) if isinstance(raw_frames, list) else None, 20))
    frames, by_id, paths, pixels_by_id, missing = [], {}, {}, {}, []
    for number, frame in enumerate(raw_frames if isinstance(raw_frames, list) else []):
        if not isinstance(frame, dict):
            checks.append(rule(f"frame_{number}_object", False, frame, "object"))
            continue
        frame_id = frame.get("id")
        valid_id = isinstance(frame_id, str) and bool(frame_id) and frame_id not in by_id
        checks.append(rule(f"frame_{number}_unique_id", valid_id, frame_id, "unique nonempty id"))
        if not valid_id:
            continue
        by_id[frame_id] = frame
        frames.append(frame)
        direction, state, index = frame.get("direction"), frame.get("state"), frame.get("frame_index")
        semantic = direction in DIRECTIONS and state in ("idle", "walk") and integer(index) and index in ([0] if state == "idle" else range(4))
        checks.append(rule(f"{frame_id}_direction_state_index", semantic, [direction, state, index], "four directions x (idle0 + walk0..3)"))
        checks.append(rule(f"{frame_id}_fixed_anchor", frame.get("anchor") == ANCHOR, frame.get("anchor"), ANCHOR))
        checks.append(rule(f"{frame_id}_sheet_coord", pair(frame.get("coord")), frame.get("coord"), "nonnegative [column,row]"))
        try:
            path = resolve_file(frame.get("file"))
            paths[frame_id] = path
        except ValueError as error:
            checks.append(rule(f"{frame_id}_project_png_path", False, str(error), "project PNG path"))
            continue
        if direction == "down" and state == "idle":
            checks.append(rule("down_idle_reuses_original_path", path == baseline_path.resolve(), str(path), str(baseline_path)))
            checks.append(rule("down_idle_declared_hard_lock", frame.get("sha256") == BASELINE_SHA256, frame.get("sha256"), BASELINE_SHA256))
        if not path.is_file():
            missing.append(frame_id)
            if not planning:
                checks.append(rule(f"{frame_id}_png_exists", False, str(path), "existing PNG"))
            continue
        try:
            measured, pixels = measure_frame(path, frame, planning)
            report["frames"].append(measured)
            if pixels is not None:
                pixels_by_id[frame_id] = pixels
            if not measured.get("suggested_x_envelope_12_to_51", True):
                warnings.append({"id": frame_id, "note": "bbox is outside suggested x=12..51; visually review placement, do not auto-recenter"})
        except (OSError, ValueError) as error:
            checks.append(rule(f"{frame_id}_readable_png", False, str(error), "readable PNG"))

    role_counts = Counter((f.get("direction"), f.get("state"), f.get("frame_index"))
                          for f in frames if isinstance(f.get("direction"), str) and isinstance(f.get("state"), str)
                          and integer(f.get("frame_index")))
    expected_roles = {(d, s, i) for d in DIRECTIONS for s in ("idle", "walk") for i in ([0] if s == "idle" else range(4))}
    checks.append(rule("complete_four_idle_sixteen_walk_roles", set(role_counts) == expected_roles and all(v == 1 for v in role_counts.values()),
                       [{"role": list(k), "count": v} for k, v in role_counts.items()], "every required role exactly once"))
    checks.append(rule("unique_single_frame_paths", len(set(paths.values())) == 20, len(set(paths.values())), 20))

    raw_animations = catalog.get("animations")
    checks.append(rule("eight_animations", isinstance(raw_animations, list) and len(raw_animations) == 8,
                       len(raw_animations) if isinstance(raw_animations, list) else None, 8))
    animation_roles = []
    for number, animation in enumerate(raw_animations if isinstance(raw_animations, list) else []):
        if not isinstance(animation, dict):
            checks.append(rule(f"animation_{number}_object", False, animation, "object"))
            continue
        direction, state = animation.get("direction"), animation.get("state")
        expected_ids = [f["id"] for f in sorted(
            [f for f in frames if f.get("direction") == direction and f.get("state") == state and integer(f.get("frame_index"))],
            key=lambda f: f["frame_index"])]
        animation_roles.append((direction, state))
        fps = animation.get("fps")
        valid_fps = isinstance(fps, (float, int)) and not isinstance(fps, bool) and math.isfinite(fps) and fps > 0
        animation_checks = [rule("explicit_frame_order", animation.get("frame_ids") == expected_ids and bool(expected_ids),
                                 animation.get("frame_ids"), expected_ids),
                            rule("positive_playback_fps", valid_fps, fps, "finite number > 0"),
                            rule("loop_declaration", animation.get("loop") is True, animation.get("loop"), True)]
        report["animations"].append({"id": animation.get("id"), "checks": animation_checks,
                                     "direction": direction, "state": state, "frame_ids": animation.get("frame_ids"),
                                     "fps": fps, "preview_effective_fps": None if state == "idle" else fps,
                                     "cycle_seconds": 4 / fps if state == "walk" and valid_fps else None})
    checks.append(rule("unique_required_animation_roles", len(animation_roles) == 8 and set(animation_roles) == {(d, s) for d in DIRECTIONS for s in ("idle", "walk")},
                       animation_roles, "one idle and one walk animation per direction"))

    # 不把 SHA 不同或颜色随机变化当成动画质量。仅完全无可见变化的循环硬失败。
    for direction in DIRECTIONS:
        group = sorted([f for f in frames if f.get("direction") == direction and f.get("state") == "walk" and integer(f.get("frame_index"))], key=lambda f: f["frame_index"])
        if len(group) != 4 or not all(f["id"] in pixels_by_id for f in group):
            report["motion"].append({"direction": direction, "status": "PENDING_FOUR_READABLE_FRAMES"})
            continue
        transitions = []
        for index in range(4):
            first, second = group[index], group[(index + 1) % 4]
            metric = motion_metrics(pixels_by_id[first["id"]], pixels_by_id[second["id"]])
            transitions.append({"from": first["id"], "to": second["id"], "loop_join": index == 3, **metric})
            if metric["visible_rgba_changed_pixels"] == 0:
                warnings.append({"direction": direction, "from": first["id"], "to": second["id"],
                                 "note": "identical visible neighboring poses; manually review gait phase"})
            elif metric["exact_whole_subject_translation"] is not None:
                warnings.append({"direction": direction, "from": first["id"], "to": second["id"],
                                 "note": "only the whole subject translates; changed pixels do not establish a walk pose",
                                 "translation": metric["exact_whole_subject_translation"]})
        motion_check = rule("walk_has_visible_cross_frame_changes", any(t["visible_rgba_changed_pixels"] > 0 for t in transitions),
                            [t["visible_rgba_changed_pixels"] for t in transitions], "at least one visible change; gait still needs review")
        report["motion"].append({"direction": direction, "status": "MEASURED_NOT_ART_ACCEPTANCE",
                                 "checks": [motion_check, rigid_motion_rule(transitions)], "transitions": transitions})

    sheet = catalog.get("sheet")
    sheet_checks, sheet_report = [], {"checks": []}
    sheet_report["checks"] = sheet_checks
    report["sheet"] = sheet_report
    checks.append(rule("sheet_object", isinstance(sheet, dict), type(sheet).__name__, "object"))
    if isinstance(sheet, dict):
        columns, rows = sheet.get("columns"), sheet.get("rows")
        sheet_checks.extend([rule("five_columns_four_rows", [columns, rows] == [5, 4], [columns, rows], [5, 4]),
                             rule("sheet_native_size_declaration", sheet.get("size") == [320, 384], sheet.get("size"), [320, 384])])
        mapping = sheet.get("frames")
        sheet_checks.append(rule("twenty_sheet_mappings", isinstance(mapping, list) and len(mapping) == 20,
                                 len(mapping) if isinstance(mapping, list) else None, 20))
        mapping_by_id, used_coords = {}, []
        for number, entry in enumerate(mapping if isinstance(mapping, list) else []):
            if not isinstance(entry, dict):
                sheet_checks.append(rule(f"sheet_entry_{number}_object", False, entry, "object"))
                continue
            frame_id, coord = entry.get("frame_id"), entry.get("coord")
            valid_entry = isinstance(frame_id, str) and frame_id in by_id and frame_id not in mapping_by_id and pair(coord)
            sheet_checks.append(rule(f"sheet_entry_{number}_valid_unique_frame", valid_entry, entry, "known unique frame_id and coord"))
            if not valid_entry:
                continue
            mapping_by_id[frame_id] = coord
            used_coords.append(tuple(coord))
            sheet_checks.append(rule(f"{frame_id}_sheet_coord_in_grid", coord[0] < 5 and coord[1] < 4, coord, "0<=x<5, 0<=y<4"))
            sheet_checks.append(rule(f"{frame_id}_frame_and_sheet_coord_agree", coord == by_id[frame_id].get("coord"), coord, by_id[frame_id].get("coord")))
        sheet_checks.append(rule("complete_sheet_frame_ids", set(mapping_by_id) == set(by_id) and len(mapping_by_id) == 20, len(mapping_by_id), 20))
        sheet_checks.append(rule("unique_sheet_coords", len(set(used_coords)) == 20, len(set(used_coords)), 20))
        try:
            sheet_path = resolve_file(sheet.get("texture"))
            sheet_report["file"] = sheet.get("texture")
            if sheet_path.is_file():
                with Image.open(sheet_path) as image:
                    sheet_report.update(sha256=sha256(sheet_path), size=list(image.size))
                    sheet_checks.append(rule("sheet_png_format", image.format == "PNG", image.format, "PNG"))
                    sheet_checks.append(rule("sheet_native_canvas", list(image.size) == [320, 384], list(image.size), [320, 384]))
                    if sheet.get("sha256") is not None:
                        sheet_checks.append(rule("sheet_sha256_matches", sheet_report["sha256"] == sheet["sha256"], sheet_report["sha256"], sheet["sha256"]))
                    matches = []
                    if list(image.size) == [320, 384]:
                        rgba = image.convert("RGBA")
                        for frame_id, (column, row) in mapping_by_id.items():
                            if frame_id not in pixels_by_id or not (0 <= column < 5 and 0 <= row < 4):
                                continue
                            cell = [rgba.getpixel((column * 64 + x, row * 96 + y)) for y in range(96) for x in range(64)]
                            mismatch = sum(a != b for a, b in zip(cell, pixels_by_id[frame_id]))
                            matches.append({"frame_id": frame_id, "coord": [column, row], "rgba_mismatched_pixels": mismatch})
                            sheet_checks.append(rule(f"{frame_id}_sheet_rgba_exact", mismatch == 0, mismatch, 0))
                    sheet_report["frame_matches"] = matches
                    if not planning:
                        sheet_checks.append(rule("all_twenty_sheet_cells_measured", len(matches) == 20, len(matches), 20))
            else:
                sheet_report["status"] = "PENDING_NOT_PRODUCED"
                if not planning:
                    sheet_checks.append(rule("sheet_png_exists", False, str(sheet_path), "existing PNG"))
        except (OSError, ValueError) as error:
            sheet_checks.append(rule("readable_sheet_png", False, str(error), "readable project PNG"))

    baseline_after = sha256(baseline_path)
    checks.append(rule("original_down_idle_unchanged_during_read", baseline_before == baseline_after == BASELINE_SHA256,
                       {"before": baseline_before, "after": baseline_after}, BASELINE_SHA256))
    all_checks = []
    def collect(value: object) -> None:
        if isinstance(value, dict):
            if "passed" in value:
                all_checks.append(value)
            for nested in value.values():
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)
    collect(report)
    failed = [c for c in all_checks if not c["passed"]]
    report["summary"] = {"expected_frames": 20, "catalog_frames": len(frames), "measured_frames": len(report["frames"]),
                         "missing_frames": missing, "automatic_checks": len(all_checks), "failed_checks": len(failed),
                         "warning_count": len(warnings), "sheet_cells_measured": len(sheet_report.get("frame_matches", [])),
                         "original_down_idle_locked": baseline_before == baseline_after == BASELINE_SHA256}
    report["failed_checks"] = failed
    report["catalog_and_present_png_checks_passed"] = not failed
    report["automated_png_and_catalog_checks_passed"] = not planning and not failed
    report["full_art_acceptance_status"] = (
        "AUTOMATIC_CHECKS_FAILED_NOT_ACCEPTED" if failed else
        "PLANNING_ONLY_NOT_ART_ACCEPTANCE" if planning else "INDEPENDENT_VISUAL_REVIEW_REQUIRED")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--catalog", type=Path, required=True, help="规划或最终 frames catalog JSON")
    parser.add_argument("--json", type=Path, help="仅写独立 JSON 报告，禁止覆盖输入目录或图片")
    parser.add_argument("--planning", action="store_true", help="允许规划中的 PNG 缺失；不表示生产/美术完成")
    args = parser.parse_args()
    catalog_path = args.catalog.resolve()
    if args.json:
        output = args.json.resolve()
        if (args.json.suffix.lower() != ".json" or output == catalog_path
                or output.is_relative_to(PROJECT / "assets") or output.is_relative_to(PROJECT / "docs")
                or "catalog" in output.name.lower()):
            parser.error("--json 必须是独立 .json 报告，不能覆盖 catalog、assets 或 docs")
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8-sig"))
        if not isinstance(catalog, dict):
            raise ValueError("catalog 顶层须为 JSON object")
        report = validate(catalog, catalog_path, args.planning)
    except (OSError, ValueError, TypeError) as error:
        # 目录错误也给结构化输出，不用 traceback 淹没用户真正需要的失败信息。
        report = {"mode": "PLANNING_STRUCTURE_ONLY" if args.planning else "READ_ONLY_PNG_AND_CATALOG",
                  "catalog_path": str(catalog_path), "catalog_and_present_png_checks_passed": False,
                  "automated_png_and_catalog_checks_passed": False, "full_art_acceptance_status": "NOT_ACCEPTED",
                  "summary": {"failed_checks": 1}, "failed_checks": [rule("readable_catalog_and_contract", False, str(error), "valid catalog")],
                  "png_modified": False}
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"mode": report["mode"], **report["summary"],
                      "automated_png_and_catalog_checks_passed": report["automated_png_and_catalog_checks_passed"],
                      "full_art_acceptance_status": report["full_art_acceptance_status"]}, ensure_ascii=False, indent=2))
    return 0 if report["catalog_and_present_png_checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
