"""D08：从已验收底图和登记几何派生十张对象通道 Mask。

这是技术数据生成脚本，不读取底图 RGB 来猜动态区域，也不修改美术底图。
R = 允许局部换色，G = 允许发光，B = 允许扰动，A = 底图原始 Alpha。
本批 B 全部未启用；风机只有 R 的实际叶片选区，没有发光窗口。
其它对象的 R/G 共用登记的安全内窗，与真实组件选区和底图 Alpha 相交。

坐标使用原生画布的像素边界：[x0, y0, x1, y1)，右、下边界不包含。
同样的 canvas / anchor 可让 Mask 与 Sprite 保持逐像素一致，无需重采样。
脚本只写本目录的来源/审阅记录和 assets/ember/data/object_masks/ 新数据图。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[3]
OUTPUT = ROOT / "assets/ember/data/object_masks"
CATALOG_SOURCE = ROOT / "assets/ember/ember_additional_catalog_v001.json"
STATION_RECORD = ROOT / "art-source/ember/batch-01/pixel-finish-v001/finishing-record.json"

# 显式绑定选区的语义名称，避免将高管线/高天线等无关组件混入动态窗口。
# None 表示底图仅有登记几何，没有可拆的精确窗口组件。
SPECS = [
    ("station", "B01", None),
    ("console", "console_base", "screen_neutral"),
    ("pump", "pump_base", None),
    ("ventilator", "ventilator_base", "fan_rotor"),
    ("cooler", "cooler_base", "core_window"),
    ("relay", "relay_base", "core_window"),
    ("wall_lamp", "wall_lamp", "lens_neutral"),
    ("floor_lamp", "floor_lamp", "lens_neutral"),
    ("telepad", "telepad_base", "marker_windows"),
    ("terminal_window", "terminal_body", "inner_screen"),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def resolve(value: str) -> Path:
    path = (ROOT / value.removeprefix("res://")).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"来源路径越出项目：{value}")
    return path


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def raw_channel_values(image: Image.Image) -> set[int]:
    """L 图使用原始字节取值，避免 RGB 转灰度引入任何推断。"""
    if image.mode != "L":
        raise ValueError("通道必须是 L 模式")
    return set(image.tobytes())


def statistics(image: Image.Image) -> dict:
    bbox = image.getbbox()
    return {
        "nonzero_count": sum(value > 0 for value in image.tobytes()),
        "bbox": list(bbox) if bbox else None,
        "values": sorted(raw_channel_values(image)),
    }


def mismatches(left: Image.Image, right: Image.Image) -> int:
    return statistics(ImageChops.difference(left, right))["nonzero_count"]


def registered_window_union(size: tuple[int, int], windows: list[dict]) -> Image.Image:
    """只读取已登记的 safe_active_rect；外框 bbox 不充当完整窗口 Mask。"""
    result = Image.new("L", size, 0)
    for window in windows:
        x0, y0, x1, y1 = window["safe_active_rect"]
        if not (0 <= x0 < x1 <= size[0] and 0 <= y0 < y1 <= size[1]):
            raise ValueError(f"登记窗口越界：{window['id']}")
        expected_center = [(x0 + x1) / 2, (y0 + y1) / 2]
        if window.get("center") != expected_center:
            raise ValueError(f"登记窗口中心不一致：{window['id']}")
        # paste 的 box 使用右下排除规则，保持与目录坐标定义相同。
        result.paste(255, (x0, y0, x1, y1))
    return result


def resolve_selection(asset: dict, layer_name: str, size: tuple[int, int], anchor: list[int]):
    matches = [layer for layer in asset["layers"] if layer["name"] == layer_name]
    if len(matches) != 1:
        raise ValueError(f"没有唯一真实组件：{asset['id']}/{layer_name}")
    layer = matches[0]
    if layer["canvas"] != list(size) or layer["anchor"] != anchor:
        raise ValueError("选区组件的画布/锚点不匹配")
    component = resolve(layer["file"])
    selection = resolve(layer["selection_mask"])
    if digest(component) != layer["sha256"]:
        raise ValueError(f"冻结组件 SHA 不匹配：{component}")
    with Image.open(component) as image:
        component_alpha = image.convert("RGBA").getchannel("A")
    with Image.open(selection) as image:
        # 已交付选区明确为单通道数据；不将组件 RGB 转灰度猜区域。
        if image.mode != "L" or image.size != size:
            raise ValueError(f"选区不是匹配画布的 L 图：{selection}")
        selected = image.copy()
    if raw_channel_values(selected) - {0, 255}:
        raise ValueError("源选区不是二值数据")
    if mismatches(selected, component_alpha):
        raise ValueError(f"selection 与真实组件 Alpha 不一致：{selection}")
    return selected, {
        "layer_name": layer_name,
        "file": relative(selection),
        "sha256": digest(selection),
        "mode": "L",
        "component_file": relative(component),
        "component_sha256": digest(component),
        "component_anchor": anchor,
        "selection_equals_component_alpha": True,
        **statistics(selected),
    }


def channel_preview(channel: Image.Image, color: tuple[int, int, int]) -> Image.Image:
    # 这是审阅图色码，不能把它误当作生产数据图的实际 RGB 数值。
    rgb = Image.new("RGB", channel.size, (9, 15, 22))
    rgb.paste(color, (0, 0), channel)
    return rgb


def checker(size: tuple[int, int]) -> Image.Image:
    result = Image.new("RGB", size)
    draw = ImageDraw.Draw(result)
    for y in range(0, size[1], 8):
        for x in range(0, size[0], 8):
            color = (30, 39, 49) if (x // 8 + y // 8) % 2 else (22, 30, 39)
            draw.rectangle((x, y, x + 7, y + 7), fill=color)
    return result


def make_review(identifier: str, source: Image.Image, output: Image.Image, anchor: list[int]) -> Path:
    r, g, b, a = output.split()
    base = checker(source.size)
    base.paste(source, (0, 0), source.getchannel("A"))
    overlay = base.copy()
    # R/G 重合显示黄色，风机仅 R 显示红色；叠加只用于肉眼验证选区位置。
    overlay_pixels = overlay.load()
    r_values, g_values = r.load(), g.load()
    for y in range(source.height):
        for x in range(source.width):
            if r_values[x, y] or g_values[x, y]:
                tint = (250, 207, 64) if r_values[x, y] and g_values[x, y] else (238, 73, 70)
                original = overlay_pixels[x, y]
                overlay_pixels[x, y] = tuple((old + new) // 2 for old, new in zip(original, tint))
    draw = ImageDraw.Draw(overlay)
    # 锚点是虚拟地面边界，只画在审阅图，生产数据图不添加任何标记。
    x, y = anchor
    draw.line((x - 3, y, x + 3, y), fill=(230, 230, 230))
    draw.line((x, y - 3, x, min(y + 3, source.height - 1)), fill=(230, 230, 230))
    panels = [base, overlay, channel_preview(r, (238, 73, 70)),
              channel_preview(g, (71, 226, 123)), channel_preview(b, (69, 145, 244)),
              channel_preview(a, (221, 221, 221))]
    labels = ["BASE", "SELECTED + ANCHOR", "R RECOLOR", "G EMISSION", "B UNUSED", "A BASE ALPHA"]
    cell_width = max(source.width, 128) + 8
    review = Image.new("RGB", (cell_width * 6, source.height + 48), (13, 20, 28))
    draw = ImageDraw.Draw(review)
    draw.text((8, 4), identifier + " / integer 2x review; exact native canvas", fill=(230, 230, 230))
    for index, (panel, label) in enumerate(zip(panels, labels)):
        start = index * cell_width + 4
        draw.text((start, 22), label, fill=(200, 210, 220))
        review.paste(panel, (start, 40))
    review_dir = BASE / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    review.save(review_dir / f"{identifier}_mask_review_1x.png")
    review_2x = review_dir / f"{identifier}_mask_review_2x.png"
    review.resize((review.width * 2, review.height * 2), Image.Resampling.NEAREST).save(review_2x)
    return review_2x


def main() -> None:
    input_catalog = read_json(CATALOG_SOURCE)
    input_assets = {item["id"]: (index, item) for index, item in enumerate(input_catalog["assets"])}
    station_records = read_json(STATION_RECORD)
    station_index, station = next((index, item) for index, item in enumerate(station_records) if item["id"] == "B01")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    checks, entries, previews = [], [], []

    def check(name: str, passed: bool, actual=None) -> None:
        checks.append({"name": name, "passed": bool(passed), "actual": actual})
        if not passed:
            raise ValueError(f"D08 验证失败：{name}")

    for identifier, source_id, selected_layer in SPECS:
        if source_id == "B01":
            source_file = resolve(station["output"])
            expected_sha = station["output_sha256"]
            canvas = station["measurements"]["canvas"]
            anchor = station["measurements"]["anchor"]
            windows = station["runtime_layout"]["windows"]
            geometry_file = STATION_RECORD
            geometry_pointer = f"/{station_index}/runtime_layout/windows"
            asset = None
        else:
            index, asset = input_assets[source_id]
            source_file = resolve(asset["file"])
            expected_sha = asset["sha256"]
            canvas, anchor, windows = asset["canvas"], asset["anchor"], asset["runtime_windows"]
            geometry_file = CATALOG_SOURCE
            geometry_pointer = f"/assets/{index}/runtime_windows"
        check(identifier + ":frozen_source_sha", digest(source_file) == expected_sha)
        with Image.open(source_file) as image:
            check(identifier + ":source_mode", image.mode == "RGBA", image.mode)
            source = image.copy()
        check(identifier + ":source_canvas", source.size == tuple(canvas), list(source.size))
        alpha = source.getchannel("A")
        check(identifier + ":source_binary_alpha", raw_channel_values(alpha) <= {0, 255})
        rectangles = registered_window_union(source.size, windows)
        selection_sources = []
        if selected_layer:
            selected, selection_record = resolve_selection(asset, selected_layer, source.size, anchor)
            selection_sources.append(selection_record)
            check(identifier + ":selection_inside_source_alpha", statistics(ImageChops.subtract(selected, alpha))["nonzero_count"] == 0)
            if identifier == "ventilator":
                # 已确认的唯一例外：实际三叶片+轴的可选换色选区，不能当发光区。
                active = ImageChops.darker(selected, alpha)
                r, g = active, Image.new("L", source.size, 0)
                basis = "真实 fan_rotor L selection；已核对与同画布叶片组件 Alpha 完全一致"
                selection_rect_difference = None
            else:
                # 有真实选区时始终以该选区为准，并限制到登记安全窗及底图 Alpha。
                # 当前七个内窗组件均与登记矩形逐像素一致；未来非矩形不能放宽成矩形。
                active = ImageChops.darker(ImageChops.darker(selected, rectangles), alpha)
                selection_rect_difference = mismatches(selected, rectangles)
                check(identifier + ":selection_matches_registered_rects", selection_rect_difference == 0)
                r, g = active, active.copy()
                basis = "真实内窗/镜片/平台标记 selection ∩ 登记 safe_active_rect ∩ 底图 Alpha"
        else:
            active = ImageChops.darker(rectangles, alpha)
            selection_rect_difference = None
            # station/pump 没有可拆窗口选区；仅使用已验收登记的安全内区。
            # 尤其 station 外框视觉定位范围绝不宣称为精确的完整窗区。
            r, g = active, active.copy()
            basis = "已验收登记 safe_active_rect ∩ 底图 Alpha；底图没有独立窗口 selection"
        b = Image.new("L", source.size, 0)
        mask = Image.merge("RGBA", (r, g, b, alpha))
        target = OUTPUT / f"{identifier}_mask_v001.png"
        # 幂等运行只允许同字节的已有新数据文件；禁止悄悄覆盖已验收的异版数据。
        if target.is_file():
            with Image.open(target) as image:
                check(identifier + ":existing_mask_same_pixels", image.mode == "RGBA" and image.size == mask.size and image.tobytes() == mask.tobytes())
        else:
            mask.save(target)
        with Image.open(target) as image:
            saved = image.copy()
        check(identifier + ":output_mode_and_canvas", saved.mode == "RGBA" and saved.size == source.size)
        saved_r, saved_g, saved_b, saved_a = saved.split()
        check(identifier + ":alpha_exact_base", saved_a.tobytes() == alpha.tobytes())
        check(identifier + ":R_exact_geometry_intersection", saved_r.tobytes() == r.tobytes())
        check(identifier + ":G_exact_geometry_intersection", saved_g.tobytes() == g.tobytes())
        check(identifier + ":B_zero", saved_b.getbbox() is None)
        check(identifier + ":RGB_zero_outside_base", all(ImageChops.subtract(channel, alpha).getbbox() is None for channel in [saved_r, saved_g, saved_b]))
        check(identifier + ":binary_data_channels", all(raw_channel_values(channel) <= {0, 255} for channel in saved.split()))
        channels = {name: statistics(channel) for name, channel in zip("RGBA", saved.split())}
        channels["R"]["purpose"] = "可选局部叶片换色" if identifier == "ventilator" else "安全内窗/镜片/平台标记局部换色"
        channels["G"]["purpose"] = "未登记发光窗口，保持0" if identifier == "ventilator" else "安全内窗/镜片/平台标记发光门控"
        channels["B"]["purpose"] = "本批没有启用扰动区域，全部为0"
        channels["A"]["purpose"] = "对应静态底图的完整原始 Alpha，逐字节复制"
        relevant_geometry = {"canvas": canvas, "anchor": anchor, "windows": windows,
                             "selected_layer": selected_layer, "selection_sources": selection_sources}
        geometry_sha = hashlib.sha256(json.dumps(relevant_geometry, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        preview = make_review(identifier, source, saved, anchor)
        previews.append({"id": identifier, "file": relative(preview)})
        entries.append({
            "id": identifier, "manifest_id": "D08", "file": "res://" + relative(target),
            "sha256": digest(target), "canvas": canvas, "mode": "RGBA", "repeat_axes": [],
            "anchor": anchor, "anchor_convention": "与底图相同的原生像素边界坐标；无移动/缩放",
            "bbox": channels["A"]["bbox"], "channels": channels,
            "source_id": source_id, "source_file": "res://" + relative(source_file),
            "source_sha256": expected_sha,
            "source_geometry_file": relative(geometry_file), "source_geometry_sha256": digest(geometry_file),
            "source_geometry_json_pointer": geometry_pointer,
            "registered_geometry_sha256": geometry_sha, "registered_geometry": relevant_geometry,
            "selection_sources": selection_sources, "selection_rect_difference_count": selection_rect_difference,
            "selection_basis": basis,
            "limitations": ["安全内区不等于完整窗框；不覆盖外框装甲、管口、烟/光外部区域",
                            "B未启用；不提供整设备扰动、叶片旋转答案或外部烟火Mask",
                            "terminal_window对应96×96 terminal_body，不对应独立screen_frame"] if identifier == "terminal_window" else
                           ["安全窗口/已确认组件范围以来源几何为准，不根据底图RGB颜色扩张",
                            "B未启用；不包含外部烟火、全设备换色或新猜测动态区域"],
            "data_sampling": {"source_color_hint": False, "filter": "Nearest", "mipmaps": False,
                              "fix_alpha_border": False, "import_owner": "root整合脚本，生成器不写.import"},
            "generator": relative(Path(__file__)), "generator_sha256": digest(Path(__file__)),
            "preview_2x": relative(preview),
        })
    check("D08_exact_ten_ids", len(entries) == 10 and len({item["id"] for item in entries}) == 10)
    catalog = {
        "schema_version": 1, "status": "D08_TEN_CHANNEL_MASKS_NUMERIC_PASS_VISUAL_REQUIRED",
        "method": "REGISTERED_GEOMETRY_AND_ACTUAL_SELECTION_DERIVED_NO_IMAGEGEN",
        "coordinate_convention": "origin top-left pixel boundary; [x0,y0,x1,y1), right/bottom excluded",
        "channel_contract": {"R": "recolor", "G": "emission", "B": "distortion", "A": "exact base alpha"},
        "generated_files": 10, "art_units_added": 0, "production_art_modified": False,
        "assets": entries,
    }
    save_json(BASE / "catalog.json", catalog)
    save_json(BASE / "validation-v001.json", {
        "status": "D08_TEN_CHANNEL_MASKS_NUMERIC_PASS", "checks": len(checks), "failed_checks": [],
        "details": checks, "catalog_sha256": digest(BASE / "catalog.json"),
        "file_count": 10, "source_pngs_modified": False, "imports_modified": False,
        "data_file_hashes": {entry["id"]: entry["sha256"] for entry in entries},
    })
    save_json(BASE / "review/index.json", {"assets": previews, "scale": "integer nearest 2x"})
    print(json.dumps({"status": "D08_TEN_CHANNEL_MASKS_NUMERIC_PASS", "count": len(entries),
                      "checks": len(checks), "catalog": relative(BASE / "catalog.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
