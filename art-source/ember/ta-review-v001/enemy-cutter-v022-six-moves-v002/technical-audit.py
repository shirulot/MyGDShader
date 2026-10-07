"""C22 独立源归属、整数刚体复现、四足相位及安装座 UV/新增像素审查。"""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import json,hashlib,math
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];P=OUT/'technical-package'
js=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
arr=lambda p:np.array(Image.open(p).convert('RGBA'))
rig,cat,receipt=js(P/'rig.json'),js(P/'output/catalog.json'),js(P/'SOURCE_RECEIPT.json')
assert cat['canvas']==[128,128] and cat['root']==[64,104]
assert sha(P/'rig.json')==cat['rig_sha256'] and sha(P/cat['tres'].removeprefix('res://'))==cat['tres_sha256']
BOUND=ROOT/'art-source/ember/ta-review-v001/enemy-eight-directions-v013-preflight/bound'
sources=[]
for d in rig['directions']:
    f=P/'source'/f'{d}.png';assert sha(f)==receipt['source_png_hashes'][d+'.png']
    assert f.read_bytes()==(BOUND/f'output/enemy_cutter/neutral_{d}.png').read_bytes()==(P/f'output/enemy_cutter/neutral_{d}.png').read_bytes()
    sources.append({'direction':d,'approved_static_bound_byte_exact':True,'sha256':sha(f)})
assert (P/'provenance/registration.json').read_bytes()==(BOUND/'registration.json').read_bytes()
preserved=[]
for d,name,key in [('down','enemy_sequences_v012_2026-10-06.zip','down_zip_sha256'),('down_right','enemy_eight_directions_v013_pilot_hc_v001_2026-10-06.zip','down_right_zip_sha256')]:
    zp=ROOT/'art-source/ember/deliveries'/name;assert sha(zp)==receipt[key]
    with ZipFile(zp) as z:
        c=next(c for c in cat['clips'] if c['direction']==d);f=c['atlas'].removeprefix('res://')
        for n in [f]+[f[:-4]+f'/f{i:02d}.png' for i in range(8)]:
            candidates=[v for v in z.namelist() if v==n or v.endswith('/'+n.removeprefix('output/'))];assert len(candidates)==1
            assert (P/n).read_bytes()==z.read(candidates[0]);preserved.append(n)
exports=[]
for c in cat['clips']:
    path=c['atlas'].removeprefix('res://');a=arr(P/path)
    assert sha(P/path)==c['atlas_sha256'] and a.shape==(128,1024,4) and c['frame_count']==8 and c['fps']==8 and c['loop']
    for f in range(8):
        p=P/(path[:-4]+f'/f{f:02d}.png');im=arr(p)
        assert im.shape==(128,128,4) and sha(p)==c['frame_hashes'][f] and np.array_equal(im,a[:,128*f:128*(f+1)]) and set(np.unique(im[:,:,3])).issubset({0,255})
        exports.append({'file':p.relative_to(P).as_posix(),'sha_and_atlas_rgba_exact':True})
assert len(exports)==64
yy,xx=np.indices((128,128));X,Y=xx+.5,yy+.5
def poly(shape):
    mask=np.zeros((128,128),bool);edge=mask.copy()
    for (x1,y1),(x2,y2) in zip(shape,shape[1:]+shape[:1]):
        if y1!=y2:mask^=((y1>Y)!=(y2>Y))&(X<(x2-x1)*(Y-y1)/(y2-y1)+x1)
        cross=(X-x1)*(y2-y1)-(Y-y1)*(x2-x1)
        edge|=(np.abs(cross)<1e-7)&(X>=min(x1,x2))&(X<=max(x1,x2))&(Y>=min(y1,y2))&(Y<=max(y1,y2))
    return mask|edge
