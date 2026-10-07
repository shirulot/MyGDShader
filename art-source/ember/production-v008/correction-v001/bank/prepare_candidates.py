"""池岸小批机械导出与诊断，所有输出只写本目录。

这里只对完整构件做方形裁切/注册和等比 Nearest 缩放。
不绘制美术，不清理 Alpha，不复制边缘，不局部拉伸，不旋转光照。
ImageDraw 仅用于诊断图的文字、背景和邻域标识。
"""
from collections import deque
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
OLD = ROOT / "art-source/ember/production-v008"
TOOL_BASE = Path(r"C:\Users\shiru\.codex\generated_images\01a10c06-70f1-7100-bf8d-c2032eb22807")


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def runs(values):
    """保留每一段实际主体，不用包围区间掩盖端口内部的孔洞。"""
    indices = np.flatnonzero(values > 127)
    if not len(indices):
        return []
    groups = np.split(indices, np.flatnonzero(np.diff(indices) > 1) + 1)
    return [[int(g[0]), int(g[-1]) + 1] for g in groups]


def bbox(alpha, threshold):
    y, x = np.where(alpha > threshold)
    return [int(x.min()), int(y.min()), int(x.max()) + 1, int(y.max()) + 1] if len(x) else None


def edges(image):
    a = np.asarray(image.convert("RGBA"))
    return {"N": a[0], "E": a[:, -1], "S": a[-1], "W": a[:, 0]}


def components(image):
    """8 邻域只作主体连通诊断；连通本身不证明凹角语义。"""
    remaining = set(map(tuple, np.argwhere(np.asarray(image)[:, :, 3] > 127)))
    areas = []
    while remaining:
        queue = deque([remaining.pop()])
        area = 0
        while queue:
            y, x = queue.popleft()
            area += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    q = (y + dy, x + dx)
                    if q in remaining:
                        remaining.remove(q)
                        queue.append(q)
        areas.append(area)
    return sorted(areas, reverse=True)


def measure(image):
    alpha = np.asarray(image.convert("RGBA"))[:, :, 3]
    return {
        "size": list(image.size),
        "alpha_unique_value_count": int(len(np.unique(alpha))),
        "alpha_zero_pixel_count": int((alpha == 0).sum()),
        "alpha_bbox_gt0": bbox(alpha, 0),
        "alpha_bbox_gt4": bbox(alpha, 4),
        "alpha_bbox_gt127": bbox(alpha, 127),
        "body_ports_alpha_gt127": {k: runs(v[:, 3]) for k, v in edges(image).items()},
        "body_edge_counts_alpha_gt127": {k: int((v[:, 3] > 127).sum()) for k, v in edges(image).items()},
    }


def compare(a, b):
    # 可见 RGB 与 Alpha 分开统计；不修改任一接口像素以制造相等。
    da = np.abs(a[:, 3].astype(int) - b[:, 3].astype(int))
    drgb = np.abs(a[:, :3].astype(int) - b[:, :3].astype(int))
    visible = np.maximum(a[:, 3], b[:, 3]) > 0
    return {
        "samples": len(a),
        "visible_rgba_mismatch_samples": int(((da > 0) | (visible & np.any(drgb > 0, axis=1))).sum()),
        "alpha_mismatch_samples": int((da > 0).sum()),
        "max_alpha_difference": int(da.max()),
        "max_visible_rgb_difference": int(drgb[visible].max()) if visible.any() else 0,
        "a_body_intervals": runs(a[:, 3]),
        "b_body_intervals": runs(b[:, 3]),
    }


