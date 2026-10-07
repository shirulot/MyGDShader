"""独立CPU与固定ZIP审计；所有输出只写TA technical-*文件。"""
from pathlib import Path
from PIL import Image
import hashlib,json,zipfile,math
HERE=Path(__file__).resolve().parent;PACK=HERE/'technical-package';REPO=HERE.parents[3]
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rgba(p):return Image.open(p).convert('RGBA')
def mismatch(a,b):return sum(x!=y for x,y in zip(a.getdata(),b.getdata()))
def inrect(x,y,r):return r[0]<=x+.5<r[0]+r[2] and r[1]<=y+.5<r[1]+r[3]
def shifted(src,dy):
    out=Image.new('RGBA',(128,128),(255,255,255,0))
    for y in range(128):
        if 0<=y+dy<128:
            for x in range(128):out.putpixel((x,y+dy),src.getpixel((x,y)))
    return out
rig=load(PACK/'rig.json');cat=load(PACK/'output/catalog.json');receipt=load(PACK/'SOURCE_RECEIPT.json');mf=load(PACK/'manifest.json');listed=mf['files'];actual={p.relative_to(PACK).as_posix() for p in PACK.rglob('*') if p.is_file()}
result={'manifest':{'sha256':sha((PACK/'manifest.json').read_bytes()),'listed':len(listed),'missing':sorted(set(listed)-actual),'extra':sorted(actual-set(listed)-{'manifest.json'}),'bad':[f for f,q in listed.items() if not (PACK/f).exists() or sha((PACK/f).read_bytes())!=q['sha256'] or (PACK/f).stat().st_size!=q['bytes']]},'catalog':{'sha256':sha((PACK/'output/catalog.json').read_bytes()),'rig_sha_exact':sha((PACK/'rig.json').read_bytes())==cat['rig_sha256'],'tres_sha_exact':sha((PACK/cat['tres'].removeprefix('res://')).read_bytes())==cat['tres_sha256'],'clips':len(cat['clips']),'root':cat['root'],'canvas':cat['canvas']}}
delivery=REPO/'art-source/ember/deliveries';sz=delivery/'enemy_drone_seven_directions_v013_s004_2026-10-06.zip';fz=delivery/'enemy_drone_actions_v011_2026-10-06.zip';dz=delivery/'enemy_sequences_v012_2026-10-06.zip'
result['source_zip_binding']=[{'file':z.name,'sha256':sha(z.read_bytes()),'receipt_hash_exact':sha(z.read_bytes())==receipt[k]} for z,k in [(sz,'static_zip_sha256'),(fz,'rotor_zip_sha256'),(dz,'down_zip_sha256')]]
sources=[]
with zipfile.ZipFile(sz) as z:
    for d in rig['directions']:
        b=(PACK/f'source/{d}.png').read_bytes();sources.append({'direction':d,'sha256':sha(b),'s004_byte_exact':b==z.read(f'neutral_{d}.png'),'receipt_hash_exact':sha(b)==receipt['source_hashes'][d+'.png']})
fan_file=rig['fan_source'].removeprefix('res://');fan=rgba(PACK/fan_file)
with zipfile.ZipFile(fz) as z:
    oldrig=json.loads(z.read('rig.json'));result['fan_source']={'file':fan_file,'v011_byte_exact':(PACK/fan_file).read_bytes()==z.read('source/rotor_well_master.png'),'sha256':sha((PACK/fan_file).read_bytes()),'rig_sha_exact':sha((PACK/fan_file).read_bytes())==rig['fan_source_sha256'],'rects_match_v011':rig['rotor_rect']==oldrig['rotor_source_rect'] and rig['well_rect']==oldrig['well_source_rect']}
