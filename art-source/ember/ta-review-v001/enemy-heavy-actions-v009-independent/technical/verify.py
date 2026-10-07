"""Incremental read-only audit of the fixed heavy actions v009 ZIP, not its active source tree."""
from pathlib import Path
from PIL import Image
from collections import Counter
import hashlib,json,math,re,zipfile,struct

ROOT=Path(r'E:/dev/shader/godot-shader/godot-shader-simple')
OUT=Path(__file__).parent
PKG=OUT/'package'
ZIP=ROOT/'art-source/ember/deliveries/enemy_heavy_actions_v009_2026-10-06.zip'
def hash_bytes(data):return hashlib.sha256(data).hexdigest()
def sha(p):return hash_bytes(Path(p).read_bytes())
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def diff(a,b):return sum(p!=q for p,q in zip(a.getdata(),b.getdata()))
def visible_diff(a,b):return sum(p[3]!=q[3] or ((p[3] or q[3]) and p[:3]!=q[:3]) for p,q in zip(a.getdata(),b.getdata()))
def sub(a,b):return [a[0]-b[0],a[1]-b[1]]
def add(a,b):return [a[0]+b[0],a[1]+b[1]]
def length(a):return math.hypot(*a)
def roundi(v):return math.floor(v+.5) if v>=0 else math.ceil(v-.5)
def f32(v):return struct.unpack('f',struct.pack('f',v))[0]
def apply(t,v):return add(t['position'],[t['basis_x'][0]*v[0]+t['basis_y'][0]*v[1],t['basis_x'][1]*v[0]+t['basis_y'][1]*v[1]])
def contains(v,poly):
    x,y=v;yes=False
    for i,(a,b) in enumerate(poly):
        c,d=poly[i-1]
        if (b>y)!=(d>y) and x<(c-a)*(y-b)/(d-b)+a:yes=not yes
    return yes
def alpha(a):
    hist=Counter(a.getchannel('A').getdata())
    return {'size':list(a.size),'bbox':a.getchannel('A').getbbox(),'visible':sum(n for v,n in hist.items() if v),'partial':sum(n for v,n in hist.items() if 0<v<255),'alpha_values':sorted(hist),'border_visible':sum(a.getpixel((x,y))[3]>0 for y in range(a.height) for x in range(a.width) if x in (0,a.width-1) or y in (0,a.height-1))}
def transform_for(rest,current,position):
    unit=[v/length(rest) for v in rest];normal=[-unit[1],unit[0]]
    axis=[v/length(rest) for v in current];target_normal=[-current[1]/length(current),current[0]/length(current)]
    return {'position':position,'basis_x':[axis[i]*unit[0]+target_normal[i]*normal[0] for i in range(2)],'basis_y':[axis[i]*unit[1]+target_normal[i]*normal[1] for i in range(2)]}
def identity(pos):return {'position':list(pos),'basis_x':[1,0],'basis_y':[0,1]}
def render_cpu(rig,texture,transforms,float32_uv=False):
    # Independent inverse affine / centre sampling. Boundary pixels can differ
    # from GPU triangle rasterization; differences are retained, never fitted away.
    img=Image.new('RGBA',(128,128));dst=img.load();src=texture.load()
    for p in sorted(rig['parts'],key=lambda p:p['z']):
        t=transforms[p['id']];a,b=t['basis_x'];c,d=t['basis_y'];det=a*d-b*c
        poly=[apply(t,sub(v,p['pivot'])) for v in p['polygon']]
        xmin=max(0,math.floor(min(v[0] for v in poly)));xmax=min(128,math.ceil(max(v[0] for v in poly)))
        ymin=max(0,math.floor(min(v[1] for v in poly)));ymax=min(128,math.ceil(max(v[1] for v in poly)))
        for y in range(ymin,ymax):
            for x in range(xmin,xmax):
                rx=x+.5-t['position'][0];ry=y+.5-t['position'][1]
                uv=[p['pivot'][0]+(d*rx-c*ry)/det,p['pivot'][1]+(-b*rx+a*ry)/det]
                if float32_uv:uv=[f32(v) for v in uv]
                if not contains(uv,p['polygon']):continue
                sx,sy=math.floor(uv[0]),math.floor(uv[1])
                v=src[sx,sy]
                if v[3]>=128:dst[x,y]=(*v[:3],255)
    return img

