"""可见锯片局部自转缺口及 NE 死亡/SE nominal sole 的独立坐标追踪。"""
from pathlib import Path
from PIL import Image,ImageDraw
import json,numpy as np
OUT=Path(__file__).resolve().parent;P=OUT/'technical-package'
rig=json.loads((P/'rig.json').read_text());cat=json.loads((P/'output/catalog.json').read_text())
arr=lambda p:np.array(Image.open(p).convert('RGBA'))
yy,xx=np.indices((128,128));X,Y=xx+.5,yy+.5
records=[]
panels=[]
for d in ['up_left','right']:
    cfg=rig['configs'][d];src=arr(P/f'source/{d}.png');mask=np.array(Image.open(OUT/f'technical-runtime-mask-{d}-saw_blade.png').convert('L'))>0
    visible=mask&(src[:,:,3]>0);sy,sx=np.where(visible)
    tool=next(t for t in cfg['tools'] if t['id']=='saw');owner=np.full((128,128),'',dtype='U32')
    for m in OUT.glob(f'technical-runtime-mask-{d}-*.png'):
        name=m.stem.removeprefix(f'technical-runtime-mask-{d}-');owner[np.array(Image.open(m).convert('L'))>0]=name
    rows=[]
    for kind,f in [('attack',3),('death',7)]:
        pose=next(c for c in cat['clips'] if c['action']==kind+'_'+d)['poses'][f];t=pose['part_transforms']['saw_blade']
        basis=np.array([t['basis_x'],t['basis_y']]).T;inv=np.linalg.inv(basis);pivot=np.array(tool['hub']);dx,dy=X-t['position'][0],Y-t['position'][1]
        u=inv[0,0]*dx+inv[0,1]*dy+pivot[0];v=inv[1,0]*dx+inv[1,1]*dy+pivot[1];ix,iy=np.floor(u).astype(int),np.floor(v).astype(int);cx,cy=np.clip(ix,0,127),np.clip(iy,0,127)
        # Ellipse is a declared projection reference, not an invented completed blade drawing.
        ellipse=((u-pivot[0])/tool['radius'][0])**2+((v-pivot[1])/tool['radius'][1])**2<=1
        absent=ellipse&~visible[cy,cx];frame=arr(P/f'output/enemy_cutter/{kind}_{d}/f{f:02d}.png')
        holes=absent&(frame[:,:,3]==0)
        trace=[{'output_xy':[int(x),int(y)],'source_xy':[int(cx[y,x]),int(cy[y,x])],'source_rgba':src[cy[y,x],cx[y,x]].tolist(),'source_owner':owner[cy[y,x],cx[y,x]],'continuous_source_xy':[float(u[y,x]),float(v[y,x])]} for y,x in np.argwhere(holes)]
        rows.append({'kind':kind,'frame':f,'blade_pose':t,'transparent_inside_declared_projection':trace,'note':'Declared ellipse only localizes loss of visible patch; it does not prescribe a new full disc.'})
        roi=(65,60,108,107) if d=='up_left' else (64,72,108,107)
        for kind2,image in [('source',src),('frame',frame)]:
            im=Image.fromarray(image).crop(roi);back=Image.new('RGBA',im.size,(215,219,224,255));back.alpha_composite(im);back=back.resize((im.width*8,im.height*8),Image.Resampling.NEAREST).convert('RGB')
            panel=Image.new('RGB',(back.width,back.height+25),'white');panel.paste(back,(0,25));ImageDraw.Draw(panel).text((4,5),f'{d} {kind} F{f:02d} {kind2}',fill='black');panels.append(panel)
    records.append({'direction':d,'source_blade_opaque':int(visible.sum()),'source_blade_bbox':[int(sx.min()),int(sy.min()),int(sx.max()+1),int(sy.max()+1)],'blade_polygon':tool['blade_polygon'],'hub':tool['hub'],'radius':tool['radius'],'frames':rows})
