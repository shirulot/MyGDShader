"""Read-only fixed-package cutter v010 audit. No Godot or production generators."""
from pathlib import Path
from PIL import Image
from collections import Counter
import json,hashlib,zipfile,re,math,io
ROOT=Path(r'E:/dev/shader/godot-shader/godot-shader-simple');OUT=Path(__file__).parent;PKG=OUT/'package'
ZIP=ROOT/'art-source/ember/deliveries/enemy_cutter_actions_v010_2026-10-06.zip';LIVE=ROOT/'art-source/ember/enemy-cutter-actions-v010'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def diff(a,b):return sum(p!=q for p,q in zip(a.getdata(),b.getdata()))
def contains(v,poly):
 x,y=v;yes=False
 for i,(a,b) in enumerate(poly):
  c,d=poly[i-1]
  if (b>y)!=(d>y) and x<(c-a)*(y-b)/(d-b)+a:yes=not yes
 return yes
def oldfoot(x,y):return (51<=x<55 or 73<=x<77) and 89<=y<95
def ident(p):return {'position':list(p),'basis_x':[1,0],'basis_y':[0,1]}
def rot(angle,p):
 a=math.radians(angle);return {'position':list(p),'basis_x':[math.cos(a),math.sin(a)],'basis_y':[-math.sin(a),math.cos(a)]}
def transform(t,p):return [t['position'][i]+t['basis_x'][i]*p[0]+t['basis_y'][i]*p[1] for i in [0,1]]
def minus(a,b):return [a[i]-b[i] for i in [0,1]]
def maxerr(a,b):return max(abs(a[k][j]-b[k][j]) for k in ['position','basis_x','basis_y'] for j in [0,1])
def alpha(image):
 h=Counter(image.getchannel('A').getdata());return {'size':list(image.size),'bbox':image.getchannel('A').getbbox(),'visible':sum(n for a,n in h.items() if a),'partial':sum(n for a,n in h.items() if 0<a<255),'border_visible':sum(image.getpixel((x,y))[3]>0 for y in range(image.height) for x in range(image.width) if x in [0,image.width-1] or y in [0,image.height-1])}
