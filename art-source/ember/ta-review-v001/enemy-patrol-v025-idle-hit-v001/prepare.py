"""P25完整固定包绑定、隔离冷副本和只读视觉诊断；不修改生产素材。"""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image, ImageDraw
import json,hashlib
OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[3]
ZIP=ROOT/'art-source/ember/deliveries/enemy_patrol_idle_hit_v025_v001_2026-10-07.zip'
FIXED=ROOT/'art-source/ember/enemy-patrol-idle-hit-v025-review-v001'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert ZIP.stat().st_size==3495238 and sha(ZIP.read_bytes())=='677b7b0747267f1c3ce36216d838696fb617184007c562bcc63e30d9e1380e0d'
with ZipFile(ZIP) as z:
 assert z.testzip() is None and len(z.namelist())==234
 manifest=json.loads(z.read('manifest.json')); files=manifest['files']
 assert len(files)==233 and set(z.namelist())==set(files)|{'manifest.json'}
 assert sha(z.read('output/catalog.json'))=='8c2c07039615fbd51e87778bd19c6cb7bec3c6a057a60e59deb8589fb8d50a75'
 for n,r in files.items():
  b=z.read(n); assert sha(b)==r['sha256'] and len(b)==r['bytes'] and (FIXED/n).read_bytes()==b
 for sub in ['technical-package','technical-cold-load']:
  p=OUT/sub; assert not p.exists()
  for n in z.namelist():
   target=p/n; assert target.resolve().is_relative_to(p.resolve()); target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(z.read(n))
(OUT/'technical-zip-binding.json').write_text(json.dumps({'status':'PASS','zip_sha256':sha(ZIP.read_bytes()),'zip_bytes':ZIP.stat().st_size,'payloads':233,'members':234,'manifest_sha256':sha((FIXED/'manifest.json').read_bytes()),'files':files},indent=2))
old=OUT.with_name('enemy-cutter-v023-idle-hit-v001')
probe=(old/'technical-cold-probe.gd').read_text(encoding='utf-8').replace('C23','P25')
# 保存实际贴图，供与固定源逐RGBA核对；实际pose单独返回后用独立数学复算。
probe=probe.replace('masks.append({"id":id,"path":path,"z":node.z_index})','var source_image:Image=sprite.texture.get_image()\n\t\t\t\tsource_image.save_png("res://../technical-runtime-source-"+direction+"-"+id+".png")\n\t\t\t\tmasks.append({"id":id,"path":path,"z":node.z_index})')
(OUT/'technical-cold-probe.gd').write_text(probe,encoding='utf-8')
(OUT/'technical-cold-load/ta_probe.gd').write_text(probe,encoding='utf-8')
cold=(old/'technical-cold.py').read_text(encoding='utf-8').replace("'--editor','--import'","'--editor','--import','--quit'")
(OUT/'technical-cold.py').write_text(cold,encoding='utf-8')
P=OUT/'technical-package';cat=json.loads((P/'output/catalog.json').read_text())
records=[]
def composite(a,bg):
 b=Image.new('RGBA',a.size,bg);b.alpha_composite(a);return b.convert('RGB')
# 每方向8帧同坐标2行展示，保留全画布原生与固定ROI放大，避免逐帧归一化。
for d in ['down_left','left','up_left','up','up_right','right','down_right']:
 clips=[next(c for c in cat['clips'] if c['action']==a+'_'+d) for a in ['idle','hit']]
 frames=[]
 for c in clips:
  for i in range(4):
   p=P/c['atlas'].removeprefix('res://');p=p.with_suffix('')/f'f{i:02d}.png'
   frames.append((c['action']+f' F{i:02d}',Image.open(p).convert('RGBA'),sha(p.read_bytes())))
 for bgname,bg in [('light',(236,232,214,255)),('dark',(20,28,37,255))]:
  for mode,roi,scale in [('native',(0,0,128,128),1),('full',(35,40,94,110),4),('joint',(39,72,92,108),8)]:
   w=(roi[2]-roi[0])*scale;h=(roi[3]-roi[1])*scale
   sheet=Image.new('RGB',(w*4,(h+22)*2),bg[:3]);draw=ImageDraw.Draw(sheet)
   for j,(label,img,sh) in enumerate(frames):
    x=j%4*w;y=j//4*(h+22)
    draw.text((x+3,y+3),label,fill=(235,235,235) if bgname=='dark' else (20,20,20))
    sheet.paste(composite(img.crop(roi),bg).resize((w,h),Image.Resampling.NEAREST),(x,y+22))
   f=OUT/f'visual-{d}-{mode}-{bgname}-{scale}x.png';sheet.save(f)
   records.append({'file':f.name,'sha256':sha(f.read_bytes()),'direction':d,'roi':roi,'scale':scale,'frames':[{'label':a,'sha256':h} for a,_,h in frames]})
(OUT/'visual-binding.json').write_text(json.dumps(records,indent=2))
print('PASS fixed 233 payloads; 42 diagnostic sheets created, not yet visually reviewed.')