def rround(v):return math.copysign(math.floor(abs(v)+.5),v)
def close(a,b,tol=2e-5):
    if isinstance(a,dict):return set(a)==set(b) and all(close(a[k],b[k],tol) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(close(x,y,tol) for x,y in zip(a,b))
    if isinstance(a,(float,int)) and not isinstance(a,bool):return abs(a-b)<tol
    return a==b
def socket_geometry(p,body,travel):
    start=np.array(p['socket']['start'])+body;end=np.array(p['socket']['end'])+travel;delta=end-start
    normal=np.array([-delta[1],delta[0]])/np.linalg.norm(delta)*p['socket']['width']/2
    return np.array([start-normal,start+normal,end+normal,end-normal])
def uv_sample(quad,rect):
    basis=np.array([quad[1]-quad[0],quad[3]-quad[0]]).T;inv=np.linalg.inv(basis);dx=X-quad[0,0];dy=Y-quad[0,1]
    u=inv[0,0]*dx+inv[0,1]*dy;v=inv[1,0]*dx+inv[1,1]*dy
    sx=np.floor(rect[0]+.001+u*(rect[2]-.002)).astype(int);sy=np.floor(rect[1]+.001+v*(rect[3]-.002)).astype(int)
    coverage=(u>=-1e-7)&(u<=1+1e-7)&(v>=-1e-7)&(v<=1+1e-7)
    return coverage,sx,sy
assert rig['depth']==[2,1,0,-1,-2,-1,0,1] and rig['lift']==[0,0,0,0,0,1,2,1] and rig['body_y']==[0,0,-1,0,0,0,-1,0]
expected_phases={'front_left':0,'rear_right':0,'front_right':4,'rear_left':4}
cold=js(OUT/'technical-minimal-cold-load.json');assert cold['status']=='PASS' and cold['frames']==64
models={};ownership=[];frames=[];sockets=[];source_only_residual=[];cold_checks=[]
for d,c in rig['configs'].items():
    src=arr(P/c['source'].removeprefix('res://'));assert sha(P/c['source'].removeprefix('res://'))==c['source_sha256']
    protected=np.zeros((128,128),bool)
    for q in c['protected_body_polygons']:protected|=poly(q)
    parts=[{'id':'body','pivot':[0,0],'z':5}]+c['parts'];masks={'body':np.ones((128,128),bool)}
    for p in c['parts']:masks['body']&=~poly(p['polygon'])
    masks['body']|=protected
    for p in c['parts']:
        mask=poly(p['polygon'])
        for q in p['overlap_polygons']:mask|=poly(q)
        masks[p['id']]=mask&~protected
        assert p['phase_offset']==expected_phases[p['id']]
    opaque=src[:,:,3]>0;multiplicity=sum(m.astype(int) for m in masks.values())
    assert not np.any(opaque&(multiplicity!=1))
    neutral=np.full_like(src,255);neutral[:,:,3]=0
    for _,p in sorted(enumerate(parts),key=lambda a:(a[1]['z'],a[0])):
        use=masks[p['id']]&opaque;neutral[use]=src[use]
    assert np.array_equal(neutral,src) and np.array_equal(arr(P/f'qa/bind_{d}.png'),src)
    counts={k:int(np.sum(v&opaque)) for k,v in masks.items()}
    sole_checks=[]
    for p in c['parts']:
        assert counts[p['id']]==p['opaque_source_pixels']
        if p['sole'] is not None:
            sx,sy=p['sole'];ys=np.where(masks[p['id']]&opaque)[0]
            assert sy==int(ys.max())+1 and masks[p['id']][sy-1,sx] and src[sy-1,sx,3]==255
            sole_checks.append({'part':p['id'],'source_sole':p['sole'],'lowest_owned_opaque_y':int(ys.max()),'original_alpha_above_sole':255})
        rect=p['socket']['source_rect'];assert rect[2:]==[2,2]
        sx,sy,w,h=rect;colors=src[sy:sy+h,sx:sx+w].reshape(-1,4)
        assert np.all(colors[:,3]==255) and np.all(colors[:,2]>=colors[:,1]) and np.all(colors[:,1]>=colors[:,0])
        quad=socket_geometry(p,np.zeros(2),np.zeros(2));coverage,_,_=uv_sample(quad,rect)
        exposed=coverage&~opaque;assert not np.any(exposed)
        sockets.append({'direction':d,'part':p['id'],'source_rect':rect,'source_rgba4':colors.tolist(),'bind_polygon':quad.tolist(),'bind_new_alpha_pixels':0,'layer_z':-10})
    ownership.append({'direction':d,'parts':counts,'missing_original_opaque':0,'duplicate_original_opaque':0,'protected_body_opaque':int(np.sum(protected&opaque)),'hidden_legs':c['hidden_legs'],'sole_registration':sole_checks,'bind_rgba_diff':0})
    for k,m in masks.items():Image.fromarray((m*255).astype(np.uint8)).save(OUT/f'technical-mask-{d}-{k}.png')
    cr=next(r for r in cold['rig_cpu_checks'] if r['direction']==d);clip=next(k for k in cat['clips'] if k['direction']==d)
    assert close(cr['poses'],clip['poses'])
    for m in cr['masks']:assert np.array_equal(np.array(Image.open(OUT/f'technical-runtime-mask-{d}-{m["id"]}.png').convert('L'))>0,masks[m['id']])
    for s in cr['sockets']:
        p=next(p for p in c['parts'] if p['id']==s['id']);x,y,w,h=p['socket']['source_rect']
        expected=[[x+.001,y+.001],[x+w-.001,y+.001],[x+w-.001,y+h-.001],[x+.001,y+h-.001]]
        assert s['z']==-10 and s['filter']==1 and close(s['uv'],expected) and close(s['bind_polygon'],socket_geometry(p,np.zeros(2),np.zeros(2)).tolist())
    cold_checks.append({'direction':d,'mask_rgba_diff':0,'mask_count':len(cr['masks']),'poses':8,'poses_match_catalog':True,'socket_uv_z_nearest_bind_exact_tolerance':2e-5})
    for i in range(8):
        pose=clip['poses'][i];body=np.array([0,rig['body_y'][i]]);tr={'body':body};supports={};quads={}
        for p in c['parts']:
            phase=(i+p['phase_offset'])%8;depth,lift=rig['depth'][phase],rig['lift'][phase]
            travel=np.array([rround(depth*.7*c['heading'][0]),rround(depth*.35*c['heading'][1]-lift)]).astype(int);tr[p['id']]=travel
            sole=(np.array(p['sole'])+travel).tolist() if p['sole'] is not None else None
            ground=(np.array(p['sole'])+[rround(depth*.7*c['heading'][0]),rround(depth*.35*c['heading'][1])]).tolist() if p['sole'] is not None else None
            supports[p['id']]={'sole':sole,'ground':ground,'support':lift==0,'depth':depth,'lift':lift,'hidden_mount_travel':travel.tolist(),'phase':phase}
            quads[p['id']]=socket_geometry(p,body,travel)
        expected_tr={p['id']:{'position':(np.array(p['pivot'])+tr[p['id']]).tolist(),'basis_x':[1,0],'basis_y':[0,1]} for p in parts}
        assert close(expected_tr,pose['part_transforms']) and close(supports,pose['supports']) and close({k:v.tolist() for k,v in quads.items()},pose['socket_polygons']) and pose['hidden_legs']==c['hidden_legs']
        actual=arr(P/f'output/enemy_cutter/move_{d}/f{i:02d}.png')
        base=np.full_like(src,255);base[:,:,3]=0;owner=np.full((128,128),-1,int)
        for index,p in sorted(enumerate(parts),key=lambda a:(a[1]['z'],a[0])):
            ys,xs=np.where(masks[p['id']]&opaque);tx,ty=xs+tr[p['id']][0],ys+tr[p['id']][1]
            assert np.all((tx>=0)&(tx<128)&(ty>=0)&(ty<128));base[ty,tx]=src[ys,xs];owner[ty,tx]=index
        rigid_diff=np.any(base!=actual,axis=2)&(base[:,:,3]>0);assert not np.any(rigid_diff)
        py,px=np.where(masks['body']&opaque);assert np.array_equal(actual[py+body[1],px],src[py,px])
        extra=(base[:,:,3]==0)&(actual[:,:,3]>0);new=[];uv_diffs=[]
        socket_composite=np.full_like(src,255);socket_composite[:,:,3]=0;socket_owner=np.full((128,128),-1,int);socket_uv={}
        for n,p in enumerate(c['parts']):
            rect=p['socket']['source_rect'];coverage,sx,sy=uv_sample(quads[p['id']],rect);valid=coverage
            cx,cy=np.clip(sx,0,127),np.clip(sy,0,127);socket_composite[valid]=src[cy[valid],cx[valid]];socket_owner[valid]=n;socket_uv[p['id']]=(sx,sy)
        for y,x in np.argwhere(extra):
            matches=[]
            for p in c['parts']:
                if not poly(quads[p['id']].tolist())[y,x]:continue
                sx,sy,w,h=p['socket']['source_rect'];palette=src[sy:sy+h,sx:sx+w].reshape(-1,4)
                if np.any(np.all(palette==actual[y,x],axis=1)):matches.append(p['id'])
            assert matches,(d,i,int(x),int(y),actual[y,x].tolist())
            cpu_owner=int(socket_owner[y,x]);cpu_part=c['parts'][cpu_owner]['id'] if cpu_owner>=0 else None
            uv=socket_uv[cpu_part] if cpu_part else None
            record={'xy':[int(x),int(y)],'rgba':actual[y,x].tolist(),'registered_polygon_and_source_color_matches':matches,'cpu_uv_source_xy':[int(uv[0][y,x]),int(uv[1][y,x])] if uv else None,'cpu_socket_part':cpu_part,'cpu_socket_rgba':socket_composite[y,x].tolist()}
            new.append(record)
            if not np.array_equal(socket_composite[y,x],actual[y,x]):uv_diffs.append(record)
        predicted=socket_composite.copy();use=base[:,:,3]>0;predicted[use]=base[use]
        cpu_diff=np.any(predicted!=actual,axis=2);ys,xs=np.where(cpu_diff)
        source_only_residual.append({'direction':d,'frame':i,'rgba_residual':len(xs),'alpha_residual':int(np.sum(predicted[:,:,3]!=actual[:,:,3])),'pixels':[{'xy':[int(x),int(y)],'cpu':predicted[y,x].tolist(),'actual':actual[y,x].tolist()} for y,x in zip(ys,xs)]})
        sole_output=[]
        for k,s in supports.items():
            if s['sole'] is None:continue
            x,y=s['sole'];assert actual[y-1,x,3]==255
            if s['support']:assert s['sole']==s['ground']
            sole_output.append({'part':k,'sole':s['sole'],'ground':s['ground'],'support':s['support'],'lift':s['lift'],'actual_alpha_above_sole':255,'actual_top_owner':parts[int(owner[y-1,x])]['id'] if owner[y-1,x]>=0 else 'socket'})
        frames.append({'direction':d,'frame':i,'rigid_source_rgba_diff':0,'body_rgba_diff':0,'pose_supports_and_socket_geometry_match':True,'visible_new_socket_alpha':len(new),'new_socket_pixels':new,'cpu_new_socket_sampling_differences':uv_diffs,'sole_checks':sole_output,'hidden_legs_not_claimed_as_measured':c['hidden_legs']})
gpu,runtime=js(P/'qa/gpu_roundtrip.json'),js(P/'qa/runtime.json')
assert gpu['status']==runtime['status']=='PASS' and gpu['catalog_sha256']==runtime['catalog_sha256']==sha(P/'output/catalog.json')
assert len(gpu['records'])==112 and len(runtime['seen_frames'])==len(runtime['loops'])==16 and len(runtime['switches'])==8
assert all(v==list(range(8)) for v in runtime['seen_frames'].values()) and min(runtime['loops'].values())>=1
result={'status':'TECHNICAL_BIND_SOURCE_POSE_PASS_PENDING_VISUAL','catalog_sha256':sha(P/'output/catalog.json'),'rig_sha256':sha(P/'rig.json'),'tres_sha256':sha(P/cat['tres'].removeprefix('res://')),'approved_static8':sources,'preserved16_png_2atlas':preserved,'exports64':exports,'ownership6':ownership,'socket18':sockets,'frames48':frames,'cold_readback':cold_checks,'cpu_model_residuals':source_only_residual,'cpu_rgba_residual_total':sum(x['rgba_residual'] for x in source_only_residual),'cpu_alpha_residual_total':sum(x['alpha_residual'] for x in source_only_residual),'new_socket_alpha_events_total':sum(f['visible_new_socket_alpha'] for f in frames),'author_bound_only':{'gpu_records':112,'players':16,'switches':8,'gpu_sha256':sha(P/'qa/gpu_roundtrip.json'),'runtime_sha256':sha(P/'qa/runtime.json'),'independent_gpu_replay':False},'documentation_issue':'SOURCE_RECEIPT.static_review wrongly uses ta-review-v002; verified accepted evidence is ta-review-v001/enemy-eight-directions-v013-preflight/review-static-preflight-v001.md','wording_boundary':'No new imagegen or new RGB palette does not mean no new output pixels: animated socket polygons create registered dark output-alpha pixels behind the original rigid parts.'}
(OUT/'technical-integrity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'sockets':len(sockets),'poses':len(frames),'new_socket_alpha_events':result['new_socket_alpha_events_total'],'cpu_rgba_residual':result['cpu_rgba_residual_total'],'cpu_alpha_residual':result['cpu_alpha_residual_total'],'max_socket_new_pixels_by_direction':{d:max(f['visible_new_socket_alpha'] for f in frames if f['direction']==d) for d in rig['configs']}}))