def rotate(angle,pos):
    a=math.radians(angle);return {'position':list(pos),'basis_x':[math.cos(a),math.sin(a)],'basis_y':[-math.sin(a),math.cos(a)]}
def linear(t,v):return [t['basis_x'][j]*v[0]+t['basis_y'][j]*v[1] for j in [0,1]]
def compose(a,b):return {'position':apply(a,b['position']),'basis_x':linear(a,b['basis_x']),'basis_y':linear(a,b['basis_y'])}
def matrix_error(a,b):return max(abs(a[k][j]-b[k][j]) for k in ['position','basis_x','basis_y'] for j in [0,1])
def sensor_texture(source,power):
    texture=source.copy();scale=.35+.65*power
    for y in [62,63]:
        for x in [64,65,66]:
            p=source.getpixel((x,y));texture.putpixel((x,y),(*[math.floor(v*scale+.5) for v in p[:3]],p[3]))
    return texture

result={'scope':'Independent heavy v009 source partition, fixed hidden mapping, actual transforms/occlusion, 14 frame resources and bound saved/cold GPU evidence; not art approval.'}
LIVE=ROOT/'art-source/ember/enemy-heavy-actions-v009'
with zipfile.ZipFile(ZIP) as z:
    names=z.namelist();manifest=json.loads(z.read('file_hashes.json'))
    assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names)
    z.extractall(PKG)
    checks=[{'path':p['path'],'sha_match':hash_bytes(z.read(p['path']))==p['sha256'],'bytes_match':len(z.read(p['path']))==p['bytes'],
        'extracted_sha_match':sha(PKG/p['path'])==p['sha256'],'current_same':sha(LIVE/p['path'])==p['sha256']} for p in manifest['files']]
    result['archive']={'sha256':sha(ZIP),'bytes':ZIP.stat().st_size,'entries':len(names),'manifest_entries':len(checks),'duplicate_paths':len(names)-len(set(names)),
        'crc_failure':z.testzip(),'unlisted':sorted(set(names)-{p['path'] for p in manifest['files']}),'checks':checks}
rig=read(PKG/'rig.json');parts={p['id']:p for p in rig['parts']};source=Image.open(PKG/'source/canonical.png').convert('RGBA');hidden=Image.open(PKG/'source/hidden_chassis_master.png').convert('RGBA');cat=read(PKG/'output/catalog_v009.json')
oldzip=ROOT/'art-source/ember/deliveries/enemy_heavy_actions_v007_2026-10-06.zip'
with zipfile.ZipFile(oldzip) as old:
    oldneutral=Image.open(__import__('io').BytesIO(old.read('output/idle_down/f00.png'))).convert('RGBA')
    result['source']={'canonical_sha256':sha(PKG/'source/canonical.png'),'canonical_same_v007':old.read('source/canonical.png')==(PKG/'source/canonical.png').read_bytes(),
        'old_v007_zip_sha256':sha(oldzip),'old_v007_frozen_sha_match':sha(oldzip)=='05350a58ef0a0e44ee19c3c6af69a2f38048f4e1c5d4ce24afae5076ece14494',
        'hidden_master_sha256':sha(PKG/'source/hidden_chassis_master.png'),'hidden_master_size':list(hidden.size),
        'catalog_source_sha_matches':cat['source_sha256']==sha(PKG/'source/canonical.png'),'catalog_rig_sha_matches':cat['rig_sha256']==sha(PKG/'rig.json')}
def region(p):return {(x,y) for y in range(128) for x in range(128) if source.getpixel((x,y))[3]>=128 and contains([x+.5,y+.5],p['polygon'])}
regions={n:region(p) for n,p in parts.items()};source_pixels={(x,y) for y in range(128) for x in range(128) if source.getpixel((x,y))[3]>=128}
repeated={p:[n for n,s in regions.items() if p in s] for p in source_pixels if sum(p in s for s in regions.values())>1}
result['partition']={'parts':rig['parts'],'part_source_pixel_counts':{n:len(p) for n,p in regions.items()},'source_visible_pixels':len(source_pixels),
    'missing_source_pixels':sorted(source_pixels-set.union(*regions.values())),'duplicate_source_pixels':[{'xy':p,'parts':ns} for p,ns in repeated.items()]}
