"""把已归档新母稿整理为 12 块原生 32×32 地面与细节瓦片。

按用户“继续”执行已提出的确定性像素整理方案。母稿不覆写。
这不是把大图粗缩后直接入库：地板接口、原生板缝、格栅、检修口
安装边框和小物轮廓均在 32 网格中重新整理；采样用于保留新材质。
"""
from functools import lru_cache
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[4]
BATCH = ROOT / "art-source/ember/tilesets-v001"
OUTPUT = BATCH / "finished-tiles/ground_details"
COLORS = {
    "ink": "101820", "shadow": "182631", "dark": "2B3E4B", "steel": "4D6470",
    "bright": "829BA3", "light": "BECBC4", "rust": "7B4D35", "brass": "B77C4B",
    "warm": "E2B77A", "energy": "51C5C2", "warning": "E5A44B", "danger": "E65B4A",
    "cold": "566B78", "waterdark": "203A4B", "water": "406B78", "white": "ECE9D8",
}
C = {key: tuple(bytes.fromhex(value)) + (255,) for key, value in COLORS.items()}
STEEL = ("ink", "shadow", "dark", "steel", "cold", "bright", "light", "rust", "brass", "warm")
RECORDS = []


@lru_cache(maxsize=65536)
def closest(rgb, names=STEEL):
    # 固定颜色集合，不添加抗锯齿或插值颜色。
    return min((C[name] for name in names), key=lambda color: sum((a - b) ** 2 for a, b in zip(rgb, color)))


def quantize(source, names=STEEL, threshold=180):
    result = Image.new("RGBA", source.size)
    for y in range(source.height):
        for x in range(source.width):
            pixel = source.getpixel((x, y))
            if pixel[3] >= threshold:
                result.putpixel((x, y), closest(pixel[:3], names))
    return result


def source_sprite(path, box_size):
    """用主体 Alpha 裁去模型残留透明光边，然后在原生画布整理轮廓。"""
    source = Image.open(path).convert("RGBA")
    mask = source.getchannel("A").point(lambda value: 255 if value >= 180 else 0)
    bbox = mask.getbbox()
    if not bbox:
        raise ValueError(f"母稿没有有效主体：{path}")
    cropped = source.crop(bbox)
    factor = min(box_size[0] / cropped.width, box_size[1] / cropped.height)
    size = (max(1, round(cropped.width * factor)), max(1, round(cropped.height * factor)))
    native = quantize(cropped.resize(size, Image.Resampling.NEAREST))
    return native


def save(tile_id, image, sources, adjustments, interfaces=None):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT / f"{tile_id}.png")
    redraw_ids = {"decal_crack", "decal_rust", "decal_bolts", "decal_oil", "hatch_open"}
    RECORDS.append({"id": tile_id, "sources": sources, "adjustments": adjustments,
                    "interfaces": interfaces or dict.fromkeys("NESW"),
                    "source_use": "DESIGN_REFERENCE_WITH_NATIVE_REDRAW" if tile_id in redraw_ids else
                    "SAMPLED_MATERIAL_OR_COMPONENT_WITH_NATIVE_RETOUCH",
                    "native_size": [32, 32], "method": "AI_MATERIAL_REFERENCE_AND_NATIVE_PIXEL_FINISH"})


