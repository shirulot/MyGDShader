"""登记理想双精度CPU与已提交PNG的取样差；不会把它改写成CPU零差。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import json,math
import numpy as np
from PIL import Image
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
z=ZipFile(ROOT/'art-source/ember/deliveries/enemy_drone_idle_hit_v017_v001_2026-10-07.zip')
rig=json.loads(z.read('rig.json'));binding=json.loads((OUT/'technical-binding.json').read_text(encoding='utf-8'))
image=lambda p:np.array(Image.open(BytesIO(z.read(p.removeprefix('res://')))).convert('RGBA'))
master=image(rig['fan_source']);rot=lambda a:np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
rows=[];counts={};unresolved=[]
for group in binding['cpu_reconstruction']:
 kind,d=group['action'].split('_',1);i=group['frame'];s=rig['actions'][kind];R=rot(math.radians(s['roll'][i]));origin=np.array([64,67+s['body_y'][i]])-R@np.array([64,67]);cfg=rig['configs'][d];source=image(cfg['source'])
 for p in group['points']:
  expected=np.array(p['cpu_rgba']);actual=np.array(p['png_rgba']);x,y=p['output'];local=(np.array([x+.5,y+.5])-origin)@R
  row={'action':group['action'],'frame':i,**p};candidates=[]
  if actual[3]==expected[3]==255 and np.max(np.abs(actual[:3]-expected[:3]))<=1:
   category='opaque_one_code_value'
  else:
   layers=[('shell',source,local)]
   aperture_margin=min(abs(np.linalg.norm((local-np.array(f['center']))/np.array(f['radius']))-1)*4.5 for f in cfg['fans'])
   row['nearest_aperture_margin_source_screen_px']=float(aperture_margin)
   for f in cfg['fans']:
    plane=(local-f['center'])/(np.array(f['radius'])/6.5)
    for layer in ['well','rotor']:
     coords=plane if layer=='well' else plane@rot(math.radians(s['rotor_angles'][i]*f['spin']));r=rig[layer+'_rect'];uv=np.array(r[:2])+(coords+6.5)/13*np.array(r[2:])
     layers.append((f['id']+'/'+layer,master,uv))
   if actual[3]==0 and aperture_margin<.01:
    category='aperture_threshold_alpha_edge'
   else:
    for name,src,uv in layers:
     ix,iy=np.floor(uv).astype(int)
     for ty in range(iy-1,iy+2):
      for tx in range(ix-1,ix+2):
       if tx<0 or ty<0 or tx>=src.shape[1] or ty>=src.shape[0]:continue
       value=src[ty,tx].astype(int);alpha=255 if value[3]>=128 else 0
       if alpha!=actual[3] or (alpha>0 and np.max(np.abs(value[:3]-actual[:3]))>1):continue
       if alpha==0:continue
       # 理想UV到能解释实际RGB的相邻texel方格的距离。
       delta=np.maximum(np.maximum(np.array([tx,ty])-uv,uv-np.array([tx+1,ty+1])),0)
       candidates.append({'layer':name,'texel':[int(tx),int(ty)],'rgba_source':value.tolist(),'distance_source_texel':float(np.linalg.norm(delta))})
    candidates.sort(key=lambda c:c['distance_source_texel'])
    if candidates and candidates[0]['distance_source_texel']<.1:category='neighbor_source_sampling_edge';row['nearest_matching_source']=candidates[0]
    else:category='UNRESOLVED';unresolved.append(row)
  row['classification']=category;counts[category]=counts.get(category,0)+1;rows.append(row)
summary={'cpu_pixel_differences':len(rows),'cpu_alpha_differences':sum(p['cpu_rgba'][3]!=p['png_rgba'][3] for p in rows),'counts':counts,'unresolved':unresolved,'neighbor_source_texel_max_distance':max((p['nearest_matching_source']['distance_source_texel'] for p in rows if 'nearest_matching_source' in p),default=0),'points':rows,'interpretation':'Ideal double-precision inverse sampling differs from producer GPU nearest interpolation. Listed source-neighbor/one-code/aperture-edge evidence explains differences; not a fresh GPU rerun or assertion of pixel identity.'}
(OUT/'technical-cpu-boundaries.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='points'},ensure_ascii=True))
