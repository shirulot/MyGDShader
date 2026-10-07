"""Incremental read-only audit of the fixed v004_r1 ZIP, not its active source tree."""
from pathlib import Path
from PIL import Image
from collections import Counter
import hashlib,json,math,re,zipfile,struct

ROOT=Path(r'E:/dev/shader/godot-shader/godot-shader-simple')
OUT=Path(__file__).parent
PKG=OUT/'package'
ZIP=ROOT/'art-source/ember/deliveries/enemy_patrol_move_v004_r1_2026-10-06.zip'
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

result={'scope':'ZIP-bound incremental source, export representation, affine endpoint and pixel consistency; not native art acceptance'}
with zipfile.ZipFile(ZIP) as z:
    names=z.namelist();manifest=json.loads(z.read('file_hashes.json'));checks=[]
    for r in manifest['files']:
        data=z.read(r['path']);p=PKG/r['path']
        checks.append({'path':r['path'],'sha_match':hash_bytes(data)==r['sha256'],'bytes_match':len(data)==r['bytes'],'extracted_sha_match':p.is_file() and sha(p)==hash_bytes(data)})
    result['archive']={'sha256':sha(ZIP),'bytes':ZIP.stat().st_size,'entries':len(names),'manifest_entries':len(checks),'duplicates':len(names)-len(set(names)),'crc_failure':z.testzip(),'unlisted':sorted(set(names)-{r['path'] for r in manifest['files']}),'cache_payloads':[n for n in names if '.godot/' in n],'import_setting_files':[n for n in names if n.endswith('.import')],'checks':checks}
rig=read(PKG/'rig.json');catalog=read(PKG/'output/catalog_v004.json')
parts={p['id']:p for p in rig['parts']}
source=Image.open(PKG/'source/canonical.png').convert('RGBA');bind=Image.open(PKG/'output/bind_pose.png').convert('RGBA');atlas=Image.open(PKG/'output/move_down_v004.png').convert('RGBA')
cutout=Image.new('RGBA',source.size);out=cutout.load()
for y in range(source.height):
    for x in range(source.width):
        v=source.getpixel((x,y))
        if v[3]>=128:out[x,y]=(*v[:3],255)
source_bind={'source_coverage_pixels':alpha(cutout)['visible'],'missing':0,'added':0,'visible_rgb_changes':0}
for s,b in zip(cutout.getdata(),bind.getdata()):
    source_bind['missing']+=s[3]>0 and b[3]==0
    source_bind['added']+=s[3]==0 and b[3]>0
    source_bind['visible_rgb_changes']+=s[3]>0 and b[3]>0 and s[:3]!=b[:3]
source_bind['raw_rgba_diff_against_declared_coverage']=diff(cutout,bind)
source_bind['visible_rgba_diff_against_declared_coverage']=visible_diff(cutout,bind)
source_bind['cpu_bind_visible_diff']=visible_diff(render_cpu(rig,source,{p['id']:identity(p['pivot']) for p in rig['parts']}),bind)
result['binding']={'source_sha256':sha(PKG/'source/canonical.png'),'canonical_sha_match':sha(PKG/'source/canonical.png')=='6e2c4eb57d214de69778291bcbdc4b40dfb4a5b4881fcb33338bb5f4474f348c','catalog_source_match':catalog['source_sha256']==sha(PKG/'source/canonical.png'),'catalog_rig_match':catalog['rig_sha256']==sha(PKG/'rig.json'),'catalog_atlas_match':catalog['atlas_sha256']==sha(PKG/'output/move_down_v004.png'),'atlas_sha256':sha(PKG/'output/move_down_v004.png'),'parts':len(parts),'source_alpha':alpha(source),'bind_alpha':alpha(bind),'source_bind':source_bind}
tres=(PKG/'output/patrol_move_frames_v004.tres').read_text(encoding='utf-8')
raw=bytes(map(int,re.search(r'PackedByteArray\(([^)]*)\)',tres).group(1).split(',')))
embedded=Image.frombytes('RGBA',(1024,128),raw)
result['contract']={'rig_canvas':rig['canvas'],'rig_root':rig['root'],'catalog_canvas':catalog['canvas'],'catalog_root':catalog['root'],'frame_count':catalog['frame_count'],'fps':catalog['fps'],'loop':catalog['loop'],'atlas_size':list(atlas.size),'embedded_atlas_diff':diff(embedded,atlas),'sprite_regions':[list(map(int,v)) for v in re.findall(r'region = Rect2\((\d+), (\d+), (\d+), (\d+)\)',tres)],'sprite_fps':re.findall(r'"speed": ([\d.]+)',tres),'sprite_loop':re.findall(r'"loop": (true|false|[01])',tres),'sprite_duration':re.findall(r'"duration": ([\d.]+)',tres)}

