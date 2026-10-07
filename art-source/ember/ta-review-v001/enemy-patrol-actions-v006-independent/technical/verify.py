"""Incremental read-only audit of the fixed actions v006 ZIP, not its active source tree."""
from pathlib import Path
from PIL import Image
from collections import Counter
import hashlib,json,math,re,zipfile,struct

ROOT=Path(r'E:/dev/shader/godot-shader/godot-shader-simple')
OUT=Path(__file__).parent
PKG=OUT/'package'
ZIP=ROOT/'art-source/ember/deliveries/enemy_patrol_actions_v006_2026-10-06.zip'
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

result={'scope':'Independent fixed archive, source segmentation, actual transforms/endpoints, PNG/SpriteFrames and saved rig/PNG ground evidence; not art acceptance.'}
with zipfile.ZipFile(ZIP) as z,zipfile.ZipFile(ROOT/'art-source/ember/deliveries/enemy_patrol_actions_v005_2026-10-06.zip') as old:
    names=z.namelist();manifest=json.loads(z.read('file_hashes.json'));checks=[]
    for r in manifest['files']:
        b=z.read(r['path']);checks.append({'path':r['path'],'sha_match':hash_bytes(b)==r['sha256'],'bytes_match':len(b)==r['bytes'],'extracted_sha_match':sha(PKG/r['path'])==r['sha256']})
    result['archive']={'sha256':sha(ZIP),'bytes':ZIP.stat().st_size,'entries':len(names),'manifest_entries':len(checks),'duplicates':len(names)-len(set(names)),'crc_failure':z.testzip(),'unlisted':sorted(set(names)-{r['path'] for r in manifest['files']}),'cache_payloads':[n for n in names if '.godot/' in n],'import_setting_files':[n for n in names if n.endswith('.import')],'checks':checks}
    result['inheritance']={'canonical_same_v005':z.read('source/canonical.png')==old.read('source/canonical.png'),'fixed_rig_same_v005':z.read('fixed_rig.gd')==old.read('fixed_rig.gd')}
    previous_rig=json.loads(old.read('rig.json'));previous_parts={p['id']:p for p in previous_rig['parts']}
    result['export_delta_only_version_paths_contact_crop']=old.read('export.gd').decode('utf8').replace('v005','v006').replace('V005','V006').replace('64*count','88*count').replace('index*128+32,32,64,80','index*128+32,32,88,80').replace('index*64,0','index*88,0').replace('count*256','count*352').replace('IDLE_HIT','ATTACK_DEATH')==z.read('export.gd').decode('utf8')
old_packages={'enemy_sequences_v001_2026-10-06.zip':'cf49b8c85a74a36654e280a44b371ed12d99f1130a4ef407b784720c68d358da','enemy_patrol_move_v004_r1_2026-10-06.zip':'33792f03eb316f7dc82618e226da2eddb9491d504b6803636d04c9e3c7633608','enemy_patrol_actions_v005_2026-10-06.zip':'6a3687783823cfd3e9db4b5c04d26b47c91a70df825ec74f8d195378b6c01468'}
result['frozen_previous_archives']=[{'path':n,'sha256':sha(ROOT/'art-source/ember/deliveries'/n),'matches_reviewed_sha':sha(ROOT/'art-source/ember/deliveries'/n)==s} for n,s in old_packages.items()]
rig=read(PKG/'rig.json');cat=read(PKG/'output/catalog_v006.json');parts={p['id']:p for p in rig['parts']};source=Image.open(PKG/'source/canonical.png').convert('RGBA');neutral=Image.open(PKG/'source/neutral_bind_v004.png').convert('RGBA')
oldgun=previous_parts['right_arm_gun'];upper=parts['right_upper_arm'];forearm=parts['right_arm_gun']
def pixels_covered(p):return {(x,y) for y in range(128) for x in range(128) if source.getpixel((x,y))[3]>=128 and contains([x+.5,y+.5],p['polygon'])}
old_arm=pixels_covered(oldgun);upper_arm=pixels_covered(upper);forearm_arm=pixels_covered(forearm)
result['source_segmentation']={'canonical_sha256':sha(PKG/'source/canonical.png'),'canonical_sha_match':sha(PKG/'source/canonical.png')=='6e2c4eb57d214de69778291bcbdc4b40dfb4a5b4881fcb33338bb5f4474f348c','parts':len(parts),'unchanged_other_ten_parts':{k:parts[k]==p for k,p in previous_parts.items() if k!='right_arm_gun'},'old_arm_source_pixels':len(old_arm),'upper_source_pixels':len(upper_arm),'forearm_source_pixels':len(forearm_arm),'missing_visible_source_pixels':sorted(old_arm-(upper_arm|forearm_arm)),'added_visible_source_pixels':sorted((upper_arm|forearm_arm)-old_arm),'declared_seam_overlap_pixels':sorted(upper_arm&forearm_arm),'neutral_bind_sha256':sha(PKG/'source/neutral_bind_v004.png'),'catalog_source_match':cat['source_sha256']==sha(PKG/'source/canonical.png'),'catalog_rig_match':cat['rig_sha256']==sha(PKG/'rig.json')}
with zipfile.ZipFile(ROOT/'art-source/ember/deliveries/enemy_patrol_move_v004_r1_2026-10-06.zip') as old:
    result['source_segmentation']['neutral_bind_same_v004']=hash_bytes(old.read('output/bind_pose.png'))==sha(PKG/'source/neutral_bind_v004.png')

