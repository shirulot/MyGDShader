"""Incremental read-only audit of the fixed actions v005 ZIP, not its active source tree."""
from pathlib import Path
from PIL import Image
from collections import Counter
import hashlib,json,math,re,zipfile,struct

ROOT=Path(r'E:/dev/shader/godot-shader/godot-shader-simple')
OUT=Path(__file__).parent
PKG=OUT/'package'
ZIP=ROOT/'art-source/ember/deliveries/enemy_patrol_actions_v005_2026-10-06.zip'
def hash_bytes(data):return hashlib.sha256(data).hexdigest()
def sha(p):return hash_bytes(p.read_bytes())
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
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

result={'scope':'ZIP-bound incremental source, actual affine endpoints, frame binding and saved black/white rig/PNG evidence; not art acceptance'}
with zipfile.ZipFile(ZIP) as z,zipfile.ZipFile(ROOT/'art-source/ember/deliveries/enemy_patrol_move_v004_r1_2026-10-06.zip') as old:
    names=z.namelist();manifest=json.loads(z.read('file_hashes.json'));checks=[]
    for r in manifest['files']:
        data=z.read(r['path']);p=PKG/r['path']
        checks.append({'path':r['path'],'sha_match':hash_bytes(data)==r['sha256'],'bytes_match':len(data)==r['bytes'],'extracted_sha_match':p.is_file() and sha(p)==hash_bytes(data)})
    result['archive']={'sha256':sha(ZIP),'bytes':ZIP.stat().st_size,'entries':len(names),'manifest_entries':len(checks),'duplicates':len(names)-len(set(names)),'crc_failure':z.testzip(),'unlisted':sorted(set(names)-{r['path'] for r in manifest['files']}),'cache_payloads':[n for n in names if '.godot/' in n],'import_setting_files':[n for n in names if n.endswith('.import')],'checks':checks}
    inherited=['source/canonical.png','rig.json','fixed_rig.gd','entity_cutout.gdshader']
    result['inheritance']={n:z.read(n)==old.read(n) for n in inherited}
rig=read(PKG/'rig.json');catalog=read(PKG/'output/catalog_v005.json');parts={p['id']:p for p in rig['parts']}
source=Image.open(PKG/'source/canonical.png').convert('RGBA');neutral=Image.open(PKG/'output/idle_down/f00.png').convert('RGBA')
cutout=Image.new('RGBA',(128,128));pixels=cutout.load()
for y in range(128):
    for x in range(128):
        p=source.getpixel((x,y))
        if p[3]>=128:pixels[x,y]=(*p[:3],255)
source_rgb={p[:3] for p in source.getdata() if p[3]>=128}
result['source_binding']={'source_sha256':sha(PKG/'source/canonical.png'),'expected_source_match':sha(PKG/'source/canonical.png')=='6e2c4eb57d214de69778291bcbdc4b40dfb4a5b4881fcb33338bb5f4474f348c','catalog_source_match':catalog['source_sha256']==sha(PKG/'source/canonical.png'),'catalog_rig_match':catalog['rig_sha256']==sha(PKG/'rig.json'),'parts':len(parts),'neutral_visible_diff_declared_source_coverage':visible_diff(cutout,neutral),'source_coverage_pixels':alpha(cutout)['visible'],'source_alpha':alpha(source)}

# Authored joint definitions from action_rig.gd, independently recomputed with
# trigonometric math instead of accepting pose leg/transform records as truth.
definitions={'idle_down':[(0,0,0,0),(0,-1,0,0),(0,0,0,3),(0,1,0,0)],'hit_down':[(0,0,0,0),(-2,1,-5,4),(1,0,3,-2),(0,0,0,0)]}
frames=[];endpoints=[];body_checks=[];roundtrip=[];actions=[]
tres=(PKG/'output/patrol_actions_v005.tres').read_text(encoding='utf8')
resources={m.group(3):(m.group(1),m.group(4)) for m in re.finditer(r'\[(sub_resource|resource)(?: type="([^"]+)" id="([^"]+)")?\]\n([\s\S]*?)(?=\n\[|\Z)',tres)}
def body_transform(angle,pos):
    a=math.radians(angle);return {'position':pos,'basis_x':[math.cos(a),math.sin(a)],'basis_y':[-math.sin(a),math.cos(a)]}
