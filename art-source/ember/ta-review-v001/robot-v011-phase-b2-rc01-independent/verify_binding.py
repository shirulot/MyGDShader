"""只读固定包独立技术核验；只将诊断/冷项目写到本审查目录。"""
from pathlib import Path
import zipfile, hashlib, json, io, math, re, subprocess
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
ZIP=ROOT/'art-source/ember/deliveries/robot_eight_way_v011_phase_b2_rc01_2026-10-07.zip'
ACTIVE=ROOT/'art-source/ember/robot-eight-way-v011/review/phase-b2-rc01'
OLD=ROOT/'art-source/ember/deliveries/robot_eight_way_v011_phase_b1_rc02_2026-10-07.zip'
EXPECTED='538d7bb49eb2e4480046eee50306a232b7a3f130219564e1618dbfbfff19164c'
PALETTE=np.array([[int(s[i:i+2],16) for i in (0,2,4)] for s in ['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A']],dtype=np.int32)
sha=lambda b:hashlib.sha256(b).hexdigest()
z=zipfile.ZipFile(ZIP); old=zipfile.ZipFile(OLD)
read=lambda f:z.read(f)
js=lambda f:json.loads(read(f))
image=lambda f:np.array(Image.open(io.BytesIO(read(f))).convert('RGBA'))
result={'status':'STATIC_IN_PROGRESS','zip':{'file':str(ZIP),'sha256':sha(ZIP.read_bytes()),'bytes':ZIP.stat().st_size,'entries':len(z.infolist()),'crc_bad':z.testzip()},'failures':[]}
def check(name,ok):
    if not ok:result['failures'].append(name)
check('zip identity',result['zip']['sha256']==EXPECTED and result['zip']['bytes']==16594983 and result['zip']['entries']==883 and result['zip']['crc_bad'] is None)
manifest=js('sha256-manifest.json')['files']
names=set(z.namelist()); payload=names-{'sha256-manifest.json'}
manifest_errors=[];active_errors=[]
for r in manifest:
    f=r['file']; b=read(f)
    if len(b)!=r['bytes'] or sha(b)!=r['sha256']:manifest_errors.append(f)
    if not (ACTIVE/f).is_file() or (ACTIVE/f).read_bytes()!=b:active_errors.append(f)
check('manifest payload exact',len(manifest)==882 and len({r['file'] for r in manifest})==882 and {r['file'] for r in manifest}==payload and not manifest_errors)
check('active package payloads match',not active_errors)
result['manifest']={'payloads':len(manifest),'set_exact':{r['file'] for r in manifest}==payload,'errors':manifest_errors,'active_errors':active_errors}
evidence=js('qa/side_walk_evidence_v011.json')
preserved=evidence['previous_batch_preserved'];old_errors=[]
for r in preserved:
    f=r['file']
    if read(f)!=old.read(f) or sha(read(f))!=r['sha256']:old_errors.append(f)
check('old 56 fixed images preserved',len(preserved)==56 and not old_errors)
result['previous']={'zip':str(OLD),'sha256':sha(OLD.read_bytes()),'images':len(preserved),'errors':old_errors}
metadata=js('walk-batch-metadata.json'); atlas=image(metadata['atlas'])
check('atlas bytes',sha(read(metadata['atlas']))==metadata['atlas_sha256'] and read(metadata['atlas'])==read('godot-walk-review/assets/robot_walk_batch_atlas_v011.png'))
png_checks=[]
for clip in metadata['clips']:
    for f in clip['frames']:
        a=image(f['file']);x,y,w,h=f['region']
        png_checks.append({'file':f['file'],'shape':list(a.shape),'hash_ok':sha(read(f['file']))==f['sha256'],'atlas_rgba_diff':int(np.any(a!=atlas[y:y+h,x:x+w],axis=2).sum()),'nonbinary_alpha':int(((a[:,:,3]!=0)&(a[:,:,3]!=255)).sum()),'off_palette':int((~np.any(np.all(a[:,:,:3,None]==PALETTE.T[None,None,:,:],axis=2),axis=2)&(a[:,:,3]>0)).sum()),'hidden_rgb_nonzero':int((np.any(a[:,:,:3]!=0,axis=2)&(a[:,:,3]==0)).sum())})
