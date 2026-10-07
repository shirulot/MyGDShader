"""Incremental read-only audit of the fixed actions v008 ZIP, not its active source tree."""
from pathlib import Path
from PIL import Image
from collections import Counter
import hashlib,json,math,re,zipfile,struct

ROOT=Path(r'E:/dev/shader/godot-shader/godot-shader-simple')
OUT=Path(__file__).parent
PKG=OUT/'package'
ZIP=ROOT/'art-source/ember/deliveries/enemy_patrol_actions_v008_2026-10-06.zip'
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

result={'scope':'Independent source-notch delta, five-action 30-frame old-package comparison, SpriteFrames mapping, saved 60 GPU pairs and cold bindings. Not visual acceptance.'}
with zipfile.ZipFile(ZIP) as z:
    names=z.namelist();manifest=json.loads(z.read('file_hashes.json'))
    assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names)
    z.extractall(PKG)
    checks=[{'path':r['path'],'bytes_match':len(z.read(r['path']))==r['bytes'],'sha_match':hash_bytes(z.read(r['path']))==r['sha256'],
        'extracted_sha_match':sha(PKG/r['path'])==r['sha256'],'current_same':sha(ROOT/'art-source/ember/enemy-patrol-actions-v008'/r['path'])==r['sha256']} for r in manifest['files']]
    result['archive']={'sha256':sha(ZIP),'bytes':ZIP.stat().st_size,'entries':len(names),'manifest_entries':len(checks),'crc_failure':z.testzip(),
        'duplicate_paths':len(names)-len(set(names)),'unlisted':sorted(set(names)-{r['path'] for r in manifest['files']}),'checks':checks}

rig=read(PKG/'rig.json');parts={p['id']:p for p in rig['parts']};source=Image.open(PKG/'source/canonical.png').convert('RGBA');cat=read(PKG/'output/catalog_v008.json')
neutral=Image.open(PKG/'source/neutral_bind_v004.png').convert('RGBA')
archives={
 'move_down':('enemy_patrol_move_v004_r1_2026-10-06.zip','output/catalog_v004.json','output/move_down_v004.png'),
 'idle_down':('enemy_patrol_actions_v005_2026-10-06.zip','output/catalog_v005.json','output/idle_down_v005.png'),
 'hit_down':('enemy_patrol_actions_v005_2026-10-06.zip','output/catalog_v005.json','output/hit_down_v005.png'),
 'attack_down':('enemy_patrol_actions_v006_2026-10-06.zip','output/catalog_v006.json','output/attack_down_v006.png'),
 'death_down':('enemy_patrol_actions_v006_2026-10-06.zip','output/catalog_v006.json','output/death_down_v006.png')}
with zipfile.ZipFile(ROOT/'art-source/ember/deliveries/enemy_patrol_actions_v006_2026-10-06.zip') as z:
    oldrig=json.loads(z.read('rig.json'))
    result['source']={'canonical_same_v006':(PKG/'source/canonical.png').read_bytes()==z.read('source/canonical.png'),
        'neutral_bind_same_v006':(PKG/'source/neutral_bind_v004.png').read_bytes()==z.read('source/neutral_bind_v004.png'),
        'canonical_sha256':sha(PKG/'source/canonical.png'),'fixed_rig_same_v006':(PKG/'fixed_rig.gd').read_bytes()==z.read('fixed_rig.gd'),
        'shader_same_v006':(PKG/'entity_cutout.gdshader').read_bytes()==z.read('entity_cutout.gdshader')}
oldparts={p['id']:p for p in oldrig['parts']}
def source_region(p):return {(x,y) for y in range(128) for x in range(128) if source.getpixel((x,y))[3]>=128 and contains([x+.5,y+.5],p['polygon'])}
before_region=source_region(oldparts['left_knee_cap']);after_region=source_region(parts['left_knee_cap']);removed=before_region-after_region
result['source'].update({'only_region_delta':[p['id'] for p in rig['parts'] if p!=oldparts[p['id']]],
    'non_parts_rig_delta_keys':[k for k in set(rig)|set(oldrig) if k!='parts' and rig.get(k)!=oldrig.get(k)],
    'region_removed_source_pixels':sorted(removed),'region_added_source_pixels':sorted(after_region-before_region),
    'removed_source_is_claw':[{'xy':[x,y],'claw_contains':contains([x+.5,y+.5],parts['left_arm_claw']['polygon']),'rgba':source.getpixel((x,y))} for x,y in sorted(removed)],
    'notch_polygon':parts['left_knee_cap']['polygon'],'catalog_source_sha_match':cat['source_sha256']==sha(PKG/'source/canonical.png'),'catalog_rig_sha_match':cat['rig_sha256']==sha(PKG/'rig.json')})