# SpriteFrames resource graph independently resolves embedded images to action
# frames. Never dump the large PackedByteArray into tool output.
tres=(PKG/'output/patrol_actions_v006.tres').read_text(encoding='utf8')
resources={m.group(3):(m.group(1),m.group(4)) for m in re.finditer(r'\[(sub_resource|resource)(?: type="([^"]+)" id="([^"]+)")?\]\n([\s\S]*?)(?=\n\[|\Z)',tres)}
animations=[]
for match in re.finditer(r'"frames": \[([\s\S]*?)\],\n"loop": ([01]),\n"name": &"([^"]+)",\n"speed": ([\d.]+)',tres):
    fs,loop,action,fps=match.groups();texture_ids=re.findall(r'"texture": SubResource\("([^"]+)"\)',fs);actual=[];regions=[];atlas=Image.open(PKG/f'output/{action}_v006.png').convert('RGBA')
    for tid in texture_ids:
        block=resources[tid][1];region=list(map(int,re.search(r'region = Rect2\((\d+), (\d+), (\d+), (\d+)\)',block).groups()));regions.append(region)
        iid=re.search(r'atlas = SubResource\("([^"]+)"\)',block).group(1);image_id=re.search(r'image = SubResource\("([^"]+)"\)',resources[iid][1]).group(1);block=resources[image_id][1]
        width=int(re.search(r'"width": (\d+)',block).group(1));height=int(re.search(r'"height": (\d+)',block).group(1));data=bytes(map(int,re.search(r'PackedByteArray\(([^)]*)\)',block).group(1).split(',')))
        image=Image.frombytes('RGBA',(width,height),data);x,y,w,h=region;actual.append(image.crop((x,y,x+w,y+h)))
    animations.append({'action':action,'fps':float(fps),'loop':loop=='1','frame_count':len(actual),'durations':list(map(float,re.findall(r'"duration": ([\d.]+)',fs))),'regions':regions,'embedded_frames_vs_atlas_diff':sum(diff(f,atlas.crop((i*128,0,(i+1)*128,128))) for i,f in enumerate(actual))})
result['spriteframes']=animations

