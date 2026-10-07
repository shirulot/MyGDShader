"""v004 保真修复：完整构件 + 接缝整理，不再强制 16 色或裁成细碎材质。

128px 纹理对应一个逻辑格；场景通过 TileMapLayer 缩放维持原逻辑尺寸。
所有裁剪、版本和对比输出均独立保存，v003 不覆盖。
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'art-source/ember/autotiles-v004'
OUT=ROOT/'assets/ember/environment/autotiles_v004'
OUT.mkdir(parents=True,exist_ok=True)
MASTER=BATCH/'industrial_tile_master_v004.png'
master=Image.open(MASTER).convert('RGBA')
SIZE=128
crops={}

def crop(name,box,size):
    crops[name]={'source_box':list(box),'output_size':list(size)}
    result=master.crop(box).resize(size,Image.Resampling.LANCZOS)
    # 只清理透明背景上的零星低 Alpha 外晕，完整保留主体 RGB 渐变。
    for y in range(result.height):
        for x in range(result.width):
            p=result.getpixel((x,y))
            result.putpixel((x,y),p[:3]+(255,) if p[3]>=160 else (0,0,0,0))
    return result

floor_frame=crop('floor_whole_island',(1150,73,1320,240),(128,128))
floor_center=crop('floor_whole_panels',(57,80,224,233),(128,128))
wall_frame=crop('wall_whole_block',(1152,273,1318,440),(128,128))
wall_center=crop('wall_whole_top',(57,275,223,330),(128,128))
bank_frame=crop('channel_whole_basin',(1150,473,1319,651),(128,128))
water_center=crop('water_whole_surface',(57,482,221,645),(128,128))
rail_h=crop('rail_whole_span_h',(83,748,196,815),(128,48))
rail_v=crop('rail_whole_span_v',(350,726,381,802),(48,128))
rail_post=crop('rail_whole_post',(1214,741,1274,826),(40,56))
bridge_h=crop('bridge_whole_span_h',(78,935,204,1038),(128,96))
bridge_v=crop('bridge_whole_span_v',(316,912,413,1058),(96,128))
bridge_platform=crop('bridge_whole_platform',(1172,923,1319,1084),(96,96))

def normalize(mask):
    for bit in (1,3,5,7):
        if not(mask&(1<<((bit-1)%8)) and mask&(1<<((bit+1)%8))): mask &= ~(1<<bit)
    return mask

BLOBS=sorted({normalize(mask) for mask in range(256)})

def area(frame,center,mask,wall=False):
    """完整面板保留；外围由母稿整体构件的四边及角组成。

