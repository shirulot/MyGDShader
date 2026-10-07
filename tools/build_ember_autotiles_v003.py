"""以 v003 美术母稿整理原生图集，v002 只提供已验证的几何接口。

不把高分辨率母稿直接当作合格图集。这里记录每个采样框，并在原生
网格修正 Alpha、色板、方向光与接口。母稿及 v002 文件均不覆盖。
"""
from pathlib import Path
from functools import lru_cache
import hashlib
import json
from PIL import Image, ImageDraw, ImageFilter
import ember_autotile_shapes as geometry

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'art-source/ember/autotiles-v003'
OUT=ROOT/'assets/ember/environment/autotiles_v003'
OUT.mkdir(parents=True,exist_ok=True)
MASTER=BATCH/'industrial_tile_master_v003.png'
master=Image.open(MASTER).convert('RGBA')
C=geometry.C; EMPTY=geometry.EMPTY
samples={}

@lru_cache(maxsize=65536)
def nearest(rgb, indices):
    return min((C[i] for i in indices),key=lambda c:sum((c[j]-rgb[j])**2 for j in range(3)))

def sample(name,box,size,indices=(0,1,2,3,4,5,6,7,8,12)):
    """采样有效美术区域；剔除生成杂色，保留母稿接缝、铆钉、格栅。"""
    patch=master.crop(box).resize(size,Image.Resampling.BOX)
    # 母稿非原生像素，低频面材质先去颗粒；格栅与杆件不做此处理。
    if name.startswith('floor_') or name in ('wall_cap','bridge_junction'):
        patch=patch.filter(ImageFilter.MedianFilter(3))
    result=Image.new('RGBA',size)
    for y in range(size[1]):
        for x in range(size[0]):
            p=patch.getpixel((x,y))
            result.putpixel((x,y),nearest(p[:3],indices) if p[3]>=180 else EMPTY)
    samples[name]={'box':list(box),'native_size':list(size),'palette_indices':list(indices),'resampling':'BOX then registered-palette quantization','median_filter':3 if name.startswith('floor_') or name in ('wall_cap','bridge_junction') else 0}
    directory=BATCH/'samples'; directory.mkdir(exist_ok=True)
    result.save(directory/(name+'.png'))
    return result

floor_patches=[sample('floor_center',(58,79,224,233),(32,32)),sample('floor_edge_interior',(281,102,447,230),(32,32)),sample('floor_island_interior',(1180,106,1286,203),(32,32))]
roof=sample('wall_cap',(65,282,218,319),(32,8),(2,3,4,5,12))
face=sample('wall_front',(286,348,437,424),(32,8))
coping=sample('channel_coping',(281,481,446,529),(32,8))
water_sample=sample('water_base',(74,525,207,633),(32,32),(13,14))
rail_h=sample('rail_horizontal',(84,748,195,807),(32,12))
rail_v=sample('rail_vertical',(354,724,381,799),(12,32))
post=sample('rail_post',(1222,741,1262,802),(10,14))
deck_h=sample('bridge_horizontal_grate',(75,957,205,1008),(32,18))
deck_v=sample('bridge_vertical_grate',(348,910,394,1047),(18,32))
platform=sample('bridge_junction',(525,948,563,992),(12,12))

def normalize(mask):
    for bit in (1,3,5,7):
        if not (mask&(1<<((bit-1)%8)) and mask&(1<<((bit+1)%8))): mask &= ~(1<<bit)
    return mask

BLOBS=sorted({normalize(m) for m in range(256)})
assert len(BLOBS)==47

def opaque(pixel,fallback=3):
    return pixel if pixel[3] else C[fallback]

def area(name,mask,variant=0):
    field=geometry.boundary(mask)
    shape=geometry.floor(mask) if name=='floor' else geometry.wall(mask) if name=='wall' else geometry.water(mask)[0]
    im=Image.new('RGBA',(32,32))
    for y in range(32):
        for x in range(32):
            if not shape.getpixel((x,y))[3]: continue
            distance,dx,dy=field[y][x]
            if name=='floor':
                color=opaque(floor_patches[variant].getpixel((x,y)))
                # 开放边保留一致钢材截面；采样接缝不越过端口契约。
                if x in (0,31) or y in (0,31): color=C[3]
                if distance<=6: color=shape.getpixel((x,y))
            elif name=='wall':
                color=opaque(roof.getpixel((x,y%8)))
                if distance<=3: color=C[0]
                elif dy>0 and distance<=11: color=opaque(face.getpixel((x,min(7,11-distance))),2)
                elif dx>0 and distance<=7: color=C[1 if distance<5 else 2]
                elif dx+dy<0 and distance<=5: color=C[5 if distance==4 else 4]
                # 母稿墙顶不重复烘焙正面；图块接口统一无厚封框。
                elif x in (0,31) or y in (0,31): color=C[3]
            elif name=='water':
                # 母稿水域包含不合要求的波纹：仅取低频水色，不继承动态波形。
                color=water_sample.getpixel((16,16))
                if not color[3]: color=C[13]
            else:
                if distance>11: continue
                along=x if dy else y
                color=opaque(coping.getpixel((along,min(7,max(0,distance-4)))))
                if distance==3 or distance==10: color=C[0]
                elif distance==4: color=C[4 if dx+dy<0 else 1]
                elif distance==9: color=C[4]
                elif distance==11: color=C[14]
            im.putpixel((x,y),color)
    return im

