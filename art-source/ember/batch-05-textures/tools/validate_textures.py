"""只读检查 7 个纹理输入与来源绑定；仅可写指定的验收 JSON。

数值测量不等同艺术独立验收，也不能证明没有烘焙定向光照。
3×3接缝、纹样重复、烟团可读性及草片近远表现仍由其他代理/制作方查看。
兼容 Pillow 旧 API；不创建、缩放、保存或修改任何图像。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

BATCH = Path(__file__).resolve().parents[1]
ROOT = BATCH.parents[2]
EXPECTED = {
    "water_calm": ((64, 64), "RGB", "XY", "V01"),
    "water_directional": ((64, 64), "RGB", "XY", "V01"),
    "foam_strip": ((64, 64), "RGBA", "X", "V02"),
    "smoke_blob": ((64, 64), "RGBA", "NONE", "V03"),
    "grass_leaf": ((64, 128), "RGBA", "NONE", "X01"),
    "metal_albedo": ((256, 256), "RGB", "XY", "X02"),
    "concrete_albedo": ((256, 256), "RGB", "XY", "X03"),
}
PALETTE = ["#101820", "#182631", "#2B3E4B", "#4D6470", "#829BA3", "#BECBC4",
           "#7B4D35", "#B77C4B", "#E2B77A", "#51C5C2", "#E5A44B", "#E65B4A",
           "#566B78", "#203A4B", "#406B78", "#ECE9D8"]
def rgb(value): return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))
ALLOWED = {rgb(c) for c in PALETTE}
STATE = {rgb(c) for c in ["#51C5C2", "#E5A44B", "#E65B4A"]}
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def resolve(value):
    path = Path(value.removeprefix("res://"))
    return path if path.is_absolute() else ROOT / path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=BATCH / "textures-catalog-v001.json")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    if args.json:
        output = args.json.resolve()
        # 不允许验收输出覆盖资源、文档或生产/规划输入目录。
        if output == args.catalog.resolve() or output.suffix.lower() != ".json" or "catalog" in output.name.lower() or output.is_relative_to(ROOT / "assets") or output.is_relative_to(ROOT / "docs"):
            parser.error("--json 只能是独立验收JSON，不能覆盖catalog/assets/docs")
    report = {"generated_utc": datetime.now(timezone.utc).isoformat(),
              "tool": "validate_textures.py / Pillow read-only",
              "validator_sha256": sha(Path(__file__)), "catalog": str(args.catalog.resolve()),
              "review_role": "PRODUCER_NUMERIC_MEASUREMENT_NOT_INDEPENDENT_ART_ACCEPTANCE",
              "checks": [], "assets": [], "source_checks": [], "png_modified": False}
    def check(name, passed, actual=None, expected=None):
        report["checks"].append({"name": name, "passed": bool(passed), "actual": actual, "expected": expected})
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    assets = catalog["assets"]; ids = [a["id"] for a in assets]
    # Counter(dict) 会把字典值当计数，必须显式取 keys，验证角色集合与重复。
    check("seven_exact_asset_ids", Counter(ids) == Counter(EXPECTED.keys()), ids, list(EXPECTED))
    check("unique_png_paths", len({a["file"] for a in assets}) == 7)
    ledger = json.loads((BATCH / "generation-record.json").read_text(encoding="utf-8"))
    check("seven_actual_source_records", len(ledger["records"]) == 7)
    for source in ledger["records"]:
        archive = resolve(source["file"]); original = Path(source["source"])
        same = sha(archive) == source["sha256"] and original.is_file() and sha(original) == source["sha256"]
        check(source["id"] + ".actual_tool_original_sha", same)
        check(source["id"] + ".complete_prompt_present", resolve(source["prompt"]).is_file())
        report["source_checks"].append({"id": source["id"], "sha256": source["sha256"], "original_and_archive_match": same})
    for item in assets:
        id = item["id"]; expected_size, expected_mode, expected_tiling, expected_manifest = EXPECTED[id]
        path = resolve(item["file"])
        check(id + ".manifest_id", item["manifest_id"] == expected_manifest)
        check(id + ".metadata_canvas", tuple(item["canvas"]) == expected_size)
        check(id + ".tiling_declaration", item["tiling"] == expected_tiling)
        check(id + ".sha256", sha(path) == item["sha256"])
        with Image.open(path) as opened:
            check(id + ".png_format", opened.format == "PNG")
            check(id + ".native_canvas", opened.size == expected_size)
            check(id + ".mode", opened.mode == expected_mode, opened.mode, expected_mode)
            im = opened.convert("RGBA")
        hist = im.getchannel("A").histogram(); bbox = im.getchannel("A").getbbox()
        colors = Counter(p[:3] for p in im.getdata() if p[3])
        off = sum(n for c, n in colors.items() if c not in ALLOWED)
        states = sum(n for c, n in colors.items() if c in STATE)
        hidden = sum(p[3] == 0 and p[:3] != (0, 0, 0) for p in im.getdata())
        check(id + ".nonempty", bbox is not None)
        check(id + ".binary_alpha", sum(hist[1:255]) == 0)
        check(id + ".exact_standard_palette", off == 0)
        check(id + ".at_most_16_colors", len(colors) <= 16)
        check(id + ".no_baked_state_colors", states == 0)
        check(id + ".zero_hidden_rgb", hidden == 0)
        check(id + ".metadata_bbox", item["bbox"] == list(bbox))
        if expected_mode == "RGB":
            check(id + ".opaque_full_canvas", hist[255] == im.width * im.height)
        else:
            check(id + ".real_transparent_margin", hist[0] > 0)
        edge = {}
        for axis, pairs in [("X", [(im.getpixel((0, y)), im.getpixel((im.width-1, y))) for y in range(im.height)]),
                            ("Y", [(im.getpixel((x, 0)), im.getpixel((x, im.height-1))) for x in range(im.width)])]:
            deltas = [abs(a[c]-b[c]) for a,b in pairs for c in range(4)]
            edge[axis] = {"samples": len(pairs), "rgba_mismatched_pixels": sum(a != b for a,b in pairs),
                          "max_channel_delta": max(deltas), "mean_absolute_channel_delta": round(sum(deltas)/len(deltas), 6)}
            if axis in expected_tiling:
                check(id + ".repeat_" + axis + "_edges_rgba_exact", edge[axis]["rgba_mismatched_pixels"] == 0)
        if id == "foam_strip":
            check(id + ".narrow_horizontal_band", bbox[1] >= 8 and bbox[3] <= 56 and bbox[3]-bbox[1] <= 24)
            check(id + ".foam_crosses_left_right", any(im.getpixel((0,y))[3] for y in range(im.height)) and any(im.getpixel((63,y))[3] for y in range(im.height)))
        elif id == "smoke_blob":
            check(id + ".full_unclipped_centered_puff", min(bbox[0],bbox[1],64-bbox[2],64-bbox[3]) >= 8 and abs((bbox[0]+bbox[2])/2-32) <= 2 and abs((bbox[1]+bbox[3])/2-32) <= 2)
            check(id + ".center_anchor", item["anchor"] == [32,32])
        elif id == "grass_leaf":
            check(id + ".root_anchor", item["anchor"] == [32,120])
            check(id + ".eight_pixel_margins", min(bbox[0],bbox[1],64-bbox[2],128-bbox[3]) >= 8)
            check(id + ".root_boundary_120", bbox[3] == 120 and im.getpixel((32,119))[3] == 255)
            check(id + ".no_pixels_below_root", all(im.getpixel((x,y))[3] == 0 for y in range(120,128) for x in range(64)))
        # 分区均值只是方向性亮度的测量，不把小差值当无烘焙灯光的艺术证明。
        def avg_luma(x0,y0,x1,y1):
            values=[sum(c*w for c,w in zip(im.getpixel((x,y))[:3],(.2126,.7152,.0722))) for y in range(y0,y1) for x in range(x0,x1) if im.getpixel((x,y))[3]]
            return round(sum(values)/len(values), 5) if values else None
        quadrants=[avg_luma(x*im.width//2,y*im.height//2,(x+1)*im.width//2,(y+1)*im.height//2) for y in range(2) for x in range(2)]
        record=json.loads(resolve(item["finishing_record"]).read_text(encoding="utf-8"))
        check(id + ".finish_output_sha", record["output_sha256"] == item["sha256"])
        check(id + ".finish_source_sha", sha(resolve(record["source"])) == record["source_sha256"])
        check(id + ".source_use_explicit", item["source_use"] == record["source_use"] and item["source_use"].startswith("AI_MATERIAL"))
        check(id + ".no_derived_pbr_or_height_maps_claimed", item["runtime_layout"]["pbr_derived_maps"] == "NOT_PRODUCED" and item["runtime_layout"]["height_weight_map"] == "NOT_PRODUCED")
        report["assets"].append({"id": id, "sha256": sha(path), "canvas": list(im.size), "bbox": list(bbox),
                                 "alpha_zero": hist[0], "alpha_partial": sum(hist[1:255]), "alpha_opaque": hist[255],
                                 "visible_rgb_count": len(colors), "palette_off_pixels": off, "state_color_pixels": states,
                                 "edges": edge, "quadrant_luma_means": quadrants,
                                 "anchor": item["anchor"], "tiling": expected_tiling})
    failed=[c for c in report["checks"] if not c["passed"]]
    report["summary"]={"assets":len(assets),"checks":len(report["checks"]),"failed_checks":len(failed),"source_masters":len(ledger["records"])}
    report["failed_checks"]=failed
    report["status"]="NUMERIC_PASS_REQUIRES_CROSS_AGENT_VISUAL_AND_GODOT_REVIEW" if not failed else "FAIL"
    report["manual_review_required"]=["逐个原生/2倍纹样与Alpha轮廓", "所有声明平铺轴的3×3视觉接缝与重复特征", "泡沫断续但X接口合理、烟团不是石块或被裁烟柱", "草叶根部会合及3D AlphaScissor近远可读", "金属/混凝土albedo没有方向高光投影、PBR实际材质由root另接"]
    if args.json: args.json.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],**report["summary"],"failed_checks":failed},ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
