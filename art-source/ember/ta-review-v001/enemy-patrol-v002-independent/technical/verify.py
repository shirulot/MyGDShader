"""Independent read-only package, raster and kinematic checks. Outputs only here."""
from pathlib import Path
from PIL import Image
from collections import Counter
import hashlib,json,math,re,zipfile

ROOT=Path(r'E:/dev/shader/godot-shader/godot-shader-simple')
SRC=ROOT/'art-source/ember/enemy-patrol-move-v002'
OUT=Path(__file__).parent
ZIP=ROOT/'art-source/ember/deliveries/enemy_patrol_move_v002_2026-10-06.zip'
def digest(data):return hashlib.sha256(data).hexdigest()
def sha(path):return digest(path.read_bytes())
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def diff(a,b):return sum(x!=y for x,y in zip(a.getdata(),b.getdata()))
def sub(a,b):return [a[0]-b[0],a[1]-b[1]]
def length(a):return math.hypot(*a)
def rotate(v,theta):return [v[0]*math.cos(theta)-v[1]*math.sin(theta),v[0]*math.sin(theta)+v[1]*math.cos(theta)]
def roundi(a):return math.floor(a+.5) if a>=0 else math.ceil(a-.5)
def contains(point,vertices):
    x,y=point;hit=False
    for i,(a,b) in enumerate(vertices):
        c,d=vertices[i-1]
        if (b>y)!=(d>y) and x<(c-a)*(y-b)/(d-b)+a:hit=not hit
    return hit
def alpha_info(a):
    c=Counter(a.getchannel('A').getdata())
    return {'size':list(a.size),'bbox_alpha_gt0':a.getchannel('A').getbbox(),'visible':sum(n for v,n in c.items() if v>0),'partial':sum(n for v,n in c.items() if 0<v<255),'near_opaque_250_254':sum(c[v] for v in range(250,255)),'opaque':c[255],'nonzero_alpha_values':sorted(v for v in c if v),'visible_border':sum(a.getpixel((x,y))[3]>0 for y in range(a.height) for x in range(a.width) if x in (0,a.width-1) or y in (0,a.height-1))}

rig=read(SRC/'rig.json');cat=read(SRC/'output/catalog_v002.json');audit=read(SRC/'qa/pixel_audit.json')
result={'scope':'independent source, archive, exported pixels and semantics; no full visual or runtime acceptance'}
with zipfile.ZipFile(ZIP) as z:
    names=z.namelist();mf=json.loads(z.read('file_hashes.json'))
    rows=mf['files'] if isinstance(mf,dict) and 'files' in mf else mf
    result['manifest_shape']={'type':type(mf).__name__,'keys':list(mf)[:5] if isinstance(mf,dict) else [],'row_example':rows[0] if isinstance(rows,list) else None}
    if isinstance(rows,dict):rows=[{'path':p,'sha256':v} if isinstance(v,str) else dict(v,path=p) for p,v in rows.items()]
    checks=[]
    for row in rows:
        data=z.read(row['path']);current=SRC/row['path']
        size=row.get('bytes',row.get('size',row.get('size_bytes')))
        checks.append({'path':row['path'],'hash_match':digest(data)==row['sha256'],'size_match':size is None or len(data)==size,'current_hash_match':current.is_file() and sha(current)==digest(data)})
    result['archive']={'sha256':sha(ZIP),'expected_sha256':'7bca0066890706a814f569de504e4902917e20db05f50f60a1d8b623e6f061a1','bytes':ZIP.stat().st_size,'entries':len(names),'manifest_entries':len(checks),'duplicate_paths':len(names)-len(set(names)),'crc_failure':z.testzip(),'unlisted':sorted(set(names)-{r['path'] for r in rows}),'checks':checks,'forbidden':[n for n in names if '.godot/' in n or n.endswith('.import')]}