result['sources']=sources
frames=[];motion=[];centers=[]
for c in cat['clips']:
    d=c['direction'];kind=c['action'].removesuffix('_'+d);state=rig['actions'][kind];file=c['atlas'].removeprefix('res://');atlas=rgba(PACK/file);n=state['frame_count'];clip={'action':c['action'],'direction':d,'atlas_sha_exact':sha((PACK/file).read_bytes())==c['atlas_sha256'],'configuration_exact':c['frame_count']==n and c['fps']==10 and not c['loop'],'atlas_size':list(atlas.size),'frames':[]};clip_png=[]
    if d in rig['configs']:
        cfg=rig['configs'][d];src=rgba(PACK/cfg['source'].removeprefix('res://'));windows=[{(x,y) for y in range(128) for x in range(128) if ((x+.5-f['center'][0])/f['radius'][0])**2+((y+.5-f['center'][1])/f['radius'][1])**2<1} for f in cfg['fans']];aperture=set.union(*windows);tip={q for q in [(x,y) for y in range(128) for x in range(128)] if inrect(*q,cfg['probe_rect'])};sensor={q for q in [(x,y) for y in range(128) for x in range(128)] if inrect(*q,cfg['sensor_rect'])};color_records={f['id']:[] for f in cfg['fans']}
    for i in range(n):
        frame_file=Path(file).with_suffix('')/f'f{i:02d}.png';final=rgba(PACK/frame_file);clip_png.append((PACK/frame_file).read_bytes());row={'frame':i,'file':frame_file.as_posix(),'sha_exact':sha(clip_png[-1])==c['frame_hashes'][i],'atlas_mismatch':mismatch(final,atlas.crop((i*128,0,(i+1)*128,128))),'nonbinary_alpha':sum(q[3] not in [0,255] for q in final.getdata()),'alpha_bbox':list(final.getchannel('A').getbbox())}
        if d in rig['configs']:
            dy=math.floor(cfg['fall_distance']*state['drop_fraction'][i]+.5) if kind=='death' else state['body_y'][i];probe_dy=state['probe_y'][i];power=state['power'][i];angles={f['id']:state['rotor_angles'][i]*f['spin'] for f in cfg['fans']};baseline=shifted(src,dy);expected=Image.new('RGBA',(128,128),(255,255,255,0));samples={}
            for x,y in aperture:
                for k,f in enumerate(cfg['fans']):
                    if (x,y) not in windows[k]:continue
                    localx=(x+.5-f['center'][0])*6.5/f['radius'][0];localy=(y+.5-f['center'][1])*6.5/f['radius'][1];a=math.radians(angles[f['id']]);cs,sn=math.cos(a),math.sin(a);sample=[]
                    for layer in ['well','rotor']:
                        u,v=(localx,localy) if layer=='well' else (localx*cs+localy*sn,-localx*sn+localy*cs);r=rig[layer+'_rect'];sx=r[0]+(u+6.5)*r[2]/13;sy=r[1]+(v+6.5)*r[3]/13;q=fan.getpixel((math.floor(sx),math.floor(sy)));sample.append({'layer':layer,'uv':[sx,sy],'texel':[math.floor(sx),math.floor(sy)],'rgba':list(q)})
                        if q[3]>=128:expected.putpixel((x,y+dy),(*q[:3],255))
                    samples[(x,y+dy)]=sample
            # 壳体保持整图，只开两风口；灯窗按声明幂系数作整数色阶衰减。
            sensor_expected={}
            for y in range(128):
                for x in range(128):
                    if (x,y) in aperture or not src.getpixel((x,y))[3]:continue
                    q=src.getpixel((x,y));target=(x,y+dy)
                    if (x,y) in sensor:q=tuple(math.floor(v*(.3+.7*power)+.5) for v in q[:3])+(q[3],);sensor_expected[target]=list(q)
                    expected.putpixel(target,q)
            # 固定套筒留在整壳；移动尖端复制原rect的同一RGBA，不擦掉套筒或补新像素。
            for x,y in tip:
                if src.getpixel((x,y))[3]:expected.putpixel((x,y+dy+probe_dy),src.getpixel((x,y)))
            active={(x,y+dy) for x,y in aperture};tip_allowed={(x,y+dy+probe_dy) for x,y in tip};sensor_allowed={(x,y+dy) for x,y in sensor};allowed=active|tip_allowed|sensor_allowed;outside=[];outside_hidden=[];residual=[];alpha_diff=[];sensor_residual=[]
            for y in range(128):
                for x in range(128):
                    xy=(x,y);e,b,t=expected.getpixel(xy),baseline.getpixel(xy),final.getpixel(xy)
                    if xy not in allowed and b!=t:(outside if b[3] or t[3] else outside_hidden).append([x,y])
                    if xy not in tip_allowed and b[3]!=t[3]:alpha_diff.append([x,y])
                    if e!=t:
                        nearby=[]
                        for sample in samples.get(xy,[]):
                            sx,sy=sample['texel']
                            for oy in range(-1,2):
                                for ox in range(-1,2):
                                    pixel=fan.getpixel((sx+ox,sy+oy))
                                    if pixel[3]>=128 and max(abs(pixel[k]-t[k]) for k in range(3))<=1:nearby.append({'layer':sample['layer'],'texel':[sx+ox,sy+oy]})
                        residual.append({'xy':[x,y],'expected':list(e),'actual':list(t),'in_aperture':xy in active,'in_sensor':xy in sensor_allowed,'in_tip':xy in tip_allowed,'samples':samples.get(xy),'adjacent_texel_matches':nearby})
                        if xy in sensor_allowed:sensor_residual.append([x,y])
            p=c['poses'][i];axis={f['id']:[f['center'][0],f['center'][1]+dy] for f in cfg['fans']};tip_mismatch=sum(expected.getpixel(q)!=final.getpixel(q) for q in tip_allowed)
            row.update({'body_y':dy,'probe_y':probe_dy,'sensor_power':power,'outside_allowed_visible_rgba_differences':outside,'outside_allowed_transparent_rgb_only':outside_hidden,'alpha_differences_outside_tip':alpha_diff,'cpu_rgba_residual_count':len(residual),'cpu_residual':residual,'tip_rgba_mismatch':tip_mismatch,'sensor_cpu_residual':sensor_residual,'sensor_expected':{str(q):v for q,v in sensor_expected.items()},'catalog_pose_exact':p['body_y']==dy and p['body_origin']==[0,dy] and p['body_basis_x']==[1,0] and p['body_basis_y']==[0,1] and p['probe_y']==probe_dy and p['sensor_power']==power and p['rotor_angles_degrees']==angles and p['axis_world']==axis and p['ground_edge_y']==cfg['ground_edge_y']+dy,'aperture_pixels':len(active),'tip_rect':cfg['probe_rect'],'tip_original_opaque_count':sum(src.getpixel(q)[3]>0 for q in tip),'sensor_rect':cfg['sensor_rect']})
            for f in cfg['fans']:
                x,y=map(math.floor,f['center']);color_records[f['id']].append(list(final.getpixel((x,y+dy))))
        clip['frames'].append(row)
    if kind=='attack':clip['first_last_byte_exact']=clip_png[0]==clip_png[-1]
    else:clip['last_three_byte_exact']=clip_png[-1]==clip_png[-2]==clip_png[-3]
    if d in rig['configs']:
        if kind=='death':motion.append({'direction':d,'source_alpha_bbox':list(src.getchannel('A').getbbox()),'registered_ground_edge':cfg['ground_edge_y'],'fall_distance':cfg['fall_distance'],'fall_distance_exact_104_minus_source_bbox_bottom':cfg['fall_distance']==104-src.getchannel('A').getbbox()[3],'body_y':[r['body_y'] for r in clip['frames']],'all_last_three_bbox_bottom_104':all(r['alpha_bbox'][3]==104 for r in clip['frames'][-3:]),'final_opaque_row':clip['frames'][-1]['alpha_bbox'][3]-1})
        centers.append({'action':c['action'],'fans':[{'id':f['id'],'colors':color_records[f['id']],'all_center_rgba_constant':len(set(map(tuple,color_records[f['id']])))==1} for f in cfg['fans']]})
    frames.append(clip)
