"""Fixed drone v011 source/registration/resources and inherited GPU record audit."""
from pathlib import Path
from PIL import Image
from collections import Counter
import json,hashlib,zipfile,re,math,io
ROOT=Path(r'E:/dev/shader/godot-shader/godot-shader-simple');OUT=Path(__file__).parent;PKG=OUT/'package';ZIP=ROOT/'art-source/ember/deliveries/enemy_drone_actions_v011_2026-10-06.zip';LIVE=ROOT/'art-source/ember/enemy-drone-actions-v011'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def diff(a,b):return sum(p!=q for p,q in zip(a.getdata(),b.getdata()))
def contains(v,poly):
 x,y=v;inside=False
 for i,(a,b) in enumerate(poly):
  c,d=poly[i-1]
  if (b>y)!=(d>y) and x<(c-a)*(y-b)/(d-b)+a:inside=not inside
 return inside
def identity(p):return {'position':list(p),'basis_x':[1,0],'basis_y':[0,1]}
def rotation(deg,p):
 a=math.radians(deg);return {'position':list(p),'basis_x':[math.cos(a),math.sin(a)],'basis_y':[-math.sin(a),math.cos(a)]}
def apply(t,v):return [t['position'][i]+t['basis_x'][i]*v[0]+t['basis_y'][i]*v[1] for i in [0,1]]
def minus(a,b):return [a[i]-b[i] for i in [0,1]]
def lin(t,v):return [t['basis_x'][i]*v[0]+t['basis_y'][i]*v[1] for i in [0,1]]
def compose(a,b):return {'position':apply(a,b['position']),'basis_x':lin(a,b['basis_x']),'basis_y':lin(a,b['basis_y'])}
def matrix_error(a,b):return max(abs(a[k][i]-b[k][i]) for k in ['position','basis_x','basis_y'] for i in [0,1])
def in_fan(x,y):return any(((x-cx)/6.5)**2+((y-64.5)/4.5)**2<1 for cx in [41.5,85.5])
def alpha(image):
 h=Counter(image.getchannel('A').getdata());return {'size':list(image.size),'bbox':image.getchannel('A').getbbox(),'visible':sum(n for a,n in h.items() if a),'partial':sum(n for a,n in h.items() if 0<a<255),'border_visible':sum(image.getpixel((x,y))[3]>0 for y in range(128) for x in range(128) if x in [0,127] or y in [0,127])}
result={'scope':'Independent fixed source/UV, part and strut endpoint registration, PNG/embedded resource and saved/cold GPU binding; art and runtime behaviour separately reviewed.'}
with zipfile.ZipFile(ZIP) as z:
 names=z.namelist();m=json.loads(z.read('file_hashes.json'));assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names);z.extractall(PKG)
 checks=[{'path':p['path'],'bytes_match':len(z.read(p['path']))==p['bytes'],'zip_sha_match':hashlib.sha256(z.read(p['path'])).hexdigest()==p['sha256'],'unpacked_sha_match':sha(PKG/p['path'])==p['sha256'],'current_same':sha(LIVE/p['path'])==p['sha256']} for p in m['files']]
 result['archive']={'sha256':sha(ZIP),'bytes':ZIP.stat().st_size,'entries':len(names),'payloads':len(checks),'crc_failure':z.testzip(),'duplicates':len(names)-len(set(names)),'unlisted':sorted(set(names)-{p['path'] for p in checks}),'checks':checks}
rig=read(PKG/'rig.json');parts={p['id']:p for p in rig['parts']};canon=Image.open(PKG/'source/canonical.png').convert('RGBA');master=Image.open(PKG/'source/rotor_well_master.png').convert('RGBA');cat=read(PKG/'output/catalog_v011.json')
oldzip=ROOT/'art-source/ember/deliveries/enemy_sequences_v001_2026-10-06.zip'
with zipfile.ZipFile(oldzip) as z:
 n='art-source/ember/enemy-sequences-v001/templates/enemy_scout_drone_canonical_down_v001.png'
 result['source']={'canonical_sha256':sha(PKG/'source/canonical.png'),'canonical_same_v001':z.read(n)==(PKG/'source/canonical.png').read_bytes(),'old_v001_zip_sha256':sha(oldzip),'master_sha256':sha(PKG/'source/rotor_well_master.png'),'master_size':list(master.size),'prompt_sha256':sha(PKG/'source/rotor_well_prompt.txt'),'catalog_source_bound':cat['source_sha256']==sha(PKG/'source/canonical.png'),'catalog_rig_bound':cat['rig_sha256']==sha(PKG/'rig.json')}
