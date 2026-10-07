"""C23 只读来源、body/脚固定、实际像素、socket及冷读回审查。"""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import numpy as np
import json,hashlib,ast
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];P=OUT/'technical-package';PREV=OUT.with_name('enemy-cutter-v022-six-moves-v002')/'technical-package'
js=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
arr=lambda p:np.array(Image.open(p).convert('RGBA'))
yy,xx=np.indices((128,128));X,Y=xx+.5,yy+.5
# 仅复用自有几何/相等函数定义，不执行 C22 审查主流程。
helper=PREV.parent/'technical-audit.py';tree=ast.parse(helper.read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['poly','close','socket_geometry','uv_sample']],type_ignores=[]),str(helper),'exec'))
rig,cat,receipt=js(P/'rig.json'),js(P/'output/catalog.json'),js(P/'SOURCE_RECEIPT.json')
assert cat['canvas']==[128,128] and cat['root']==[64,104] and sha(P/'rig.json')==cat['rig_sha256'] and sha(P/cat['tres'].removeprefix('res://'))==cat['tres_sha256']
assert rig['actions']=={'idle':{'fps':4,'loop':True,'body':[[0,0],[0,-1],[0,0],[0,1]]},'hit':{'fps':12,'loop':False,'body':[[0,0],[-1,1],[1,0],[0,0]]}}
assert (P/'move_rig.json').read_bytes()==(PREV/'rig.json').read_bytes()
assert (P/'move_rig.gd').read_text(encoding='utf-8').replace('res://move_rig.json','res://rig.json')==(PREV/'rig.gd').read_text(encoding='utf-8')
HC=ROOT/'art-source/ember/deliveries/enemy_eight_directions_v013_pilot_hc_v001_2026-10-06.zip'
assert sha(HC)==receipt['se_first_gate_zip_sha256']=='5db52757c74fc537b3f45d87abdbab8c58e5d8fcd3cf6366153f7b32ef98b9ef'
hc=ZipFile(HC);pilot=js(P/'pilot_rigs.json')['units'][0]
assert pilot==next(x for x in json.loads(hc.read('pilot_rigs.json'))['units'] if x['unit']=='enemy_cutter')
original_pilot=hc.read('pilot_rig.gd').decode('utf-8')
expected_pilot=original_pilot.replace('texture=load(str(spec.source))','texture=ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(str(spec.source))))').replace('atlas.atlas=load(str(spec.leg_source))','atlas.atlas=ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(str(spec.leg_source))))')
assert expected_pilot==(P/'pilot_rig.gd').read_text(encoding='utf-8')
for n in [pilot['source'].removeprefix('res://'),pilot['leg_source'].removeprefix('res://')]:assert (P/n).read_bytes()==hc.read(n)
sources=[]
for d in rig['directions']:
    src=P/f'source/{d}.png';assert sha(src)==receipt['source_png_hashes'][d+'.png']
    if d=='down_right':assert src.read_bytes()==hc.read('output/enemy_cutter/rig_neutral_down_right.png') and sha(src)=='79e56cd5438f5b78d4dad555e9a364c359635b8cb8b58c6b1790cc166679b462'
    else:assert src.read_bytes()==(PREV/f'source/{d}.png').read_bytes()
    assert src.read_bytes()==(P/f'output/enemy_cutter/neutral_{d}.png').read_bytes()
    sources.append({'direction':d,'sha256':sha(src),'approved_basis':'HC actual rig_neutral_down_right' if d=='down_right' else 'C22 fixed static source'})
preserved=[];downzip=ROOT/'art-source/ember/deliveries/enemy_sequences_v012_2026-10-06.zip';assert sha(downzip)==receipt['down_zip_sha256']
with ZipFile(downzip) as z:
    for action in ['idle_down','hit_down']:
        prefix='output/enemy_cutter/'+action
        for n in [prefix+'.png']+[prefix+f'/f{i:02d}.png' for i in range(4)]:
            candidates=[v for v in z.namelist() if v==n or v.endswith('/'+n.removeprefix('output/'))];assert len(candidates)==1 and (P/n).read_bytes()==z.read(candidates[0]);preserved.append(n)