animations=[]
for match in re.finditer(r'"frames": \[([\s\S]*?)\],\n"loop": ([01]),\n"name": &"([^"]+)",\n"speed": ([\d.]+)',tres):
    fs,loop,action,fps=match.groups();textures=re.findall(r'"texture": SubResource\("([^"]+)"\)',fs);durations=re.findall(r'"duration": ([\d.]+)',fs)
    actual_frames=[];regions=[];image_ids=[]
    for tid in textures:
        block=resources[tid][1];region=list(map(int,re.search(r'region = Rect2\((\d+), (\d+), (\d+), (\d+)\)',block).groups()));regions.append(region)
        iid=re.search(r'atlas = SubResource\("([^"]+)"\)',block).group(1)
        image_id=re.search(r'image = SubResource\("([^"]+)"\)',resources[iid][1]).group(1);image_ids.append(image_id)
        data=bytes(map(int,re.search(r'PackedByteArray\(([^)]*)\)',resources[image_id][1]).group(1).split(',')))
        image=Image.frombytes('RGBA',(512,128),data);x,y,w,h=region;actual_frames.append(image.crop((x,y,x+w,y+h)))
    atlas=Image.open(PKG/f'output/{action}_v005.png').convert('RGBA')
    animations.append({'action':action,'fps':float(fps),'loop':loop=='1','frame_count':len(textures),'durations':list(map(float,durations)),'regions':regions,'image_ids':image_ids,'embedded_frames_vs_atlas_diff':sum(diff(f,atlas.crop((i*128,0,(i+1)*128,128))) for i,f in enumerate(actual_frames))})