def rail(mask):
    im=Image.new('RGBA',(32,32))
    for bit in range(4):
        if not mask&(1<<bit): continue
        if bit in (1,3):
            a,b=(16,32) if bit==1 else (0,16)
            im.alpha_composite(rail_h.crop((a,0,b,12)),(a,10))
        else:
            a,b=(0,16) if bit==0 else (16,32)
            im.alpha_composite(rail_v.crop((0,a,12,b)),(10,a))
    if mask not in (5,10): im.alpha_composite(post,(11,9))
    # 统一所有开放端口为母稿截面的同一列/行，端口连续不能靠猜测。
    for bit in range(4):
        if not mask&(1<<bit): continue
        for p in range(12):
            if bit in (1,3): im.putpixel((31 if bit==1 else 0,p+10),rail_h.getpixel((16,p)))
            else: im.putpixel((p+10,0 if bit==0 else 31),rail_v.getpixel((p,16)))
    return im

def bridge(mask):
    # 几何只约束 24px 路幅与封闭边；桥板与节点内部实际来自母稿。
    im=geometry.bridge(mask)
    for y in range(32):
        for x in range(32):
            if not im.getpixel((x,y))[3]: continue
            vertical=mask in (1,4,5) or (mask not in (2,8,10) and (y<10 or y>21))
            # 只替换通行内区，原生校正的外梁保持方向光照和接口。
            inner=(7<=x<=24 if vertical else 7<=y<=24)
            if inner:
                color=deck_v.getpixel((x-7,y)) if vertical else deck_h.getpixel((x,y-7))
                if 10<=x<=21 and 10<=y<=21 and mask not in (5,10): color=platform.getpixel((x-10,y-10))
                # 任何靠近封闭边的部分都保留包边，不能用母稿纹理盖住封口。
                near_closed=(not mask&1 and y<8) or (not mask&2 and x>23) or (not mask&4 and y>23) or (not mask&8 and x<8)
                if not near_closed: im.putpixel((x,y),opaque(color))
    return im

catalog={'revision':'v003','visual_status':'AI_MASTER_NATIVE_FINISHED_PENDING_USER_REVIEW','tile_size':32,'bit_order_8':'N NE E SE S SW W NW','bit_order_4':'N E S W','atlases':[]}
old=json.loads((ROOT/'assets/ember/environment/autotiles_v002/catalog.json').read_text())
for name in ('floor','wall','water','bank','pipe','rail','bridge'):
    blob=name in ('floor','wall','water','bank'); masks=BLOBS if blob else range(16)
    variants=3 if name=='floor' else 1
    atlas=Image.new('RGBA',(256,32*((len(masks)*variants+7)//8))); records=[]
    if name=='pipe':
        source=next(a for a in old['atlases'] if a['id']=='pipe')
        atlas=Image.open(ROOT/source['texture'].removeprefix('res://')).convert('RGBA')
        records=source['tiles']
    else:
        for mask in masks:
            for variant in range(variants):
                tile=area(name,mask,variant) if blob else rail(mask) if name=='rail' else bridge(mask)
                assert set(tile.getdata())<=set(C)|{EMPTY},name
                index=len(records); coord=[index%8,index//8]
                atlas.paste(tile,(coord[0]*32,coord[1]*32))
                records.append({'mask':mask,'variant':variant,'coord':coord})
    filename=name+'_autotile_v003.png'; atlas.save(OUT/filename)
    catalog['atlases'].append({'id':name,'mode':'blob' if blob else 'sides','texture':'res://assets/ember/environment/autotiles_v003/'+filename,'sha256':hashlib.sha256((OUT/filename).read_bytes()).hexdigest(),'tiles':records})
(OUT/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n',encoding='utf-8')
record={'method':'AI_MASTER_CROPS_WITH_NATIVE_PIXEL_INTERFACE_FINISH','tool':'image_gen.imagegen','master':str(MASTER.relative_to(ROOT)),'master_sha256':hashlib.sha256(MASTER.read_bytes()).hexdigest(),'prompt':'prompt.txt','samples':samples,'corrections':['native palette quantization and binary alpha','mother sheet not uniform grid; explicit crop rectangles','wall perspective discarded; cap and fascia sampled separately','water wave details removed; static base retained','32px topology and port finishing; no rotation of directional shading'],'pipe':'v002 pixels preserved','user_visual_approval':False}
(BATCH/'generation-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('v003:',sum(len(a['tiles']) for a in catalog['atlases']),'tiles; AI master +',len(samples),'registered art crops')
