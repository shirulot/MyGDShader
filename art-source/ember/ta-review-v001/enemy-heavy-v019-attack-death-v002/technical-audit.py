"""Independent frozen-package CPU audit. Does not run production export or GPU.

The model follows registered geometry but uses independent pixel-centre polygon
ownership and inverse transforms. Residuals remain explicit, never tolerance zero.
"""
from pathlib import Path
from PIL import Image
import hashlib, json, math, zipfile

B = Path(__file__).resolve().parent
P = B / 'technical-package'
ROOT = B.parents[3]
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rgba = lambda p: Image.open(p).convert('RGBA')

def inside(x, y, poly):
    state = False
    for i, (ax, ay) in enumerate(poly):
        bx, by = poly[(i+1) % len(poly)]
        cross = (x-ax)*(by-ay)-(y-ay)*(bx-ax)
        if abs(cross) < 1e-10 and min(ax,bx) <= x <= max(ax,bx) and min(ay,by) <= y <= max(ay,by):
            return True
        if (ay > y) != (by > y) and x < (bx-ax)*(y-ay)/(by-ay)+ax:
            state = not state
    return state

manifest = load(P/'manifest.json')
actual = {q.relative_to(P).as_posix() for q in P.rglob('*') if q.is_file()}
listed = manifest['files']
rig = load(P/'rig.json')
cat = load(P/'output/catalog.json')
receipt = load(P/'SOURCE_RECEIPT.json')
reg = load(P/'source/hidden_registration.json')
hidden = rgba(P/'source/hidden_chassis_eight_views_v001.png')
out = {
    'manifest': {'sha256': sha(P/'manifest.json'), 'listed':len(listed),
                 'missing':sorted(set(listed)-actual), 'extra': sorted(actual-set(listed)-{'manifest.json'}),
                 'bad':[f for f,r in listed.items() if not (P/f).exists() or sha(P/f)!=r['sha256'] or (P/f).stat().st_size!=r['bytes']]},
    'catalog': {'sha256':sha(P/'output/catalog.json'), 'rig_hash_exact':sha(P/'rig.json')==cat['rig_sha256'],
                'tres_hash_exact':sha(P/cat['tres'].removeprefix('res://'))==cat['tres_sha256'],
                'clips':len(cat['clips']), 'root':cat['root'], 'canvas':cat['canvas'], 'version_label':cat['version']},
    'hidden': {'sha256':sha(P/'source/hidden_chassis_eight_views_v001.png'), 'size':list(hidden.size),
               'receipt_hash_exact':sha(P/'source/hidden_chassis_eight_views_v001.png')==receipt['hidden_master_sha256'],
               'prompt_sha256':sha(P/'source/hidden_chassis_prompt.txt'), 'registration_sha256':sha(P/'source/hidden_registration.json'),
               'declared_generation_exec':receipt['hidden_generation_exec'],
               'registration_exec_exact':reg['generation_exec']==receipt['hidden_generation_exec'],
               'common_scale_exact':abs(reg['common_scale']-32/373)<1e-15},
    'sources':[], 'clips':[], 'preserved_down':[], 'hidden_usage':[]
}
static = load(ROOT/'art-source/ember/enemy-eight-directions-v013/static_preflight_v001/master_catalog_v013.json')
masters = {m['direction']:m for m in static['masters'] if m['unit']=='enemy_tracked_heavy'}
models = {}
source_zip = ROOT/'art-source/ember/deliveries/enemy_heavy_idle_hit_v015_v001_2026-10-07.zip'
out['reviewed_source_zip'] = {'file':source_zip.name,'sha256':sha(source_zip)}
with zipfile.ZipFile(source_zip) as z:
    for d in rig['directions']:
        f=P/f'source/{d}.png'; src=rgba(f)
        out['sources'].append({'direction':d,'sha256':sha(f), 'static_preflight_sha_exact':sha(f)==masters[d]['sha256'],
                               'receipt_sha_exact':sha(f)==receipt['source_png_hashes'][d+'.png'],
                               'v015_byte_exact':f.read_bytes()==z.read(f'source/{d}.png')})
        if d not in rig['configs']: continue
        cfg=rig['configs'][d]; own={}; counts={k:0 for k in ['fixed','tower','gun']}
        for y in range(128):
            for x in range(128):
                tr=any(inside(x+.5,y+.5,poly) for poly in cfg['track_polygons'])
                part='tower' if not tr and y<cfg['tower_bottom'] else 'fixed'
                if inside(x+.5,y+.5,cfg['gun']['housing_polygon']): part='fixed'
                if inside(x+.5,y+.5,cfg['gun']['polygon']): part='gun'
                own[(x,y)]=part
                if src.getpixel((x,y))[3]>=128: counts[part]+=1
        hr=cfg['hidden']; expected_region=reg['regions'][rig['directions'].index(d)]
        out['sources'][-1].update({'config_sha_exact':sha(f)==cfg['source_sha256'],
                                   'ownership_opaque_counts':counts,
                                   'hidden_region_exact':hr['source_rect']==expected_region,
                                   'hidden_scale_exact':hr['scale']==reg['common_scale'],
                                   'hidden_anchor_exact':hr['target_bottom']==[64,98],
                                   'hidden_y_min_exact':hr['canonical_y_min']==72})
        mask=Image.new('RGB',(128,128)); colors={'fixed':(80,190,100),'tower':(80,130,210),'gun':(220,160,60)}
        for xy,part in own.items(): mask.putpixel(xy,colors[part])
        mask.save(B/f'technical-ownership-{d}.png')
        models[d]=(src,cfg,own)