valid={(x,y) for y in range(128) for x in range(128) if canon.getpixel((x,y))[3]>=128};regions={n:{v for v in valid if contains([v[0]+.5,v[1]+.5],p['polygon'])} for n,p in parts.items()};principal=['left_pod','right_pod','body','probe']
result['partition']={'source_visible':len(valid),'region_counts':{n:len(v) for n,v in regions.items()},'main_missing':sorted(valid-set.union(*(regions[n] for n in principal))),'main_duplicate':[v for v in valid if sum(v in regions[n] for n in principal)>1],'intentional_strut_overlap':[{'xy':v,'parts':[n for n,s in regions.items() if v in s]} for v in valid if sum(v in s for s in regions.values())>1]}
neutral=Image.open(PKG/'output/idle_down/f00.png').convert('RGBA');baseline=Image.new('RGBA',(128,128),(255,255,255,0));changes=[]
for y in range(128):
 for x in range(128):
  p=canon.getpixel((x,y))
  if p[3]>=128:baseline.putpixel((x,y),(*p[:3],255))
  if baseline.getpixel((x,y))!=neutral.getpixel((x,y)):changes.append({'xy':[x,y],'baseline':baseline.getpixel((x,y)),'neutral':neutral.getpixel((x,y)),'inside_declared_ellipse':in_fan(x+.5,y+.5)})
result['neutral_source_correction']={'changed_pixels':len(changes),'outside_declared_ellipses':sum(not c['inside_declared_ellipse'] for c in changes),'changes':changes,'raw_rgba_diff':diff(canon,neutral),'comparison':'Original source at 0.5 hard coverage and exported transparent RGB; not raw Alpha equality.'}
def expected(action,i):
 dy=pod=angle=roll=probe=0;power=1;phase='hover'
 if action=='idle_down':dy=[0,-1,0,1][i];angle=i*22.5
 elif action=='move_down':dy=[0,-1,-1,0,1,1,0,0][i];angle=i*11.25;phase='hover_cruise'
 elif action=='attack_down':dy=[0,0,1,2,1,0][i];probe=[0,0,1,2,1,0][i];angle=[0,22.5,45,67.5,22.5,0][i];phase=['neutral','target_lock','probe_ready','short_forward_dip','recover','neutral_recovered'][i]
 elif action=='hit_down':roll=[0,-6,3,0][i];angle=[0,15,8,0][i];phase='impact_roll_recover'
 else:dy=[0,3,8,14,20,24,24,24][i];pod=[0,0,0,1,2,3,3,3][i];angle=[0,25,42,52,58,60,60,60][i];power=[1,.6,.2,0,0,0,0,0][i];phase=['hover','power_loss','drop','drop_fold_struts','approach_ground','contact','grounded_wreck','wreck_hold'][i]
 whole=compose(rotation(roll,[64,67+dy]),identity([-64,-67]));t={}
 for n in ['body','probe']:t[n]=compose(whole,identity(parts[n]['pivot']))
 for j in [0,1]:t['probe']['position'][j]+=whole['basis_y'][j]*probe
 endpoints={};fan_transforms={}
 for side,sgn in [('left',1),('right',-1)]:
  n=side+'_pod';pos=parts[n]['pivot'];t[n]=compose(whole,identity([pos[0],pos[1]+pod]));start=[54 if side=='left' else 74,67];end=[51 if side=='left' else 77,67];target_start=apply(whole,start);target_end=apply(whole,[end[0],end[1]+pod]);rest=minus(end,start);current=minus(target_end,target_start);length=math.hypot(*rest);unit=[v/length for v in rest];axis=[v/length for v in current];normal=[-current[1]/math.hypot(*current),current[0]/math.hypot(*current)];rest_normal=[-unit[1],unit[0]];t[side+'_strut']={'position':target_start,'basis_x':[axis[j]*unit[0]+normal[j]*rest_normal[0] for j in [0,1]],'basis_y':[axis[j]*unit[1]+normal[j]*rest_normal[1] for j in [0,1]]};endpoints[side]={'start':target_start,'end':target_end,'rest_local_end':rest}
  projection={'position':[0,0],'basis_x':[1,0],'basis_y':[0,9/13]};fan_transforms[side]={'well':compose(t[n],projection),'rotor':compose(compose(t[n],projection),rotation(angle*sgn,[0,0]))}
 contacts={'body_probe_bottom':apply(whole,[64,80+probe]),'left_pod_bottom':apply(whole,[42,77+pod]),'right_pod_bottom':apply(whole,[86,77+pod])}
 return t,endpoints,contacts,fan_transforms,{'body_y':dy,'pod_local_y':pod,'rotor_angle_deg':angle,'probe_y':probe,'roll_deg':roll,'sensor_power':power,'phase':phase}

