"""按真实占用邻域选择官方47槽，绘制源图试铺对照；绝不修补图块。"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parent
REVIEW = P / 'review'
FONT = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 18)
DIRECTIONS = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

def mask_for(cell, occupied):
    x, y = cell
    active = [(x+dx, y+dy) in occupied for dx, dy in DIRECTIONS]
    # 角只在自身及相邻两正交邻域都填充时有效，与官方3×3 minimal规则一致。
    for i in [1, 3, 5, 7]:
        active[i] = active[i] and active[(i-1)%8] and active[(i+1)%8]
    return sum(1 << i for i, on in enumerate(active) if on)

def main():
    catalog = json.loads((P / 'official/catalog.json').read_text(encoding='utf-8'))
    sets = {}
    for atlas in catalog['atlases']:
        image = Image.open(P / 'official' / atlas['texture']).convert('RGBA')
        sets[atlas['id']] = {e['mask']: image.crop((e['coord'][0]*128, e['coord'][1]*128,
                                                   (e['coord'][0]+1)*128, (e['coord'][1]+1)*128))
                             for e in atlas['tiles']}
    cases = [
        ('center', '中心与外围', {(x, y) for y in range(4) for x in range(6)}),
        ('long_north', '长直北外边', {(x, y) for y in range(3) for x in range(8)}),
        ('L_corner', 'L形：内外角', {(x, y) for y in range(7) for x in range(7) if x >= 4 or y >= 4}),
        ('hole', '凹洞：四方向', {(x, y) for y in range(7) for x in range(9)
                              if not (3 <= x <= 5 and 2 <= y <= 3)}),
        ('narrow', '单格窄条与端头', {(0, y) for y in range(7)}),
        ('erase', '擦除后收口', {(x, y) for y in range(5) for x in range(8)
                               if not (3 <= x <= 4 and y <= 2)}),
    ]
    observations = []
    for identifier, title, occupied in cases:
        w, h = max(x for x, y in occupied)+1, max(y for x, y in occupied)+1
        # 窄条只有一列；额外留出标签空间，不缩放图块本身。
        panel_w = max(w*128, 384)
        board = Image.new('RGB', (panel_w*2+56, h*128+110), '#182631')
        draw = ImageDraw.Draw(board)
        draw.text((16, 8), title+' | 源图拼接，非GPU渲染 | 每格128px', font=FONT, fill='white')
        chosen = []
        for column, atlas_id in enumerate(['baseline', 'trial']):
            ox, oy = 16+column*(panel_w+24), 62
            draw.text((ox, 34), 'v007 官方排列基线' if column == 0 else '试验：42旧+5新，未通过接口',
                      font=FONT, fill='#edbd79')
            for cell in sorted(occupied, key=lambda c: (c[1], c[0])):
                mask = mask_for(cell, occupied)
                image = sets[atlas_id][mask]
                board.paste(image, (ox+cell[0]*128, oy+cell[1]*128), image)
                if column == 1:
                    chosen.append({'cell': list(cell), 'mask': mask,
                                   'new_sample': mask in [255, 124, 28, 127, 17]})
        draw.text((16, h*128+80), '其他方向、端头等沿用v007；不能以本图证明新47套已完成。',
                  font=FONT, fill='#ffb4a1')
        path = REVIEW / f'floor_{identifier}_cpu_before_after.png'
        board.save(path)
        observations.append({'id': identifier, 'name': title, 'cells': [list(c) for c in sorted(occupied)],
                             'selected_trial_tiles': chosen, 'image': path.name,
                             'render_type': 'CPU_SOURCE_COMPOSITE_128PX'})
    (P / 'review-layouts.json').write_text(json.dumps({'cases': observations}, ensure_ascii=False, indent=2), encoding='utf-8')

    # 标记每一格的真实新旧来源，标签独立于原始atlas纹理。
    atlas = next(a for a in catalog['atlases'] if a['id'] == 'trial')
    image = Image.open(P / 'official' / atlas['texture']).convert('RGBA')
    board = Image.new('RGB', (1552, 704), '#182631')
    draw = ImageDraw.Draw(board)
    draw.text((8, 8), '官方12×4槽位：47mask；仅5格新样，42格沿用v007。空槽不创建Tile。', font=FONT, fill='white')
    for e in atlas['tiles']:
        x, y = e['coord']
        tile = image.crop((x*128, y*128, (x+1)*128, (y+1)*128))
        ox, oy = 8+x*128, 40+y*164
        board.paste(tile, (ox, oy), tile)
        new = e['source']['kind'] == 'v008_generated_sample'
        draw.text((ox, oy+131), f'{e["mask"]} '+('新样' if new else 'v007'), font=FONT,
                  fill='#edbd79' if new else '#a3b9c3')
    board.save(REVIEW / 'floor_official_layout_sources.png')
    print('6 source trials and official per-tile source sheet saved.')

if __name__ == '__main__':
    main()
