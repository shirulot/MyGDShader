"""按项目敌人规范切分赤隼八向；只裁切、平移和共同缩放，不生成新造型。"""

from pathlib import Path
import hashlib
import json
import zipfile

import numpy as np
from PIL import Image, ImageDraw


PROJECT = Path(__file__).resolve().parents[3]
WORK = Path(__file__).resolve().parent
SOURCE = PROJECT / "assets/ember/characters/red_falcon_extracted_v001/red_falcon_8dir_horns_removed.png"
GAME = PROJECT / "assets/ember/characters/red_falcon_directions_v001"
HIGH = WORK / "source_512"
DIRECTIONS = ["down", "down_left", "left", "up_left", "up", "up_right", "right", "down_right"]
COMPASS = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]

# 静态母版只校准一次：X 取两只脚接触区域的中心平均值，Y 共用源图地面线。
# 后续同方向动画必须继承这份注册，不能逐帧重新计算 bbox 或缩放。
SOURCE_ROOT_X = [140, 406, 650, 925, 1217, 1506, 1777, 2029]
SOURCE_GROUND_Y = 554
SOURCE_ROOT = (256, 416)
GAME_ROOT = (64, 104)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    GAME.mkdir(parents=True, exist_ok=True)
    HIGH.mkdir(parents=True, exist_ok=True)
    (WORK / ".gdignore").write_text("", encoding="utf-8")
    source_hash = sha256(SOURCE)
    source = Image.open(SOURCE).convert("RGBA")
    assert source.size == (2172, 724), "源图尺寸发生变化，请重新检查注册。"
    pixels = np.asarray(source)
    records = []
    previews = []

    for index, direction in enumerate(DIRECTIONS):
        # 单排源图的八个独立区域。先限制区域，避免补成正方形时带入邻居。
        left = round(index * source.width / 8)
        right = round((index + 1) * source.width / 8)
        top = SOURCE_GROUND_Y - SOURCE_ROOT[1]
        box = (left, top, right, top + 512)
        crop = source.crop(box)
        paste_xy = (SOURCE_ROOT[0] + left - SOURCE_ROOT_X[index], 0)
        high = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        # 不传 mask，原样复制 RGBA，避免把原图半透明边缘再次乘以 Alpha。
        high.paste(crop, paste_xy)
        name = f"red_falcon_{direction}.png"
        high_path = HIGH / name
        high.save(high_path)

        # 同一源图八向统一 1/4 最近邻缩小；128 导出采用二值 Alpha，不代表美术验收通过。
        game = high.resize((128, 128), Image.Resampling.NEAREST)
        game_pixels = np.array(game)
        game_pixels[:, :, 3] = np.where(game_pixels[:, :, 3] >= 128, 255, 0)
        game_pixels[game_pixels[:, :, 3] == 0, :3] = 0
        game = Image.fromarray(game_pixels)
        game_path = GAME / name
        game.save(game_path)
        previews.append(game)

        # 验证高分辨率切图未改变所复制区域的任何像素。
        copied = high.crop((paste_xy[0], 0, paste_xy[0] + crop.width, 512))
        assert copied.tobytes() == crop.tobytes()
        # 被裁掉的上下边缘仅可含低 Alpha 生成噪点，不能裁掉可见角色。
        outside_alpha = np.concatenate((pixels[:top, left:right, 3].ravel(), pixels[top + 512:, left:right, 3].ravel()))
        assert int(outside_alpha.max(initial=0)) < 16
        assert set(np.unique(game_pixels[:, :, 3]).tolist()) == {0, 255}
        bbox = game.getbbox()
        assert bbox and bbox[0] > 0 and bbox[1] > 0 and bbox[2] < 128 and bbox[3] < 128

        records.append({
            "direction": direction,
            "compass": COMPASS[index],
            "source_cell": [left, 0, right - left, source.height],
            "source_crop_xyxy": list(box),
            "source_root_xy": [SOURCE_ROOT_X[index], SOURCE_GROUND_Y],
            "source_512_paste_xy": list(paste_xy),
            "source_512_root_xy": list(SOURCE_ROOT),
            "game_root_xy": list(GAME_ROOT),
            "source_512": f"source_512/{name}",
            "game_128": name,
            "source_512_sha256": sha256(high_path),
            "game_128_sha256": sha256(game_path),
            "game_visible_bbox_xyxy": list(bbox),
            "game_visible_size": [bbox[2] - bbox[0], bbox[3] - bbox[1]],
        })

    manifest = {
        "source": str(SOURCE.relative_to(PROJECT)),
        "source_sha256": source_hash,
        "source_size": list(source.size),
        "status": "static_direction_crops; not an animated idle or a new art approval",
        "specification": "docs/shader-learning/ember-enemy-eight-direction-standard-v002.md",
        "source_512_size": [512, 512],
        "game_size": [128, 128],
        "uniform_source_to_game_scale": 0.25,
        "resampling": "nearest",
        "game_alpha": "binary, threshold >= 128",
        "source_512_alpha": "source RGBA preserved without thresholding",
        "godot": {"centered": False, "offset": [-64, -104], "texture_filter": "Nearest", "scale": [1, 1]},
        "directions": records,
    }
    (GAME / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme = """# 赤隼八向静态切图 v001

从已去掉两个多余头角的 `red_falcon_8dir_horns_removed.png` 裁出；没有重新生成、镜像或补绘角色。

- `game_128/`（ZIP 内）：8 张 128×128 透明 PNG，脚底根点 (64,104)，Nearest，共同缩放 0.25，二值 Alpha。
- `source_512/`：8 张 512×512 透明 PNG，脚底根点 (256,416)。保留裁切区域原始 RGBA 和像素细节，用于后续单方向制作。
- 顺序：down/S、down_left/SW、left/W、up_left/NW、up/N、up_right/NE、right/E、down_right/SE。
- 方向名继承原设定图标签；本次不重新设计原图的侧向姿态，不声明已通过八向造型或动画验收。
- 源图每格先独立裁切，再透明补齐成正方形。共用地面线 y=554；X 在静态母版阶段按两脚接触区域校准一次。源坐标、偏移与 SHA256 见 manifest.json。
- 128 版只是规范尺寸导出，并非人工逐像素重绘。原图仍有的细节或造型问题会保留。

Godot 中使用 128 版：Sprite2D 的 centered=false，offset=(-64,-104)，纹理过滤 Nearest。scale=(1,1) 时画布为128世界单位；实际可见主体尺寸见 manifest。此交付未改动现有场景或玩家。

重跑脚本需要 Python、Pillow、NumPy。脚本仅写本批次专用目录，并验证源文件未变、八方向完整、裁切像素一致、128版二值Alpha与边缘无截断。
"""
    (WORK / "README.md").write_text(readme, encoding="utf-8")
    # 预览同一套128导出图片：上半部深底，下半部浅底，2倍最近邻。
    preview = Image.new("RGB", (1088, 1232), "#202733")
    draw = ImageDraw.Draw(preview)
    for background_index, background in enumerate(("#202733", "#e5e7eb")):
        start_y = background_index * 616
        draw.rectangle((0, start_y, 1087, start_y + 615), fill=background)
        for index, frame in enumerate(previews):
            x = (index % 4) * 272 + 8
            y = start_y + (index // 4) * 300 + 8
            preview.paste(frame.resize((256, 256), Image.Resampling.NEAREST), (x, y), frame.resize((256, 256), Image.Resampling.NEAREST))
            draw.text((x + 8, y + 267), f"{index + 1:02d} {DIRECTIONS[index]} / {COMPASS[index]}", fill="white" if background_index == 0 else "#17202a")
    preview.save(WORK / "directions_preview.png")

    assert sha256(SOURCE) == source_hash, "源图不应被修改。"
    with zipfile.ZipFile(WORK / "red_falcon_directions_v001.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for record in records:
            archive.write(GAME / record["game_128"], f"game_128/{record['game_128']}")
            archive.write(WORK / record["source_512"], record["source_512"])
        archive.write(GAME / "manifest.json", "manifest.json")
        archive.write(WORK / "README.md", "README.md")
        archive.write(WORK / "directions_preview.png", "directions_preview.png")

    print(json.dumps({"game_directory": str(GAME), "source_directory": str(HIGH), "archive": str(WORK / "red_falcon_directions_v001.zip"), "directions": len(records), "checks": "PASS: source unchanged, exact source crops, no visible clipping, uniform scale, binary game alpha", "visible_sizes": [record["game_visible_size"] for record in records]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
