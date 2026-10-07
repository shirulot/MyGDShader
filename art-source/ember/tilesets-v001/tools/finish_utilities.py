"""以本轮新母稿为材质与零件参考，整理 24 块原生 32×32 设施瓦片。

这一步在用户认可脚本像素整理方案后执行。生成母稿始终保留不覆写。
母稿中的钢管亮暗层、黄铜套筒、铆接岸板先裁剪采样，再在原生网格
重建接头、转角与轮廓；不会把整张大图粗缩后直接登记为完成。

端口采用半开区间 [start,end)。N/S 从左到右，E/W 从上到下。
管线端口固定 10 像素，水岸端口固定 12 像素。水岸是透明边界部件，
内部水面必须另配水纹或材质，不在这 24 块预算内。
"""

from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import sys

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[4]
BATCH = ROOT / "art-source/ember/tilesets-v001"
OUTPUT = BATCH / "finished-tiles/utilities"
PIPE_SOURCE = BATCH / "generated/pipe_module_master_v001.png"
CHANNEL_SOURCE = BATCH / "generated/channel_module_master_v001.png"
COLORS = {
    "ink": "101820", "shadow": "182631", "dark": "2B3E4B", "steel": "4D6470",
    "bright": "829BA3", "light": "BECBC4", "rust": "7B4D35", "brass": "B77C4B",
    "warm": "E2B77A", "energy": "51C5C2", "warning": "E5A44B", "danger": "E65B4A",
    "cold": "566B78", "waterdark": "203A4B", "water": "406B78", "white": "ECE9D8",
}
C = {name: tuple(bytes.fromhex(hex_value)) + (255,) for name, hex_value in COLORS.items()}
STEEL_NAMES = ("ink", "shadow", "dark", "steel", "cold", "bright", "light")
BRASS_NAMES = ("rust", "brass", "warm")
ALL_MATERIAL_NAMES = STEEL_NAMES + BRASS_NAMES
SIDES = "NESW"
CENTER = 15.5
RECORDS: list[dict] = []


@lru_cache(maxsize=65536)
def nearest_color(rgb: tuple[int, ...], names=ALL_MATERIAL_NAMES) -> tuple[int, ...]:
    """仅返回标准中的注册颜色；不用插值颜色或抗锯齿半透明边。"""
    return min((C[name] for name in names),
               key=lambda color: sum((a - b) ** 2 for a, b in zip(rgb[:3], color[:3])))


def native_sample(source: Image.Image, crop_box: tuple, native_size: tuple) -> Image.Image:
    """采样稿仅作为内部参考；后续原生结构、接口与轮廓会明确重绘。"""
    cropped = source.crop(crop_box).resize(native_size, Image.Resampling.NEAREST)
    result = Image.new("RGBA", native_size)
    for y in range(native_size[1]):
        for x in range(native_size[0]):
            pixel = cropped.getpixel((x, y))
            if pixel[3] >= 180:
                result.putpixel((x, y), nearest_color(pixel[:3]))
    return result


def reference_materials() -> tuple[Image.Image, Image.Image, Image.Image, Image.Image]:
    pipe = Image.open(PIPE_SOURCE).convert("RGBA")
    channel = Image.open(CHANNEL_SOURCE).convert("RGBA")
    # 裁出母稿上的管身、三段接头、岸板和铆接立条；舍弃残留低 Alpha 外晕。
    pipe_strip = native_sample(pipe, (72, 308, 748, 495), (32, 10))
    coupling = native_sample(pipe, (835, 258, 1150, 542), (16, 14))
    bank_strip = native_sample(channel, (374, 529, 875, 812), (32, 12))
    bank_bracket = native_sample(channel, (254, 514, 360, 812), (6, 14))
    # 保留采样工程，便于审阅确实来自本轮新母稿；它们不计正式 Tile。
    references = BATCH / "pixel-reference-samples/utilities"
    references.mkdir(parents=True, exist_ok=True)
    for filename, image in (("pipe_strip", pipe_strip), ("coupling", coupling),
                            ("bank_strip", bank_strip), ("bank_bracket", bank_bracket)):
        image.save(references / f"{filename}_sample.png")
    return pipe_strip, coupling, bank_strip, bank_bracket


