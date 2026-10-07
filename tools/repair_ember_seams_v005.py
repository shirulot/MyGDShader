"""只修复开放接口窄边带；不重建角色/瓦片轮廓，不减色，不强加像素角。

按相同共享边/角语义建立唯一截面，相邻图块采用同一截面并在 6px
边带内过渡。原始 v004 不修改，记录修改量及所有接口对的实际 RGBA。
"""
from pathlib import Path
import json
import hashlib
import statistics
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/ember/environment/autotiles_v004'
OUT=ROOT/'assets/ember/environment/autotiles_v005'
OUT.mkdir(parents=True,exist_ok=True)
catalog=json.loads((SOURCE/'catalog.json').read_text()); S=catalog['tile_size']; BAND=8

def edge(im,side,p,depth=0):
    return [(p,depth),(S-1-depth,p),(p,S-1-depth),(depth,p)][side]

def key(mask,side,blob):
    # N/S 接口按左→右；E/W 接口按上→下。共享角必须语义一致。
    corners=[(7,1),(1,3),(5,3),(7,5)][side]
    return (side%2,)+tuple(bool(mask&(1<<b)) for b in corners) if blob else (side%2,)

def active(mask,side,blob): return bool(mask&(1<<(side*2 if blob else side)))

def representative(values):
    opaque=[p for p in values if p[3]>127]
    if len(opaque)<len(values)/2: return (0,0,0,0)
    return tuple(round(statistics.median(p[c] for p in opaque)) for c in range(3))+(255,)