attack=[(0,[0,0],0),(0,[-1,-1],-3),(1,[-1,-3],-5),(0,[-1,-4],-5),(1,[-1,-2],-3),(0,[0,0],0)]
death=[(0,0,0,[64,80],True),(2,5,0,[64,82],True),(5,12,0,[64,85],True),(8,22,22,[66,86],False),(8,30,50,[68,85],False),(8,35,78,[70,89],False),(8,35,88,[70,90],False),(8,35,88,[70,90],False)]
frames=[];endpoints=[];poses=[];roundtrip=[];sensor_checks=[]
for action,clip in cat['actions'].items():
    atlas=Image.open(PKG/f'output/{action}_v006.png').convert('RGBA')
    assert sha(PKG/f'output/{action}_v006.png')==clip['atlas_sha256']
    for i,pose in enumerate(clip['poses']):
        if action=='attack_down':by,elbow_delta,claw=attack[i];fold=0;roll=0;origin=[64,80+by];support=True;power=1.0
        else:by,fold,roll,origin,support=death[i];claw=fold;power=max(0,1-i*.4)
        expected={p['id']:identity(p['pivot']) for p in rig['parts']}
        for n in ['head_chest_pelvis','left_arm_claw','right_arm_gun','right_upper_arm']:expected[n]['position'][1]+=by
        legpoints={}
        for side,sign in [('right',-1),('left',1)]:
            hip=[64+sign*6,80+by];knee=[64+sign*7,90+roundi(by*.6)];ankle=[64+sign*8,98];legpoints[side]={'hip':hip,'knee':knee,'ankle':ankle}
            for kind,start,end in [('thigh',hip,knee),('shin',knee,ankle)]:
                name=f'{side}_{kind}';rest=sub(parts[name]['end'],parts[name]['pivot']);expected[name]=transform_for(rest,sub(end,start),start)
            expected[f'{side}_knee_cap']=identity(knee);expected[f'{side}_foot']=identity(ankle)
        shoulder=[51,69+by];elbow=[48,77+by]
        if action=='attack_down':elbow=add(elbow,elbow_delta);expected['right_arm_gun']=identity(elbow)
        else:elbow=apply(rotate(-fold,shoulder),[-3,8]);expected['right_arm_gun']=rotate(-fold,elbow)
        expected['right_upper_arm']=transform_for(sub(upper['end'],upper['pivot']),sub(elbow,shoulder),shoulder)
        expected['left_arm_claw']=rotate(claw,add(parts['left_arm_claw']['pivot'],[0,by]))
        fall=rotate(roll,origin);fall['position']=sub(origin,linear(fall,[64,80+by]))
        expected={n:compose(fall,t) for n,t in expected.items()}
        transforms=pose['part_transforms'];joint_error=0
        for side in legpoints:
            leg=pose['legs'][side]
            for name in ['hip','knee','ankle']:
                p=apply(fall,legpoints[side][name]);joint_error=max(joint_error,max(abs(p[j]-leg[name+'_px'][j]) for j in [0,1]))
            assert leg['support']==support
        for part in rig['parts']:
            if 'end' not in part:continue
            t=transforms[part['id']];rest=sub(part['end'],part['pivot']);mapped=apply(t,rest)
            if part['id']=='right_upper_arm':target=pose['arms']['right']['elbow_px']
            else:side=part['id'].split('_')[0];target=pose['legs'][side]['knee_px' if part['id'].endswith('thigh') else 'ankle_px']
            endpoints.append({'action':action,'frame':i,'part':part['id'],'mapped_end':mapped,'target':target,'endpoint_error_px':length(sub(mapped,target)),'matrix_error':matrix_error(t,expected[part['id']])})
        arms=pose['arms']['right'];arms_error=max(abs(a[j]-b[j]) for a,b in [(apply(fall,shoulder),arms['shoulder_px']),(apply(fall,elbow),arms['elbow_px'])] for j in [0,1])
        actual=Image.open(PKG/f'output/{action}/f{i:02}.png').convert('RGBA');texture=sensor_texture(source,float(pose['sensor_power']));cpu=render_cpu(rig,texture,transforms)
        differences=[{'xy':[x,y],'expected':cpu.getpixel((x,y)),'actual':actual.getpixel((x,y))} for y in range(128) for x in range(128) if cpu.getpixel((x,y))[3]!=actual.getpixel((x,y))[3] or ((cpu.getpixel((x,y))[3] or actual.getpixel((x,y))[3]) and cpu.getpixel((x,y))[:3]!=actual.getpixel((x,y))[:3])]
        allowed={p[:3] for p in texture.getdata() if p[3]>=128};unknown={p[:3] for p in actual.getdata() if p[3]}-allowed
        ground={}
        if action=='death_down':
            landmark=apply(transforms['left_arm_claw'],[0,-2]);independent=apply(expected['left_arm_claw'],[0,-2]);lx,ly=map(math.floor,landmark)
            ground={'actual_transform_landmark':landmark,'independent_landmark':independent,'recorded_landmark':pose['shoulder_contact_landmark_px'],'landmark_record_error':length(sub(landmark,pose['shoulder_contact_landmark_px'])),'source_landmark_alpha':source.getpixel((77,67))[3],'png_alpha_at_landmark_pixel':actual.getpixel((lx,ly))[3] if 0<=lx<128 and 0<=ly<128 else None,'ground_y':pose['ground_y'],'landmark_to_ground':pose['ground_y']-landmark[1],'visible_bottom_edge':alpha(actual)['bbox'][3],'visible_pixels_below_y104':sum(actual.getpixel((x,y))[3]>0 for y in range(104,128) for x in range(128))}
        if action=='death_down' and i<=2:
            comparisons=[]
            for y in [62,63]:
                for x in [64,65,66]:
                    expected_rgb=texture.getpixel((x,y))[:3];actual_rgb=actual.getpixel((x,y+by))[:3];comparisons.append({'source':[x,y],'output':[x,y+by],'expected_rgb':expected_rgb,'actual_rgb':actual_rgb,'match':expected_rgb==actual_rgb})
            sensor_checks.append({'frame':i,'power':pose['sensor_power'],'comparisons':comparisons})
        poses.append({'action':action,'frame':i,'pose_definition':pose['pose_definition'],'all_matrix_error':max(matrix_error(transforms[n],expected[n]) for n in parts),'joint_error':joint_error,'arms_error':arms_error,'sensor_power_expected':power,'sensor_power_error':abs(power-pose['sensor_power']),'ground':ground})
        frames.append({'action':action,'frame':i,'alpha':alpha(actual),'frame_sha_catalog_match':sha(PKG/f'output/{action}/f{i:02}.png')==clip['frame_hashes'][i],'atlas_diff':diff(actual,atlas.crop((i*128,0,(i+1)*128,128))),'support_phase':support,'foot_roi_rgba_diff':diff(actual.crop((50,98,79,105)),neutral.crop((50,98,79,105))),'cpu_float64_visible_diff':len(differences),'cpu_differences':differences,'visible_rgb_outside_declared_source_and_sensor_colors':sorted(unknown)})
        for background,value in [('black',0),('white',255)]:
            pair=Image.open(PKG/f'qa/roundtrip_{action}_f{i:02}_{background}.png').convert('RGBA');left=pair.crop((0,0,352,320));right=pair.crop((352,0,704,320));direct=Image.alpha_composite(Image.new('RGBA',(128,128),(value,value,value,255)),actual).crop((32,32,120,112)).resize((352,320),Image.Resampling.NEAREST)
            roundtrip.append({'action':action,'frame':i,'background':background,'size':list(pair.size),'left_right_rgba_diff':diff(left,right),'rig_side_vs_direct_png_rgba_diff':diff(left,direct),'png_side_vs_direct_png_rgba_diff':diff(right,direct)})