exports=[]
for c in cat['clips']:
    kind=c['action'].split('_')[0];path=c['atlas'].removeprefix('res://');atlas=arr(P/path)
    assert sha(P/path)==c['atlas_sha256'] and atlas.shape==(128,512,4) and c['frame_count']==4 and c['fps']==rig['actions'][kind]['fps'] and c['loop']==rig['actions'][kind]['loop']
    for i in range(4):
        n=path[:-4]+f'/f{i:02d}.png';im=arr(P/n)
        assert im.shape==(128,128,4) and sha(P/n)==c['frame_hashes'][i] and np.array_equal(im,atlas[:,128*i:128*(i+1)]) and set(np.unique(im[:,:,3])).issubset({0,255})
        exports.append({'file':n,'sha_and_atlas_rgba_exact':True})
assert len(exports)==64
cold=js(OUT/'technical-minimal-cold-load.json');assert cold['status']=='PASS' and cold['frames']==64
models={};bindings=[];frames=[];runtime_checks=[]
def blank():
    a=np.full((128,128,4),255,np.uint8);a[:,:,3]=0;return a
for d,c in rig['configs'].items():
    if d!='down_right':
        assert c==js(PREV/'rig.json')['configs'][d]
        src=arr(P/c['source'].removeprefix('res://'));parts=[{'id':'body','pivot':[0,0],'z':5}]+c['parts'];protected=np.zeros((128,128),bool)
        for s in c['protected_body_polygons']:protected|=poly(s)
        masks={'body':np.ones((128,128),bool)}
        for p in c['parts']:masks['body']&=~poly(p['polygon'])
        masks['body']|=protected
        for p in c['parts']:
            mask=poly(p['polygon'])
            for s in p['overlap_polygons']:mask|=poly(s)
            masks[p['id']]=mask&~protected
        assert np.all(sum(m.astype(int) for m in masks.values())[src[:,:,3]>0]==1)
        externals=[]
    else:
        src=arr(P/pilot['source'].removeprefix('res://'));parts=[{'id':'body','pivot':[0,0],'z':5}]+pilot['parts'];masks={'body':np.ones((128,128),bool)}
        for s in pilot['remove_polygons']+[p['polygon'] for p in pilot['parts']]:masks['body']&=~poly(s)
        for p in pilot['parts']:
            m=poly(p['polygon'])
            for s in p['overlap_polygons']:m|=poly(s)
            for s in p['exclude']:m&=~poly(s)
            masks[p['id']]=m
        externals=[];legraw=arr(P/pilot['leg_source'].removeprefix('res://'))
        for leg in pilot['legs']:
            if leg.get('registered',False):continue
            x,y,w,h=leg['source_rect'];crop=legraw[y:y+h,x:x+w]
            # 原统一0.04登记固定于所有帧；不是动作中缩放或每帧重配尺寸。
            sx=np.floor((X-leg['target_origin'][0])/leg['scale']).astype(int);sy=np.floor((Y-leg['target_origin'][1])/leg['scale']).astype(int)
            valid=(sx>=0)&(sx<w)&(sy>=0)&(sy<h);cx,cy=np.clip(sx,0,w-1),np.clip(sy,0,h-1);valid&=crop[cy,cx,3]>=128
            image=blank();image[valid]=crop[cy[valid],cx[valid]];image[valid,3]=255
            externals.append((leg,image));parts.append({'id':leg['id'],'pivot':leg['target_origin'],'z':leg['z'],'external':True,'scale':leg['scale']})
    cr=next(r for r in cold['rig_cpu_checks'] if r['direction']==d)
    for k,m in masks.items():
        Image.fromarray((m*255).astype(np.uint8)).save(OUT/f'technical-mask-{d}-{k}.png')
        assert np.array_equal(np.array(Image.open(OUT/f'technical-runtime-mask-{d}-{k}.png').convert('L'))>0,m)
    for leg,_ in externals:
        image=arr(OUT/f'technical-runtime-texture-{d}-{leg["id"]}.png');x,y,w,h=leg['source_rect'];assert np.array_equal(image,legraw[y:y+h,x:x+w])
    runtime_checks.append({'direction':d,'mask_count':len(masks),'mask_differences':0,'registered_texture_crops':len(externals),'pose_count':8})
    models[d]=(src,parts,masks,externals)
    multiplicity=sum(m.astype(int) for m in masks.values());bindings.append({'direction':d,'registered_source_opaque':int(np.sum(src[:,:,3]>0)),'multiple_original_part_owners':int(np.sum((src[:,:,3]>0)&(multiplicity>1))),'SE_inherited_registered_overlap':d=='down_right','neutral_basis_sha256':sha(P/f'source/{d}.png')})
    for kind in ['idle','hit']:
        clip=next(k for k in cat['clips'] if k['action']==kind+'_'+d)
        assert close([p for p in cr['poses'] if p['action']==kind],clip['poses'])
        neutral=arr(P/f'source/{d}.png');reset=2 if kind=='idle' else 3
        assert np.array_equal(arr(P/f'output/enemy_cutter/{kind}_{d}/f00.png'),neutral) and np.array_equal(arr(P/f'output/enemy_cutter/{kind}_{d}/f{reset:02d}.png'),neutral)
        first=clip['poses'][0]
        for i in range(4):
            delta=np.array(rig['actions'][kind]['body'][i]);pose=clip['poses'][i];assert pose['body_translation']==delta.tolist()
            expected={p['id']:{'position':(np.array(p['pivot'])+(delta if p['id']=='body' else 0)).tolist(),'basis_x':[p.get('scale',1),0],'basis_y':[0,p.get('scale',1)]} for p in parts}
            assert close(expected,pose['part_transforms']) and pose['supports']==first['supports']
            actual=arr(P/f'output/enemy_cutter/{kind}_{d}/f{i:02d}.png');base=blank();owners=np.full((128,128),-1,int)
            for n,p in sorted(enumerate(parts),key=lambda t:(t[1]['z'],t[0])):
                if p.get('external'):
                    im=next(im for leg,im in externals if leg['id']==p['id']);use=im[:,:,3]>0;base[use]=im[use];owners[use]=n
                else:
                    ys,xs=np.where(masks[p['id']]&(src[:,:,3]>0));dx,dy=delta if p['id']=='body' else [0,0];base[ys+dy,xs+dx]=src[ys,xs];owners[ys+dy,xs+dx]=n
            bdiff=np.any(base!=actual,axis=2)&(base[:,:,3]>0);py,px=np.where(masks['body']&(src[:,:,3]>0))
            bodydiff=int(np.sum(np.any(actual[py+delta[1],px+delta[0]]!=src[py,px],axis=1)));assert bodydiff==0
            sockets=blank();socket_owner=np.full((128,128),-1,int);socket_rows=[]
            if d!='down_right':
                assert not np.any(bdiff)
                for n,p in enumerate(c['parts']):
                    quad=socket_geometry(p,delta,np.zeros(2));assert close(quad.tolist(),pose['socket_polygons'][p['id']])
                    valid,sx,sy=uv_sample(quad,p['socket']['source_rect']);cx,cy=np.clip(sx,0,127),np.clip(sy,0,127)
                    sockets[valid]=src[cy[valid],cx[valid]];socket_owner[valid]=n
                extra=(base[:,:,3]==0)&(actual[:,:,3]>0)
                for y,x in np.argwhere(extra):
                    matches=[]
                    for p in c['parts']:
                        quad=socket_geometry(p,delta,np.zeros(2));rect=p['socket']['source_rect'];sx,sy,w,h=rect
                        if poly(quad.tolist())[y,x] and np.any(np.all(src[sy:sy+h,sx:sx+w].reshape(-1,4)==actual[y,x],axis=1)):matches.append(p['id'])
                    assert matches
                    socket_rows.append({'xy':[int(x),int(y)],'rgba':actual[y,x].tolist(),'sources':matches,'cpu_rgba':sockets[y,x].tolist()})
            predicted=sockets.copy();use=base[:,:,3]>0;predicted[use]=base[use];difference=np.any(predicted!=actual,axis=2);ys,xs=np.where(difference)
            soles=[]
            for k,s in pose['supports'].items():
                if s['sole'] is None:continue
                x,y=map(int,s['sole']);assert s['ground']==s['sole'] and s['support'] and actual[y-1,x,3]==255
                top=parts[int(owners[y-1,x])]['id'] if owners[y-1,x]>=0 else 'unresolved_CPU_or_socket'
                soles.append({'part':k,'sole':s['sole'],'actual_alpha_above_sole':255,'actual_top_owner':top,'visible_owned_foot':top==k})
            frames.append({'direction':d,'action':kind,'frame':i,'body_translation':delta.tolist(),'legs_fixed_to_bind':True,'body_rgba_differences':bodydiff,'base_opaque_cpu_rgba_differences':int(bdiff.sum()),'socket_new_alpha':socket_rows,'sole_checks':soles,'cpu_residual_count':len(xs),'cpu_alpha_residual':int(np.sum(predicted[:,:,3]!=actual[:,:,3])),'cpu_residual':[{'xy':[int(x),int(y)],'cpu':predicted[y,x].tolist(),'actual':actual[y,x].tolist()} for y,x in zip(ys,xs)]})
