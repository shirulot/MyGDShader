"""C24：独立绑定来源、像素归属、动作数学、固定脚与 UV 输出。保留 CPU 采样残差。"""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import ast,hashlib,json,math
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];P=OUT/'technical-package'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
js=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
arr=lambda p:np.array(Image.open(p).convert('RGBA'))
rig,cat,receipt=js(P/'rig.json'),js(P/'output/catalog.json'),js(P/'SOURCE_RECEIPT.json')
cold=js(OUT/'technical-minimal-cold-load.json');assert cold['status']=='PASS' and cold['frames']==112
assert cat['canvas']==[128,128] and cat['root']==[64,104] and sha(P/'rig.json')==cat['rig_sha256'] and sha(P/cat['tres'].removeprefix('res://'))==cat['tres_sha256']
C22=OUT.with_name('enemy-cutter-v022-six-moves-v002')/'technical-package'
HC=ROOT/'art-source/ember/deliveries/enemy_eight_directions_v013_pilot_hc_v001_2026-10-06.zip'
assert sha(HC)==receipt['se_first_gate_zip_sha256']=='5db52757c74fc537b3f45d87abdbab8c58e5d8fcd3cf6366153f7b32ef98b9ef'
sources=[]
with ZipFile(HC) as z:
    for d,c in rig['configs'].items():
        src=P/c['source'].removeprefix('res://');assert sha(src)==c['source_sha256']==receipt['source_png_hashes'][d+'.png']
        if d=='down_right':
            assert src.read_bytes()==z.read('output/enemy_cutter/rig_neutral_down_right.png')==(P/'provenance/approved_hc_neutral.png').read_bytes()
        else:assert src.read_bytes()==(C22/f'source/{d}.png').read_bytes()
        sources.append({'direction':d,'sha256':sha(src),'approved_source':'HC actual assembled rig_neutral' if d=='down_right' else 'C22 approved same source'})
provenance=[]
for f in (P/'provenance').rglob('*'):
    if f.is_file() and (C22/f.relative_to(P)).exists():
        assert f.read_bytes()==(C22/f.relative_to(P)).read_bytes();provenance.append(f.relative_to(P).as_posix())
downzip=ROOT/'art-source/ember/deliveries/enemy_sequences_v012_2026-10-06.zip';assert sha(downzip)==receipt['down_zip_sha256']
preserved=[]
with ZipFile(downzip) as z:
    for c in cat['clips']:
        if c['direction']!='down':continue
        path=c['atlas'].removeprefix('res://')
        for name in [path]+[path[:-4]+f'/f{i:02d}.png' for i in range(c['frame_count'])]:
            choices=[v for v in z.namelist() if v==name or v.endswith('/'+name.removeprefix('output/'))]
            assert len(choices)==1 and (P/name).read_bytes()==z.read(choices[0]);preserved.append(name)
exports=[]
for c in cat['clips']:
    kind=c['action'].split('_')[0];n=6 if kind=='attack' else 8
    assert c['frame_count']==n and c['fps']==10 and c['loop'] is False
    path=c['atlas'].removeprefix('res://');a=arr(P/path);assert a.shape==(128,n*128,4) and sha(P/path)==c['atlas_sha256']
    images=[]
    for i in range(n):
        fp=P/(path[:-4]+f'/f{i:02d}.png');im=arr(fp);images.append(im)
        assert sha(fp)==c['frame_hashes'][i] and im.shape==(128,128,4) and np.array_equal(im,a[:,i*128:(i+1)*128]) and set(np.unique(im[:,:,3]))=={0,255}
        ys,xs=np.where(im[:,:,3]>0);bbox=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
        assert bbox[0]>0 and bbox[1]>0 and bbox[2]<128 and bbox[3]<128
        if c['direction']!='down':assert bbox[3]<=104
        exports.append({'action':c['action'],'frame':i,'sha256':sha(fp),'atlas_rgba_equal':True,'bbox':bbox})
    assert np.array_equal(images[0],images[-1]) if kind=='attack' else all(np.array_equal(images[-1],im) for im in images[-3:])