def declared_clips(text):return json.JSONDecoder().raw_decode(text[text.index('{',text.index('const CLIPS')):])[0]
new_clips=declared_clips((PKG/'action_rig.gd').read_text(encoding='utf8'))
clip_parameter_checks=[]
for oldname,actions in [('enemy_patrol_actions_v005_2026-10-06.zip',['idle_down','hit_down']),('enemy_patrol_actions_v006_2026-10-06.zip',['attack_down','death_down'])]:
    with zipfile.ZipFile(ROOT/'art-source/ember/deliveries'/oldname) as oldz:
        old_clips=declared_clips(oldz.read('action_rig.gd').decode('utf8'))
        clip_parameter_checks.extend({'action':a,'declared_runtime_clip_same':new_clips[a]==old_clips[a]} for a in actions)
with zipfile.ZipFile(ROOT/'art-source/ember/deliveries/enemy_patrol_move_v004_r1_2026-10-06.zip') as oldz:
    oldmove=json.loads(oldz.read('rig.json'))
    clip_parameter_checks.append({'action':'move_down','rig_phases_same':rig['phases']==oldmove['phases'],'rig_projection_same':rig['projection']==oldmove['projection']})
result['source']['clip_parameter_checks']=clip_parameter_checks

def point_layers(position,partlist,transforms,power=1):
    result=[]
    for p in sorted(partlist,key=lambda p:p['z']):
        t=transforms[p['id']];a,b=t['basis_x'];c,d=t['basis_y'];det=a*d-b*c
        rx=position[0]+.5-t['position'][0];ry=position[1]+.5-t['position'][1]
        uv=[p['pivot'][0]+(d*rx-c*ry)/det,p['pivot'][1]+(-b*rx+a*ry)/det]
        if not contains(uv,p['polygon']):continue
        xy=(math.floor(uv[0]),math.floor(uv[1]));color=source.getpixel(xy)
        if color[3]>=128:result.append({'part':p['id'],'uv':uv,'source_xy':list(xy),'source_rgba':color})
    return result

