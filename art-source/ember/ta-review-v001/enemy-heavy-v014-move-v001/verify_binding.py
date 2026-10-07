"""重装六新向固定包来源、ownership、实际像素流、内嵌资源独立审计。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import json,hashlib,math,re
import numpy as np
from PIL import Image
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
DELIVERY=ROOT/'art-source/ember/deliveries'
ZIP=DELIVERY/'enemy_heavy_eight_moves_v014_v001_2026-10-06.zip'
ACTIVE=ROOT/'art-source/ember/enemy-heavy-directions-move-v014-review-v001'
PKG=OUT/'cold-project'
EXPECTED='dbad34a8845cce2a648d904790f5abd34fd64abbb5762f50d458f595e648c9ae'
def sha(b):return hashlib.sha256(b).hexdigest()
def js(b):return json.loads(b.decode('utf-8-sig'))
def path(p):return p.removeprefix('res://')
def im(b):return Image.open(BytesIO(b)).convert('RGBA')
def arr(b):return np.array(im(b))
assert sha(ZIP.read_bytes())==EXPECTED and ZIP.stat().st_size==3906157
assert not (PKG/'.godot').exists()
with ZipFile(ZIP) as z:
    assert z.testzip() is None
    files={n:z.read(n) for n in z.namelist()}
manifest=js(files['manifest.json'])['files']
assert len(files)==160 and len(manifest)==159 and set(manifest)==set(files)-{'manifest.json'}
assert all(sha(files[n])==r['sha256'] and len(files[n])==r['bytes'] for n,r in manifest.items())
assert all((ACTIVE/n).read_bytes()==b for n,b in files.items())
for n,b in files.items():
    target=PKG/n;assert target.resolve().is_relative_to(PKG.resolve())
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
spec=js(files['rig.json']);cat=js(files['output/catalog.json']);receipt=js(files['SOURCE_RECEIPT.json'])
dirs=['down','down_left','left','up_left','up','up_right','right','down_right']
new=['down_left','left','up_left','up','up_right','right']
assert spec['directions']==dirs and set(spec['configs'])==set(new)
assert (spec['canvas'],spec['root'],spec['frame_count'],spec['fps'],spec['loop'],spec['body_y'])==([128,128],[64,104],8,8,True,[0,0,1,0,0,0,1,0])
assert cat['canvas']==[128,128] and cat['root']==[64,104] and cat['rig_sha256']==sha(files['rig.json'])
assert len(cat['clips'])==8 and [c['direction'] for c in cat['clips']]==dirs
original=ROOT/'art-source/ember/enemy-eight-directions-v013'
oldcat=js((original/'static_preflight_v001/master_catalog_v013.json').read_bytes())
masters={r['direction']:r for r in oldcat['masters'] if r['unit']=='enemy_tracked_heavy'}
static=[]
for d in dirs:
    n='source/'+d+'.png';h=sha(files[n]);source=arr(files[n])
    assert h==receipt['source_png_hashes'][d+'.png'] and source.shape==(128,128,4)
    assert set(np.unique(source[:,:,3]))=={0,255}
    assert files['output/enemy_tracked_heavy/neutral_'+d+'.png']==files[n]
    assert masters[d]['sha256']==h and (original/path(masters[d]['path'])).read_bytes()==files[n]
    static.append({'direction':d,'sha256':h,'snapshot_master_catalog_and_original_png_same':True})
reg=js(files['provenance/registration.json'])
assert files['provenance/registration.json']==(original/'registration.json').read_bytes()==(original/'static_preflight_v001/registration.json').read_bytes()
heavy=next(r for r in reg['units'] if r['unit']=='enemy_tracked_heavy')
assert files['provenance/'+path(heavy['source'])]==(original/path(heavy['source'])).read_bytes()
assert sha(files['provenance/'+path(heavy['source'])])==heavy['source_sha256']
assert files['provenance/prompts/enemy_tracked_heavy_eight_views_v001.txt']==(original/'prompts/enemy_tracked_heavy_eight_views_v001.txt').read_bytes()
baselines=[]
for d,name,member,expected in [('down','enemy_sequences_v012_2026-10-06.zip','output/enemy_tracked_heavy/move_down','42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe'),('down_right','enemy_eight_directions_v013_pilot_hc_v001_2026-10-06.zip','output/enemy_tracked_heavy/move_down_right','5db52757c74fc537b3f45d87abdbab8c58e5d8fcd3cf6366153f7b32ef98b9ef')]:
    base=DELIVERY/name;assert sha(base.read_bytes())==expected
    assert receipt['down_zip_sha256' if d=='down' else 'down_right_zip_sha256']==expected
    with ZipFile(base) as z:
        for i in range(8):assert files[f'output/enemy_tracked_heavy/move_{d}/f{i:02d}.png']==z.read(f'{member}/f{i:02d}.png')
        assert files[f'output/enemy_tracked_heavy/move_{d}.png']==z.read(member+'.png')
    baselines.append({'direction':d,'zip':name,'sha256':expected,'eight_frames_and_atlas_byte_same':True})

def inside(x,y,poly):
    hit=False;j=len(poly)-1
    for i,a in enumerate(poly):
        b=poly[j]
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:hit=not hit
        j=i
    return hit
new_records=[];allframes=[];contacts=[]
for clip in cat['clips']:
    d=clip['direction'];assert (clip['action'],clip['unit'],clip['fps'],clip['loop'],clip['frame_count'])==('move_'+d,'enemy_tracked_heavy',8,True,8)
    atlas=arr(files[path(clip['atlas'])]);assert atlas.shape==(128,1024,4) and sha(files[path(clip['atlas'])])==clip['atlas_sha256']
    frames=[]
    for i in range(8):
        n=f'output/enemy_tracked_heavy/move_{d}/f{i:02d}.png';a=arr(files[n])
        assert a.shape==(128,128,4) and np.array_equal(a,atlas[:,128*i:128*(i+1)]) and sha(files[n])==clip['frame_hashes'][i]
        assert set(np.unique(a[:,:,3]))=={0,255} and not any(np.any(v[:,:,3]) for v in [a[:1],a[-1:],a[:,:1],a[:,-1:]])
        allframes.append({'direction':d,'frame':i,'sha256':sha(files[n]),'atlas_rgba_difference':0,'binary_alpha':True,'edge_visible_pixels':0})
        frames.append(a)
    if d in new:
        config=spec['configs'][d];source=arr(files[path(config['source'])]);visible=source[:,:,3]>0
        assert sha(files[path(config['source'])])==config['source_sha256']
        assert np.array_equal(source,frames[0]) and files[f'qa/bind_{d}.png']==files[f'output/enemy_tracked_heavy/move_{d}/f00.png']
        owned=np.array([[any(inside(x+.5,y+.5,p) for p in config['track_polygons']) for x in range(128)] for y in range(128)])
        body=visible&~owned;tracks=visible&owned
        assert not np.any(body&tracks) and np.array_equal(body|tracks,visible)
        windows=[];winmask=np.zeros((128,128),dtype=np.uint8)
        for w in config['windows']:
            assert w['period']==16 and w['sign'] in [-1,1]
            x0,y0=w['origin'];points=[]
            for y in range(128):
                for x in range(128):
                    top=y0+math.floor((x-x0)*w['shear'])
                    inwindow=(x0<=x<x0+16 and y0<=y<y0+w['thickness']) if w['horizontal'] else (x0<=x<x0+w['cross_width'] and top<=y<top+16)
                    if inwindow:points.append([x,y]);winmask[y,x]+=1
            windows.append({'definition':w,'native_window_pixels':len(points),'owned_visible_window_pixels':sum(bool(tracks[y,x]) for x,y in points),'destination_rgb_feature_flow':('right' if w['sign']>0 else 'left') if w['horizontal'] else ('down' if w['sign']>0 else 'up'),'points':points})
        assert int(winmask.max())==1
        cpu=[];unsafe=[]
        for i in range(8):
            image=np.full((128,128,4),255,dtype=np.uint8);image[:,:,3]=0
            for y,x in zip(*np.where(tracks)):
                color=source[y,x].copy()
                for w in config['windows']:
                    x0,y0=w['origin'];top=y0+math.floor((x-x0)*w['shear'])
                    hit=(x0<=x<x0+16 and y0<=y<y0+w['thickness']) if w['horizontal'] else (x0<=x<x0+w['cross_width'] and top<=y<top+16)
                    if hit:
                        sx=x0+(x-x0-i*2*w['sign'])%16 if w['horizontal'] else x
                        sy=y if w['horizontal'] else top+(y-top-i*2*w['sign'])%16
                        if not(0<=sx<128 and 0<=sy<128) or source[sy,sx,3]<128:unsafe.append({'frame':i,'dest':[int(x),int(y)],'sample':[int(sx),int(sy)]})
                        color[:3]=source[sy,sx,:3]
                image[y,x]=color
            bob=spec['body_y'][i]
            for sy,sx in zip(*np.where(body)):
                dy=sy+bob
                assert 0<=dy<128
                image[dy,sx]=source[sy,sx]
            delta=np.any(image!=frames[i],axis=2);ys,xs=np.where(delta)
            diffs=[{'output':[int(x),int(y)],'cpu_rgba':image[y,x].tolist(),'png_rgba':frames[i][y,x].tolist()} for y,x in zip(ys,xs)]
            cpu.append({'frame':i,'full_rgba_pixel_differences':len(diffs),'alpha_pixel_differences':int(np.sum(image[:,:,3]!=frames[i][:,:,3])),'diffs':diffs})
            pose=clip['poses'][i]
            assert pose['frame']==i and pose['direction']==d and pose['body_translation']==[0,bob] and pose['tread_phase']==i*2 and pose['supports']==config['supports'] and pose['root']==[64,104]
        new_records.append({'direction':d,'source_visible':int(visible.sum()),'track_visible':int(tracks.sum()),'body_visible':int(body.sum()),'ownership_missing_or_double_pixels':0,'bind_full_rgba_difference':0,'supports':config['supports'],'windows':windows,'window_overlap_pixels':int(np.sum(winmask>1)),'unsafe_source_samples':unsafe,'cpu_native_reconstruction':cpu,'phase_8_equals_phase_0_source_indices':True})
        # 自有 ownership 图供必要时查轮盖与侧甲归属，保持原位置。
        color=source.copy();color[tracks,:3]=[24,142,158];color[body,:3]=[221,94,47]
        Image.fromarray(color).resize((1024,1024),Image.Resampling.NEAREST).save(OUT/(d+'_ownership_8x.png'))
    for color in ['white','black']:
        contact=Image.new('RGBA',(512,256),color)
        for i,a in enumerate(frames):contact.alpha_composite(Image.fromarray(a),((i%4)*128,(i//4)*128))
        for factor in [1,4]:
            n=f'qa/move_{d}_{color}_{factor}x.png'
            assert contact.resize((512*factor,256*factor),Image.Resampling.NEAREST).tobytes()==im(files[n]).tobytes()
            contacts.append({'file':n,'full_rgba_difference':0})
    if d in new:
        roi=Image.new('RGBA',(352,96),'white')
        for i,a in enumerate(frames):roi.alpha_composite(Image.fromarray(a).crop((20,58,108,106)),((i%4)*88,(i//4)*48))
        assert roi.resize((1408,384),Image.Resampling.NEAREST).tobytes()==im(files[f'qa/treads_{d}_4x.png']).tobytes()

text=files[path(cat['tres'])].decode('utf-8');assert '[ext_resource' not in text and sha(files[path(cat['tres'])])==cat['tres_sha256']
images=re.findall(r'\[sub_resource type="Image" id="([^\"]+)"\]\s*data = \{\s*"data": PackedByteArray\(([^)]+)\)',text)
atlas_by_rgba={arr(files[path(c['atlas'])]).tobytes():c['direction'] for c in cat['clips']}
matched=[]
for ident,raw in images:
    image=np.array([int(v) for v in raw.split(',')],dtype=np.uint8).tobytes()
    assert image in atlas_by_rgba
    matched.append({'image_subresource':ident,'direction':atlas_by_rgba[image],'full_rgba_difference':0})
assert len(matched)==8 and {r['direction'] for r in matched}==set(dirs)
assert len(re.findall(r'region = Rect2\(',text))==64 and text.count('"duration": 1.0')==64 and text.count('"speed": 8.0')==8 and text.count('"loop": 1')==8

author=[];catalogsha=sha(files['output/catalog.json'])
for n in ['qa/gpu_roundtrip.json','qa/pixel_audit.json','qa/runtime.json']:
    data=js(files[n]);assert data['status']=='PASS' and data['catalog_sha256']==catalogsha
    author.append({'file':n,'sha256':sha(files[n]),'catalog_sha_same':True,'ta_rerun':False})
gpu=js(files['qa/gpu_roundtrip.json'])['records']
fresh=[r for r in gpu if not r.get('preserved',False)];old=[r for r in gpu if r.get('preserved',False)]
assert len(fresh)==96 and len(old)==16
assert {(r['action'],r['frame'],r['background']) for r in fresh}=={('move_'+d,i,b) for d in new for i in range(8) for b in ['white','black']}
assert all(r['tres_vs_png']==0 and r['live_rig_vs_png']==0 for r in fresh) and all(r['tres_vs_png']==0 for r in old)
runtime=js(files['qa/runtime.json']);assert len(runtime['loops'])==16 and all(v>=1 for v in runtime['loops'].values())
assert all(v==list(range(8)) for v in runtime['seen_frames'].values()) and len(runtime['switches'])==8 and all(r['passed'] for r in runtime['switches'])
coldpath=ROOT/'art-source/ember/enemy-heavy-directions-move-v014/qa/cold_receipt_v001.json'
cold=js(coldpath.read_bytes());assert cold['zip_sha256']==EXPECTED and cold['payloads']==159
producerpath=Path(cold['cold_project']);same=[];different=[];missing=[]
for n,r in manifest.items():
    p=producerpath/n
    if not p.is_file():missing.append(n)
    elif sha(p.read_bytes())==r['sha256']:same.append(n)
    else:different.append({'path':n,'current_sha256':sha(p.read_bytes()),'zip_sha256':r['sha256']})
result={'status':'FIXED_SOURCE_EXPORT_BINDING_PASS_PENDING_COLD','zip_sha256':EXPECTED,'zip_bytes':ZIP.stat().st_size,'entries':160,'payload':159,'crc_manifest_and_active_160_same':True,'static_original_8':static,'preserved_two_clips':baselines,'new_6':new_records,'frames64':allframes,'embedded8_images':matched,'contacts32':contacts,'treads6_roi_composition_rgba_difference':0,'catalog_sha256':catalogsha,'author_bindings':author,'author_gpu_new_live96':96,'author_gpu_old_tres_only16':16,'author_player_groups':16,'author_switches':8,'producer_cold_receipt':{'path':str(coldpath.relative_to(ROOT)),'sha256':sha(coldpath.read_bytes()),'claims':cold,'current_manifest_byte_same':len(same),'current_manifest_different':different,'current_manifest_missing':missing},'ta_gpu_rerun':False}
(OUT/'binding.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'payload':159,'new':[{ 'd':r['direction'],'cpu_diffs':[v['full_rgba_pixel_differences'] for v in r['cpu_native_reconstruction']],'unsafe':len(r['unsafe_source_samples'])} for r in new_records],'producer_cold_same':len(same),'producer_cold_missing':missing,'producer_cold_different':different},indent=2))
