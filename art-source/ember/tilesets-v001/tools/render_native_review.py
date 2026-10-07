"""生成原生/整数放大、地板平铺和已声明连接的审阅图。

此文件只组合已有 32×32 内容，不改生产单块；审阅文字/底色不入 atlas。
--ground-only 可在另外两包仍整理时先检查地板。完整连接分页来自实际
验收报告中的全部有向组合，不把未声明连接当作任意可用连接。
"""
import json
from math import ceil
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[4]
BATCH = ROOT / "art-source/ember/tilesets-v001"
REVIEW = BATCH / "review"
REVIEW.mkdir(exist_ok=True)
PLAN = json.loads((BATCH / "planned-catalog-v001.json").read_text(encoding="utf-8"))
FONT = "C:/Windows/Fonts/msyh.ttc"
SMALL = ImageFont.truetype(FONT, 12)
TEXT = ImageFont.truetype(FONT, 16)
TITLE = ImageFont.truetype(FONT, 24)
BG = (24, 38, 49, 255)
FG = (190, 203, 196, 255)
LABEL = (226, 183, 122, 255)
TILES = {}
for atlas in PLAN["atlases"]:
    for tile in atlas["tiles"]:
        path = BATCH / "finished-tiles" / atlas["id"] / (tile["id"] + ".png")
        if path.is_file():
            TILES[atlas["id"] + "/" + tile["id"]] = Image.open(path).convert("RGBA")


def get(tile_id):
    return next(image for ref, image in TILES.items() if ref.split("/", 1)[1] == tile_id)


def floor_base(size):
    image = Image.new("RGBA", size)
    floor = get("floor_clean")
    for y in range(0, size[1], 32):
        for x in range(0, size[0], 32):
            image.paste(floor, (x, y))
    return image


def stamp(board, image, position, scale=1):
    image = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
    board.alpha_composite(image, position)


# 每块 3×3 自身平铺，2x 与文件原生 PNG 对应。
board = Image.new("RGBA", (896, 304), BG)
draw = ImageDraw.Draw(board)
draw.text((20, 12), "四种地板 · 3×3 连铺 · 整数2倍", font=TITLE, fill=FG)
for index, kind in enumerate(("clean", "worn", "grate", "wet")):
    image = Image.new("RGBA", (96, 96))
    for y in range(3):
        for x in range(3):
            image.paste(get("floor_" + kind), (x * 32, y * 32))
    stamp(board, image, (20 + index * 220, 60), 2)
    draw.text((20 + index * 220, 262), "floor_" + kind, font=TEXT, fill=LABEL)
board.save(REVIEW / "floor_self_3x3_2x.png")

# 16 个有向类型组合，每格同时显示水平与垂直相邻的原生内容。
board = Image.new("RGBA", (1456, 792), BG)
draw = ImageDraw.Draw(board)
draw.text((20, 12), "全部16种地板类型相邻 · 左水平 / 右垂直 · 整数2倍", font=TITLE, fill=FG)
kinds = ("clean", "worn", "grate", "wet")
for a, first in enumerate(kinds):
    for b, second in enumerate(kinds):
        x, y = 20 + b * 358, 62 + a * 178
        horizontal = Image.new("RGBA", (64, 32))
        horizontal.paste(get("floor_" + first), (0, 0))
        horizontal.paste(get("floor_" + second), (32, 0))
        vertical = Image.new("RGBA", (32, 64))
        vertical.paste(get("floor_" + first), (0, 0))
        vertical.paste(get("floor_" + second), (0, 32))
        stamp(board, horizontal, (x, y + 30), 2)
        stamp(board, vertical, (x + 162, y + 30), 2)
        draw.text((x, y), first + " → " + second, font=TEXT, fill=LABEL)
board.save(REVIEW / "all_floor_adjacencies_2x.png")

if "--ground-only" in sys.argv:
    print(json.dumps({"ground_reviews": 2}, ensure_ascii=False))
    raise SystemExit(0)
if len(TILES) != 62:
    raise SystemExit(f"完整审阅需要62块，目前{len(TILES)}")