result['clips']=frames;result['death_motion']=motion;result['axis_center']=centers
preserved=[]
with zipfile.ZipFile(dz) as z:
    for kind in ['attack','death']:
        f=f'output/enemy_scout_drone/{kind}_down.png';preserved.append({'file':f,'byte_exact':(PACK/f).read_bytes()==z.read(f)})
        for i in range(rig['actions'][kind]['frame_count']):
            f=f'output/enemy_scout_drone/{kind}_down/f{i:02d}.png';preserved.append({'file':f,'byte_exact':(PACK/f).read_bytes()==z.read(f)})
result['preserved_down']=preserved
(HERE/'technical-pixel-integrity.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('MANIFEST',result['manifest']);print('SOURCES',all(q['s004_byte_exact'] and q['receipt_hash_exact'] for q in sources),'FAN',result['fan_source']);print('OLD',len(preserved),all(q['byte_exact'] for q in preserved))
for c in frames:
    if 'body_y' not in c['frames'][0]:continue
    print(c['action'],'CPU',[r['cpu_rgba_residual_count'] for r in c['frames']],'outside',[len(r['outside_allowed_visible_rgba_differences']) for r in c['frames']],'tip',[r['tip_rgba_mismatch'] for r in c['frames']],'sensor',[len(r['sensor_cpu_residual']) for r in c['frames']])
print('DEATH',[(q['direction'],q['fall_distance'],q['body_y'],q['all_last_three_bbox_bottom_104']) for q in motion]);print('CENTER',all(f['all_center_rgba_constant'] for c in centers for f in c['fans']))