width=max(p.width for p in panels);height=max(p.height for p in panels);sheet=Image.new('RGB',(width*4,height*2),(130,130,130))
for i,panel in enumerate(panels):sheet.paste(panel,((i%4)*width,(i//4)*height))
sheet.save(OUT/'technical-blade-source-frame-8x.png')
# Inspect true SE foot masks; nominal sole probes can belong to the overlaid tools already at bind.
se=[]
for leg in rig['configs']['down_right']['parts']:
    name=leg['id']+'_foot';src=arr(P/'source/down_right.png');mask=np.array(Image.open(OUT/f'technical-runtime-mask-down_right-{name}.png').convert('L'))>0
    use=mask&(src[:,:,3]>0);ys,xs=np.where(use);se.append({'id':leg['id'],'nominal_sole':leg['sole'],'owned_foot_pixels':[[int(x),int(y)] for y,x in np.argwhere(use)],'actual_foot_bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)] if len(xs) else None})
# NE source-visible far-front shell/body mapping in the reported ROI, using registered inverse rigid transforms.
ne=[];d='up_right';src=arr(P/f'source/{d}.png');clip=next(c for c in cat['clips'] if c['action']=='death_'+d);cfg=rig['configs'][d]
pivots={'body':[0,0]}
for p in cfg['parts']:pivots[p['id']]=p['pivot'];pivots[p['id']+'_foot']=[0,0]
for t in cfg['tools']:
    pivots[t['id']]=t['pivot']
    if t['blade_polygon']:pivots[t['id']+'_blade']=t['hub']
for f in range(4,8):
    image=arr(P/f'output/enemy_cutter/death_{d}/f{f:02d}.png');pixels=[]
    for y in range(72,82):
      for x in range(38,49):
        if not image[y,x,3]:continue
        matches=[]
        for name,pivot in pivots.items():
            t=clip['poses'][f]['part_transforms'][name];basis=np.array([t['basis_x'],t['basis_y']]).T;uv=np.linalg.inv(basis)@(np.array([x+.5,y+.5])-np.array(t['position']))+pivot;sx,sy=np.floor(uv).astype(int)
            if not(0<=sx<128 and 0<=sy<128):continue
            mask=np.array(Image.open(OUT/f'technical-runtime-mask-{d}-{name}.png').convert('L'))>0
            if mask[sy,sx] and np.array_equal(src[sy,sx],image[y,x]):matches.append({'part':name,'source_xy':[int(sx),int(sy)]})
        pixels.append({'xy':[x,y],'rgba':image[y,x].tolist(),'source_matches':matches})
    footmask=np.array(Image.open(OUT/f'technical-runtime-mask-{d}-front_left_foot.png').convert('L'))>0
    bodymask=np.array(Image.open(OUT/f'technical-runtime-mask-{d}-body.png').convert('L'))>0
    delta=int(clip['poses'][f]['body_translation'][1]);bodycoords=set()
    for by,bx in np.argwhere(bodymask&(src[:,:,3]>0)):
        if by+delta<128 and np.array_equal(image[by+delta,bx],src[by,bx]):bodycoords.add((int(bx),int(by+delta)))
    contacts=[]
    for fy,fx in np.argwhere(footmask&(src[:,:,3]>0)):
        if not np.array_equal(image[fy,fx],src[fy,fx]):continue
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            if (fx+dx,fy+dy) in bodycoords:contacts.append({'foot_xy':[int(fx),int(fy)],'body_xy':[int(fx+dx),int(fy+dy)]})
    ne.append({'frame':f,'roi':[38,72,49,82],'pixels':pixels,'visible_foot_to_body_4neighbor_contacts':contacts})
result={'blade_visible_patch_spin':records,'SE_actual_foot_masks':se,'NE_death_roi_trace':ne}
(OUT/'technical-defect-trace.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'blade_holes':[{'d':r['direction'],'opaque':r['source_blade_opaque'],'frames':[{'kind':f['kind'],'frame':f['frame'],'holes':len(f['transparent_inside_declared_projection'])} for f in r['frames']]} for r in records],'SE':se,'NE_roi_pixel_counts':[len(r['pixels']) for r in ne]},ensure_ascii=False))
