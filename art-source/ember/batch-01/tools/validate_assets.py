#!/usr/bin/env python3
"""只读测量《余烬采能站》首批六个生产 PNG，不生成或修改图像。

依赖 Pillow。结果输出为 JSON；--json 只保存测量报告。
退出码：0=可自动检查的规则通过，1=规则失败或文件缺失。
退出码 0 不等于美术验收通过：造型、视角、像素尺度、锚点语义及
地板的实际拼接仍须在原生尺寸、整数放大和 3×3 平铺预览中人工复核。
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

try:
    from PIL import Image
except ImportError:
    raise SystemExit("缺少 Pillow；请使用含 Pillow 的 Python 运行本脚本。")


PALETTE_HEX = (
    "101820", "182631", "2B3E4B", "4D6470", "829BA3", "BECBC4",
    "7B4D35", "B77C4B", "E2B77A", "51C5C2", "E5A44B", "E65B4A",
    "566B78", "203A4B", "406B78", "ECE9D8",
)
PALETTE = {tuple(bytes.fromhex(value)) for value in PALETTE_HEX}
FLOOR_TYPES = ("clean", "worn", "grate", "wet")


def hex_rgb(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{channel:02X}" for channel in rgb)


def check(name: str, passed: bool, actual: object, expected: object) -> dict:
    """每条规则保留实测值，避免只有合格 / 不合格结论。"""
    return {"name": name, "passed": passed, "actual": actual, "expected": expected}


def describe_png(path: Path, kind: str, extra_colors: set) -> tuple[dict, Image.Image | None]:
    """只读取原文件；颜色统计不包含 Alpha 为 0 的隐藏 RGB。"""
    result = {"path": str(path), "kind": kind, "checks": []}
    if not path.is_file():
        result.update({"error": "FILE_MISSING", "automated_checks_passed": False})
        return result, None
    try:
        with Image.open(path) as source:
            result["source_format"] = source.format
            result["source_mode"] = source.mode
            has_alpha = "A" in source.getbands() or "transparency" in source.info
            image = source.convert("RGBA")
    except (OSError, ValueError) as exc:
        result.update({"error": str(exc), "automated_checks_passed": False})
        return result, None

    width, height = image.size
    pixels = list(image.getdata())
    alpha_histogram = Counter(pixel[3] for pixel in pixels)
    visible_colors = Counter(pixel[:3] for pixel in pixels if pixel[3] > 0)
    bbox = image.getchannel("A").getbbox()
    # Pillow 包围盒为 [left, top, right, bottom)，右边与下边不含在主体内。
    margins = None if bbox is None else [bbox[0], bbox[1], width - bbox[2], height - bbox[3]]
    allowed_colors = PALETTE | extra_colors
    off_palette = {rgb: count for rgb, count in visible_colors.items() if rgb not in allowed_colors}
    semi_transparent = sum(count for alpha, count in alpha_histogram.items() if 0 < alpha < 255)
    result.update({
        "size": [width, height],
        "has_alpha_channel_or_png_transparency": has_alpha,
        "alpha_values": sorted(alpha_histogram),
        "transparent_pixel_count": alpha_histogram[0],
        "semi_transparent_pixel_count": semi_transparent,
        "opaque_pixel_count": alpha_histogram[255],
        "bbox_exclusive": list(bbox) if bbox else None,
        "bbox_size": [bbox[2] - bbox[0], bbox[3] - bbox[1]] if bbox else None,
        "transparent_margins_left_top_right_bottom": margins,
        "visible_color_count": len(visible_colors),
        "visible_colors": [
            {"rgb": hex_rgb(rgb), "pixels": count, "in_base_palette": rgb in PALETTE}
            for rgb, count in visible_colors.most_common()
        ],
        "off_registered_palette_pixel_count": sum(off_palette.values()),
        "off_registered_palette_colors": [hex_rgb(rgb) for rgb in sorted(off_palette)],
    })
    checks = result["checks"]
    checks.append(check("png_format", result["source_format"] == "PNG", result["source_format"], "PNG"))
    expected_size = (64, 96) if kind == "robot" else (128, 160) if kind == "station" else (32, 32)
    checks.append(check("native_canvas_size", image.size == expected_size, list(image.size), list(expected_size)))
    checks.append(check("visible_colors_in_registered_palette", not off_palette, len(off_palette), 0))
    checks.append(check("visible_color_budget", len(visible_colors) <= len(allowed_colors), len(visible_colors), f"<= {len(allowed_colors)}"))

    if kind in ("robot", "station"):
        max_width, max_height = (40, 64) if kind == "robot" else (96, 128)
        anchor = (32, 80) if kind == "robot" else (64, 144)
        checks.append(check("real_transparent_background", has_alpha and alpha_histogram[0] > 0, {
            "has_alpha": has_alpha, "transparent_pixels": alpha_histogram[0],
        }, "PNG transparency with Alpha=0 pixels"))
        checks.append(check("binary_alpha", semi_transparent == 0, semi_transparent, 0))
        checks.append(check("nonempty_subject", bbox is not None, bbox is not None, True))
        checks.append(check("subject_bbox_limit", bbox is not None and bbox[2] - bbox[0] <= max_width and bbox[3] - bbox[1] <= max_height,
                            result["bbox_size"], [max_width, max_height]))
        if kind == "station":
            checks.append(check("minimum_transparent_margin", margins is not None and min(margins) >= 16, margins, "all >= 16"))
        elif bbox:
            # 此区域在标准中是建议构图，单独记录，不能冒充强制规则。
            result["recommended_robot_region"] = {
                "region_exclusive": [12, 16, 52, 80],
                "subject_within_region": bbox[0] >= 12 and bbox[1] >= 16 and bbox[2] <= 52 and bbox[3] <= 80,
                "classification": "COMPOSITION_RECOMMENDATION",
            }
        # 接地点常位于最下方不透明像素之后的边界，因此同时记录 bottom 与 last row。
        # 两只脚中间可能透明，不能以锚点单个像素的 Alpha 判定脚底正确。
        lowest_x = [] if bbox is None else [x for x in range(width) if image.getpixel((x, bbox[3] - 1))[3] > 0]
        result["anchor_review"] = {
            "required_anchor_xy": list(anchor),
            "coordinate_convention": "canvas coordinates; contact is a boundary, not necessarily an opaque pixel",
            "opaque_bottom_boundary_y": bbox[3] if bbox else None,
            "bottom_boundary_minus_anchor_y": bbox[3] - anchor[1] if bbox else None,
            "lowest_opaque_row_y": bbox[3] - 1 if bbox else None,
            "lowest_row_x_coordinates": lowest_x,
            "lowest_row_span_contains_anchor_x": bool(lowest_x) and min(lowest_x) <= anchor[0] <= max(lowest_x),
            "status": "MANUAL_SEMANTIC_VERIFICATION_REQUIRED",
        }
        result["manual_checks"] = [
            "俯视三分之四正交视角、统一原生像素尺度、轻微左上方明暗",
            "透明区没有画成棋盘格；轮廓无白边、裁切或烘焙投影",
            "脚底 / 基座实际接地点符合固定锚点；PNG 包围盒不能证明语义",
            "机器人与站点为同一制造体系；没有运行火焰、雨、护盾、光晕或危险圈",
            "能量 / 状态窗口中性；逐项记录窗口中心和发射点",
        ]
    else:
        checks.append(check("fully_opaque_tile", alpha_histogram[255] == width * height, alpha_histogram[255], width * height))
        result["manual_checks"] = [
            "满铺平面图案、低对比、没有高亮假危险线和强反射",
            "本类型 3×3 平铺的规律与接缝；仅边缘相等不足以证明平铺自然",
            "与其他三种地板在水平 / 垂直方向相邻时结构和材质可连接",
        ]
    result["automated_checks_passed"] = all(item["passed"] for item in checks)
    return result, image


def delta_metrics(first: list[tuple], second: list[tuple]) -> dict:
    """两行 / 两列像素的 RGB 跳变；仅作测量，不设武断的合格阈值。"""
    differences = [sum(abs(a[channel] - b[channel]) for channel in range(3)) / 3
                   for a, b in zip(first, second)]
    return {
        "sample_count": len(differences),
        "mean_absolute_rgb_delta_0_255": round(sum(differences) / len(differences), 6) if differences else None,
        "max_mean_absolute_rgb_delta_0_255": round(max(differences), 6) if differences else None,
        "exact_rgb_mismatch_count": sum(a[:3] != b[:3] for a, b in zip(first, second)),
    }


def edge(image: Image.Image, direction: str) -> list[tuple]:
    width, height = image.size
    if direction in ("left", "right"):
        x = 0 if direction == "left" else width - 1
        return [image.getpixel((x, y)) for y in range(height)]
    y = 0 if direction == "top" else height - 1
    return [image.getpixel((x, y)) for x in range(width)]


def tile_review(images: dict[str, Image.Image]) -> dict:
    """测量全部有向类型组合；左右或上下交换后的组合也单独列出。"""
    result = {
        "status": "NUMERIC_MEASUREMENTS_ONLY_VISUAL_REVIEW_REQUIRED",
        "interpretation": "零差值证明边缘像素相等；不证明拼接图案自然。非零差值也不必然是接缝错误。",
        "self_repeat_3x3": [],
        "ordered_adjacencies": [],
    }
    valid = {name: image for name, image in images.items() if image.size == (32, 32)}
    for name, image in valid.items():
        horizontal = delta_metrics(edge(image, "right"), edge(image, "left"))
        vertical = delta_metrics(edge(image, "bottom"), edge(image, "top"))
        # 3×3 同型重复中，每方向有 2 条内接缝，每条由 3 块组成。
        result["self_repeat_3x3"].append({
            "type": name, "horizontal_boundary": horizontal, "vertical_boundary": vertical,
            "boundary_segments_per_direction_in_3x3": 6,
            "edges_rgb_sha256": {
                direction: hashlib.sha256(bytes(channel for pixel in edge(image, direction) for channel in pixel[:3])).hexdigest()
                for direction in ("left", "top", "right", "bottom")
            },
        })
    for first_name, first in valid.items():
        for second_name, second in valid.items():
            result["ordered_adjacencies"].append({
                "first": first_name, "second": second_name,
                "horizontal_first_right_to_second_left": delta_metrics(edge(first, "right"), edge(second, "left")),
                "vertical_first_bottom_to_second_top": delta_metrics(edge(first, "bottom"), edge(second, "top")),
            })
    result["present_types"] = list(valid)
    result["all_four_types_available_at_native_size"] = len(valid) == 4
    return result


def parse_color(value: str) -> tuple[int, int, int]:
    value = value.removeprefix("#")
    try:
        rgb = bytes.fromhex(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("颜色须为 #RRGGBB") from exc
    if len(rgb) != 3:
        raise argparse.ArgumentTypeError("颜色须为 #RRGGBB")
    return tuple(rgb)


def main() -> int:
    # 在参数解析前设置编码，--help 和参数错误也能正确输出中文。
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4], help="项目目录")
    parser.add_argument("--version", default="v001", help="默认文件名版本，默认 v001")
    parser.add_argument("--robot", type=Path, help="机器人 PNG；覆盖默认路径")
    parser.add_argument("--station", type=Path, help="采能站 PNG；覆盖默认路径")
    for name in FLOOR_TYPES:
        parser.add_argument(f"--floor-{name}", type=Path, help=f"{name} 地板 PNG；覆盖默认路径")
    parser.add_argument("--allow-color", type=parse_color, action="append", default=[], help="已在生产记录登记的增补色；可重复")
    parser.add_argument("--json", type=Path, help="保存 JSON 测量报告；不写任何图像")
    args = parser.parse_args()
    root = args.root.resolve()
    formal = root / "assets" / "ember"
    paths = {
        "robot": args.robot or formal / "characters/robot" / f"robot_idle_down_f00_base_{args.version}.png",
        "station": args.station or formal / "buildings/station" / f"station_base_{args.version}.png",
        **{f"floor_{name}": getattr(args, f"floor_{name}") or formal / "environment/tiles/floor" / f"floor_{name}_base_{args.version}.png"
           for name in FLOOR_TYPES},
    }
    if args.json:
        # 报告只能写 JSON，禁止误将 --json 指向待测 PNG 覆盖原图。
        if args.json.suffix.lower() != ".json":
            parser.error("--json 的输出文件必须使用 .json 扩展名。")
        if args.json.resolve() in {path.resolve() for path in paths.values()}:
            parser.error("报告输出路径不能与待测素材相同。")
    results = []
    floors = {}
    for name, path in paths.items():
        # 覆盖路径若为相对路径，按命令执行目录解析，与一般 CLI 一致。
        kind = name if name in ("robot", "station") else "floor"
        result, image = describe_png(path.resolve(), kind, set(args.allow_color))
        result["asset_key"] = name
        result["manifest_id"] = "C01" if name == "robot" else "B01" if name == "station" else "T01"
        results.append(result)
        if name.startswith("floor_") and image is not None:
            floors[name.removeprefix("floor_")] = image
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "tool": "validate_assets.py / Pillow / read-only PNG measurements",
        "base_palette": [f"#{value}" for value in PALETTE_HEX],
        "registered_extra_colors": [hex_rgb(rgb) for rgb in sorted(set(args.allow_color))],
        "counting_rule": {
            "first_batch_target_units": 6, "C01_target_frames_in_this_batch": 1,
            "C01_group_budget_frames": 20, "B01_target_objects": 1, "T01_target_tiles": 4,
            "full_art_budget_units": 123, "reference_boards_are_production_units": False,
            "note": "本报告不修改清单完成状态；自动规则通过不能自动登记艺术单元完成。",
        },
        "assets": results,
        "tile_seams": tile_review(floors),
        "automated_checks_passed": all(item["automated_checks_passed"] for item in results),
        "full_art_acceptance_status": "MANUAL_REVIEW_REQUIRED",
    }
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if report["automated_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
