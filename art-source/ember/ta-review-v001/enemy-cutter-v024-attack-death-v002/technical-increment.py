"""相对已冻结 v001 的独立增量核验：逐帧、可见像素归属、轴心及固定脚。"""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,collections,numpy as np
OUT=Path(__file__).resolve().parent;P=OUT/'technical-package'
OLD=OUT.with_name('enemy-cutter-v024-attack-death-v001');B=OLD/'technical-package'
js=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
arr=lambda p:np.array(Image.open(p).convert('RGBA'))
rig,oldrig,cat,oldcat=js(P/'rig.json'),js(B/'rig.json'),js(P/'output/catalog.json'),js(B/'output/catalog.json')
author=js(P/'qa/revision_v002.json');cold=js(OUT/'technical-minimal-cold-load.json')
assert author['previous_zip_sha256']=='c3c1d9fb84d909fb113ee0a9d7ddac6afa98b8132f669ae0f5be5fa0963d572c'

def diff(a,b,path=''):
    """保留真实结构差异，不把作者摘要作为唯一允许列表。"""
    if isinstance(a,dict) and isinstance(b,dict):
        return sum((diff(a.get(k),b.get(k),path+'/'+k) for k in sorted(a.keys()|b.keys())),[])
    if a!=b:return [{'path':path,'before':a,'after':b}]
    return []

source_equal=[];neutral_equal=[]
for d in rig['configs']:
    assert (P/f'source/{d}.png').read_bytes()==(B/f'source/{d}.png').read_bytes()
    assert (P/f'qa/bind_{d}.png').read_bytes()==(B/f'qa/bind_{d}.png').read_bytes()
    source_equal.append({'direction':d,'sha256':sha(P/f'source/{d}.png')})
for f in (B/'output/enemy_cutter').glob('neutral_*.png'):
    assert (P/f.relative_to(B)).read_bytes()==f.read_bytes();neutral_equal.append(f.name)
assert rig['actions']==oldrig['actions']

frames=[];changed=[];unchanged=[]
for c in cat['clips']:
    path=c['atlas'].removeprefix('res://');oldc=next(q for q in oldcat['clips'] if q['action']==c['action'])
    same_atlas=(P/path).read_bytes()==(B/path).read_bytes();local=[]
    for i in range(c['frame_count']):
        file=path[:-4]+f'/f{i:02d}.png';a,b=arr(B/file),arr(P/file)
        n=int(np.any(a!=b,axis=2).sum());same=(P/file).read_bytes()==(B/file).read_bytes()
        if n:local.append({'frame':i,'rgba_pixels':n});changed.append({'file':file,'frame':i,'rgba_pixels':n})
        else:assert same;unchanged.append(file)
        frames.append({'action':c['action'],'frame':i,'rgba_pixels_changed':n,'same_bytes':same})
    author_record=next(q for q in author['records'] if q['action']==c['action'])
    assert author_record['changed_frames']==local
    if c['action'] in ['attack_down','death_down','attack_left','death_left','death_up']:
        assert not local and same_atlas
    assert np.array_equal(arr(P/(path[:-4]+'/f00.png')),arr(B/(path[:-4]+'/f00.png')))
assert len(changed)==59 and sum(x['rgba_pixels'] for x in changed)==11597 and len(unchanged)==53

def owners(out,d):
    owner=np.full((128,128),'',dtype='U32')
    for m in out.glob(f'technical-runtime-mask-{d}-*.png'):
        owner[np.array(Image.open(m).convert('L'))>0]=m.stem.removeprefix(f'technical-runtime-mask-{d}-')
    assert np.all(owner!='');return owner