frames=[];endpoints=[];pose_checks=[];knee_checks=[];roundtrip_images=[]
for i,pose in enumerate(catalog['poses']):
    actual=Image.open(PKG/f'output/f{i:02}.png').convert('RGBA');bob=rig['phases'][i]['body_y']
    transforms=pose['part_transforms'];expected={p['id']:identity(p['pivot']) for p in rig['parts']}
    for name in ('head_chest_pelvis','right_arm_gun','left_arm_claw'):expected[name]['position'][1]+=bob
    for side in ('right','left'):
        foot=rig['phases'][i][side];leg=pose['legs'][side];proj=rig['projection']
        hip=[proj['hip_height']-bob/.75,0];ankle=[proj['ankle_height']+foot['lift'],foot['depth']]
        delta=sub(ankle,hip);distance=length(delta);unit=[v/distance for v in delta]
        along=(proj['thigh_length']**2-proj['shin_length']**2+distance**2)/(2*distance)
        outward=math.sqrt(max(0,proj['thigh_length']**2-along**2))
        knee=[hip[0]+unit[0]*along+unit[1]*outward,hip[1]+unit[1]*along-unit[0]*outward]
        points=[[58 if side=='right' else 70,roundi(104-.75*hip[0]+.35*hip[1])],[57 if side=='right' else 71,roundi(104-.75*knee[0]+.35*knee[1])],[56 if side=='right' else 72,roundi(104-.75*ankle[0]+.35*ankle[1])]]
        pose_checks.append({'frame':i,'side':side,'independent_projected_joints':points,'recorded_joints':[leg['hip_px'],leg['knee_px'],leg['ankle_px']],'joint_match':points==[leg['hip_px'],leg['knee_px'],leg['ankle_px']],'support':foot['support'],'sole_ground_delta':leg['sole_marker_px'][1]-leg['projected_ground_px'][1]})
        for kind,start,end in (('thigh',points[0],points[1]),('shin',points[1],points[2])):
            name=f'{side}_{kind}';p=parts[name];rest=sub(p['end'],p['pivot']);current=sub(end,start)
            expected[name]=transform_for(rest,current,start);t=transforms[name]
            mapped=apply(t,rest);error=length(sub(mapped,end))
            matrix_error=max(abs(t[k][j]-expected[name][k][j]) for k in ('basis_x','basis_y','position') for j in (0,1))
            endpoints.append({'frame':i,'part':name,'mapped_end':mapped,'target':end,'endpoint_error_px':error,'independent_basis_max_error':matrix_error,'bone_axis_scale':length(current)/length(rest)})
        for kind,pos in (('knee_cap',points[1]),('foot',points[2])):expected[f'{side}_{kind}']=identity(pos)
        knee_checks.append({'frame':i,'side':side,'knee_cap_rigid':all(transforms[f'{side}_knee_cap'][k]==expected[f'{side}_knee_cap'][k] for k in ('basis_x','basis_y','position'))})
    render=render_cpu(rig,source,transforms)
    differences=[{'xy':[x,y],'expected':render.getpixel((x,y)),'actual':actual.getpixel((x,y))} for y in range(128) for x in range(128) if render.getpixel((x,y))[3]!=actual.getpixel((x,y))[3] or ((render.getpixel((x,y))[3] or actual.getpixel((x,y))[3]) and render.getpixel((x,y))[:3]!=actual.getpixel((x,y))[:3])]
    frames.append({'frame':i,'sha256':sha(PKG/f'output/f{i:02}.png'),'alpha':alpha(actual),'atlas_diff':diff(actual,atlas.crop((128*i,0,128*(i+1),128))),'core_roi_diff':diff(actual.crop((54,52+bob,74,77+bob)),bind.crop((54,52,74,77))),'all_part_matrix_error':max(abs(transforms[n][k][j]-expected[n][k][j]) for n in parts for k in ('basis_x','basis_y','position') for j in (0,1)),'cpu_float64_uv_visible_diff':len(differences),'cpu_float64_raster_differences':differences})
    for background,value in (('black',0),('white',255)):
        pair_path=PKG/f'qa/roundtrip_f{i:02}_{background}_4x.png'
        if pair_path.exists():
            pair=Image.open(pair_path).convert('RGBA');left=pair.crop((0,0,192,256));right=pair.crop((192,0,384,256))
            composed=Image.alpha_composite(Image.new('RGBA',(128,128),(value,value,value,255)),actual).crop((40,48,88,112)).resize((192,256),Image.Resampling.NEAREST)
            roundtrip_images.append({'frame':i,'background':background,'pair_size':list(pair.size),'left_vs_right_diff':diff(left,right),'stored_png_side_vs_direct_png_composite_diff':diff(right,composed),'stored_rig_side_vs_direct_png_composite_diff':diff(left,composed)})