def pixel_layer(model, kind, i, x, y):
    src,cfg,own=model; state=rig['actions'][kind]; q=(x+.5,y+.5)
    pixel=(255,255,255,0); owner=None
    hr=cfg['hidden']; box=hr['source_rect']; scale=hr['scale']; w,h=box[2]*scale,box[3]*scale
    tl=(hr['target_bottom'][0]-w/2,hr['target_bottom'][1]-h)
    if tl[0]<=q[0]<tl[0]+w and tl[1]<=q[1]<tl[1]+h and q[1]>=hr['canonical_y_min'] and src.getpixel((x,y))[3]>=128:
        uv=(box[0]+(q[0]-tl[0])/scale,box[1]+(q[1]-tl[1])/scale); xy=(math.floor(uv[0]),math.floor(uv[1])); value=hidden.getpixel(xy)
        if value[3]>=128: pixel=(*value[:3],255);owner={'part':'hidden_mount','source_xy':xy,'source_uv':uv}
    poly=cfg['gun']['polygon']
    if poly and own[(x,y)]=='gun' and src.getpixel((x,y))[3]>=128:
        xs=[a[0] for a in poly];ys=[a[1] for a in poly];bounds=(min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys))
        sr=(box[0]+box[2]*.4,box[1]+box[3]*.55,box[2]*.2,box[3]*.15)
        uv=(sr[0]+min(1,max(0,(q[0]-bounds[0])/bounds[2]))*sr[2],sr[1]+min(1,max(0,(q[1]-bounds[1])/bounds[3]))*sr[3])
        xy=(math.floor(uv[0]),math.floor(uv[1]));value=hidden.getpixel(xy)
        if value[3]>=128:pixel=(*value[:3],255);owner={'part':'socket','source_xy':xy,'source_uv':uv}
    dy=state['body_y'][i]; sx,sy=x,y-dy
    if 0<=sy<128 and own[(sx,sy)]=='tower' and src.getpixel((sx,sy))[3]>=128:
        value=src.getpixel((sx,sy));r=cfg['sensor_rect'];power=state['power'][i]
        if r[0]<=sx+.5<r[0]+r[2] and r[1]<=sy+.5<r[1]+r[3]:
            value=tuple(math.floor(c*(.3+.7*power)+.5) for c in value[:3])+(255,)
        pixel=(*value[:3],255);owner={'part':'tower','source_xy':(sx,sy)}
    if own[(x,y)]=='fixed' and src.getpixel((x,y))[3]>=128:
        pixel=src.getpixel((x,y));owner={'part':'fixed','source_xy':(x,y)}
    px,py=cfg['gun']['pivot'];dx=cfg['gun']['recoil'][0]*state['recoil'][i];dy=cfg['gun']['recoil'][1]*state['recoil'][i]+state['gun_y'][i]
    angle=math.radians(state['gun_roll'][i]*cfg['gun']['droop_sign']);co=math.cos(angle);si=math.sin(angle)
    lx=q[0]-px-dx;ly=q[1]-py-dy;uv=(co*lx+si*ly+px,-si*lx+co*ly+py);xy=(math.floor(uv[0]),math.floor(uv[1]))
    if 0<=xy[0]<128 and 0<=xy[1]<128 and own[xy]=='gun' and src.getpixel(xy)[3]>=128:
        pixel=src.getpixel(xy);owner={'part':'gun','source_xy':xy,'source_uv':uv}
    return pixel,owner

