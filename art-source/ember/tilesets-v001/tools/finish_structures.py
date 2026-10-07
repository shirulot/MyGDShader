"""依据新生成母稿整理 26 个原生结构瓦片；保留母稿，不宣称视觉验收通过。

这不是把整张大图缩小：只从明确的钢板/立柱区域抽取材质与零件，再在
32 像素网格手工重建接口、倒角、螺栓和方向光照。所有坐标单位均为原生像素。
桥母稿的棋盘格属于错误背景，采样区全部位于钢板内部；外轮廓重新绘制。
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[2]
OUT = BASE / 'finished-tiles' / 'structures'
OUT.mkdir(parents=True, exist_ok=True)
HEX = ['101820', '182631', '2B3E4B', '4D6470', '829BA3', 'BECBC4',
       '7B4D35', 'B77C4B', 'E2B77A', '51C5C2', 'E5A44B', 'E65B4A',
       '566B78', '203A4B', '406B78', 'ECE9D8']
C = [tuple(bytes.fromhex(s)) + (255,) for s in HEX]
EMPTY = (0, 0, 0, 0)
STEEL = [0, 1, 2, 3, 4, 5, 12]
RECORDS = []
TILES = {}


def px(im, x, y, color):
    if 0 <= x < 32 and 0 <= y < 32:
        im.putpixel((x, y), EMPTY if color is None else C[color])


def rect(im, box, color):
    """包含端点的原生像素矩形，不做抗锯齿。"""
    ImageDraw.Draw(im).rectangle(box, fill=EMPTY if color is None else C[color])


def line(im, points, color, width=1):
    ImageDraw.Draw(im).line(points, fill=C[color], width=width)


def nearest(rgb, indices):
    return min(indices, key=lambda i: sum((rgb[k] - C[i][k]) ** 2 for k in range(3)))


def source_patch(filename, box, size, indices=STEEL):
    """区域采样到原生网格，固定调色板；后续仍须重画接口和方向明暗。

    用块内中位代表色排除母稿细碎抗锯齿，而非把整张母稿粗缩当成成品。
    返回的材质片不保留母稿背景，也不承担最终轮廓。
    """
    src = Image.open(BASE / 'generated' / filename).convert('RGBA')
    x0, y0, x1, y1 = box
    patch = Image.new('RGBA', size, EMPTY)
    for y in range(size[1]):
        for x in range(size[0]):
            sx0, sx1 = int(x0+x*(x1-x0)/size[0]), int(x0+(x+1)*(x1-x0)/size[0])
            sy0, sy1 = int(y0+y*(y1-y0)/size[1]), int(y0+(y+1)*(y1-y0)/size[1])
            # 5×5 规则采样，保留大色块，不把亚像素边缘带入原生瓦片。
            values = [src.getpixel((min(x1-1, sx0+(sx1-sx0)*u//5),
                                   min(y1-1, sy0+(sy1-sy0)*v//5)))[:3]
                      for v in range(5) for u in range(5)]
            rgb = tuple(sorted(p[k] for p in values)[12] for k in range(3))
            patch.putpixel((x, y), C[nearest(rgb, indices)])
    return patch


WALL_SRC = 'wall_module_master_v001.png'
RAIL_SRC = 'railing_module_master_v001.png'
BRIDGE_SRC = 'bridge_module_master_v001.png'
# 采样框是人工查看母稿后选择的钢板/零件区域，完全排除背景。
wall_material = source_patch(WALL_SRC, (436, 283, 1338, 449), (26, 12), [2, 3, 4, 12])
rail_post = source_patch(RAIL_SRC, (102, 254, 239, 676), (7, 21), [0, 1, 2, 3, 4, 5, 6, 7, 8])
bridge_material = source_patch(BRIDGE_SRC, (277, 258, 977, 983), (24, 24), [2, 3, 12])


def bolt(im, x, y, brass=False):
    """母稿方形沉头螺栓转成清晰 3×3 原生图案。"""
    rect(im, (x, y, x+2, y+2), 0)
    px(im, x+1, y, 8 if brass else 4)
    px(im, x+1, y+1, 7 if brass else 3)
    px(im, x+2, y+2, 6 if brass else 1)


def port(kind, ranges):
    return {'kind': kind, 'ports': ranges, 'alpha_at_ports': 'opaque', 'exact_edge_required': False}


def save(tile_id, im, interfaces, source, adjustments):
    # 透明像素 RGB 清零，确保图集边缘导出可复现。
    for y in range(32):
        for x in range(32):
            if im.getpixel((x, y))[3] == 0:
                im.putpixel((x, y), EMPTY)
    assert {im.getpixel((x, y)) for y in range(32) for x in range(32)} <= set(C) | {EMPTY}
    im.save(OUT / (tile_id + '.png'))
    TILES[tile_id] = im
    RECORDS.append({'id': tile_id, 'sources': ['art-source/ember/tilesets-v001/generated/' + source],
                    'adjustments': adjustments, 'interfaces': interfaces,
                    'native_size': [32, 32], 'method': 'AI_MATERIAL_REFERENCE_AND_NATIVE_PIXEL_FINISH'})


def wall_tile(variant):
    """13 片共用同一钢板模块；边界以 4 像素偏移形成可拼装墙顶。"""
    mask = [[True] * 32 for _ in range(32)]
    bounds = []
    if variant.startswith('edge_'):
        bounds = [variant[-1].upper()]
    if variant.startswith('outer_'):
        bounds = list(variant[-2:].upper())
    notch = variant[-2:].upper() if variant.startswith('inner_') else None
    for y in range(32):
        for x in range(32):
            if ('N' in bounds and y < 4) or ('S' in bounds and y >= 28) or ('W' in bounds and x < 4) or ('E' in bounds and x >= 28):
                mask[y][x] = False
            if notch and (x >= 28 if 'E' in notch else x < 4) and (y < 4 if 'N' in notch else y >= 28):
                mask[y][x] = False
    im = Image.new('RGBA', (32, 32), C[3])
    # 母稿钢板上表面及凹槽，作为模块的主材质和识别语汇。
    im.paste(wall_material, (3, 4))
    rect(im, (3, 16, 28, 22), 2)
    line(im, [(4, 16), (27, 16)], 4)
    line(im, [(4, 22), (27, 22)], 1)
    # 低对比板块接缝；跨 tile 的四边保留一致底色，避免每块包黑框。
    line(im, [(6, 3), (25, 3)], 4)
    line(im, [(6, 24), (25, 24)], 2)
    bolt(im, 5, 18)
    bolt(im, 24, 18)
    # 左上倒角和南/东暗面使用世界方向，不旋转现成着色片。
    for y in range(32):
        for x in range(32):
            if not mask[y][x]:
                im.putpixel((x, y), EMPTY)
                continue
            exposed = {d: not mask[yy][xx] for d, xx, yy in
                       [('N', x, y-1), ('S', x, y+1), ('W', x-1, y), ('E', x+1, y)]
                       if 0 <= xx < 32 and 0 <= yy < 32}
            if any(exposed.values()):
                px(im, x, y, 0)
            elif y > 0 and not mask[y-1][x]:
                px(im, x, y, 4)
    # 重画连续边界阶梯，最多三色，独立于材质采样。
    for d in bounds:
        if d == 'N':
            for x in range(32):
                if mask[4][x]:
                    for y, c in [(4, 0), (5, 4), (6, 3)]: px(im, x, y, c)
        elif d == 'S':
            for x in range(32):
                if mask[27][x]:
                    for y, c in [(24, 3), (25, 2), (26, 1), (27, 0)]: px(im, x, y, c)
        elif d == 'W':
            for y in range(32):
                if mask[y][4]:
                    for x, c in [(4, 0), (5, 4), (6, 3)]: px(im, x, y, c)
        elif d == 'E':
            for y in range(32):
                if mask[y][27]:
                    for x, c in [(25, 2), (26, 1), (27, 0)]: px(im, x, y, c)
    # 内角的小缺口同样是结构边界：补清楚的凹角高光和深面。
    if notch:
        nx, ny = (28 if 'E' in notch else 3), (3 if 'N' in notch else 28)
        for y in range(32):
            for x in range(32):
                if not mask[y][x]: continue
                if y > 0 and not mask[y-1][x]: px(im, x, y, 4)
                if x > 0 and not mask[y][x-1]: px(im, x, y, 4)
                if y < 31 and not mask[y+1][x]: px(im, x, y, 1)
                if x < 31 and not mask[y][x+1]: px(im, x, y, 1)
    # 接口按实际边缘的非透明范围分类；无实像素则为封闭边。
    interfaces = {}
    for d in 'NESW':
        values = [mask[0][k] if d == 'N' else mask[31][k] if d == 'S' else
                  mask[k][0] if d == 'W' else mask[k][31] for k in range(32)]
        on = [k for k, v in enumerate(values) if v]
        if not on:
            interfaces[d] = None
        else:
            a, b = min(on), max(on)+1
            # N/S 和 E/W 不混用截面名称；半片边界不可冒充整墙接口。
            orientation = 'vertical' if d in 'NS' else 'horizontal'
            interfaces[d] = port(f'wall-{orientation}-{a}-{b}-v001', [[a, b]])
    save('wall_' + variant, im, interfaces, WALL_SRC,
         ['采样母稿中央墙顶钢板区域(436,283)-(1338,449)，整理为26×12像素材质片',
          '手工重建32×32墙顶、方形凹槽与两个3×3沉头螺栓；四边连续底色',
          '按' + variant + '重画4像素边界/缺口，保持左上亮、右下暗；不旋转方向光',
          '固定16色、二值Alpha；按真实边截面声明连接接口'])


def rail_tile(variant, directions):
    im = Image.new('RGBA', (32, 32), EMPTY)
    # 两根平行钢栏杆；上杆较厚，下杆轻薄，来自生成母稿的双杆结构。
    if 'W' in directions or 'E' in directions:
        xa, xb = (0 if 'W' in directions else 15), (31 if 'E' in directions else 16)
        for y, c in [(9, 0), (10, 4), (11, 3), (12, 2), (19, 4), (20, 2)]:
            line(im, [(xa, y), (xb, y)], c)
    if 'N' in directions or 'S' in directions:
        ya, yb = (0 if 'N' in directions else 15), (31 if 'S' in directions else 16)
        for x, c in [(10, 0), (11, 4), (12, 2), (20, 4), (21, 3), (22, 1)]:
            line(im, [(x, ya), (x, yb)], c)
    # 真实母稿立柱提供面色和两处套环，整理后重画高光和脚座。
    im.paste(rail_post, (13, 5))
    rect(im, (13, 4, 19, 5), 0)
    rect(im, (14, 5, 18, 6), 4)
    rect(im, (13, 9, 19, 12), 2)
    line(im, [(14, 9), (18, 9)], 4)
    rect(im, (12, 9, 13, 12), 7)
    px(im, 12, 9, 8)
    rect(im, (19, 9, 20, 12), 6)
    rect(im, (12, 22, 20, 26), 0)
    rect(im, (13, 22, 19, 24), 3)
    line(im, [(13, 22), (19, 22)], 4)
    px(im, 13, 23, 4)
    # 双栏杆端片在本片中央收束，不给封闭端虚构外部接口。
    if variant.startswith('end_'):
        bolt(im, 15, 14)
    interfaces = {d: None for d in 'NESW'}
    for d in directions:
        interfaces[d] = port('rail-h-v001' if d in 'EW' else 'rail-v-v001',
                             [[9, 13], [19, 21]] if d in 'EW' else [[10, 13], [20, 23]])
    save('rail_' + variant, im, interfaces, RAIL_SRC,
         ['抽取母稿左立柱区域(102,254)-(239,676)为7×21像素零件并固定调色板',
          '在32像素网格重画双钢杆、黄铜上套环、沉头紧固件与脚座',
          '按' + variant + '装配连接方向；四向重新安排左上高光，不机械旋转有向明暗',
          '双栏杆端口分别固定9..12/19..20行或10..12/20..22列；二值Alpha'])


def bridge_tile(variant):
    im = Image.new('RGBA', (32, 32), EMPTY)
    vertical = variant.endswith('_v')
    edge = variant.startswith('edge')
    end = variant == 'end_cap'
    if edge:
        # 桥边沿独立覆盖层：一道带螺栓的钢梁，不冒充主桥面接口。
        if vertical:
            rect(im, (6, 0, 11, 31), 2)
            line(im, [(6, 0), (6, 31)], 4)
            line(im, [(11, 0), (11, 31)], 0)
            bolt(im, 8, 8)
            bolt(im, 8, 24)
        else:
            rect(im, (0, 6, 31, 11), 2)
            line(im, [(0, 6), (31, 6)], 4)
            line(im, [(0, 11), (31, 11)], 0)
            bolt(im, 8, 8)
            bolt(im, 24, 8)
        dirs = 'NS' if vertical else 'EW'
        interfaces = {d: port('bridge-edge-v-v001' if vertical else 'bridge-edge-h-v001', [[6, 12]]) if d in dirs else None for d in 'NESW'}
    else:
        # 母稿桥面钢板与矩形检修槽保留；外侧棋盘格完全不进入采样框。
        rect(im, (4, 0, 27, 31) if vertical else (0, 4, 31, 27), 3)
        im.paste(bridge_material, (4, 4))
        # 将方向光统一到世界左上方，凹槽用4色重描，减少母稿渐变与噪点。
        if vertical:
            line(im, [(4, 0), (4, 31)], 4)
            line(im, [(5, 0), (5, 31)], 3)
            line(im, [(26, 0), (26, 31)], 2)
            line(im, [(27, 0), (27, 31)], 0)
            for y in [8, 20]:
                rect(im, (9, y, 22, y+3), 0)
                line(im, [(10, y+1), (21, y+1)], 1)
                line(im, [(10, y+3), (21, y+3)], 4)
            bolt(im, 5, 14)
            bolt(im, 24, 14)
        else:
            line(im, [(0, 4), (31, 4)], 4)
            line(im, [(0, 5), (31, 5)], 3)
            line(im, [(0, 26), (31, 26)], 2)
            line(im, [(0, 27), (31, 27)], 0)
            for x in [8, 20]:
                rect(im, (x, 9, x+3, 22), 0)
                line(im, [(x+1, 10), (x+1, 21)], 1)
                line(im, [(x+3, 10), (x+3, 21)], 4)
            bolt(im, 14, 5)
            bolt(im, 14, 24)
        # 所有开放端统一清理接缝，避免把母稿单件边框复制到每格。
        if vertical:
            for y in [0, 1, 30, 31]:
                for x in range(6, 26): px(im, x, y, 3)
        else:
            for x in [0, 1, 30, 31]:
                for y in range(6, 26): px(im, x, y, 3)
        dirs = 'NS' if vertical else 'EW'
        if end:
            dirs = 'W'
            rect(im, (28, 4, 31, 27), None)
            rect(im, (25, 4, 27, 27), 0)
            line(im, [(25, 5), (25, 26)], 4)
            bolt(im, 23, 7, True)
            bolt(im, 23, 22, True)
        interfaces = {d: port('bridge-deck-v-v001' if vertical else 'bridge-deck-h-v001', [[4, 28]]) if d in dirs else None for d in 'NESW'}
    save('bridge_' + variant, im, interfaces, BRIDGE_SRC,
         ['仅取母稿钢板内部(277,258)-(977,983)，不采样绘制棋盘格背景',
          '人工重建32×32桥面/边沿轮廓、检修槽与方形紧固件，移除渐变和碎色',
          '按' + variant + '重新绘制左上高光、右下阴影与开放端；桥边梁为独立装饰覆盖层',
          '开放桥面宽24像素；封闭端保留黄铜固定件；二值Alpha、固定16色'])


def main():
    wall_tile('center')
    for d in ['n', 'e', 's', 'w']: wall_tile('edge_' + d)
    for prefix in ['outer_', 'inner_']:
        for d in ['ne', 'se', 'sw', 'nw']: wall_tile(prefix + d)
    for variant, dirs in [('straight_h', 'EW'), ('straight_v', 'NS'),
                          ('corner_ne', 'NE'), ('corner_se', 'SE'),
                          ('corner_sw', 'SW'), ('corner_nw', 'NW'),
                          ('end_h', 'W'), ('end_v', 'N')]:
        rail_tile(variant, dirs)
    for variant in ['deck_h', 'deck_v', 'edge_h', 'edge_v', 'end_cap']:
        bridge_tile(variant)
    assert len(TILES) == 26
    (OUT / 'finish-record.json').write_text(json.dumps(RECORDS, ensure_ascii=False, indent=2), encoding='utf-8')
    # 只作可自动测量的检查，不能替代母稿一致性、造型及地图可读性审阅。
    measurements = []
    for record in RECORDS:
        im = TILES[record['id']]
        rgba = [im.getpixel((x, y)) for y in range(32) for x in range(32)]
        interface_pixels = {}
        for side, spec in record['interfaces'].items():
            if spec is None: continue
            positions = [p for start, end in spec['ports'] for p in range(start, end)]
            samples = [im.getpixel((p, 0) if side == 'N' else (p, 31) if side == 'S' else
                                  (0, p) if side == 'W' else (31, p)) for p in positions]
            opaque = all(v[3] == 255 for v in samples)
            assert opaque, (record['id'], side, 'declared port contains transparency')
            interface_pixels[side] = {'sample_count': len(samples), 'opaque': opaque}
        measurements.append({'id': record['id'], 'size':list(im.size),
                             'bbox':list(im.getbbox()),
                             'opaque_rgb_color_count':len({p[:3] for p in rgba if p[3]}),
                             'alpha_values':sorted({p[3] for p in rgba}),
                             'interfaces':interface_pixels})
    (OUT/'measurements.json').write_text(json.dumps({'tiles':measurements,
        'scope':'AUTOMATED_MEASUREMENTS_ONLY_VISUAL_APPROVAL_NOT_DECLARED'}, ensure_ascii=False, indent=2), encoding='utf-8')
    source_hashes = {name: hashlib.sha256((BASE/'generated'/name).read_bytes()).hexdigest()
                     for name in [WALL_SRC, RAIL_SRC, BRIDGE_SRC]}
    (OUT / 'source-hashes.json').write_text(json.dumps(source_hashes, indent=2), encoding='utf-8')
    # 原生审阅板每片保持32像素，加入空隙与编号，不能作为游戏 atlas。
    native = Image.new('RGB', (320, 192), '#607079')
    native_draw = ImageDraw.Draw(native)
    tiny_font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 8)
    for i, (tile_id, tile) in enumerate(TILES.items()):
        x, y = (i % 8)*40+4, (i//8)*48+2
        native.paste(tile, (x,y), tile)
        native_draw.text((x, y+34), str(i+1), font=tiny_font, fill='#BECBC4')
    native.save(OUT/'structures_native_contact.png')
    # 8 倍只用于查看；成品文件始终保留32×32，不含标签或审阅底色。
    font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 16)
    sheet = Image.new('RGB', (8*280, 4*310), '#182631')
    draw = ImageDraw.Draw(sheet)
    for i, (tile_id, tile) in enumerate(TILES.items()):
        x, y = (i % 8)*280+12, (i//8)*310+12
        bg = Image.new('RGBA', (256, 256), '#607079')
        bg.alpha_composite(tile.resize((256, 256), Image.Resampling.NEAREST))
        sheet.paste(bg.convert('RGB'), (x, y))
        draw.text((x, y+266), tile_id, font=font, fill='#BECBC4')
    sheet.save(OUT/'structures_contact_sheet_8x.png')
    # 连片审阅板：墙的外边/凹角、双杆转角、桥两方向实际连接。
    canvas = Image.new('RGBA', (320, 160), '#4D6470')
    rows = [['wall_outer_nw', 'wall_edge_n', 'wall_outer_ne'],
            ['wall_edge_w', 'wall_center', 'wall_edge_e'],
            ['wall_outer_sw', 'wall_edge_s', 'wall_outer_se']]
    for y, row in enumerate(rows):
        for x, tile_id in enumerate(row): canvas.alpha_composite(TILES[tile_id], (x*32+8, y*32+8))
    for tile_id, x, y in [('rail_corner_se', 4, 0), ('rail_straight_h', 5, 0), ('rail_corner_sw', 6, 0),
                          ('rail_straight_v', 4, 1), ('rail_straight_v', 6, 1),
                          ('rail_corner_ne', 4, 2), ('rail_straight_h', 5, 2), ('rail_corner_nw', 6, 2),
                          ('bridge_deck_h', 4, 4), ('bridge_deck_h', 5, 4), ('bridge_end_cap', 6, 4),
                          ('bridge_deck_v', 8, 0), ('bridge_deck_v', 8, 1), ('bridge_deck_v', 8, 2)]:
        canvas.alpha_composite(TILES[tile_id], (x*32, y*32))
    canvas.resize((1280, 640), Image.Resampling.NEAREST).save(OUT/'structures_connections_4x.png')
    print(json.dumps({'tiles':len(TILES), 'output':str(OUT), 'palette_and_alpha':'all 26 deterministic assertions passed'}, ensure_ascii=False))


if __name__ == '__main__': main()