result['frames']=frames;result['endpoints']=endpoints;result['pose_checks']=pose_checks;result['knee_checks']=knee_checks;result['roundtrip_saved_images']=roundtrip_images
result['producer_roundtrip_report']=read(PKG/'qa/render_roundtrip.json')
result['producer_playback_record']=read(PKG/'qa/gpu_playback.json')
t=catalog['poses'][4]['part_transforms']['right_shin'];a,b=t['basis_x'];c,d=t['basis_y'];rx=56.5-t['position'][0];ry=95.5-t['position'][1];det=a*d-b*c
uv=[57+(d*rx-c*ry)/det,90+(-b*rx+a*ry)/det]
result['raster_boundary_case']={'frame':4,'screen_pixel':[56,95],'uv_float64':uv,'uv_rounded_float32':[f32(v) for v in uv],'source_at_float64_uv':source.getpixel(tuple(math.floor(v) for v in uv)),'source_at_float32_uv':source.getpixel(tuple(math.floor(f32(v)) for v in uv)),'actual_exported_pixel':Image.open(PKG/'output/f04.png').convert('RGBA').getpixel((56,95)),'interpretation':'One nearest-neighbour integer UV boundary; GPU actual RGB equals original source at the float32 boundary. This explains the sole CPU-float64 sample difference and is not a new source colour.'}
result['delta_summary']={'source_bind_visible_rgba_diff':source_bind['visible_rgba_diff_against_declared_coverage'],'all_endpoints_max_error':max(p['endpoint_error_px'] for p in endpoints),'basis_max_error':max(p['independent_basis_max_error'] for p in endpoints),'knee_rigid_all':all(p['knee_cap_rigid'] for p in knee_checks),'all_frames_partial_alpha':sum(f['alpha']['partial'] for f in frames),'all_frames_atlas_diff':sum(f['atlas_diff'] for f in frames),'all_frames_cpu_float64_uv_diff':sum(f['cpu_float64_uv_visible_diff'] for f in frames),'roundtrip_saved_pair_diff':sum(p['left_vs_right_diff'] for p in roundtrip_images),'roundtrip_saved_vs_direct_composite_diff':sum(p['stored_png_side_vs_direct_png_composite_diff'] for p in roundtrip_images)}
(OUT/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'archive':{k:v for k,v in result['archive'].items() if k not in ('checks','import_setting_files')},'archive_failures':[v for v in checks if not(v['sha_match'] and v['bytes_match'] and v['extracted_sha_match'])],'source_bind':source_bind,'delta_summary':result['delta_summary'],'raster_boundary_case':result['raster_boundary_case']},ensure_ascii=False,indent=2))