def rotated_point(point: tuple[float, float], quarter_turns: int) -> tuple[float, float]:
    # 只旋转结构坐标，亮暗会在最终方向重新计算，避免把左上光照也旋转。
    x, y = point
    for _ in range(quarter_turns % 4):
        x, y = 31 - y, x
    return x, y


def elbow_points(direction: str, radius: float = 7.0) -> list[tuple[float, float]]:
    """NE 的弯心偏离中心，得到原生像素中的平滑铸管内外弧。"""
    circle_center = (CENTER + radius, CENTER - radius)
    points = [(CENTER, -8.0), (CENTER, CENTER - radius)]
    for step in range(17):
        angle = math.pi - step * math.pi / 32
        points.append((circle_center[0] + radius * math.cos(angle),
                       circle_center[1] + radius * math.sin(angle)))
    points.append((39.0, CENTER))
    turn = {"ne": 0, "se": 1, "sw": 2, "nw": 3}[direction]
    return [rotated_point(point, turn) for point in points]


def nearest_path(x: float, y: float, paths: list[list[tuple]]) -> tuple[float, float, float]:
    """返回距管中心线最近点；不依赖浮点图像缩放，最终直接写原生像素。"""
    best = (1e9, 0.0, 0.0)
    for path in paths:
        for (x1, y1), (x2, y2) in zip(path, path[1:]):
            vx, vy = x2 - x1, y2 - y1
            length_squared = vx * vx + vy * vy
            ratio = 0.0 if length_squared == 0 else max(0.0, min(1.0, ((x - x1) * vx + (y - y1) * vy) / length_squared))
            px, py = x1 + ratio * vx, y1 + ratio * vy
            distance = math.hypot(x - px, y - py)
            if distance < best[0]:
                best = distance, px, py
    return best


def pipe_paths(variant: str) -> tuple[list[list[tuple]], tuple[str, ...]]:
    endpoints = {"N": (CENTER, -8.0), "E": (39.0, CENTER), "S": (CENTER, 39.0), "W": (-8.0, CENTER)}
    if variant in ("straight_h", "valve"):
        return [[endpoints["W"], endpoints["E"]]], ("E", "W")
    if variant == "straight_v":
        return [[endpoints["N"], endpoints["S"]]], ("N", "S")
    if variant.startswith("elbow_"):
        direction = variant.removeprefix("elbow_")
        return [elbow_points(direction)], tuple(direction.upper())
    if variant == "cross":
        sides = tuple(SIDES)
    else:
        # tee_n 的名字表示支管朝北：东西贯通并在北侧增加一支。
        branch = variant.removeprefix("tee_").upper()
        sides = ("E", "W", branch) if branch in "NS" else ("N", "S", branch)
    return [[[CENTER, CENTER], endpoints[side]] for side in sides], sides


def paint_tube(paths: list[list[tuple]], width: int, sampled_strip: Image.Image) -> Image.Image:
    """以母稿层次为依据重建钢管/岸带；左上受光、右下压暗、外轮廓 1 像素。"""
    image = Image.new("RGBA", (32, 32))
    half = width / 2
    for y in range(32):
        for x in range(32):
            distance, px, py = nearest_path(x, y, paths)
            if distance >= half:
                continue
            nx, ny = x - px, y - py
            facing_light = nx + ny < 0
            if distance >= half - 1:
                color = C["ink"]
            elif distance >= half - 2:
                color = C["bright"] if facing_light else C["shadow"]
            elif distance >= half - 3:
                color = C["cold"] if facing_light else C["dark"]
            else:
                # 留下母稿主材质的安静色块，只取内部钢板区，不保留摄影颗粒。
                along = int(px if abs(ny) >= abs(nx) else py) % sampled_strip.width
                row = sampled_strip.height // 2 - 1
                sample = sampled_strip.getpixel((along, row))
                color = nearest_color(sample[:3], ("steel", "cold"))
            image.putpixel((x, y), color)
    return image