registration=[];panels=[];nw_points=[]
for d in rig['configs']:
    src=arr(P/f'source/{d}.png');oldowner,newowner=owners(OLD,d),owners(OUT,d)
    use=(oldowner!=newowner)&(src[:,:,3]>0)
    changes=[{'xy':[int(x),int(y)],'rgba':src[y,x].tolist(),'before':oldowner[y,x],'after':newowner[y,x]} for y,x in np.argwhere(use)]
    tools=[t for t in rig['configs'][d]['tools'] if t['blade_polygon']]
    if not tools:
        assert not changes
        continue
    t=tools[0];oldtool=next(t for t in oldrig['configs'][d]['tools'] if t['id']==tools[0]['id'])
    name=t['id']+'_blade';hub=t['hub'];hx,hy=hub
    hub_samples=[{'xy':[x,y],'rgba':src[y,x].tolist(),'owner':newowner[y,x]} for y in sorted({int(np.floor(hy)),int(np.ceil(hy))}) for x in sorted({int(np.floor(hx)),int(np.ceil(hx))})]
    before=(oldowner==name)&(src[:,:,3]>0);after=(newowner==name)&(src[:,:,3]>0)
    # 盘面采纳仍来自同一固定母图，所有重归属坐标明列供视觉核身份。
    registration.append({'direction':d,'old_hub':oldtool['hub'],'hub':hub,'old_pivot':oldtool['pivot'],'pivot':t['pivot'],'old_radius':oldtool['radius'],'radius':t['radius'],'hub_source_samples':hub_samples,'old_opaque_blade':int(before.sum()),'new_opaque_blade':int(after.sum()),'visible_ownership_changes':changes,'transition_counts':dict(collections.Counter(x['before']+' -> '+x['after'] for x in changes))})
    if d=='up_left':
        for x,y in [(80,76),(82,87),(83,78),(83,77),(83,80),(83,79)]:
            assert newowner[y,x]=='saw_blade'
            nw_points.append({'source_xy':[x,y],'rgba':src[y,x].tolist(),'old_owner':oldowner[y,x],'new_owner':newowner[y,x]})
    ys,xs=np.where(before|after);roi=(max(0,int(xs.min())-3),max(0,int(ys.min())-3),min(128,int(xs.max())+4),min(128,int(ys.max())+4))
    for label,data in [('source',src),('v001 blade',np.where(before[:,:,None],src,0).astype(np.uint8)),('v002 blade',np.where(after[:,:,None],src,0).astype(np.uint8))]:
        im=Image.fromarray(data).crop(roi);back=Image.new('RGBA',im.size,(214,218,222,255));back.alpha_composite(im);back=back.resize((im.width*10,im.height*10),Image.Resampling.NEAREST).convert('RGB')
        panel=Image.new('RGB',(300,315),'white');panel.paste(back,(0,30));draw=ImageDraw.Draw(panel);draw.text((4,4),d+' '+label,fill='black')
        if label=='source':
            x,y=(hx-roi[0])*10,(hy-roi[1])*10+30;draw.ellipse([x-3,y-3,x+3,y+3],outline='red',width=1)
        panels.append(panel)

se=[]
for p in rig['configs']['down_right']['parts']:
    prior=next(q for q in oldrig['configs']['down_right']['parts'] if q['id']==p['id']);x,y=p['sole'];src=arr(P/'source/down_right.png');own=owners(OUT,'down_right')
    assert own[y-1,x]==p['id']+'_foot' and src[y-1,x,3]>0
    assert p['ankle']==prior['ankle'] and p['foot_cut_y']==prior['foot_cut_y'] and p['pivot']==prior['pivot']
    se.append({'id':p['id'],'old_nominal_sole':prior['sole'],'new_sole':p['sole'],'source_probe_xy':[x,y-1],'source_rgba':src[y-1,x].tolist(),'source_owner':own[y-1,x],'ankle_unchanged':True,'cut_unchanged':True})

n=[]
newclip=next(c for c in cat['clips'] if c['action']=='attack_up')
for i,pose in enumerate(newclip['poses']):
    t=pose['part_transforms']['body'];basis=np.array([t['basis_x'],t['basis_y']]).T;center=np.array([64,85]);trans=np.array(t['position']);delta=pose['body_translation']
    assert np.allclose(basis.T@basis,np.eye(2),atol=1e-6) and np.allclose(basis@center+trans,center+delta,atol=1e-5)
    assert all(q['basis_x']==[1,0] and q['basis_y']==[0,1] and q['position']==[0,0] for name,q in pose['part_transforms'].items() if name.endswith('_foot'))
    n.append({'frame':i,'body_registration':rig['configs']['up']['attack_body_poses'][i],'body_transform':t,'body_rigid':True,'feet_fixed_identity':True})

sheet=Image.new('RGB',(900,315*len(registration)),(150,150,150))
for i,panel in enumerate(panels):sheet.paste(panel,((i%3)*300,(i//3)*315))
sheet.save(OUT/'technical-blade-registration-10x.png')
out={'status':'PASS_INCREMENT_BINDINGS_VISUAL_SEPARATE','source7_bytes_unchanged':source_equal,'neutral_bytes_unchanged':neutral_equal,'actions_arrays_unchanged':True,'changed_frames':59,'changed_rgba_pixel_events':11597,'unchanged_png_bytes':53,'frames112':frames,'rig_config_diff':diff(oldrig,rig),'blade_registration5':registration,'NW_named_points':nw_points,'SE_corrected_sole_probes':se,'N_attack_rigid6':n,'boundaries':['Ownership changes are true reassignment, not new RGB/source pixels.','A hub sample and valid transform do not establish blade visual continuity; separate visual review is required.','SE source sole probes now point to actual fixed foot pixels; motion can still occlude them.']}
(OUT/'technical-increment.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':out['status'],'changed':59,'rgba_pixel_events':11597,'unchanged':53,'blades':[{'direction':r['direction'],'before':r['old_opaque_blade'],'after':r['new_opaque_blade'],'transitions':r['transition_counts']} for r in registration],'SE':se},ensure_ascii=False))