def floor(kind):
    path = ROOT / f"art-source/ember/batch-01/generated/floor_{kind}_master_v001.png"
    source = Image.open(path).convert("RGBA")
    # 从板材内部取材质，舍弃大图版缝；连接边将在原生网格中统一重画。
    patch = source.crop((int(source.width * .08), int(source.height * .08),
                         int(source.width * .42), int(source.height * .42)))
    patch = quantize(patch.resize((24, 24), Image.Resampling.NEAREST),
                     ("dark", "steel", "cold", "rust", "waterdark", "water"))
    image = Image.new("RGBA", (32, 32), C["steel"])
    image.paste(patch, (4, 4))
    draw = ImageDraw.Draw(image)
    # 四边最外两列完全相同，四种钢板可任意互接。明暗仅在板内，不占接口。
    draw.rectangle((0, 0, 31, 31), outline=C["steel"], width=2)
    draw.line((3, 3, 28, 3), fill=C["cold"])
    draw.line((3, 4, 3, 27), fill=C["cold"])
    draw.line((4, 28, 28, 28), fill=C["dark"])
    draw.line((28, 4, 28, 27), fill=C["dark"])
    if kind == "clean":
        # 清洁板只留两处装配压痕，压低地面细节密度。
        draw.rectangle((5, 5, 26, 26), fill=C["steel"])
        draw.line((6, 6, 17, 6), fill=C["cold"])
    elif kind == "grate":
        # 原母稿格栅重新按整数像素绘制，槽宽/间距不会受采样漂移影响。
        draw.rectangle((5, 5, 26, 26), fill=C["dark"])
        for y in range(6, 27, 4):
            draw.line((5, y, 26, y), fill=C["cold"])
            draw.line((5, y + 1, 26, y + 1), fill=C["steel"])
        draw.line((15, 5, 15, 26), fill=C["steel"])
        draw.line((16, 5, 16, 26), fill=C["cold"])
    elif kind == "worn":
        # 维护划痕有方向和疏密，不靠随机颗粒产生旧化感。
        draw.line((8, 12, 11, 12), fill=C["dark"])
        draw.line((9, 13, 12, 13), fill=C["cold"])
        draw.line((20, 21, 23, 20), fill=C["dark"])
        draw.point((22, 21), fill=C["rust"])
    elif kind == "wet":
        # 只做静态低对比材质色差，不把水波或反光高光画进底图。
        draw.polygon([(7, 18), (10, 16), (14, 16), (17, 18), (17, 21), (12, 23), (7, 22)], fill=C["water"])
        draw.line((9, 18, 14, 18), fill=C["steel"])
    # 小压痕均处于板内，对应新母稿安装语汇，不构成路线障碍。
    draw.point((5, 5), fill=C["dark"])
    draw.point((26, 26), fill=C["dark"])
    port = {"kind": "floor-flat-v001", "ports": [[0, 32]], "alpha_at_ports": "opaque", "exact_edge_required": True}
    save(f"floor_{kind}", image, [path.relative_to(ROOT).as_posix()],
         ["取板内材质并固定调色板", "原生板缝与格栅整理", "四边两像素统一接口", "删去高频颗粒与动态反光"],
         {side: port.copy() for side in "NESW"})


