"""只拼接已完成的单块瓦片，输出原生连接示例与整数放大诊断图。

不修改瓦片，不生成水面图片，不把诊断图登记为正式资源。
三个 3×3 模式分别验证分支管路、凸出陆地区块岸线、凹入水域岸线。
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[4]
BATCH = ROOT / "art-source/ember/tilesets-v001"
FINISHED = BATCH / "finished-tiles/utilities"
OUTPUT = BATCH / "pixel-review"
PATTERNS = {
    "pipes_3x3": [
        ["pipe_elbow_se", "pipe_tee_s", "pipe_elbow_sw"],
        ["pipe_tee_e", "pipe_cross", "pipe_tee_w"],
        ["pipe_elbow_ne", "pipe_tee_n", "pipe_elbow_nw"],
    ],
    "land_outer_bank_3x3": [
        ["channel_outer_nw", "channel_edge_n", "channel_outer_ne"],
        ["channel_edge_w", None, "channel_edge_e"],
        ["channel_outer_sw", "channel_edge_s", "channel_outer_se"],
    ],
    "water_inner_bank_3x3": [
        ["channel_inner_se", "channel_edge_s", "channel_inner_sw"],
        ["channel_edge_e", None, "channel_edge_w"],
        ["channel_inner_ne", "channel_edge_n", "channel_inner_nw"],
    ],
}


def main():
    OUTPUT.mkdir(exist_ok=True)
    # 底色仅是诊断衬底；不烘焙进岸线、不作为水面资产。
    sheet = Image.new("RGBA", (336, 116), (24, 38, 49, 255))
    drawing = ImageDraw.Draw(sheet)
    for index, (name, pattern) in enumerate(PATTERNS.items()):
        image = Image.new("RGBA", (96, 96))
        for y, row in enumerate(pattern):
            for x, tile_id in enumerate(row):
                if tile_id:
                    image.alpha_composite(Image.open(FINISHED / f"{tile_id}.png").convert("RGBA"), (32 * x, 32 * y))
        image.save(OUTPUT / f"{name}_native_v001.png")
        image.resize((384, 384), Image.Resampling.NEAREST).save(OUTPUT / f"{name}_x4_v001.png")
        origin_x = index * 112
        drawing.rectangle((origin_x + 8, 16, origin_x + 103, 111), fill=(77, 100, 112, 255))
        sheet.alpha_composite(image, (origin_x + 8, 16))
        drawing.text((origin_x + 8, 1), ("PIPE BRANCHES", "LAND OUTER", "WATER INNER")[index], fill=(190, 203, 196, 255))
    sheet.resize((1344, 464), Image.Resampling.NEAREST).save(OUTPUT / "utilities_connected_review_v001.png")
    (OUTPUT / "utilities_3x3_patterns_v001.json").write_text(json.dumps(PATTERNS, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