frames=[];roundtrip=[];endpoints=[];references=[];pose_comparisons=[]
for action,clip in cat['actions'].items():
    oldname,oldcatalog_path,oldatlas_path=archives[action]
    with zipfile.ZipFile(ROOT/'art-source/ember/deliveries'/oldname) as oldz:
        oldcat=json.loads(oldz.read(oldcatalog_path));oldclip=oldcat if action=='move_down' else oldcat['actions'][action]
        oldpartlist=json.loads(oldz.read('rig.json'))['parts'];oldpartmap={p['id']:p for p in oldpartlist}
        oldatlas=Image.open(__import__('io').BytesIO(oldz.read(oldatlas_path))).convert('RGBA')
        ref=PKG/'references'/Path(oldatlas_path).name
        references.append({'action':action,'original_fixed_zip':oldname,'original_zip_sha256':sha(ROOT/'art-source/ember/deliveries'/oldname),
            'old_atlas_sha256':hash_bytes(oldz.read(oldatlas_path)),'reference_sha_match':ref.read_bytes()==oldz.read(oldatlas_path),
            'old_canonical_same':oldz.read('source/canonical.png')==(PKG/'source/canonical.png').read_bytes()})
    atlas=Image.open(PKG/f'output/{action}_v008.png').convert('RGBA')
    for i,pose in enumerate(clip['poses']):
        oldpose=oldclip['poses'][i];actual=Image.open(PKG/f'output/{action}/f{i:02}.png').convert('RGBA');before=oldatlas.crop((i*128,0,(i+1)*128,128))
        common_keys=[k for k in oldpose if k not in ['part_transforms','pose_space'] and k in pose]
        matrix_checks=[]
        for name,t in oldpose['part_transforms'].items():
            if name=='right_arm_gun' and action in ['idle_down','hit_down','move_down']:
                # Compare source UV mapping, rather than differing local origins,
                # for the inherited one-time arm split.
                for newname in ['right_arm_gun','right_upper_arm']:
                    local=sub(parts[newname]['pivot'],oldpartmap[name]['pivot']);mapped_old=apply(t,local);mapped_new=pose['part_transforms'][newname]['position']
                    matrix_checks.append({'part':newname,'old_arm_source_pivot_mapping_error':length(sub(mapped_old,mapped_new)),
                        'basis_error':max(abs(t[k][j]-pose['part_transforms'][newname][k][j]) for k in ['basis_x','basis_y'] for j in [0,1])})
            else:
                matrix_checks.append({'part':name,'error':matrix_error(t,pose['part_transforms'][name])})
        pose_comparisons.append({'action':action,'frame':i,'shared_pose_metadata_match':all(oldpose[k]==pose[k] for k in common_keys),
            'changed_common_keys':[k for k in common_keys if oldpose[k]!=pose[k]],'whole_pose_exact_v006':oldpose==pose if action in ['attack_down','death_down'] else None,'matrix_checks':matrix_checks})
        changes=[];invalid=[]
        for y in range(128):
            for x in range(128):
                b=before.getpixel((x,y));n=actual.getpixel((x,y))
                if b==n:continue
                old_layers=point_layers([x,y],oldpartlist,oldpose['part_transforms']);new_layers=point_layers([x,y],rig['parts'],pose['part_transforms'])
                top_old=old_layers[-1] if old_layers else None;top_new=new_layers[-1] if new_layers else None
                old_error=bool(top_old and top_old['part']=='left_knee_cap' and tuple(top_old['source_xy']) in removed)
                # Use the unchanged prior export clear pixel for transparent RGB.
                # Godot's Color.TRANSPARENT keeps white RGB at alpha zero here;
                # deletion must match that representation, not an invented black.
                expected_after=(*top_new['source_rgba'][:3],255) if top_new else before.getpixel((0,0))
                entry={'xy':[x,y],'before':b,'after':n,'old_top_source':top_old,'new_top_source':top_new,
                    'only_wrong_knee_source_removed':old_error,'old_rgb_matches_canonical':bool(top_old and b[:3]==tuple(top_old['source_rgba'][:3])),
                    'new_matches_source_or_transparent':expected_after==n}
                changes.append(entry)
                if not old_error or expected_after!=n:invalid.append(entry)
        record={'action':action,'frame':i,'full_rgba_change_count':len(changes),'changes':changes,'invalid_change_count':len(invalid),
            'legal_visible_to_different_rgb_count':sum(c['before'][3]>0 and c['after'][3]>0 and c['before'][:3]!=c['after'][:3] for c in changes),
            'deleted_visible_count':sum(c['before'][3]>0 and c['after'][3]==0 for c in changes),'added_visible_count':sum(c['before'][3]==0 and c['after'][3]>0 for c in changes),
            'atlas_full_rgba_diff':diff(actual,atlas.crop((i*128,0,(i+1)*128,128))),'hash_catalog_matches':sha(PKG/f'output/{action}/f{i:02}.png')==clip['frame_hashes'][i],
            'alpha':alpha(actual),'support_foot_roi_diff':diff(actual.crop((50,98,79,105)),neutral.crop((50,98,79,105))) if action!='move_down' and (action!='death_down' or i<=2) else None}
        frames.append(record)
        for p in rig['parts']:
            if 'end' not in p:continue
            mapped=apply(pose['part_transforms'][p['id']],sub(p['end'],p['pivot']))
            target=pose['arms']['right']['elbow_px'] if p['id']=='right_upper_arm' else pose['legs'][p['id'].split('_')[0]]['knee_px' if p['id'].endswith('thigh') else 'ankle_px']
            endpoints.append({'action':action,'frame':i,'part':p['id'],'error_px':length(sub(mapped,target))})
        for background,color in [('black',0),('white',255)]:
            pair=Image.open(PKG/f'qa/roundtrip_{action}_f{i:02}_{background}.png').convert('RGBA')
            direct=Image.alpha_composite(Image.new('RGBA',(128,128),(color,color,color,255)),actual).crop((32,32,120,112)).resize((352,320),Image.Resampling.NEAREST)
            left=pair.crop((0,0,352,320));right=pair.crop((352,0,704,320))
            roundtrip.append({'action':action,'frame':i,'background':background,'size':list(pair.size),'left_right_diff':diff(left,right),'left_direct_diff':diff(left,direct),'right_direct_diff':diff(right,direct)})
