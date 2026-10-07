"""导入完整重绘稿，按已有语义格切片，仅统一开放接口的窄边带。

不提取材质重画轮廓，不减色。原始生成稿和未经接口修正的图集均保留，
方便把生图偏差与导入处理分开检查。实际视觉效果另由 Godot 铺刷页审查。
"""
from pathlib import Path
import hashlib
import json
import statistics
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets/ember/environment/autotiles_v005'
ART = ROOT / 'art-source/ember/autotiles-v006'
OUT = ROOT / 'assets/ember/environment/autotiles_v006'
OUT.mkdir(parents=True, exist_ok=True)
S, BAND = 128, 8
# 两轮岸沿重绘均出现跨格阴影，未通过实际铺刷审查，沿用稳定岸沿。
REDRAWN = {'floor', 'wall', 'bridge'}


def edge(side, p, depth=0):
    return [(p, depth), (S-1-depth, p), (p, S-1-depth), (depth, p)][side]


def active(mask, side, blob):
    return bool(mask & (1 << (side*2 if blob else side)))


def key(mask, side, blob):
    corners = [(7, 1), (1, 3), (5, 3), (7, 5)][side]
    return (side % 2,) + tuple(bool(mask & (1 << b)) for b in corners) if blob else (side % 2,)


def representative(values):
    opaque = [p for p in values if p[3] > 127]
    if len(opaque) < len(values)/2 or not opaque:
        return (0, 0, 0, 0)
    return tuple(round(statistics.median(p[c] for p in opaque)) for c in range(3)) + (255,)


def stitch(tiles, blob):
    """同语义接口共用截面，保留距边缘 8px 以外的完整美术。"""
    profiles = {}
    by_mask = {entry['mask']: im for entry, im in tiles}
    for entry, im in tiles:
        for side in range(4):
            if active(entry['mask'], side, blob):
                profiles.setdefault(key(entry['mask'], side, blob), []).append((im, side))
    full = by_mask.get(255)
    corner = representative([full.getpixel(p) for p in [(0,0),(0,S-1),(S-1,0),(S-1,S-1)]]) if full else (0,0,0,0)
    canonical = {}
    for k, members in profiles.items():
        if blob:
            refs = ({(False,False):17,(False,True):31,(True,False):241,(True,True):255} if k[0] == 0 else
                    {(False,False):68,(False,True):124,(True,False):199,(True,True):255})
            ref = by_mask[refs[k[1:]]]
            members = [(ref, k[0]), (ref, k[0]+2)]
        else:
            # 直段决定端口宽度；不能把端头和交叉平台混在一起取平均。
            ref = by_mask[5 if k[0] == 0 else 10]
            members = [(ref, k[0]), (ref, k[0]+2)]
        line = [representative([im.getpixel(edge(side,p)) for im,side in members]) for p in range(S)]
        if blob:
            line[0] = corner if k[1] else (0,0,0,0)
            line[-1] = corner if k[2] else (0,0,0,0)
        canonical[k] = line
    corrected = []
    changed = 0
    for entry, base in tiles:
        im = base.copy()
        for y in range(S):
            for x in range(S):
                constraints = [(depth, canonical[key(entry['mask'],side,blob)][p])
                    for side,depth,p in [(0,y,x),(1,S-1-x,y),(2,S-1-y,x),(3,x,y)]
                    if depth < BAND and active(entry['mask'],side,blob)]
                if not constraints:
                    continue
                depth, target = min(constraints, key=lambda pair: pair[0])
                source = base.getpixel((x,y))
                weight = (BAND-depth)/BAND
                alpha = round(source[3]*(1-weight)+target[3]*weight)
                rgb = tuple(round((source[c]*source[3]*(1-weight)+target[c]*target[3]*weight)/alpha) for c in range(3)) if alpha else (0,0,0)
                value = tuple(max(0,min(255,c)) for c in rgb) + (alpha,)
                changed += value != source
                im.putpixel((x,y),value)
        corrected.append((entry,im))
    return corrected, changed