for action,definition in definitions.items():
    clip=catalog['actions'][action];atlas=Image.open(PKG/f'output/{action}_v005.png').convert('RGBA')
    actions.append({'action':action,'frame_count':clip['frame_count'],'fps':clip['fps'],'loop':clip['loop'],'canvas':catalog['canvas'],'root':catalog['root'],'atlas_size':list(atlas.size),'atlas_sha256':sha(PKG/f'output/{action}_v005.png'),'atlas_sha_matches_catalog':sha(PKG/f'output/{action}_v005.png')==clip['atlas_sha256']})
    for i,(sx,sy,angle,claw) in enumerate(definition):
        pose=clip['poses'][i];transforms=pose['part_transforms'];bt=body_transform(angle,[64+sx,80+sy]);expected={}
        for name in ['head_chest_pelvis','right_arm_gun','left_arm_claw']:
            pos=apply(bt,sub(parts[name]['pivot'],[64,80]));expected[name]=body_transform(angle+(claw if name=='left_arm_claw' else 0),pos)
        for side,sign in [('right',-1),('left',1)]:
            hip=apply(bt,[sign*6,0]);knee=[64+sign*7+roundi(sx*.5),90+roundi(sy*.5)];ankle=[64+sign*8,98];leg=pose['legs'][side]
            body_checks.append({'action':action,'frame':i,'side':side,'recorded_joint_max_error':max(abs(p[j]-q[j]) for p,q in zip([hip,knee,ankle],[leg['hip_px'],leg['knee_px'],leg['ankle_px']]) for j in [0,1]),'fixed_ankle_match':leg['ankle_px']==ankle,'support_and_marker_match':leg['support']==True and leg['sole_marker_px']==[ankle[0],104]})
            for kind,start,end in [('thigh',hip,knee),('shin',knee,ankle)]:
                name=f'{side}_{kind}';rest=sub(parts[name]['end'],parts[name]['pivot']);expected[name]=transform_for(rest,sub(end,start),start)
                t=transforms[name];mapped=apply(t,rest);recordedtarget=leg['knee_px'] if kind=='thigh' else leg['ankle_px']
                endpoints.append({'action':action,'frame':i,'part':name,'mapped_end':mapped,'recorded_target':recordedtarget,'actual_endpoint_error_px':length(sub(mapped,recordedtarget)),'independent_basis_error':max(abs(t[k][j]-expected[name][k][j]) for k in ['basis_x','basis_y','position'] for j in [0,1]),'axis_scale':length(sub(end,start))/length(rest)})
            expected[f'{side}_knee_cap']=identity(knee);expected[f'{side}_foot']=identity(ankle)
        actual=Image.open(PKG/f'output/{action}/f{i:02}.png').convert('RGBA');cpu=render_cpu(rig,source,transforms)
        differences=[{'xy':[x,y],'expected':cpu.getpixel((x,y)),'actual':actual.getpixel((x,y))} for y in range(128) for x in range(128) if cpu.getpixel((x,y))[3]!=actual.getpixel((x,y))[3] or ((cpu.getpixel((x,y))[3] or actual.getpixel((x,y))[3]) and cpu.getpixel((x,y))[:3]!=actual.getpixel((x,y))[:3])]
        frames.append({'action':action,'frame':i,'frame_sha256':sha(PKG/f'output/{action}/f{i:02}.png'),'frame_sha_catalog_match':sha(PKG/f'output/{action}/f{i:02}.png')==clip['frame_hashes'][i],'atlas_diff':diff(actual,atlas.crop((i*128,0,(i+1)*128,128))),'foot_roi_rgba_diff':diff(neutral.crop((50,98,79,105)),actual.crop((50,98,79,105))),'alpha':alpha(actual),'all_matrix_max_error':max(abs(transforms[n][k][j]-expected[n][k][j]) for n in expected for k in ['basis_x','basis_y','position'] for j in [0,1]),'foot_basis_identity':all(transforms[f'{s}_foot']==identity([64+sign*8,98]) for s,sign in [('right',-1),('left',1)]),'knee_basis_identity':all(transforms[f'{s}_knee_cap']['basis_x']==[1,0] and transforms[f'{s}_knee_cap']['basis_y']==[0,1] for s in ['right','left']),'new_visible_rgb_count':len({p[:3] for p in actual.getdata() if p[3]}-source_rgb),'cpu_float64_visible_diff':len(differences),'cpu_float64_differences':differences})
        for background,value in [('black',0),('white',255)]:
            pair=Image.open(PKG/f'qa/roundtrip_{action}_f{i:02}_{background}.png').convert('RGBA');left=pair.crop((0,0,256,320));right=pair.crop((256,0,512,320));direct=Image.alpha_composite(Image.new('RGBA',(128,128),(value,value,value,255)),actual).crop((32,32,96,112)).resize((256,320),Image.Resampling.NEAREST)
            roundtrip.append({'action':action,'frame':i,'background':background,'size':list(pair.size),'left_right_rgba_diff':diff(left,right),'rig_side_vs_direct_png_rgba_diff':diff(left,direct),'png_side_vs_direct_png_rgba_diff':diff(right,direct)})