canonical=Image.open(SRC/'source/canonical.png').convert('RGBA')
atlas=Image.open(SRC/'output/move_down_v002.png').convert('RGBA')
bind=Image.open(SRC/'output/bind_pose.png').convert('RGBA')
result['source']={'sha256':sha(SRC/'source/canonical.png'),'expected_sha256':'6e2c4eb57d214de69778291bcbdc4b40dfb4a5b4881fcb33338bb5f4474f348c','canonical_template_sha256':sha(ROOT/'art-source/ember/enemy-sequences-v001/templates/enemy_patrol_canonical_down_v001.png'),'source_alpha':alpha_info(canonical),'bind_alpha':alpha_info(bind),'canonical_vs_bind_rgba_diff':diff(canonical,bind),'parts':len(rig['parts']),'unique_parts':len({p['id'] for p in rig['parts']}),'bound_rig_sha_match':sha(SRC/'rig.json')==cat['rig_sha256'],'bound_source_sha_match':sha(SRC/'source/canonical.png')==cat['source_sha256'],'bound_atlas_sha_match':sha(SRC/'output/move_down_v002.png')==cat['atlas_sha256'],'atlas_sha256':sha(SRC/'output/move_down_v002.png')}
differences=[{'xy':[x,y],'source':canonical.getpixel((x,y)),'bind':bind.getpixel((x,y))} for y in range(128) for x in range(128) if canonical.getpixel((x,y))!=bind.getpixel((x,y))]
visible=[p for p in differences if p['source'][3] or p['bind'][3]]
result['source']['bind_comparison']={'hidden_rgb_only_differences':len(differences)-len(visible),'visible_rgba_differences':len(visible),'visible_rgb_differences':sum(p['source'][:3]!=p['bind'][:3] for p in visible),'visible_alpha_differences':sum(p['source'][3]!=p['bind'][3] for p in visible),'near_opaque_max_rgb_delta':max(max(abs(a-b) for a,b in zip(p['source'][:3],p['bind'][:3])) for p in visible if p['source'][3]>=250),'samples':visible[:15]}
coverage=[];premul_fit=[];single_coverage_fit=[]
for y in range(128):
    for x in range(128):
        value=canonical.getpixel((x,y));target=bind.getpixel((x,y))
        if not value[3]:continue
        owners=[p['id'] for p in rig['parts'] if contains((x+.5,y+.5),p['polygon'])]
        count=len(owners)
        ideal_alpha=roundi(255*(1-(1-value[3]/255)**count))
        color_error=max(abs(roundi(c*target[3]/255)-b) for c,b in zip(value[:3],target[:3]))
        premul_fit.append(color_error)
        if count==1:single_coverage_fit.append(color_error)
        if count!=1 or ideal_alpha!=target[3]:coverage.append({'xy':[x,y],'parts':owners,'source':value,'bind':target,'ideal_alpha':ideal_alpha,'alpha_error':abs(ideal_alpha-target[3]),'premultiplied_color_error':color_error})
result['source']['bind_comparison'].update(premultiplication_fit_max_rgb_error=max(premul_fit),premultiplication_fit_pixels_within_1=sum(v<=1 for v in premul_fit),single_coverage_premultiply_max_error=max(single_coverage_fit),single_coverage_count=len(single_coverage_fit),visible_sample_count=len(premul_fit),overlap_source_pixels=sum(len(c['parts'])>1 for c in coverage),max_overlap_alpha_error=max(c['alpha_error'] for c in coverage),coverage_details=coverage)

# SpriteFrames contains a raw RGBA Image; parse this without importing Godot.
tres=(SRC/'output/patrol_move_frames_v002.tres').read_text(encoding='utf-8')
raw=bytes(map(int,re.search(r'PackedByteArray\(([^)]*)\)',tres).group(1).split(',')))
embedded=Image.frombytes('RGBA',(1024,128),raw)
result['sprite_frames']={'embedded_rgba_bytes':len(raw),'embedded_atlas_diff':diff(embedded,atlas),'regions':[list(map(int,m)) for m in re.findall(r'region = Rect2\((\d+), (\d+), (\d+), (\d+)\)',tres)],'speed':re.findall(r'"speed": ([\d.]+)',tres),'loop':re.findall(r'"loop": (true|false|[01])',tres),'name':re.findall(r'"name": &"([^"]+)"',tres),'durations':re.findall(r'"duration": ([\d.]+)',tres)}

