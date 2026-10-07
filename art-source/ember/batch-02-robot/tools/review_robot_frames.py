"""只读已整理帧，生成全20帧审阅表和四向循环；底色不进入正式PNG。"""
import json
from pathlib import Path
from PIL import Image, ImageDraw

BATCH = Path(__file__).resolve().parents[1]
ROOT = BATCH.parents[2]
catalog = json.loads((BATCH / "frames-catalog-v001.json").read_text(encoding="utf-8"))
frames = {f["id"]: Image.open(ROOT / f["file"].removeprefix("res://")).convert("RGBA")
          for f in catalog["frames"]}
review = BATCH / "pixel-review"
for background, name in [("#4D6470", "neutral"), ("#ECE9D8", "light"), ("#101820", "dark")]:
    board = Image.new("RGBA", (400, 512), background)
    draw = ImageDraw.Draw(board)
    for row, direction in enumerate(catalog["directions"]):
        ids = [f"robot_idle_{direction}"] + [f"robot_walk_{direction}_f{f:02d}" for f in range(4)]
        for col, frame_id in enumerate(ids):
            board.alpha_composite(frames[frame_id], (col * 80 + 8, row * 128 + 8))
            draw.text((col * 80 + 8, row * 128 + 108), direction + (" idle" if col == 0 else f" f{col-1}"),
                      fill="#BECBC4" if name == "dark" else "#101820")
    board.save(review / f"all20_{name}_1x.png")
    board.resize((800, 1024), Image.Resampling.NEAREST).save(review / f"all20_{name}_2x.png")

loop_frames = []
for frame in range(4):
    board = Image.new("RGBA", (320, 112), "#4D6470")
    draw = ImageDraw.Draw(board)
    for col, direction in enumerate(catalog["directions"]):
        board.alpha_composite(frames[f"robot_walk_{direction}_f{frame:02d}"], (col * 80 + 8, 0))
        draw.text((col * 80 + 12, 96), direction, fill="#ECE9D8")
    loop_frames.append(board.resize((640, 224), Image.Resampling.NEAREST))
# APNG 精确125ms；GIF的10ms量化使用120/130交替，完整周期均为500ms。
loop_frames[0].save(review / "walk_all_directions_8fps_2x.apng", save_all=True,
                    append_images=loop_frames[1:], duration=125, loop=0, disposal=1, blend=0)
# 自动量化可能把小面积黄铜色合并；使用登记色表保留角色原色。
palette = Image.new("P", (1, 1))
palette.putpalette([v for value in catalog["palette"] for v in bytes.fromhex(value[1:])]
                   + [0] * (768 - 16 * 3))
gif = [im.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE) for im in loop_frames]
gif[0].save(review / "walk_all_directions_8fps_2x.gif", save_all=True,
            append_images=gif[1:], duration=[120, 130, 120, 130], loop=0, disposal=2)
print("20帧三背景审阅表与四向500ms循环已保存")
