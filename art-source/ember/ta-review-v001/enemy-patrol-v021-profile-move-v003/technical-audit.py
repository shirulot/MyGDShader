"""P21 必要完整性及动作约束；新腿身份审核另有专项，不把技术一致性写成美术通过。"""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import json,hashlib,math
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];P=OUT/'technical-package'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
js=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
arr=lambda p:np.array(Image.open(p).convert('RGBA'))
# 沿用已经独立实现的步态数学，仅加载函数定义，不执行 P20 审查主过程。
helper=OUT.with_name('enemy-patrol-v020-four-moves-v002')/'technical-audit.py'
exec(compile(helper.read_text(encoding='utf-8').split('manifest=load(')[0],str(helper),'exec'))
P=OUT/'technical-package'
rig=js(P/'rig.json');cat=js(P/'output/catalog.json');receipt=js(P/'SOURCE_RECEIPT.json')
assert sha(P/'rig.json')==cat['rig_sha256'] and sha(P/cat['tres'].removeprefix('res://'))==cat['tres_sha256']
assert cat['canvas']==[128,128] and cat['root']==[64,104]
assert rig['phases']==js(OUT.with_name('enemy-patrol-v020-four-moves-v002')/'technical-package/rig.json')['phases']
dirs=['down','down_left','left','up_left','up','up_right','right','down_right']
static=ROOT/'art-source/ember/deliveries/enemy_patrol_seven_directions_v013_s002_2026-10-06.zip'
assert sha(static)==receipt['static_zip_sha256']=='28951089e1403c65f6a8446aed5f049fdba704809175da36a391c6c5fa1e99a1'
sources=[]
with ZipFile(static) as z:
    for d in dirs:
        f='source/'+d+'.png';b=(P/f).read_bytes()
        assert sha(P/f)==receipt['source_png_hashes'][d+'.png'] and b==z.read('neutral_'+d+'.png') and b==(P/f'reference/enemy_patrol/neutral_{d}.png').read_bytes()
        sources.append({'direction':d,'s002_and_reference_byte_exact':True,'sha256':sha(P/f)})
for f,sh in receipt['source_png_hashes'].items():assert sha(P/'source'/f)==sh
calibration=ROOT/'art-source/ember/deliveries/enemy_patrol_profile_calibration_v021_c002_v003_2026-10-07.zip'
assert sha(calibration)==receipt['calibration_zip_sha256']==rig['calibration_zip_sha256']=='87d0ecf437c93451eddcdad59387f6f03191efcdfdfa1cb197b6e41e819f4ab2'
calibration_bindings=[]
with ZipFile(calibration) as z:
    for d in ['left','right']:
        for kind in ['body','near','far']:
            file=P/f'source/c002_{d}_{kind}.png';assert file.read_bytes()==z.read(f'output/{d}_{kind}.png')
        candidate=P/f'source/c002_neutral_{d}.png';assert candidate.read_bytes()==z.read(f'output/neutral_{d}.png')
        neutral=arr(candidate);original=arr(P/f'source/{d}.png');difference=np.any(neutral!=original,axis=2)
        assert int(difference.sum())==(49 if d=='left' else 50)
        assert np.array_equal(neutral,arr(P/f'qa/bind_{d}.png')) and np.array_equal(neutral,arr(P/f'output/enemy_patrol/neutral_{d}.png'))
        assert np.array_equal(neutral[103],original[103])
        calibration_bindings.append({'direction':d,'actual_body_near_far_byte_exact':True,'c002_neutral_byte_exact':True,'bind_vs_c002_rgba':0,'bind_vs_s002_rgba':int(difference.sum()),'historical_new_alpha':int(np.sum((original[:,:,3]==0)&(neutral[:,:,3]>0))),'historical_lost_alpha':int(np.sum((original[:,:,3]>0)&(neutral[:,:,3]==0))),'row103_original_equal':True})
preserved=[]
for d,zipname,sh in [('down','enemy_sequences_v012_2026-10-06.zip',receipt['down_zip_sha256']),('down_right','enemy_eight_directions_v013_pilot_patrol_v001_2026-10-06.zip',receipt['down_right_zip_sha256'])]:
    zp=ROOT/'art-source/ember/deliveries'/zipname;assert sha(zp)==sh
    with ZipFile(zp) as z:
        c=next(c for c in cat['clips'] if c['direction']==d);f=c['atlas'].removeprefix('res://')
        for n in [f]+[f[:-4]+f'/f{i:02d}.png' for i in range(8)]:
            names=[v for v in z.namelist() if v==n or v.endswith('/'+n.removeprefix('output/'))];assert len(names)==1
            assert (P/n).read_bytes()==z.read(names[0]);preserved.append(n)