def draw_collar(image: Image.Image, vertical: bool, sample: Image.Image) -> None:
    """重新整理采样接头的 16×14 固定包围盒、三段材质和螺栓孔。"""
    # 此处的轮廓、色阶及孔洞是逐像素工程结构；采样保留少量主面色块。
    draw = ImageDraw.Draw(image)
    if not vertical:
        image.paste(sample, (8, 9), sample)
        draw.polygon([(10, 9), (21, 9), (23, 11), (23, 20), (21, 22), (10, 22), (8, 20), (8, 11)], fill=C["ink"])
        for left, right in ((9, 12), (19, 22)):
            draw.rectangle((left, 10, right, 21), fill=C["steel"])
            draw.line((left, 10, right, 10), fill=C["bright"])
            draw.line((left, 11, left, 20), fill=C["cold"])
            draw.line((left, 21, right, 21), fill=C["dark"])
            draw.point((left + 1, 12), fill=C["ink"])
            draw.point((left + 1, 19), fill=C["ink"])
        for x in range(13, 19):
            for y in range(10, 22):
                sampled = sample.getpixel((x - 8, y - 9))
                image.putpixel((x, y), nearest_color(sampled[:3], BRASS_NAMES))
        draw.line((13, 10, 18, 10), fill=C["warm"])
        draw.line((13, 11, 15, 11), fill=C["warm"])
        draw.line((18, 13, 18, 21), fill=C["rust"])
        draw.line((13, 21, 18, 21), fill=C["rust"])
    else:
        # 垂直接头重新绘制左亮右暗；不是把横向明暗直接旋转。
        draw.polygon([(9, 10), (11, 8), (20, 8), (22, 10), (22, 21), (20, 23), (11, 23), (9, 21)], fill=C["ink"])
        for top, bottom in ((9, 12), (19, 22)):
            draw.rectangle((10, top, 21, bottom), fill=C["steel"])
            draw.line((10, top, 20, top), fill=C["bright"])
            draw.line((10, top, 10, bottom), fill=C["bright"])
            draw.line((21, top, 21, bottom), fill=C["dark"])
            draw.point((12, top + 1), fill=C["ink"])
            draw.point((19, top + 1), fill=C["ink"])
        draw.rectangle((10, 13, 21, 18), fill=C["brass"])
        draw.line((10, 13, 21, 13), fill=C["warm"])
        draw.line((10, 14, 10, 17), fill=C["warm"])
        draw.line((21, 14, 21, 18), fill=C["rust"])
        draw.line((11, 18, 21, 18), fill=C["rust"])


def arm_clamps(image: Image.Image, sides: tuple[str, ...]) -> None:
    """在边界内 5 像素处放低矮管箍；边界端口本身不加封口、无缝对接。"""
    draw = ImageDraw.Draw(image)
    for side in sides:
        if side in "EW":
            x = 26 if side == "E" else 5
            draw.rectangle((x - 1, 10, x + 1, 21), fill=C["dark"])
            draw.line((x - 1, 10, x + 1, 10), fill=C["bright"])
            draw.line((x, 11, x, 20), fill=C["cold"])
            draw.point((x, 12), fill=C["brass"])
        else:
            y = 5 if side == "N" else 26
            draw.rectangle((10, y - 1, 21, y + 1), fill=C["dark"])
            draw.line((10, y - 1, 20, y - 1), fill=C["bright"])
            draw.line((10, y, 20, y), fill=C["cold"])
            draw.point((12, y), fill=C["brass"])


def junction_details(image: Image.Image) -> None:
    """铸造分流座保持钢管连续；小铆钉和分模痕不遮断各支管。"""
    draw = ImageDraw.Draw(image)
    draw.line((13, 13, 18, 13), fill=C["cold"])
    draw.line((13, 14, 13, 18), fill=C["cold"])
    draw.line((14, 19, 18, 19), fill=C["dark"])
    draw.point((13, 13), fill=C["brass"])
    draw.point((18, 18), fill=C["rust"])
    draw.point((14, 14), fill=C["steel"])


def valve_wheel(image: Image.Image) -> None:
    """小型黄铜手轮：有空心内圈、三根辐条与轴心，底图不表现运行发光。"""
    for y in range(8, 24):
        for x in range(8, 24):
            distance = math.hypot(x - CENTER, y - CENTER)
            if 5.0 <= distance < 7.0:
                color = C["ink"] if distance >= 6.0 else (C["warm"] if x + y < 31 else C["rust"])
                image.putpixel((x, y), color)
    draw = ImageDraw.Draw(image)
    # 采用不对称三辐条，与普通套筒区别明显；不以旋转动画假装本次多帧。
    draw.line((15, 10, 15, 16), fill=C["brass"], width=2)
    draw.line((11, 19, 15, 16), fill=C["brass"], width=2)
    draw.line((20, 19, 16, 16), fill=C["rust"], width=2)
    draw.rectangle((14, 14, 17, 17), fill=C["ink"])
    draw.rectangle((15, 15, 16, 16), fill=C["brass"])
    draw.point((15, 15), fill=C["warm"])