hidden_layer=Image.new('RGBA',(128,128),(255,255,255,0));hidden_mappings=[]
sx,sy,sw,sh=rig['hidden_chassis']['source_rect'];dx,dy,dw,dh=rig['hidden_chassis']['destination_rect']
for y in range(dy,dy+dh):
    for x in range(dx,dx+dw):
        uv=[sx+(x+.5-dx)*sw/dw,sy+(y+.5-dy)*sh/dh];xx,yy=map(math.floor,uv);sample=hidden.getpixel((xx,yy));mask=source.getpixel((x,y))[3]>=128
        if sample[3]>=128 and mask:hidden_layer.putpixel((x,y),(*sample[:3],255))
        hidden_mappings.append({'xy':[x,y],'source_uv':uv,'source_xy':[xx,yy],'canonical_mask':mask,'hidden_source_alpha':sample[3]})
hidden_layer.save(OUT/'independent-hidden-layer.png')
result['hidden_mapping']={'source_rect':[sx,sy,sw,sh],'destination_rect':[dx,dy,dw,dh],'scale_xy':[dw/sw,dh/sh],
    'fixed_transform_not_per_frame':True,'visible_pixels':sum(p[3]>0 for p in hidden_layer.getdata()),'source_samples':hidden_mappings,
    'visible_outside_canonical_mask':sum(p[3]>0 and source.getpixel((x,y))[3]<128 for y in range(128) for x in range(128) for p in [hidden_layer.getpixel((x,y))])}

def owned_render(texture,transforms):
    image=hidden_layer.copy();owners={p['xy'][0]+p['xy'][1]*128:'hidden_chassis' for p in hidden_mappings if hidden_layer.getpixel(tuple(p['xy']))[3]}
    for p in sorted(rig['parts'],key=lambda p:p['z']):
        t=transforms[p['id']];a,b=t['basis_x'];c,d=t['basis_y'];det=a*d-b*c
        for y in range(128):
            for x in range(128):
                rx=x+.5-t['position'][0];ry=y+.5-t['position'][1]
                uv=[p['pivot'][0]+(d*rx-c*ry)/det,p['pivot'][1]+(-b*rx+a*ry)/det]
                if not contains(uv,p['polygon']):continue
                xx,yy=map(math.floor,uv);sample=texture.getpixel((xx,yy))
                if sample[3]>=128:image.putpixel((x,y),(*sample[:3],255));owners[x+y*128]=p['id']
    return image,owners