gpu,runtime=js(P/'qa/gpu_roundtrip.json'),js(P/'qa/runtime.json')
assert gpu['status']==runtime['status']=='PASS' and gpu['catalog_sha256']==runtime['catalog_sha256']==sha(P/'output/catalog.json') and len(gpu['records'])==120
assert len(runtime['players'])==32 and len(runtime['switches'])==16 and all(r['passed'] and r['seen_frames']==[0,1,2,3] for r in runtime['players']) and all(r['passed'] for r in runtime['switches'])
result={'status':'SOURCE_POSE_RESOURCE_TECHNICAL_PASS_VISUAL_GAP_REVIEW_SEPARATE','catalog_sha256':sha(P/'output/catalog.json'),'rig_sha256':sha(P/'rig.json'),'tres_sha256':sha(P/cat['tres'].removeprefix('res://')),'sources8':sources,'SE_actual_approved_neutral_sha256':sha(P/'source/down_right.png'),'six_c22_configs_and_move_source_same':True,'pilot_cutter_spec_and_original_images_same':True,'pilot_code_changes':'Only direct Image.load_from_file texture creation at canonical/leg texture loads; all masks/registration/geometry unchanged.','preserved8_png_2atlas':preserved,'exports64':exports,'bindings7':bindings,'cold_readback7':runtime_checks,'frames56':frames,'cpu_residual_total':sum(f['cpu_residual_count'] for f in frames),'cpu_alpha_residual_total':sum(f['cpu_alpha_residual'] for f in frames),'socket_alpha_events':sum(len(f['socket_new_alpha']) for f in frames),'author_bound_only':{'gpu_records':120,'gpu_sha256':sha(P/'qa/gpu_roundtrip.json'),'runtime_sha256':sha(P/'qa/runtime.json'),'runtime_keys':list(runtime),'gpu_replayed':False},'boundary':'Technical source preservation and fixed legs do not prove body-to-leg seams are visually acceptable. Missing hidden feet and body-occluded sole samples are not direct visible-foot measurements.'}
(OUT/'technical-integrity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'frames':len(frames),'socket_pixels':result['socket_alpha_events'],'cpu_rgba':result['cpu_residual_total'],'cpu_alpha':result['cpu_alpha_residual_total'],'by_direction':{d:sum(f['cpu_residual_count'] for f in frames if f['direction']==d) for d in rig['configs']},'SE_body_or_source_differences':[(f['action'],f['frame'],f['body_rgba_differences'],f['base_opaque_cpu_rgba_differences']) for f in frames if f['direction']=='down_right']}))
