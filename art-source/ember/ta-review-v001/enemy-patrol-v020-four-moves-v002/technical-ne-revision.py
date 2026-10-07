"""P20 v002 限定返修复审：源唯一归属、真实最终像素路径、改动范围与冷读回。"""
from pathlib import Path
from PIL import Image
import numpy as np
import json,hashlib
OUT=Path(__file__).resolve().parent;P=OUT/'technical-package';OLD=OUT.with_name('enemy-patrol-v020-four-moves-v001');OP=OLD/'technical-package'
js=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
arr=lambda p:np.array(Image.open(p).convert('RGBA'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rig,prev=js(P/'rig.json'),js(OP/'rig.json');cat,oldcat=js(P/'output/catalog.json'),js(OP/'output/catalog.json')
assert all(rig[k]==prev[k] for k in rig if k!='configs')
assert all(rig['configs'][d]==prev['configs'][d] for d in ['down_left','up_left','up'])
newc,oldc=rig['configs']['up_right'],prev['configs']['up_right']
assert all(newc[k]==oldc[k] for k in newc if k!='parts')
assert all({k:v for k,v in a.items() if k not in ['polygon','exclude']}=={k:v for k,v in b.items() if k not in ['polygon','exclude']} for a,b in zip(newc['parts'],oldc['parts']))
for f in ['rig.gd','masked_part.gdshader']:
    assert (P/f).read_bytes()==(OP/f).read_bytes()
for f in (P/'source').glob('*.png'):assert f.read_bytes()==(OP/'source'/f.name).read_bytes()
frame_changes=[];sameframes=[];sameatlas=[]
for c in cat['clips']:
    oc=next(v for v in oldcat['clips'] if v['direction']==c['direction']);assert c.get('poses')==oc.get('poses')
    atlas=c['atlas'].removeprefix('res://')
    if c['direction']!='up_right':assert (P/atlas).read_bytes()==(OP/atlas).read_bytes();sameatlas.append(atlas)
    for i in range(8):
        f=atlas[:-4]+f'/f{i:02d}.png';a,b=arr(OP/f),arr(P/f);diff=np.any(a!=b,axis=2)
        if c['direction']=='up_right':frame_changes.append({'frame':i,'rgba_pixel_events':int(diff.sum()),'changed_xy':np.argwhere(diff)[:,[1,0]].tolist()})
        else:assert (P/f).read_bytes()==(OP/f).read_bytes();sameframes.append(f)
assert sum(r['rgba_pixel_events'] for r in frame_changes)==334 and len(sameframes)==40 and len(sameatlas)==5
pixel=js(OUT/'technical-pixel-integrity.json')
assert all(x['multiple_owners_original_opaque']==0 and x['unowned_original_opaque']==0 for x in pixel['binds'])
cfg=rig['configs']['up_right'];src=arr(P/'source/up_right.png')
masks={k:np.array(Image.open(OUT/f'technical-mask-up_right-{k}.png'))>0 for k in ['body']+[x['id'] for x in cfg['parts']]}
oldreview=js(OLD/'technical-rigidity-crosscheck.json')
old20=next(r for r in oldreview['source_ownership'] if r['direction']=='up_right')['shared_opaque']
ownership=[]
for r in old20:
    x,y=r['source'];owners=[k for k,v in masks.items() if v[y,x]];assert len(owners)==1
    ownership.append({'source_xy':[x,y],'rgba':src[y,x].tolist(),'previous_owners':r['owners'],'current_owner':owners[0]})
dark=np.argwhere(masks['left_thigh']&(src[:,:,3]>0))[:,[1,0]].tolist()
assert sorted(dark)==sorted([[x,y] for y in range(80,85) for x in [57,58]])
pale=oldreview['NE_left_thigh_pale_source_pixels'];assert len(pale)==15
assert all(masks['body'][y,x] and sum(v[y,x] for v in masks.values())==1 for x,y,_ in pale)
poses=next(c['poses'] for c in cat['clips'] if c['direction']=='up_right')
parts=[{'id':'body','pivot':[0,0],'z':5}]+cfg['parts'];order=sorted(enumerate(parts),key=lambda v:(v[1]['z'],v[0]))
yy,xx=np.indices((128,128));routes=[]
# 渲染层次逆投影得到顶层源坐标，再核实际交付 PNG；不以归属计数替代像素可见性。
for frame,pose in enumerate(poses):
    owner=np.full((128,128),-1,int);sxout=np.full((128,128),-1,int);syout=sxout.copy()
    for index,p in order:
        t=pose['part_transforms'][p['id']];basis=np.array([t['basis_x'],t['basis_y']]).T
        if abs(np.linalg.det(basis))<1e-12:continue
        inverse=np.linalg.inv(basis);dx=xx+.5-t['position'][0];dy=yy+.5-t['position'][1]
        sx=np.floor(inverse[0,0]*dx+inverse[0,1]*dy+p['pivot'][0]).astype(int)
        sy=np.floor(inverse[1,0]*dx+inverse[1,1]*dy+p['pivot'][1]).astype(int)
        valid=(sx>=0)&(sx<128)&(sy>=0)&(sy<128);cy,cx=np.clip(sy,0,127),np.clip(sx,0,127)
        valid&=masks[p['id']][cy,cx]&(src[cy,cx,3]>0)
        owner[valid]=index;sxout[valid]=sx[valid];syout[valid]=sy[valid]
    final=arr(P/f'output/enemy_patrol/move_up_right/f{frame:02d}.png')
    entries=[]
    for r in ownership:
        x,y=r['source_xy'];hits=np.argwhere((sxout==x)&(syout==y))[:,[1,0]].tolist()
        assert len(hits)<=1
        visible=[]
        for ox,oy in hits:
            assert final[oy,ox].tolist()==r['rgba']
            visible.append({'output_xy':[ox,oy],'part':parts[int(owner[oy,ox])]['id'],'actual_rgba':final[oy,ox].tolist()})
        entries.append({'source_xy':[x,y],'unique_owner':r['current_owner'],'visible':visible})
    # 原 15 点浅甲始终随 body 整体平移，没有同源点纵向复制取样。
    dy=rig['phases'][frame]['body_y']
    assert all(np.array_equal(final[y+dy,x],src[y,x]) for x,y,_ in pale)
    routes.append({'frame':frame,'previous20_source_routes':entries,'rigid_pale15_body_rgba_exact':True})
cold=js(OUT/'technical-minimal-cold-load.json');assert cold['status']=='PASS' and cold['frames']==48
cpu=cold['rig_cpu_checks'][0];assert cpu['direction']=='up_right' and len(cpu['masks'])==9 and len(cpu['poses'])==8
maskdiff=[]
for m in cpu['masks']:
    actual=np.array(Image.open(OUT/f'technical-runtime-mask-up_right-{m["id"]}.png').convert('L'))>0
    delta=int(np.sum(actual!=masks[m['id']]));assert delta==0;maskdiff.append({'id':m['id'],'different_pixels':delta})
def error(a,b):
    if isinstance(a,dict):assert set(a)==set(b);return max([error(a[k],b[k]) for k in a] or [0])
    if isinstance(a,list):assert len(a)==len(b);return max([error(x,y) for x,y in zip(a,b)] or [0])
    if isinstance(a,(float,int)) and not isinstance(a,bool):return abs(a-b)
    assert a==b;return 0
pose_error=max(error(a,b) for a,b in zip(cpu['poses'],poses));assert pose_error<2e-5
gpu,runtime=js(P/'qa/gpu_roundtrip.json'),js(P/'qa/runtime.json')
assert gpu['status']==runtime['status']=='PASS' and gpu['catalog_sha256']==runtime['catalog_sha256']==sha(P/'output/catalog.json')
assert len(gpu['records'])==80 and len(runtime['seen_frames'])==len(runtime['loops'])==12 and len(runtime['switches'])==8
assert all(v==list(range(8)) for v in runtime['seen_frames'].values()) and min(runtime['loops'].values())>=1
result={'status':'TECHNICAL_REPAIR_PASS_PENDING_VISUAL','changed_frame_details':frame_changes,'total_rgba_pixel_events':334,'same40_png':sameframes,'same5_atlas':sameatlas,'same_sources_and_rig_code':True,'only_rig_config_difference':'NE parts polygon/exclude; all pivots/endpoints/z/source/heading/legs/phases and all catalog pose records unchanged','all4_directions_missing_and_duplicate_original_opaque':0,'previous20_unique_ownership':ownership,'new_left_thigh10_original_points':[{'source_xy':[x,y],'rgba':src[y,x].tolist()} for x,y in dark],'old15_pale_points_now_rigid_body':pale,'actual_all8_frame_top_source_routes':routes,'runtime_mask_readback':maskdiff,'runtime_pose_max_error':pose_error,'author_evidence_bound_only':{'gpu_file_sha256':sha(P/'qa/gpu_roundtrip.json'),'runtime_file_sha256':sha(P/'qa/runtime.json'),'gpu_records':80,'players':12,'switches':8,'replayed_gpu_or_player_matrix':False}}
(OUT/'technical-ne-revision.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'NE_changes':[r['rgba_pixel_events'] for r in frame_changes],'unique20_owners':{k:sum(r['current_owner']==k for r in ownership) for k in ['body','left_cap','left_foot']},'cold_masks':9,'cold_pose_max_error':pose_error}))
