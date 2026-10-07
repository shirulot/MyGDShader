"""完整走道母图的三整格裁切和诊断；只写本 corridor 目录。

源图只生成一次。这里只机械裁切完整方格并等比 Nearest 导出；
不绘制美术、不调色、不修 Alpha、不拼局部、不旋转或镜像。
诊断中的亮度阈值只做测量，绝不写回图片。
"""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from PIL import Image

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
RAW = BASE / "raw/corridor_master_pixel_v001.png"
TOOL_ORIGINAL = Path(r"C:\Users\shiru\.codex\generated_images\01a10c06-70f1-7100-bf8d-c2032eb22807\exec-5cc27424-cc8e-42bb-b1be-07763bebaa93.png")
REFERENCE = ROOT / "art-source/ember/production-v008/correction-v001/raw/floor_center_pixel_v001.png"
PROMPT = BASE / "corridor_master_pixel_v001.prompt.txt"


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def write_json(name, value):
    (BASE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def edge_data(image):
    a = np.asarray(image.convert("RGBA"))
    return {"N": a[0], "E": a[:, -1], "S": a[-1], "W": a[:, 0]}


def difference(first, second):
    # 连续母图中相邻两排不要求RGB完全相同；这里仍完整记录差异。
    rgb = np.abs(first[:, :3].astype(int) - second[:, :3].astype(int))
    alpha = np.abs(first[:, 3].astype(int) - second[:, 3].astype(int))
    return {
        "visible_rgba_mismatch_samples": int(((alpha > 0) | np.any(rgb > 0, axis=1)).sum()),
        "alpha_mismatch_samples": int((alpha > 0).sum()),
        "max_rgb_difference": int(rgb.max()), "mean_rgb_absolute_difference": float(rgb.mean()),
    }


def intervals(indices):
    return [[int(g[0]), int(g[-1])+1] for g in np.split(indices, np.flatnonzero(np.diff(indices)>1)+1)] if len(indices) else []


def main():
    assert digest(RAW) == digest(TOOL_ORIGINAL), "完整原稿副本必须保持工具原文件字节不变"
    source = Image.open(RAW)
    rgba = source.convert("RGBA")
    width, height = rgba.size
    # 只有精确1:3才按三格机械导出，禁止拉伸或偷裁成目标比例。
    assert height == 3*width, "实际比例不是1:3，须联系根代理评估后再切"
    for name in ("candidates", "review"):
        (BASE / name).mkdir(exist_ok=True)
    specs = [
        ("floor_end_N_pixel_v001", 16, ["S"], ["N", "E", "W"]),
        ("floor_narrow_NS_pixel_v001", 17, ["N", "S"], ["E", "W"]),
        ("floor_end_S_pixel_v001", 1, ["N"], ["E", "S", "W"]),
    ]
    entries, images = [], []
    stack = Image.new("RGBA", (128, 384))
    for i, (name, mask, opened, closed) in enumerate(specs):
        crop = [0, i*width, width, (i+1)*width]
        image = rgba.crop(crop).resize((128, 128), Image.Resampling.NEAREST)
        path = BASE / "candidates" / (name + "_128.png")
        image.save(path)
        image.resize((512, 512), Image.Resampling.NEAREST).save(BASE / "review" / (name + "_4x.png"))
        images.append(image)
        stack.paste(image, (0, i*128))
        alpha = np.asarray(image)[:, :, 3]
        entries.append({
            "id": name, "family": "floor", "mask": mask,
            "mask_bit_order": "N NE E SE S SW W NW", "open_sides": opened, "closed_sides": closed,
            "raw_path": relative(RAW), "raw_sha256": digest(RAW),
            "crop_xyxy": crop, "crop_convention": "XYXY half-open", "crop_size": [width, width],
            "candidate_path": relative(path), "candidate_sha256": digest(path),
            "texture_size": [128, 128], "world_grid_units": 32, "layer_scale": 0.25,
            "uniform_scale_factor": 128/width, "resampling": "PIL.Image.Resampling.NEAREST",
            "alpha_min_max": [int(alpha.min()), int(alpha.max())],
            "actual_alpha_body_ports_gt127": {k: intervals(np.flatnonzero(v[:, 3]>127)) for k, v in edge_data(image).items()},
            "status": "REJECTED_STRUCTURAL_TARGETS_DIAGNOSTIC_ONLY", "production_ready": False,
            "no_local_art_or_alpha_repair": True, "user_visual_approval": False,
        })
    stack.save(BASE / "review/corridor_registered_128x384.png")
    stack.resize((512, 1536), Image.Resampling.NEAREST).save(BASE / "review/corridor_registered_4x.png")
    # 拼完整切片测试中段重复；没有复制或修改某条边。
    repeat = Image.new("RGBA", (128, 640))
    for i, image in enumerate((images[0], images[1], images[1], images[1], images[2])):
        repeat.paste(image, (0, i*128))
    repeat.save(BASE / "review/corridor_mid_repeat_128x640_cpu.png")
    repeat.resize((256, 1280), Image.Resampling.NEAREST).save(BASE / "review/corridor_mid_repeat_2x_cpu.png")

    rgb = np.asarray(stack)[:, :, :3]
    luma = rgb[:, :, 0]*.2126 + rgb[:, :, 1]*.7152 + rgb[:, :, 2]*.0722
    # 避开两侧外梁及中间竖板缝，用横向中位数定位主暗板缝。
    columns = np.r_[np.arange(8, 58), np.arange(70, 120)]
    median = np.median(luma[:, columns], axis=1)
    dark_bands = intervals(np.flatnonzero(median < 40))
    means = [rgb[i*128+8:(i+1)*128-8, 8:120].mean(axis=(0, 1)).tolist() for i in range(3)]
    e = [edge_data(image) for image in images]
    interfaces = {
        "N_end_S_to_NS_N": difference(e[0]["S"], e[1]["N"]),
        "NS_S_to_S_end_N": difference(e[1]["S"], e[2]["N"]),
        "NS_repeat_S_to_NS_N": difference(e[1]["S"], e[1]["N"]),
        "numeric_equality_is_not_visual_acceptance": True,
    }
    palette_probe = np.asarray(Image.open(REFERENCE).convert("RGB"))
    reference_mean = palette_probe[32:-32, 32:-32].mean(axis=(0, 1)).tolist()
    raw_alpha = np.asarray(rgba)[:, :, 3]
    report = {
        "status": "ONE_CONTINUOUS_MOTHER_COLOR_STABLE_STRUCTURAL_TARGETS_REJECTED",
        "built_in_generation_call_count": 1, "maximum_authorized_calls": 1,
        "tool": "image_gen.imagegen built-in", "transparent_background": False,
        "tool_original_path": str(TOOL_ORIGINAL), "tool_original_sha256": digest(TOOL_ORIGINAL),
        "raw_path": relative(RAW), "raw_sha256": digest(RAW), "raw_dimensions": [width, height],
        "raw_mode": source.mode, "raw_alpha_min_max": [int(raw_alpha.min()), int(raw_alpha.max())],
        "actual_ratio_exact_1_to_3": True, "registered_logical_size": [128, 384],
        "prompt_path": relative(PROMPT), "prompt_sha256": digest(PROMPT),
        "reference": {"path": relative(REFERENCE), "sha256": digest(REFERENCE), "role": "ONLY pixel style and palette reference; no old realistic or endpoint references"},
        "entries": entries, "interface_observations": interfaces,
        "inspection": {
            "continuous_full_width_opaque_floor": True,
            "target_side_beam_width_pixels": 8,
            "observed_side_frame_width_approx_pixels": [2, 3],
            "side_width_measurement_method": "visual estimate from registered 4x image; dark outer edge plus pale contour, plate face begins near x=2..3",
            "side_beam_8px_result": False,
            "target_plate_grid": "2 columns x 6 rows; seams y=64,128,192,256,320",
            "observed_main_horizontal_dark_bands": dark_bands,
            "horizontal_band_scan_method": "median Rec709 luma<40 over x=[8,58)+[70,120); diagnostics only, not image editing",
            "target_grid_result": False,
            "top_middle_bottom_interior_mean_RGB": means,
            "max_third_mean_RGB_channel_spread": float(np.ptp(np.asarray(means), axis=0).max()),
            "reference_mean_RGB_interior_32px_inset_NOT_exact_style_test": reference_mean,
            "material_visual_result": "同一母图保持蓝灰像素配色，三段均值稳定，未见整体上下渐变；用户视觉认可未取得。",
            "geometry_visual_result": "外侧梁明显不足8px；六行板缝逐步偏离64px节奏，三格内部不能登记统一64px网格通过。",
        },
        "production_ready": False, "user_visual_approval": False, "GPU_result": "PENDING_ROOT_UNIFIED_REVIEW",
        "operations": ["one continuous generated mother", "three complete equal square crops", "uniform NEAREST 128px exports", "CPU complete-slice repeat diagnostic only"],
        "no_additional_generation": True, "no_local_art_alpha_palette_repair": True,
        "script_sha256": digest(Path(__file__)),
        "review_paths": [relative(p) for p in sorted((BASE / "review").glob("*.png"))],
    }
    write_json("prompts.json", {"generation_count": 1, "tool": report["tool"], "transparent_background": False,
                                "referenced_image_paths": [str(REFERENCE)], "prompt": PROMPT.read_text(encoding="utf-8")})
    write_json("candidate-catalog.json", {"status": report["status"], "entries": entries})
    write_json("generation-record.json", report)
    write_json("result.json", report)
    print(json.dumps({"status": report["status"], "actual_size": [width, height], "candidate_count": 3,
                      "dark_bands": dark_bands, "third_mean_RGB_spread": report["inspection"]["max_third_mean_RGB_channel_spread"],
                      "interfaces": interfaces}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