exports=[]
for c in cat['clips']:
    f=c['atlas'].removeprefix('res://');atlas=arr(P/f)
    assert sha(P/f)==c['atlas_sha256'] and atlas.shape==(128,1024,4) and c['frame_count']==8 and c['fps']==8 and c['loop']
    for i in range(8):
        n=f[:-4]+f'/f{i:02d}.png';a=arr(P/n)
        assert sha(P/n)==c['frame_hashes'][i] and a.shape==(128,128,4) and np.array_equal(a,atlas[:,i*128:(i+1)*128]) and set(np.unique(a[:,:,3])).issubset({0,255})
        exports.append({'file':n,'hash_and_atlas_rgba_exact':True})
assert len(exports)==32
yy,xx=np.indices((128,128));X,Y=xx+.5,yy+.5
def polygon_mask(shape):
    m=np.zeros((128,128),bool)
    for (x1,y1),(x2,y2) in zip(shape,shape[1:]+shape[:1]):
        if y1!=y2:m^=((y1>Y)!=(y2>Y))&(X<(x2-x1)*(Y-y1)/(y2-y1)+x1)
    return m
models={};ownership=[];pose_checks=[];residuals=[];bind_checks=[];connector_sources=[];sole_samples=[]
for d,c in rig['configs'].items():
    textures={'canonical':arr(P/c['body_source'].removeprefix('res://')),'near':arr(P/c['near_source'].removeprefix('res://')),'far':arr(P/c['far_source'].removeprefix('res://'))}
    assert sha(P/c['far_source'].removeprefix('res://'))==c['far_sha256'] and sha(P/c['near_source'].removeprefix('res://'))==c['near_sha256']
    protected=np.zeros((128,128),bool)
    for s in c['protected_body_polygons']:protected|=polygon_mask(s)
    excluded=[p['polygon'] for p in c['parts'] if p['source_kind']=='canonical']+c['occluded_original_polygons']
    parts=[{'id':'body','pivot':[0,0],'polygon':[],'exclude':excluded,'z':10,'source_kind':'canonical'}]+c['parts'];masks={}
    for part in parts:
        m=polygon_mask(part['polygon']) if part['polygon'] else np.ones((128,128),bool)
        for s in part['exclude']:m&=~polygon_mask(s)
        if part['source_kind']=='canonical':m[protected]=part['id']=='body'
        masks[part['id']]=m
        Image.fromarray((m*255).astype(np.uint8)).save(OUT/f'technical-mask-{d}-{part["id"]}.png')
    counts={}
    for kind in ['near','far']:
        multiplicity=sum(masks[p['id']].astype(int) for p in parts if p['source_kind']==kind);opaque=textures[kind][:,:,3]>0
        missing=int(np.sum(opaque&(multiplicity==0)));duplicate=int(np.sum(opaque&(multiplicity>1)))
        assert missing==duplicate==0
        counts[kind]={'opaque':int(opaque.sum()),'missing':missing,'duplicate_within_instance':duplicate}
    ownership.append({'direction':d,'instances':counts,'part_opaque_counts':{p['id']:int(np.sum(masks[p['id']]&(textures[p['source_kind']][:,:,3]>0))) for p in parts},'note':'Near/far are fixed C002 same-source physical instances; unique ownership is measured within each instance only.'})
    assert all(p['source_kind']==('near' if p['id'].startswith('left_') else 'far') for p in c['parts']) if d=='left' else all(p['source_kind']==('near' if p['id'].startswith('right_') else 'far') for p in c['parts'])
    # Neutral is assembled with actual masks and z order; it is not walking frame F0.
    bind=np.full((128,128,4),255,np.uint8);bind[:,:,3]=0
    for _,part in sorted(enumerate(parts),key=lambda q:(q[1]['z'],q[0])):
        source=textures[part['source_kind']];valid=masks[part['id']]&(source[:,:,3]>0);bind[valid]=source[valid]
        if part.get('end') is not None:
            colors=source[valid,:3]
            connector_sources.append({'direction':d,'id':part['id'],'source_kind':part['source_kind'],'pixels':int(valid.sum()),'rgb_min':colors.min(axis=0).tolist(),'rgb_max':colors.max(axis=0).tolist(),'source_pixels':[{'xy':[int(x),int(y)],'rgba':source[y,x].tolist()} for y,x in np.argwhere(valid)]})
    assert np.array_equal(bind,arr(P/c['approved_bind_source'].removeprefix('res://')))
    bind_checks.append({'direction':d,'independent_mask_z_composite_vs_c002_rgba':0})
    models[d]=(textures,parts,masks,protected)
    clip=next(k for k in cat['clips'] if k['direction']==d)
    src=textures['canonical'];py,px=np.where(protected&(src[:,:,3]>0))
    for i in range(8):
        transforms,supports=pose(c,rig['phases'][i]);actual_pose=clip['poses'][i]
        assert equal(transforms,actual_pose['part_transforms']) and equal(supports,actual_pose['supports'])
        assert all(s['sole']==s['ground'] for s in supports.values() if s['support'])
        assert all(t['basis_x']==[1,0] and t['basis_y']==[0,1] for k,t in transforms.items() if k=='body' or k.endswith('cap') or k.endswith('foot'))
        final=arr(P/f'output/enemy_patrol/move_{d}/f{i:02d}.png');bob=rig['phases'][i]['body_y']
        assert np.array_equal(final[py+bob,px],src[py,px])
        endpoints=[];collapsed=[]
        for part in c['parts']:
            if part['end'] is None:continue
            t=transforms[part['id']];basis=np.array([t['basis_x'],t['basis_y']]).T;axis=np.subtract(part['end'],part['pivot']);end=np.array(t['position'])+basis@axis
            side=part['id'].split('_')[0];leg=c['legs'][side]
            target=np.array(supports[side]['knee'])+np.subtract(part['end'],leg['knee']) if part['id'].endswith('thigh') else np.array(supports[side]['ankle'])+np.subtract(part['end'],leg['ankle'])
            endpoints.append(float(np.max(np.abs(end-target))))
            if abs(np.linalg.det(basis))<1e-12:collapsed.append(part['id'])
        predicted=np.full((128,128,4),255,np.uint8);predicted[:,:,3]=0
        top_owner=np.full((128,128),'',dtype='U32')
        for _,part in sorted(enumerate(parts),key=lambda q:(q[1]['z'],q[0])):
            t=transforms[part['id']];basis=np.array([t['basis_x'],t['basis_y']]).T
            if abs(np.linalg.det(basis))<1e-12:continue
            inv=np.linalg.inv(basis);dx=X-t['position'][0];dy=Y-t['position'][1]
            sx=np.floor(inv[0,0]*dx+inv[0,1]*dy+part['pivot'][0]).astype(int);sy=np.floor(inv[1,0]*dx+inv[1,1]*dy+part['pivot'][1]).astype(int)
            cx,cy=np.clip(sx,0,127),np.clip(sy,0,127);texture=textures[part['source_kind']]
            valid=(sx>=0)&(sx<128)&(sy>=0)&(sy<128)&masks[part['id']][cy,cx]&(texture[cy,cx,3]>=128)
            predicted[valid]=texture[cy[valid],cx[valid]];predicted[valid,3]=255;top_owner[valid]=part['id']
        different=np.any(predicted!=final,axis=2);ys,xs=np.where(different)
        residuals.append({'direction':d,'frame':i,'count':len(xs),'alpha_differences':int(np.sum(predicted[:,:,3]!=final[:,:,3])),'pixels':[{'xy':[int(x),int(y)],'cpu':predicted[y,x].tolist(),'final':final[y,x].tolist()} for y,x in zip(ys,xs)]})
        # Resolve the registered sole against the true rigid foot source, then identify occlusion.
        for side,support in supports.items():
            x,y=map(int,support['sole']);q=y-1;part=next(p for p in c['parts'] if p['id']==side+'_foot');t=transforms[part['id']]
            origin=np.array(t['position'])-np.array(part['pivot']);source_xy=[int(x-origin[0]),int(q-origin[1])];sx,sy=source_xy;texture=textures[part['source_kind']]
            nominal_on_foot=bool(masks[part['id']][sy,sx] and texture[sy,sx,3]==255)
            owned_ys,owned_xs=np.where(masks[part['id']]&(texture[:,:,3]>0));lowest=int(owned_ys.max())
            # A nominal x coordinate may miss a beveled sole. Measure actual lowest-row source pixels too.
            contact_samples=[]
            for ax in owned_xs[owned_ys==lowest]:
                ox,oy=int(ax+origin[0]),int(lowest+origin[1]);shown=top_owner[oy,ox]==part['id'];rgba_equal=bool(np.array_equal(final[oy,ox],texture[lowest,ax]))
                if shown:assert rgba_equal
                contact_samples.append({'source_xy':[int(ax),lowest],'output_xy':[ox,oy],'self_visible':bool(shown),'actual_rgba_equal':rgba_equal,'top_owner':top_owner[oy,ox]})
            assert lowest+origin[1]+1==support['sole'][1]
            visible=top_owner[q,x]==part['id'];same=bool(np.array_equal(final[q,x],texture[sy,sx]))
            if visible:assert same
            sole_samples.append({'direction':d,'frame':i,'side':side,'instance':part['source_kind'],'support':support['support'],'sole':support['sole'],'ground':support['ground'],'source_foot_xy':source_xy,'nominal_source_probe_on_foot':nominal_on_foot,'actual_alpha':int(final[q,x,3]),'cpu_top_owner':top_owner[q,x],'self_visible':bool(visible),'actual_source_rgba_equal':same,'cpu_residual_at_probe':bool(different[q,x]),'actual_bottom_row_matches_sole_y':True,'actual_bottom_row_samples':contact_samples})
        pose_checks.append({'direction':d,'frame':i,'pose_and_support_exact':True,'body_caps_boots_rigid':True,'protected_tool_pixels':len(px),'protected_tool_rgba_diff':0,'connector_endpoint_error':max(endpoints),'collapsed_connectors':collapsed})