result['actions']={k:{x:v for x,v in clip.items() if x not in ['poses','pixel_reports','frame_hashes']} for k,clip in cat['actions'].items()};result['frames']=frames;result['poses']=poses;result['endpoints']=endpoints;result['sensor_native_checks']=sensor_checks;result['roundtrip_saved_images']=roundtrip
attackrelease=cat['actions']['attack_down']['poses'][3];event=attackrelease['events'][0];result['release_event']={'recorded':event,'actual_muzzle':apply(attackrelease['part_transforms']['right_arm_gun'],sub([47,89],forearm['pivot'])),'source_muzzle_alpha':source.getpixel((47,89))[3]}
result['recovery_hold']={'attack_f00_neutral_diff':diff(Image.open(PKG/'output/attack_down/f00.png').convert('RGBA'),neutral),'attack_f05_neutral_diff':diff(Image.open(PKG/'output/attack_down/f05.png').convert('RGBA'),neutral),'death_f00_neutral_diff':diff(Image.open(PKG/'output/death_down/f00.png').convert('RGBA'),neutral),'death_f06_f07_diff':diff(Image.open(PKG/'output/death_down/f06.png').convert('RGBA'),Image.open(PKG/'output/death_down/f07.png').convert('RGBA'))}
serve=ROOT/'art-source/ember/enemy-sequences-v001/previews';mapped=serve/'patrol-actions-v006';config=read(serve/'preview_server.json');served={'index.html':'preview.html','output/catalog_v006.json':'output/catalog_v006.json','output/attack_down_v006.png':'output/attack_down_v006.png','output/death_down_v006.png':'output/death_down_v006.png'}
result['served_binding']={'config':config,'files':[{'served':k,'package':v,'same_fixed_sha':sha(mapped/k)==sha(PKG/v),'sha256':sha(mapped/k)} for k,v in served.items()]}
result['producer_report_binding']={n:read(PKG/f'qa/{n}.json')['catalog_sha256']==sha(PKG/'output/catalog_v006.json') for n in ['verification','gpu_playback']}
result['independent_gpu_rerun']=False
result['isolated_pixel_source_ownership']={
    'source_pixels':[{ 'xy':[76,y], 'rgba':source.getpixel((76,y)),
        'regions':[p['id'] for p in rig['parts'] if contains([76.5,y+.5],p['polygon'])] }
        for y in [87,88,89]],
    'diagnostic_file':'pixel-ownership.json',
    'cause':'left_knee_cap rectangle duplicates three pixels belonging to the inner claw edge; rotations expose the duplicate as an isolated strip.',
    'minimal_fix':'Exclude only these three non-knee source pixels from the knee region once, then regenerate both actions and their validation assets.'}