def hatches():
    path = BATCH / "generated/hatch_closed_module_master_v001.png"
    sampled = source_sprite(path, (28, 28))
    closed = Image.new("RGBA", (32, 32))
    closed.paste(sampled, ((32 - sampled.width) // 2, (32 - sampled.height) // 2))
    draw = ImageDraw.Draw(closed)
    # 安装主体固定在 2..29；板内划出可替换区域，两态共用同一像素边框。
    draw.rectangle((8, 8, 23, 23), fill=C["steel"])
    draw.line((8, 8, 23, 8), fill=C["dark"])
    draw.line((8, 8, 8, 23), fill=C["dark"])
    draw.line((9, 22, 22, 22), fill=C["cold"])
    draw.rectangle((21, 20, 22, 22), fill=C["brass"])
    draw.point((21, 20), fill=C["warm"])
    opened = closed.copy()
    draw = ImageDraw.Draw(opened)
    draw.rectangle((8, 8, 23, 23), fill=C["shadow"])
    draw.line((8, 8, 23, 8), fill=C["ink"])
    draw.line((8, 8, 8, 23), fill=C["ink"])
    # 梯子来自开启母稿：三阶暗槽和两条窄侧梁，不附加水面或运行灯。
    draw.line((10, 10, 10, 23), fill=C["dark"])
    draw.line((21, 10, 21, 23), fill=C["dark"])
    for y in (12, 17, 22):
        draw.line((11, y, 20, y), fill=C["steel"])
        draw.line((11, y + 1, 20, y + 1), fill=C["dark"])
    sources = [path.relative_to(ROOT).as_posix(), (BATCH / "generated/hatch_open_module_master_v001.png").relative_to(ROOT).as_posix()]
    for state, image in (("closed", closed), ("open", opened)):
        save(f"hatch_{state}", image, sources,
             ["主体Alpha去光边并二值化", "28像素安装主体", "两态复用同一外框", "原生内板/梯子整理"])


def decals():
    source_names = {"crack": "crack_decal_master_v002.png", "cable_loop": "cable_loop_module_master_v001.png",
                    "debris": "debris_module_master_v001.png"}
    sizes = {"crack": (19, 19), "cable_loop": (24, 21), "debris": (17, 17)}
    for kind, filename in source_names.items():
        path = BATCH / "generated" / filename
        sprite = source_sprite(path, sizes[kind])
        image = Image.new("RGBA", (32, 32))
        image.paste(sprite, ((32 - sprite.width) // 2, (32 - sprite.height) // 2))
        if kind == "crack":
            # 原薄裂痕缩入原生网格后出现孤点，按母稿走向重连一像素主支。
            image = Image.new("RGBA", (32, 32))
            draw = ImageDraw.Draw(image)
            draw.line([(7, 8), (10, 10), (12, 14), (16, 16), (17, 20), (18, 23)], fill=C["shadow"], width=1)
            draw.line([(16, 16), (20, 14), (22, 11)], fill=C["dark"], width=1)
        save(f"decal_{kind}", image, [path.relative_to(ROOT).as_posix()],
             ["新母稿主体提取", "固定16色与二值Alpha", "按原生轮廓控制尺寸并保留留边", "裂痕孤点按母稿走向重连"] if kind == "crack" else
             ["新母稿主体提取", "固定16色与二值Alpha", "按原生轮廓控制尺寸并保留留边"])

    # 其余三个小贴花从本批物件/地板的维护材质派生，并逐像素整理形状。
    rust = Image.new("RGBA", (32, 32))
    draw = ImageDraw.Draw(rust)
    draw.polygon([(9, 8), (12, 8), (13, 10), (15, 11), (14, 15), (11, 17), (11, 21), (8, 22), (7, 19), (9, 15), (8, 12)], fill=C["rust"])
    draw.line((10, 10, 10, 14), fill=C["brass"])
    draw.point((9, 18), fill=C["brass"])
    draw.point((16, 19), fill=C["rust"])
    save("decal_rust", rust, [(BATCH / "generated/crack_module_master_v001.png").relative_to(ROOT).as_posix()],
         ["参照未选整板母稿的锈迹语汇", "原生重绘疏松锈斑，不保留钢板轮廓"])

    bolts = Image.new("RGBA", (32, 32))
    draw = ImageDraw.Draw(bolts)
    for x, y in ((7, 9), (20, 15), (12, 24)):
        draw.rectangle((x - 2, y - 2, x + 2, y + 2), fill=C["dark"])
        draw.rectangle((x - 1, y - 1, x + 1, y + 1), fill=C["steel"])
        draw.line((x - 1, y - 1, x + 1, y - 1), fill=C["bright"])
        draw.point((x, y), fill=C["shadow"])
    save("decal_bolts", bolts, [(BATCH / "generated/hatch_closed_module_master_v001.png").relative_to(ROOT).as_posix()],
         ["检修口安装螺栓语汇", "原生5像素螺栓，统一左上明暗"])

    oil = Image.new("RGBA", (32, 32))
    draw = ImageDraw.Draw(oil)
    draw.polygon([(9, 12), (12, 11), (16, 12), (20, 10), (23, 12), (22, 16), (24, 19),
                  (21, 22), (16, 21), (13, 23), (8, 21), (7, 17)], fill=C["waterdark"])
    draw.polygon([(10, 13), (14, 13), (16, 15), (20, 13), (20, 16), (22, 19), (17, 19), (12, 21), (9, 19)], fill=C["dark"])
    save("decal_oil", oil, ["art-source/ember/batch-01/generated/floor_wet_master_v001.png"],
         ["潮湿地板暗部材质派生", "原生重绘静态低对比油迹，无反光动画"])


if __name__ == "__main__":
    for kind in ("clean", "worn", "grate", "wet"):
        floor(kind)
    hatches()
    decals()
    (OUTPUT / "finish-record.json").write_text(json.dumps(RECORDS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # 整数放大只是审阅图；单块 PNG 始终为真实 32×32。
    sheet = Image.new("RGBA", (4 * 32, 3 * 32), C["steel"])
    for index, item in enumerate(RECORDS):
        tile = Image.open(OUTPUT / f"{item['id']}.png").convert("RGBA")
        sheet.alpha_composite(tile, ((index % 4) * 32, (index // 4) * 32))
    sheet.resize((512, 384), Image.Resampling.NEAREST).save(BATCH / "ground_details_native_review_4x.png")
    print(json.dumps({"tiles": len(RECORDS), "directory": OUTPUT.relative_to(ROOT).as_posix()}, ensure_ascii=False))
