"""固定 P26 包的独立绑定、隔离冷加载准备和固定格视觉诊断。"""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image,ImageDraw
import json,hashlib
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
ZIP=ROOT/'art-source/ember/deliveries/enemy_patrol_attack_death_v026_v001_2026-10-07.zip'
FIXED=ROOT/'art-source/ember/enemy-patrol-attack-death-v026-review-v001'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert ZIP.stat().st_size==4900369 and sha(ZIP.read_bytes())=='15ce4681bc9f83ab27288a8ab9d33edf51cc4c7c4cf748420114ada7b23bc242'
with ZipFile(ZIP) as z:
 assert z.testzip() is None and len(z.namelist())==365
 m=json.loads(z.read('manifest.json'));files=m['files'];assert len(files)==364 and set(files)|{'manifest.json'}==set(z.namelist())
 assert sha(z.read('output/catalog.json'))=='1cb4fd0224321a31334fcb3de19668ddecf2173cd72042c80ec7a36ac17723cd'
 for n,r in files.items():
  b=z.read(n);assert sha(b)==r['sha256'] and len(b)==r['bytes'] and (FIXED/n).read_bytes()==b
 for sub in ['technical-package','technical-cold-load']:
  p=OUT/sub;assert not p.exists()
  for n in z.namelist():
   target=p/n;assert target.resolve().is_relative_to(p.resolve());target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(n))
(OUT/'technical-zip-binding.json').write_text(json.dumps({'status':'PASS','zip_sha256':sha(ZIP.read_bytes()),'bytes':ZIP.stat().st_size,'payloads':364,'manifest_sha256':sha((FIXED/'manifest.json').read_bytes()),'files':files},indent=2))
old=OUT.with_name('enemy-cutter-v024-attack-death-v002')
probe=(old/'technical-cold-probe.gd').read_text(encoding='utf-8')
probe=probe.replace('for id:String in rig.parts:','var all_parts:Dictionary=rig.raw.parts.duplicate()\n\t\tall_parts.merge(rig.arms)\n\t\tfor id:String in all_parts:').replace('rig.parts[id]','all_parts[id]').replace('vec(rig.pivots[id])','vec(-sprite.position)')
probe=probe.replace('masks.append({','sprite.texture.get_image().save_png("res://../technical-runtime-source-"+direction+"-"+id+".png")\n\t\t\tmasks.append({')
probe=probe.replace('for mat:ShaderMaterial in rig.materials:powers.append(mat.get_shader_parameter("sensor_power"))','powers.append(rig.body_material.get_shader_parameter("sensor_power"))')
(OUT/'technical-cold-probe.gd').write_text(probe,encoding='utf-8');(OUT/'technical-cold-load/ta_probe.gd').write_text(probe,encoding='utf-8')
(OUT/'technical-cold.py').write_text((OUT.with_name('enemy-patrol-v025-idle-hit-v001')/'technical-cold.py').read_text(encoding='utf-8'),encoding='utf-8')
P=OUT/'technical-package';cat=json.loads((P/'output/catalog.json').read_text());records=[]
for d in ['down_left','left','up_left','up','up_right','right','down_right']:
 for a,n in [('attack',6),('death',8)]:
  frames=[]
  for i in range(n):
   p=P/f'output/enemy_patrol/{a}_{d}/f{i:02d}.png';frames.append((f'{a}_{d} F{i:02d}',Image.open(p).convert('RGBA'),sha(p.read_bytes())))
  for bgname,bg in [('light',(236,232,214,255)),('dark',(20,28,37,255))]:
   for mode,roi,scale in [('native',(0,0,128,128),1),('full',(22,35,111,110),4)]:
    w=(roi[2]-roi[0])*scale;h=(roi[3]-roi[1])*scale;cols=3 if n==6 else 4
    sheet=Image.new('RGB',(w*cols,(h+22)*2),bg[:3]);draw=ImageDraw.Draw(sheet)
    for j,(label,img,hash_) in enumerate(frames):
     x=j%cols*w;y=j//cols*(h+22);draw.text((x+3,y+3),label,fill=(235,235,235) if bgname=='dark' else (20,20,20))
     layer=Image.new('RGBA',img.size,bg);layer.alpha_composite(img);sheet.paste(layer.crop(roi).convert('RGB').resize((w,h),Image.Resampling.NEAREST),(x,y+22))
    f=OUT/f'visual-{d}-{a}-{mode}-{bgname}-{scale}x.png';sheet.save(f);records.append({'file':f.name,'sha256':sha(f.read_bytes()),'roi':roi,'scale':scale,'frames':[{'label':label,'sha256':hash_}for label,_,hash_ in frames]})
(OUT/'visual-binding.json').write_text(json.dumps(records,indent=2))
print('PASS 364 payload bindings; 56 diagnostic sheets created, not yet viewed.')
