"""C1独立固定包/定长排姿/局部补丁重算；不运行生产脚本。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image
import numpy as np
import json,hashlib,math,subprocess
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];DEL=ROOT/'art-source/ember/deliveries'
ZIP=DEL/'robot_eight_way_v011_phase_c1_rc01_2026-10-07.zip'
ACTIVE=ROOT/'art-source/ember/robot-eight-way-v011/review/phase-c1-rc01'
EXPECTED='0c62177198973b24bb3fbfcc306ba4617af3ad754eb5a0696bdfddb4f19f51df'
sha=lambda b:hashlib.sha256(b).hexdigest()
z=ZipFile(ZIP);files={n:z.read(n) for n in z.namelist()};js=lambda n:json.loads(files[n]);arr=lambda n:np.array(Image.open(BytesIO(files[n])).convert('RGBA'))
assert sha(ZIP.read_bytes())==EXPECTED and ZIP.stat().st_size==19576548 and len(files)==859 and z.testzip() is None
manifest=js('sha256-manifest.json')['files'];assert len(manifest)==858 and {r['file'] for r in manifest}==set(files)-{'sha256-manifest.json'}
assert all(len(files[r['file']])==r['bytes'] and sha(files[r['file']])==r['sha256'] for r in manifest)
assert all((ACTIVE/n).read_bytes()==b for n,b in files.items())
oldfile=DEL/'robot_eight_way_v011_phase_b2_rc01_2026-10-07.zip';assert sha(oldfile.read_bytes())=='538d7bb49eb2e4480046eee50306a232b7a3f130219564e1618dbfbfff19164c';old=ZipFile(oldfile)
oldmeta=json.loads(old.read('walk-batch-metadata.json'));preserved=[f['file'] for c in oldmeta['clips'] for f in c['frames']];assert len(preserved)==72 and all(files[n]==old.read(n) for n in preserved)
assert files['robot_walk_batch_atlas_v011.png']==old.read('robot_walk_batch_atlas_v011.png')
meta=js('action-pilot-metadata.json');atlas=arr(meta['atlas']);assert sha(files[meta['atlas']])==meta['atlas_sha256'] and files[meta['atlas']]==files['godot-action-review/assets/robot_action_pilot_atlas_v011.png']
assert meta['canvas']==[64,96] and meta['root_anchor']==[32,80] and meta['direction']=='down_left' and len(meta['clips'])==4
PALETTE=np.array([[int(h[i:i+2],16) for i in (0,2,4)] for h in ['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A']],np.int32)
clipmap={c['name']:c for c in meta['clips']};pngchecks=[]
for c in meta['clips']:
 for f in c['frames']:
  a=arr(f['file']);x,y,w,h=f['region'];assert a.shape==(96,64,4) and np.array_equal(a,atlas[y:y+h,x:x+w]) and sha(files[f['file']])==f['sha256'];assert set(np.unique(a[:,:,3]))=={0,255}
  opaque=a[:,:,3]>0;assert np.all(np.any(np.all(a[:,:,:3,None]==PALETTE.T[None,None,:,:],axis=2),axis=2)[opaque]) and not np.any(a[a[:,:,3]==0,:3])
  pngchecks.append({'file':f['file'],'atlas_rgba_diff':0,'hash':f['sha256']})
assert len(pngchecks)==15
assert (clipmap['idle_down_left']['fps'],clipmap['idle_down_left']['loop'],len(clipmap['idle_down_left']['frames']))==(2,True,2)
assert (clipmap['collect_down_left']['fps'],clipmap['collect_down_left']['loop'],len(clipmap['collect_down_left']['frames']))==(6,False,4)
yy,xx=np.indices((96,64))
def stamp(a,t):
 c=math.cos(t['radians']);s=math.sin(t['radians']);dx=xx+.5-t['targetPivot'][0];dy=yy+.5-t['targetPivot'][1];sx=np.floor(dx*c+dy*s+t['sourcePivot'][0]).astype(int);sy=np.floor(-dx*s+dy*c+t['sourcePivot'][1]).astype(int)
 out=np.zeros_like(a);valid=(sx>=0)&(sx<64)&(sy>=0)&(sy<96);out[valid]=a[sy[valid],sx[valid]];return out
def render(parts,rig,state):
 out=np.zeros((96,64,4),np.uint8)
 for limb in rig['limb_order']:
  ids=['pelvis','body'] if limb=='body' else [limb+'_'+s for s in ['end','lower','upper'] if limb+'_'+s in parts]
  for k in ids:
   a=stamp(parts[k],state['transforms'][k]);pick=a[:,:,3]>0;out[pick]=a[pick]
 return out
def protect(a,y0,y1):
 out=np.zeros_like(a);ys,xs=np.where((a[:,:,3]>0)&(yy>=y0)&(yy<=y1))
 if len(xs):out[int(ys.min()):int(ys.max())+1,max(0,int(xs.min())-1):min(64,int(xs.max())+2)]=255
 return out
def point(p,t):
 x,y=np.array(p)-t['sourcePivot'];c=math.cos(t['radians']);s=math.sin(t['radians']);return np.array(t['targetPivot'])+[x*c-y*s,x*s+y*c]
def turn(v,a):return np.array([v[0]*math.cos(a)-v[1]*math.sin(a),v[0]*math.sin(a)+v[1]*math.cos(a)])
def solve(root,end,l1,l2,bend):
 v=np.array(end)-root;d=np.linalg.norm(v);axis=v/d;along=(l1*l1-l2*l2+d*d)/(2*d);off=math.sqrt(max(0,l1*l1-along*along));return root+axis*along+np.array([-axis[1],axis[0]])*off*bend
ledgers={a:js(f'source/action-rig-pilot/{a}/down_left/rig_and_poses.json') for a in ['idle','collect']};led=ledgers['idle'];rig=led['rig'];assert rig==json.loads(old.read('qa/down_left_fixed_rig_v011.json'))['rig']
parts={p['id']:arr(p['file']) for p in led['parts']};assert len(parts)==12
original={p['id']:np.array(Image.open(BytesIO(old.read(p['file']))).convert('RGBA')) for p in json.loads(old.read('qa/down_left_fixed_rig_v011.json'))['parts']}
partchecks=[]
for p in led['parts']:
 k=p['id'];expected=original['body'].copy() if k in ['body','pelvis'] else original[k]
 if k=='body':expected[56:]=0
 if k=='pelvis':expected[:54]=0
 assert np.array_equal(expected,parts[k]) and sha(parts[k].tobytes())==p['raw_sha256'];partchecks.append({'part':k,'source_rgba_diff':0})
mother=arr(led['source_file']);assert files[led['source_file']]==old.read(led['source_file']);assert sha(files[led['source_file']])==led['source_sha256']
assert np.array_equal(render(parts,rig,led['states'][0]),mother)
overlap=int(((parts['body'][54:56,:,3]>0)&(parts['pelvis'][54:56,:,3]>0)).sum())
requests=[]
for a in ['idle','collect']:
 p=js(f'qa/{a}_down_left_joint_patch_v011.json');assert sha(files[p['source_file']])==p['source_sha256'];assert p['source_size']==[Image.open(BytesIO(files[p['source_file']])).width,Image.open(BytesIO(files[p['source_file']])).height]
 requests.append({'input':str(ACTIVE/p['source_file']),'size':[128,96 if a=='idle' else 192],'output':str(OUT/f'technical-{a}-resampled.raw')})
(OUT/'technical-resample-requests.json').write_text(json.dumps(requests),encoding='utf-8')
(OUT/'technical-resample.cjs').write_text("const fs=require('node:fs/promises'),sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');(async()=>{for(const r of JSON.parse(await fs.readFile(process.argv[2],'utf8')))await fs.writeFile(r.output,await sharp(r.input).resize(...r.size,{kernel:'nearest'}).ensureAlpha().raw().toBuffer());})().catch(e=>{console.error(e);process.exitCode=1;});",encoding='utf-8')
subprocess.run(['E:/dev/node/node.EXE',str(OUT/'technical-resample.cjs'),str(OUT/'technical-resample-requests.json')],check=True,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
guards={};protectrules=[]
for k,a in parts.items():
 if k in ['body','pelvis']:guards[k]=a.copy();continue
 l=rig['limbs'][k.rsplit('_',1)[0]]
 span=[0,95] if k.endswith('_end') else ([0,math.floor(l['joint'][1]-(2.5 if l['kind']=='leg' else 1.5))] if k.endswith('_upper') else [math.ceil(l['joint'][1]+2),math.floor(l['end'][1]-2) if l['kind']=='leg' else 95])
 guards[k]=protect(a,*span);protectrules.append({'part':k,'source_y':span})
results=[]
for action,ledger in ledgers.items():
 assert ledger['parts']==led['parts'] and ledger['rig']==rig and ledger['waist_overlap_source_rows']==[54,55] and ledger['root']==[32,80] and ledger['canvas']==[64,96]
 patch=js(f'qa/{action}_down_left_joint_patch_v011.json');rows=1 if action=='idle' else 2
 sheet=np.frombuffer((OUT/f'technical-{action}-resampled.raw').read_bytes(),dtype=np.uint8).reshape(96*rows,128,4).copy();valid=sheet[:,:,3]>=160;delta=sheet[:,:,:3].astype(np.int32)[:,:,None,:]-PALETTE[None,None,:,:];idx=np.argmin(np.sum(delta*delta,axis=3),axis=2);sheet[:,:,:3]=PALETTE[idx];sheet[:,:,3]=255;sheet[~valid]=0
 previous=[];endpoint_error=0.;pose_error=0.;length_error=0.;framechecks=[]
 for i,state in enumerate(ledger['states']):
  upper=[0,-1 if i==1 else 0] if action=='idle' else [-.8,2] if i in [1,2] else [0,0];pelvis=[0,0] if action=='idle' else upper
  assert state['upper_body_shift']==upper and state['pelvis_shift']==pelvis and state['both_feet_fixed'] and not state['notes']
  assert state['transforms']['body']=={'sourcePivot':[32,54],'targetPivot':(np.array([32,54])+upper).tolist(),'radians':0}
  assert state['transforms']['pelvis']=={'sourcePivot':[32,56],'targetPivot':(np.array([32,56])+pelvis).tolist(),'radians':0}
  for id,l in rig['limbs'].items():
   j=state['joints'][id];root=np.array(l['root'])+(pelvis if l['kind']=='leg' else upper);endfield='ankle' if l['kind']=='leg' else 'wrist'
   if l['kind']=='leg':
    expectedjoint=np.array(l['joint']) if not any(pelvis) else solve(root,l['end'],np.linalg.norm(np.subtract(l['joint'],l['root'])),np.linalg.norm(np.subtract(l['end'],l['joint'])),l['bend'])
    expectedend=np.array(l['end']);assert state['transforms'][id+'_end']=={'sourcePivot':l['end'],'targetPivot':l['end'],'radians':0} and j['lift']==0 and j['contact']
   else:
    angle=0 if action=='idle' else ([.12,.42,.46,0] if l['side']=='left' else [-.05,-.12,-.12,0])[i]
    expectedjoint=root+turn(np.subtract(l['joint'],l['root']),angle);expectedend=expectedjoint+turn(np.subtract(l['end'],l['joint']),angle*.72)
   pose_error=max(pose_error,float(np.max(np.abs(j['root']-root))),float(np.max(np.abs(j['joint']-expectedjoint))),float(np.max(np.abs(j[endfield]-expectedend))))
   for p,t,target in [(l['root'],id+'_upper',j['root']),(l['joint'],id+'_upper',j['joint']),(l['joint'],id+'_lower',j['joint']),(l['end'],id+'_lower',j[endfield])]:endpoint_error=max(endpoint_error,float(np.max(np.abs(point(p,state['transforms'][t])-target))))
   for a,b,aa,bb in [(l['root'],l['joint'],j['root'],j['joint']),(l['joint'],l['end'],j['joint'],j[endfield])]:length_error=max(length_error,abs(np.linalg.norm(np.subtract(a,b))-np.linalg.norm(np.subtract(aa,bb))))
  raw=arr(ledger['frames'][i]['file']);assert np.array_equal(raw,render(parts,rig,state)) and sha(raw.tobytes())==ledger['frames'][i]['raw_sha256']
  guard=render(guards,rig,state);record=patch['records'][i];locked=(action=='idle' and i==0) or (action=='collect' and i==3);assert record['locked']==locked
  regions=[]
  if action=='idle':regions=[{'id':'waist','center':[32,54],'rx':9,'ry':3}]
  else:
   for id,j in state['joints'].items():
    if i==0 and id.startswith('leg'):continue
    for label,key,rx,ry in ([('hip','root',3.2,3.2),('knee','joint',4.8,4.8),('ankle','ankle',4,3.5)] if id.startswith('leg') else [('shoulder','root',3.4,3.4),('elbow','joint',3.5,3.5)]):regions.append({'id':id+'_'+label,'center':j[key],'rx':rx,'ry':ry})
  assert regions==record['regions'];mask=np.zeros((96,64),bool)
  if not locked:
   for r in regions:mask|=((xx+.5-r['center'][0])/r['rx'])**2+((yy+.5-r['center'][1])/r['ry'])**2<=1
   mask&=(yy>=45)&(guard[:,:,3]==0)
  assert np.array_equal(mask,arr(f'qa/{action}_down_left_joint_mask_f{i:02}.png')[:,:,3]>0)
  cell=sheet[(i//2)*96:(i//2+1)*96,(i%2)*64:(i%2+1)*64];out=raw.copy();take=mask&~((cell[:,:,3]==0)&(raw[:,:,3]>0))&~((raw[:,:,3]==0)&(cell[:,:,3]>0)&(cell[:,:,:3].astype(int).sum(axis=2)>350));out[take]=cell[take]
  shared_count=0
  if action=='collect' and i==2:
   prev=ledger['states'][1];assert all(state['transforms'][k]==prev['transforms'][k] for k in state['transforms'] if not k.startswith('arm_left_'))
   armguards={k:protect(a,0,95) if k.startswith('arm_left_') else np.zeros_like(a) for k,a in parts.items()};near=(render(armguards,rig,prev)[:,:,3]>0)|(render(armguards,rig,state)[:,:,3]>0)
   for s in [prev,state]:
    for key in ['root','joint']:
     p=s['joints']['arm_left'][key];near|=((xx+.5-p[0])/3.5)**2+((yy+.5-p[1])/3.5)**2<=1
   out[~near]=previous[1][~near];shared_count=int((~near).sum());assert shared_count==record['shared_pose_patch']['shared_pixels']
  final=arr(record['file']);diff=np.any(final!=raw,axis=2);protected=int((diff&(guard[:,:,3]>0)).sum());outside=int((diff&~mask).sum());added=(raw[:,:,3]==0)&(final[:,:,3]>0)
  assert np.array_equal(final,out) and sha(files[record['file']])==record['sha256'] and int(diff.sum())==record['changed_pixels'] and protected==outside==0 and np.all(final[added,:3].astype(int).sum(axis=1)<=350)
  previous.append(final);framechecks.append({'frame':i,'rig_reconstruction_rgba_diff':0,'final_composite_rgba_diff':0,'changed_pixels':int(diff.sum()),'protected_changed':protected,'outside_mask_changed':outside,'added_dark_core_pixels':int(added.sum()),'shared_pose_pixels':shared_count})
 assert endpoint_error<1e-10 and length_error<1e-10 and pose_error<1e-10
 assert files[f'source/action_edit_inputs_c1_rc01/{action}_down_left.png']==files[f'source/action-rig-pilot/{action}/down_left/edit_target_4x.png']
 results.append({'action':action,'endpoint_error':endpoint_error,'pose_error':pose_error,'bone_length_error':length_error,'frames':framechecks})
assert files[clipmap['idle_down_left']['frames'][0]['file']]==files[led['source_file']]
assert np.array_equal(arr(clipmap['collect_down_left']['frames'][3]['file']),arr(clipmap['idle_down_left']['frames'][0]['file']))
for f in clipmap['idle_down_left']['frames']:assert np.array_equal(arr(f['file'])[64:],mother[64:])
for f in clipmap['collect_down_left']['frames']:assert np.array_equal(arr(f['file'])[77:],mother[77:])
prov=js('qa/action_pilot_provenance.json');assert prov['atlas_sha256']==meta['atlas_sha256'];generation=[]
for g in prov['generations']:
 assert sha(files[g['source']])==g['sha256'] and sha(files[g['actual_input']])==g['input_sha256'] and sha(files[g['prompt']])==g['prompt_sha256'];generation.append({'source':g['source'],'usage':g.get('usage',g.get('status')),'sha256':g['sha256']})
assert generation[1]['usage']=='REJECTED_NOT_USED'
gpu=js('qa/godot_action_pilot_v011.json');assert gpu['technical_checks']=='PASS' and gpu['atlas_sha256']==meta['atlas_sha256'] and len(gpu['cases'])==30
for r in gpu['cases']:
 native=arr(clipmap[r['clip']]['frames'][int(r['frame'])]['file']);factor=int(r['scale']);assert np.array_equal(arr(r['file']),np.repeat(np.repeat(native,factor,axis=0),factor,axis=1)) and r['rgba_exact']
recover=gpu['collect_to_idle'];assert recover['finished_events']==[{'frame':3,'clip':'collect_down_left'}] and recover['collect_sequence']==[0,1,2,3] and recover['result_animation']=='idle_down_left' and recover['result_frame']==0 and recover['idle0_rgba_exact']
assert np.array_equal(arr('gpu-action-playback/collect_finished_to_idle0.png'),arr(clipmap['idle_down_left']['frames'][0]['file']))
collect_preview_loops=[]
for n in sorted(files):
 if not n.startswith('previews/collect_down_left_') or not n.endswith(('.gif','.webp')):continue
 im=Image.open(BytesIO(files[n]));assert im.n_frames==4
 # GIF 实际未写 NETSCAPE 循环扩展；不能把导出调用的 loop=1 误读为重复一次。
 if n.endswith('.gif'):assert 'loop' not in im.info and b'NETSCAPE2.0' not in files[n];semantic='single_no_loop_extension'
 else:assert im.info['loop']==1;semantic='webp_total_plays_1'
 collect_preview_loops.append({'file':n,'frames':4,'semantic':semantic})
assert len(collect_preview_loops)==8
result={'status':'STATIC_SOURCE_PATCH_EXPORT_PASS_PENDING_COLD','zip_sha256':EXPECTED,'bytes':ZIP.stat().st_size,'entries':859,'payload':858,'manifest_crc_active_all_same':True,'baseline_b2_sha256':sha(oldfile.read_bytes()),'accepted72_images_byte_same':True,'old_walk_atlas_byte_same':True,'atlas_sha256':meta['atlas_sha256'],'parts12':partchecks,'waist_overlap_rows':[54,55],'opaque_overlap_pixels':overlap,'neutral_rgba_diff':0,'raw_and_patch':results,'exports15':pngchecks,'idle_lower_y64_and_collect_boot_y77_fixed':True,'collect_f03_equals_idle0':True,'generations':generation,'producer_gpu_saved30_exact':True,'producer_gpu_report_sha256':sha(files['qa/godot_action_pilot_v011.json']),'producer_collect_recovery_bound':recover,'ta_gpu_rerun':False}
result['collect_animated_preview_single_play']=collect_preview_loops
if (OUT/'technical-cold-receipt.json').is_file():
 cold=json.loads((OUT/'technical-cold-receipt.json').read_text(encoding='utf-8-sig'));assert cold['status']=='PASS' and cold['zip_sha256']==EXPECTED and not cold['payload_changes_after_import'] and cold['original_payloads']==858 and cold['passed']==cold['total']==27
 assert sha((OUT/'technical-cold-probe.json').read_bytes())==cold['probe_sha256']
 for call in cold['calls']:
  assert call['exit_code']==0 and call['stderr_bytes']==0
  for stream in ['stdout','stderr']:assert sha((OUT/call[stream+'_file']).read_bytes())==call[stream+'_sha256']
 result['independent_cold']=cold;result['status']='FIXED_SOURCE_PATCH_EXPORT_AND_MINIMAL_COLD_PASS'
(OUT/'technical-binding.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'overlap':overlap,'results':results},ensure_ascii=True))