check('72 PNG metadata/atlas/alpha/palette',len(png_checks)==72 and all(v['shape']==[96,64,4] and v['hash_ok'] and not v['atlas_rgba_diff'] and not v['nonbinary_alpha'] and not v['off_palette'] for v in png_checks))
result['export']={'atlas_sha256':metadata['atlas_sha256'],'atlas_size':[atlas.shape[1],atlas.shape[0]],'clips':len(metadata['clips']),'pngs':png_checks}

# 仅调用图像库的最近邻缩放，不 require 或运行任何生产脚本。
requests=[]
for d in ['left','right']:
    led=js(f'source/fixed-rig-pilot/{d}/rig_and_poses.json')
    raw=image(led['hidden_source_registration']['source_file']); hh,ww=raw.shape[:2]; row=0 if d=='left' else 1
    for entry in led['hidden_source_registration']['parts']:
        c=entry['column']; x0=math.floor(ww*c/3);x1=math.floor(ww*(c+1)/3);y0=math.floor(hh*row/2);y1=math.floor(hh*(row+1)/2)
        yy,xx=np.where(raw[y0:y1,x0:x1,3]>=160)
        crop={'left':int(xx.min()+x0),'top':int(yy.min()+y0),'width':int(xx.max()-xx.min()+1),'height':int(yy.max()-yy.min()+1)}
        check(d+' '+entry['id']+' crop bbox',crop==entry['source_crop'])
        size=[math.floor(crop['width']*entry['height']/crop['height']+.5),entry['height']]
        check(d+' '+entry['id']+' fixed registration size',size==entry['registered_size'])
        requests.append({'id':d+'/'+entry['id'],'input':str(ACTIVE/led['hidden_source_registration']['source_file']),'crop':crop,'size':size,'output':str(OUT/f'{d}_{entry["id"]}_resampled.raw')})
    patch=js(f'qa/{d}_joint_patch_v011.json')
    requests.append({'id':d+'/patch','input':str(ACTIVE/patch['source_file']),'size':[256,192],'output':str(OUT/f'{d}_patch_resampled.raw')})
