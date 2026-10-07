"""以同一世界像素尺度并列机器人、采能站与32地板，不改任何生产PNG。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[5]
robot = Image.open(ROOT / "assets/ember/characters/robot/robot_idle_down_v001.png").convert("RGBA")
station = Image.open(ROOT / "assets/ember/buildings/station/station_base_v001.png").convert("RGBA")
floor = Image.open(ROOT / "art-source/ember/tilesets-v001/finished-tiles/ground_details/floor_clean.png").convert("RGBA")
world = Image.new("RGBA", (256, 176), (24, 38, 49, 255))
for y in (128, 160):
    for x in range(0, 256, 32):
        world.paste(floor, (x, y))
# 统一世界接地点 y=144；每件素材仍使用自己的原生画布和已记录锚点。
world.alpha_composite(robot, (32, 64))
world.alpha_composite(station, (120, 0))
board = Image.new("RGBA", (1024, 832), (24, 38, 49, 255))
board.paste(world.resize((1024, 704), Image.Resampling.NEAREST), (0, 64))
draw = ImageDraw.Draw(board)
font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
title = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 25)
draw.text((24, 12), "《余烬采能站》原生素材比例 · 同一4倍整数展示", font=title, fill=(190, 203, 196, 255))
for x in (64, 184):
    draw.line((x * 4 - 8, 64 + 144 * 4, x * 4 + 8, 64 + 144 * 4), fill=(226, 183, 122, 255), width=1)
draw.text((24, 778), "机器人64×96；脚底(32,80)；仅1/20帧", font=font, fill=(190, 203, 196, 255))
draw.text((524, 778), "站点128×160；基座(64,144)", font=font, fill=(190, 203, 196, 255))
output = ROOT / "art-source/ember/references/batch01_native_scale_v002.png"
board.save(output)
print(output.relative_to(ROOT).as_posix())