frames=[];segments=[];body_roi=(54,52,74,77)
for i,pose in enumerate(cat['poses']):
    img=Image.open(SRC/f'output/f{i:02}.png').convert('RGBA')
    bob=int(pose['body_translation_px'][1])
    core=img.crop((54,52+bob,74,77+bob))
    frames.append({'frame':i,'sha256':sha(SRC/f'output/f{i:02}.png'),'atlas_diff':diff(img,atlas.crop((128*i,0,128*(i+1),128))),'alpha':alpha_info(img),'core_vs_bind_rgba_diff':diff(core,bind.crop(body_roi)),'core_vs_canonical_rgba_diff':diff(core,canonical.crop(body_roi)),'duplicate_of':[j for j in range(i) if Image.open(SRC/f'output/f{j:02}.png').convert('RGBA').tobytes()==img.tobytes()]})
    for side in ('right','left'):
        leg=pose['legs'][side];specphase=rig['phases'][i][side]
        W=leg['world_joints']
        record={'frame':i,'side':side,'support':leg['support'],'depth_world':leg['depth_world'],'lift_world':leg['lift_world'],'hip_y':leg['hip_px'][1],'knee_y':leg['knee_px'][1],'ankle_y':leg['ankle_px'][1],'sole_y':leg['sole_marker_px'][1],'ground_y':leg['projected_ground_px'][1],'sole_ground_delta':leg['sole_marker_px'][1]-leg['projected_ground_px'][1],'world_thigh_length':length(sub(W[1],W[0])),'world_shin_length':length(sub(W[2],W[1])),'phase_record_match':leg['support']==specphase['support'] and leg['depth_world']==specphase['depth'] and leg['lift_world']==specphase['lift']}
        record['projection_max_error']=max(abs(roundi(104-.75*v[0]+.35*v[1])-leg[j][1]) for v,j in zip(W,('hip_px','knee_px','ankle_px')))
        for part_name,start,end in ((side+'_thigh',leg['hip_px'],leg['knee_px']),(side+'_shin',leg['knee_px'],leg['ankle_px'])):
            part=next(p for p in rig['parts'] if p['id']==part_name);t=pose['part_transforms'][part_name]
            rest=sub(part['end'],part['pivot']);world=sub(end,start);scale=length(world)/length(rest)
            rotation=math.atan2(world[1],world[0])-math.atan2(rest[1],rest[0])
            endpoint=[a+b for a,b in zip(start,rotate([rest[0],rest[1]*scale],rotation))]
            error=length(sub(endpoint,end))
            record[part_name]={'recorded_scale':t['scale'],'computed_scale_y':scale,'scale_match':abs(scale-t['scale'][1])<1e-6,'rotation_match':abs(rotation-t['rotation_radians'])<1e-6,'position_match':start==t['position'],'rendered_end_px':endpoint,'semantic_end_px':end,'end_error_px':error}
        # The foot is translation-only; marker is the original y104 sole boundary.
        foot_t=pose['part_transforms'][side+'_foot']
        record['foot_rigid_transform_match']=foot_t['position']==leg['ankle_px'] and foot_t['scale']==[1,1] and foot_t['rotation_radians']==0
        segments.append(record)
result['contract']={'rig_canvas':rig['canvas'],'rig_root':rig['root'],'catalog_canvas':cat['canvas'],'catalog_root':cat['root'],'catalog_fps':cat['fps'],'catalog_loop':cat['loop'],'catalog_frame_count':cat['frame_count'],'atlas_size':list(atlas.size)}
result['frames']=frames;result['semantic_legs']=segments
result['playback_record']=read(SRC/'qa/gpu_playback.json')
result['observed_scale_y_range']=[min(v[k]['computed_scale_y'] for v in segments for k in (v['side']+'_thigh',v['side']+'_shin')),max(v[k]['computed_scale_y'] for v in segments for k in (v['side']+'_thigh',v['side']+'_shin'))]
result['max_semantic_end_error_px']=max(v[k]['end_error_px'] for v in segments for k in (v['side']+'_thigh',v['side']+'_shin'))
(OUT/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'archive':{k:v for k,v in result['archive'].items() if k!='checks'},'archive_failures':[c for c in checks if not all(c[k] for k in ('hash_match','size_match','current_hash_match'))],'source_bind_comparison':{k:v for k,v in result['source']['bind_comparison'].items() if k not in ('samples','coverage_details')},'sprite_frames':result['sprite_frames'],'frames':[{'frame':v['frame'],'visible':v['alpha']['visible'],'partial':v['alpha']['partial'],'alpha250_254':v['alpha']['near_opaque_250_254'],'atlas_diff':v['atlas_diff'],'core_vs_bind_diff':v['core_vs_bind_rgba_diff'],'duplicates':v['duplicate_of']} for v in frames],'scale_y_range':result['observed_scale_y_range'],'end_error_max':result['max_semantic_end_error_px'],'semantics':[{'frame':v['frame'],'side':v['side'],'support':v['support'],'sole':v['sole_y'],'ground':v['ground_y'],'lift_delta':v['sole_ground_delta'],'thigh_scale':v[v['side']+'_thigh']['computed_scale_y'],'shin_scale':v[v['side']+'_shin']['computed_scale_y'],'shin_endpoint_error':v[v['side']+'_shin']['end_error_px']} for v in segments]},ensure_ascii=False,indent=2))