assert len(exports)==112
yy,xx=np.indices((128,128));X,Y=xx+.5,yy+.5
helper=OUT.with_name('enemy-cutter-v022-six-moves-v002')/'technical-audit.py';tree=ast.parse(helper.read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['poly','close','uv_sample']],type_ignores=[]),str(helper),'exec'))
def rot(degrees):
    angle=math.radians(degrees);return np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
def trans(basis,position):return {'position':list(position),'basis_x':list(basis[:,0]),'basis_y':list(basis[:,1])}
def quad(a,b,width):
    a,b=np.array(a),np.array(b);d=b-a;n=np.array([-d[1],d[0]])/np.linalg.norm(d)*width*.5
    return np.array([a-n,a+n,b+n,b-n])
def blank():
    im=np.full((128,128,4),255,np.uint8);im[:,:,3]=0;return im
def sampled(src,mask,t,pivot):
    # Inverse-map canvas pixel centers into the fixed full-size source texture.
    basis=np.array([t['basis_x'],t['basis_y']]).T;inv=np.linalg.inv(basis)
    dx,dy=X-t['position'][0],Y-t['position'][1]
    sx=np.floor(inv[0,0]*dx+inv[0,1]*dy+pivot[0]).astype(int);sy=np.floor(inv[1,0]*dx+inv[1,1]*dy+pivot[1]).astype(int)
    valid=(sx>=0)&(sx<128)&(sy>=0)&(sy<128);cx,cy=np.clip(sx,0,127),np.clip(sy,0,127)
    valid&=mask[cy,cx]&(src[cy,cx,3]>0)
    image=blank();image[valid]=src[cy[valid],cx[valid]]
    return image,valid,sx,sy
expected_actions={
 'attack':{'body_y':[0,-1,-1,1,0,0],'swing':[0,-.35,-.6,1,.3,0],'blade':[0,15,30,45,15,0],'fold':[0]*6,'power':[1]*6},
 'death':{'body_y':[0,1,2,4,6,7,7,7],'swing':[0,.2,.4,.65,.85,1,1,1],'blade':[0,15,25,30,32,32,32,32],'fold':[0,5,12,25,42,55,55,55],'power':[1,.6,.2,0,0,0,0,0]}}
for action,values in expected_actions.items():
    for key,value in values.items():assert rig['actions'][action][key]==value
