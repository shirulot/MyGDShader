"""把旧 67 个手工笔刷 ID 映射到统一风格的新图，保持旧坐标便于查找。

新增稿只做整块提取、占位注册、图集打包。地形连接构件直接取 v007
Terrain 图集，不再维护另一套低分辨率绘图实现。
"""
from pathlib import Path
import json
import hashlib
from PIL import Image, ImageDraw, ImageFont
from build_ember_autotiles_v006 import stitch

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT/'art-source/ember/autotiles-v007'
AUTO = ROOT/'assets/ember/environment/autotiles_v007'
OUT = ROOT/'assets/ember/environment/tilesets_v007'
SIZE = 128


def fit_sprite(sprite, width, height, square=False):
    box = sprite.getchannel('A').point(lambda a: 255 if a > 80 else 0).getbbox()
    assert box, 'Empty sprite'
    sprite = sprite.crop(box)
    if square:
        sprite = sprite.resize((width,height),Image.Resampling.LANCZOS)
    else:
        sprite.thumbnail((width,height),Image.Resampling.LANCZOS)
    tile = Image.new('RGBA',(SIZE,SIZE))
    tile.paste(sprite,((SIZE-sprite.width)//2,(SIZE-sprite.height)//2))
    return tile


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    auto = json.loads((AUTO/'catalog.json').read_text(encoding='utf-8'))
    source = json.loads((ROOT/'assets/ember/environment/tilesets/ember_tiles_catalog_v002.json').read_text(encoding='utf-8'))
    atlas_images = {a['id']:Image.open(ROOT/a['texture'].removeprefix('res://')).convert('RGBA') for a in auto['atlases']}
    masks = {a['id']:{t['mask']:t['coord'] for t in a['tiles']} for a in auto['atlases']}

    def tile_for(name,mask):
        x,y = masks[name][mask]
        return atlas_images[name].crop((x*SIZE,y*SIZE,(x+1)*SIZE,(y+1)*SIZE))

    details = Image.open(ART/'details_master.png').convert('RGBA')
    # 母稿实际行间空隙经查看确认；不能把非均分展示页强行等分而截断检修口。
    row_edges = [0,round(details.height*.393),round(details.height*.69),details.height]
    ids = ['hatch_closed','hatch_open','pipe_valve','decal_crack','decal_rust','decal_bolts','decal_oil','decal_cable_loop','decal_debris']
    sprites = {}
    extraction = []
    for i,name in enumerate(ids):
        x,y = i%3,i//3
        box = (round(x*details.width/3),row_edges[y],round((x+1)*details.width/3),row_edges[y+1])
        extent = 112 if name.startswith('hatch') else 68 if name == 'decal_bolts' else 88 if name == 'pipe_valve' else 104
        sprites[name] = fit_sprite(details.crop(box),extent,extent,name.startswith('hatch'))
        extraction.append({'id':name,'source_box':box,'target_extent':extent})
    # 阀门笔刷仍可接在水平管线上，不能因新图是独立手轮而丢掉两侧端口。
    valve_body = tile_for('pipe',10)
    valve_body.alpha_composite(sprites['pipe_valve'])
    sprites['pipe_valve'] = valve_body
    floors = Image.open(ART/'floors_master.png').convert('RGBA')
    floor_tiles = []
    for i,name in enumerate(['floor_worn','floor_grate','floor_wet']):
        image = floors.crop((round(i*floors.width/3),0,round((i+1)*floors.width/3),floors.height)).resize((SIZE,SIZE),Image.Resampling.LANCZOS)
        floor_tiles.append(({'id':name,'mask':255},image))
    # 清洁地板作为唯一边缘基准，保证四种填充可以混刷，而不靠加黑框遮缝。
    floor_tiles.append(({'id':'floor_clean','mask':255},tile_for('floor',255)))
    for entry,image in stitch(floor_tiles,True)[0]:
        sprites[entry['id']] = image

    blob_masks = {'center':255,'edge_n':124,'edge_e':241,'edge_s':199,'edge_w':31,
                  'outer_ne':112,'outer_se':193,'outer_sw':7,'outer_nw':28,
                  'inner_ne':253,'inner_se':247,'inner_sw':223,'inner_nw':127}
    path_masks = {'straight_h':10,'straight_v':5,'corner_ne':3,'corner_se':6,'corner_sw':12,'corner_nw':9,
                  'elbow_ne':3,'elbow_se':6,'elbow_sw':12,'elbow_nw':9,
                  'tee_n':11,'tee_e':7,'tee_s':14,'tee_w':13,'cross':15,'end_h':8,'end_v':1}
    bridge_masks = {'deck_h':10,'deck_v':5,'end_cap':8,'end_cap_w':2,'end_cap_n':4,'end_cap_s':1}
    for atlas in source['atlases']:
        for entry in atlas['tiles']:
            name = entry['id']
            if name in sprites:
                continue
            family,suffix = name.split('_',1)
            if family in ('wall','channel'):
                sprites[name] = tile_for('wall' if family == 'wall' else 'bank',blob_masks[suffix])
            elif family in ('pipe','rail'):
                sprites[name] = tile_for(family,path_masks[suffix])
            elif family == 'bridge':
                if suffix in bridge_masks:
                    sprites[name] = tile_for('bridge',bridge_masks[suffix])
                else:
                    # 单独边梁沿用整块桥面中已画好的边梁；保持其原图坐标，
                    # 不旋转光照、不另外用线条画一个程序版。
                    horizontal = suffix.startswith('edge_h')
                    deck = tile_for('bridge',10 if horizontal else 5)
                    box = deck.getchannel('A').point(lambda a:255 if a>127 else 0).getbbox()
                    left,top,right,bottom = box
                    if horizontal:
                        box = (0,bottom-12,SIZE,bottom) if suffix.endswith('_s') else (0,top,SIZE,top+12)
                    else:
                        box = (right-12,0,right,SIZE) if suffix.endswith('_e') else (left,0,left+12,SIZE)
                    image = Image.new('RGBA',(SIZE,SIZE)); image.paste(deck.crop(box),box[:2]); sprites[name] = image
            else:
                raise ValueError(name)

    catalog = {'revision':'v007','tile_size':SIZE,'logical_tile_size':32,'display_scale':.25,
               'status':'STYLE_UNIFIED_PENDING_USER_REVIEW','atlases':[]}
    coverage = []
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
    review = Image.new('RGBA',(1280,9*160+64),'#182631')
    draw = ImageDraw.Draw(review)
    draw.text((20,14),'全部 67 个旧笔刷 ID → v007 统一风格（128px 原图预览）',font=font,fill='white')
    index = 0
    for old in source['atlases']:
        rows = 1 + max(t['coord'][1] for t in old['tiles'])
        image = Image.new('RGBA',(8*SIZE,rows*SIZE))
        entry_list = []
        for entry in old['tiles']:
            name = entry['id']; x,y = entry['coord']; tile = sprites[name]
            image.paste(tile,(x*SIZE,y*SIZE))
            entry_list.append({'id':name,'name':entry['name'],'category':entry['category'],'coord':[x,y],
                               'usage':'manual_brush','status':'STYLE_UNIFIED_PENDING_USER_REVIEW'})
            coverage.append({'old_id':name,'old_atlas':old['texture'],'new_atlas':f'{old["id"]}_v007.png','coord':[x,y]})
            px,py = 16+(index%8)*158,56+(index//8)*160
            # 透明贴花叠加新地板，才能看清实际使用效果；atlas 本身保持透明。
            if name.startswith('decal') or name.startswith('hatch'):
                review.alpha_composite(sprites['floor_clean'],(px,py))
            review.alpha_composite(tile,(px,py))
            draw.text((px,py+132),name,font=font,fill='#bccbd4')
            index += 1
        filename = f'{old["id"]}_v007.png'; image.save(OUT/filename)
        catalog['atlases'].append({'id':old['id'],'source_id':old['source_id'],'texture':f'res://assets/ember/environment/tilesets_v007/{filename}',
                                  'sha256':hashlib.sha256((OUT/filename).read_bytes()).hexdigest(),'tiles':entry_list})
    assert index == 67 and len(sprites) == 67
    # 所有地板变体两两比较 N/S、E/W，检查实际 RGBA。
    floor_bad = 0
    fills = [sprites[n] for n in ['floor_clean','floor_worn','floor_grate','floor_wet']]
    for a in fills:
        for b in fills:
            floor_bad += any(a.getpixel((SIZE-1,p)) != b.getpixel((0,p)) for p in range(SIZE))
            floor_bad += any(a.getpixel((p,SIZE-1)) != b.getpixel((p,0)) for p in range(SIZE))
    assert floor_bad == 0
    (OUT/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'migration.json').write_text(json.dumps(coverage,indent=2)+'\n',encoding='utf-8')
    (OUT/'validation.json').write_text(json.dumps({'covered_old_ids':index,'floor_adjacency_pairs':32,'floor_mismatches':floor_bad},indent=2)+'\n',encoding='utf-8')
    (ART/'detail-extraction.json').write_text(json.dumps(extraction,indent=2)+'\n',encoding='utf-8')
    review.save(OUT/'all_brushes_review.png')
    print(f'Built {index} brushes, floor adjacency mismatches: {floor_bad}')


if __name__ == '__main__':
    main()
