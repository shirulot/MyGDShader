#!/usr/bin/env python3
"""只读检查《余烬采能站》三套 32×32 瓦片 atlas 与坐标目录。

不会创建、编辑或导出图片；--json 仅写 JSON 测量报告。
目录兼容结构：
  {"tile_size":32, "atlases":[{"source_id":0, "id":"ground_details",
    "texture":"res://assets/ember/environment/tilesets/ground.png",
    "columns":8, "margins":[0,0], "separation":[0,0],
    "tiles":[{"id":"floor_clean", "name":"干净地板", "coord":[0,0],
      "category":"T01", "variant":"clean", "alpha_mode":"opaque",
      "interfaces":{"N":"floor-v001","E":"floor-v001",
                    "S":"floor-v001","W":"floor-v001"}}]}]}

interfaces 每侧可为 null（没有可连接接口）、接口名字符串，或对象：
  {"kind":"pipe-v001", "ports":[[14,18]], "alpha_at_ports":"opaque",
   "exact_edge_required":false}
ports 使用 [start,end) 原生像素区间；N/S 从左到右，E/W 从上到下。
相同 kind 的相对接口会全部测量。只在显式 exact_edge_required=true 时
把边缘不完全相等判为自动规则失败。接缝均值不设任意合格阈值。

布局的默认 8 列、零边距和零间隔是本轮 atlas 交付约定，非美术标准
本身的要求；可用目录字段或 --columns 覆盖。Godot 内部 texture padding
不是文件内 separation，本脚本不把它计入 PNG 坐标。
variant 或 topology 使用本脚本 REQUIRED_VARIANTS 中的明确语义名称；
tile 的 id/name 可以保留中文或原有命名。margins 只表示左/上边距，
右/下留白另用 trailing_padding=[x,y] 声明，默认均为零。
退出码 0 只表示可自动验证的规则通过；所有结果仍须人工视觉审查。
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from math import ceil
from pathlib import Path
import sys

from PIL import Image


PALETTE = {tuple(bytes.fromhex(value)) for value in (
    "101820", "182631", "2B3E4B", "4D6470", "829BA3", "BECBC4",
    "7B4D35", "B77C4B", "E2B77A", "51C5C2", "E5A44B", "E65B4A",
    "566B78", "203A4B", "406B78", "ECE9D8",
)}
GROUPS = {
    "ground_details": {"T01": 4, "T07": 2, "T08": 6},
    "structures": {"T02": 13, "T03": 8, "T06": 5},
    "utilities": {"T04": 12, "T05": 12},
}
REQUIRED_VARIANTS = {
    # 这是坐标目录的规范语义键，用来展开原清单中的 edges4 / corners4 等预算。
    "T01": {"clean", "worn", "grate", "wet"},
    "T02": {"center", "edge_n", "edge_e", "edge_s", "edge_w",
            "outer_ne", "outer_se", "outer_sw", "outer_nw",
            "inner_ne", "inner_se", "inner_sw", "inner_nw"},
    "T03": {"straight_h", "straight_v", "corner_ne", "corner_se", "corner_sw", "corner_nw", "end_h", "end_v"},
    "T04": {"straight_h", "straight_v", "elbow_ne", "elbow_se", "elbow_sw", "elbow_nw",
            "tee_n", "tee_e", "tee_s", "tee_w", "cross", "valve"},
    "T05": {"edge_n", "edge_e", "edge_s", "edge_w", "outer_ne", "outer_se", "outer_sw", "outer_nw",
            "inner_ne", "inner_se", "inner_sw", "inner_nw"},
    "T06": {"deck_h", "deck_v", "edge_h", "edge_v", "end_cap"},
    "T07": {"hatch_closed", "hatch_open"},
    "T08": {"crack", "rust", "bolts", "oil", "cable_loop", "debris"},
}
SIDES = ("N", "E", "S", "W")
OPPOSITE = {"N": "S", "E": "W", "S": "N", "W": "E"}
TILE_SIZE = 32


def hex_rgb(rgb: tuple) -> str:
    return "#" + "".join(f"{channel:02X}" for channel in rgb)


def rule(name: str, passed: bool, actual: object, expected: object) -> dict:
    return {"name": name, "passed": bool(passed), "actual": actual, "expected": expected}


def pair(value: object, positive: bool = False) -> bool:
    return isinstance(value, list) and len(value) == 2 and all(
        isinstance(item, int) and not isinstance(item, bool) and item >= (1 if positive else 0)
        for item in value)


def resolve_texture(value: str, project: Path) -> Path:
    if value.startswith("res://"):
        return (project / value[6:]).resolve()
    path = Path(value)
    return path.resolve() if path.is_absolute() else (project / path).resolve()


def region_pixels(image: Image.Image, rect: list[int]) -> list[tuple]:
    # 只读像素坐标，不 crop / resize / save，也不改变任何源图。
    left, top, right, bottom = rect
    return [image.getpixel((x, y)) for y in range(top, bottom) for x in range(left, right)]


def edges(pixels: list[tuple]) -> dict:
    return {
        "N": pixels[:TILE_SIZE],
        "S": pixels[-TILE_SIZE:],
        "W": pixels[::TILE_SIZE],
        "E": pixels[TILE_SIZE - 1::TILE_SIZE],
    }


def metrics(pixels: list[tuple], allowed: set) -> dict:
    histogram = Counter(pixel[3] for pixel in pixels)
    colors = Counter(pixel[:3] for pixel in pixels if pixel[3] > 0)
    coordinates = [(index % TILE_SIZE, index // TILE_SIZE)
                   for index, pixel in enumerate(pixels) if pixel[3] > 0]
    bbox = None if not coordinates else [
        min(x for x, _ in coordinates), min(y for _, y in coordinates),
        max(x for x, _ in coordinates) + 1, max(y for _, y in coordinates) + 1,
    ]
    return {
        "bbox_exclusive_local": bbox,
        "transparent_pixels": histogram[0],
        "semi_transparent_pixels": sum(count for alpha, count in histogram.items() if 0 < alpha < 255),
        "opaque_pixels": histogram[255],
        "visible_rgb_color_count": len(colors),
        "off_registered_palette_colors": [hex_rgb(rgb) for rgb in sorted(colors) if rgb not in allowed],
        "off_registered_palette_pixels": sum(count for rgb, count in colors.items() if rgb not in allowed),
    }


def normalize_interface(value: object) -> dict | None:
    if value is None:
        return None
    if isinstance(value, str) and value:
        return {"kind": value, "ports": None, "alpha_at_ports": None, "exact_edge_required": False}
    if not isinstance(value, dict) or not isinstance(value.get("kind"), str) or not value["kind"]:
        raise ValueError("接口必须为 null、非空名称或含非空 kind 的对象")
    ports = value.get("ports")
    if ports is not None:
        if not isinstance(ports, list) or not all(
            pair(port) and 0 <= port[0] < port[1] <= TILE_SIZE for port in ports):
            raise ValueError("ports 须为 0..32 范围内的 [start,end) 区间列表")
        positions = [offset for start, end in ports for offset in range(start, end)]
        if len(set(positions)) != len(positions):
            raise ValueError("同一边的 ports 不能重叠")
        ports = sorted(ports)
    alpha_mode = value.get("alpha_at_ports")
    if alpha_mode not in (None, "opaque", "transparent"):
        raise ValueError("alpha_at_ports 只支持 opaque、transparent 或 null")
    if alpha_mode is not None and not ports:
        raise ValueError("alpha_at_ports 需要非空 ports")
    exact_required = value.get("exact_edge_required", False)
    if not isinstance(exact_required, bool):
        raise ValueError("exact_edge_required 须为 JSON 布尔值，不接受字符串")
    return {
        "kind": value["kind"], "ports": ports, "alpha_at_ports": alpha_mode,
        "exact_edge_required": exact_required,
    }


def interface_review(tile: dict, tile_edges: dict) -> dict:
    declaration = tile.get("interfaces")
    review = {"declared_all_sides": isinstance(declaration, dict) and all(side in declaration for side in SIDES),
              "interfaces": {}, "checks": []}
    if not review["declared_all_sides"]:
        review["status"] = "NEEDS_INTERFACE_METADATA_AND_VISUAL_REVIEW"
        return review
    for side in SIDES:
        try:
            interface = normalize_interface(declaration[side])
            review["interfaces"][side] = interface
            if interface and interface["alpha_at_ports"] is not None:
                expected = 255 if interface["alpha_at_ports"] == "opaque" else 0
                values = [tile_edges[side][offset][3]
                          for start, end in interface["ports"] for offset in range(start, end)]
                review["checks"].append(rule(f"{side}_declared_port_alpha", all(alpha == expected for alpha in values),
                                              sorted(set(values)), expected))
        except ValueError as exc:
            review["checks"].append(rule(f"{side}_interface_metadata", False, str(exc), "valid interface declaration"))
    category = tile.get("category", tile.get("manifest_id"))
    connected = [value for value in review["interfaces"].values() if value is not None]
    if category in ("T01", "T02", "T03", "T04", "T05", "T06"):
        required = 4 if category == "T01" else 1
        review["checks"].append(rule("semantic_connection_interfaces_present", len(connected) >= required,
                                     len(connected), f">= {required} non-null interface(s)"))
    if category in ("T03", "T04"):
        # 栏杆与管线是窄构件，仅有接口名称无法说明连接位置和宽度。
        review["checks"].append(rule("thin_component_port_ranges_present", all(value["ports"] for value in connected),
                                     [value["ports"] for value in connected], "explicit nonempty port ranges"))
    review["metadata_valid"] = len(review["interfaces"]) == 4 and all(item["passed"] for item in review["checks"])
    review["status"] = "METADATA_MEASURED_VISUAL_REVIEW_REQUIRED"
    return review


def seam_metrics(first: list[tuple], second: list[tuple]) -> dict:
    # 两侧皆透明时忽略隐藏 RGB，避免把不可见数据误计为视觉接缝。
    visible_first = [(0, 0, 0, 0) if pixel[3] == 0 else pixel for pixel in first]
    visible_second = [(0, 0, 0, 0) if pixel[3] == 0 else pixel for pixel in second]
    differences = [sum(abs(a[channel] - b[channel]) for channel in range(3)) / 3
                   for a, b in zip(visible_first, visible_second)]
    return {
        "samples": len(first),
        "mean_absolute_rgb_delta_0_255": round(sum(differences) / len(differences), 6),
        "max_mean_absolute_rgb_delta_0_255": round(max(differences), 6),
        "visible_rgba_mismatch_count": sum(a != b for a, b in zip(visible_first, visible_second)),
        "alpha_mismatch_count": sum(a[3] != b[3] for a, b in zip(first, second)),
    }


def measure_atlas(atlas: dict, project: Path, columns: int, allowed: set) -> tuple[dict, list]:
    atlas_id = atlas.get("id")
    expected_counts = GROUPS.get(atlas_id, {})
    tile_records = atlas.get("tiles", [])
    if not isinstance(tile_records, list):
        return {"id": atlas_id, "checks": [rule("tiles_array", False, type(tile_records).__name__, "list")], "tiles": []}, []
    texture = atlas.get("texture", "")
    report = {"id": atlas_id, "source_id": atlas.get("source_id"), "texture": texture, "checks": [], "tiles": []}
    checks = report["checks"]
    checks.append(rule("known_tileset_group", atlas_id in GROUPS, atlas_id, list(GROUPS)))
    counts = Counter(tile.get("category", tile.get("manifest_id")) for tile in tile_records if isinstance(tile, dict))
    checks.append(rule("category_budget", dict(counts) == expected_counts, dict(counts), expected_counts))
    atlas_columns = atlas.get("columns", columns)
    margins = atlas.get("margins", [0, 0])
    separation = atlas.get("separation", [0, 0])
    trailing_padding = atlas.get("trailing_padding", [0, 0])
    layout_valid = isinstance(atlas_columns, int) and not isinstance(atlas_columns, bool) and atlas_columns > 0 and pair(margins) and pair(separation) and pair(trailing_padding)
    checks.append(rule("layout_metadata", layout_valid,
                       {"columns": atlas_columns, "margins": margins, "separation": separation, "trailing_padding": trailing_padding},
                       "positive columns and nonnegative [x,y] margins/separation/trailing_padding"))
    if not layout_valid or not isinstance(texture, str) or not texture:
        checks.append(rule("texture_path_present", bool(texture), texture, "PNG path"))
        return report, []
    path = resolve_texture(texture, project)
    report["resolved_texture_path"] = str(path)
    try:
        with Image.open(path) as source:
            image = source.convert("RGBA")
            report.update({"source_format": source.format, "source_mode": source.mode,
                           "has_png_alpha": "A" in source.getbands() or "transparency" in source.info})
        report["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, ValueError) as exc:
        checks.append(rule("readable_png", False, str(exc), "decodable PNG"))
        return report, []
    checks.append(rule("png_format", report["source_format"] == "PNG", report["source_format"], "PNG"))
    expected_units = sum(expected_counts.values())
    row_count = ceil(expected_units / atlas_columns) if expected_units else 0
    expected_size = [margins[0] + atlas_columns * TILE_SIZE + (atlas_columns - 1) * separation[0] + trailing_padding[0],
                     margins[1] + row_count * TILE_SIZE + max(row_count - 1, 0) * separation[1] + trailing_padding[1]]
    report.update({"size": list(image.size), "expected_packed_size": expected_size,
                   "layout": {"columns": atlas_columns, "rows": row_count, "margins": margins,
                              "separation": separation, "trailing_padding": trailing_padding}})
    checks.append(rule("declared_packed_canvas", list(image.size) == expected_size, list(image.size), expected_size))
    # 每套均包含 RGBA 部件；RGBA 不等于要求每个部件都必须出现透明像素。
    checks.append(rule("atlas_supports_png_alpha", report["has_png_alpha"], report["has_png_alpha"], True))
    occupied = set()
    ids = set()
    variants = set()
    measured = []
    for tile in tile_records:
        if not isinstance(tile, dict):
            checks.append(rule("tile_record_object", False, type(tile).__name__, "object"))
            continue
        tile_id = str(tile.get("id", ""))
        category = tile.get("category", tile.get("manifest_id"))
        variant = tile.get("topology", tile.get("variant"))
        coord = tile.get("coord", tile.get("atlas_coords"))
        item = {"id": tile_id, "category": category, "variant": variant, "coord": coord, "checks": []}
        report["tiles"].append(item)
        item_checks = item["checks"]
        item_checks.append(rule("explicit_semantic_variant", isinstance(variant, str) and variant in REQUIRED_VARIANTS.get(category, set()),
                                variant, sorted(REQUIRED_VARIANTS.get(category, set()))))
        item_checks.append(rule("unique_tile_id_in_atlas", bool(tile_id) and tile_id not in ids, tile_id, "nonempty unique id"))
        ids.add(tile_id)
        variant_key = (category, str(variant))
        item_checks.append(rule("unique_category_variant", bool(variant) and variant_key not in variants, list(variant_key), "unique category/variant"))
        variants.add(variant_key)
        valid_coord = pair(coord) and coord[0] < atlas_columns and coord[1] < row_count
        item_checks.append(rule("atlas_coord_in_grid", valid_coord, coord, [atlas_columns, row_count]))
        if not valid_coord:
            continue
        key = tuple(coord)
        item_checks.append(rule("atlas_coord_not_reused", key not in occupied, coord, "one registered tile per cell"))
        occupied.add(key)
        left = margins[0] + coord[0] * (TILE_SIZE + separation[0])
        top = margins[1] + coord[1] * (TILE_SIZE + separation[1])
        rect = [left, top, left + TILE_SIZE, top + TILE_SIZE]
        item["content_rect_exclusive"] = rect
        if rect[2] > image.width or rect[3] > image.height:
            item_checks.append(rule("content_rect_inside_png", False, rect, list(image.size)))
            continue
        pixels = region_pixels(image, rect)
        result = metrics(pixels, allowed)
        item.update(result)
        item_checks.append(rule("nonempty_tile", result["bbox_exclusive_local"] is not None, result["bbox_exclusive_local"], "at least one visible pixel"))
        item_checks.append(rule("visible_palette", result["off_registered_palette_pixels"] == 0,
                                result["off_registered_palette_pixels"], 0))
        alpha_mode = tile.get("alpha_mode", "opaque" if category == "T01" else "binary")
        item["alpha_mode"] = alpha_mode
        item_checks.append(rule("declared_alpha_mode", alpha_mode in ("opaque", "binary"), alpha_mode, ["opaque", "binary"]))
        item_checks.append(rule("binary_alpha", result["semi_transparent_pixels"] == 0, result["semi_transparent_pixels"], 0))
        if category == "T01" or alpha_mode == "opaque":
            item_checks.append(rule("opaque_content", result["opaque_pixels"] == TILE_SIZE ** 2, result["opaque_pixels"], TILE_SIZE ** 2))
        if tile.get("requires_transparency", False):
            item_checks.append(rule("declared_cutout_has_transparency", result["transparent_pixels"] > 0, result["transparent_pixels"], "> 0"))
        tile_edges = edges(pixels)
        item["edge_alpha_profiles"] = {side: [pixel[3] for pixel in values] for side, values in tile_edges.items()}
        item["interface_review"] = interface_review(tile, tile_edges)
        measured.append({"ref": f"{atlas_id}/{tile_id}", "category": category,
                         "edges": tile_edges, "interface_review": item["interface_review"]})
    for category in expected_counts:
        actual = sorted({str(tile.get("topology", tile.get("variant"))) for tile in tile_records
                         if isinstance(tile, dict) and tile.get("category", tile.get("manifest_id")) == category})
        checks.append(rule(f"{category}_required_variant_set", actual == sorted(REQUIRED_VARIANTS[category]),
                           actual, sorted(REQUIRED_VARIANTS[category])))
    report["unused_cells"] = []
    for y in range(row_count):
        for x in range(atlas_columns):
            if (x, y) in occupied:
                continue
            left, top = margins[0] + x * (TILE_SIZE + separation[0]), margins[1] + y * (TILE_SIZE + separation[1])
            if left + TILE_SIZE > image.width or top + TILE_SIZE > image.height:
                continue
            visible = sum(pixel[3] > 0 for pixel in region_pixels(image, [left, top, left + TILE_SIZE, top + TILE_SIZE]))
            report["unused_cells"].append({"coord": [x, y], "visible_pixels": visible})
            checks.append(rule(f"unused_cell_{x}_{y}_transparent", visible == 0, visible, 0))
    return report, measured


def all_interface_connections(tiles: list[dict]) -> dict:
    comparisons, rules, unmatched = [], [], []
    for first in tiles:
        first_interfaces = first["interface_review"].get("interfaces", {})
        for side, interface in first_interfaces.items():
            if interface is None:
                continue
            candidates = [(second, second["interface_review"].get("interfaces", {}).get(OPPOSITE[side])) for second in tiles]
            candidates = [(second, other) for second, other in candidates if other and other["kind"] == interface["kind"]]
            if not candidates:
                unmatched.append({"tile": first["ref"], "side": side, "kind": interface["kind"]})
            for second, other in candidates:
                # 全有向组合：允许同一种 tile 与自身连接，也保留交换方向后的记录。
                result = seam_metrics(first["edges"][side], second["edges"][OPPOSITE[side]])
                result.update({"first": first["ref"], "side": side, "second": second["ref"],
                               "other_side": OPPOSITE[side], "kind": interface["kind"]})
                comparisons.append(result)
                if interface["ports"] is not None and other["ports"] is not None:
                    rules.append(rule(f"ports_{first['ref']}_{side}_{second['ref']}", interface["ports"] == other["ports"],
                                      [interface["ports"], other["ports"]], "matching declared port ranges"))
                if interface["exact_edge_required"] or other["exact_edge_required"]:
                    rules.append(rule(f"exact_edge_{first['ref']}_{side}_{second['ref']}", result["visible_rgba_mismatch_count"] == 0,
                                      result["visible_rgba_mismatch_count"], 0))
    return {"comparisons": comparisons, "checks": rules, "unmatched_declared_interfaces": unmatched,
            "status": "DECLARED_INTERFACE_MEASUREMENTS_ONLY_VISUAL_REVIEW_REQUIRED"}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--catalog", required=True, type=Path, help="只读 atlas 坐标 JSON")
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[4], help="res:// 对应项目目录")
    parser.add_argument("--columns", type=int, default=8, help="catalog 未声明 columns 时的本批布局约定")
    parser.add_argument("--json", type=Path, help="保存 JSON 测量报告，不可覆盖输入文件")
    parser.add_argument("--print-full", action="store_true", help="同时在标准输出打印全部报告，默认只打印摘要")
    args = parser.parse_args()
    if args.columns < 1:
        parser.error("--columns 必须大于 0")
    try:
        catalog = json.loads(args.catalog.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        parser.error(f"无法读取目录：{exc}")
    if not isinstance(catalog, dict) or not isinstance(catalog.get("atlases"), list):
        parser.error("catalog 须为含 atlases 数组的对象")
    if not all(isinstance(atlas, dict) for atlas in catalog["atlases"]):
        parser.error("atlases 中每项须为对象")
    project = args.project.resolve()
    inputs = {args.catalog.resolve()}
    inputs.update(resolve_texture(atlas["texture"], project) for atlas in catalog["atlases"] if isinstance(atlas.get("texture"), str))
    if args.json and (args.json.suffix.lower() != ".json" or args.json.resolve() in inputs):
        parser.error("报告必须为独立 .json 文件，不能覆盖目录或源 PNG")
    extra_colors = set()
    for extra in catalog.get("registered_extra_colors", []):
        if not isinstance(extra, dict) or not extra.get("registration_note"):
            parser.error("registered_extra_colors 每项须有 color 与 registration_note")
        try:
            color = tuple(bytes.fromhex(extra["color"].removeprefix("#")))
        except (ValueError, KeyError, AttributeError) as exc:
            parser.error(f"无效登记增补色：{exc}")
        if len(color) != 3:
            parser.error("增补色须为 #RRGGBB")
        extra_colors.add(color)
    checks = [rule("native_tile_size", catalog.get("tile_size") in (32, [32, 32]), catalog.get("tile_size"), 32),
              rule("three_expected_atlas_ids", sorted(str(atlas.get("id")) for atlas in catalog["atlases"]) == sorted(GROUPS),
                   [atlas.get("id") for atlas in catalog["atlases"]], list(GROUPS)),
              rule("source_ids_0_1_2", sorted(str(atlas.get("source_id")) for atlas in catalog["atlases"]) == ["0", "1", "2"],
                   [atlas.get("source_id") for atlas in catalog["atlases"]], [0, 1, 2])]
    atlases, tiles = [], []
    for atlas in catalog["atlases"]:
        report, measured = measure_atlas(atlas, project, args.columns, PALETTE | extra_colors)
        atlases.append(report)
        tiles.extend(measured)
    connections = all_interface_connections(tiles)
    all_checks = checks + [item for atlas in atlases for item in atlas["checks"]]
    all_checks += [item for atlas in atlases for tile in atlas["tiles"] for item in tile["checks"]]
    all_checks += [item for tile in tiles for item in tile["interface_review"]["checks"]]
    all_checks += connections["checks"]
    png_checks_passed = all(item["passed"] for item in all_checks)
    metadata_complete = len(tiles) == 62 and all(tile["interface_review"].get("metadata_valid", False) for tile in tiles)
    metadata_complete = metadata_complete and not connections["unmatched_declared_interfaces"]
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "tool": "validate_tileset_atlas.py / Pillow / read-only PNG and catalog measurements",
        "catalog_path": str(args.catalog.resolve()), "checks": checks, "atlases": atlases,
        "expected_units": 62, "measured_units": len(tiles),
        "base_palette": sorted(hex_rgb(rgb) for rgb in PALETTE),
        "registered_extra_colors": catalog.get("registered_extra_colors", []),
        "connections": connections, "automated_png_and_catalog_checks_passed": png_checks_passed,
        "interface_metadata_complete": metadata_complete,
        "full_art_acceptance_status": "MANUAL_VISUAL_REVIEW_REQUIRED",
        "manual_review": [
            "原生尺寸与整数2倍下的轮廓、统一像素尺度、左上光照和工业造型",
            "3×3自身平铺、不同地板相邻、墙/栏杆/桥/管线/岸线全部声明连接与角点",
            "透明部件叠在实际地板/水面时无白边、假棋盘、烘焙影或接缝干扰",
            "检修口两态安装点和固定边框；内外角陆/水侧；桥面与水岸衔接",
            "旋转/镜像后的明暗与非对称细节；13片墙不自动证明任意Terrain拓扑完整",
            "TileMapLayer绘制/遮挡/碰撞由Godot数据决定，PNG Alpha不能代替碰撞验收",
        ],
    }
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(output + "\n", encoding="utf-8")
    if args.print_full:
        print(output)
    else:
        print(json.dumps({
            "measured_units": len(tiles), "expected_units": 62,
            "automated_png_and_catalog_checks_passed": png_checks_passed,
            "failed_automatic_rules": sum(not item["passed"] for item in all_checks),
            "interface_metadata_complete": metadata_complete,
            "declared_directed_connection_measurements": len(connections["comparisons"]),
            "unmatched_declared_interfaces": len(connections["unmatched_declared_interfaces"]),
            "full_art_acceptance_status": "MANUAL_VISUAL_REVIEW_REQUIRED",
            "report_path": str(args.json.resolve()) if args.json else None,
        }, ensure_ascii=False, indent=2))
    return 0 if png_checks_passed and metadata_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
