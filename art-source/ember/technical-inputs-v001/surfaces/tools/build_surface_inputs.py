"""派生 D09/D11/D12 技术输入；只写新文件，不改已验收底图。

高度不是 RGB 亮度：建筑使用登记的部件几何和真实 Alpha，地板使用
原生整理脚本登记的板缝，金属只把确定的两种涂层标签转成极浅起伏。
这些是供灯光练习的艺术高度场，不是物理测量或真实三维建模。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

SURFACES = Path(__file__).resolve().parents[1]
ROOT = SURFACES.parents[3]
CATALOG = SURFACES / "catalog.json"
ASSETS = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source(path):
    path = ROOT / path
    return {"file": "res://" + relative(path), "sha256": sha(path)}


def erode(mask):
    """四邻域距离用于整数像素倒角，不依赖颜色明暗。"""
    padded = np.pad(mask, 1, constant_values=False)
    return (padded[1:-1, 1:-1] & padded[:-2, 1:-1] & padded[2:, 1:-1]
            & padded[1:-1, :-2] & padded[1:-1, 2:])


def bevel(mask, width):
    result = np.zeros(mask.shape, np.float32)
    inner = mask.copy()
    for _ in range(width):
        result += inner.astype(np.float32) / width
        inner = erode(inner)
    return result


def shape(size, feature):
    im = Image.new("L", size, 0)
    draw = ImageDraw.Draw(im)
    if "polygon" in feature:
        draw.polygon([tuple(p) for p in feature["polygon"]], fill=255)
    elif "ellipse" in feature:
        x0, y0, x1, y1 = feature["ellipse"]
        draw.ellipse((x0, y0, x1 - 1, y1 - 1), fill=255)
    else:
        x0, y0, x1, y1 = feature["rect"]
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=255)
    return np.array(im) > 0


def encode_normal(height, strength, support=None, repeat=False):
    """图像 y 朝下，OpenGL +Y 朝上：n=(-dh/dx,+dh/dy,1)。

    非平铺用居中差分（画布端用单边）；平铺用 256 样本周期差分。
    编码为 round((n*.5+.5)*255)；中性法线是 RGB(128,128,255)。
    """
    if repeat:
        dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) / 2
        dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) / 2
    else:
        dy, dx = np.gradient(height)
    normals = np.stack((-dx * strength, dy * strength, np.ones_like(height)), axis=-1)
    normals /= np.linalg.norm(normals, axis=-1, keepdims=True)
    if support is not None:
        normals[~support] = (0, 0, 1)
    encoded = np.clip(np.floor((normals * .5 + .5) * 255 + .5), 0, 255).astype(np.uint8)
    return encoded, normals, dx, dy


def store_height(id, height, geometry):
    # float32 NPY 是可精确复算的源；灰度预览仅为观察，不能替代源高度。
    field_path = SURFACES / "heightfields" / f"{id}_height_v001.npy"
    field_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(field_path, height.astype(np.float32), allow_pickle=False)
    geometry_path = SURFACES / "geometry" / f"{id}_geometry_v001.json"
    write_json(geometry_path, geometry)
    lo, hi = float(height.min()), float(height.max())
    mapped = np.zeros_like(height, np.uint8) if hi == lo else np.rint((height-lo)/(hi-lo)*255).astype(np.uint8)
    Image.fromarray(mapped).save(SURFACES / "review" / f"{id}_height_display_v001.png")
    return {"file": relative(field_path), "sha256": sha(field_path), "format": "NPY float32 [y,x]",
            "canvas": [height.shape[1], height.shape[0]], "units": "artistic native-pixel relief unit",
            "range": [lo, hi], "geometry_file": relative(geometry_path), "geometry_sha256": sha(geometry_path),
            "physical_model": False}


def save_asset(id, manifest_id, image, file, sources, **data):
    target = ROOT / file
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target)
    entry = {"id": id, "manifest_id": manifest_id, "file": "res://" + file,
             "sha256": sha(target), "canvas": list(image.size), "mode": image.mode,
             "repeat_axes": [], "sampling": "linear data; do not apply sRGB decoding",
             "sources": sources, "source_use": "PROCEDURAL_GEOMETRY_DERIVED_TECHNICAL_INPUT",
             **data}
    ASSETS.append(entry)
    # 每块立即落盘 catalog，使并行集成无需等全部十块。
    write_json(CATALOG, {"schema_version": 1, "status": "GENERATED_PENDING_INDEPENDENT_REVIEW",
                        "normal_convention": "OpenGL +X +Y +Z; image-y down; n=(-dh/dx,+dh/dy,1)",
                        "assets": ASSETS})
    print(id, file, flush=True)
    return entry


def normal_asset(id, manifest, height, geometry, base_path, file, *, support=None,
                 strength=1.0, repeat=False, anchor=None, window=None, base_region=None):
    field = store_height(id, height, geometry)
    encoded, normals, dx, dy = encode_normal(height, strength, support, repeat)
    return save_asset(id, manifest, Image.fromarray(encoded), file, [source(base_path)],
                      heightfield=field, strength=strength, anchor=anchor,
                      neutral_window=window, base_region=base_region,
                      repeat_axes=["X", "Y"] if repeat else [],
                      normal_encoding="RGB8 normalized tangent vector; lossless; normal_map=0",
                      mipmaps=manifest == "D11", texture_filter="LINEAR" if manifest == "D11" else "NEAREST",
                      support="source Alpha exactly; transparent exterior encoded neutral" if support is not None else "full canvas",
                      encoded_max_unit_length_error=float(np.abs(np.linalg.norm(encoded.astype(np.float64)/255*2-1, axis=-1)-1).max()),
                      derivative_max=[float(np.abs(dx).max()), float(np.abs(dy).max())])


def building(id, base_path, annotation, anchor, window, features, base_z):
    base = Image.open(ROOT / base_path).convert("RGBA")
    support = np.array(base.getchannel("A")) == 255
    height = np.full(support.shape, base_z, np.float32)
    for feature in features:
        selection = shape(base.size, feature) & support
        blend = bevel(selection, feature.get("bevel", 2))
        # 每个区域是明确平面高度，倒角只在该区域内，与底图亮度无关。
        height += (feature["z"] - height) * blend
    height *= bevel(support, 2)
    x0, y0, x1, y1 = window
    # 扩一像素的中性平面保证 safe rect 内每一像素的差分法线均为中性。
    height[y0-1:y1+1, x0-1:x1+1] = .38
    height[~support] = 0
    geom = {"id": id, "source": source(base_path), "annotation": source(annotation),
            "coordinate_convention": "pixel boundaries; rect [x0,y0,x1,y1)",
            "canvas": list(base.size), "alpha_bbox": list(base.getbbox()), "anchor": anchor,
            "basis": "source annotation + visually registered component silhouettes; no RGB luminance conversion",
            "base_z": base_z, "outer_bevel_px": 2, "components": features,
            "neutral_window": {"safe_rect": window, "planar_rect": [x0-1,y0-1,x1+1,y1+1], "z": .38},
            "limits": "low relief for CanvasTexture learning; no physical dimensions or back-facing 3D geometry"}
    return normal_asset(id, "D09", height, geom, base_path,
                        f"assets/ember/data/normals/{id}_v001.png", support=support,
                        strength=.85, anchor=anchor, window=window)


def canvas_normals():
    building("station_normal", "assets/ember/buildings/station/station_base_v001.png",
             "art-source/ember/batch-01/pixel-finish-v001/object-layout-v001.json", [64,144], [54,66,74,95], [
                 {"name": "foundation", "rect": [17,117,111,144], "z": .32, "bevel": 2},
                 {"name": "central_housing", "polygon": [[46,29],[80,29],[91,45],[96,107],[87,124],[41,124],[33,107],[35,45]], "z": .95, "bevel": 3},
                 {"name": "roof_cap", "ellipse": [48,28,80,45], "z": 1.1, "bevel": 2},
                 {"name": "window_frame", "rect": [49,60,79,102], "z": 1.04, "bevel": 2},
                 {"name": "left_service_tube", "rect": [27,57,39,114], "z": .58, "bevel": 2},
                 {"name": "right_service_tube", "rect": [89,57,101,114], "z": .58, "bevel": 2},
                 {"name": "front_hatch", "rect": [51,122,77,137], "z": .52, "bevel": 2},
             ], .24)
    building("console_normal", "assets/ember/buildings/console/console_base_v001.png",
             "art-source/ember/batch-03-objects/finished/console_base_v001.finish.json", [48,80], [36,33,60,47], [
                 {"name": "foundation", "rect": [19,63,77,80], "z": .24, "bevel": 2},
                 {"name": "housing", "polygon": [[31,22],[65,22],[70,28],[70,59],[64,67],[32,67],[26,59],[26,28]], "z": .85, "bevel": 3},
                 {"name": "screen_frame", "rect": [33,29,63,50], "z": .94, "bevel": 2},
                 {"name": "control_deck", "rect": [33,51,63,58], "z": .90, "bevel": 2},
                 {"name": "left_coupler", "rect": [20,36,28,63], "z": .48, "bevel": 2},
                 {"name": "right_coupler", "rect": [68,36,76,63], "z": .48, "bevel": 2},
                 {"name": "front_hatch", "rect": [39,67,56,77], "z": .38, "bevel": 2},
             ], .20)
    # floor() 原生几何在 finish_ground_details.py 明确登记，不能把光边当起伏。
    height = np.zeros((32,32), np.float32)
    height[4:28,4:28] = .18
    height[3,3:29] = -.08; height[4:28,3] = -.08
    height[28,4:29] = -.08; height[4:28,28] = -.08
    height[6,6:18] = .13
    height[5,5] = .08; height[26,26] = .08
    geom = {"id": "floor_clean_normal", "source_geometry": source("art-source/ember/tilesets-v001/tools/finish_ground_details.py"),
            "base_region": [0,0,32,32], "basis": "explicit native seams and two assembly indent pixels from floor(clean); not brightness",
            "plate_rect": [4,4,28,28], "plate_z": .18, "seam_z": -.08,
            "seam_segments": [[3,3,29,4],[3,4,4,28],[4,28,29,29],[28,4,29,28]],
            "pressed_line": [6,6,18,7], "pressed_z": .13, "corner_indent_pixels": [[5,5],[26,26]],
            "outer_two_pixels": "height zero, exact repeat gradient support", "period": [32,32]}
    normal_asset("floor_clean_normal", "D09", height, geom,
                 "assets/ember/environment/tilesets/ground_details_v001.png",
                 "assets/ember/data/normals/floor_clean_normal_v001.png", strength=1.0, repeat=True,
                 anchor=[0,0], base_region=[0,0,32,32])


def pbr_inputs():
    for material in ["metal", "concrete"]:
        base_path = f"assets/ember/three_d/textures/{material}/{material}_albedo_v001.png"
        annotation = f"art-source/ember/batch-05-textures/finished-textures/{material}_albedo_v001.finish.json"
        height = np.zeros((256,256), np.float32)
        geom = {"id": material, "source": source(base_path), "annotation": source(annotation),
                "period": [256,256], "units": "artistic native-pixel relief unit", "physical_model": False,
                "no_luminance_to_height": True}
        if material == "metal":
            # 两档真实材质是标签，不以颜色亮度排序，更不把烘焙光照转为高度。
            rgb = np.array(Image.open(ROOT/base_path).convert("RGB"))
            coating = np.all(rgb == (86,107,120), axis=-1).astype(np.float32)
            mask_file = SURFACES / "geometry" / "metal_coating_label_v001.png"
            Image.fromarray((coating*255).astype(np.uint8)).save(mask_file)
            # 环形 5x5 binomial 低通削去原生材质簇的锐边，避免脏点强法线。
            weights = np.array([1,4,6,4,1], np.float32)/16
            filtered = coating
            for axis in [0,1]:
                filtered = sum(weight*np.roll(filtered, shift, axis=axis) for shift,weight in zip(range(-2,3),weights))
            # 沿已登记 5px 接边带把微涂层缝归零：首末边及差分完全相同。
            y,x = np.indices((256,256)); distance = np.minimum.reduce([x,y,255-x,255-y])
            ramp = np.clip((distance-2)/3,0,1).astype(np.float32)
            ramp = ramp*ramp*(3-2*ramp)
            height = filtered*.06*ramp
            geom.update({"method": "categorical coating microseams; separate material labels; periodic binomial smoothing",
                         "coating_label_rgb": [86,107,120], "coating_mask": relative(mask_file), "coating_mask_sha256": sha(mask_file),
                         "max_coating_relief": .06, "smoothing_kernel": [1,4,6,4,1], "kernel_divisor":16,
                         "seam_band_px":5, "neutral_edge_band_px":3,
                         "limitations": "no large panel grid invented; shallow label-boundary relief is an authored approximation"})
        else:
            geom.update({"method": "intentional flat surface height=0", "rationale": "albedo clusters are pigment/aggregate appearance, with no measured relief geometry; avoid speculative bumps"})
        normal_asset(f"{material}_normal", "D11", height, geom, base_path,
                     f"assets/ember/three_d/textures/{material}/{material}_normal_v001.png", strength=1.0, repeat=True, anchor=[0,0])
        for channel, nominal in [("roughness", .65 if material=="metal" else 1.0), ("metallic", .55 if material=="metal" else 0.0)]:
            value = int(np.floor(nominal*255+.5))
            save_asset(f"{material}_{channel}", "D11", Image.new("L",(256,256),value),
                       f"assets/ember/three_d/textures/{material}/{material}_{channel}_v001.png", [source(base_path)],
                       repeat_axes=["X","Y"], nominal_parameter=nominal, channel="R", mipmaps=True,
                       byte_value=value, quantized_parameter=value/255, texture_filter="LINEAR",
                       derivation="documented uniform artistic PBR parameter; no albedo inference")


def grass_weight():
    base_path = "assets/ember/three_d/textures/grass/grass_leaf_v001.png"
    base = Image.open(ROOT/base_path).convert("RGBA")
    support = np.array(base.getchannel("A")) == 255
    ys = np.where(support)[0]
    assert int(ys.min())==10 and int(ys.max())==119, "根/叶顶实际像素变化，不能沿用旧参数"
    y = np.indices(support.shape)[0]
    weight = np.rint(np.clip((119-y)/109,0,1)*255).astype(np.uint8)
    weight[~support] = 0
    geom = {"id":"grass_height_weight", "source":source(base_path),
            "source_annotation":source("art-source/ember/batch-05-textures/finished-textures/grass_leaf_v001.finish.json"),
            "basis":"actual accepted Alpha silhouette; zero outside, linear normalized visible vertical height",
            "root_boundary":120, "zero_root_pixel_y":119, "full_weight_visible_y":10,
            "anchor":[32,120], "formula":"where alpha=255: round(clamp((119-y)/109,0,1)*255); else 0",
            "canvas_height_128_is_not_root":True}
    geometry_path = SURFACES/"geometry/grass_height_weight_geometry_v001.json"
    write_json(geometry_path,geom)
    save_asset("grass_height_weight", "D12", Image.fromarray(weight),
               "assets/ember/three_d/textures/grass/grass_height_weight_v001.png", [source(base_path)],
               anchor=[32,120], channel="R", root_boundary=120, zero_root_pixel_y=119,
               full_weight_visible_y=10, geometry_file=relative(geometry_path), geometry_sha256=sha(geometry_path),
               formula=geom["formula"], mipmaps=True, texture_filter="LINEAR", linear_parameter=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=["canvas","pbr","grass","all"], default="all")
    args = parser.parse_args()
    for name in ["geometry","heightfields","review"]: (SURFACES/name).mkdir(parents=True,exist_ok=True)
    if CATALOG.exists():
        ASSETS.extend(json.loads(CATALOG.read_text(encoding="utf-8"))["assets"])
    ids = {"canvas": ["station_normal","console_normal","floor_clean_normal"],
           "pbr": [f"{m}_{c}" for m in ["metal","concrete"] for c in ["normal","roughness","metallic"]],
           "grass": ["grass_height_weight"]}
    chosen = list(ids) if args.only=="all" else [args.only]
    replace = {id for group in chosen for id in ids[group]}
    ASSETS[:] = [a for a in ASSETS if a["id"] not in replace]
    for group in chosen:
        {"canvas":canvas_normals,"pbr":pbr_inputs,"grass":grass_weight}[group]()


if __name__ == "__main__": main()