frames=[];poses=[];pairs=[];contactsheets=[]
for action,clip in cat['actions'].items():
 atlas=Image.open(PKG/f'output/{action}_v011.png').convert('RGBA');count=clip['frame_count']
 for i,record in enumerate(clip['poses']):
  t,ends,contacts,fan_t,d=expected(action,i);struts={}
  for side in ['left','right']:
   actual=record['part_transforms'][side+'_strut'];start=actual['position'];end=apply(actual,record['strut_endpoints'][side]['rest_local_end']);struts[side]={'actual_start':start,'actual_end':end,'expected':ends[side],'max_endpoint_error':max(abs(a-b) for p,q in [(start,ends[side]['start']),(end,ends[side]['end'])] for a,b in zip(p,q)),'record_max_error':max(abs(a-b) for k in ['start','end','rest_local_end'] for a,b in zip(record['strut_endpoints'][side][k],ends[side][k])),'axial_scale':math.hypot(*minus(ends[side]['end'],ends[side]['start']))/3,'normal_scale':math.hypot(*actual['basis_y'])}
  contact_error=max(abs(a-b) for k,v in contacts.items() for a,b in zip(v,record['contacts'][k]));poses.append({'action':action,'frame':i,'definition':d,'matrix_max_error':max(matrix_error(record['part_transforms'][n],v) for n,v in t.items()),'fields_match':all(record[k]==d[k] for k in ['body_y','pod_local_y','rotor_angle_deg','phase']),'root_matches':record['root_px']==[64,104],'struts':struts,'contacts_expected':contacts,'contact_record_max_error':contact_error,'derived_fan_transforms':fan_t,'fan_transform_scope':'Derived from fixed runtime code and pose fields, not separately logged actual fan-node matrices.'})
  actual=Image.open(PKG/f'output/{action}/f{i:02}.png').convert('RGBA');crop_points=[[x,y] for y in range(128) for x in range(128) if actual.getpixel((x,y))[3] and not(32<=x<120 and 32<=y<112)];frames.append({'action':action,'frame':i,'alpha':alpha(actual),'frame_sha_matches':sha(PKG/f'output/{action}/f{i:02}.png')==clip['frame_hashes'][i],'atlas_rgba_diff':diff(actual,atlas.crop((i*128,0,(i+1)*128,128))),'preview_roi_omitted_points':crop_points})
  for background,c in [('black',0),('white',255)]:
   pair=Image.open(PKG/f'qa/roundtrip_{action}_f{i:02}_{background}.png').convert('RGBA');left=pair.crop((0,0,320,320));right=pair.crop((320,0,640,320));direct=Image.alpha_composite(Image.new('RGBA',(128,128),(c,c,c,255)),actual).crop((24,32,104,112)).resize((320,320),Image.Resampling.NEAREST);pairs.append({'action':action,'frame':i,'background':background,'size':list(pair.size),'left_right_diff':diff(left,right),'left_direct_diff':diff(left,direct),'right_direct_diff':diff(right,direct)})
 for background,c in [('black',0),('white',255)]:
  contact=Image.new('RGBA',(88*count,80),(c,c,c,255))
  for i in range(count):contact.paste(Image.alpha_composite(Image.new('RGBA',(128,128),(c,c,c,255)),Image.open(PKG/f'output/{action}/f{i:02}.png').convert('RGBA')).crop((32,32,120,112)),(88*i,0))
  for s in [1,4]:
   want=contact if s==1 else contact.resize((contact.width*4,320),Image.Resampling.NEAREST);have=Image.open(PKG/f'qa/{action}_{background}_{s}x.png').convert('RGBA');contactsheets.append({'action':action,'background':background,'scale':s,'size_matches':want.size==have.size,'rgba_diff':diff(want,have)})
