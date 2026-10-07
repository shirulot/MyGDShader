"""C2 TA 独立重算；只读固定包，不运行生产构建脚本。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image
import numpy as np
import json, hashlib, math, subprocess

OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[3]; P=OUT/'technical-package'
DEL=ROOT/'art-source/ember/deliveries'; sha=lambda b:hashlib.sha256(b).hexdigest()
js=lambda n:json.loads((P/n).read_text(encoding='utf-8'))
arr=lambda n:np.array(Image.open(P/n).convert('RGBA'))
files={f.relative_to(P).as_posix():f.read_bytes() for f in P.rglob('*') if f.is_file()}
manifest=js('sha256-manifest.json')['files']
assert len(manifest)==1702 and {m['file'] for m in manifest}==set(files)-{'sha256-manifest.json'}
assert all(len(files[m['file']])==m['bytes'] and sha(files[m['file']])==m['sha256'] for m in manifest)
meta=js('full-action-metadata.json'); assert sha(files['full-action-metadata.json'])=='8072ce3ef444d8c2d3c13cf072380c7398385997b008c01269d0bb3c6d210b6e'
assert sha(files['sha256-manifest.json'])=='27b6448dbb0de738fc87b45dc17924dafedec3af8dee47f4512f256a4f02ba4d'
assert meta['canvas']==[64,96] and meta['root_anchor']==[32,80] and meta['total_clips']==24 and meta['total_frames']==112 and meta['new_frames']==42
atlas=arr(meta['atlas']); assert atlas.shape==(2304,512,4) and sha(files[meta['atlas']])==meta['atlas_sha256']=='c9963cd1f9c1db11a932164c57eefde0ed80e2de692f0d3700338d7bddba6cc1'
assert files[meta['atlas']]==files['godot-full-review/assets/robot_eight_way_actions_atlas_v011.png']
oldpath=DEL/'robot_eight_way_v011_phase_c1_rc01_2026-10-07.zip'
assert sha(oldpath.read_bytes())=='0c62177198973b24bb3fbfcc306ba4617af3ad754eb5a0696bdfddb4f19f51df'
old=ZipFile(oldpath)
preserved=[n for n in old.namelist() if n.startswith('frames/walk/') and n.endswith('.png')]
preserved += [n for n in old.namelist() if (n.startswith('frames/idle/down_left/') or n.startswith('frames/collect/down_left/')) and n.endswith('.png')]
preserved += [n for n in old.namelist() if n.startswith('source/candidate-masters/robot_idle_') and n.endswith('.png')]
assert len(preserved)==78 and all(files[n]==old.read(n) for n in preserved)
PALETTE=np.array([[int(h[i:i+2],16) for i in (0,2,4)] for h in ['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A']],np.int32)
exports=[]; clipmap={c['name']:c for c in meta['clips']}
for c in meta['clips']:
 expected={'idle':(2,2,True),'walk':(8,8,True),'collect':(4,6,False)}[c['action']]
 assert (len(c['frames']),c['fps'],c['loop'])==expected
 for f in c['frames']:
  a=arr(f['file']); x,y,w,h=f['region']; assert a.shape==(96,64,4) and np.array_equal(a,atlas[y:y+h,x:x+w]) and sha(files[f['file']])==f['sha256']
  assert set(np.unique(a[:,:,3]))=={0,255} and not np.any(a[a[:,:,3]==0,:3])
  opaque=a[:,:,3]>0; assert np.all(np.any(np.all(a[:,:,:3,None]==PALETTE.T[None,None,:,:],axis=2),axis=2)[opaque])
  exports.append({'file':f['file'],'sha256':f['sha256'],'atlas_rgba_diff':0})
assert len(exports)==112
yy,xx=np.indices((96,64))
def stamp(a,t):
 c=math.cos(t['radians']); s=math.sin(t['radians']); dx=xx+.5-t['targetPivot'][0]; dy=yy+.5-t['targetPivot'][1]
 sx=np.floor(dx*c+dy*s+t['sourcePivot'][0]).astype(int); sy=np.floor(-dx*s+dy*c+t['sourcePivot'][1]).astype(int)
 out=np.zeros_like(a); valid=(sx>=0)&(sx<64)&(sy>=0)&(sy<96); out[valid]=a[sy[valid],sx[valid]]; return out
def render(parts,rig,state):
 out=np.zeros((96,64,4),np.uint8)
 for limb in rig['limb_order']:
  ids=['pelvis','body'] if limb=='body' else [limb+'_'+s for s in ['end','lower','upper'] if limb+'_'+s in parts]
  for k in ids:
   a=stamp(parts[k],state['transforms'][k]); pick=a[:,:,3]>0; out[pick]=a[pick]
 return out
def protect(a,y0,y1):
 out=np.zeros_like(a); ys,xs=np.where((a[:,:,3]>0)&(yy>=y0)&(yy<=y1))
 if len(xs):out[int(ys.min()):int(ys.max())+1,max(0,int(xs.min())-1):min(64,int(xs.max())+2)]=255
 return out
def point(p,t):
 x,y=np.array(p)-t['sourcePivot']; c=math.cos(t['radians']); s=math.sin(t['radians']); return np.array(t['targetPivot'])+[x*c-y*s,x*s+y*c]
def turn(v,a):return np.array([v[0]*math.cos(a)-v[1]*math.sin(a),v[0]*math.sin(a)+v[1]*math.cos(a)])
def solve(root,end,l1,l2,bend):
 v=np.array(end)-root; d=np.linalg.norm(v); axis=v/d; along=(l1*l1-l2*l2+d*d)/(2*d); off=math.sqrt(max(0,l1*l1-along*along)); return root+axis*along+np.array([-axis[1],axis[0]])*off*bend

directions=['down','left','up_left','up','up_right','right','down_right']; requests=[]; generations=[]
for d in directions:
 for action in ['idle','collect']:
  patch=js(f'qa/{action}_{d}_joint_patch_v011.json'); rows=1 if action=='idle' else 2
  assert sha(files[patch['source_file']])==patch['source_sha256']
  im=Image.open(P/patch['source_file']); assert patch['source_size']==list(im.size)
  assert np.max(np.abs(np.array(patch['common_sheet_transform'])-[128/im.width,96*rows/im.height]))<1e-12
  assert abs(im.width/im.height-128/(96*rows))<.001
  requests.append({'input':str(P/patch['source_file']),'size':[128,96*rows],'output':str(OUT/f'technical-resampled-{action}-{d}.raw')})
run=js('run-manifest.json')
for g in run['generation']:
 if not g.get('scope','').startswith('C2 '):continue
 assert sha(files[g['source']])==g['sha256'] and sha(files[g['actual_input']])==g['input_sha256'] and sha(files[g['prompt']])==g['prompt_sha256']
 rigfolder=f'source/action-rig-batch/{g["action"]}/{g["direction"]}'
 assert files[g['actual_input']]==files[rigfolder+'/edit_target_4x.png']
 generations.append({'direction':g['direction'],'action':g['action'],'source':g['source'],'source_sha256':g['sha256'],'input':g['actual_input'],'input_sha256':g['input_sha256'],'prompt':g['prompt'],'prompt_sha256':g['prompt_sha256'],'original_output':g['original_output']})
assert len(generations)==14 and len({g['original_output'] for g in generations})==14
(OUT/'technical-resample-requests.json').write_text(json.dumps(requests),encoding='utf-8')
(OUT/'technical-resample.cjs').write_text("const fs=require('node:fs/promises'),sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');(async()=>{for(const r of JSON.parse(await fs.readFile(process.argv[2],'utf8')))await fs.writeFile(r.output,await sharp(r.input).resize(...r.size,{kernel:'nearest'}).ensureAlpha().raw().toBuffer());})().catch(e=>{console.error(e);process.exitCode=1;});",encoding='utf-8')
subprocess.run(['E:/dev/node/node.EXE',str(OUT/'technical-resample.cjs'),str(OUT/'technical-resample-requests.json')],check=True,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
results=[]; registrations=[]
for d in directions:
 registration=js(f'source/action-source-registration/{d}/registration.json'); rig=registration['rig']; parts={p['id']:arr(p['file']) for p in registration['parts']}
 assert len(parts)==12 and all(sha(parts[p['id']].tobytes())==p['raw_sha256'] for p in registration['parts'])
 mother=arr(registration['source_file']); assert sha(files[registration['source_file']])==registration['source_sha256']
 sourcepartcheck=[]
 if d!='down':
  prior=json.loads(old.read(f'qa/{d}_fixed_rig_v011.json')); rcopy=dict(rig);rcopy.pop('action_waist_overlap');assert rcopy==prior['rig']
  originals={p['id']:np.array(Image.open(BytesIO(old.read(p['file']))).convert('RGBA')) for p in prior['parts']}
  for part in registration['parts']:
   k=part['id']; expected=originals['body'].copy() if k in ['body','pelvis'] else originals[k]
   if k=='body':expected[56:]=0
   if k=='pelvis':expected[:54]=0
   assert np.array_equal(parts[k],expected);sourcepartcheck.append({'part':k,'prior_source_rgba_diff':0})
  assert files[registration['source_file']]==old.read(registration['source_file'])
 else:
  # S neutral 的 1px/5点生成来源由 neutral-* 独立专项承担，主报告只重算其登记片/动作。
  sourcepartcheck.append({'scope':'S neutral provenance delegated to neutral-binding.json; fixed part raw hashes verified here'})
 overlap=registration['waist_overlap_source_rows']; assert overlap==([58,59] if d=='down' else [54,55])
 registrations.append({'direction':d,'source_file':registration['source_file'],'source_sha256':registration['source_sha256'],'parts':sourcepartcheck,'waist_overlap_rows':overlap,'opaque_body_pelvis_overlap':int(((parts['body'][overlap[0]:overlap[1]+1,:,3]>0)&(parts['pelvis'][overlap[0]:overlap[1]+1,:,3]>0)).sum())})
 guards={}; guardrules=[]
 for k,a in parts.items():
  if k in ['body','pelvis']:guards[k]=a.copy();continue
  limb=rig['limbs'][k.rsplit('_',1)[0]]
  span=[0,95] if k.endswith('_end') else ([0,math.floor(limb['joint'][1]-(2.5 if limb['kind']=='leg' else 1.5))] if k.endswith('_upper') else [math.ceil(limb['joint'][1]+2),math.floor(limb['end'][1]-2) if limb['kind']=='leg' else 95])
  guards[k]=protect(a,*span); guardrules.append({'part':k,'source_y':span})
 for action in ['idle','collect']:
  ledger=js(f'source/action-rig-batch/{action}/{d}/rig_and_poses.json'); patch=js(f'qa/{action}_{d}_joint_patch_v011.json')
  assert ledger['parts']==registration['parts'] and ledger['rig']==rig and ledger['waist_overlap_source_rows']==overlap and ledger['root']==[32,80] and ledger['canvas']==[64,96]
  rows=1 if action=='idle' else 2;sheet=np.frombuffer((OUT/f'technical-resampled-{action}-{d}.raw').read_bytes(),dtype=np.uint8).reshape(rows*96,128,4).copy()
  valid=sheet[:,:,3]>=160; delta=sheet[:,:,:3].astype(np.int32)[:,:,None,:]-PALETTE[None,None,:,:]; idx=np.argmin(np.sum(delta*delta,axis=3),axis=2);sheet[:,:,:3]=PALETTE[idx];sheet[:,:,3]=255;sheet[~valid]=0
  previous=[]; framechecks=[]; pose_error=endpoint_error=length_error=0.
  for i,state in enumerate(ledger['states']):
   upper=[0,-1 if i==1 else 0] if action=='idle' else [rig['forward'][0]*.8,1 if rig['forward'][0]==0 else 2] if i in [1,2] else [0,0];pelvis=[0,0] if action=='idle' else upper
   assert state['upper_body_shift']==upper and state['pelvis_shift']==pelvis and state['both_feet_fixed'] and not state['notes']
   for k,pivot,shift in [('body',[32,54],upper),('pelvis',[32,56],pelvis)]:assert state['transforms'][k]=={'sourcePivot':pivot,'targetPivot':(np.array(pivot)+shift).tolist(),'radians':0}
   for id,l in rig['limbs'].items():
    j=state['joints'][id];root=np.array(l['root'])+(pelvis if l['kind']=='leg' else upper);endfield='ankle' if l['kind']=='leg' else 'wrist'
    l1=np.linalg.norm(np.subtract(l['joint'],l['root']));l2=np.linalg.norm(np.subtract(l['end'],l['joint']))
    if l['kind']=='leg':
     expectedjoint=np.array(l['joint']) if not any(pelvis) else solve(root,l['end'],l1,l2,l['bend']);expectedend=np.array(l['end'])
     assert state['transforms'][id+'_end']=={'sourcePivot':l['end'],'targetPivot':l['end'],'radians':0} and j['lift']==0 and j['contact']
    elif action=='collect' and rig['forward'][0]==0 and i!=3:
     reach=([.03,.15,.20,0] if rig['forward'][1]>0 else [-.2,-.9,-1.,0])[i] if l['side']=='left' else [0,-.3,-.3,0][i]
     expectedend=np.array(l['end'])+upper+[0,reach];expectedjoint=solve(root,expectedend,l1,l2,l['bend'])
    else:
     sign=1 if rig['forward'][0]<0 else -1;angle=0 if action=='idle' else ([.12,.42,.46,0] if l['side']=='left' else [-.05,-.12,-.12,0])[i]*sign
     expectedjoint=root+turn(np.subtract(l['joint'],l['root']),angle);expectedend=expectedjoint+turn(np.subtract(l['end'],l['joint']),angle*.72)
    pose_error=max(pose_error,float(np.max(np.abs(np.array(j['root'])-root))),float(np.max(np.abs(np.array(j['joint'])-expectedjoint))),float(np.max(np.abs(np.array(j[endfield])-expectedend))))
    for src,t,target in [(l['root'],id+'_upper',j['root']),(l['joint'],id+'_upper',j['joint']),(l['joint'],id+'_lower',j['joint']),(l['end'],id+'_lower',j[endfield])]:endpoint_error=max(endpoint_error,float(np.max(np.abs(point(src,state['transforms'][t])-target))))
    for a,b,aa,bb in [(l['root'],l['joint'],j['root'],j['joint']),(l['joint'],l['end'],j['joint'],j[endfield])]:length_error=max(length_error,abs(np.linalg.norm(np.subtract(a,b))-np.linalg.norm(np.subtract(aa,bb))))
   raw=arr(ledger['frames'][i]['file']); assert np.array_equal(raw,render(parts,rig,state)) and sha(raw.tobytes())==ledger['frames'][i]['raw_sha256']
   guard=render(guards,rig,state); record=patch['records'][i];locked=(action=='idle' and i==0) or (action=='collect' and i==3);assert record['locked']==locked
   regions=[]
   if action=='idle':regions=[{'id':'waist','center':[32,58 if d=='down' else 54],'rx':11 if d=='down' else 9,'ry':3}]
   else:
    for id,j in state['joints'].items():
     if i==0 and id.startswith('leg'):continue
     for label,key,rx,ry in ([('hip','root',3.2,3.2),('knee','joint',4.8,4.8),('ankle','ankle',4,3.5)] if id.startswith('leg') else [('shoulder','root',3.4,3.4),('elbow','joint',3.5,3.5)]):regions.append({'id':id+'_'+label,'center':j[key],'rx':rx,'ry':ry})
   assert regions==record['regions']; mask=np.zeros((96,64),bool)
   if not locked:
    for r in regions:mask|=((xx+.5-r['center'][0])/r['rx'])**2+((yy+.5-r['center'][1])/r['ry'])**2<=1
    mask&=(yy>=45)&(guard[:,:,3]==0)
   assert np.array_equal(mask,arr(f'qa/{action}_{d}_joint_mask_f{i:02d}.png')[:,:,3]>0)
   cell=sheet[(i//2)*96:(i//2+1)*96,(i%2)*64:(i%2+1)*64]; out=raw.copy()
   take=mask&~((cell[:,:,3]==0)&(raw[:,:,3]>0))&~((raw[:,:,3]==0)&(cell[:,:,3]>0)&(cell[:,:,:3].astype(int).sum(axis=2)>350))
   padded=np.pad(raw[:,:,3]>0,1);touch=np.zeros((96,64),bool)
   for dy in range(3):
    for dx in range(3):touch|=padded[dy:dy+96,dx:dx+64]
   detached=take&(raw[:,:,3]==0)&(cell[:,:,3]>0)&~touch;rejected=int(detached.sum());take&=~detached;out[take]=cell[take]
   assert rejected==record['rejected_detached_additions']
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
   previous.append(final);framechecks.append({'frame':i,'raw_rig_rgba_diff':0,'patch_final_rgba_diff':0,'changed_pixels':int(diff.sum()),'protected_changed':protected,'outside_mask_changed':outside,'added_dark_core':int(added.sum()),'detached_rejected':rejected,'shared_pose_pixels':shared_count})
  assert endpoint_error<1e-10 and pose_error<1e-10 and length_error<1e-10
  assert np.array_equal(previous[0 if action=='idle' else 3],mother)
  results.append({'direction':d,'action':action,'pose_error':pose_error,'endpoint_error':endpoint_error,'bone_length_error':length_error,'frames':framechecks})
 assert np.array_equal(arr(clipmap['collect_'+d]['frames'][3]['file']),arr(clipmap['idle_'+d]['frames'][0]['file']))

gpu=js('qa/godot_full_actions_v011.json')
assert gpu['atlas_sha256']==meta['atlas_sha256'] and gpu['technical_checks']=='PASS' and len(gpu['cases'])==224
assert all(case['rgba_exact'] and case['file'] in files for case in gpu['cases'])
result={'status':'FIXED_SOURCE_PATCH_EXPORT_PASS_PENDING_COLD','manifest_payloads':1702,'manifest_bytes_hashes_exact':True,'manifest_sha256':sha(files['sha256-manifest.json']),'metadata_sha256':sha(files['full-action-metadata.json']),'atlas_sha256':meta['atlas_sha256'],'preserved78':preserved,'preserved_byte_differences':0,'registrations':registrations,'new42_raw_and_patch':results,'exports112':exports,'generations14':generations,'S_neutral_source_deep_review':'neutral-binding.json (independent other agent; not repeated here)','author_gpu224_bound_only':{'qa_sha256':sha(files['qa/godot_full_actions_v011.json']),'records':224,'all_records_present_and_reported_exact':True},'gpu_replayed':False}
(OUT/'technical-binding.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'exports':len(exports),'registrations':len(registrations),'new_frames':sum(len(z['frames']) for z in results),'changed':{z['action']+'_'+z['direction']:[f['changed_pixels'] for f in z['frames']] for z in results}},ensure_ascii=False))
