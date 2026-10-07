"""将已保存的生图整理成固定画布动作试样。只切片、限色、注册与导出。"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
ROOT=Path(__file__).resolve().parent
PAL=[tuple(bytes.fromhex(c)) for c in ['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','ECE9D8','7B4D35','B77C4B','E2B77A','B9947B','D7B59B']]
TIMING=json.loads((ROOT/'references/timing.json').read_text())
CONFIG={'idle':{'name':'待机','scale':.128,'x':170},'walk':{'name':'行走','scale':.128,'x':196},'run':{'name':'跑动','scale':.128,'x':194},'crouch':{'name':'下蹲','scale':.078,'x':245}}
cache={};allframes={};report=[]
def clean(im):
 values=[]
 for r,g,b,a in im.get_flattened_data():
  if a<210:values.append((0,0,0,0));continue
  key=(r,g,b)
  if key not in cache:cache[key]=min(PAL,key=lambda c:sum((c[j]-key[j])**2 for j in range(3)))
  values.append((*cache[key],255))
 im.putdata(values);return im
def components(im):
 pts={(x,y) for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3]};out=[]
 while pts:
  q=[pts.pop()];count=0
  while q:
   x,y=q.pop();count+=1
   for n in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
    if n in pts:pts.remove(n);q.append(n)
  out.append(count)
 return sorted(out,reverse=True)
for action,c in CONFIG.items():
 src=Image.open(ROOT/'source'/f'{action}-generated.png').convert('RGBA');t=TIMING[action];n=t['count'];cols=t['cols'];s=c['scale'];frames=[];recs=[]
 folder=ROOT/'frames'/action;folder.mkdir(exist_ok=True)
 for i in range(n):
  x0=round(i%cols*src.width/cols);x1=round((i%cols+1)*src.width/cols)
  # 下蹲生图上下排的空白不等高，分界置于实际两排之间；避免上排鞋底混入下排。
  split=round(src.height*680/1280) if action=='crouch' else src.height//2
  y0=0 if i<cols else split;y1=split if i<cols else src.height
  cell=src.crop((x0,y0,x1,y1))
  # 无地面或粒子的透明源稿，最下实体行为鞋底。只对齐脚底，不拟合每帧轮廓或缩放。
  alpha=cell.getchannel('A').point(lambda a:255 if a>=210 else 0);bounds=alpha.getbbox();assert bounds
  sole=bounds[3]-1;target_y=77 if action=='run' and i in (3,7) else 80
  im=cell.transform((64,96),Image.Transform.AFFINE,(1/s,0,c['x']-32/s,0,1/s,sole-target_y/s),Image.Resampling.NEAREST);im=clean(im)
  im.save(folder/f'f{i:02d}.png');frames.append(im)
  recs.append({'frame':i,'file':f'frames/{action}/f{i:02d}.png','duration_ms':t['durations_ms'][i],'source_sole_y':sole,'target_sole_y':target_y,'bbox':im.getbbox(),'components_4':components(im),'sha256':hashlib.sha256((folder/f'f{i:02d}.png').read_bytes()).hexdigest()})
 allframes[action]=frames
 strip=Image.new('RGBA',(64*n,96))
 for i,im in enumerate(frames):strip.paste(im,(i*64,0))
 strip.save(ROOT/'previews'/f'{action}-strip.png');strip.resize((64*n*3,288),Image.Resampling.NEAREST).save(ROOT/'previews'/f'{action}-strip-3x.png')
 transparent=[im.resize((256,384),Image.Resampling.NEAREST) for im in frames];opaque=[]
 for im in transparent:
  bg=Image.new('RGBA',im.size,'#182631');bg.alpha_composite(im);opaque.append(bg.convert('RGB'))
 for speed,mult in [('normal',1),('slow',3)]:
  delays=[d*mult for d in t['durations_ms']]
  opaque[0].save(ROOT/'previews'/f'{action}-{speed}.gif',save_all=True,append_images=opaque[1:],duration=delays,loop=0,disposal=2)
  transparent[0].save(ROOT/'previews'/f'{action}-{speed}-transparent.webp',save_all=True,append_images=transparent[1:],duration=delays,loop=0,lossless=True)
 report.append({'action':action,'count':n,'registration':c,'frames':recs})
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20);overview=[]
for tick in range(48):
 board=Image.new('RGB',(640,680),'#101820');d=ImageDraw.Draw(board)
 for j,(action,frames) in enumerate(allframes.items()):
  x=j%2*320;y=j//2*340;c=CONFIG[action];d.rounded_rectangle((x+8,y+8,x+312,y+332),12,fill='#182631');d.text((x+24,y+20),f"{c['name']} · {len(frames)} 帧",font=font,fill='#ece9d8')
  durations=TIMING[action]['durations_ms'];ms=tick*80%sum(durations);f=0
  while ms>=durations[f] and f<len(frames)-1:ms-=durations[f];f+=1
  im=frames[f].resize((192,288),Image.Resampling.NEAREST);board.paste(im,(x+64,y+45),im)
 overview.append(board)
overview[0].save(ROOT/'previews/all-actions.gif',save_all=True,append_images=overview[1:],duration=80,loop=0)
overview[0].save(ROOT/'previews/all-actions.png')
# 原三视图同一固定尺度导出；不把设计原稿宣称成已接受生产资产。
canonical=Image.new('RGBA',(192,96))
for i,name in enumerate(['left','front','back']):
 im=clean(Image.open(ROOT/'source'/f'canonical-{name}.png').convert('RGBA'));im.save(ROOT/'frames'/f'canonical-{name}.png');canonical.paste(im,(i*64,0))
canonical.resize((1152,576),Image.Resampling.NEAREST).save(ROOT/'previews/canonical-6x.png')
qa={'status':'VISUAL_CANDIDATE_NOT_USER_ACCEPTED','new_animation_frame_count':sum(len(v) for v in allframes.values()),'cell':[64,96],'root':[32,80],'palette':[bytes(c).hex() for c in PAL],'fixed_scale_per_action':True,'duration_match':'public decoded GIFs only; no original Aseprite tags available','actions':report,'note':'Alpha connectivity does not establish anatomical correctness or exact pose matching.'}
(ROOT/'qa/validation.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'actions.json').write_text(json.dumps({a:{**c,**TIMING[a]} for a,c in CONFIG.items()},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{r['action']:[(f['bbox'],f['components_4']) for f in r['frames']]} for r in report]))