result={'scope':'Fixed package source/UV/matrix/feet/PNG-resource and bound saved/cold GPU evidence; not art approval.'}
with zipfile.ZipFile(ZIP) as z:
 names=z.namelist();m=json.loads(z.read('file_hashes.json'))
 assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names)
 z.extractall(PKG)
 checks=[{'path':f['path'],'bytes_match':len(z.read(f['path']))==f['bytes'],'zip_sha_match':hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256'],'unpacked_sha_match':sha(PKG/f['path'])==f['sha256'],'current_sha_match':sha(LIVE/f['path'])==f['sha256']} for f in m['files']]
 result['archive']={'sha256':sha(ZIP),'bytes':ZIP.stat().st_size,'entries':len(names),'payloads':len(checks),'duplicates':len(names)-len(set(names)),'crc_failure':z.testzip(),'unlisted':sorted(set(names)-{x['path'] for x in checks}),'checks':checks}
rig=read(PKG/'rig.json');parts={p['id']:p for p in rig['parts']};cat=read(PKG/'output/catalog_v010.json');canon=Image.open(PKG/'source/canonical.png').convert('RGBA');legs=Image.open(PKG/'source/front_legs_master.png').convert('RGBA')
oldzip=ROOT/'art-source/ember/deliveries/enemy_sequences_v001_2026-10-06.zip'
with zipfile.ZipFile(oldzip) as z:
 oldname='art-source/ember/enemy-sequences-v001/templates/enemy_cutter_canonical_down_v001.png'
 result['source']={'canonical_sha256':sha(PKG/'source/canonical.png'),'canonical_same_v001_template':(PKG/'source/canonical.png').read_bytes()==z.read(oldname),'v001_zip_sha256':sha(oldzip),'front_master_sha256':sha(PKG/'source/front_legs_master.png'),'front_master_size':list(legs.size),'front_prompt_sha256':sha(PKG/'source/front_legs_prompt.txt'),'catalog_source_bound':cat['source_sha256']==sha(PKG/'source/canonical.png'),'catalog_rig_bound':cat['rig_sha256']==sha(PKG/'rig.json')}
canonical_parts=[p for p in rig['parts'] if 'polygon' in p];rect_parts=[p for p in rig['parts'] if 'source_rect' in p]
sourcepixels={(x,y) for y in range(128) for x in range(128) if canon.getpixel((x,y))[3]>=128}
regions={p['id']:{v for v in sourcepixels if contains([v[0]+.5,v[1]+.5],p['polygon'])} for p in canonical_parts}
result['partition']={'source_pixel_count':len(sourcepixels),'canonical_part_counts':{n:len(v) for n,v in regions.items()},'missing':sorted(sourcepixels-set.union(*regions.values())),'duplicate':[{'xy':v,'parts':[n for n,s in regions.items() if v in s]} for v in sourcepixels if sum(v in s for s in regions.values())>1],'intentional_excluded_old_front_pixels':sorted(v for v in sourcepixels if oldfoot(*v))}
result['fixed_front_mapping']=[{'id':p['id'],'source_rect':p['source_rect'],'destination_rect':p['destination_rect'],'scale_xy':[p['destination_rect'][i]/p['source_rect'][i] for i in [2,3]],'pivot':p['pivot'],'z':p['z']} for p in rect_parts]
def pose_expected(action,i):
 t={n:ident(p['pivot']) for n,p in parts.items()};dy=0;saw=claw=blade=fold=0;power=1;stance=list(rig['supports'])
 if action=='idle_down':dy=[0,-1,0,1][i];phase='quiet_actuator_idle'
 elif action=='move_down':
  sweep=[2,1,0,-1,-2,-1,0,1];a=sweep[i];b=sweep[(i+4)%8];dy=[0,0,-1,0,0,0,-1,0][i]
  for n in ['rear_left','front_right','front_right_foot']:t[n]['position'][1]+=a
  for n in ['rear_right','front_left','front_left_foot']:t[n]['position'][1]+=b
  stance=['rear_left','front_right'] if i<4 else ['rear_right','front_left'];phase='diagonal_pair_A' if i<4 else 'diagonal_pair_B'
 elif action=='attack_down':saw=[0,12,22,-18,-8,0][i];claw=[0,-3,-6,3,1,0][i];blade=[0,15,30,45,15,0][i];dy=[0,-1,-1,1,1,0][i];phase=['neutral','saw_windup','ready','short_cut_release','recovery','neutral_recovered'][i]
 elif action=='hit_down':dy=[0,-1,1,0][i];saw=[0,8,-4,0][i];claw=[0,-8,4,0][i];phase='impact_then_recover'
 else:
  dy=[0,1,3,5,7,8,8,8][i];fold=[0,3,7,12,18,22,22,22][i];saw=fold*2;claw=-fold*2;power=[1,.6,.2,0,0,0,0,0][i];phase=['neutral','power_loss','legs_fold','body_drops','lower_stop','settle','wreck','wreck_hold'][i]
  for side,sgn in [('left',1),('right',-1)]:
   n='rear_'+side;t[n]=rot(fold*sgn,[parts[n]['pivot'][0],parts[n]['pivot'][1]+dy]);n='front_'+side;ankle=[49 if side=='left' else 79,96];r=rot(fold*1.5*sgn,ankle);t[n]=rot(fold*1.5*sgn,transform(r,minus(parts[n]['pivot'],ankle)))
 for n in ['body','saw_arm','saw_blade','claw_arm']:t[n]['position'][1]+=dy
 shoulder=t['saw_arm']['position'];r=rot(saw,shoulder)
 t['saw_arm']=rot(saw,shoulder);t['saw_blade']=rot(saw+blade,transform(r,minus(t['saw_blade']['position'],shoulder)));t['claw_arm']=rot(claw,t['claw_arm']['position'])
 return t,{'body_delta':[0,dy],'power':power,'phase':phase,'stance':stance,'saw_angle':saw,'claw_angle':claw,'blade_angle':blade,'leg_fold':fold}

def render(transforms,power):
 # Centre inverse sampling; retain GPU raster/UV boundary exceptions explicitly.
 image=Image.new('RGBA',(128,128),(255,255,255,0));owners={}
 for p in sorted(rig['parts'],key=lambda x:x['z']):
  t=transforms[p['id']];a,b=t['basis_x'];c,d=t['basis_y'];det=a*d-b*c
  if 'polygon' in p:poly=p['polygon'];texture=canon
  else:
   dx,dy,dw,dh=p['destination_rect'];sx,sy,sw,sh=p['source_rect'];poly=[[dx,dy],[dx+dw,dy],[dx+dw,dy+dh],[dx,dy+dh]];texture=legs
  outpoly=[transform(t,minus(v,p['pivot'])) for v in poly]
  xmin=max(0,math.floor(min(v[0] for v in outpoly)));xmax=min(128,math.ceil(max(v[0] for v in outpoly)));ymin=max(0,math.floor(min(v[1] for v in outpoly)));ymax=min(128,math.ceil(max(v[1] for v in outpoly)))
  for y in range(ymin,ymax):
   for x in range(xmin,xmax):
    rx=x+.5-t['position'][0];ry=y+.5-t['position'][1];v=[p['pivot'][0]+(d*rx-c*ry)/det,p['pivot'][1]+(-b*rx+a*ry)/det]
    if not contains(v,poly):continue
    uv=v if 'polygon' in p else [sx+(v[0]-dx)*sw/dw,sy+(v[1]-dy)*sh/dh];xx,yy=map(math.floor,uv)
    if not (0<=xx<texture.width and 0<=yy<texture.height):continue
    rgb=texture.getpixel((xx,yy))
    if 'polygon' in p and oldfoot(xx,yy):continue
    if rgb[3]<128:continue
    if 'polygon' in p and 60<=xx<68 and 82<=yy<85:rgb=tuple(math.floor(v*(.3+.7*power)+.5) for v in rgb[:3])+(rgb[3],)
    image.putpixel((x,y),(*rgb[:3],255));owners[x+y*128]={'part':p['id'],'uv':uv}
 return image,owners

frames=[];poses=[];pairs=[];sample_exceptions=[]
for action,clip in cat['actions'].items():
 atlas=Image.open(PKG/f'output/{action}_v010.png').convert('RGBA')
 for i,record in enumerate(clip['poses']):
  t,definition=pose_expected(action,i);actual=Image.open(PKG/f'output/{action}/f{i:02}.png').convert('RGBA');cpu,owners=render(record['part_transforms'],definition['power'])
  differences=[]
  for y in range(128):
   for x in range(128):
    cp=cpu.getpixel((x,y));ap=actual.getpixel((x,y))
    if cp!=ap:
     owner=owners.get(x+y*128);e={'xy':[x,y],'cpu':cp,'actual':ap,'owner':owner};differences.append(e)
     if owner and cp[3]==ap[3]:
      texture=legs if 'source_rect' in parts[owner['part']] else canon;uv=owner['uv'];xx,yy=map(math.floor,uv)
      candidates=[[xx+ox,yy+oy] for ox,oy in [(0,0),(-1,0),(1,0),(0,-1),(0,1)] if 0<=xx+ox<texture.width and 0<=yy+oy<texture.height and texture.getpixel((xx+ox,yy+oy))[:3]==ap[:3]]
      sample_exceptions.append({'action':action,'frame':i,**e,'same_source_neighbor_matches':candidates,'distance_to_integer_uv':min(abs(v-round(v)) for v in uv)})
  feet={};ankles={}
  for n,point in rig['supports'].items():
   node=n+'_foot' if n.startswith('front_') else n;calculated=transform(record['part_transforms'][node],minus(point,parts[node]['pivot']));feet[n]={'actual_calculated':calculated,'registered':record['feet'][n],'max_error':max(abs(a-b) for a,b in zip(calculated,record['feet'][n]))}
  for side in ['left','right']:
   upper='front_'+side;foot=upper+'_foot';ankle=[49 if side=='left' else 79,96];up=transform(record['part_transforms'][upper],minus(ankle,parts[upper]['pivot']));ft=transform(record['part_transforms'][foot],minus(ankle,parts[foot]['pivot']));ankles[side]={'upper':up,'foot':ft,'max_gap':max(abs(a-b) for a,b in zip(up,ft))}
  poses.append({'action':action,'frame':i,'expected_definition':definition,'matrix_max_error':max(maxerr(record['part_transforms'][n],v) for n,v in t.items()),'root_matches':record['root_px']==[64,104],'phase_matches':record['phase']==definition['phase'],'body_delta_matches':record['body_delta']==definition['body_delta'],'stance_matches':record['stance']==definition['stance'],'feet':feet,'ankles':ankles})
  frames.append({'action':action,'frame':i,'alpha':alpha(actual),'atlas_rgba_diff':diff(actual,atlas.crop((i*128,0,(i+1)*128,128))),'frame_sha_match':sha(PKG/f'output/{action}/f{i:02}.png')==clip['frame_hashes'][i],'cpu_rgba_diff':len(differences),'cpu_differences':differences})
  for background,color in [('black',0),('white',255)]:
   pair=Image.open(PKG/f'qa/roundtrip_{action}_f{i:02}_{background}.png').convert('RGBA');left=pair.crop((0,0,320,320));right=pair.crop((320,0,640,320));direct=Image.alpha_composite(Image.new('RGBA',(128,128),(color,color,color,255)),actual).crop((24,32,104,112)).resize((320,320),Image.Resampling.NEAREST)
   pairs.append({'action':action,'frame':i,'background':background,'size':list(pair.size),'left_right_diff':diff(left,right),'left_direct_diff':diff(left,direct),'right_direct_diff':diff(right,direct)})
result['frames']=frames;result['poses']=poses;result['saved_gpu_pairs']=pairs;result['sampling_exceptions']=sample_exceptions

# Inspect the retained exceptions without changing the independent renderer.
# Include the 3x3 source-neighbour neighbourhood and higher-layer source-mask
# boundaries; diagonal UV ties and masked-tool occlusion need more than a
# four-neighbour RGB search. Actual source candidates are diagnostic evidence.
boundary_diagnostics=[]
for f in frames:
 record=cat['actions'][f['action']]['poses'][f['frame']];power=pose_expected(f['action'],f['frame'])[1]['power']
 for e in f['cpu_differences']:
  x,y=e['xy'];ap=tuple(e['actual']);candidates=[]
  for p in rig['parts']:
   t=record['part_transforms'][p['id']];a,b=t['basis_x'];c,d=t['basis_y'];det=a*d-b*c;rx=x+.5-t['position'][0];ry=y+.5-t['position'][1];v=[p['pivot'][0]+(d*rx-c*ry)/det,p['pivot'][1]+(-b*rx+a*ry)/det]
   if 'source_rect' in p:
    dx,dy,dw,dh=p['destination_rect'];sx,sy,sw,sh=p['source_rect']
    if not(dx-.0001<=v[0]<=dx+dw+.0001 and dy-.0001<=v[1]<=dy+dh+.0001):continue
    uv=[sx+(v[0]-dx)*sw/dw,sy+(v[1]-dy)*sh/dh];texture=legs
   else:
    if not contains(v,p['polygon']):continue
    uv=v;texture=canon
   xx,yy=map(math.floor,uv)
   for oy in [-1,0,1]:
    for ox in [-1,0,1]:
     px,py=xx+ox,yy+oy
     if not(0<=px<texture.width and 0<=py<texture.height):continue
     rgb=texture.getpixel((px,py))
     if rgb[3]<128 or ('polygon' in p and oldfoot(px,py)):continue
     color=rgb[:3]
     if 'polygon' in p and 60<=px<68 and 82<=py<85:color=tuple(math.floor(v*(.3+.7*power)+.5) for v in color)
     if ap[3]==255 and color==ap[:3]:candidates.append({'part':p['id'],'source_uv':uv,'source_pixel':[px,py],'source_offset':[ox,oy],'distance_to_integer_uv':min(abs(v-round(v)) for v in uv),'z':p['z']})
  boundary_diagnostics.append({'action':f['action'],'frame':f['frame'],**e,'actual_same_source_nearest_candidates':candidates})
result['cpu_boundary_diagnostics']=boundary_diagnostics
result['cpu_boundary_summary']={'exceptions':len(boundary_diagnostics),'same_source_candidate_count':sum(bool(e['actual_same_source_nearest_candidates']) for e in boundary_diagnostics),'without_same_source_candidates':[e for e in boundary_diagnostics if not e['actual_same_source_nearest_candidates']]}

neutral=Image.open(PKG/'output/idle_down/f00.png').convert('RGBA');baseline=Image.new('RGBA',(128,128),(255,255,255,0))
for y in range(128):
 for x in range(128):
  p=canon.getpixel((x,y))
  if p[3]>=128:baseline.putpixel((x,y),(*p[:3],255))
local_rects=[p['destination_rect'] for p in rect_parts]+[[51,89,4,6],[73,89,4,6]]
changes=[]
for y in range(128):
 for x in range(128):
  p=baseline.getpixel((x,y));n=neutral.getpixel((x,y))
  if p!=n:changes.append({'xy':[x,y],'baseline':p,'neutral':n,'inside_declared_local_regions':any(dx<=x<dx+dw and dy<=y<dy+dh for dx,dy,dw,dh in local_rects)})
result['neutral_correction']={'declared_local_rects':local_rects,'changes':changes,'changed_pixels':len(changes),'outside_declared_changes':sum(not c['inside_declared_local_regions'] for c in changes),'raw_rgba_diff_vs_canonical':diff(neutral,canon),'baseline_meaning':'Original canonical with declared 0.5 coverage and transparent white RGB; separates source Alpha representation from authored local replacement.'}
result['neutral_returns']={'attack_f00':diff(neutral,Image.open(PKG/'output/attack_down/f00.png').convert('RGBA')),'attack_f05':diff(neutral,Image.open(PKG/'output/attack_down/f05.png').convert('RGBA')),'hit_f00':diff(neutral,Image.open(PKG/'output/hit_down/f00.png').convert('RGBA')),'hit_f03':diff(neutral,Image.open(PKG/'output/hit_down/f03.png').convert('RGBA')),'death_f00':diff(neutral,Image.open(PKG/'output/death_down/f00.png').convert('RGBA')),'death_f06_f07':diff(Image.open(PKG/'output/death_down/f06.png').convert('RGBA'),Image.open(PKG/'output/death_down/f07.png').convert('RGBA'))}
neutral_cpu,_=render({n:ident(p['pivot']) for n,p in parts.items()},1);neutral_cpu.save(OUT/'independent-neutral.png')

tres=(PKG/'output/cutter_actions_v010.tres').read_text(encoding='utf8');resources={m.group(3):m.group(4) for m in re.finditer(r'\[(sub_resource|resource)(?: type="([^"]+)" id="([^"]+)")?\]\n([\s\S]*?)(?=\n\[|\Z)',tres)};animations=[]
for m in re.finditer(r'"frames": \[([\s\S]*?)\],\n"loop": ([01]),\n"name": &"([^"]+)",\n"speed": ([\d.]+)',tres):
 fs,loop,action,fps=m.groups();atlas=Image.open(PKG/f'output/{action}_v010.png').convert('RGBA');regions=[];errors=[]
 for i,tid in enumerate(re.findall(r'"texture": SubResource\("([^"]+)"\)',fs)):
  b=resources[tid];r=list(map(int,re.search(r'region = Rect2\((\d+), (\d+), (\d+), (\d+)\)',b).groups()));regions.append(r);iid=re.search(r'atlas = SubResource\("([^"]+)"\)',b).group(1);image_id=re.search(r'image = SubResource\("([^"]+)"\)',resources[iid]).group(1);b=resources[image_id];width=int(re.search(r'"width": (\d+)',b).group(1));height=int(re.search(r'"height": (\d+)',b).group(1));data=bytes(map(int,re.search(r'PackedByteArray\(([^)]*)\)',b).group(1).split(',')));image=Image.frombytes('RGBA',(width,height),data);x,y,w,h=r;errors.append(diff(image.crop((x,y,x+w,y+h)),atlas.crop((i*128,0,(i+1)*128,128))))
 animations.append({'action':action,'fps':float(fps),'loop':loop=='1','frame_count':len(regions),'durations':list(map(float,re.findall(r'"duration": ([\d.]+)',fs))),'regions':regions,'embedded_atlas_rgba_diffs':errors,'catalog_atlas_sha_matches':sha(PKG/f'output/{action}_v010.png')==cat['actions'][action]['atlas_sha256']})
result['spriteframes']=animations
receipt_path=LIVE/'qa/cold_receipt_v010.json';receipt=read(receipt_path);cold=Path(receipt['cold_workspace']);cold_report=read(receipt['actual_playback_report'])
result['cold_bindings']={'receipt_sha256':sha(receipt_path),'zip_sha_matches':sha(ZIP)==receipt['zip_sha256'],'report_sha_matches':sha(receipt['actual_playback_report'])==receipt['playback_report_sha256'],'report_sha256':sha(receipt['actual_playback_report']),'report_equals_embedded':cold_report==receipt['gpu'],'catalog_bound':cold_report['catalog_sha256']==sha(PKG/'output/catalog_v010.json'),'core_files':[{'path':r['path'],'cold_sha_matches':sha(cold/r['path'])==r['sha256'],'package_sha_matches':sha(PKG/r['path'])==r['sha256']} for r in receipt['core_files']],'logs':[{'path':r['path'],'bytes':Path(r['path']).stat().st_size,'bytes_matches':Path(r['path']).stat().st_size==r['bytes'],'sha_matches':sha(r['path'])==r['sha256']} for r in receipt['logs']],'import_exit':receipt['import_exit'],'capture_exit':receipt['capture_exit'],'actual_cold_playback_report':cold_report,'independent_gpu_rerun':False}
(OUT/'bound-cold-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');(OUT/'bound-cold-playback.json').write_text(json.dumps(cold_report,ensure_ascii=False,indent=2),encoding='utf8')
servedroot=ROOT/'art-source/ember/enemy-sequences-v001/previews';served=servedroot/'cutter-actions-v010';paths={'index.html':'preview.html','output/catalog_v010.json':'output/catalog_v010.json',**{f'output/{a}_v010.png':f'output/{a}_v010.png' for a in cat['actions']}}
result['served_bindings']={'config':read(servedroot/'preview_server.json'),'files':[{'path':p,'exists':(served/p).is_file(),'same_package_sha':sha(served/p)==sha(PKG/q) if (served/p).is_file() else False} for p,q in paths.items()]}
crop_cases=[];saved_roi_clipped=0
for f in frames:
 image=Image.open(PKG/f"output/{f['action']}/f{f['frame']:02}.png").convert('RGBA');points=[[x,y] for y in range(128) for x in range(128) if image.getpixel((x,y))[3] and not(32<=x<120 and 32<=y<112)]
 if points:crop_cases.append({'action':f['action'],'frame':f['frame'],'clipped_pixels':len(points),'points':points})
 saved_roi_clipped+=sum(image.getpixel((x,y))[3]>0 and not(24<=x<104 and 32<=y<112) for y in range(128) for x in range(128))
result['preview_crop']={'declared_preview_and_contact_roi':[32,32,88,80],'clipped_frames':crop_cases,'gpu_saved_roi':[24,32,80,80],
 'gpu_saved_roi_clipped_pixels':saved_roi_clipped,
 'minimal_fix':'Use the same Rect(24,32,80,80) in preview.html and export.gd contact-sheet crop; regenerate auxiliary contact sheets and repackage without changing formal frame/atlas pixels.'}
runtime_paths=['preview.tscn','preview.gd','output/cutter_actions_v010.tres','action_rig.gd','rig.json','source/canonical.png','source/front_legs_master.png','entity_cutout.gdshader']
result['static_dependency_closure']=[{'path':p,'exists_in_fixed_package':(PKG/p).is_file(),'manifest_bound':p in {r['path'] for r in checks}} for p in runtime_paths]
result['source_alpha_histograms']={'canonical':dict(sorted(Counter(canon.getchannel('A').getdata()).items())),'front_master':dict(sorted(Counter(legs.getchannel('A').getdata()).items()))}
result['summary']={'all_manifest_checks':all(all(x[k] for k in ['bytes_match','zip_sha_match','unpacked_sha_match','current_sha_match']) for x in checks),'frames':len(frames),'cpu_rgba_diff':sum(f['cpu_rgba_diff'] for f in frames),'sampling_exceptions':len(sample_exceptions),'matrix_max_error':max(p['matrix_max_error'] for p in poses),'feet_max_error':max(v['max_error'] for p in poses for v in p['feet'].values()),'front_ankle_max_gap':max(v['max_gap'] for p in poses for v in p['ankles'].values()),'atlas_rgba_diff':sum(f['atlas_rgba_diff'] for f in frames),'saved_gpu_pairs':len(pairs),'saved_gpu_rgba_diff':sum(x['left_right_diff']+x['left_direct_diff']+x['right_direct_diff'] for x in pairs),'neutral_outside_declared_changes':result['neutral_correction']['outside_declared_changes']}
(OUT/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'archive':{k:v for k,v in result['archive'].items() if k!='checks'},'source':result['source'],'partition':{k:v for k,v in result['partition'].items() if k not in ['duplicate','intentional_excluded_old_front_pixels']},'duplicate_pixels':len(result['partition']['duplicate']),'excluded_old_front_pixels':len(result['partition']['intentional_excluded_old_front_pixels']),'summary':result['summary'],'neutral_changes':len(changes),'cpu_diff_frames':[(f['action'],f['frame'],f['cpu_rgba_diff']) for f in frames if f['cpu_rgba_diff']]},ensure_ascii=False,indent=2))