result['references']=references;result['frames']=frames;result['poses']=pose_comparisons;result['roundtrip_saved']=roundtrip;result['endpoints']=endpoints

# Independently resolve embedded SpriteFrames image bytes to the PNG atlas.
tres=(PKG/'output/patrol_actions_v008.tres').read_text(encoding='utf8')
resources={m.group(3):(m.group(1),m.group(4)) for m in re.finditer(r'\[(sub_resource|resource)(?: type="([^"]+)" id="([^"]+)")?\]\n([\s\S]*?)(?=\n\[|\Z)',tres)}
animations=[]
for match in re.finditer(r'"frames": \[([\s\S]*?)\],\n"loop": ([01]),\n"name": &"([^"]+)",\n"speed": ([\d.]+)',tres):
    fs,loop,action,fps=match.groups();texture_ids=re.findall(r'"texture": SubResource\("([^"]+)"\)',fs);actual=[];regions=[];atlas=Image.open(PKG/f'output/{action}_v008.png').convert('RGBA')
    for tid in texture_ids:
        block=resources[tid][1];region=list(map(int,re.search(r'region = Rect2\((\d+), (\d+), (\d+), (\d+)\)',block).groups()));regions.append(region)
        iid=re.search(r'atlas = SubResource\("([^"]+)"\)',block).group(1);image_id=re.search(r'image = SubResource\("([^"]+)"\)',resources[iid][1]).group(1);block=resources[image_id][1]
        width=int(re.search(r'"width": (\d+)',block).group(1));height=int(re.search(r'"height": (\d+)',block).group(1));data=bytes(map(int,re.search(r'PackedByteArray\(([^)]*)\)',block).group(1).split(',')))
        image=Image.frombytes('RGBA',(width,height),data);x,y,w,h=region;actual.append(image.crop((x,y,x+w,y+h)))
    animations.append({'action':action,'fps':float(fps),'loop':loop=='1','frame_count':len(actual),'durations':list(map(float,re.findall(r'"duration": ([\d.]+)',fs))),'regions':regions,'embedded_vs_atlas_full_rgba_diff':sum(diff(f,atlas.crop((i*128,0,(i+1)*128,128))) for i,f in enumerate(actual))})
result['spriteframes']=animations
result['recovery_hold']={'neutral_starts':[{'action':a,'diff':diff(Image.open(PKG/f'output/{a}/f00.png').convert('RGBA'),neutral)} for a in cat['actions'] if a!='move_down'],
    'attack_end_neutral_diff':diff(Image.open(PKG/'output/attack_down/f05.png').convert('RGBA'),neutral),'hit_end_neutral_diff':diff(Image.open(PKG/'output/hit_down/f03.png').convert('RGBA'),neutral),
    'death_final_hold_diff':diff(Image.open(PKG/'output/death_down/f06.png').convert('RGBA'),Image.open(PKG/'output/death_down/f07.png').convert('RGBA'))}
result['events']=[{'action':a,'frame':p['frame'],'events':p.get('events',[])} for a,c in cat['actions'].items() for p in c['poses'] if p.get('events')]
served_root=ROOT/'art-source/ember/enemy-sequences-v001/previews';served=served_root/'patrol-actions-v008'
bindings={'index.html':'preview.html','output/catalog_v008.json':'output/catalog_v008.json',**{f'output/{a}_v008.png':f'output/{a}_v008.png' for a in cat['actions']}}
result['served_binding']={'config':read(served_root/'preview_server.json'),'files':[{'served':k,'package':v,'same_sha':sha(served/k)==sha(PKG/v),'sha256':sha(PKG/v)} for k,v in bindings.items()]}
result['producer_bound_reports']={name:{'sha256':sha(PKG/f'qa/{name}.json'),'catalog_sha_matches':read(PKG/f'qa/{name}.json')['catalog_sha256']==sha(PKG/'output/catalog_v008.json')} for name in ['verification','gpu_playback']}
receipt_path=ROOT/'art-source/ember/enemy-patrol-actions-v008/qa/cold_receipt_v008.json';receipt=read(receipt_path);cold=Path(receipt['cold_workspace'])
cold_playback=read(receipt['actual_playback_report']);cold_core=[];logchecks=[]
for p in receipt['core_files']:
    cold_core.append({'path':p['path'],'receipt_digest':p['sha256'],'cold_sha_match':sha(cold/p['path'])==p['sha256'],'package_sha_match':sha(PKG/p['path'])==p['sha256']})