def save_json(name, value):
    (BASE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    for folder in ("candidates", "review", "inputs"):
        (BASE / folder).mkdir(exist_ok=True)
    specs = [
        {
            "id": "bank_straight_N_pixel_v001", "mask": 124,
            "tool_output": "exec-c8ee78e4-3a42-4834-8b2b-3188058bc04e.png",
            "crop_xyxy": [0, 176, 1254, 1430],
            "status": "DIAGNOSTIC_ONLY_PORTS_PASS_REPEAT_INTERFACE_REJECTED",
            "geometry_result": "E/W 主体均为 [0,32)，达到本轮位置和总岸宽目标。",
            "material_result": "像素色簇改善，但左端白亮竖边与右端暗边构成重复封边；不满足贯通无端头要求。",
            "bank_connection_sides": ["E", "W"],
            "water_neighbor_sides": ["E", "S", "W"],
        },
        {
            "id": "bank_inner_NW_pixel_v001", "mask": 127,
            "tool_output": "exec-d1210736-1379-4d3a-83dd-cd9885a3d40e.png",
            "crop_xyxy": [65, 68, 1319, 1322],
            "status": "REJECTED_PORTS_CROSS_SECTION_SEMANTICS_AND_STYLE",
            "geometry_result": "原图四边均无主体接点；完整注册后 N=[0,2)，W=[0,18)+[19,55)，均不匹配32px直岸，压顶仍封边。",
            "material_result": "细碎写实磨损和圆润高光回流，未稳定采用新直岸像素簇。",
            "bank_connection_sides": ["N", "W"],
            "water_neighbor_sides": ["N", "E", "S", "W"],
        },
    ]
    entries, prompts = [], []
    images = {}
    for index, spec in enumerate(specs, 1):
        raw_path = BASE / "raw" / (spec["id"] + ".png")
        tool_path = TOOL_BASE / spec["tool_output"]
        assert digest(raw_path) == digest(tool_path), "项目副本必须保持工具原稿字节不变"
        raw = Image.open(raw_path).convert("RGBA")
        box = spec["crop_xyxy"]
        assert box[2] - box[0] == box[3] - box[1] == 1254
        # PIL 的画布外裁框只补透明画布；完整构件没有局部几何修复。
        candidate = raw.crop(box).resize((128, 128), Image.Resampling.NEAREST)
        path = BASE / "candidates" / (spec["id"] + "_128.png")
        candidate.save(path)
        candidate.resize((512, 512), Image.Resampling.NEAREST).save(BASE / "review" / (spec["id"] + "_4x.png"))
        prompt_path = BASE / "prompts" / (spec["id"] + ".txt")
        prompt_text = prompt_path.read_text(encoding="utf-8")
        images[spec["id"]] = candidate
        entries.append({
            **spec, "family": "bank", "tool": "image_gen.imagegen built-in",
            "call_number": index, "tool_original_path": str(tool_path),
            "tool_original_sha256": digest(tool_path), "raw_path": relative(raw_path),
            "raw_sha256": digest(raw_path), "raw_measurements": measure(raw),
            "prompt_path": relative(prompt_path), "prompt_sha256": digest(prompt_path),
            "candidate_path": relative(path), "candidate_sha256": digest(path),
            "candidate_measurements": measure(candidate), "body_components8": components(candidate),
            "crop_coordinate_convention": "XYXY half-open",
            "whole_component_offset_native_pixels": [-box[0], -box[1]],
            "registered_canvas_size": [1254, 1254], "uniform_scale_factor": 128 / 1254,
            "out_of_source_padding_LTRB": [max(0, -box[0]), max(0, -box[1]), max(0, box[2]-raw.width), max(0, box[3]-raw.height)],
            "resampling": "PIL.Image.Resampling.NEAREST", "no_local_art_or_alpha_repair": True,
            "user_visual_approval": False, "GPU_result": "PENDING_ROOT_UNIFIED_REVIEW",
        })
        refs = [
            ROOT / "art-source/ember/production-v008/correction-v001/raw/floor_center_pixel_v001.png",
            ROOT / "art-source/ember/autotiles-v003/industrial_tile_master_v003.png",
            OLD / "bank/raw/bank_straight_N_v001.png",
        ] if index == 1 else [
            BASE / "candidates/bank_straight_N_pixel_v001_128.png",
            OLD / "bank/raw/bank_inner_NW_v003.png",
            OLD / "inputs/official_mask127.png",
        ]
        prompts.append({"id": spec["id"], "tool": "image_gen.imagegen built-in", "transparent_background": True,
                       "prompt": prompt_text, "referenced_images_in_order": [{"path": relative(p), "sha256": digest(p)} for p in refs]})

    # 用户/根代理指定的唯一二次机械注册：裁去连续开口端20px的封边。
    # 这是同一原稿的一张整体方形裁框，不是第三次生图或局部修补。
    registered_id = "bank_straight_N_pixel_registered_v002"
    registered_raw_path = BASE / "raw/bank_straight_N_pixel_v001.png"
    registered_box = [20, 176, 1234, 1390]
    registered = Image.open(registered_raw_path).convert("RGBA").crop(registered_box).resize((128, 128), Image.Resampling.NEAREST)
    registered_path = BASE / "candidates" / (registered_id + "_128.png")
    registered.save(registered_path)
    registered.resize((512, 512), Image.Resampling.NEAREST).save(BASE / "review" / (registered_id + "_4x.png"))
    registered_entry = {
        "id": registered_id, "family": "bank", "mask": 124,
        "registration_source_id": "bank_straight_N_pixel_v001", "new_generation": False,
        "tool": "image_gen.imagegen built-in original; mechanical registration only", "call_number": 1,
        "tool_original_path": entries[0]["tool_original_path"], "tool_original_sha256": entries[0]["tool_original_sha256"],
        "raw_path": relative(registered_raw_path), "raw_sha256": digest(registered_raw_path),
        "raw_measurements": entries[0]["raw_measurements"],
        "candidate_path": relative(registered_path), "candidate_sha256": digest(registered_path),
        "candidate_measurements": measure(registered), "body_components8": components(registered),
        "crop_xyxy": registered_box, "crop_coordinate_convention": "XYXY half-open",
        "whole_component_offset_native_pixels": [-20, -176], "registered_canvas_size": [1214, 1214],
        "uniform_scale_factor": 128 / 1214, "out_of_source_padding_LTRB": [0, 0, 0, 136],
        "resampling": "PIL.Image.Resampling.NEAREST", "no_local_art_or_alpha_repair": True,
        "bank_connection_sides": ["E", "W"], "water_neighbor_sides": ["E", "S", "W"],
        "status": "DIAGNOSTIC_CANDIDATE_PORTS_WITHIN_1PX_GPU_AND_VISUAL_PENDING",
        "geometry_result": "E/W主体均[0,33)，比目标[0,32)多1px；处在首轮容差内，未达到严格32px。",
        "material_result": "整块裁去原稿两端20px后明显端封边消失，RGBA差异减小；长段视觉仍待根代理GPU审核。",
        "exact_32px_target_result": False, "geometry_1px_screening_result": True,
        "production_ready": False, "user_visual_approval": False, "GPU_result": "PENDING_ROOT_UNIFIED_REVIEW",
    }

    # 真正的 WEST 直岸是 mask31；mask17 是双岸窄通道，不能误当西直岸。
    old_catalog = ROOT / "assets/ember/environment/autotiles_v007/catalog.json"
    bank = next(a for a in json.loads(old_catalog.read_text(encoding="utf-8"))["atlases"] if a["id"] == "bank")
    coord = next(t["coord"] for t in bank["tiles"] if t["mask"] == 31)
    west_source = ROOT / bank["texture"].removeprefix("res://")
    west_box = [coord[0]*128, coord[1]*128, (coord[0]+1)*128, (coord[1]+1)*128]
    west = Image.open(west_source).convert("RGBA").crop(west_box)
    west_path = BASE / "inputs/v007_bank_W_mask31_diagnostic.png"
    west.save(west_path)
    original_straight, inner = [images[s["id"]] for s in specs]
    straight = registered
    e_straight, e_inner, e_west = edges(straight), edges(inner), edges(west)
    e_original = edges(original_straight)
    connections = {
        "neighborhood_case": {
            "center": [1, 1], "water_cells_3x3": [[False, True, True], [True, True, True], [True, True, True]],
            "center_mask": 127, "N_neighbor_bank_direction": "W", "W_neighbor_bank_direction": "N",
            "N_pair": "W-straight.S -> inner.N", "W_pair": "N-straight.E -> inner.W",
            "new_target_port_intervals": {"inner.N": [0, 32], "inner.W": [0, 32]},
            "notes": "边界外水域延续用于方向诊断；旧WEST方向不计新版通过。",
        },
        "v001_straight_E_to_straight_W": compare(e_original["E"], e_original["W"]),
        "registered_v002_straight_E_to_straight_W": compare(e_straight["E"], e_straight["W"]),
        "new_N_straight_E_to_inner_W": compare(e_straight["E"], e_inner["W"]),
        "legacy_W_straight_S_to_inner_N_DIAGNOSTIC_ONLY": compare(e_west["S"], e_inner["N"]),
        "legacy_west_source": {"path": relative(west_source), "sha256": digest(west_source), "mask": 31, "coord": coord,
                               "crop_xyxy": west_box, "copy_path": relative(west_path), "copy_sha256": digest(west_path), "measurements": measure(west)},
        "new_west_direction_generated": False,
        "full_loop_verified": False,
        "numeric_results_are_not_user_visual_approval": True,
    }
    # 仅拼接完整候选做 CPU 对照，既不修接口，也不把旧方向计作新版覆盖。
    for version, image in (("before", Image.open(OLD / "bank/candidates/bank_straight_N_sample_v001.png").convert("RGBA")), ("after", straight)):
        canvas = Image.new("RGBA", (8*128, 160), (21, 49, 61, 255))
        for x in range(8):
            canvas.alpha_composite(image, (x*128, 0))
        ImageDraw.Draw(canvas).text((8, 136), f"CPU 8-tile N straight {version}; 128px tiles; no edge repair", fill=(230, 234, 237, 255))
        canvas.save(BASE / "review" / f"north_repeat_{version}_128.png")
        game = Image.new("RGBA", (256, 54), (21, 49, 61, 255))
        game.alpha_composite(canvas.crop((0, 0, 1024, 128)).resize((256, 32), Image.Resampling.NEAREST), (0, 0))
        ImageDraw.Draw(game).text((4, 36), f"{version}: 8 tiles at world32 display", fill=(230, 234, 237, 255))
        game.save(BASE / "review" / f"north_repeat_{version}_world32.png")
    panels = Image.new("RGBA", (768, 440), (15, 30, 38, 255))
    draw = ImageDraw.Draw(panels)
    old_inner = Image.open(OLD / "bank/candidates/bank_inner_NW_sample_v003.png").convert("RGBA")
    for index, corner in enumerate((old_inner, inner)):
        board = Image.new("RGBA", (384, 384), (21, 49, 61, 255))
        # 缺 NW 的真实邻接：N 邻格为旧 WEST 岸，W 邻格为新 NORTH 岸。
        ImageDraw.Draw(board).rectangle((0, 0, 127, 127), fill=(44, 46, 48, 255))
        board.alpha_composite(west, (128, 0))
        board.alpha_composite(straight, (0, 128))
        board.alpha_composite(corner, (128, 128))
        panels.alpha_composite(board, (index*384, 0))
        draw.text((index*384 + 8, 390), "OLD v003 inner" if index == 0 else "NEW inner REJECTED", fill=(236, 197, 145, 255))
        draw.text((index*384 + 8, 407), "CPU missing-NW; legacy W + new N diagnostic", fill=(224, 230, 233, 255))
        draw.text((index*384 + 8, 424), "No closed pool / no full-new-direction proof", fill=(224, 230, 233, 255))
    panels.save(BASE / "review/missing_NW_neighborhood_cpu_before_after.png")
    panels.resize((1536, 880), Image.Resampling.NEAREST).save(BASE / "review/missing_NW_neighborhood_cpu_before_after_2x.png")

    save_json("prompts.json", {"built_in_call_count": 2, "prompts": prompts})
    all_entries = [entries[0], registered_entry, entries[1]]
    save_json("candidate-catalog.json", {"status": "REGISTERED_N_DIAGNOSTIC_CANDIDATE_INNER_REJECTED_NOT_PRODUCTION",
                                        "selected_diagnostic_N_candidate_id": registered_id, "entries": all_entries})
    report = {
        "status": "LIMITED_TWO_CALLS_COMPLETE_NOT_FULL_TILESET", "built_in_call_count": 2, "maximum_authorized_calls": 2,
        "texture_size": [128, 128], "world_grid_units": 32, "layer_scale": 0.25,
        "alpha_body_measurement_threshold_exclusive": 127, "geometry_tolerance_pixels": 1,
        "scope": "N straight pixel correction and one rejected NW concave attempt only",
        "user_visual_approval": False, "complete_tileset": False, "engine_test": "PENDING_ROOT_UNIFIED_GPU_REVIEW",
        "standards": [{"path": relative(BASE.parent / n), "sha256": digest(BASE.parent / n)} for n in ("standard.md", "profiles.json")],
        "handoff_path": "docs/shader-learning/art-production-handoff.md",
        "entries": all_entries, "selected_diagnostic_N_candidate_id": registered_id, "interface_observations": connections,
        "registered_straight_profile_rgba_W_0_to_33": e_straight["W"][:33].tolist(),
        "registered_straight_profile_rgba_E_0_to_33": e_straight["E"][:33].tolist(),
        "remaining_issues": [
            "直岸E/W位置和总宽通过，但左亮右暗端封边仍可见，拒绝作为无缝生产直岸；仅用于对照。",
            "v002整体裁框去除端封边后E/W为33px，处在1px筛查容差内；RGBA与GPU视觉尚未通过，不登记生产可用。",
            "直岸顶边三处板缝导致最外排主体中断1px；主体内部仍单一连通，不做补Alpha修复。",
            "凹角输出的封边压顶、N/W跨度和截面均未与相邻直段统一，拒收。",
            "凹角生成未稳定继承新直岸像素簇，写实颗粒回流，拒收。",
            "新WEST及其它朝向未生成；旧mask31只用于真实邻接的几何诊断。",
            "原稿微弱Alpha散点照实保留，不阈值清理、不补边、不局部变形。",
            "没有完整闭环、没有全部必要形态、没有Godot铺刷通过宣称。",
        ],
        "operations": ["whole square crop/translation", "whole uniform NEAREST reduction", "diagnostic compositing of complete images only"],
        "script_sha256": digest(Path(__file__)), "review_files": [relative(p) for p in sorted((BASE / "review").glob("*.png"))],
    }
    save_json("generation-record.json", report)
    save_json("result.json", {"status": report["status"], "straight": registered_entry, "straight_v001_preserved": entries[0],
                              "inner": entries[1], "interface_observations": connections})
    print(json.dumps({"status": report["status"], "selected_N": registered_id,
                      "ports": {e["id"]: e["candidate_measurements"]["body_ports_alpha_gt127"] for e in all_entries},
                      "registered_interface": connections["registered_v002_straight_E_to_straight_W"]}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