def interface_map(sides: tuple[str, ...], kind: str, interval: tuple[int, int]) -> dict:
    declaration = dict.fromkeys(SIDES)
    for side in sides:
        declaration[side] = {"kind": kind, "ports": [list(interval)],
                             "alpha_at_ports": "opaque", "exact_edge_required": False}
    return declaration


def bank_interfaces(variant: str) -> dict:
    """岸带接口同时标记水在哪侧，排除物理口相同但水陆方向相反的组合。

    E/W 接口对应水平岸带，水侧只能为 N/S；N/S 接口对应垂直岸带，
    水侧只能为 E/W。曲岸按每个端口的局部方向登记，不能只写一个全局
    角向。kind 相同才可在同一条水陆轮廓中继续连接。
    """
    water_at_ports = {
        "edge_n": {"E": "N", "W": "N"},
        "edge_s": {"E": "S", "W": "S"},
        "edge_e": {"N": "E", "S": "E"},
        "edge_w": {"N": "W", "S": "W"},
        "outer_ne": {"W": "N", "S": "E"},
        "outer_se": {"W": "S", "N": "E"},
        "outer_sw": {"E": "S", "N": "W"},
        "outer_nw": {"E": "N", "S": "W"},
        "inner_ne": {"N": "E", "E": "N"},
        "inner_se": {"E": "S", "S": "E"},
        "inner_sw": {"W": "S", "S": "W"},
        "inner_nw": {"N": "W", "W": "N"},
    }[variant]
    result = dict.fromkeys(SIDES)
    for side, water_side in water_at_ports.items():
        result[side] = {"kind": f"channel-bank-12px-water-{water_side}-v001",
                        "ports": [[10, 22]], "alpha_at_ports": "opaque",
                        "exact_edge_required": False}
    return result


def save(tile_id: str, image: Image.Image, source: Path, adjustments: list[str], interfaces: dict,
         topology: dict | None = None) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    # 透明像素清空 RGB；可见像素严格属于 16 色，Alpha 只允许 0 / 255。
    for y in range(32):
        for x in range(32):
            pixel = image.getpixel((x, y))
            if pixel[3] == 0:
                image.putpixel((x, y), (0, 0, 0, 0))
            elif pixel[3] != 255 or pixel[:3] not in {color[:3] for color in C.values()}:
                raise ValueError(f"原生调色板或 Alpha 不符：{tile_id} {x},{y}")
    for side, interface in interfaces.items():
        if not interface:
            continue
        for start, end in interface["ports"]:
            for offset in range(start, end):
                coordinate = {"N": (offset, 0), "E": (31, offset), "S": (offset, 31), "W": (0, offset)}[side]
                if image.getpixel(coordinate)[3] != 255:
                    raise ValueError(f"声明端口没有覆盖到图边：{tile_id} {side} {offset}")
    image.save(OUTPUT / f"{tile_id}.png")
    record = {"id": tile_id, "sources": [source.relative_to(ROOT).as_posix()],
              "adjustments": adjustments, "interfaces": interfaces, "native_size": [32, 32],
              "method": "AI_MATERIAL_REFERENCE_AND_NATIVE_PIXEL_FINISH"}
    if topology:
        record["layout_topology"] = topology
    RECORDS.append(record)


def make_pipes(strip: Image.Image, coupling: Image.Image) -> None:
    variants = ["straight_h", "straight_v", "elbow_ne", "elbow_se", "elbow_sw", "elbow_nw",
                "tee_n", "tee_e", "tee_s", "tee_w", "cross", "valve"]
    for variant in variants:
        paths, sides = pipe_paths(variant)
        image = paint_tube(paths, 10, strip)
        if variant in ("straight_h", "straight_v", "valve"):
            draw_collar(image, variant == "straight_v", coupling)
        else:
            arm_clamps(image, sides)
            if variant.startswith("tee_") or variant == "cross":
                junction_details(image)
        if variant == "valve":
            valve_wheel(image)
        save(f"pipe_{variant}", image, PIPE_SOURCE,
             ["采样新母稿钢管横截面与三段黄铜套筒材质", "32×32 中重建10像素管径与1像素外轮廓",
              "四向端口固定在[11,21)，不加边缘封口", "弯曲、分流、十字原生连接轮廓连续化",
              "每个方向重新设置左上亮面，螺孔与卡箍使用原生整数像素", "清除生成外晕，Alpha二值化，颜色固定16色"],
             interface_map(sides, "pipe-10px-v001", (11, 21)),
             {"connected_sides": list(sides), "tee_name": "支管指向；其余两方向贯通" if variant.startswith("tee_") else None})