text=(PKG/'action_rig.gd').read_text(encoding='utf8');clips=json.JSONDecoder().raw_decode(text[text.index('{',text.index('const CLIPS')):])[0]
frames=[];poses=[];roundtrip=[];hidden_visible=[]
for action,clip in cat['actions'].items():
    atlas=Image.open(PKG/f'output/{action}_v009.png').convert('RGBA')
    for i,record in enumerate(clip['poses']):
        pose=clips[action]['poses'][i];expected={p['id']:identity(p['pivot']) for p in rig['parts']};expected['tower_shell']['position'][1]+=pose['body_y'];expected['projector']=rotate(pose['gun_angle'],add(parts['projector']['pivot'],[0,pose['gun_y']]))
        texture=source.copy();power_scale=.3+.7*pose['power']
        for y in range(69,72):
            for x in range(60,69):
                p=source.getpixel((x,y));texture.putpixel((x,y),(*[math.floor(v*power_scale+.5) for v in p[:3]],p[3]))
        actual=Image.open(PKG/f'output/{action}/f{i:02}.png').convert('RGBA');cpu,owners=owned_render(texture,record['part_transforms'])
        differences=[{'xy':[x,y],'cpu':cpu.getpixel((x,y)),'actual':actual.getpixel((x,y)),'owner':owners.get(x+y*128)} for y in range(128) for x in range(128) if cpu.getpixel((x,y))!=actual.getpixel((x,y))]
        visible_hidden=[{'xy':[p%128,p//128],'rgb':cpu.getpixel((p%128,p//128))[:3]} for p,n in owners.items() if n=='hidden_chassis']
        hidden_visible.append({'action':action,'frame':i,'count':len(visible_hidden),'points':visible_hidden})
        poses.append({'action':action,'frame':i,'expected_definition':pose,'matrix_max_error':max(matrix_error(record['part_transforms'][n],t) for n,t in expected.items()),
            'body_translation_matches':record['body_translation_px']==[0,pose['body_y']],'gun_translation_matches':record['gun_translation_px']==[0,pose['gun_y']],
            'gun_angle_matches':record['gun_angle_deg']==pose['gun_angle'],'supports_matches':record['supports']==[[36,104],[92,104]],'root_matches':record['root_px']==[64,104]})
        track_rgba=sum(actual.getpixel((x,y))!=oldneutral.getpixel((x,y)) for xs in [24,86] for y in range(64,104) for x in range(xs,xs+18))
        frames.append({'action':action,'frame':i,'alpha':alpha(actual),'cpu_full_rgba_diff':len(differences),'cpu_differences':differences,'track_roi_full_rgba_diff':track_rgba,
            'sole_band_full_rgba_diff':diff(actual.crop((24,102,104,104)),oldneutral.crop((24,102,104,104))),
            'atlas_full_rgba_diff':diff(actual,atlas.crop((i*128,0,(i+1)*128,128))),'frame_sha_catalog_matches':sha(PKG/f'output/{action}/f{i:02}.png')==clip['frame_hashes'][i]})
        for background,color in [('black',0),('white',255)]:
            pair=Image.open(PKG/f'qa/roundtrip_{action}_f{i:02}_{background}.png').convert('RGBA');left=pair.crop((0,0,384,320));right=pair.crop((384,0,768,320))
            direct=Image.alpha_composite(Image.new('RGBA',(128,128),(color,color,color,255)),actual).crop((16,32,112,112)).resize((384,320),Image.Resampling.NEAREST)
            roundtrip.append({'action':action,'frame':i,'background':background,'size':list(pair.size),'left_right_diff':diff(left,right),'left_direct_diff':diff(left,direct),'right_direct_diff':diff(right,direct)})
result['frames']=frames;result['poses']=poses;result['hidden_visible_per_frame']=hidden_visible;result['saved_gpu_pairs']=roundtrip
neutral=Image.open(PKG/'output/attack_down/f00.png').convert('RGBA')
result['neutral_source_coverage_rgb_differences']=sum((p[3]>=128)!=(n[3]==255) or (n[3]>0 and p[:3]!=n[:3]) for p,n in zip(source.getdata(),neutral.getdata()))
result['raw_canonical_to_neutral']={
    'raw_full_rgba_diff':diff(source,neutral),
    'raw_alpha_diff':sum(p[3]!=n[3] for p,n in zip(source.getdata(),neutral.getdata())),
    'both_transparent_rgb_diff':sum(p[3]==0 and n[3]==0 and p[:3]!=n[:3] for p,n in zip(source.getdata(),neutral.getdata())),
    'effective_visible_rgb_diff':sum(n[3]>0 and p[:3]!=n[:3] for p,n in zip(source.getdata(),neutral.getdata())),
    'raw_source_alpha_histogram':dict(sorted(Counter(source.getchannel('A').getdata()).items())),
    'meaning':'Raw RGBA is not identical: declared 0.5 hard coverage and transparent RGB differ; effective RGB and threshold coverage are exact.'}
result['neutral_and_recovery']={'neutral_full_rgba_same_v007':diff(neutral,oldneutral),'attack_terminal_neutral_diff':diff(neutral,Image.open(PKG/'output/attack_down/f05.png').convert('RGBA')),
    'death_initial_neutral_diff':diff(neutral,Image.open(PKG/'output/death_down/f00.png').convert('RGBA')),'death_final_hold_diff':diff(Image.open(PKG/'output/death_down/f06.png').convert('RGBA'),Image.open(PKG/'output/death_down/f07.png').convert('RGBA'))}
result['event_registration']={'attack_f03_phase':cat['actions']['attack_down']['poses'][3]['phase'],'death_f07_phase':cat['actions']['death_down']['poses'][7]['phase'],
    'explicit_event_fields_present':any(p.get('events') for c in cat['actions'].values() for p in c['poses']),'readme_f03_f07_declared':'攻击 f03 释放事件，死亡 f07 残骸保持' in (PKG/'README.md').read_text(encoding='utf8'),
    'meaning':'Release/hold time are identified by phase and README; no exact VFX spawn/source muzzle coordinate is supplied, to be registered during integration.'}

# Explain independent double-precision sampling exceptions without changing the
# render model or hiding its differences. All alternatives must be same-source
# nearest neighbours at a documented UV boundary.
sampling_exceptions=[]
for f in frames:
    pose=cat['actions'][f['action']]['poses'][f['frame']]
    for e in f['cpu_differences']:
        x,y=e['xy'];image=hidden if e['owner']=='hidden_chassis' else source
        if e['owner']=='hidden_chassis':uv=[sx+(x+.5-dx)*sw/dw,sy+(y+.5-dy)*sh/dh]
        else:
            p=parts[e['owner']];t=pose['part_transforms'][e['owner']];a,b=t['basis_x'];c,d=t['basis_y'];det=a*d-b*c;rx=x+.5-t['position'][0];ry=y+.5-t['position'][1]
            uv=[p['pivot'][0]+(d*rx-c*ry)/det,p['pivot'][1]+(-b*rx+a*ry)/det]
        xx,yy=map(math.floor,uv);candidates=[]
        for ox,oy in [(0,0),(-1,0),(1,0),(0,-1),(0,1)]:
            px,py=xx+ox,yy+oy
            if 0<=px<image.width and 0<=py<image.height and image.getpixel((px,py))[:3]==tuple(e['actual'][:3]):candidates.append([px,py])
        sampling_exceptions.append({'action':f['action'],'frame':f['frame'],'xy':[x,y],'owner':e['owner'],'source_uv':uv,
            'distance_to_integer_uv':min(abs(v-round(v)) for v in uv),'actual_rgb_matches_same_source_neighbor_pixels':candidates,
            'alpha_exact':e['cpu'][3]==e['actual'][3]})
result['sampling_exceptions']=sampling_exceptions
result['sampling_exception_summary']={'count':len(sampling_exceptions),'same_source_neighbor_match_all':all(e['actual_rgb_matches_same_source_neighbor_pixels'] for e in sampling_exceptions),
    'max_distance_to_integer_uv':max(e['distance_to_integer_uv'] for e in sampling_exceptions),'alpha_exact_all':all(e['alpha_exact'] for e in sampling_exceptions)}

tres=(PKG/'output/heavy_actions_v009.tres').read_text(encoding='utf8')
resources={m.group(3):(m.group(1),m.group(4)) for m in re.finditer(r'\[(sub_resource|resource)(?: type="([^"]+)" id="([^"]+)")?\]\n([\s\S]*?)(?=\n\[|\Z)',tres)}
animations=[]
for match in re.finditer(r'"frames": \[([\s\S]*?)\],\n"loop": ([01]),\n"name": &"([^"]+)",\n"speed": ([\d.]+)',tres):
    fs,loop,action,fps=match.groups();texture_ids=re.findall(r'"texture": SubResource\("([^"]+)"\)',fs);actual=[];regions=[];atlas=Image.open(PKG/f'output/{action}_v009.png').convert('RGBA')
    for tid in texture_ids:
        block=resources[tid][1];region=list(map(int,re.search(r'region = Rect2\((\d+), (\d+), (\d+), (\d+)\)',block).groups()));regions.append(region)
        iid=re.search(r'atlas = SubResource\("([^"]+)"\)',block).group(1);image_id=re.search(r'image = SubResource\("([^"]+)"\)',resources[iid][1]).group(1);block=resources[image_id][1]
        width=int(re.search(r'"width": (\d+)',block).group(1));height=int(re.search(r'"height": (\d+)',block).group(1));data=bytes(map(int,re.search(r'PackedByteArray\(([^)]*)\)',block).group(1).split(',')))
        image=Image.frombytes('RGBA',(width,height),data);x,y,w,h=region;actual.append(image.crop((x,y,x+w,y+h)))
    animations.append({'action':action,'fps':float(fps),'loop':loop=='1','frame_count':len(actual),'durations':list(map(float,re.findall(r'"duration": ([\d.]+)',fs))),'regions':regions,'embedded_atlas_rgba_diff':sum(diff(f,atlas.crop((i*128,0,(i+1)*128,128))) for i,f in enumerate(actual))})
result['spriteframes']=animations
receipt_path=LIVE/'qa/cold_receipt_v009.json';receipt=read(receipt_path);cold=Path(receipt['cold_workspace']);cold_report=read(receipt['actual_playback_report'])
result['cold_bindings']={'receipt_sha256':sha(receipt_path),'receipt_expected_sha_match':sha(receipt_path)=='546da28e9ed7fd1342f1cf890067b2442cde502bc16c65976ba9aebbde4dcaa9',
    'zip_sha_match':sha(ZIP)==receipt['zip_sha256'],'report_sha_matches':sha(receipt['actual_playback_report'])==receipt['playback_report_sha256'],
    'report_sha256':sha(receipt['actual_playback_report']),'report_matches_receipt_embedded':cold_report==receipt['gpu'],'catalog_bound':cold_report['catalog_sha256']==sha(PKG/'output/catalog_v009.json'),
    'core_files':[{'path':p['path'],'cold_sha_matches':sha(cold/p['path'])==p['sha256'],'fixed_package_sha_matches':sha(PKG/p['path'])==p['sha256']} for p in receipt['core_files']],
    'logs':[{'path':p['path'],'bytes':Path(p['path']).stat().st_size,'bytes_matches':Path(p['path']).stat().st_size==p['bytes'],'sha_matches':sha(p['path'])==p['sha256']} for p in receipt['logs']],
    'import_exit':receipt['import_exit'],'capture_exit':receipt['capture_exit'],'cold_report':cold_report,'independent_gpu_rerun':False}
(OUT/'bound-cold-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');(OUT/'bound-cold-playback.json').write_text(json.dumps(cold_report,ensure_ascii=False,indent=2),encoding='utf8')
served_root=ROOT/'art-source/ember/enemy-sequences-v001/previews';served=served_root/'heavy-actions-v009'
paths={'index.html':'preview.html','output/catalog_v009.json':'output/catalog_v009.json',**{f'output/{a}_v009.png':f'output/{a}_v009.png' for a in cat['actions']}}
result['served_binding']={'config':read(served_root/'preview_server.json'),'files':[{'path':p,'exists':(served/p).is_file(),'same_package_sha':sha(served/p)==sha(PKG/q) if (served/p).is_file() else False} for p,q in paths.items()]}
runtime_paths=['preview.tscn','preview.gd','output/heavy_actions_v009.tres','action_rig.gd','rig.json','source/canonical.png','source/hidden_chassis_master.png','entity_cutout.gdshader','hidden_chassis.gdshader']
result['static_dependency_closure']={'paths':[{'path':p,'exists_in_fixed_package':(PKG/p).is_file(),'manifest_bound':p in {r['path'] for r in checks}} for p in runtime_paths],
    'meaning':'Preview and rig/export source references are self-contained; this static inspection does not replace a fresh Godot import.'}
result['summary']={'manifest_all_checks':all(all(p[k] for k in ['sha_match','bytes_match','extracted_sha_match','current_same']) for p in checks),
    'cpu_full_rgba_diffs':sum(f['cpu_full_rgba_diff'] for f in frames),'track_roi_full_rgba_diffs':sum(f['track_roi_full_rgba_diff'] for f in frames),'sole_band_full_rgba_diffs':sum(f['sole_band_full_rgba_diff'] for f in frames),
    'atlas_full_rgba_diffs':sum(f['atlas_full_rgba_diff'] for f in frames),'saved_gpu_pairs':len(roundtrip),'gpu_pair_rgba_diffs':sum(p['left_right_diff']+p['left_direct_diff']+p['right_direct_diff'] for p in roundtrip),
    'all_embedded_atlas_rgba_diffs':sum(a['embedded_atlas_rgba_diff'] for a in animations),'matrix_max_error':max(p['matrix_max_error'] for p in poses)}
(OUT/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'archive':{k:v for k,v in result['archive'].items() if k!='checks'},'source':result['source'],'partition':{k:v for k,v in result['partition'].items() if k!='parts'},
    'summary':result['summary'],'hidden_mapping':{k:v for k,v in result['hidden_mapping'].items() if k!='source_samples'},'hidden_counts':[(p['action'],p['frame'],p['count']) for p in hidden_visible],
    'cpu_diff_frames':[(p['action'],p['frame'],p['cpu_full_rgba_diff']) for p in frames]},ensure_ascii=False,indent=2))