# 带 ID 的两倍总览；同时保存无文字原生版和完全相同 RGBA 的二倍版。
rows = sum(ceil(len(atlas["tiles"]) / 8) for atlas in PLAN["atlases"])
board = Image.new("RGBA", (960, 75 + rows * 110 + 3 * 46), BG)
draw = ImageDraw.Draw(board)
draw.text((24, 12), "《余烬采能站》三套通用瓦片 · 62块 · 原生32×32", font=TITLE, fill=FG)
draw.text((24, 47), "下方每块整数2倍；透明构件叠在实际地板上审阅。", font=TEXT, fill=LABEL)
labels = {"ground_details": "地面与细节 · 12", "structures": "墙体 / 栏杆 / 桥面 · 26", "utilities": "管线 / 水渠岸线 · 24"}
y = 84
for atlas in PLAN["atlases"]:
    draw.text((24, y), labels[atlas["id"]], font=TITLE, fill=LABEL)
    y += 44
    for index, tile in enumerate(atlas["tiles"]):
        x0, y0 = 24 + (index % 8) * 116, y + (index // 8) * 110
        sample = floor_base((32, 32))
        sample.alpha_composite(TILES[atlas["id"] + "/" + tile["id"]])
        stamp(board, sample, (x0 + 20, y0), 2)
        draw.text((x0, y0 + 70), tile["id"], font=SMALL, fill=FG)
        draw.text((x0, y0 + 88), str(tile["coord"]), font=SMALL, fill=LABEL)
    y += ceil(len(atlas["tiles"]) / 8) * 110
board.save(REVIEW / "tileset_catalog_2x.png")
for atlas in PLAN["atlases"]:
    native = Image.open(BATCH / "native-atlases" / (atlas["id"] + "_v001.png")).convert("RGBA")
    native.resize((native.width * 2, native.height * 2), Image.Resampling.NEAREST).save(REVIEW / (atlas["id"] + "_2x.png"))

# 组合示例只是可复用模块的连接展示，生产中没有整张关卡背景。
demo = floor_base((20 * 32, 11 * 32))
def place(tile_id, x, y):
    demo.alpha_composite(get(tile_id), (x * 32, y * 32))
for y0, row in enumerate((("wall_outer_nw", "wall_edge_n", "wall_outer_ne"),
                           ("wall_edge_w", "wall_center", "wall_edge_e"),
                           ("wall_outer_sw", "wall_edge_s", "wall_outer_se"))):
    for x0, name in enumerate(row):
        place(name, x0 + 1, y0 + 1)
for x0, name in enumerate(("rail_corner_se", "rail_straight_h", "rail_straight_h", "rail_corner_sw")):
    place(name, x0 + 6, 1)
    place(("rail_corner_ne", "rail_straight_h", "rail_straight_h", "rail_corner_nw")[x0], x0 + 6, 4)
for y0 in (2, 3):
    place("rail_straight_v", 6, y0)
    place("rail_straight_v", 9, y0)
for x0, name in enumerate(("pipe_elbow_se", "pipe_straight_h", "pipe_tee_s", "pipe_valve", "pipe_elbow_sw")):
    place(name, x0 + 12, 1)
for y0 in (2, 3):
    place("pipe_straight_v", 12, y0)
    place("pipe_straight_v", 16, y0)
for x0, name in enumerate(("pipe_elbow_ne", "pipe_straight_h", "pipe_tee_n", "pipe_straight_h", "pipe_elbow_nw")):
    place(name, x0 + 12, 4)
place("pipe_cross", 14, 3)
place("pipe_straight_v", 14, 2)
place("pipe_tee_e", 12, 3)
place("pipe_straight_h", 13, 3)
place("pipe_straight_h", 15, 3)
place("pipe_tee_w", 16, 3)
# 水面单色仅是审阅底色，不是新增/生产水纹。edge后缀指水侧；水在
# 池内时顶边water=S、左边water=E，四角使用凹入水域的inner片。
draw_demo = ImageDraw.Draw(demo)
draw_demo.rounded_rectangle((6 * 32 + 16, 6 * 32 + 16, 11 * 32 - 16, 10 * 32 - 16),
                            radius=12, fill=(32, 58, 75, 255))
shore_rows = (("channel_inner_se", "channel_edge_s", "channel_edge_s", "channel_edge_s", "channel_inner_sw"),
              ("channel_inner_ne", "channel_edge_n", "channel_edge_n", "channel_edge_n", "channel_inner_nw"))
for row, y0 in zip(shore_rows, (6, 9)):
    for x0, name in enumerate(row):
        place(name, x0 + 6, y0)
for y0 in (7, 8):
    place("channel_edge_e", 6, y0)
    place("channel_edge_w", 10, y0)
for x0 in range(6, 11):
    place("bridge_deck_h", x0, 8)
place("hatch_closed", 2, 7)
place("hatch_open", 3, 7)
for index, name in enumerate(("crack", "rust", "bolts", "oil", "cable_loop", "debris")):
    place("decal_" + name, 12 + index, 7)
demo.save(REVIEW / "module_connections_native.png")
demo.resize((1280, 704), Image.Resampling.NEAREST).save(REVIEW / "module_connections_2x.png")

# 逐个有向声明组合分页留证据；跨种类未声明的对接不自动登记成功。
report = json.loads((BATCH / "validation-native-atlases.json").read_text(encoding="utf-8"))
comparisons = report["connections"]["comparisons"]
pages = []
for page in range(ceil(len(comparisons) / 40)):
    proof = Image.new("RGBA", (896, 1874), BG)
    draw = ImageDraw.Draw(proof)
    draw.text((18, 12), f"已声明有向连接 · {page + 1} / {ceil(len(comparisons) / 40)} · 2倍", font=TITLE, fill=FG)
    for index, item in enumerate(comparisons[page * 40:(page + 1) * 40]):
        first, second, side = item["first"], item["second"], item["side"]
        pair = floor_base((64, 64))
        positions = {"E": ((0, 0), (32, 0)), "W": ((32, 0), (0, 0)),
                     "N": ((0, 32), (0, 0)), "S": ((0, 0), (0, 32))}[side]
        pair.alpha_composite(TILES[first], positions[0])
        pair.alpha_composite(TILES[second], positions[1])
        x0, y0 = 18 + (index % 4) * 220, 60 + (index // 4) * 181
        stamp(proof, pair, (x0 + 36, y0 + 38), 2)
        draw.text((x0, y0), first.split("/")[1], font=SMALL, fill=FG)
        draw.text((x0, y0 + 16), side + " → " + second.split("/")[1], font=SMALL, fill=LABEL)
    # v002 标识加入水侧语义后的组合；保留v001物理端口审阅页作过程记录。
    name = f"declared_connections_v002_{page + 1:02}.png"
    proof.save(REVIEW / name)
    pages.append(name)
(REVIEW / "review-index.json").write_text(json.dumps({
    "native_tile_count": 62, "directed_connections": len(comparisons),
    "connection_pages": pages, "method": "native RGBA composition and integer nearest previews",
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"native_tiles": 62, "connection_pages": len(pages), "directed_connections": len(comparisons)}, ensure_ascii=False))