result['frames']=frames;result['poses']=poses;result['saved_gpu_pairs']=pairs;result['contact_recomputation']=contactsheets
result['neutral_returns']={n:diff(neutral,Image.open(PKG/f'output/{a}/f{i:02}.png').convert('RGBA')) for n,a,i in [('attack_initial','attack_down',0),('attack_return','attack_down',5),('hit_initial','hit_down',0),('hit_return','hit_down',3),('death_initial','death_down',0)]};result['neutral_returns']['death_hold']=diff(Image.open(PKG/'output/death_down/f06.png').convert('RGBA'),Image.open(PKG/'output/death_down/f07.png').convert('RGBA'))

ground=Image.open(PKG/'output/death_down/f06.png').convert('RGBA')
result['actual_final_ground_pixels']={'row_103_x':[x for x in range(128) if ground.getpixel((x,103))[3]],'registered_contact_neighbourhood_actual_bottoms':[{'anchor_x':cx,'actual_bottom_exclusive':max(y for y in range(128) for x in range(cx-2,cx+3) if ground.getpixel((x,y))[3])+1} for cx in [42,64,86]],'meaning':'Exclusive bitmap bottom104 means pixels extend through row103 and touch the registered ground boundary; not bbox alignment.'}
result['source_alpha_histograms']={'canonical':dict(sorted(Counter(canon.getchannel('A').getdata()).items())),'rotor_well_master':dict(sorted(Counter(master.getchannel('A').getdata()).items()))}
tres=(PKG/'output/drone_actions_v011.tres').read_text(encoding='utf8');resources={m.group(3):m.group(4) for m in re.finditer(r'\[(sub_resource|resource)(?: type="([^"]+)" id="([^"]+)")?\]\n([\s\S]*?)(?=\n\[|\Z)',tres)};animations=[]
for m in re.finditer(r'"frames": \[([\s\S]*?)\],\n"loop": ([01]),\n"name": &"([^"]+)",\n"speed": ([\d.]+)',tres):
 fs,loop,action,fps=m.groups();atlas=Image.open(PKG/f'output/{action}_v011.png').convert('RGBA');regions=[];errors=[]
 for i,tid in enumerate(re.findall(r'"texture": SubResource\("([^"]+)"\)',fs)):
  b=resources[tid];r=list(map(int,re.search(r'region = Rect2\((\d+), (\d+), (\d+), (\d+)\)',b).groups()));regions.append(r);iid=re.search(r'atlas = SubResource\("([^"]+)"\)',b).group(1);image_id=re.search(r'image = SubResource\("([^"]+)"\)',resources[iid]).group(1);b=resources[image_id];width=int(re.search(r'"width": (\d+)',b).group(1));height=int(re.search(r'"height": (\d+)',b).group(1));data=bytes(map(int,re.search(r'PackedByteArray\(([^)]*)\)',b).group(1).split(',')));image=Image.frombytes('RGBA',(width,height),data);x,y,w,h=r;errors.append(diff(image.crop((x,y,x+w,y+h)),atlas.crop((i*128,0,(i+1)*128,128))))
 animations.append({'action':action,'fps':float(fps),'loop':loop=='1','frame_count':len(regions),'durations':list(map(float,re.findall(r'"duration": ([\d.]+)',fs))),'regions':regions,'embedded_atlas_rgba_diffs':errors,'catalog_atlas_sha_matches':sha(PKG/f'output/{action}_v011.png')==cat['actions'][action]['atlas_sha256']})
