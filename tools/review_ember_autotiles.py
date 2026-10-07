"""为 v002 输出可审阅的语义图板，并检查所有兼容接口的 Alpha 截面。"""
from pathlib import Path
import hashlib
import json
import argparse
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--revision',choices=['v002','v003'],default='v002')
revision=parser.parse_args().revision
OUT=ROOT/('assets/ember/environment/autotiles_'+revision)
catalog=json.loads((OUT/'catalog.json').read_text(encoding='utf-8'))
images={}; stats={}; edge_checks=0
for atlas in catalog['atlases']:
    name=atlas['id']; image=Image.open(ROOT/atlas['texture'].removeprefix('res://')).convert('RGBA')
    tiles={}; hashes=set()
    for entry in atlas['tiles']:
        x,y=entry['coord']; tile=image.crop((x*32,y*32,x*32+32,y*32+32))
        tiles[(entry['mask'],entry['variant'])]=tile
        hashes.add(hashlib.sha256(tile.tobytes()).hexdigest())
    images[name]=tiles
    stats[name]={'configurations':len(tiles),'unique_images':len(hashes)}
    # 一个 tile 的右侧共享 E、NE、SE；相邻片共享 W、NW、SW。
    # 下侧共享 S、SE、SW；相邻片共享 N、NE、NW。
    pairs=[((2,1,3),(6,7,5),'h'),((4,3,5),(0,1,7),'v')] if atlas['mode']=='blob' else [((1,),(3,),'h'),((2,),(0,),'v')]
    for aa,bb,direction in pairs:
        for (ma,va),a in tiles.items():
            if not ma & (1<<aa[0]): continue
            for (mb,vb),b in tiles.items():
                if tuple(bool(ma&(1<<i)) for i in aa)!=tuple(bool(mb&(1<<i)) for i in bb): continue
                for p in range(32):
                    pa,pb=((31,p),(0,p)) if direction=='h' else ((p,31),(p,0))
                    assert a.getpixel(pa)[3]==b.getpixel(pb)[3], (name,ma,mb,direction,p)
                edge_checks+=1

# 保留旧管线所有像素，尤其用户认可的四个拐角。
old=ROOT/'assets/ember/environment/autotiles/pipe_autotile_v001.png'
# 比较解码像素，容许不同 PNG 编码器产生等价文件。
assert Image.open(old).convert('RGBA').tobytes()==Image.open(OUT/('pipe_autotile_'+revision+'.png')).convert('RGBA').tobytes()
stats['compatible_alpha_edges_checked']=edge_checks
stats['pipe_pixels_unchanged']=True
(OUT/'pixel_validation.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

font_path=Path('C:/Windows/Fonts/msyh.ttc')
font=ImageFont.truetype(str(font_path),18)
small=ImageFont.truetype(str(font_path),14)
board=Image.new('RGB',(1488,1120),'#182631'); d=ImageDraw.Draw(board)
d.text((24,16),revision+' 结构检查：中心 / 边 / 角 / 窄条 / 端头',font=font,fill='#BECBC4')
d.text((24,46),'每格原生 32×32，以下为 4 倍最近邻显示；管线完整保留。',font=small,fill='#829BA3')
area=[(255,'中心'),(124,'北侧收边'),(28,'西北外角'),(127,'西北凹角'),(17,'南北窄条'),(0,'孤立块'),(85,'四向窄连接'),(1,'向北开放端头')]
line=[(10,'东西直段'),(5,'南北直段'),(3,'东北转角'),(11,'朝北 T 形'),(1,'向北开放端头'),(0,'孤立节点'),(15,'十字节点'),(4,'向南开放端头')]
for row,(name,label) in enumerate([('floor','地板'),('wall','墙体'),('bank','水面 + 渠岸'),('rail','栏杆'),('bridge','栈桥')]):
    top=92+row*196; d.text((24,top),label,font=font,fill='#E2B77A')
    for col,(mask,title) in enumerate(area if name in ('floor','wall','bank') else line):
        x=24+col*182; y=top+28
        tile=images[name][(mask,0)].copy()
        if name=='bank':
            base=images['water'][(mask,0)].copy(); base.alpha_composite(tile); tile=base
        board.paste(tile.resize((128,128),Image.Resampling.NEAREST),(x,y),tile.resize((128,128),Image.Resampling.NEAREST))
        d.text((x,y+133),title,font=small,fill='#BECBC4')
d.text((24,1084),'结构模板已补齐；美术效果仍以实际拼图与用户审阅为准。',font=small,fill='#829BA3')
board.save(OUT/'structure_review.png')
print(json.dumps(stats,ensure_ascii=False))
