"""视觉提供的背景缝位置，只追踪源归属及横移/四边形覆盖，不据连通数裁决美术。"""
from pathlib import Path
from PIL import Image
import json,numpy as np,ast
OUT=Path(__file__).resolve().parent;P=OUT/'technical-package'
js=lambda p:json.loads(p.read_text(encoding='utf-8'));arr=lambda p:np.array(Image.open(p).convert('RGBA'))
yy,xx=np.indices((128,128));X,Y=xx+.5,yy+.5
helper=OUT.with_name('enemy-cutter-v022-six-moves-v002')/'technical-audit.py'
tree=ast.parse(helper.read_text(encoding='utf-8'));exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='poly'],type_ignores=[]),str(helper),'exec'))
rig,cat=js(P/'rig.json'),js(P/'output/catalog.json');records=[]
for d,frame,x,y0,y1 in [('up_left',1,75,88,93),('up_right',2,50,83,89),('up_right',2,45,75,79),('right',2,50,87,93)]:
    c=rig['configs'][d];pose=next(v for v in cat['clips'] if v['action']=='hit_'+d)['poses'][frame];dx,dy=pose['body_translation'];dx,dy=int(dx),int(dy)
    src=arr(P/c['source'].removeprefix('res://'));actual=arr(P/f'output/enemy_cutter/hit_{d}/f{frame:02d}.png')
    masks={k:np.array(Image.open(OUT/f'technical-mask-{d}-{k}.png'))>0 for k in ['body']+[p['id'] for p in c['parts']]}
    rows=[]
    for y in range(y0,y1+1):
        original=[k for k,m in masks.items() if m[y,x] and src[y,x,3]>0]
        body_source=[x-dx,y-dy];body_owned=bool(masks['body'][y-dy,x-dx] and src[y-dy,x-dx,3]>0)
        fixed_leg_owned=[k for k,m in masks.items() if k!='body' and m[y,x] and src[y,x,3]>0]
        socket_shapes=[k for k,q in pose['socket_polygons'].items() if poly(q)[y,x]]
        rows.append({'xy':[x,y],'neutral_rgba':src[y,x].tolist(),'neutral_owners':original,'actual_rgba':actual[y,x].tolist(),'current_body_inverse_source_xy':body_source,'current_body_inverse_source_rgba':src[y-dy,x-dx].tolist(),'current_body_inverse_pixel_is_body':body_owned,'fixed_leg_owners':fixed_leg_owned,'socket_polygon_covering_pixel':socket_shapes})
    records.append({'direction':d,'action':'hit','frame':frame,'body_translation':[dx,dy],'pixels':rows})
result={'scope':'Exact visual-reported seams. Raw transparency from intended source movement is a causal explanation, not aesthetic approval.','records':records}
(OUT/'technical-seam-trace.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{'direction':r['direction'],'frame':r['frame'],'column':r['pixels'][0]['xy'][0],'actual_transparent':sum(p['actual_rgba'][3]==0 for p in r['pixels']),'neutral_body':sum(p['neutral_owners']==['body'] for p in r['pixels']),'current_body_or_leg_opaque':sum(p['current_body_inverse_pixel_is_body'] or bool(p['fixed_leg_owners']) for p in r['pixels']),'socket_covered':sum(bool(p['socket_polygon_covering_pixel']) for p in r['pixels'])} for r in records]))