cold=js(OUT/'technical-minimal-cold-load.json');assert cold['status']=='PASS' and cold['frames']==32
readback=[]
for row in cold['rig_cpu_checks']:
    d=row['direction'];textures,parts,masks,protected=models[d];clip=next(k for k in cat['clips'] if k['direction']==d)
    assert len(row['masks'])==9 and len(row['poses'])==8
    for m in row['masks']:
        actual=np.array(Image.open(OUT/f'technical-runtime-mask-{d}-{m["id"]}.png').convert('L'))>0;assert np.array_equal(actual,masks[m['id']])
    assert equal(row['poses'],clip['poses'])
    expected_bind={p['id']:{'position':p['pivot'],'basis_x':[1,0],'basis_y':[0,1]} for p in parts}
    assert equal(row['bind_transforms'],expected_bind)
    readback.append({'direction':d,'mask_count':9,'mask_different_pixels':0,'pose_count':8,'pose_matches_catalog_tolerance':2e-5})
gpu,runtime=js(P/'qa/gpu_roundtrip.json'),js(P/'qa/runtime.json')
assert gpu['status']==runtime['status']=='PASS' and gpu['catalog_sha256']==runtime['catalog_sha256']==sha(P/'output/catalog.json')
assert len(gpu['records'])==48 and len(runtime['seen_frames'])==len(runtime['loops'])==8 and len(runtime['switches'])==8
assert all(v==list(range(8)) for v in runtime['seen_frames'].values()) and min(runtime['loops'].values())>=1
result={'status':'TECHNICAL_BASELINE_PASS_C002_EXTENSION_PENDING','catalog_sha256':sha(P/'output/catalog.json'),'rig_sha256':sha(P/'rig.json'),'tres_sha256':sha(P/cat['tres'].removeprefix('res://')),'canonical8':sources,'preserved16_png_2_atlas':preserved,'exports32':exports,'phase_matches_prior_p20':True,'per_instance_ownership':ownership,'poses16':pose_checks,'runtime_readback':readback,'cpu_residuals':residuals,'cpu_residual_total':sum(r['count'] for r in residuals),'cpu_alpha_total':sum(r['alpha_differences'] for r in residuals),'author_evidence_bound_only':{'gpu_sha256':sha(P/'qa/gpu_roundtrip.json'),'runtime_sha256':sha(P/'qa/runtime.json'),'gpu_records':48,'players':8,'switches':8,'gpu_or_matrix_replayed':False},'identity_boundary':'Uses approved C002 body/near/far. Bind against C002 must be RGBA0; historical S00249/50 changes remain. Static approval does not prove motion.'}
result.update({'status':'PASS_TECHNICAL_C002_BIND_MOVE_PHASE_SOURCE_AND_COLD','calibration_bindings':calibration_bindings,'independent_bind_checks':bind_checks,'short_connector_source_pixels':connector_sources,'actual_sole_samples':sole_samples,'sole_samples_self_visible':sum(s['self_visible'] for s in sole_samples),'sole_samples_occluded':sum(not s['self_visible'] for s in sole_samples),'near_anatomy':{'W':'left','E':'right'},'identity_boundary':'Six body/near/far images and two neutral references are byte-exact C002 v003; actual bind RGBA0 versus C002. Historical S002 W49/E50 changes remain. Only16 new W/E move frames are in this review.'})
result['status']='PASS_TECHNICAL_V003_CORE'
result['findings']=[]
(OUT/'technical-integrity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'exports':len(exports),'poses':len(pose_checks),'cpu_residual_total':result['cpu_residual_total'],'cpu_alpha_total':result['cpu_alpha_total'],'per_frame':[(r['direction'],r['frame'],r['count']) for r in residuals],'collapsed':[(r['direction'],r['frame'],r['collapsed_connectors']) for r in pose_checks if r['collapsed_connectors']]}))
