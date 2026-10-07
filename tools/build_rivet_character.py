"""新履带检修机器人：按完整角色裁剪、统一缩放和地面锚点，不减色重绘。

剔除生成母稿中朝下第四列的左右工具互换帧，不能为凑四帧掩盖错帧。
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'art-source/ember/rivet-v001'
OUT=ROOT/'assets/ember/characters/rivet'
OUT.mkdir(parents=True,exist_ok=True)
MASTER=BATCH/'rivet_master_v001.png'; master=Image.open(MASTER).convert('RGBA')
CANVAS=(128,160); ANCHOR=(64,136)
directions=['down','left','right','up']; items=[]
for row,direction in enumerate(directions):
    for column in range(5):
        box=(round(column*master.width/5),round(row*master.height/4),round((column+1)*master.width/5),round((row+1)*master.height/4))
        cell=master.crop(box)
        alpha=cell.getchannel('A').point(lambda a:255 if a>=100 else 0)
        bounds=alpha.getbbox(); assert bounds,(direction,column)
        cell.putalpha(alpha)
        # 背景 RGB 全部归零，避免线性过滤出现彩色毛边。
        cleared=Image.new('RGBA',cell.size); cleared.paste(cell,(0,0),alpha)
        items.append({'direction':direction,'column':column,'source_box':list(box),'bounds':list(bounds),'image':cleared.crop(bounds)})
scale=min(112/max(t['image'].width for t in items),120/max(t['image'].height for t in items))
atlas=Image.new('RGBA',(5*128,4*160)); records=[]; frames={}
for item in items:
    direction,column=item['direction'],item['column']
    original=item.pop('image')
    image=original.resize((round(original.width*scale),round(original.height*scale)),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',CANVAS)
    position=(ANCHOR[0]-image.width//2,ANCHOR[1]-image.height)
    canvas.alpha_composite(image,position)
    accepted=not(direction=='down' and column==3)
    frame_id=f'{direction}_{column:02d}'
    canvas.save(OUT/(frame_id+'.png')); frames[frame_id]=canvas
    row=directions.index(direction); atlas.paste(canvas,(column*128,row*160))
    records.append({**item,'id':frame_id,'anchor':list(ANCHOR),'coord':[column,row],'accepted':accepted,'rejection':None if accepted else '左右工具互换；排除出移动动画'})
atlas.save(OUT/'rivet_atlas_v001.png')
animations={}
for direction in directions:
    animations['idle_'+direction]={'fps':1,'frames':[direction+'_00']}
    animations['walk_'+direction]={'fps':6,'frames':[f'{direction}_{i:02d}' for i in range(1,5) if not(direction=='down' and i==3)]}
catalog={'character':'Rivet / 铆钉','canvas':list(CANVAS),'anchor':list(ANCHOR),'common_scale':scale,'texture':'res://assets/ember/characters/rivet/rivet_atlas_v001.png','master_sha256':hashlib.sha256(MASTER.read_bytes()).hexdigest(),'frames':records,'animations':animations,'status':'NEW_DESIGN_ANIMATION_PREVIEW_PENDING_USER_REVIEW','limitations':['down travel has 3 accepted frames; other directions have 4','AI travel cycle requires visual review; not marked production animation approved']}
(OUT/'rivet_catalog_v001.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22)
review=Image.new('RGB',(1024,450),'#182631'); d=ImageDraw.Draw(review)
d.text((24,16),'新角色「铆钉」：单目履带检修机器人',font=font,fill='#BECBC4')
for i,direction in enumerate(directions):
    frame=frames[direction+'_00'].resize((256,320),Image.Resampling.NEAREST)
    review.paste(frame,(i*256,64),frame); d.text((i*256+100,388),['正面','左侧','右侧','背面'][i],font=font,fill='#E2B77A')
review.save(OUT/'rivet_turnaround.png')
# 同步播放四向移动，供检查固定锚点与生成姿态的一致性。
gif=[]
for i in range(12):
    panel=Image.new('RGB',(512,160),'#182631')
    for col,direction in enumerate(directions):
        clip=animations['walk_'+direction]['frames']; frame=frames[clip[i%len(clip)]]
        panel.paste(frame,(col*128,0),frame)
    gif.append(panel)
gif[0].save(OUT/'rivet_motion_preview.gif',save_all=True,append_images=gif[1:],duration=170,loop=0)
(BATCH/'generation-record.json').write_text(json.dumps({'tool':'image_gen.imagegen','prompt':'prompt.txt','master':'rivet_master_v001.png','master_sha256':catalog['master_sha256'],'finish':'whole-character crops; one common scale; ground anchor; no palette quantization','source_frames':20,'accepted_frames':19,'rejected':'down column 4 tools swap','visual_approval':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Rivet: 4 directions, 8 clips, 19 accepted frames; 1 incorrect pose excluded')
