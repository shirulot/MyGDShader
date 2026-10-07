"""根代理生成的走道v002：只做三整格导出、测量和诊断。

只写本目录。保留根代理原稿、旧v001和全部参考，不再调用生图。
测量阈值不写回图像；不修Alpha、不调色、不拉伸、不拼局部。
"""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from PIL import Image

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
RAW = BASE / "corridor_master_pixel_v002.png"
PROMPT = BASE / "corridor_master_pixel_v002.prompt.txt"
ORIGINAL = Path(r"C:\Users\shiru\.codex\generated_images\01a10204-0a39-77b3-b144-9e7a03fd8e93\exec-51e3c031-71fc-411f-9dd7-074da5629293.png")
REFS = [
    (BASE.parent / "corridor/raw/corridor_master_pixel_v001.png", "Image 1: complete continuous corridor edit target"),
    (BASE.parent / "raw/floor_connected_v001.png", "Image 2: matching connected floor style, palette and bevel reference"),
]


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def save_json(name, value):
    (BASE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def bands(condition):
    indices = np.flatnonzero(condition)
    if not len(indices):
        return []
    return [[int(g[0]), int(g[-1])+1] for g in np.split(indices, np.flatnonzero(np.diff(indices)>1)+1)]


def luma(rgb):
    return rgb[:, :, 0]*.2126 + rgb[:, :, 1]*.7152 + rgb[:, :, 2]*.0722


def edges(image):
    a = np.asarray(image.convert("RGBA"))
    return {"N": a[0], "E": a[:, -1], "S": a[-1], "W": a[:, 0]}


def difference(a, b):
    rgb = np.abs(a[:, :3].astype(int)-b[:, :3].astype(int))
    alpha = np.abs(a[:, 3].astype(int)-b[:, 3].astype(int))
    return {"visible_rgba_mismatch_samples": int(((alpha>0)|np.any(rgb>0, axis=1)).sum()),
            "alpha_mismatch_samples": int((alpha>0).sum()), "max_rgb_difference": int(rgb.max()),
            "mean_rgb_absolute_difference": float(rgb.mean())}


def main():
    # 来源核验是字节一致检查；没有重编码或修改根代理原稿。
    assert digest(RAW)==digest(ORIGINAL)
    ref_before = {relative(p): digest(p) for p, _ in REFS}
    original_mode = Image.open(RAW).mode
    raw = Image.open(RAW).convert("RGBA")
    width, height = raw.size
    assert height==width*3, "实际比例不是1:3，不允许机械切三格或非等比拉伸"
    for folder in ("candidates", "review"):
        (BASE / folder).mkdir(exist_ok=True)
    specs = [
        ("floor_end_N_pixel_v002", 16, ["S"], ["N", "E", "W"]),
        ("floor_narrow_NS_pixel_v002", 17, ["N", "S"], ["E", "W"]),
        ("floor_end_S_pixel_v002", 1, ["N"], ["E", "S", "W"]),
    ]
    entries, images = [], []
    stack = Image.new("RGBA", (128, 384))
    for i, (name, mask, opened, closed) in enumerate(specs):
        crop = [0, i*width, width, (i+1)*width]
        # 每个完整方格先裁后等比Nearest，不能缩整张图后偷偷均分。
        tile = raw.crop(crop).resize((128,128), Image.Resampling.NEAREST)
        path = BASE / "candidates" / (name+"_128.png")
        tile.save(path)
        tile.resize((512,512), Image.Resampling.NEAREST).save(BASE / "review" / (name+"_4x.png"))
        alpha = np.asarray(tile)[:, :, 3]
        stack.paste(tile, (0, i*128))
        images.append(tile)
        entries.append({
            "id": name, "family": "floor", "mask": mask, "mask_bit_order": "N NE E SE S SW W NW",
            "open_sides": opened, "closed_sides": closed, "raw_path": relative(RAW), "raw_sha256": digest(RAW),
            "crop_xyxy": crop, "crop_convention": "XYXY half-open", "crop_size": [width,width],
            "candidate_path": relative(path), "candidate_sha256": digest(path), "texture_size": [128,128],
            "world_grid_units": 32, "layer_scale": .25, "uniform_scale_factor": 128/width,
            "resampling": "PIL.Image.Resampling.NEAREST", "alpha_min_max": [int(alpha.min()),int(alpha.max())],
            "alpha_body_ports_gt127": {k:bands(v[:,3]>127) for k,v in edges(tile).items()},
            "status": "DIAGNOSTIC_CANDIDATE_STRUCTURAL_SCREENING_NOT_ALL_PASSED",
            "production_ready": False, "user_visual_approval": False, "GPU_result": "PENDING_ROOT_UNIFIED_REVIEW",
            "no_local_art_or_alpha_repair": True,
        })
    stack.save(BASE / "review/corridor_registered_128x384.png")
    stack.resize((512,1536), Image.Resampling.NEAREST).save(BASE / "review/corridor_registered_4x.png")
    repeat = Image.new("RGBA", (128,640))
    for i, image in enumerate((images[0], images[1], images[1], images[1], images[2])):
        repeat.paste(image, (0,i*128))
    repeat.save(BASE / "review/corridor_mid_repeat_128x640_cpu.png")
    repeat.resize((256,1280), Image.Resampling.NEAREST).save(BASE / "review/corridor_mid_repeat_2x_cpu.png")
    # 游戏显示尺度仅是诊断图；正式切片仍保留128px。
    repeat.resize((32,160), Image.Resampling.NEAREST).save(BASE / "review/corridor_mid_repeat_world32_cpu.png")

    raw_rgb = np.asarray(raw)[:,:,:3]
    rgb = np.asarray(stack)[:,:,:3]
    raw_luma, registered_luma = luma(raw_rgb), luma(rgb)
    raw_x = np.r_[np.arange(90,320),np.arange(402,633)]
    x = np.r_[np.arange(16,56),np.arange(72,112)]
    raw_hprofile = np.median(raw_luma[:,raw_x], axis=1)
    hprofile = np.median(registered_luma[:,x], axis=1)
    raw_vprofile = np.median(raw_luma[100:-100,:], axis=0)
    vprofile = np.median(registered_luma[18:-18,:], axis=0)
    horizontal = bands(hprofile<36)
    internal = [b for b in horizontal if 48<=b[0]<336]
    centers = [(a+b)/2 for a,b in internal]
    targets = [64,128,192,256,320]
    errors = [a-b for a,b in zip(centers,targets)]
    means = [rgb[i*128+12:(i+1)*128-12,12:116].mean(axis=(0,1)).tolist() for i in range(3)]
    e = [edges(image) for image in images]
    interfaces = {"N_end_S_to_NS_N":difference(e[0]["S"],e[1]["N"]),
                  "NS_S_to_S_end_N":difference(e[1]["S"],e[2]["N"]),
                  "NS_repeat_S_to_NS_N":difference(e[1]["S"],e[1]["N"]),
                  "numeric_equality_is_not_visual_acceptance":True}
    alpha = np.asarray(raw)[:,:,3]
    report = {
        "status":"ROOT_GENERATED_V002_MECHANICAL_EXPORT_COMPLETE_NOT_PRODUCTION_ACCEPTED",
        "generator_owner":"root", "root_imagegen_call_count_for_this_input":1,
        "subagent_imagegen_calls_for_this_task":0,
        "note":"This is the root agent's authorized correction generation, not another imagegen call by the corridor subagent.",
        "tool":"image_gen.imagegen built-in", "transparent_background":False,
        "tool_original_path":str(ORIGINAL), "tool_original_sha256":digest(ORIGINAL),
        "raw_path":relative(RAW), "raw_sha256":digest(RAW), "raw_size":[width,height],
        "raw_mode":original_mode, "alpha_min_max":[int(alpha.min()),int(alpha.max())],
        "exact_ratio_1_to_3":True, "prompt_path":relative(PROMPT), "prompt_sha256":digest(PROMPT),
        "prompt":PROMPT.read_text(encoding="utf-8"),
        "references_in_tool_order":[{"path":relative(p),"sha256":digest(p),"role":role} for p,role in REFS],
        "standard":{"path":relative(BASE.parent/"standard.md"),"sha256":digest(BASE.parent/"standard.md")},
        "entries":entries, "interface_observations":interfaces,
        "measurements":{
            "side_beam_target_pixels":8,
            "main_metal_side_band_visual_estimate":{"W":[0,8],"E":[120,128],"width_pixels":[8,8]},
            "inner_separator_dark_bands128":{"W":[8,10],"E":[118,120]},
            "plate_bevel_highlight_columns128":{"W":10,"E":117},
            "complete_visible_frame_including_separator_and_plate_bevel_estimate":{"W":[0,11],"E":[117,128],"width_pixels":[11,11]},
            "side_beam_result":"Main band looks approximately8px; total frame including adjoining roles is approximately11px. Role boundaries are visual estimates, not final shared-profile acceptance.",
            "raw_vertical_dark_bands_luma_lt36":bands(raw_vprofile<36),
            "registered_vertical_dark_bands_luma_lt36":bands(vprofile<36),
            "registered_vertical_median_luma_profile":vprofile.round(3).tolist(),
            "raw_horizontal_dark_bands_luma_lt36":bands(raw_hprofile<36),
            "registered_horizontal_dark_bands_luma_lt36":horizontal,
            "internal_horizontal_bands128":internal,
            "internal_band_centers128":centers, "target_internal_seams128":targets,
            "band_center_errors_pixels":errors,
            "all_internal_band_centers_within_1px":len(errors)==5 and all(abs(v)<=1 for v in errors),
            "threshold_sensitivity_internal_bands":{str(t):[b for b in bands(hprofile<t) if 48<=b[0]<336] for t in (32,36,40)},
            "method":"Read-only Rec709 luminance median bands; raw horizontal x=[90,320)+[402,633), registered x=[16,56)+[72,112); threshold36. Side-role widths visually estimated from registered4x. No pixels modified.",
            "limitations":"Threshold bands locate dark cores, not full bevel extents. Wear and bolts alter local RGB. First band center approximately66 vs target64 remains outside1px screening tolerance. Whole side frame is broader than the metal band; role widths must be checked against matching floor profiles.",
            "thirds_interior_mean_RGB":means, "max_third_mean_RGB_channel_spread":float(np.ptp(np.asarray(means),axis=0).max()),
            "mean_sampling_region":"Each128px tile y=[12,116), x=[12,116); excludes most side/end beams, still includes ordinary plate seams and wear.",
            "color_visual_result":"New image shares blue-grey industrial pixel language with the root matching floor; thirds are close in mean color. This is not exact palette matching or user visual approval.",
        },
        "production_ready":False, "user_visual_approval":False, "GPU_result":"PENDING_ROOT_UNIFIED_REVIEW",
        "complete_tileset":False, "no_local_art_alpha_palette_repair":True, "no_additional_generation":True,
        "operations":["Three complete724x724 square crops", "UniformNEAREST128px exports", "Complete-sliceCPU diagnostics only"],
        "script_sha256":digest(Path(__file__)), "review_paths":[relative(p) for p in sorted((BASE/"review").glob("*.png"))],
        "reference_files_unchanged_after_export":{relative(p):digest(p)==ref_before[relative(p)] for p,_ in REFS},
    }
    save_json("generation-record.json",report)
    save_json("result.json",report)
    save_json("candidate-catalog.json",{"status":report["status"],"entries":entries})
    save_json("prompts.json",{"generator_owner":"root","tool":report["tool"],"transparent_background":False,
                              "referenced_image_paths":[str(p) for p,_ in REFS],"prompt":report["prompt"]})
    print(json.dumps({"status":report["status"],"source_size":[width,height],"subagent_imagegen_calls":0,
                      "side_metal_band_width_estimate":[8,8],"side_total_frame_width_estimate":[11,11],
                      "horizontal_bands128":internal,"errors":errors,
                      "thirds_mean_channel_spread":report["measurements"]["max_third_mean_RGB_channel_spread"],
                      "interfaces":interfaces},ensure_ascii=True,indent=2))


if __name__=="__main__":
    main()
