"""将其他旧 tile 统一到高保真金属风格，保留 v006 已修复的三类图集。"""
from pathlib import Path
import hashlib
import json
from PIL import Image
from build_ember_autotiles_v006 import stitch, validate, active

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT/'art-source/ember/autotiles-v007'
OUT = ROOT/'assets/ember/environment/autotiles_v007'
SOURCE = ROOT/'assets/ember/environment/autotiles_v006'
SIZE = 128


def solid_bounds(image):
    """只用主要不透明像素求包围盒；保留输出图本身的平滑 Alpha。"""
    return image.getchannel('A').point(lambda a: 255 if a > 127 else 0).getbbox()


def register_whole_tile(tile, reference):
    """只调整完整构件占位，不以旧像素轮廓当遮罩。"""
    source_box, target_box = solid_bounds(tile), solid_bounds(reference)
    if not source_box or not target_box:
        return tile
    left,top,right,bottom = target_box
    result = Image.new('RGBA',(SIZE,SIZE))
    result.paste(tile.crop(source_box).resize((right-left,bottom-top),Image.Resampling.LANCZOS),(left,top))
    return result


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    catalog = json.loads((SOURCE/'catalog.json').read_text(encoding='utf-8'))
    reports = {}
    for atlas in catalog['atlases']:
        name, blob = atlas['id'], atlas['mode'] == 'blob'
        reference = Image.open(ROOT/atlas['texture'].removeprefix('res://')).convert('RGBA')
        redraw = name in ('pipe','rail','bank')
        raw_path = ART/f'{name}_master.png' if redraw else ROOT/atlas['texture'].removeprefix('res://')
        raw = Image.open(raw_path).convert('RGBA')
        rows = 6 if blob else 2
        tiles = []
        for entry in atlas['tiles']:
            x,y = entry['coord']
            if not redraw:
                tile = reference.crop((x*SIZE,y*SIZE,(x+1)*SIZE,(y+1)*SIZE))
            else:
                box = (round(x*raw.width/8),round(y*raw.height/rows),round((x+1)*raw.width/8),round((y+1)*raw.height/rows))
                tile = raw.crop(box).resize((SIZE,SIZE),Image.Resampling.LANCZOS)
                if not blob:
                    # 展示稿闭合端外侧有时混入邻格一两列像素，不能把它们
                    # 算进整块包围盒，否则圆角/柱头会被横向压偏。
                    guard = 3
                    for side in range(4):
                        if active(entry['mask'],side,False):
                            continue
                        strip = [(0,0,SIZE,guard),(SIZE-guard,0,SIZE,SIZE),
                                 (0,SIZE-guard,SIZE,SIZE),(0,0,guard,SIZE)][side]
                        tile.paste((0,0,0,0),strip)
                    tile = register_whole_tile(tile,reference.crop((x*SIZE,y*SIZE,(x+1)*SIZE,(y+1)*SIZE)))
                else:
                    # 岸沿稿上一行的压顶阴影越过了展示格。开放边的注册保护
                    # 区去掉这部分溢出；闭合边和画好的圆角仍使用原美术。
                    original_tile = tile.copy()
                    inset = [24 if active(entry['mask'],side,True) else 0 for side in range(4)]
                    tile = tile.crop((inset[3],inset[0],SIZE-inset[1],SIZE-inset[2])).resize((SIZE,SIZE),Image.Resampling.LANCZOS)
                    # 凹角是真正要保留的绘制内容，不是上一格的串边。还原同格
                    # 原画中的完整角部，不用程序画方角或套旧轮廓遮罩。
                    corners = [(7,0,3,(0,0,32,32)),(1,0,1,(96,0,128,32)),
                               (3,1,2,(96,96,128,128)),(5,2,3,(0,96,32,128))]
                    for diagonal,a,b,corner_box in corners:
                        mask = entry['mask']
                        if active(mask,a,True) and active(mask,b,True) and not mask & (1 << diagonal):
                            tile.paste(original_tile.crop(corner_box),corner_box[:2])
            if name == 'floor' and entry['mask'] == 255:
                # 全内区不能带凹角：使用单独生成、无孔洞的完整填充图。
                tile = Image.open(ART/'clean_floor_master.png').convert('RGBA').resize((SIZE,SIZE),Image.Resampling.LANCZOS)
            tiles.append((entry,tile))
        normalized = Image.new('RGBA',reference.size)
        for entry,tile in tiles:
            x,y = entry['coord']; normalized.paste(tile,(x*SIZE,y*SIZE))
        if redraw or name == 'floor':
            normalized.save(ART/f'{name}_normalized.png')
            tiles,changed = stitch(tiles,blob)
        else:
            changed = 0
        image = Image.new('RGBA',reference.size)
        for entry,tile in tiles:
            x,y = entry['coord']; image.paste(tile,(x*SIZE,y*SIZE))
        filename = f'{name}_autotile_v007.png'
        image.save(OUT/filename)
        atlas['texture'] = f'res://assets/ember/environment/autotiles_v007/{filename}'
        atlas['sha256'] = hashlib.sha256((OUT/filename).read_bytes()).hexdigest()
        atlas['art_source'] = raw_path.relative_to(ROOT).as_posix()
        if name == 'floor':
            atlas['center_art_source'] = (ART/'clean_floor_master.png').relative_to(ROOT).as_posix()
        reports[name] = validate(tiles,blob) | {'redrawn_this_batch':redraw,'modified_interface_pixels':changed,'source_size':raw.size}
        assert reports[name]['rgba_mismatch_pairs'] == 0, (name,reports[name])
    catalog['revision'] = 'v007'
    catalog['visual_status'] = 'STYLE_UNIFICATION_CANDIDATE_PENDING_USER_REVIEW'
    (OUT/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n',encoding='utf-8')
    (OUT/'seam_validation.json').write_text(json.dumps(reports,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(reports))


if __name__ == '__main__':
    main()
