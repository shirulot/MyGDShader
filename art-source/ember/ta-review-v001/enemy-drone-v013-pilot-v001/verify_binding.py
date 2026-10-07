"""固定包独立来源/像素/转子投影核验。只在 TA 目录写证据与冷拷贝。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import hashlib,json,math,re
import numpy as np
from PIL import Image

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
DELIVERY=ROOT/'art-source/ember/deliveries'
ZIP=DELIVERY/'enemy_eight_directions_v013_pilot_drone_v001_2026-10-06.zip'
ACTIVE=ROOT/'art-source/ember/enemy-eight-directions-v013-pilot-drone-v001'
PKG=OUT/'cold-project'
EXPECTED='2ef84aaa45b2970bf4db9c5abdf4f845f4d65be9878c97d929701d090d4e37f1'
def sha(b): return hashlib.sha256(b).hexdigest()
def js(b): return json.loads(b.decode('utf-8-sig'))
def im(b): return Image.open(BytesIO(b)).convert('RGBA')
def arr(b): return np.array(im(b))
def path(p): return p.removeprefix('res://')
assert sha(ZIP.read_bytes())==EXPECTED and ZIP.stat().st_size==707823
assert not (PKG/'.godot').exists(),'冷拷贝初始不得含旧缓存'
with ZipFile(ZIP) as z:
    assert z.testzip() is None
    files={n:z.read(n) for n in z.namelist()}
manifest=js(files['manifest.json'])['files']
assert len(files)==56 and len(manifest)==55 and set(manifest)==set(files)-{'manifest.json'}
for n,r in manifest.items(): assert sha(files[n])==r['sha256'] and len(files[n])==r['bytes']
assert all((ACTIVE/n).read_bytes()==b for n,b in files.items())
for n,b in files.items():
    target=PKG/n; assert target.resolve().is_relative_to(PKG.resolve())
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)

rig=js(files['pilot_rigs.json']);spec=next(u for u in rig['units'] if u['unit']=='enemy_scout_drone')
assert rig['enabled_pilot_units']==['enemy_scout_drone'] and (rig['canvas'],rig['root'],rig['frames'],rig['fps'],rig['loop'])==([128,128],[64,104],8,8,True)
assert spec['parts']==[]
source=arr(files[path(spec['source'])]);master=arr(files[path(spec['fan_source'])])
assert sha(files[path(spec['source'])])==spec['source_sha256']=='8cef29b2ad627d52c256a812133b6a3d943ddbdc2a741bd67c0043c8c018acca'
assert sha(files[path(spec['fan_source'])])==spec['fan_source_sha256']=='8824eeff102796d523fa8fab1f17f90c5716b7f34097987c0d5ea8151c2a3a94'
receipt=js(files['STATIC_SOURCE_RECEIPT.json'])
assert receipt['direction_source_sha256']==spec['source_sha256'] and receipt['rotor_source_sha256']==spec['fan_source_sha256']
baselines=[]
for name,expected in [('enemy_drone_seven_directions_v013_s004_2026-10-06.zip','3a6dc8a5ab9c16dc5e71d083568768ff3cabefae2675d5385e552149acb79342'),('enemy_drone_actions_v011_2026-10-06.zip','13a4942d34d0ceabac7473c1689aa4784bc0c6f1555ff68817ed9d93159dab3e'),('enemy_sequences_v012_2026-10-06.zip',None)]:
    baseline=DELIVERY/name;h=sha(baseline.read_bytes());assert expected is None or h==expected
    with ZipFile(baseline) as z:
        if 's004' in name:
            assert files[path(spec['source'])]==z.read('neutral_down_right.png')
            for d in ['down','down_left','left','up_left','up','up_right','right','down_right']:
                assert files[f'output/enemy_scout_drone/neutral_{d}.png']==z.read(f'neutral_{d}.png')
        elif 'v011' in name:
            assert files[path(spec['fan_source'])]==z.read('source/rotor_well_master.png')
            assert files['source/parts/rotor_well_prompt.txt']==z.read('source/rotor_well_prompt.txt')
        else:
            assert files['reference/enemy_scout_drone/move_down.png']==z.read('output/enemy_scout_drone/move_down.png')
            assert files['reference/enemy_scout_drone/neutral_down.png']==z.read('output/enemy_scout_drone/move_down/f00.png')
        baselines.append({'zip':name,'sha256':h,'matched':True})
with ZipFile(DELIVERY/'enemy_drone_diagonal_calibration_v013_c003_2026-10-06.zip') as z:
    assert files[path(spec['source'])]==z.read('neutral_down_right.png')

fans=spec['fans']
assert [(f['center'],f['radius'],f['spin']) for f in fans]==[([48.5,69.5],[6.5,4.5],1),([79.5,58.5],[6.5,4.5],-1)]
yy,xx=np.mgrid[:128,:128];screen=np.stack([xx+.5,yy+.5],axis=2)
masks=[np.sum(((screen-np.array(f['center']))/np.array(f['radius']))**2,axis=2)<1 for f in fans]
aperture=masks[0]|masks[1]
assert int(aperture.sum())==178 and not np.any(masks[0]&masks[1])
bind=arr(files['output/enemy_scout_drone/rig_neutral_down_right.png'])
changed=np.any(bind!=source,axis=2)
assert int(changed.sum())==178 and np.array_equal(changed,aperture) and not np.any(bind[~aperture]!=source[~aperture])
cat=js(files['output/pilot_catalog_v013.json']);clip=cat['clips'][0]
assert len(cat['clips'])==1 and cat['canvas']==[128,128] and cat['root']==[64,104]
assert cat['rig_script_sha256']==sha(files['pilot_rig.gd']) and cat['rig_spec_sha256']==sha(files['pilot_rigs.json'])
assert (clip['unit'],clip['action'],clip['fps'],clip['loop'],clip['frame_count'])==('enemy_scout_drone','move_down_right',8,True,8)
atlas=arr(files[path(clip['atlas'])]);assert atlas.shape==(128,1024,4) and sha(files[path(clip['atlas'])])==clip['atlas_sha256']
assert sha(files[path(clip['tres'])])==clip['tres_sha256'] and sha(files['output/enemy_scout_drone/rig_neutral_down_right.png'])==clip['bind_sha256']
text=files[path(clip['tres'])].decode('utf-8')
raw=np.array([int(v) for v in re.search(r'PackedByteArray\(([^)]+)\)',text).group(1).split(',')],dtype=np.uint8).reshape(128,1024,4)
assert np.array_equal(raw,atlas) and '[ext_resource' not in text
assert [[int(v) for v in m] for m in re.findall(r'region = Rect2\((\d+), (\d+), (\d+), (\d+)\)',text)]==[[128*i,0,128,128] for i in range(8)]
assert text.count('"duration": 1.0')==8 and '"speed": 8.0' in text and '"loop": 1' in text and '"name": &"move_down_right"' in text

bobs=[0,-1,-1,0,1,1,0,0]
frames=[];matrices=[];axis_pixels=[]
for i in range(8):
    png=files[f'output/enemy_scout_drone/move_down_right/f{i:02d}.png'];a=arr(png)
    assert a.shape==(128,128,4) and set(np.unique(a[:,:,3]))=={0,255}
    assert np.array_equal(a,atlas[:,128*i:128*(i+1)]) and sha(png)==clip['frame_hashes'][i]
    shifted=np.full((128,128,4),255,dtype=np.uint8);shifted[:,:,3]=0
    if bobs[i]<0: shifted[:127]=source[1:]
    elif bobs[i]>0:shifted[1:]=source[:127]
    else:shifted=source.copy()
    shiftedmask=np.roll(aperture,bobs[i],axis=0)
    assert np.array_equal(a[~shiftedmask],shifted[~shiftedmask])
    assert int((a[:,:,3]>0).sum())==968
    pose=clip['poses'][i]
    assert pose['frame']==i and pose['body_translation']==[0,bobs[i]] and pose['rotor_angle_deg']==i*11.25 and pose['root']==[64,104] and pose['rotor_count']==2 and pose['blades_per_rotor']==4
    # 屏幕基底 S*R：自身平面先转，再投影；不能对已压扁椭圆直接做屏幕旋转。
    for fan in fans:
        theta=math.radians(i*11.25*fan['spin']);cs,sn=math.cos(theta),math.sin(theta)
        matrix=np.diag(np.array(fan['radius'])/6.5)@np.array([[cs,-sn],[sn,cs]])
        matrices.append({'frame':i,'fan':fan['id'],'angle_deg':i*11.25*fan['spin'],'screen_basis':matrix.tolist(),'axis_screen':[fan['center'][0],fan['center'][1]+bobs[i]],'determinant':float(np.linalg.det(matrix))})
    axis_pixels.append({'frame':i,'far':a[58+bobs[i],79].tolist(),'near':a[69+bobs[i],48].tolist()})
    frames.append({'frame':i,'sha256':sha(png),'atlas_full_rgba_difference':0,'nonaperture_source_after_bob_rgba_difference':0,'body_y':bobs[i],'binary_alpha':True,'visible_pixels':968})
assert all(r['far']==r['near']==[55,39,19,255] for r in axis_pixels)
assert files['output/enemy_scout_drone/move_down_right/f00.png']==files['output/enemy_scout_drone/rig_neutral_down_right.png']

# 独立 CPU 逆变换与源取样。少量理想采样边界差保存实点，不能冒充 GPU 0。
cpu=[]
for i in range(8):
    target=arr(files[f'output/enemy_scout_drone/move_down_right/f{i:02d}.png'])
    predicted=np.full((128,128,4),255,dtype=np.uint8);predicted[:,:,3]=0
    sample_records={}
    for fi,fan in enumerate(fans):
        theta=math.radians(i*11.25*fan['spin']);cs,sn=math.cos(theta),math.sin(theta)
        center=np.array(fan['center'])+[0,bobs[i]]
        for y,x in zip(*np.where(np.roll(masks[fi],bobs[i],axis=0))):
            local=(np.array([x+.5,y+.5])-center)/(np.array(fan['radius'])/6.5)
            for layer in ['well','rotor']:
                p=local if layer=='well' else np.array([[cs,sn],[-sn,cs]])@local
                if np.linalg.norm(p)>6.5:continue
                r=spec[layer+'_rect'];uv=np.array(r[:2])+(p+6.5)/13*np.array(r[2:]);sx,sy=np.floor(uv).astype(int)
                v=master[sy,sx].copy()
                if v[3]<128:continue
                v[3]=255;predicted[y,x]=v
                sample_records[(int(x),int(y))]={'layer':layer,'source_float':uv.tolist(),'source_texel':[int(sx),int(sy)]}
    diffs=[]
    for y,x in zip(*np.where(np.any(predicted!=target,axis=2)&np.roll(aperture,bobs[i],axis=0))):
        r=sample_records.get((int(x),int(y)),{}).copy()
        r.update({'output':[int(x),int(y)],'cpu_rgba':predicted[y,x].tolist(),'png_rgba':target[y,x].tolist()})
        diffs.append(r)
    cpu.append({'frame':i,'ideal_cpu_aperture_rgba_pixel_diffs':len(diffs),'diffs':diffs})

contacts=[]
for color in ['white','black']:
    base=Image.new('RGBA',(1024,128),color);base.alpha_composite(Image.fromarray(atlas))
    for factor in [1,4]:
        n=f'qa/enemy_scout_drone_move_{color}_{factor}x.png'
        assert base.resize((1024*factor,128*factor),Image.Resampling.NEAREST).tobytes()==im(files[n]).tobytes()
        contacts.append({'file':n,'full_rgba_difference':0})

author=[];catalog_sha=sha(files['output/pilot_catalog_v013.json'])
for name in ['qa/pilot_gpu_roundtrip.json','qa/pilot_pixel_audit.json','qa/pilot_runtime.json']:
    r=js(files[name]);assert r['catalog_sha256']==catalog_sha and r['status']=='PASS'
    author.append({'file':name,'sha256':sha(files[name]),'catalog_sha_same':True,'independent_rerun':False})
gpu=js(files['qa/pilot_gpu_roundtrip.json'])['records'];assert len(gpu)==16
assert {(r['frame'],r['background']) for r in gpu}=={(i,b) for i in range(8) for b in ['white','black']}
assert all(r['live_rig_vs_png_differing_channels']==r['tres_vs_png_differing_channels']==0 and r['unit']=='enemy_scout_drone' for r in gpu)
runtime=js(files['qa/pilot_runtime.json'])
assert len(runtime['completed_loops'])==4 and all(n>=1 for n in runtime['completed_loops'].values()) and all(v==list(range(8)) for v in runtime['seen_frames'].values())
assert len(runtime['direction_switches'])==8 and all(r['pass'] for r in runtime['direction_switches'])
result={'status':'STATIC_SOURCE_EXPORT_BINDING_PASS_PENDING_COLD','zip_sha256':EXPECTED,'zip_bytes':ZIP.stat().st_size,'entries':56,'payload':55,'crc_manifest_and_active_56_same':True,'baselines':baselines,'static_8_and_SE_source_same':True,'fan_source_v011_not_r1_same':True,'catalog_sha256':catalog_sha,'bind_changed_pixels':178,'bind_changed_outside_two_ellipses':0,'aperture_points_each':[int(m.sum()) for m in masks],'8frame_nonaperture_protection_difference':0,'frames':frames,'rotor_screen_matrices_SR':matrices,'axis_rgba_each_frame':axis_pixels,'cpu_rotor_aperture_reconstruction':cpu,'embedded_tres_atlas_full_rgba_difference':0,'contacts':contacts,'author_bindings':author,'author_gpu_records':16,'author_playback_record_groups':4,'author_switch_records':8,'gpu_saved_framebuffer_png_count':0,'ta_gpu_rerun':False}
(OUT/'binding.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'entries':56,'payload':55,'changed':178,'outside':0,'cpu_diffs_by_frame':[r['ideal_cpu_aperture_rgba_pixel_diffs'] for r in cpu],'tres_rgba_diff':0,'author_gpu':16},indent=2))