for clip in cat['clips']:
    d=clip['direction'];kind=clip['action'].removesuffix('_'+d); state=rig['actions'][kind]; path=P/clip['atlas'].removeprefix('res://');atlas=rgba(path)
    cc={'action':clip['action'],'direction':d,'atlas_sha_exact':sha(path)==clip['atlas_sha256'],
        'configuration_exact':clip['frame_count']==state['frame_count'] and clip['fps']==state['fps'] and clip['loop']==state['loop'],
        'atlas_size':list(atlas.size),'frames':[]}
    for i in range(clip['frame_count']):
        fp=path.with_suffix('')/f'f{i:02d}.png';actual=rgba(fp);crop=atlas.crop((i*128,0,(i+1)*128,128)); pixels=list(actual.getdata())
        fr={'frame':i,'file':fp.relative_to(P).as_posix(),'sha_exact':sha(fp)==clip['frame_hashes'][i],
            'atlas_difference':sum(a!=b for a,b in zip(pixels,crop.getdata())),
            'nonbinary_alpha':sum(a[3] not in [0,255] for a in pixels),'size':list(actual.size),'bbox':actual.getchannel('A').getbbox()}
        if d in models:
            model=models[d];src,cfg,own=model; expect=Image.new('RGBA',(128,128),(255,255,255,0));residual=[];fixed_diffs=[];usage={'hidden_mount':[],'socket':[]};owner_counts={}
            for y in range(128):
                for x in range(128):
                    exp,owner=pixel_layer(model,kind,i,x,y);expect.putpixel((x,y),exp);got=actual.getpixel((x,y))
                    if owner:
                        owner_counts[owner['part']]=owner_counts.get(owner['part'],0)+1
                        if owner['part'] in usage:usage[owner['part']].append({'xy':[x,y],**owner,'actual_rgba':got,'cpu_rgba':exp})
                    if exp!=got:residual.append({'xy':[x,y],'cpu_rgba':exp,'actual_rgba':got,'owner':owner})
                    if own[(x,y)]=='fixed' and src.getpixel((x,y))[3]>=128 and owner and owner['part']=='fixed' and got!=src.getpixel((x,y)):
                        fixed_diffs.append([x,y])
            angle=state['gun_roll'][i]*cfg['gun']['droop_sign'];rad=math.radians(angle);co,si=math.cos(rad),math.sin(rad)
            pose=clip['poses'][i];dx=cfg['gun']['recoil'][0]*state['recoil'][i];dy=cfg['gun']['recoil'][1]*state['recoil'][i]+state['gun_y'][i]
            pose_expected={'action':kind,'direction':d,'frame':i,'body_translation':[0,state['body_y'][i]],'gun_translation':[dx,dy],
                           'gun_roll':angle,'gun_pivot':cfg['gun']['pivot'],'sensor_power':state['power'][i], 'supports':cfg['supports'],'root':[64,104]}
            exact=all(pose[k]==v for k,v in pose_expected.items()) and all(abs(a-b)<1e-6 for a,b in zip(pose['gun_basis_x']+pose['gun_basis_y'],[co,si,-si,co]))
            fr.update({'cpu_residual_count':len(residual),'cpu_residual':residual,'cpu_alpha_residual':sum(r['cpu_rgba'][3]!=r['actual_rgba'][3] for r in residual),
                       'visible_fixed_source_differences':fixed_diffs,'pose_exact':exact,'owner_counts':owner_counts,
                       'neutral_rgba_difference':sum(a!=b for a,b in zip(src.getdata(),pixels)) if i==0 else None})
            expect.save(B/f'technical-cpu-{clip["action"]}-f{i:02d}.png')
            out['hidden_usage'].append({'action':clip['action'],'frame':i,**usage})
        cc['frames'].append(fr)
    files=[path.with_suffix('')/f'f{i:02d}.png' for i in range(clip['frame_count'])]
    cc['first_last_byte_exact']=files[0].read_bytes()==files[-1].read_bytes()
    if kind=='death':
        cc['f04_f06_f07_byte_exact']=files[4].read_bytes()==files[6].read_bytes()==files[7].read_bytes()
        cc['f05_rebound_differs_from_f06']=files[5].read_bytes()!=files[6].read_bytes()
    out['clips'].append(cc)