result['summary']={'manifest_all_match':all(all(e[k] for k in ['sha_match','bytes_match','extracted_sha_match']) for e in checks),'source_arm_missing':len(result['source_segmentation']['missing_visible_source_pixels']),'source_arm_added':len(result['source_segmentation']['added_visible_source_pixels']),'source_seam_overlap':len(result['source_segmentation']['declared_seam_overlap_pixels']),'endpoint_count':len(endpoints),'endpoint_max_error':max(e['endpoint_error_px'] for e in endpoints),'all_matrix_max_error':max(e['all_matrix_error'] for e in poses),'support_foot_diff_total':sum(e['foot_roi_rgba_diff'] for e in frames if e['support_phase']),'frame_atlas_diff_total':sum(e['atlas_diff'] for e in frames),'partial_alpha_total':sum(e['alpha']['partial'] for e in frames),'roundtrip_count':len(roundtrip),'roundtrip_diff_total':sum(e['left_right_rgba_diff']+e['rig_side_vs_direct_png_rgba_diff']+e['png_side_vs_direct_png_rgba_diff'] for e in roundtrip),'sensor_native_checks_match':all(c['match'] for e in sensor_checks for c in e['comparisons']),'cpu_float64_diff_total':sum(e['cpu_float64_visible_diff'] for e in frames),'unexpected_rgb_color_total':sum(len(e['visible_rgb_outside_declared_source_and_sensor_colors']) for e in frames)}
(OUT/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'archive':{k:v for k,v in result['archive'].items() if k!='checks'},'segmentation':result['source_segmentation'],'summary':result['summary'],'recovery_hold':result['recovery_hold'],'release':result['release_event'],'pose_ground':[e for e in poses if e['action']=='death_down'],'cpu_diff_brief':[(e['action'],e['frame'],e['cpu_float64_visible_diff'],len(e['visible_rgb_outside_declared_source_and_sensor_colors'])) for e in frames]},ensure_ascii=False,indent=2))

