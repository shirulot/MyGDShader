"""从实际 GPU PNG 复核采样结果；作者自审不冒充独立素材审阅。"""
import json
import numpy as np
from PIL import Image
from assemble_catalog import ROOT, PROOF, sha


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    catalog_path = ROOT / "assets/ember/data/technical_inputs_catalog_v001.json"
    catalog = read(catalog_path)
    assets = {a["id"]: a for a in catalog["assets"]}
    report = read(PROOF / "godot-render.json")
    previous = read(PROOF / "attempt-04-before-explicit-import-policy/runtime-review.json")
    assert report["catalog_sha256"] == sha(catalog_path)
    images = {p.name: sha(p) for p in (PROOF / "render").glob("*.png")}
    assert len(images) == 26
    # 此次只修正导入配置；图像与已逐页查看的版本相同，才能沿用视觉意见。
    assert images == previous["screenshot_sha256"], "GPU images changed; inspect new images first"
    assert all(sha(PROOF / "fresh-render" / name) == value for name, value in images.items())
    rechecks = []
    for check in report["gpu_light_checks"]:
        axis = "x" if check["axis"] == "X_RIGHT" else "y"
        component_index = 0 if axis == "x" else 1
        source = ROOT / assets[check["id"]]["file"].removeprefix("res://")
        normal = Image.open(source).convert("RGB").getpixel(tuple(check["source_pixel"]))
        component = normal[component_index] / 255.0 * 2 - 1
        assert abs(component - check["normal_component"]) < 1e-6
        brightness = []
        screen_pixel = check["screen_pixel"]
        for sign in ("negative", "positive"):
            image = Image.open(PROOF / "render" / f"{check['id']}_axis_{axis}_{sign}.png").convert("RGB")
            brightness.append(sum(image.getpixel(tuple(screen_pixel))) / (3 * 255))
        assert abs(brightness[0] - check["brightness_negative_light"]) < 1e-6
        assert abs(brightness[1] - check["brightness_positive_light"]) < 1e-6
        assert (brightness[1] - brightness[0]) * component > 0
        # 两灯距同一实际采样点相等；Y+ 在 Godot 中朝上。
        expected_positions = [[screen_pixel[0] - 300, screen_pixel[1]], [screen_pixel[0] + 300, screen_pixel[1]]] if axis == "x" else [
            [screen_pixel[0], screen_pixel[1] + 300], [screen_pixel[0], screen_pixel[1] - 300]]
        assert check["actual_light_positions"] == expected_positions
        assert check["pass"]
        rechecks.append({"id": check["id"], "axis": axis, "raw_png_brightness": brightness,
            "source_component": component, "sample_and_light_position_pass": True})
    assert len(rechecks) == 8
    left = np.asarray(Image.open(PROOF / "render/surfaces_light_left.png").convert("RGB"), dtype=np.int16)
    right = np.asarray(Image.open(PROOF / "render/surfaces_light_right.png").convert("RGB"), dtype=np.int16)
    difference = np.abs(left - right)
    result = {**previous, "catalog_sha256": sha(catalog_path), "screenshot_sha256": images,
        "asset_sha256": {a["id"]: a["sha256"] for a in catalog["assets"]},
        "fresh_byte_identical": len(images), "raw_gpu_axis_recheck": rechecks,
        "material_light_changed_pixels": int(np.any(difference != 0, axis=2).sum()),
        "material_light_max_channel_delta": int(difference.max()),
        "explicit_import_policy": {"compress/mode": 0, "compress/normal_map": 2,
            "roughness/mode": 1, "detect_3d/compress_to": 0},
        "visual_opinion_reused_only_for_identical_images": True}
    (PROOF / "runtime-review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Runtime review PASS: 8 raw GPU axis checks / 26 identical reviewed screenshots")


if __name__ == "__main__":
    main()