results={}
for a in catalog['atlases']:
    original=Image.open(ROOT/a['texture'].removeprefix('res://')).convert('RGBA')
    blob=a['mode']=='blob'; tiles=[]
    for entry in a['tiles']:
        x,y=entry['coord']; tiles.append((entry,original.crop((x*S,y*S,(x+1)*S,(y+1)*S))))
    # 母稿的水域和墙顶是独立示例，外框误被当作内部纹理重复。
    # 仅为这两类提取无框内部；墙面的立面/外缘通过精确像素归属保留。
    clean_center=None; old_center=None
    if a['id'] in ('water','wall'):
        old_center=next(im for entry,im in tiles if entry['mask']==255)
        interior_box=(32,40,S-24,S-24) if a['id']=='water' else (18,18,S-18,S-24)
        clean_center=old_center.crop(interior_box).resize((S,S),Image.Resampling.LANCZOS)
        cleaned=[]
        for entry,im in tiles:
            im=im.copy()
            for y in range(S):
                for x in range(S):
                    pixel=im.getpixel((x,y))
                    if a['id']=='water' or pixel==old_center.getpixel((x,y)):
                        im.putpixel((x,y),clean_center.getpixel((x,y))[:3]+(pixel[3],))
            cleaned.append((entry,im))
        tiles=cleaned
    if a['id']=='bank':
        # v004 通过颜色分离水岸，低亮度水纹未被识别而残留在岸沿层。
        # 使用原始水面逐像素归属剔除，不能只靠颜色阈值猜测材质。
        water_atlas=next(v for v in catalog['atlases'] if v['id']=='water')
        # 前面的 water 条目已改为 v005 路径；此处必须读取原始 v004。
        source_catalog=json.loads((SOURCE/'catalog.json').read_text())
        water_atlas=next(v for v in source_catalog['atlases'] if v['id']=='water')
        water_image=Image.open(ROOT/water_atlas['texture'].removeprefix('res://')).convert('RGBA')
        water_entry=next(v for v in water_atlas['tiles'] if v['mask']==255)
        wx,wy=water_entry['coord']; original_water=water_image.crop((wx*S,wy*S,(wx+1)*S,(wy+1)*S))
        cleaned=[]
        for entry,im in tiles:
            im=im.copy()
            for y in range(S):
                for x in range(S):
                    if im.getpixel((x,y))[:3]==original_water.getpixel((x,y))[:3]: im.putpixel((x,y),(0,0,0,0))
            cleaned.append((entry,im))
        tiles=cleaned
    profiles={}
    for entry,im in tiles:
        for side in range(4):
            if active(entry['mask'],side,blob): profiles.setdefault(key(entry['mask'],side,blob),[]).append((im,side))
    # 完全填满的面积交汇点使用各接口相同颜色；岸沿全内区透明。
    full=next((im for entry,im in tiles if entry['mask']==255),None)
    corner_color=representative([full.getpixel((x,y)) for x,y in [(0,0),(0,S-1),(S-1,0),(S-1,S-1)]]) if full else (0,0,0,0)
    canonical={}
    for k,members in profiles.items():
        # 优先使用无转角歧义的完整中心/直边/窄条作为共享截面。
        # 不能把形态不同的内角、外边混在一起平均成带缺口的边梁。
        if blob:
            reference_masks=({(False,False):17,(False,True):31,(True,False):241,(True,True):255} if k[0]==0 else {(False,False):68,(False,True):124,(True,False):199,(True,True):255})
            reference=next(im for entry,im in tiles if entry['mask']==reference_masks[k[1:]])
            members=[(reference,0),(reference,2)] if k[0]==0 else [(reference,1),(reference,3)]
        line=[representative([im.getpixel(edge(im,side,p)) for im,side in members]) for p in range(S)]
        if blob:
            line[0]=corner_color if k[1] else (0,0,0,0)
            line[-1]=corner_color if k[2] else (0,0,0,0)
        canonical[k]=line
    atlas=original.copy(); corrected=[]; changed=0
    for entry,base in tiles:
        im=base.copy(); mask=entry['mask']
        if a['id']!='pipe':
            for y in range(S):
                for x in range(S):
                    constraints=[]
                    for side,depth,p in [(0,y,x),(1,S-1-x,y),(2,S-1-y,x),(3,x,y)]:
                        if depth<BAND and active(mask,side,blob): constraints.append((depth,canonical[key(mask,side,blob)][p]))
                    if not constraints: continue
                    # 真正接缝优先；角点受两个方向约束时使用统一端点。
                    depth,target=min(constraints,key=lambda pair:pair[0])
                    source=base.getpixel((x,y)); weight=(BAND-depth)/BAND
                    alpha=round(source[3]*(1-weight)+target[3]*weight)
                    rgb=tuple(round((source[c]*source[3]*(1-weight)+target[c]*target[3]*weight)/alpha) for c in range(3)) if alpha else (0,0,0)
                    value=tuple(max(0,min(255,c)) for c in rgb)+(alpha,)
                    if value!=source: changed+=1
                    im.putpixel((x,y),value)
        x,y=entry['coord']; atlas.paste(im,(x*S,y*S)); corrected.append((entry,im))
    # 穷举所有兼容接口，RGB 与 Alpha 必须同时完全匹配。
    checks=bad=0
    for side in (1,2):
        opposite=(side+2)%4
        for ea,ia in corrected:
            if not active(ea['mask'],side,blob): continue
            for eb,ib in corrected:
                if not active(eb['mask'],opposite,blob) or key(ea['mask'],side,blob)!=key(eb['mask'],opposite,blob): continue
                checks+=1
                mismatch=any(ia.getpixel(edge(ia,side,p))!=ib.getpixel(edge(ib,opposite,p)) for p in range(S))
                # 原管线由用户认可，不为消除其允许的轻微色差而修改。
                bad+=mismatch
    filename=a['id']+'_autotile_v005.png'; atlas.save(OUT/filename)
    a['texture']='res://assets/ember/environment/autotiles_v005/'+filename
    a['sha256']=hashlib.sha256((OUT/filename).read_bytes()).hexdigest()
    results[a['id']]={'tested_pairs':checks,'rgba_mismatch_pairs':bad,'modified_pixels':changed,'band_width':BAND,'interior_unchanged':clean_center is None and a['id']!='bank','center_frame_removed':clean_center is not None,'water_residue_removed':a['id']=='bank'}
    assert bad==0 or a['id']=='pipe',(a['id'],bad)
catalog['revision']='v005'; catalog['visual_status']='SEAM_REPAIR_PENDING_USER_REVIEW'
(OUT/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
(OUT/'seam_validation.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results))
