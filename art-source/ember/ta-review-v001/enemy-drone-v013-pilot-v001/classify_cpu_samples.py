"""解释已保存理想 CPU 与 PNG 采样差；不重新导出或运行 GPU。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import json,math
import numpy as np
from PIL import Image
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
p=OUT/'binding.json';data=json.loads(p.read_text(encoding='utf-8'))
with ZipFile(ROOT/'art-source/ember/deliveries/enemy_eight_directions_v013_pilot_drone_v001_2026-10-06.zip') as z:
    master=np.array(Image.open(BytesIO(z.read('source/parts/rotor_well_master.png'))).convert('RGBA'))
    spec=next(s for s in json.loads(z.read('pilot_rigs.json'))['units'] if s['unit']=='enemy_scout_drone')
records=[]
for frame in data['cpu_rotor_aperture_reconstruction']:
    alpha=0;one=0;boundary=[];unexplained=[]
    for d in frame['diffs']:
        cpu=np.array(d['cpu_rgba']);actual=np.array(d['png_rgba'])
        alpha+=int(cpu[3]!=actual[3])
        if cpu[3]==actual[3] and np.max(np.abs(cpu[:3]-actual[:3]))<=1:
            one+=1;continue
        x,y=d['output'];i=frame['frame'];bob=[0,-1,-1,0,1,1,0,0][i]
        fan=min(spec['fans'],key=lambda f:abs(x+.5-f['center'][0]))
        local=(np.array([x+.5,y+.5])-np.array(fan['center'])-[0,bob])/(np.array(fan['radius'])/6.5)
        theta=math.radians(i*11.25*fan['spin']);cs,sn=math.cos(theta),math.sin(theta)
        matches=[]
        # Alpha 门槛跨 texel 边界可能令顶层转子显露/透出井底，检查两固定来源。
        for layer in ['rotor','well']:
            q=local if layer=='well' else np.array([[cs,sn],[-sn,cs]])@local
            rect=spec[layer+'_rect'];fx,fy=np.array(rect[:2])+(q+6.5)/13*np.array(rect[2:]);sx,sy=math.floor(fx),math.floor(fy)
            for iy in range(sy-1,sy+2):
                for ix in range(sx-1,sx+2):
                    value=master[iy,ix].astype(int)
                    if (value[3]>=128)!=bool(actual[3]) or np.max(np.abs(value[:3]-actual[:3]))>1:continue
                    distance=max(max(ix-fx,0,fx-(ix+1)),max(iy-fy,0,fy-(iy+1)))
                    matches.append((distance,int(np.max(np.abs(value[:3]-actual[:3]))),ix,iy,layer,fx,fy))
        if matches and min(matches)[0]<.1:
            distance,delta,ix,iy,layer,fx,fy=min(matches)
            boundary.append({'output':d['output'],'layer':layer,'cpu_selected_layer':d['layer'],'source_float':[float(fx),float(fy)],'ideal_texel':[math.floor(fx),math.floor(fy)],'png_matching_neighbor':[ix,iy],'distance_source_px':float(distance),'source_rgb':master[iy,ix,:3].tolist(),'png_rgb':actual[:3].tolist(),'residual_rgb_code':delta})
        else:unexplained.append(d)
    records.append({'frame':frame['frame'],'ideal_cpu_aperture_rgba_pixel_diffs':len(frame['diffs']),'alpha_difference_points':alpha,'onecode_rgb_points':one,'source_boundary_neighbor_points':len(boundary),'max_boundary_distance_source_px':max((b['distance_source_px'] for b in boundary),default=0),'neighbor_samples':boundary,'unexplained':unexplained})
data['cpu_sample_classification']=records
p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{k:v for k,v in r.items() if k not in ['neighbor_samples','unexplained']}|{'unexplained':len(r['unexplained'])} for r in records],indent=2))
assert all(not r['unexplained'] and r['alpha_difference_points']==0 for r in records)
