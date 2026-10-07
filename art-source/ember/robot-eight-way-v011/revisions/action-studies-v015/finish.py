"""动作试样导出：固定网格取样、全动作统一比例、限色、透明与预览；不绘制身体。"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parent
PAL=[tuple(bytes.fromhex(c)) for c in ['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A']]
CONFIG={
 'idle':{'name':'待机','scale':.153,'marks':[(190,525),(610,525),(1030,525),(190,1152),(610,1152),(1030,1152)],'fps':4,'ref':'idle'},
 'walk':{'name':'行走','scale':.153,'marks':[(200,530),(620,530),(1040,530),(200,1155),(620,1155),(1040,1155)],'fps':7,'ref':'walk'},
 'run':{'name':'小跑','scale':.153,'marks':[(200,535),(620,535),(1040,535),(200,1160),(620,1160),(1040,1160)],'fps':9,'ref':'run'},
 'push':{'name':'推物','scale':.142,'marks':[(230,565),(655,565),(1075,565),(240,1170),(660,1170),(1080,1170)],'fps':5,'ref':'interact_b'},
 'pull':{'name':'拉动','scale':.142,'marks':[(200,585),(625,585),(1050,585),(200,1185),(625,1185),(1050,1185)],'fps':5,'ref':'interact_c'}}
all_frames={}; report=[];cache={}
CORRECTIONS={
 'idle':{'dx':[0,1,2,0,1,2],'dy':[0,1,1,2,2,2]},
 'walk':{'dx':[0,1,2,0,1,2],'dy':[1,1,1,2,2,2]},
 'run':{'dx':[0,1,2,0,1,2],'dy':[1,1,0,3,3,6]},
 'push':{'dx':[1,0,-1,-1,-1,1],'dy':[1,1,1,2,2,2]},
 'pull':{'dx':[0,0,0,0,0,0],'dy':[0,0,1,2,2,2]}}
def groups(im):
 pts={(x,y) for y in range(96) for x in range(64) if im.getpixel((x,y))[3]};sizes=[]
 while pts:
  q=[pts.pop()];count=0
  while q:
   x,y=q.pop();count+=1
   for n in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
    if n in pts:pts.remove(n);q.append(n)
  sizes.append(count)
 return sorted(sizes,reverse=True)
for action,c in CONFIG.items():
 folder=ROOT/'frames'/action;folder.mkdir(exist_ok=True);frames=[];records=[]
 for i,(mx,my) in enumerate(c['marks']):
  # 已经满意的上排继续用第一版，步态修订只采用下排；同一动作始终共用缩放。
  version=2 if action in ('walk','run') and i>=3 else 1
  src=Image.open(ROOT/'source'/f'{action}-v{version}.png').convert('RGBA');factor=src.width/1280
  x0=round(i%3*src.width/3);y0=i//3*(src.height//2);x1=round((i%3+1)*src.width/3)
  cell=src.crop((x0,y0,x1,y0+src.height//2));scale=c['scale']/factor
  # 人工核对地面/支撑位置后的整数平移；跑步 F2/F5 保留离地高度。
  mx+=CORRECTIONS[action]['dx'][i]/c['scale'];my+=CORRECTIONS[action]['dy'][i]/c['scale']
  im=cell.transform((64,96),Image.Transform.AFFINE,(1/scale,0,mx*factor-x0-32/scale,0,1/scale,my*factor-y0-79/scale),Image.Resampling.NEAREST)
  pixels=[]
  for r,g,b,a in im.get_flattened_data():
   if a<210:pixels.append((0,0,0,0));continue
   key=(r,g,b)
   if key not in cache:cache[key]=min(PAL,key=lambda c:sum((c[j]-key[j])**2 for j in range(3)))
   pixels.append((*cache[key],255))
  im.putdata(pixels);im.save(folder/f'f{i:02d}.png');frames.append(im)
  records.append({'index':i,'file':f'frames/{action}/f{i:02d}.png','source':f'source/{action}-v{version}.png','bbox':im.getbbox(),'components_4':groups(im),'colors':len({p[:3] for p in pixels if p[3]}),'sha256':hashlib.sha256((folder/f'f{i:02d}.png').read_bytes()).hexdigest()})
 all_frames[action]=frames
 strip=Image.new('RGBA',(384,96))
 for i,im in enumerate(frames):strip.paste(im,(i*64,0))
 strip.save(ROOT/'previews'/f'{action}-strip.png');strip.resize((1536,384),Image.Resampling.NEAREST).save(ROOT/'previews'/f'{action}-strip-4x.png')
 transparent=[im.resize((256,384),Image.Resampling.NEAREST) for im in frames]
 bgframes=[]
 for im in transparent:
  bg=Image.new('RGBA',im.size,'#182631');bg.alpha_composite(im);bgframes.append(bg.convert('RGB'))
 for speed,mult in [('normal',1),('slow',3)]:
  delay=round(1000/c['fps'])*mult
  transparent[0].save(ROOT/'previews'/f'{action}-{speed}-transparent.webp',save_all=True,append_images=transparent[1:],duration=delay,loop=0,lossless=True)
  bgframes[0].save(ROOT/'previews'/f'{action}-{speed}.gif',save_all=True,append_images=bgframes[1:],duration=delay,loop=0,disposal=2)
 report.append({'action':action,'registration':c,'translation_corrections':CORRECTIONS[action],'frames':records})
# 同页概览包含已有采集试样，采集帧原样读取。
all_frames['collect']=[Image.open(ROOT.parent/'collect-knee-v014-pilot/frames'/f'left_collect_f{i:02d}.png').convert('RGBA') for i in range(6)]
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
names=[c['name'] for c in CONFIG.values()]+['采集 · V014']
montages=[]
for k in range(36):
 board=Image.new('RGB',(768,640),'#101820');d=ImageDraw.Draw(board)
 for j,(action,frames) in enumerate(all_frames.items()):
  x=j%3*256;y=j//3*320
  d.rounded_rectangle((x+7,y+7,x+249,y+312),12,fill='#182631');d.text((x+22,y+18),names[j],font=font,fill='#ece9d8')
  fps=CONFIG.get(action,{'fps':5})['fps'];im=frames[int(k*.1*fps)%6].resize((160,240),Image.Resampling.NEAREST)
  board.paste(im,(x+48,y+61),im)
 montages.append(board)
montages[0].save(ROOT/'previews/all-actions.gif',save_all=True,append_images=montages[1:],duration=100,loop=0)
montages[0].save(ROOT/'previews/all-actions.png')
(ROOT/'qa/validation.json').write_text(json.dumps({'status':'VISUAL_PILOT_NOT_PRODUCTION_APPROVED','actions':report,'no_per_frame_scale':True,'transparent_alpha_binary':True,'note':'Connected pixels do not establish correct anatomy or timing.'},ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'actions.json').write_text(json.dumps(CONFIG,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{r['action']:[(f['bbox'],f['components_4']) for f in r['frames']]} for r in report]))