downzip=ROOT/'art-source/ember/deliveries/enemy_sequences_v012_2026-10-06.zip'
out['down_zip_sha256']=sha(downzip)
with zipfile.ZipFile(downzip) as z:
    for c in cat['clips']:
        if c['direction']!='down':continue
        rel=c['atlas'].removeprefix('res://'); files=[rel]+[rel[:-4]+f'/f{i:02d}.png' for i in range(c['frame_count'])]
        for f in files:
            zf='assets/ember/characters/enemies_v012/'+f.removeprefix('output/')
            if zf not in z.namelist():
                candidates=[s for s in z.namelist() if s.endswith('/'+f.removeprefix('output/'))]
                assert len(candidates)==1,(f,candidates);zf=candidates[0]
            out['preserved_down'].append({'file':f,'v012_byte_exact':(P/f).read_bytes()==z.read(zf)})

(B/'technical-pixel-integrity.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
frames=[f for c in out['clips'] for f in c['frames']];nf=[f for f in frames if 'cpu_residual_count' in f]
summary={'manifest':out['manifest'],'catalog':out['catalog'],'source_all_exact':all(r['static_preflight_sha_exact'] and r['receipt_sha_exact'] and r['v015_byte_exact'] for r in out['sources']),
         'preserved_down_all_exact':all(r['v012_byte_exact'] for r in out['preserved_down']), 'frames':len(frames),'new_frames':len(nf),
         'all_hashes_exact':all(c['atlas_sha_exact'] and c['configuration_exact'] for c in out['clips']) and all(f['sha_exact'] for f in frames),
         'atlas_pixel_difference':sum(f['atlas_difference'] for f in frames),'nonbinary_alpha':sum(f['nonbinary_alpha'] for f in frames),
         'all_poses_exact':all(f['pose_exact'] for f in nf),'neutral_14_difference':sum(f['neutral_rgba_difference'] for f in nf if f['frame']==0),
         'fixed_visible_difference':sum(len(f['visible_fixed_source_differences']) for f in nf),
         'cpu_residual_total':sum(f['cpu_residual_count'] for f in nf),'cpu_alpha_residual_total':sum(f['cpu_alpha_residual'] for f in nf),
         'per_clip':[{k:v for k,v in c.items() if k!='frames'}|{'cpu_per_frame':[f['cpu_residual_count'] for f in c['frames'] if 'cpu_residual_count' in f]} for c in out['clips']]}
(B/'technical-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