bindings=[];frames=[];sockets=[]
for d,cfg in rig['configs'].items():
    src=arr(P/f'source/{d}.png');opaque=src[:,:,3]>0
    pivots={'body':[0,0]};zorder={'body':5};link_specs={}
    for p in cfg['parts']:
        pivots[p['id']]=p['pivot'];pivots[p['id']+'_foot']=[0,0]
        zorder[p['id']]=zorder[p['id']+'_foot']=0;link_specs[p['id']]=p['socket']
    for t in cfg['tools']:
        pivots[t['id']]=t['pivot'];zorder[t['id']]=6
        if t['blade_polygon']:pivots[t['id']+'_blade']=t['hub'];zorder[t['id']+'_blade']=6
        if 'socket' in t:link_specs[t['id']]=t['socket']
        if 'spindle' in t:link_specs[t['id']+'_spindle']=t['spindle']
    owner=np.full((128,128),'body',dtype='U32');protected=np.zeros((128,128),bool)
    for shape in cfg['protected_body_polygons']:protected|=poly(shape)
    for p in reversed(cfg['parts']):
        use=poly(p['polygon'])&~protected;owner[use]=p['id'];owner[use&(Y>=p['foot_cut_y'])]=p['id']+'_foot'
    for t in reversed(cfg['tools']):
        use=poly(t['polygon'])
        for shape in t['extra_polygons']:use|=poly(shape)
        owner[use]=t['id']
        if t['blade_polygon']:owner[use&poly(t['blade_polygon'])]=t['id']+'_blade'
    for item in reversed(cfg['ownership_overrides']):owner[poly(item['polygon'])]=item['owner']
    masks={name:owner==name for name in pivots};assert np.all(sum(m.astype(int) for m in masks.values())==1)
    runtime=next(r for r in cold['rig_checks'] if r['direction']==d)
    for m in runtime['masks']:
        name=m['id'];actual=np.array(Image.open(OUT/f'technical-runtime-mask-{d}-{name}.png').convert('L'))>0
        assert np.array_equal(actual,masks[name]) and m['pivot']==pivots[name] and m['sprite_position']==[-v for v in pivots[name]] and m['z']==zorder[name] and not m['centered'] and m['filter']==1
        Image.fromarray((masks[name]*255).astype(np.uint8)).save(OUT/f'technical-mask-{d}-{name}.png')
        # Author part captures have transparent-black RGB; compare alpha and all visible source RGBA.
        part=arr(P/f'qa/parts/{d}/{name}.png');use=masks[name]&opaque
        assert np.array_equal(part[:,:,3]>0,use) and np.array_equal(part[use],src[use])
    assert set(m['id'] for m in runtime['masks'])==set(masks)
    assert np.array_equal(arr(P/f'qa/bind_{d}.png'),src)
    for action in ['attack','death']:assert np.array_equal(arr(P/f'output/enemy_cutter/{action}_{d}/f00.png'),src)
    for link in runtime['links']:
        name=link['id'];r=link_specs[name]['source_rect'];x,y,w,h=r
        expected_uv=[[x+.001,y+.001],[x+w-.001,y+.001],[x+w-.001,y+h-.001],[x+.001,y+h-.001]]
        assert close(link['uv'],expected_uv) and link['z']==-10 and link['filter']==1 and link['texture_size']==[128,128]
        assert [w,h]==[2,2]
        sockets.append({'direction':d,'id':name,'source_rect':r,'rgba4':src[y:y+h,x:x+w].reshape(-1,4).tolist(),'source_opaque_pixels':int(np.sum(src[y:y+h,x:x+w,3]>0)),'width':link_specs[name]['width'],'runtime_uv_exact':True})
    bindings.append({'direction':d,'opaque_source':int(opaque.sum()),'owned_opaque':{k:int(np.sum(m&opaque)) for k,m in masks.items()},'source_pixel_unique':True,'masks_runtime_equal':True,'part_source_rgba_equal':True,'bind_rgba_diff':0,'tools':[t['id'] for t in cfg['tools']],'hidden_legs':cfg['hidden_legs'],'attack_note':cfg['attack_note'],'sensor_rect':cfg['sensor_rect']})
    for action,values in expected_actions.items():
      clip=next(v for v in cat['clips'] if v['action']==action+'_'+d)
      for i in range(len(values['body_y'])):
        body=np.array([0,values['body_y'][i]]);transforms={name:trans(np.eye(2),np.array(pivot)) for name,pivot in pivots.items()};transforms['body']=trans(np.eye(2),body)
        polygons={};supports={}
        for p in cfg['parts']:
            name=p['id'];angle=values['fold'][i]*p['fold_sign']*p['fold_multiplier']
            if p['sole'] is not None:
                basis=rot(angle);ankle=np.array(p['ankle']);position=ankle+basis@(np.array(p['pivot'])-ankle)
            else:basis=np.eye(2);position=np.array(p['pivot'])+body
            transforms[name]=trans(basis,position)
            s=p['socket'];start=np.array(s['start'])+body;end=basis@(np.array(s['end'])-np.array(p['pivot']))+position
            polygons[name]=quad(start,end,s['width'])
            supports[name]={'sole':p['sole'],'ground':p['sole'],'support':p['sole'] is not None,'foot_cut_y':p['foot_cut_y']}
        for t in cfg['tools']:
            name=t['id'];angle=t['attack_angle' if action=='attack' else 'death_angle']*values['swing'][i];basis=rot(angle);pivot=np.array(t['pivot']);position=pivot+body
            transforms[name]=trans(basis,position)
            if t['blade_polygon']:
                hub=position+basis@(np.array(t['hub'])-pivot);rx,ry=t['radius']
                projected=np.diag([rx,ry])@rot(values['blade'][i])@np.diag([1/rx,1/ry])
                transforms[name+'_blade']=trans(basis@projected,hub)
            if 'socket' in t:
                s=t['socket'];polygons[name]=quad(np.array(s['start'])+body,basis@(np.array(s['end'])-pivot)+position,s['width'])
            if 'spindle' in t:
                s=t['spindle'];polygons[name+'_spindle']=quad(basis@(np.array(s['start'])-pivot)+position,basis@(np.array(s['end'])-pivot)+position,s['width'])
        expected={'action':action,'direction':d,'frame':i,'root':[64,104],'body_translation':body.tolist(),'supports':supports,'part_transforms':transforms,'socket_polygons':{k:v.tolist() for k,v in polygons.items()},'sensor_power':values['power'][i]}
        pose=clip['poses'][i];cold_pose=next(p for p in runtime['poses'] if p['pose']['action']==action and p['pose']['frame']==i)
        assert close(expected,pose) and close(expected,cold_pose['pose']) and all(abs(v-values['power'][i])<1e-6 for v in cold_pose['actual_material_powers'])
        for name,t in transforms.items():
            basis=np.array([t['basis_x'],t['basis_y']]).T
            assert abs(np.linalg.det(basis)-1)<1e-9
            if not name.endswith('_blade'):assert np.allclose(basis.T@basis,np.eye(2))
            if name.endswith('_foot'):assert close(t,trans(np.eye(2),[0,0]))
        shaded=src.copy();rx,ry,rw,rh=cfg['sensor_rect'];sensor=(X>=rx)&(X<rx+rw)&(Y>=ry)&(Y<ry+rh)
        shaded[sensor,:3]=np.floor(src[sensor,:3].astype(float)*(.3+.7*values['power'][i])+.5).astype(np.uint8)
        base=blank();baseowner=np.full((128,128),'',dtype='U32');sample_data={}
        for name in sorted(pivots,key=lambda k:zorder[k]):
            image,use,sx,sy=sampled(shaded,masks[name],transforms[name],pivots[name]);base[use]=image[use];baseowner[use]=name;sample_data[name]=(sx,sy)
        predicted=blank();linkowner=np.full((128,128),'',dtype='U32');linkdata={}
        for name,s in link_specs.items():
            coverage,sx,sy=uv_sample(polygons[name],s['source_rect']);cx,cy=np.clip(sx,0,127),np.clip(sy,0,127);use=coverage&(src[cy,cx,3]>0)
            predicted[use]=src[cy[use],cx[use]];linkowner[use]=name;linkdata[name]=(coverage,sx,sy)
        use=base[:,:,3]>0;predicted[use]=base[use]
        actual=arr(P/f'output/enemy_cutter/{action}_{d}/f{i:02d}.png');different=np.any(predicted!=actual,axis=2)
        residual=[]
        for y,x in np.argwhere(different):
            name=baseowner[y,x];is_link=not bool(name);name=name or linkowner[y,x]
            uv=linkdata[name][1:] if is_link and name else sample_data[name] if name else None
            residual.append({'xy':[int(x),int(y)],'cpu':predicted[y,x].tolist(),'actual':actual[y,x].tolist(),'cpu_part':name,'cpu_is_link':is_link,'cpu_source_xy':[int(uv[0][y,x]),int(uv[1][y,x])] if uv else None})
        extra=(actual[:,:,3]>0)&(base[:,:,3]==0);extra_records=[]
        for y,x in np.argwhere(extra):
            matches=[]
            for name,s in link_specs.items():
                if not poly(polygons[name].tolist())[y,x]:continue
                u,v,w,h=s['source_rect'];palette=src[v:v+h,u:u+w].reshape(-1,4)
                if np.any(np.all(palette==actual[y,x],axis=1)):matches.append(name)
            # Unmatched CPU-base extras remain in residuals; do not falsely label every edge sample a UV addition.
            extra_records.append({'xy':[int(x),int(y)],'rgba':actual[y,x].tolist(),'registered_socket_source_matches':matches,'cpu_residual':bool(different[y,x])})
        soles=[]
        for p in cfg['parts']:
            if p['sole'] is None:continue
            x,y=p['sole'];q=y-1;name=p['id']+'_foot';top=baseowner[q,x] or ('link:'+linkowner[q,x] if linkowner[q,x] else 'transparent')
            soles.append({'id':p['id'],'sole':p['sole'],'fixed_transform':True,'source_owner':owner[q,x],'source_alpha':int(src[q,x,3]),'actual_alpha':int(actual[q,x,3]),'cpu_top_owner':top,'self_visible_cpu':bool(baseowner[q,x]==name),'actual_matches_original_rgba':bool(np.array_equal(actual[q,x],src[q,x])),'cpu_residual_at_probe':bool(different[q,x])})
        frames.append({'direction':d,'action':action,'frame':i,'source_transforms_and_cold_pose_match':True,'armor_rigid':True,'blade_fixed_projection_det1':True,'registered_fixed_feet':soles,'cpu_residual':residual,'cpu_alpha_residual':int(np.sum(predicted[:,:,3]!=actual[:,:,3])),'cpu_base_uncovered_actual_pixels':extra_records})
