"""将已整理的原生像素零件装配为完整 Terrain 图集；不覆盖 v001 手工版。

四邻接位序 N/E/S/W；八邻接位序 N/NE/E/SE/S/SW/W/NW。
面积型采用 47 blob：对角只有在两条相邻边都连接时才有效。
"""
from pathlib import Path
import importlib.util
import hashlib
import json
from PIL import Image, ImageDraw
import ember_autotile_shapes as revised

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'art-source/ember/tilesets-v001/finished-tiles'
OUT = ROOT / 'assets/ember/environment/autotiles_v002'
OUT.mkdir(parents=True, exist_ok=True)
PALETTE = ['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','7B4D35','B77C4B','E2B77A','51C5C2','E5A44B','E65B4A','566B78','203A4B','406B78','ECE9D8']
C = [tuple(bytes.fromhex(s)) + (255,) for s in PALETTE]
EMPTY = (0, 0, 0, 0)

def source(group, name):
    return Image.open(SRC / group / (name + '.png')).convert('RGBA')

def normalize(mask):
    for corner in (1, 3, 5, 7):
        if not (mask & (1 << ((corner - 1) % 8)) and mask & (1 << ((corner + 1) % 8))):
            mask &= ~(1 << corner)
    return mask

BLOBS = sorted({normalize(m) for m in range(256)})
assert len(BLOBS) == 47


# 仅导入无副作用的设施绘制函数；不执行旧批次 main，不改旧图片。
spec = importlib.util.spec_from_file_location('ember_utilities', ROOT / 'art-source/ember/tilesets-v001/tools/finish_utilities.py')
utility = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utility)
strip = source('utilities','pipe_straight_h').crop((0,11,32,21))

def pipe(mask):
    sides = [s for i,s in enumerate('NESW') if mask & (1 << i)]
    names = {5:'straight_v',10:'straight_h',3:'elbow_ne',6:'elbow_se',12:'elbow_sw',9:'elbow_nw',11:'tee_n',7:'tee_e',14:'tee_s',13:'tee_w',15:'cross'}
    if mask in names:
        return source('utilities','pipe_'+names[mask])
    ends={'N':(15.5,-8),'E':(39,15.5),'S':(15.5,39),'W':(-8,15.5)}
    paths=[[(15.5,15.5),ends[s]] for s in sides] or [[(15.5,15),(15.5,16)]]
    im=utility.paint_tube(paths,10,strip)
    utility.arm_clamps(im,tuple(sides))
    utility.junction_details(im)
    return im


catalog={'revision':'v002','visual_status':'REVISED_PENDING_USER_REVIEW','tile_size':32,'bit_order_8':'N NE E SE S SW W NW','bit_order_4':'N E S W','atlases':[]}
for name,mode,masks,make in [('floor','blob',BLOBS,revised.floor),('wall','blob',BLOBS,revised.wall),('water','blob',BLOBS,lambda m:revised.water(m)[0]),('bank','blob',BLOBS,lambda m:revised.water(m)[1]),('pipe','sides',range(16),pipe),('rail','sides',range(16),revised.rail),('bridge','sides',range(16),revised.bridge)]:
    variants=3 if name=='floor' else 1
    atlas=Image.new('RGBA',(256,32*((len(masks)*variants+7)//8)))
    records=[]
    for mask in masks:
        for variant in range(variants):
            im=make(mask,variant) if name=='floor' else make(mask)
            assert set(im.getdata()) <= set(C)|{EMPTY}, name
            index=len(records); x,y=index%8,index//8
            atlas.paste(im,(x*32,y*32))
            records.append({'mask':mask,'variant':variant,'coord':[x,y]})
    filename=name+'_autotile_v002.png'; atlas.save(OUT/filename)
    catalog['atlases'].append({'id':name,'mode':mode,'texture':'res://assets/ember/environment/autotiles_v002/'+filename,'sha256':hashlib.sha256((OUT/filename).read_bytes()).hexdigest(),'tiles':records})
(OUT/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n',encoding='utf-8')
print('Built',sum(len(a['tiles']) for a in catalog['atlases']),'terrain patterns across',len(catalog['atlases']),'atlases')
