"""按实际登记姿态核安装座栅格与移动body/本腿的覆盖或邻接；诊断不替代视觉。"""
from pathlib import Path
from PIL import Image
import numpy as np
import json
OUT=Path(__file__).resolve().parent;P=OUT/'technical-package'
js=lambda p:json.loads(p.read_text(encoding='utf-8'))
rig,cat=js(P/'rig.json'),js(P/'output/catalog.json')
yy,xx=np.indices((128,128));X,Y=xx+.5,yy+.5
def polygon_mask(shape):
    m=np.zeros((128,128),bool)
    for (x1,y1),(x2,y2) in zip(shape,shape[1:]+shape[:1]):
        if y1!=y2:m^=((y1>Y)!=(y2>Y))&(X<(x2-x1)*(Y-y1)/(y2-y1)+x1)
    return m
def placed(mask,offset):
    out=np.zeros_like(mask);ys,xs=np.where(mask);out[ys+int(offset[1]),xs+int(offset[0])]=True;return out
def expand(mask):
    p=np.pad(mask,1);out=np.zeros_like(mask)
    for y in range(3):
        for x in range(3):out|=p[y:y+128,x:x+128]
    return out
records=[]
for d,c in rig['configs'].items():
    source=np.array(Image.open(P/c['source'].removeprefix('res://')).convert('RGBA'))[:,:,3]>0
    masks={k:np.array(Image.open(OUT/f'technical-mask-{d}-{k}.png'))>0 for k in ['body']+[p['id'] for p in c['parts']]}
    clip=next(v for v in cat['clips'] if v['direction']==d)
    for pose in clip['poses']:
        body=placed(masks['body']&source,pose['body_translation'])
        for p in c['parts']:
            key=p['id'];leg=placed(masks[key]&source,pose['supports'][key]['hidden_mount_travel'])
            quad=polygon_mask(pose['socket_polygons'][key])
            records.append({'direction':d,'frame':pose['frame'],'part':key,'quad_raster_pixels':int(quad.sum()),'body_overlap':int(np.sum(quad&body)),'own_leg_overlap':int(np.sum(quad&leg)),'body_overlap_or_8neighbor':int(np.sum(quad&expand(body))),'own_leg_overlap_or_8neighbor':int(np.sum(quad&expand(leg))),'whole_leg_body_overlap':int(np.sum(leg&body)),'whole_leg_body_overlap_or_8neighbor':int(np.sum(leg&expand(body)))})
suspects=[r for r in records if not r['body_overlap_or_8neighbor'] or not r['own_leg_overlap_or_8neighbor']]
out={'status':'NO_PIXEL_DISCONNECTION_CANDIDATES' if not suspects else 'VISUAL_FOLLOWUP','scope':'Polygon raster touching body and own leg; does not prove installation is visually natural. Endpoints alone do not establish surface attachment.','records':records,'no_body_or_own_leg_neighbor':suspects}
(OUT/'technical-socket-contact.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'status':out['status'],'records':len(records),'suspects':suspects}))
