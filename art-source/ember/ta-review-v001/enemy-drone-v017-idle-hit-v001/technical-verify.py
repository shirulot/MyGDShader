"""只读独立复核 D17 固定包、原来源、刚性位姿及 PNG；不运行生产脚本。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import hashlib,json,math,re
from collections import Counter
import numpy as np
from PIL import Image
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3];DEL=ROOT/'art-source/ember/deliveries'
ZIP=DEL/'enemy_drone_idle_hit_v017_v001_2026-10-07.zip'
ACTIVE=ROOT/'art-source/ember/enemy-drone-idle-hit-v017-review-v001'
EXPECTED='19b3ba844e5df945292953520fa17a3c5a8a0c8bbf7a852a8fdd56d8e3773d05'
sha=lambda b:hashlib.sha256(b).hexdigest()
z=ZipFile(ZIP);files={n:z.read(n) for n in z.namelist()}
js=lambda n:json.loads(files[n]);arr=lambda n:np.array(Image.open(BytesIO(files[n])).convert('RGBA'))
path=lambda p:p.removeprefix('res://')
assert sha(ZIP.read_bytes())==EXPECTED and ZIP.stat().st_size==1899538 and len(files)==212 and z.testzip() is None
manifest=js('manifest.json')['files'];assert len(manifest)==211 and set(manifest)==set(files)-{'manifest.json'}
assert all(sha(files[n])==r['sha256'] and len(files[n])==r['bytes'] for n,r in manifest.items())
assert all((ACTIVE/n).read_bytes()==b for n,b in files.items())
rig=js('rig.json');cat=js('output/catalog.json');receipt=js('SOURCE_RECEIPT.json')
assert rig['canvas']==cat['canvas']==[128,128] and rig['root']==cat['root']==[64,104]
assert set(rig['actions'])=={'idle','hit'} and not any(k in rig for k in ['frames','fps','loop','body_y','rotor_angles','move'])
assert rig['actions']=={'idle':{'frames':4,'fps':4,'loop':True,'body_y':[0,-1,0,1],'roll':[0,0,0,0],'rotor_angles':[0,22.5,45,67.5]},'hit':{'frames':4,'fps':12,'loop':False,'body_y':[0,0,0,0],'roll':[0,-6,3,0],'rotor_angles':[0,15,8,0]}}
assert cat['rig_sha256']==sha(files['rig.json']) and cat['tres_sha256']==sha(files[path(cat['tres'])])
directions=['down','down_left','left','up_left','up','up_right','right','down_right']
assert rig['directions']==directions and set(rig['configs'])==set(directions)-{'down'} and len(cat['clips'])==16
baselines={}
for key,filename in [('static','enemy_drone_seven_directions_v013_s004_2026-10-06.zip'),('down','enemy_sequences_v012_2026-10-06.zip'),('rotor','enemy_drone_actions_v011_2026-10-06.zip'),('se','enemy_eight_directions_v013_pilot_drone_v001_2026-10-06.zip')]:
 p=DEL/filename; h=sha(p.read_bytes());assert h==receipt[key+'_zip_sha256'];baselines[key]={'zip':filename,'sha256':h};baselines[key]['archive']=ZipFile(p)
old=baselines['down']['archive'];static=baselines['static']['archive'];rotor=baselines['rotor']['archive']
for d in directions:
 b=files['source/'+d+'.png'];assert sha(b)==receipt['source_hashes'][d+'.png']
 assert b==(old.read('output/enemy_scout_drone/idle_down/f00.png') if d=='down' else static.read('neutral_'+d+'.png'))
 if d!='down':assert rig['configs'][d]['source']=='res://source/'+d+'.png' and sha(b)==rig['configs'][d]['source_sha256']
 assert files[f'output/enemy_scout_drone/neutral_{d}.png']==b
assert files[path(rig['fan_source'])]==rotor.read('source/rotor_well_master.png') and sha(files[path(rig['fan_source'])])==rig['fan_source_sha256']==receipt['source_hashes']['rotor_well_master.png']
assert files['provenance/rotor_well_prompt.txt']==rotor.read('source/rotor_well_prompt.txt')
assert files['provenance/s004_manifest.json']==static.read('manifest.json') and files['provenance/s004_registration.json']==static.read('provenance/static_registration_drone_s004.json')
for kind in ['idle','hit']:
 action=kind+'_down'
 for name in [f'output/enemy_scout_drone/{action}.png']+[f'output/enemy_scout_drone/{action}/f{i:02}.png' for i in range(4)]:assert files[name]==old.read(name)
 assert files['reference/enemy_scout_drone/'+action+'.png']==old.read('output/enemy_scout_drone/'+action+'.png')
master=arr(path(rig['fan_source']));screen=np.stack(np.meshgrid(np.arange(128)+.5,np.arange(128)+.5),axis=2)
rotate=lambda a:np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
clipmap={c['action']:c for c in cat['clips']};assert set(clipmap)=={k+'_'+d for k in ['idle','hit'] for d in directions}
binds=[];frames=[];cpu=[];pose_records=[];contacts=[];atlas_hashes=[]
for clip in cat['clips']:
 action=clip['action'];d=clip['direction'];kind=action.split('_')[0];state=rig['actions'][kind]
 assert clip['unit']=='enemy_scout_drone' and action==kind+'_'+d and clip['frame_count']==4 and clip['fps']==state['fps'] and clip['loop']==state['loop']
 atlas=arr(path(clip['atlas']));assert atlas.shape==(128,512,4) and sha(files[path(clip['atlas'])])==clip['atlas_sha256'];atlas_hashes.append(sha(atlas.tobytes()))
 assert len(clip['poses'])==(0 if d=='down' else 4)
 for i in range(4):
  name=path(clip['atlas'])[:-4]+f'/f{i:02}.png';a=arr(name)
  assert a.shape==(128,128,4) and sha(files[name])==clip['frame_hashes'][i] and np.array_equal(a,atlas[:,i*128:(i+1)*128]) and set(np.unique(a[:,:,3]))=={0,255}
  yy,xx=np.where(a[:,:,3]>0);assert xx.min()>0 and xx.max()<127 and yy.min()>0 and yy.max()<127
  frames.append({'action':action,'frame':i,'file':name,'sha256':sha(files[name]),'atlas_rgba_diff':0,'binary_alpha':True,'visible_bbox':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]})
  if d=='down':continue
  cfg=rig['configs'][d];source=arr(path(cfg['source']));fans=cfg['fans'];p=clip['poses'][i]
  dy=state['body_y'][i];roll=state['roll'][i];R=rotate(math.radians(roll));origin=np.array([64,67+dy])-R@np.array([64,67]);local=(screen-origin)@R
  bx=np.array(p['body_basis_x']);by=np.array(p['body_basis_y']);actualR=np.column_stack([bx,by]);posed=np.array([p['axis_world'][f['id']] for f in fans]);expected=np.array([R@f['center']+origin for f in fans]);dist=np.linalg.norm(np.subtract(fans[0]['center'],fans[1]['center']));pdist=np.linalg.norm(posed[0]-posed[1])
  error=max(float(np.max(np.abs(actualR-R))),float(np.max(np.abs(p['body_origin']-origin))),float(np.max(np.abs(posed-expected))),abs(dist-pdist))
  assert error<2e-5 and p['frame']==i and p['direction']==d and p['body_y']==dy and p['body_roll_degrees']==roll and p['root']==[64,104] and p['fans']==fans
  assert {f['id']:state['rotor_angles'][i]*f['spin'] for f in fans}==p['rotor_angles_degrees'] and [f['spin'] for f in fans]==[1,-1] and all(f['radius']==[6.5,4.5] for f in fans)
  matrices=[R@np.diag(np.array(f['radius'])/6.5)@rotate(math.radians(state['rotor_angles'][i]*f['spin'])) for f in fans]
  pose_records.append({'action':action,'frame':i,'body_origin':origin.tolist(),'body_matrix':R.tolist(),'rotor_basis_body_SR':[m.tolist() for m in matrices],'rigid_and_axis_max_error':error,'source_axis_distance':float(dist),'posed_axis_distance':float(pdist)})
  masks=[np.sum(((local-np.array(f['center']))/np.array(f['radius']))**2,axis=2)<1 for f in fans];aperture=masks[0]|masks[1]
  sx=np.floor(local[:,:,0]).astype(int);sy=np.floor(local[:,:,1]).astype(int);valid=(sx>=0)&(sx<128)&(sy>=0)&(sy<128)
  sample=np.zeros((128,128,4),np.uint8);sample[valid]=source[sy[valid],sx[valid]]
  predicted=np.full((128,128,4),255,np.uint8);predicted[:,:,3]=0
  sampled_records={}
  for fi,f in enumerate(fans):
   theta=math.radians(state['rotor_angles'][i]*f['spin']);pl=(local-np.array(f['center']))/(np.array(f['radius'])/6.5)
   for layer in ['well','rotor']:
    coords=pl if layer=='well' else pl@rotate(theta);r=rig[layer+'_rect'];uv=np.array(r[:2])+(coords+6.5)/13*np.array(r[2:]);ix=np.floor(uv[:,:,0]).astype(int);iy=np.floor(uv[:,:,1]).astype(int)
    covered=(np.sum(coords**2,axis=2)<=6.5**2)&(ix>=0)&(ix<master.shape[1])&(iy>=0)&(iy<master.shape[0]);color=np.zeros((128,128,4),np.uint8);color[covered]=master[iy[covered],ix[covered]];covered&=color[:,:,3]>=128
    predicted[covered,:3]=color[covered,:3];predicted[covered,3]=255
    for y,x in zip(*np.where(covered)):sampled_records[(int(x),int(y))]={'layer':layer,'source_float':uv[y,x].tolist(),'source_texel':[int(ix[y,x]),int(iy[y,x])]}
  shell=valid&(sample[:,:,3]>=128)&~aperture;predicted[shell,:3]=sample[shell,:3];predicted[shell,3]=255
  for y,x in zip(*np.where(shell)):sampled_records[(int(x),int(y))]={'layer':'shell','source_float':local[y,x].tolist(),'source_texel':[int(sx[y,x]),int(sy[y,x])]}
  changed=np.any(a!=predicted,axis=2);points=[]
  for y,x in zip(*np.where(changed)):
   r=sampled_records.get((int(x),int(y)),{'layer':'transparent','source_float':local[y,x].tolist(),'source_texel':[int(sx[y,x]),int(sy[y,x])]});r={**r,'output':[int(x),int(y)],'cpu_rgba':predicted[y,x].tolist(),'png_rgba':a[y,x].tolist(),'in_aperture':bool(aperture[y,x])};points.append(r)
  outside=int((changed&~aperture).sum())
  if kind=='idle' or i in [0,3]:assert outside==0
  cpu.append({'action':action,'frame':i,'full_rgba_diffs':int(changed.sum()),'alpha_diffs':int((a[:,:,3]!=predicted[:,:,3]).sum()),'outside_aperture_diffs':outside,'points':points})
  if i==0:
   delta=np.any(a!=source,axis=2);assert not np.any(delta&~aperture)
   binds.append({'action':action,'direction':d,'changed_pixels':int(delta.sum()),'aperture_pixels':int(aperture.sum()),'changed_outside':0})
   assert np.array_equal(a,arr('qa/bind_'+d+'.png'))
 for bg in ['white','black']:
  composite=np.full_like(atlas,255 if bg=='white' else 0);composite[:,:,3]=255;pick=atlas[:,:,3]>0;composite[pick]=atlas[pick]
  for factor in [1,4]:
   n=f'qa/{action}_{bg}_{factor}x.png';expected=np.repeat(np.repeat(composite,factor,axis=0),factor,axis=1);assert np.array_equal(expected,arr(n));contacts.append(n)
for d in directions:
 assert np.array_equal(arr(f'output/enemy_scout_drone/hit_{d}/f00.png'),arr(f'output/enemy_scout_drone/hit_{d}/f03.png'))
 if d!='down':assert np.array_equal(arr(f'output/enemy_scout_drone/hit_{d}/f00.png'),arr(f'output/enemy_scout_drone/idle_{d}/f00.png'))
text=files[path(cat['tres'])].decode('utf-8');rawimages=[]
for data in re.findall(r'PackedByteArray\(([^)]+)\)',text):
 raw=np.fromstring(data,sep=',',dtype=np.uint8);assert len(raw)==128*512*4;rawimages.append(sha(raw.tobytes()))
assert len(rawimages)==16 and Counter(rawimages)==Counter(atlas_hashes) and '[ext_resource' not in text
gpu=js('qa/gpu_roundtrip.json');runtime=js('qa/runtime.json');author=[]
for n in ['qa/gpu_roundtrip.json','qa/runtime.json','qa/pixel_audit.json','qa/pose_audit.json']:
 j=js(n);assert j['status']=='PASS' and j['catalog_sha256']==sha(files['output/catalog.json']);author.append({'file':n,'sha256':sha(files[n]),'catalog_bound':True,'independent_runtime_rerun':False})
new=[r for r in gpu['records'] if not r.get('preserved',False)];preserved=[r for r in gpu['records'] if r.get('preserved',False)]
assert len(new)==112 and len(preserved)==8 and {(r['action'],r['frame'],r['background']) for r in new}=={(k+'_'+d,i,b) for k in ['idle','hit'] for d in directions[1:] for i in range(4) for b in ['white','black']}
assert all(r['live_rig_vs_png']==r['tres_vs_png']==0 for r in new) and all(r['tres_vs_png']==0 for r in preserved)
assert len(runtime['players'])==32 and all(r['passed'] and r['seen_frames']==[0,1,2,3] for r in runtime['players'])
assert len(runtime['switches'])==16 and all(r['passed'] and r['frame']==2 and r['progress']==.375 for r in runtime['switches'])
authorcold=ROOT/'art-source/ember/enemy-drone-idle-hit-v017/qa/cold_receipt_v001.json';coldsource=json.loads(authorcold.read_text(encoding='utf-8-sig'));assert coldsource['zip_sha256']==EXPECTED and coldsource['status']=='PASS' and coldsource['payloads']==211
corecold=Path(coldsource['cold_project']);coldpayloadchanges=[]
for n,b in files.items():
 if not (corecold/n).is_file() or (corecold/n).read_bytes()!=b:coldpayloadchanges.append(n)
external={}
for log in authorcold.parent.glob('cold_*.log'):external[log.name]={'bytes':log.stat().st_size,'sha256':sha(log.read_bytes())}
result={'status':'STATIC_SOURCE_EXPORT_PASS_PENDING_MINIMAL_COLD','zip_sha256':EXPECTED,'zip_bytes':ZIP.stat().st_size,'entries':212,'payload':211,'manifest_crc_active_212_same':True,'baselines':{k:{n:v for n,v in b.items() if n!='archive'} for k,b in baselines.items()},'source8_preserved':True,'original_down8_frames_and2atlases_same':True,'rotor_v011_not_r1_same':True,'rig_only_actions_no_top_move':True,'catalog_sha256':sha(files['output/catalog.json']),'binds':binds,'frames64':frames,'poses56':pose_records,'hit_recovery8_rgba_same':True,'embedded16images_rgba_same':True,'contacts64_rgba_same':True,'cpu_reconstruction':cpu,'author_bindings':author,'author_gpu_new112_old8':True,'author_players32_and_switches16':True,'author_gpu_raw_saved_pngs':0,'author_cold':{'receipt_sha256':sha(authorcold.read_bytes()),'receipt':coldsource,'payload_mismatches_vs_zip':coldpayloadchanges,'logs':external},'ta_gpu_rerun':False}
if coldpayloadchanges==['qa/runtime.json']:
 authorruntime=json.loads((corecold/'qa/runtime.json').read_text(encoding='utf-8-sig'))
 differences={k:{'fixed_zip':runtime.get(k),'author_cold':authorruntime.get(k)} for k in set(runtime)|set(authorruntime) if runtime.get(k)!=authorruntime.get(k)}
 assert set(differences)=={'elapsed_ms'}
 result['author_cold']['runtime_only_elapsed_difference']=differences
if (OUT/'technical-cold-receipt.json').is_file():
 cold=json.loads((OUT/'technical-cold-receipt.json').read_text(encoding='utf-8-sig'))
 assert cold['status']=='PASS' and cold['zip_sha256']==EXPECTED and cold['passed']==cold['total']==25 and cold['original_payloads']==211 and not cold['payload_changes_after_import']
 assert sha((OUT/'technical-cold-probe.json').read_bytes())==cold['probe_sha256']
 for c in cold['calls']:
  assert c['exit_code']==0 and c['stderr_bytes']==0 and sha((OUT/c['stdout_file']).read_bytes())==c['stdout_sha256'] and sha((OUT/c['stderr_file']).read_bytes())==c['stderr_sha256']
 result['independent_cold']=cold
 result['status']='FIXED_SOURCE_EXPORT_AND_MINIMAL_COLD_PASS'
(OUT/'technical-binding.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'binds':binds,'cpu_pixel_diff_total':sum(r['full_rgba_diffs'] for r in cpu),'alpha_diffs_total':sum(r['alpha_diffs'] for r in cpu),'outside_diffs_total':sum(r['outside_aperture_diffs'] for r in cpu),'author_cold_payload_changes':coldpayloadchanges},ensure_ascii=True))