result['actions']=actions;result['spriteframes_registration']=animations;result['frames']=frames;result['endpoints']=endpoints;result['joints']=body_checks;result['roundtrip_saved_images']=roundtrip
result['neutral_recovery']={'hit_f03_vs_idle_f00_rgba_diff':diff(Image.open(PKG/'output/hit_down/f03.png').convert('RGBA'),neutral),'hit_f00_vs_idle_f00_rgba_diff':diff(Image.open(PKG/'output/hit_down/f00.png').convert('RGBA'),neutral)}
serve=ROOT/'art-source/ember/enemy-sequences-v001/previews'; config=read(serve/'preview_server.json');mapped=serve/'patrol-actions-v005'; served_files={'index.html':'preview.html','output/catalog_v005.json':'output/catalog_v005.json','output/hit_down_v005.png':'output/hit_down_v005.png','output/idle_down_v005.png':'output/idle_down_v005.png'}
result['served_binding']={'config_directory':config['directory'],'config_port':config['port'],'files':[{'served':k,'package':v,'sha256':sha(mapped/k),'same_fixed_package':sha(mapped/k)==sha(PKG/v)} for k,v in served_files.items()]}
result['producer_records']={'verification_catalog_sha_matches':read(PKG/'qa/verification.json')['catalog_sha256']==sha(PKG/'output/catalog_v005.json'),'playback_catalog_sha_matches':read(PKG/'qa/gpu_playback.json')['catalog_sha256']==sha(PKG/'output/catalog_v005.json'),'playback':read(PKG/'qa/gpu_playback.json'),'independent_gpu_rerun':False}
result['summary']={'manifest_all_match':all(all(e[k] for k in ['sha_match','bytes_match','extracted_sha_match']) for e in checks),'inherited_all_match':all(result['inheritance'].values()),'endpoint_count':len(endpoints),'endpoint_max_error':max(e['actual_endpoint_error_px'] for e in endpoints),'independent_matrix_max_error':max(e['all_matrix_max_error'] for e in frames),'foot_roi_difference_total':sum(e['foot_roi_rgba_diff'] for e in frames),'atlas_frame_diff_total':sum(e['atlas_diff'] for e in frames),'partial_alpha_total':sum(e['alpha']['partial'] for e in frames),'roundtrip_count':len(roundtrip),'roundtrip_difference_total':sum(e['left_right_rgba_diff']+e['rig_side_vs_direct_png_rgba_diff']+e['png_side_vs_direct_png_rgba_diff'] for e in roundtrip),'cpu_float64_diff_total':sum(e['cpu_float64_visible_diff'] for e in frames),'new_visible_rgb_count_total':sum(e['new_visible_rgb_count'] for e in frames)}
gpu_file=OUT/'independent-gpu-evidence.json'
if gpu_file.exists():
    gpu=read(gpu_file)
    if gpu['report']['catalog_sha256']==sha(PKG/'output/catalog_v005.json'):
        result['producer_records']['independent_gpu_rerun']=True
        result['independent_gpu_evidence']=gpu_file.name
        result['summary']['independent_gpu_roundtrip_diff_total']=sum(e['differing_channels'] for e in gpu['report']['roundtrip'])
        result['summary']['new_gpu_images_vs_fixed_image_diff_total']=sum(e['gpu_rgba_diff'] for e in gpu['saved_images'])
        result['cpu_sampling_notes']=[
            {'action':'idle_down','frame':1,'screen_pixel':[56,93],'uv_float64':[56.49999997031328,93.99999965706631],'uv_float32':[56.5,94.0],'actual_rgba':[123,145,156,255],'interpretation':'GPU float32 integer nearest-sampling boundary, exact original source texel (56,94).'},
            {'action':'hit_down','frame':2,'screen_pixel':[67,70],'uv_cpu_float64':[65.99938226287408,70.38217928877548],'cpu_sample_source':[65,70],'gpu_rgb_matches_original_source':[66,70],'actual_rgba':[216,206,190,255],'interpretation':'Fresh GPU repeats stored rig/PNG match. CPU double inverse sampling differs at adjacent nearest texel boundary; precise texture-unit quantization not measured. No new visible RGB, not an export premultiplication fault.'}]
(OUT/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'archive':{k:v for k,v in result['archive'].items() if k!='checks'},'inheritance':result['inheritance'],'source_binding':result['source_binding'],'summary':result['summary'],'neutral_recovery':result['neutral_recovery'],'spriteframes':animations,'served':result['served_binding'],'cpu_differences':[{k:e[k] for k in ['action','frame','cpu_float64_differences']} for e in frames if e['cpu_float64_visible_diff']]},ensure_ascii=False,indent=2))