def bank_paths(variant: str) -> tuple[list[list[tuple]], tuple[str, ...], tuple[str, ...]]:
    if variant.startswith("edge_"):
        water_side = variant[-1].upper()
        if water_side in "NS":
            return [[(-8.0, CENTER), (39.0, CENTER)]], ("E", "W"), (water_side,)
        return [[(CENTER, -8.0), (CENTER, 39.0)]], ("N", "S"), (water_side,)
    corner = variant[-2:]
    water_sides = tuple(corner.upper())
    if variant.startswith("outer_"):
        # 凸出的陆地区块：NE 外角连 W / S，水位于其北方和东方。
        direction = {"ne": "sw", "se": "nw", "sw": "ne", "nw": "se"}[corner]
    else:
        # 凹入的水域：NE 内角连 N / E，水从东北方向凹进陆地。
        direction = corner
    return [elbow_points(direction, 8.0)], tuple(direction.upper()), water_sides


def bank_facing(image: Image.Image, paths: list[list[tuple]], water_sides: tuple[str, ...]) -> None:
    """水侧在岸带内部留1像素冷色包边；透明区不烘焙水面或泡沫。"""
    water_vector = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}
    vx = sum(water_vector[side][0] for side in water_sides)
    vy = sum(water_vector[side][1] for side in water_sides)
    for y in range(32):
        for x in range(32):
            distance, px, py = nearest_path(x, y, paths)
            # 最外缘仍保留深轮廓，冷色只在岸体内，保持像素描边可用。
            if 4.0 <= distance < 5.0 and (x - px) * vx + (y - py) * vy > 0:
                image.putpixel((x, y), C["water"])


def bank_details(image: Image.Image, horizontal: bool, bracket: Image.Image) -> None:
    draw = ImageDraw.Draw(image)
    if horizontal:
        # 母稿铆接立条的色块缩到原生参考，再重新整理宽度和螺栓。
        image.paste(bracket, (13, 9), bracket)
        draw.rectangle((13, 10, 18, 21), fill=C["steel"])
        draw.line((13, 10, 18, 10), fill=C["bright"])
        draw.line((13, 11, 13, 20), fill=C["cold"])
        draw.line((18, 11, 18, 21), fill=C["dark"])
        draw.rectangle((15, 16, 16, 17), fill=C["ink"])
        draw.point((15, 16), fill=C["brass"])
        draw.line((4, 14, 10, 14), fill=C["cold"])
        draw.line((21, 14, 27, 14), fill=C["cold"])
    else:
        # 垂直岸线固定同宽端口，但重新画左受光的支承条，不旋转光照。
        draw.rectangle((10, 13, 21, 18), fill=C["steel"])
        draw.line((10, 13, 20, 13), fill=C["bright"])
        draw.line((10, 14, 10, 18), fill=C["cold"])
        draw.line((21, 14, 21, 18), fill=C["dark"])
        draw.rectangle((16, 15, 17, 16), fill=C["ink"])
        draw.point((16, 15), fill=C["brass"])
        draw.line((14, 4, 14, 10), fill=C["cold"])
        draw.line((14, 21, 14, 27), fill=C["cold"])