result['spriteframes']=animations
rp=LIVE/'qa/cold_receipt_v011.json';r=read(rp);cold=Path(r['cold_workspace']);cold_report=read(r['actual_playback_report']);result['cold_bindings']={'receipt_sha256':sha(rp),'zip_sha_matches':sha(ZIP)==r['zip_sha256'],'report_sha_matches':sha(r['actual_playback_report'])==r['playback_report_sha256'],'report_sha256':sha(r['actual_playback_report']),'report_equals_embedded':cold_report==r['gpu'],'catalog_bound':cold_report['catalog_sha256']==sha(PKG/'output/catalog_v011.json'),'core_files':[{'path':f['path'],'cold_sha_matches':sha(cold/f['path'])==f['sha256'],'package_sha_matches':sha(PKG/f['path'])==f['sha256']} for f in r['core_files']],'logs':[{'path':f['path'],'bytes':Path(f['path']).stat().st_size,'bytes_matches':Path(f['path']).stat().st_size==f['bytes'],'sha_matches':sha(f['path'])==f['sha256']} for f in r['logs']],'import_exit':r['import_exit'],'capture_exit':r['capture_exit'],'actual_cold_playback_report':cold_report,'independent_gpu_rerun':False}
(OUT/'bound-cold-receipt.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');(OUT/'bound-cold-playback.json').write_text(json.dumps(cold_report,ensure_ascii=False,indent=2),encoding='utf8')
servedroot=ROOT/'art-source/ember/enemy-sequences-v001/previews';served=servedroot/'drone-actions-v011';paths={'index.html':'preview.html','output/catalog_v011.json':'output/catalog_v011.json',**{f'output/{a}_v011.png':f'output/{a}_v011.png' for a in cat['actions']},**{f'qa/{a}_{b}_4x.png':f'qa/{a}_{b}_4x.png' for a in cat['actions'] for b in ['black','white']}}
result['served_binding']={'config':read(servedroot/'preview_server.json'),'files':[{'path':p,'exists':(served/p).is_file(),'same_package_sha':sha(served/p)==sha(PKG/q) if (served/p).is_file() else False} for p,q in paths.items()]}
runtime_paths=['preview.tscn','preview.gd','output/drone_actions_v011.tres','action_rig.gd','rig.json','source/canonical.png','source/rotor_well_master.png','entity_cutout.gdshader','fan_cutout.gdshader'];result['static_dependency_closure']=[{'path':p,'exists_in_package':(PKG/p).is_file(),'manifest_bound':p in {f['path'] for f in checks}} for p in runtime_paths]
result['summary']={'manifest_all':all(all(c[k] for k in ['bytes_match','zip_sha_match','unpacked_sha_match','current_same']) for c in checks),'frames':len(frames),'matrix_max_error':max(p['matrix_max_error'] for p in poses),'strut_endpoint_max_error':max(v['max_endpoint_error'] for p in poses for v in p['struts'].values()),'strut_record_max_error':max(v['record_max_error'] for p in poses for v in p['struts'].values()),'contact_max_error':max(p['contact_record_max_error'] for p in poses),'atlas_rgba_diff':sum(f['atlas_rgba_diff'] for f in frames),'saved_gpu_pairs':len(pairs),'saved_gpu_rgba_diff':sum(v['left_right_diff']+v['left_direct_diff']+v['right_direct_diff'] for v in pairs),'contact_sheet_rgba_diff':sum(v['rgba_diff'] for v in contactsheets),'preview_roi_omitted_pixels':sum(len(f['preview_roi_omitted_points']) for f in frames),'neutral_outside_ellipses':result['neutral_source_correction']['outside_declared_ellipses']}
(OUT/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'archive':{k:v for k,v in result['archive'].items() if k!='checks'},'source':result['source'],'partition_counts':result['partition']['region_counts'],'strut_overlap_pixels':len(result['partition']['intentional_strut_overlap']),'neutral_changes':len(changes),'summary':result['summary']},ensure_ascii=False,indent=2))
