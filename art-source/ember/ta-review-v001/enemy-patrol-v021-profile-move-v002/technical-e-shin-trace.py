"""追踪 E 短连杆中两点浅甲是否被仿射、遮挡以及相对刚性靴子的真实偏离。"""
from pathlib import Path
from PIL import Image,ImageDraw
import json,numpy as np
OUT=Path(__file__).resolve().parent;P=OUT/'technical-package'
rig=json.loads((P/'rig.json').read_text());cat=json.loads((P/'output/catalog.json').read_text());cfg=rig['configs']['right'];clip=next(c for c in cat['clips'] if c['direction']=='right')
arr=lambda p:np.array(Image.open(p).convert('RGBA'))
textures={'canonical':arr(P/cfg['body_source'].removeprefix('res://')),'near':arr(P/cfg['near_source'].removeprefix('res://')),'far':arr(P/cfg['far_source'].removeprefix('res://'))}
parts=[{'id':'body','pivot':[0,0],'z':10,'source_kind':'canonical'}]+cfg['parts']
yy,xx=np.indices((128,128));X,Y=xx+.5,yy+.5
masks={p['id']:np.array(Image.open(OUT/f'technical-runtime-mask-right-{p["id"]}.png').convert('L'))>0 for p in parts}
rgba=[[244,237,225,255],[238,227,213,255]];rows=[];panels=[];roi=(48,78,74,107);scale=12
def panel(image,label,markers):
    crop=Image.fromarray(image).crop(roi);back=Image.new('RGBA',crop.size,(210,214,220,255));back.alpha_composite(crop);big=back.resize((crop.width*scale,crop.height*scale),Image.Resampling.NEAREST).convert('RGB');canvas=Image.new('RGB',(big.width,big.height+28),'white');canvas.paste(big,(0,28));dr=ImageDraw.Draw(canvas);dr.text((4,5),label,fill='black')
    for x,y,color in markers:
        ax,ay=(x-roi[0])*scale,(y-roi[1])*scale+28
        dr.rectangle((ax,ay,ax+scale-1,ay+scale-1),outline=color,width=2)
    return canvas
panels.append(panel(arr(P/'source/c002_neutral_right.png'),'C002 E neutral / magenta=near cyan=far',[(61,94,'magenta'),(61,95,'magenta'),(64,91,'cyan'),(64,92,'cyan')]))
for i in range(8):
    pose=clip['poses'][i];actual=arr(P/f'output/enemy_patrol/move_right/f{i:02d}.png');owner=np.full((128,128),'',dtype='U32');samples={}
    for p in sorted(parts,key=lambda p:p['z']):
        t=pose['part_transforms'][p['id']];basis=np.array([t['basis_x'],t['basis_y']]).T;inv=np.linalg.inv(basis);dx,dy=X-t['position'][0],Y-t['position'][1];sx=np.floor(inv[0,0]*dx+inv[0,1]*dy+p['pivot'][0]).astype(int);sy=np.floor(inv[1,0]*dx+inv[1,1]*dy+p['pivot'][1]).astype(int);cx,cy=np.clip(sx,0,127),np.clip(sy,0,127);texture=textures[p['source_kind']];use=(sx>=0)&(sx<128)&(sy>=0)&(sy<128)&masks[p['id']][cy,cx]&(texture[cy,cx,3]>0);owner[use]=p['id'];samples[p['id']]=(sx,sy)
    frame=[];markers=[]
    for name,points,color in [('right_shin',[(61,94),(61,95)],'magenta'),('left_shin',[(64,91),(64,92)],'cyan')]:
        p=next(p for p in parts if p['id']==name);t=pose['part_transforms'][name];basis=np.array([t['basis_x'],t['basis_y']]).T;side=name.split('_')[0];foot=next(p for p in parts if p['id']==side+'_foot');foot_delta=np.array(pose['part_transforms'][side+'_foot']['position'])-foot['pivot'];sx,sy=samples[name]
        coords=[]
        for j,point in enumerate(points):
            transform_center=np.array(t['position'])+basis@(np.array(point)+.5-p['pivot']);rigid_center=np.array(point)+.5+foot_delta
            possible=(sx==point[0])&(sy==point[1]);final_points=[]
            for y,x in np.argwhere(possible):
                matches=bool(np.array_equal(actual[y,x],rgba[j]));self_top=owner[y,x]==name
                if matches and self_top:markers.append((int(x),int(y),color))
                final_points.append({'xy':[int(x),int(y)],'top_owner':owner[y,x],'source_color_equal':matches,'visible_self':bool(matches and self_top)})
            coords.append({'source_xy':list(point),'affine_center':transform_center.tolist(),'rigid_foot_center':rigid_center.tolist(),'deviation_from_rigid_foot':(transform_center-rigid_center).tolist(),'raster_samples':final_points})
        frame.append({'part':name,'basis':basis.tolist(),'axis_scale':float(np.linalg.norm(basis[:,1])),'det':float(np.linalg.det(basis)),'points':coords})
    rows.append({'frame':i,'parts':frame});panels.append(panel(actual,f'E move F{i:02d} / actual exposed affine light pixels',markers))
w,h=panels[0].size;sheet=Image.new('RGB',(w*3,h*3),(128,128,128))
for i,im in enumerate(panels):sheet.paste(im,((i%3)*w,(i//3)*h))
sheet.save(OUT/'technical-e-shin-armor-12x.png')
result={'direction':'right','source_points_near':[[61,94],[61,95]],'source_points_far':[[64,91],[64,92]],'rgba':rgba,'frames':rows,'boundary':'Markers only where the CPU top layer samples the indicated point and actual PNG equals that point color. Boundary residuals may need separate actual-color inspection; no claim every visible pixel has been rendered independently.'}
(OUT/'technical-e-shin-trace.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps([{'frame':f['frame'],'parts':[{'part':p['part'],'scale':p['axis_scale'],'points':[{'source':r['source_xy'],'deviation':r['deviation_from_rigid_foot'],'visible':[q['xy'] for q in r['raster_samples'] if q['visible_self']]} for r in p['points']]} for p in f['parts']]} for f in rows]))
