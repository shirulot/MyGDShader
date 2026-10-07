"""获取作者公开动作预览，拆帧用于姿势研究；不获取付费素材包。"""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import urllib.request,json
ROOT=Path(__file__).resolve().parent
for sub in ['references','source','prompts','frames','previews','qa']:(ROOT/sub).mkdir(exist_ok=True)
refs={
 'idle':'https://img.itch.zone/aW1hZ2UvMTE0MDExMS8xNzkxNDYzNS5naWY=/original/6NpL3Z.gif',
 'walk':'https://img.itch.zone/aW1hZ2UvMTE0MDExMS8xODEwMTUyNC5naWY=/original/EJp%2BCO.gif',
 'run':'https://img.itch.zone/aW1hZ2UvMTE0MDExMS8xNzkxNDYzNi5naWY=/original/AKUIvh.gif',
 'interact_a':'https://img.itch.zone/aW1hZ2UvMTE0MDExMS8xNzkxNDY3Ni5naWY=/original/fgtxME.gif',
 'interact_b':'https://img.itch.zone/aW1hZ2UvMTE0MDExMS8xNzkxNDY3Ny5naWY=/original/D91ENG.gif',
 'interact_c':'https://img.itch.zone/aW1hZ2UvMTE0MDExMS8xNzkxNDY3OS5naWY=/original/lBgXtX.gif'}
records={}; overview=Image.new('RGB',(1152,6*260),'#182631')
for row,(name,url) in enumerate(refs.items()):
 target=ROOT/'references'/f'{name}.gif'
 if not target.exists():urllib.request.urlretrieve(url,target)
 gif=Image.open(target);record={'url':url,'source_frames':gif.n_frames,'size':gif.size,'samples':[]}
 sheet=Image.new('RGB',(1152,256),'#182631')
 for i in range(6):
  f=round(i*(gif.n_frames-1)/5);gif.seek(f);record['samples'].append(f)
  # 固定角色区域裁切，仅去掉预览边框和下方倒影；保留原始像素姿势。
  frame=ImageOps.mirror(gif.convert('RGB').crop((32,24,176,144))).resize((192,160),Image.Resampling.NEAREST)
  sheet.paste(frame,(i*192,40));ImageDraw.Draw(sheet).text((i*192+6,216),f'{name} source F{f}',fill='white')
 sheet.save(ROOT/'references'/f'{name}-six-poses.png');overview.paste(sheet,(0,row*260));records[name]=record
overview.save(ROOT/'references/overview.png')
original=Image.open(ROOT.parent/'collect-knee-v014-pilot/source/robot-neutral.png')
canonical=Image.new('RGBA',(192,192));
for i in range(6):canonical.paste(original,((i%3)*64,(i//3)*96))
canonical.resize((1536,1536),Image.Resampling.NEAREST).save(ROOT/'source/identity-grid.png')
(ROOT/'references/index.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
(ROOT/'run-manifest.json').write_text(json.dumps({'status':'IN_PROGRESS','scope':{'direction':'left','actions':['idle','walk','run','push','pull'],'frames_per_action':6,'cell':[64,96]},'method':'imagegen','reference_page':'https://deadrevolver.itch.io/pixel-prototype-player-sprites','identity':'original robot, light armor, blue-gray mechanical limbs, limited brass','production_replacement':False},indent=2),encoding='utf-8')
print(json.dumps(records,indent=2))

