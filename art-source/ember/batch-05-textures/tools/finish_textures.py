"""按已授权方案整理 7 个真实 imagegen 母稿，不改原母稿或生产目录。

母稿只提供构图、材质与像素簇参考。这里明确执行原生网格重采样、
无抖动调色、轮廓清理和接口修补；不能把生成器的 seamless 描述当作验收。
整个过程没有随机图案生成，所有纹样都来自已归档的实际母稿。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

BATCH = Path(__file__).resolve().parents[1]
ROOT = BATCH.parents[2]
PALETTE = ["#101820", "#182631", "#2B3E4B", "#4D6470", "#829BA3", "#BECBC4",
           "#7B4D35", "#B77C4B", "#E2B77A", "#51C5C2", "#E5A44B", "#E65B4A",
           "#566B78", "#203A4B", "#406B78", "#ECE9D8"]


def rgb(hex_color: str) -> tuple[int, int, int]:
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nearest(color, choices):
    return min(choices, key=lambda c: sum((color[i] - c[i]) ** 2 for i in range(3)))


def percent(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def rgba_edges(image):
    """严格报告首末边的 RGBA 差；RGB 输入只为比较视作 Alpha=255。"""
    im = image.convert("RGBA")
    result = {}
    for axis, pairs in [
        ("X", [(im.getpixel((0, y)), im.getpixel((im.width - 1, y))) for y in range(im.height)]),
        ("Y", [(im.getpixel((x, 0)), im.getpixel((x, im.height - 1))) for x in range(im.width)]),
    ]:
        differences = [abs(a[c] - b[c]) for a, b in pairs for c in range(4)]
        result[axis] = {"samples": len(pairs), "rgba_mismatched_pixels": sum(a != b for a, b in pairs),
                        "max_channel_delta": max(differences),
                        "mean_absolute_channel_delta": round(sum(differences) / len(differences), 6)}
    return result


def metrics(image):
    im = image.convert("RGBA"); alpha = im.getchannel("A")
    hist = alpha.histogram()
    # getdata 是 Pillow 旧/新版本均可用的 API，避免依赖 get_flattened_data。
    colors = Counter(p[:3] for p in im.getdata() if p[3])
    return {"canvas": list(im.size), "mode": image.mode,
            "bbox": list(alpha.getbbox()) if alpha.getbbox() else None,
            "alpha_zero": hist[0], "alpha_partial": sum(hist[1:255]), "alpha_opaque": hist[255],
            "visible_rgb_count": len(colors), "palette_off_pixels": sum(n for c, n in colors.items() if c not in {rgb(v) for v in PALETTE}),
            "edges": rgba_edges(image)}


def remove_small_groups(image, minimum, *, background=None, wrap_x=False, wrap_y=False):
    """去掉少量离散噪点；透明对象用 Alpha 连通，材料用非底色连通。

    8 邻域保留斜叶片与曲线。wrap 模式保证边界的小簇不会被误当两个孤点。
    """
    im = image.copy(); w, h = im.size; data = im.load(); seen = set(); removed = 0
    def active(x, y):
        p = data[x, y]
        return p[3] != 0 if background is None else p[:3] != background
    for y in range(h):
        for x in range(w):
            if (x, y) in seen or not active(x, y):
                continue
            group = []; queue = deque([(x, y)]); seen.add((x, y))
            while queue:
                px, py = queue.popleft(); group.append((px, py))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == dy == 0: continue
                        nx, ny = px + dx, py + dy
                        if wrap_x: nx %= w
                        if wrap_y: ny %= h
                        if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and active(nx, ny):
                            seen.add((nx, ny)); queue.append((nx, ny))
            if len(group) < minimum:
                for point in group: data[point] = (0, 0, 0, 0) if background is None else (*background, 255)
                removed += len(group)
    return im, removed


def close_boundaries(image, axes, choices, band=3):
    """显式重建相对边的短接缝带，再将最外边逐像素配对。

    中央纹样仍来自母稿；接缝带用两侧真实色值渐近配对，避免统一空白边框。
    数值相同只是必要条件，3×3 和跨边纹样连续性仍必须人工查看。
    """
    im = image.convert("RGBA").copy(); w, h = im.size
    for axis in axes:
        before = im.copy()
        length = h if axis == "X" else w
        for t in range(length):
            first = before.getpixel((0, t) if axis == "X" else (t, 0))
            last = before.getpixel((w - 1, t) if axis == "X" else (t, h - 1))
            # X 泡沫以 alpha 的平均覆盖配对；不把所有边缘强填为实体泡沫。
            seam_alpha = 255 if (first[3] + last[3]) >= 255 else 0
            visible = [p for p in [first, last] if p[3]]
            seam_rgb = nearest(tuple(sum(p[i] for p in visible) / len(visible) for i in range(3)), choices) if visible else (0, 0, 0)
            seam = (*seam_rgb, seam_alpha) if seam_alpha else (0, 0, 0, 0)
            for k in range(band):
                weight = (band - k) / band
                for low in [True, False]:
                    coord = ((k if low else w - 1 - k), t) if axis == "X" else (t, (k if low else h - 1 - k))
                    old = before.getpixel(coord)
                    if k == 0:
                        color = seam
                    elif old[3] and seam[3]:
                        mix = tuple(old[i] * (1 - weight) + seam[i] * weight for i in range(3))
                        color = (*nearest(mix, choices), 255)
                    else:
                        color = old
                    im.putpixel(coord, color)
    return im


def material(id, source):
    canvas = (64, 64) if id.startswith("water_") else (256, 256)
    sampled = source.convert("RGB").resize(canvas, Image.Resampling.BOX)
    # 先消除大图缩放形成的随机单点，再以母稿强度分位数提取真实纹样簇。
    sampled = sampled.filter(ImageFilter.MedianFilter(3))
    data = list(sampled.getdata()); luma = [0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2] for p in data]
    if id.startswith("water_"):
        choices = [rgb(v) for v in ["#203A4B", "#2B3E4B", "#406B78"]]
        thresholds = [percent(luma, .45), percent(luma, .90)]
    elif id == "metal_albedo":
        choices = [rgb(v) for v in ["#4D6470", "#566B78"]]
        thresholds = [percent(luma, .80)]
    else:
        choices = [rgb(v) for v in ["#829BA3", "#BECBC4"]]
        thresholds = [percent(luma, .89)]
    out = Image.new("RGBA", canvas)
    out.putdata([(*choices[sum(value > t for t in thresholds)], 255) for value in luma])
    background = Counter(out.getdata()).most_common(1)[0][0][:3]
    out, removed = remove_small_groups(out, 3 if canvas[0] == 64 else 5, background=background, wrap_x=True, wrap_y=True)
    before = metrics(out); out = close_boundaries(out, "XY", choices, band=3 if canvas[0] == 64 else 5)
    return out.convert("RGB"), {"source_crop": [0, 0, source.width, source.height], "source_reference_canvas": list(source.size),
        "native_quantization": "source luminance cluster quantiles, fixed palette, no dithering",
        "quantile_thresholds": thresholds, "palette_subset": ["#%02X%02X%02X" % c for c in choices],
        "sample_filter": "BOX to native grid then 3x3 median",
        "isolated_native_pixels_removed": removed, "seam_band_pixels": 3 if canvas[0] == 64 else 5,
        "before_boundary_repair": before["edges"], "directional_lighting_baked": False,
        "source_use": "AI_MATERIAL_PATTERN_REFERENCE_WITH_NATIVE_GRID_RECONSTRUCTION"}


def cutout(id, source):
    if id == "foam_strip":
        crop = [0, 0, source.width, source.height]; size = (64, 64); origin = (0, 0)
        choices = [rgb(v) for v in ["#829BA3", "#BECBC4", "#ECE9D8"]]; alpha_cut = 160
    elif id == "smoke_blob":
        crop = [274, 315, 1000, 973]; size = (46, 42); origin = (9, 11)
        choices = [rgb(v) for v in ["#4D6470", "#566B78", "#829BA3"]]; alpha_cut = 160
    else:
        # 草片左右也保留至少 8 原生像素；根底依旧落在 y=120。
        crop = [192, 160, 875, 1416]; size = (48, 110); origin = (8, 10)
        choices = [rgb(v) for v in ["#2B3E4B", "#4D6470", "#566B78", "#829BA3"]]; alpha_cut = 160
    sampled = source.convert("RGBA").crop(crop).resize(size, Image.Resampling.BOX)
    patch = Image.new("RGBA", size)
    patch.putdata([(*nearest(p, choices), 255) if p[3] >= alpha_cut else (0, 0, 0, 0) for p in sampled.getdata()])
    canvas = (64, 128) if id == "grass_leaf" else (64, 64)
    out = Image.new("RGBA", canvas); out.paste(patch, origin)
    out, removed = remove_small_groups(out, 2 if id == "foam_strip" else 3, wrap_x=id == "foam_strip")
    record = {"source_crop": crop, "native_patch_size": list(size), "native_patch_origin": list(origin),
              "source_alpha_threshold": alpha_cut, "alpha_policy": "BINARY_0_255",
              "palette_subset": ["#%02X%02X%02X" % c for c in choices],
              "native_quantization": "BOX coverage into designed native canvas, nearest fixed color, no dithering",
              "isolated_native_pixels_removed": removed,
              "source_use": "AI_MATERIAL_AND_SILHOUETTE_REFERENCE_WITH_NATIVE_PIXEL_FINISH"}
    if id == "foam_strip":
        record["before_boundary_repair"] = rgba_edges(out)
        out = close_boundaries(out, "X", choices, band=3)
        record["seam_band_pixels"] = 3
    elif id == "grass_leaf":
        # 原生叶片会合根部，统一根底边界 y=120；这不是投射阴影或权重数据图。
        for x in (31, 32, 33):
            out.putpixel((x, 119), (*choices[0], 255))
        record["native_root_junction_patch"] = [[31, 119], [32, 119], [33, 119]]
        record["root_anchor"] = [32, 120]
        record["wind_or_height_weight_baked"] = False
    return out, record


def review_texture(image, id):
    review = BATCH / "review"
    # 单个母稿对应一个候选，不把九格重复或放大预览计算为更多艺术单元。
    image.save(review / f"{id}_native_1x.png")
    image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST).save(review / f"{id}_native_2x.png")
    if id in {"water_calm", "water_directional", "foam_strip", "metal_albedo", "concrete_albedo"}:
        grid = Image.new("RGBA", (image.width * 3, image.height * 3))
        for y in range(3):
            for x in range(3): grid.paste(image.convert("RGBA"), (x * image.width, y * image.height))
        grid.save(review / f"{id}_3x3_native.png")
        grid.resize((grid.width * 2, grid.height * 2), Image.Resampling.NEAREST).save(review / f"{id}_3x3_2x.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="*")
    args = parser.parse_args()
    planned = json.loads((BATCH / "planned-catalog-v001.json").read_text(encoding="utf-8"))
    ledger = json.loads((BATCH / "generation-record.json").read_text(encoding="utf-8"))
    sources = {a["id"]: a for a in ledger["records"]}
    current_path = BATCH / "textures-catalog-v001.json"
    previous = {a["id"]: a for a in json.loads(current_path.read_text(encoding="utf-8"))["assets"]} if current_path.exists() else {}
    for item in planned["assets"]:
        id = item["id"]
        if args.only and id not in args.only: continue
        raw = sources[id]; source_path = ROOT / raw["file"]
        if digest(source_path) != raw["sha256"]: raise SystemExit("母稿哈希已改变：" + id)
        source = Image.open(source_path)
        output, process = material(id, source) if item["mode"] == "RGB" else cutout(id, source)
        target = ROOT / item["file"].removeprefix("res://"); output.save(target)
        measured = metrics(output)
        if measured["alpha_partial"] or measured["palette_off_pixels"]: raise SystemExit("原生规则未通过：" + id)
        anchor = [32, 120] if id == "grass_leaf" else [32, 32] if id == "smoke_blob" else [0, 0]
        runtime = {"layer_convention": "STATIC_SINGLE_FLATTENED_BASE", "emitter_points": [],
                   "emission_baked": False, "pbr_derived_maps": "NOT_PRODUCED", "height_weight_map": "NOT_PRODUCED"}
        recommendation = {"compression": "Lossless", "mipmaps": id in {"grass_leaf", "metal_albedo", "concrete_albedo"},
                          "filter": "3D material filter and mipmap close/far validation required" if id.startswith(("metal_", "concrete_", "grass_")) else "Nearest",
                          "repeat": item["tiling"], "status": "RECOMMENDATION_PENDING_ROOT_GODOT_VALIDATION"}
        record_path = BATCH / "finished-textures" / f"{id}_v001.finish.json"
        entry = {"id": id, "manifest_id": item["manifest_id"], "file": item["file"],
                 "production_file": item["production_file"], "canvas": item["canvas"], "size": item["canvas"],
                 "bbox": measured["bbox"], "anchor": anchor, "tiling": item["tiling"], "alpha_mode": item["mode"],
                 "sha256": digest(target), "source_use": process["source_use"], "source_file": raw["file"],
                 "source_sha256": raw["sha256"], "finishing_record": record_path.relative_to(ROOT).as_posix(),
                 "measurement": measured, "import_recommendation": recommendation, "runtime_layout": runtime,
                 "status": "NATIVE_CANDIDATE_NEEDS_CROSS_AGENT_REVIEW"}
        record = {"id": id, "source": raw["file"], "source_sha256": raw["sha256"],
                  "prompt": raw["prompt"], "output": target.relative_to(ROOT).as_posix(),
                  "output_sha256": entry["sha256"], "process": process, "measurement": measured,
                  "anchor": anchor, "tiling": item["tiling"], "runtime_layout": runtime,
                  "source_use": process["source_use"], "producer_visual_status": "PENDING_PRODUCER_REVIEW", "independent_visual_status": "PENDING_ROOT_OR_OTHER_AGENT_REVIEW"}
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_texture(output, id); previous[id] = entry
        print(json.dumps({"id": id, "canvas": measured["canvas"], "bbox": measured["bbox"], "colors": measured["visible_rgb_count"], "edges": measured["edges"]}, ensure_ascii=False))
    entries = [previous[a["id"]] for a in planned["assets"] if a["id"] in previous]
    catalog = {"date": "2026-10-04", "status": "NATIVE_CANDIDATES_NEED_CROSS_AGENT_REVIEW", "assets": entries,
               "palette": PALETTE, "art_units": len(entries), "formal_approved_production_units": 0,
               "source_master_count": len(sources), "png_sources_modified": False,
               "pbr_or_height_data_generated": False, "source_disclaimer": "AI references + explicit native finishing, not direct pixel extraction or independent self-acceptance"}
    current_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if len(entries) == 7:
        board = Image.new("RGBA", (576, 512), "#182631"); draw = ImageDraw.Draw(board)
        positions = [(16, 40), (112, 40), (208, 40), (304, 40), (432, 40), (16, 224), (304, 224)]
        for item, pos in zip(entries, positions):
            im = Image.open(ROOT / item["file"].removeprefix("res://")).convert("RGBA")
            board.alpha_composite(im, pos)
            draw.text((pos[0], pos[1] - 18), item["id"], fill="#BECBC4")
        board.save(BATCH / "review" / "textures_contact_native_v001.png")
        board.resize((1152, 1024), Image.Resampling.NEAREST).save(BATCH / "review" / "textures_contact_2x_v001.png")


if __name__ == "__main__":
    main()