def validate(tiles, blob):
    checks = bad = 0
    for side in (1,2):
        opposite = (side+2)%4
        for ea,ia in tiles:
            if not active(ea['mask'],side,blob):
                continue
            for eb,ib in tiles:
                if not active(eb['mask'],opposite,blob) or key(ea['mask'],side,blob) != key(eb['mask'],opposite,blob):
                    continue
                checks += 1
                bad += any(ia.getpixel(edge(side,p)) != ib.getpixel(edge(opposite,p)) for p in range(S))
    return {'tested_pairs':checks, 'rgba_mismatch_pairs':bad}


def main():
    catalog = json.loads((SOURCE/'catalog.json').read_text())
    reports = {}
    for a in catalog['atlases']:
        name, blob = a['id'], a['mode'] == 'blob'
        rows = 6 if blob else 2
        redraw = name in REDRAWN
        path = ART/f'{name}_master.png' if redraw else ROOT/a['texture'].removeprefix('res://')
        raw = Image.open(path).convert('RGBA')
        reference = Image.open(ROOT/f'assets/ember/environment/autotiles_v005/{name}_autotile_v005.png').convert('RGBA')
        tiles = []
        normalized = Image.new('RGBA',(8*S,rows*S))
        for entry in a['tiles']:
            x,y = entry['coord']
            # 各格分别缩放，避免在缩整张图集时采样到相邻格。
            box = (round(x*raw.width/8),round(y*raw.height/rows),round((x+1)*raw.width/8),round((y+1)*raw.height/rows))
            tile = raw.crop(box).resize((S,S),Image.Resampling.LANCZOS)
            if name in ('floor', 'wall'):
                # 整图生图的排版边界有数像素漂移，上一行立面会侵入下一格
                # 开放墙顶。仅在开放边剔除 4px 注册误差，再整体归位；闭合
                # 外缘不裁，避免损失外侧倒角。随后仍执行共享截面校准。
                inset = [4 if active(entry['mask'],side,True) else 0 for side in range(4)]
                tile = tile.crop((inset[3],inset[0],S-inset[1],S-inset[2])).resize((S,S),Image.Resampling.LANCZOS)
            if name == 'bridge':
                # 生图多出的留白不是连接端口。用原笔刷的占位包围盒做整块
                # 注册；只整体裁切和缩放，不描摹旧轮廓，不拼接局部肢臂。
                bounds = tile.getchannel('A').point(lambda v: 255 if v > 127 else 0).getbbox()
                target = reference.crop((x*S,y*S,(x+1)*S,(y+1)*S))
                target_bounds = target.getchannel('A').point(lambda v: 255 if v > 127 else 0).getbbox()
                if bounds and target_bounds:
                    left,top,right,bottom = target_bounds
                    registered = Image.new('RGBA',(S,S))
                    registered.paste(tile.crop(bounds).resize((right-left,bottom-top),Image.Resampling.LANCZOS),(left,top))
                    tile = registered
            normalized.paste(tile,(x*S,y*S))
            tiles.append((entry,tile))
        if redraw:
            normalized.save(ART/f'{name}_normalized.png')
            tiles, changed = stitch(tiles,blob)
        else:
            changed = 0
        result = Image.new('RGBA',normalized.size)
        for entry,tile in tiles:
            x,y = entry['coord']
            result.paste(tile,(x*S,y*S))
        filename = f'{name}_autotile_v006.png'
        result.save(OUT/filename)
        a['texture'] = f'res://assets/ember/environment/autotiles_v006/{filename}'
        a['sha256'] = hashlib.sha256((OUT/filename).read_bytes()).hexdigest()
        a['art_source'] = str(path.relative_to(ROOT)).replace('\\','/')
        reports[name] = validate(tiles,blob) | {'redrawn':redraw,'source_size':raw.size,'modified_pixels':changed,'interface_band':BAND if redraw else 0}
        assert reports[name]['rgba_mismatch_pairs'] == 0, (name,reports[name])
    catalog['revision'] = 'v006'
    catalog['visual_status'] = 'REDRAW_CANDIDATE_PENDING_VISUAL_REVIEW'
    (OUT/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
    (OUT/'seam_validation.json').write_text(json.dumps(reports,indent=2)+'\n')
    print(json.dumps(reports))


if __name__ == '__main__':
    main()