gpu,runtime=js(P/'qa/gpu_roundtrip.json'),js(P/'qa/runtime.json')
assert gpu['status']==runtime['status']=='PASS' and gpu['catalog_sha256']==runtime['catalog_sha256']==sha(P/'output/catalog.json')
assert len(gpu['records'])==210 and len(runtime['players'])==32 and len(runtime['switches'])==16
assert all(p['passed'] and p['finishes']>=1 and p['loops']==0 and not p['playing'] and p['seen_frames']==list(range(6 if p['key'].startswith('attack') else 8)) for p in runtime['players'])
result={'status':'SOURCE_POSE_COLD_PASS_CPU_RESIDUAL_RETAINED_VISUAL_SEPARATE','catalog_sha256':sha(P/'output/catalog.json'),'rig_sha256':sha(P/'rig.json'),'tres_sha256':sha(P/cat['tres'].removeprefix('res://')),'sources7':sources,'provenance_c22_equal':provenance,'preserved14_png_2atlas':preserved,'exports112':exports,'bindings7':bindings,'sockets':sockets,'frames98':frames,'cpu_rgba_residual_total':sum(len(f['cpu_residual']) for f in frames),'cpu_alpha_residual_total':sum(f['cpu_alpha_residual'] for f in frames),'registered_new_socket_alpha_events':sum(bool(p['registered_socket_source_matches']) for f in frames for p in f['cpu_base_uncovered_actual_pixels']),'unmatched_base_extra_pixels':sum(not p['registered_socket_source_matches'] for f in frames for p in f['cpu_base_uncovered_actual_pixels']),'author_bound_only':{'gpu_records':210,'players':32,'switches':16,'gpu_sha256':sha(P/'qa/gpu_roundtrip.json'),'runtime_sha256':sha(P/'qa/runtime.json'),'independent_gpu_replay':False},'boundary':'Source masks have unique ownership; UV links instance source pixels and can add output alpha. Fixed-foot transforms and sole metadata do not imply unobstructed visible foot pixels. Projected blade spin uses fixed elliptical metric, not rigid screen-space orthogonal rotation. Sensor brightness changes are declared death effect, not identity generation.'}
result['status']='RETURN_P2_VISIBLE_BLADE_PATCH_SPIN_RESOURCE_POSE_COLD_PASS'
result['findings']=[{'priority':'P2','id':'NW_VISIBLE_BLADE_PATCH_SPIN','summary':'The source-visible saw_blade mask spins its preexisting occlusion/cut boundary into the exposed silhouette. NW attack F03 reads as an open hook; recipe agreement does not prove shape validity. E flat cut edge is a secondary same-mechanism observation.','evidence':'technical-defect-trace.json; visual-review.md when merged'},
 {'priority':'P3','id':'SE_NOMINAL_SOLE_AND_SOCKET_WORDING','summary':'SE front sole probes point to saw_blade/claw source owners; actual foot masks exist elsewhere. SE front_left 2x2 socket has one opaque brown pixel and three transparent pixels, not four dark blue-gray pixels. Do not label these nominal probes as measured visible support.'}]
(OUT/'technical-integrity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'masks':sum(len(b['owned_opaque']) for b in bindings),'links':len(sockets),'poses':len(frames),'cpu_rgba_residual':result['cpu_rgba_residual_total'],'cpu_alpha_residual':result['cpu_alpha_residual_total'],'new_socket_alpha_events':result['registered_new_socket_alpha_events'],'unmatched_base_extra':result['unmatched_base_extra_pixels']}))