(OUT/'resample-requests.json').write_text(json.dumps(requests,indent=2),encoding='utf-8')
helper=OUT/'resample.cjs'
helper.write_text("const fs=require('node:fs/promises');const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');(async()=>{for(const r of JSON.parse(await fs.readFile(process.argv[2],'utf8'))){let s=sharp(r.input).ensureAlpha();if(r.crop)s=s.extract(r.crop);const raw=await s.resize(...r.size,{kernel:'nearest'}).raw().toBuffer();await fs.writeFile(r.output,raw);}})().catch(e=>{console.error(e);process.exitCode=1;});",encoding='utf-8')
subprocess.run(['E:/dev/node/node.EXE',str(helper),str(OUT/'resample-requests.json')],check=True,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
def quant(a):
    out=np.zeros_like(a); opaque=a[:,:,3]>=160
    delta=a[:,:,:3].astype(np.int32)[:,:,None,:]-PALETTE[None,None,:,:]
    idx=np.argmin(np.sum(delta*delta,axis=3),axis=2)
    out[opaque,:3]=PALETTE[idx[opaque]];out[opaque,3]=255
    return out
def inside(x,y,p):
    hit=False
    for i in range(len(p)):
        a=p[i];b=p[i-1]
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:hit=not hit
    return hit
def stamp(part,t):
    yy,xx=np.indices((96,64));c=math.cos(t['radians']);s=math.sin(t['radians'])
    dx=xx+.5-t['targetPivot'][0];dy=yy+.5-t['targetPivot'][1]
    sx=np.floor(dx*c+dy*s+t['sourcePivot'][0]).astype(int);sy=np.floor(-dx*s+dy*c+t['sourcePivot'][1]).astype(int)
    out=np.zeros((96,64,4),np.uint8);valid=(sx>=0)&(sx<64)&(sy>=0)&(sy<96)
    out[valid]=part[sy[valid],sx[valid]];return out
def render(parts,rig,state):
    out=np.zeros((96,64,4),np.uint8)
    for limb in rig['limb_order']:
        ids=['body'] if limb=='body' else [limb+'_'+s for s in ['end','lower','upper'] if limb+'_'+s in parts]
        for name in ids:
            a=stamp(parts[name],state['transforms'][name]);opaque=a[:,:,3]>0;out[opaque]=a[opaque]
    return out
def point(p,t):
    c=math.cos(t['radians']);s=math.sin(t['radians']);x=p[0]-t['sourcePivot'][0];y=p[1]-t['sourcePivot'][1]
    return np.array([x*c-y*s+t['targetPivot'][0],x*s+y*c+t['targetPivot'][1]])
results=[]
for d in ['left','right']:
    led=js(f'source/fixed-rig-pilot/{d}/rig_and_poses.json');rig=led['rig'];source=image(led['source_file'])
    check(d+' mother source byte hash',sha(read(led['source_file']))==led['source_sha256'])
    owner=np.full((96,64),'body',dtype=object);near_arm='arm_left' if d=='left' else 'arm_right';near_leg='leg_left' if d=='left' else 'leg_right';far_leg='leg_right' if d=='left' else 'leg_left'
    for y in range(96):
        for x in range(64):
            if not source[y,x,3]:continue
            if y>=64:owner[y,x]=far_leg if ((x>=34 and y>=70) if d=='left' else (x<=27 and y>=69)) else near_leg
            elif inside(x+.5,y+.5,led['near_arm_ownership_polygon']):owner[y,x]=near_arm
    hidden={};registrations=[]
    for e in led['hidden_source_registration']['parts']:
        w,h=e['registered_size'];small=quant(np.frombuffer((OUT/f'{d}_{e["id"]}_resampled.raw').read_bytes(),dtype=np.uint8).reshape(h,w,4))
        registered=np.zeros((96,64,4),np.uint8);rx,ry=e['xy'];outside=0;overfar=0
        for y in range(h):
            for x in range(w):
                if not small[y,x,3]:continue
                tx,ty=rx+x,ry+y
                if tx<0 or tx>=64 or ty<0 or ty>=96 or source[ty,tx,3]==0:outside+=1;continue
                if e['id']==near_leg and owner[ty,tx]==far_leg:overfar+=1;continue
                registered[ty,tx]=small[y,x]
        actual=image(e['registered_file']);diff=int(np.any(registered!=actual,axis=2).sum())
        check(d+' '+e['id']+' registered exact',diff==0 and sha(actual.tobytes())==e['raw_sha256'] and outside==e['removed_outside_neutral_silhouette'] and overfar==e['removed_near_over_far_visible_pixels'])
        hidden[e['id']]=registered;registrations.append({'id':e['id'],'rgba_diff':diff,'outside_removed':outside,'near_over_far_removed':overfar,'size':[w,h],'xy':e['xy']})
    parts={'body':np.where((owner=='body')[:,:,None],source,0).astype(np.uint8)}
    yy=np.indices((96,64))[0]
    for id,l in rig['limbs'].items():
        whole=hidden.get(id,np.zeros_like(source)).copy();visible=(owner==id)&(source[:,:,3]>0);whole[visible]=source[visible]
        for segment,pick in [('upper',yy<l['joint'][1]+2),('lower',(yy>=l['joint'][1]-2)&((yy<l['end'][1]+.5) if l['end_part'] else True))]+([('end',yy>=l['end'][1]-.5)] if l['end_part'] else []):
            parts[id+'_'+segment]=np.where(pick[:,:,None],whole,0).astype(np.uint8)
    part_diffs=[]
    for p in led['parts']:
        actual=image(p['file']);diff=int(np.any(parts[p['id']]!=actual,axis=2).sum());part_diffs.append(diff)
        check(d+' part '+p['id'],diff==0 and sha(actual.tobytes())==p['raw_sha256'])
    identity={'sourcePivot':[0,0],'targetPivot':[0,0],'radians':0}
    neutral=render(parts,rig,{'transforms':{k:identity for k in parts}})
    neutraldiff=int(np.any(neutral!=source,axis=2).sum());bodybelow=int((parts['body'][55:,:,3]>0).sum())
    check(d+' neutral mother full RGBA',neutraldiff==0);check(d+' body no limbs below y55',bodybelow==0)
    brass={}
    for side in ['left','right']:
        a=parts['arm_'+side+'_lower'];brass[side]=int((np.any(np.all(a[:,:,:3,None]==PALETTE[-3:].T[None,None,:,:],axis=2),axis=2)&(a[:,:,3]>0)).sum())
    check(d+' anatomical tool brass',brass==({'left':13,'right':0} if d=='left' else {'left':3,'right':0}))
    patch=js(f'qa/{d}_joint_patch_v011.json'); sheet=quant(np.frombuffer((OUT/f'{d}_patch_resampled.raw').read_bytes(),dtype=np.uint8).reshape(192,256,4))
    check(d+' joint source hash',sha(read(patch['source_file']))==patch['source_sha256'])
    check(d+' quantized joint source',np.array_equal(sheet,image(f'source/walk_{d}_joint_edit_quantized_v011.png')))
    guardparts={k:np.zeros_like(v) for k,v in parts.items()};guardparts['body']=parts['body'].copy();guards=[]
    for id,l in rig['limbs'].items():
        ranges=[('upper',0,math.floor(l['joint'][1]-(2.5 if l['kind']=='leg' else 1.5))),('lower',math.ceil(l['joint'][1]+2),math.floor(l['end'][1]-2) if l['kind']=='leg' else 95)]+([('end',0,95)] if l['end_part'] else [])
        for seg,y0,y1 in ranges:
            k=id+'_'+seg;a=parts[k];ys,xs=np.where((a[:,:,3]>0)&(yy>=y0)&(yy<=y1))
            if len(xs):
                x0=max(0,int(xs.min())-1);x1=min(63,int(xs.max())+1);j0=int(ys.min());j1=int(ys.max())
                guardparts[k][j0:j1+1,x0:x1+1]=255;guards.append({'part':k,'source_y':[y0,y1],'source_rect':[x0,j0,x1-x0+1,j1-j0+1]})
    check(d+' protection range records',all(any(r.get('part')==g['part'] and r.get('source_rect')==g['source_rect'] and r.get('source_y')==g['source_y'] for r in patch['protection']) for g in guards))
    frames=[];endpoint_error=0.;bone_length_error=0.;pose_error=0.;opposed=[]
    for i,state in enumerate(led['states']):
        bob=[.7,1,.6,.4,.7,1,.6,.4][i]
        check(d+f' body rigid bob{i}',state['transforms']['body']=={'sourcePivot':[32,56],'targetPivot':[32,56+bob],'radians':0} and state['bob']==bob)
        recomputed=render(parts,rig,state);raw=image(led['frames'][i]['file']);rawdiff=int(np.any(raw!=recomputed,axis=2).sum())
        check(d+f' raw rig frame{i}',rawdiff==0 and sha(raw.tobytes())==led['frames'][i]['raw_sha256'])
        guard=render(guardparts,rig,state);mask=np.zeros((96,64),bool);regions=[]
        for id,l in rig['limbs'].items():
            j=state['joints'][id]
            root=np.array(l['root'])+[0,bob]
            pose_error=max(pose_error,float(np.max(np.abs(np.array(j['root'])-root))))
            if l['kind']=='arm':
                k=(i+(4 if l['side']=='right' else 0))%8
                angle=[1,.6,0,-.6,-1,-.6,0,.6][k]*.25*(1 if d=='right' else -1)
                def rot(v,a):return np.array([v[0]*math.cos(a)-v[1]*math.sin(a),v[0]*math.sin(a)+v[1]*math.cos(a)])
                elbow=root+rot(np.subtract(l['joint'],l['root']),angle)
                wrist=elbow+rot(np.subtract(l['end'],l['joint']),angle*.65)
                pose_error=max(pose_error,float(np.max(np.abs(np.array(j['joint'])-elbow))),float(np.max(np.abs(np.array(j['wrist'])-wrist))))
            specs=[('hip','root',3.2,3.2),('knee','joint',4.8,4.8),('ankle','ankle',4,3.5)] if l['kind']=='leg' else [('shoulder','root',3.4,3.4),('elbow','joint',3.5,3.5)]
            for label,field,rx,ry in specs:
                center=j[field];regions.append({'id':id+'_'+label,'center':center,'rx':rx,'ry':ry})
                xs=np.indices((96,64))[1];ellipse=((xs+.5-center[0])/rx)**2+((yy+.5-center[1])/ry)**2<=1
                mask|=ellipse
            endfield='ankle' if l['kind']=='leg' else 'wrist'
            endpoint_error=max(endpoint_error,*[float(np.max(np.abs(point(p,state['transforms'][k])-np.array(target)))) for p,k,target in [(l['root'],id+'_upper',j['root']),(l['joint'],id+'_upper',j['joint']),(l['joint'],id+'_lower',j['joint']),(l['end'],id+'_lower',j[endfield])]])
            for a,b,aa,bb in [(l['root'],l['joint'],j['root'],j['joint']),(l['joint'],l['end'],j['joint'],j[endfield])]:bone_length_error=max(bone_length_error,abs(np.linalg.norm(np.subtract(a,b))-np.linalg.norm(np.subtract(aa,bb))))
            if l['end_part']:
                check(d+f' boot rigid{i}{id}',state['transforms'][id+'_end']['radians']==0)
                k=(i+(4 if l['side']=='right' else 0))%8;lift=[0,0,0,0,0,.5,1.1,.7][k];target=np.array(l['end'])+[rig['forward'][0]*2*[1,.6,0,-.6,-1,-.6,0,.6][k],-lift]
                check(d+f' foot phase{i}{id}',np.allclose(j[endfield],target,atol=1e-10) and j['lift']==lift and j['contact']==(lift==0))
        mask &= (yy>=45)&(guard[:,:,3]==0)
        record=patch['records'][i];check(d+f' joint ellipses{i}',regions==record['regions'])
        actualmask=image(f'qa/{d}_joint_mask_f{i:02}.png')[:,:,3]>0
        check(d+f' joint mask{i}',np.array_equal(mask,actualmask))
        cell=sheet[(i//4)*96:(i//4+1)*96,(i%4)*64:(i%4+1)*64]
        expected=raw.copy();edit=mask&~((cell[:,:,3]==0)&(raw[:,:,3]>0));expected[edit]=cell[edit]
        final=image(record['file']);changed=np.any(final!=raw,axis=2);protected=int((changed&(guard[:,:,3]>0)).sum());outside=int((changed&~mask).sum());count=int(changed.sum());compdiff=int(np.any(final!=expected,axis=2).sum())
        check(d+f' composite {i}',compdiff==0 and protected==0 and outside==0 and count==record['changed_pixels'] and sha(read(record['file']))==record['sha256'])
        frames.append({'frame':i,'raw_rgba_diff':rawdiff,'patch_composite_rgba_diff':compdiff,'changed_pixels':count,'protected_changed':protected,'outside_changed':outside,'mask_pixels':int(mask.sum())})
    for side in ['left','right']:
        j0=led['states'][0]['joints'];j4=led['states'][4]['joints'];f=np.array(rig['forward'])
        arm=float(np.dot(np.subtract(j4['arm_'+side]['wrist'],j0['arm_'+side]['wrist']),f));leg=float(np.dot(np.subtract(j4['leg_'+side]['ankle'],j0['leg_'+side]['ankle']),f));check(d+side+' opposite arm/leg phase',arm*leg<0)
        opposed.append({'side':side,'f0_to_f4_arm':arm,'f0_to_f4_leg':leg})
    check(d+' endpoint/bone lengths/arm phase',endpoint_error<1e-10 and bone_length_error<1e-10 and pose_error<1e-10 and not any(s['notes'] for s in led['states']))
    check(d+' saved edit input target preserved',read(f'source/side_edit_inputs_b2_rc01/{d}.png')==read(f'source/fixed-rig-pilot/{d}/edit_target_4x.png'))
    results.append({'direction':d,'registration':registrations,'parts':len(parts),'part_rgba_diffs':part_diffs,'neutral_rgba_diff':neutraldiff,'body_pixels_y55_plus':bodybelow,'brass_forearms':brass,'endpoint_max_error':endpoint_error,'bone_length_max_error':bone_length_error,'arm_phase_max_error':pose_error,'opposition':opposed,'frames':frames})
result['side_rig_and_patch']=results

# 复核保存的 GPU 图片；它们是制作方运行证据，不冒称本 TA 再跑 GPU。
gpu=js('qa/godot_walk_batch_v011.json');gpu_errors=[]
lookup={c['name']:c for c in metadata['clips']}
for case in gpu['cases']:
    clip=lookup[case['clip']];native=image(clip['frames'][int(case['frame'])]['file']);scale=int(case['scale']);expected=np.repeat(np.repeat(native,scale,axis=0),scale,axis=1)
    matches=[n for n in names if n.endswith('/'+case['file']) or n==case['file']]
    check('GPU evidence unique path '+case['file'],len(matches)==1)
    f=matches[0];actual=image(f)
    if not np.array_equal(expected,actual):gpu_errors.append(f)
transitions=js('qa/godot_walk_transitions_v011.json');nat=gpu['natural_playback']
check('producer saved 144 GPU images exact',len(gpu['cases'])==144 and not gpu_errors and gpu['atlas_sha256']==metadata['atlas_sha256'])
check('producer loops/transitions records bind',len(nat)==8 and all(n['actual_loops']==2 for n in nat) and len(transitions['cases'])==64 and transitions['atlas_sha256']==metadata['atlas_sha256'] and all(c['phase_preserved'] and c['gpu_rgba_exact'] for c in transitions['cases']))
result['producer_evidence']={'qa_gpu_sha256':sha(read('qa/godot_walk_batch_v011.json')),'saved_gpu_pngs':len(gpu['cases']),'saved_image_mismatches':gpu_errors,'loops_records':len(nat),'transition_records':len(transitions['cases']),'qa_transition_sha256':sha(read('qa/godot_walk_transitions_v011.json')),'ta_gpu_rerun':False}
generation_bindings=[]
for g in js('run-manifest.json')['generation']:
    if g['scope'].startswith('B2 ') or g['scope']=='W/E fixed hidden limbs':
        ok=sha(read(g['source']))==g['sha256'] and g['prompt'] in names
        if 'actual_input' in g:ok=ok and sha(read(g['actual_input']))==g['input_sha256']
        check('B2 source/prompt/input ledger '+g['scope'],ok)
        generation_bindings.append({'scope':g['scope'],'source':g['source'],'sha256':g['sha256'],'prompt':g['prompt'],'bound':ok})
result['source_generation_ledger']=generation_bindings
if (OUT/'cold-receipt.json').is_file():
    cold=json.loads((OUT/'cold-receipt.json').read_text(encoding='utf-8'))
    cold_ok=cold['status']=='PASS' and cold['zip_sha256']==EXPECTED and cold['independent_checks_passed']==cold['independent_checks_total']==96 and cold['original_payloads']==882 and not cold['payload_mismatches_after_import']
    for c in cold['calls']:
        cold_ok=cold_ok and c['exit_code']==0 and c['stderr_bytes']==0 and sha((OUT/c['stdout_file']).read_bytes())==c['stdout_sha256'] and sha((OUT/c['stderr_file']).read_bytes())==c['stderr_sha256']
    cold_ok=cold_ok and sha((OUT/'cold-probe.json').read_bytes())==cold['probe_sha256']
    check('independent cold receipt/log/file binding',cold_ok)
    result['independent_cold']=cold
result['status']=('FIXED_SOURCE_EXPORT_AND_MINIMAL_COLD_PASS' if 'independent_cold' in result else 'STATIC_SOURCE_EXPORT_PASS_PENDING_MINIMAL_COLD') if not result['failures'] else 'NEEDS_INVESTIGATION'
(OUT/'binding.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'failures':result['failures'],'sides':results},ensure_ascii=True))