def make_banks(strip: Image.Image, bracket: Image.Image) -> None:
    variants = [f"edge_{direction}" for direction in "nesw"]
    variants += [f"{kind}_{direction}" for kind in ("outer", "inner") for direction in ("ne", "se", "sw", "nw")]
    for variant in variants:
        paths, sides, water_sides = bank_paths(variant)
        image = paint_tube(paths, 12, strip)
        bank_facing(image, paths, water_sides)
        if variant.startswith("edge_"):
            bank_details(image, variant[-1] in "ns", bracket)
        else:
            # 在弯角内部放两像素铆接标识，位置取实际岸体内部，不填透明水域。
            for x, y in ((13, 13), (18, 18), (13, 18), (18, 13)):
                if image.getpixel((x, y))[3] == 255:
                    image.putpixel((x, y), C["brass"])
                    break
        save(f"channel_{variant}", image, CHANNEL_SOURCE,
             ["裁出新水岸母稿的钢板主面与黄铜铆接条作为材质参考", "重建12像素岸带和1像素外轮廓",
              "固定全部岸线端口[10,22)，凸角/凹角按真实连接方向分别登记", "水侧冷色包边留在岸体内部，水域保持真实透明",
              "转角重新绘制左上亮暗与铆接像素，避免旋转造成光照漂移", "删除半透明外晕和杂点，固定16色及0/255 Alpha"],
             bank_interfaces(variant),
             {"connected_sides": list(sides), "water_sides": list(water_sides),
              "corner_semantics": "外角为陆地凸出；内角为水域凹入；方向指水侧", "water_surface_included": False})


def verify_matching_ports() -> dict:
    """检查声明口之间没有透明 gap；色差只报告，不当作动态光照错误。"""
    images = {record["id"]: Image.open(OUTPUT / f"{record['id']}.png").convert("RGBA") for record in RECORDS}
    opposite = {"N": "S", "E": "W", "S": "N", "W": "E"}
    comparisons = 0
    for left in RECORDS:
        for right in RECORDS:
            for side in SIDES:
                a = left["interfaces"][side]
                b = right["interfaces"][opposite[side]]
                if a is None or b is None or a["kind"] != b["kind"]:
                    continue
                if a["ports"] != b["ports"]:
                    raise ValueError(f"相同岸带/管径声明口不一致：{left['id']} / {right['id']}")
                for start, end in a["ports"]:
                    for offset in range(start, end):
                        position_a = {"N": (offset, 0), "E": (31, offset), "S": (offset, 31), "W": (0, offset)}[side]
                        position_b = {"N": (offset, 31), "E": (0, offset), "S": (offset, 0), "W": (31, offset)}[side]
                        if images[left["id"]].getpixel(position_a)[3] != 255 or images[right["id"]].getpixel(position_b)[3] != 255:
                            raise ValueError("相反端口有透明缺口")
                comparisons += 1
    return {"matching_port_comparisons": comparisons, "port_alpha_gap_count": 0,
            "scope": "原生尺寸、调色板、二值Alpha、接口覆盖；布局美术仍需拼接图审阅"}


def main() -> None:
    if "--metadata-only" in sys.argv:
        # 审阅发现水陆语义需要更严格时，只更新记录，不重新保存任何 PNG。
        record_path = OUTPUT / "finish-record.json"
        RECORDS.extend(json.loads(record_path.read_text(encoding="utf-8")))
        hashes_before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUT.glob("*.png")}
        for record in RECORDS:
            if record["id"].startswith("channel_"):
                variant = record["id"].removeprefix("channel_")
                record["interfaces"] = bank_interfaces(variant)
                adjustment = "岸线接口kind细分为局部水侧N/E/S/W，排除水陆方向相反的同宽物理口"
                if adjustment not in record["adjustments"]:
                    record["adjustments"].append(adjustment)
        hashes_after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUT.glob("*.png")}
        if hashes_before != hashes_after:
            raise ValueError("metadata-only 不允许改变 PNG 字节")
    else:
        pipe_strip, coupling, bank_strip, bank_bracket = reference_materials()
        make_pipes(pipe_strip, coupling)
        make_banks(bank_strip, bank_bracket)
    if len(RECORDS) != 24:
        raise ValueError("utilities必须恰好24块")
    (OUTPUT / "finish-record.json").write_text(json.dumps(RECORDS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    measurements = verify_matching_ports()
    measurements["tile_count"] = len(RECORDS)
    measurements["bank_interface_semantics"] = "同kind同时具有相同12px端口和相同局部水侧；不同kind不宣称语义互拼"
    if "--metadata-only" in sys.argv:
        measurements["png_hashes_unchanged"] = True
        measurements["png_sha256"] = hashes_after
    measurements["masters_sha256"] = {source.name: hashlib.sha256(source.read_bytes()).hexdigest()
                                       for source in (PIPE_SOURCE, CHANNEL_SOURCE)}
    (OUTPUT / "native-interface-measurements.json").write_text(json.dumps(measurements, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(measurements, ensure_ascii=False))


if __name__ == "__main__":
    main()