南墙面保留 48px 高的完整立面。边条只沿切向延展，不压扁立面厚度。
"""
    if mask==0: return frame.copy()
    im=center.copy()
    widths=[18,18,88 if wall else 18,18]
    n,e,s,w=widths
    strips=[frame.crop((w,0,128-e,n)).resize((128,n),Image.Resampling.LANCZOS),
            frame.crop((128-e,n,128,128-s)).resize((e,128),Image.Resampling.LANCZOS),
            frame.crop((w,128-s,128-e,128)).resize((128,s),Image.Resampling.LANCZOS),
            frame.crop((0,n,w,128-s)).resize((w,128),Image.Resampling.LANCZOS)]
    positions=[(0,0),(128-e,0),(0,128-s),(0,0)]
    for side in range(4):
        if not mask&(1<<(side*2)):
            im.paste(strips[side],positions[side])
    # 两条关闭边相遇时，直接使用完整母稿角，不叠两条边制造交叉假角。
    for a,b,diagonal,box in [(0,3,7,(0,0,w,n)),(0,1,1,(128-e,0,128,n)),(2,1,3,(128-e,128-s,128,128)),(2,3,5,(0,128-s,w,128))]:
        if not mask&(1<<(a*2)) and not mask&(1<<(b*2)):
            im.paste(frame.crop(box),(box[0],box[1]))
        elif mask&(1<<(a*2)) and mask&(1<<(b*2)) and not mask&(1<<diagonal):
            # 凹角的小缺口与附近两条内侧压边；方向使用相应原稿边条。
            left=b==3; top=a==0; inset=12
            x=0 if left else 128-inset; y=0 if top else 128-inset
            im.paste((0,0,0,0),(x,y,x+inset,y+inset))
            h=strips[a].resize((inset,12),Image.Resampling.LANCZOS)
            v=strips[b].resize((12,inset),Image.Resampling.LANCZOS)
            im.paste(h,(x,inset if top else 128-inset-12))
            im.paste(v,(inset if left else 128-inset-12,y))
    return im

def rails(mask):
    im=Image.new('RGBA',(128,128))
    for bit in range(4):
        if not mask&(1<<bit): continue
        a,b=(0,64) if bit in (0,3) else (64,128)
        if bit in (1,3): im.alpha_composite(rail_h.crop((a,0,b,48)),(a,40))
        else: im.alpha_composite(rail_v.crop((0,a,48,b)),(40,a))
    if mask not in (5,10): im.alpha_composite(rail_post,(44,36))
    # 开放端口使用同一截面，完整母稿的端柱不出现在直段之间。
    for bit in range(4):
        if mask&(1<<bit):
            for p in range(48):
                im.putpixel((127 if bit==1 else 0,p+40),rail_h.getpixel((64,p))) if bit in (1,3) else im.putpixel((p+40,0 if bit==0 else 127),rail_v.getpixel((p,64)))
    return im

def bridges(mask):
    im=Image.new('RGBA',(128,128)); im.alpha_composite(bridge_platform,(16,16))
    if mask==10:
        im=Image.new('RGBA',(128,128)); im.alpha_composite(bridge_h,(0,16)); return im
    if mask==5:
        im=Image.new('RGBA',(128,128)); im.alpha_composite(bridge_v,(16,0)); return im
    # 用完整桥臂覆盖开放方向的平台封边；关闭方向保留原稿端梁。
    for bit in range(4):
        if not mask&(1<<bit): continue
        a,b=(0,64) if bit in (0,3) else (64,128)
        if bit in (1,3): im.alpha_composite(bridge_h.crop((a,0,b,96)),(a,16))
        else: im.alpha_composite(bridge_v.crop((0,a,96,b)),(16,a))
    # 两条桥臂交汇的内区使用完整平台表面，移除相互叠加的横向封梁。
    junction=bridge_platform.crop((14,14,82,82)).resize((96,96),Image.Resampling.LANCZOS)
    for y in range(16,112):
        for x in range(16,112):
            horizontal=bool((mask&2 and x>=64) or (mask&8 and x<64))
            vertical=bool((mask&1 and y<64) or (mask&4 and y>=64))
            if horizontal and vertical: im.putpixel((x,y),junction.getpixel((x-16,y-16)))
    return im

def water(mask,bank=False):
    # 水岸完整造型保留；水体从基底独立分离，避免岸沿随 shader 变形。
    both=area(bank_frame,water_center,mask)
    if not bank:
        surface=water_center.copy(); surface.putalpha(both.getchannel('A')); return surface
    im=both.copy()
    for y in range(128):
        for x in range(128):
            # 母稿水体为青蓝、钢岸接近灰色；仅拆分水体，不改岸体色阶。
            r,g,b,a=im.getpixel((x,y))
            if b>45 and g>r*1.8+8 and b>r*2+8: im.putpixel((x,y),(0,0,0,0))
    if mask==255: im=Image.new('RGBA',(128,128))
    return im

catalog={'revision':'v004','tile_size':128,'logical_tile_size':32,'display_scale':0.25,'visual_status':'FIDELITY_REPAIR_PENDING_USER_REVIEW','bit_order_8':'N NE E SE S SW W NW','bit_order_4':'N E S W','atlases':[]}
old=json.loads((ROOT/'assets/ember/environment/autotiles_v003/catalog.json').read_text())
tiles_by_name={}
for name in ('floor','wall','water','bank','pipe','rail','bridge'):
    blob=name in ('floor','wall','water','bank'); masks=BLOBS if blob else range(16)
    atlas=Image.new('RGBA',(1024,128*((len(masks)+7)//8))); records=[]; tiles={}
    oldpipe=next(a for a in old['atlases'] if a['id']=='pipe')
    pipeimage=Image.open(ROOT/oldpipe['texture'].removeprefix('res://')).convert('RGBA')
    for index,mask in enumerate(masks):
        if name=='floor': im=area(floor_frame,floor_center,mask)
        elif name=='wall': im=area(wall_frame,wall_center,mask,True)
        elif name in ('water','bank'): im=water(mask,name=='bank')
        elif name=='rail': im=rails(mask)
        elif name=='bridge': im=bridges(mask)
        else:
            rec=next(t for t in oldpipe['tiles'] if t['mask']==mask); x,y=rec['coord']
            im=pipeimage.crop((x*32,y*32,x*32+32,y*32+32)).resize((128,128),Image.Resampling.NEAREST)
        coord=[index%8,index//8]; atlas.paste(im,(coord[0]*128,coord[1]*128)); tiles[mask]=im
        records.append({'mask':mask,'variant':0,'coord':coord})
    filename=name+'_autotile_v004.png'; atlas.save(OUT/filename); tiles_by_name[name]=tiles
    catalog['atlases'].append({'id':name,'mode':'blob' if blob else 'sides','texture':'res://assets/ember/environment/autotiles_v004/'+filename,'sha256':hashlib.sha256((OUT/filename).read_bytes()).hexdigest(),'tiles':records})
(OUT/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n',encoding='utf-8')

# 同样显示尺寸比较信息损失，而不是让 128px 大图凭尺寸优势胜出。
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
board=Image.new('RGB',(1000,1070),'#182631'); d=ImageDraw.Draw(board)
d.text((24,16),'保真修复：相同显示大小，比较实际保留的细节',font=font,fill='#BECBC4')
for column,title in enumerate(['v003 旧处理','32px 完整构件','64px 完整构件','128px 完整构件']): d.text((160+column*205,60),title,font=small,fill='#E2B77A')
for row,(name,label,mask) in enumerate([('floor','地板',0),('wall','墙体',0),('bank','渠岸',0),('rail','栏杆',3),('bridge','栈桥',3)]):
    top=102+row*188; d.text((24,top+56),label,font=font,fill='#BECBC4')
    entry=next(a for a in old['atlases'] if a['id']==name); rec=next(t for t in entry['tiles'] if t['mask']==mask and t['variant']==0)
    src=Image.open(ROOT/entry['texture'].removeprefix('res://')).convert('RGBA'); x,y=rec['coord']; previous=src.crop((x*32,y*32,x*32+32,y*32+32))
    candidate=tiles_by_name[name][mask].copy()
    if name=='bank':
        base=tiles_by_name['water'][mask].copy(); base.alpha_composite(candidate); candidate=base
    for col,size in enumerate([0,32,64,128]):
        tile=previous if not size else candidate.resize((size,size),Image.Resampling.LANCZOS)
        tile=tile.resize((160,160),Image.Resampling.NEAREST); board.paste(tile,(160+col*205,top),tile)
board.save(OUT/'fidelity_comparison.png')
record={'method':'WHOLE_COMPONENT_FIDELITY_REPAIR','master':str(MASTER.relative_to(ROOT)),'sha256':hashlib.sha256(MASTER.read_bytes()).hexdigest(),'crops':crops,'texture_tile_size':128,'logical_tile_size':32,'forced_palette':False,'user_visual_approval':False,'limitations':['source sheet is not a uniform pixel grid','corner and edge assembly remains subject to visual review','water-bank color separation needs visual inspection']}
(BATCH/'generation-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('v004 high fidelity atlases and comparison saved')