for p in receipt['logs']:
    f=Path(p['path']);logchecks.append({'path':p['path'],'size':f.stat().st_size,'sha_match':sha(f)==p['sha256'],'bytes_match':f.stat().st_size==p['bytes']})
result['cold_evidence_binding']={'receipt_sha256':sha(receipt_path),'receipt_expected_sha_match':sha(receipt_path)=='e00b906726c4afb3a7086d033ffd5c77a3ceccf23db0ec57f865b86646842d44',
    'zip_sha_match':sha(ZIP)==receipt['zip_sha256'],'core_files':cold_core,'logs':logchecks,
    'cold_report_sha256':sha(receipt['actual_playback_report']),
    'cold_report_sha_match':sha(receipt['actual_playback_report'])==receipt['playback_report_sha256']=='09511b30c3def57f1b1a6d28c9ca433529b67c5e819c27fdf453e69f02a0455c',
    'cold_report_embedded_receipt_equal':cold_playback==receipt['gpu'],'catalog_sha_bound':cold_playback['catalog_sha256']==sha(PKG/'output/catalog_v008.json'),
    'import_exit':receipt['import_exit'],'capture_exit':receipt['capture_exit'],'cold_playback':cold_playback,'independent_godot_rerun':False,
    'cold_frozen_frame_sha_match':[sha(cold/f'output/{f["action"]}/f{f["frame"]:02}.png')==sha(PKG/f'output/{f["action"]}/f{f["frame"]:02}.png') for f in frames]}
(OUT/'bound-cold-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'bound-cold-playback.json').write_text(json.dumps(cold_playback,ensure_ascii=False,indent=2),encoding='utf8')
# Check static page image paths including the ten contact images used on
# action/background changes. No browser or network access is needed.
result['served_binding']['contact_files']=[{'path':f'qa/{a}_{b}_4x.png','package_and_served_sha_match':sha(served/f'qa/{a}_{b}_4x.png')==sha(PKG/f'qa/{a}_{b}_4x.png')} for a in cat['actions'] for b in ['black','white']]
dependency_checks=[]
for f in [PKG/'project.godot',PKG/'preview.tscn',PKG/'preview.gd',PKG/'action_rig.gd',PKG/'fixed_rig.gd']:
    for p in re.findall(r'"(res://[^"]+)"',f.read_text(encoding='utf8')):
        dependency_checks.append({'declaring':f.name,'resource':p,'package_exists':(PKG/p.removeprefix('res://')).is_file()})
result['runtime_dependencies']=dependency_checks
result['summary']={'all_manifest_checks':all(all(c[k] for k in ['bytes_match','sha_match','extracted_sha_match','current_same']) for c in checks),
    'total_full_rgba_changed_pixels':sum(f['full_rgba_change_count'] for f in frames),'invalid_change_count':sum(f['invalid_change_count'] for f in frames),
    'visible_rgb_changes':sum(f['legal_visible_to_different_rgb_count'] for f in frames),'visible_additions':sum(f['added_visible_count'] for f in frames),
    'visible_deletions':sum(f['deleted_visible_count'] for f in frames),'roundtrip_count':len(roundtrip),
    'roundtrip_diffs_total':sum(r['left_right_diff']+r['left_direct_diff']+r['right_direct_diff'] for r in roundtrip),
    'endpoints':len(endpoints),'maximum_endpoint_error':max(e['error_px'] for e in endpoints),
    'old_shared_metadata_all_match':all(p['shared_pose_metadata_match'] for p in pose_comparisons),
    'combat_whole_pose_exact':all(p['whole_pose_exact_v006'] for p in pose_comparisons if p['whole_pose_exact_v006'] is not None),
    'all_embedded_atlas_diff':sum(a['embedded_vs_atlas_full_rgba_diff'] for a in animations)}
(OUT/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'source':result['source'],'summary':result['summary'],'action_changes':{a:[f['full_rgba_change_count'] for f in frames if f['action']==a] for a in cat['actions']},
    'invalid_change_frames':[(f['action'],f['frame']) for f in frames if f['invalid_change_count']], 'served':result['served_binding']},ensure_ascii=False,indent=2))

