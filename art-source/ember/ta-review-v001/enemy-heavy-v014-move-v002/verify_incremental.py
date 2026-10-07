"""v002 增量独立审计：固定包、N采样域、保护区与嵌入资源；不运行生产器。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import json,hashlib,copy,re
import numpy as np
from PIL import Image
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
D=ROOT/'art-source/ember/deliveries'
OLD=D/'enemy_heavy_eight_moves_v014_v001_2026-10-06.zip'
ZIP=D/'enemy_heavy_eight_moves_v014_v002_2026-10-07.zip'
ACTIVE=ROOT/'art-source/ember/enemy-heavy-directions-move-v014-review-v002'
PKG=OUT/'cold-project'
EXPECTED='74ce3153d2389e9d170fbc5ccf0ea92dcf0a14dd671822d3479a5feaa1d00db9'
def sha(b):return hashlib.sha256(b).hexdigest()
def js(b):return json.loads(b.decode('utf-8-sig'))
def im(b):return Image.open(BytesIO(b)).convert('RGBA')
def arr(b):return np.array(im(b))
def path(s):return s.removeprefix('res://')
assert sha(ZIP.read_bytes())==EXPECTED and ZIP.stat().st_size==3901897
assert sha(OLD.read_bytes())=='dbad34a8845cce2a648d904790f5abd34fd64abbb5762f50d458f595e648c9ae'
assert not (PKG/'.godot').exists()
with ZipFile(ZIP) as z,ZipFile(OLD) as old:
    assert z.testzip() is None and old.testzip() is None
    files={n:z.read(n) for n in z.namelist()};before={n:old.read(n) for n in old.namelist()}
manifest=js(files['manifest.json'])['files']
assert len(files)==162 and len(manifest)==161 and set(manifest)==set(files)-{'manifest.json'}
assert all(sha(files[n])==r['sha256'] and len(files[n])==r['bytes'] for n,r in manifest.items())
assert all((ACTIVE/n).read_bytes()==b for n,b in files.items())
for n,b in files.items():
    p=PKG/n;assert p.resolve().is_relative_to(PKG.resolve());p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
added=sorted(set(files)-set(before));removed=sorted(set(before)-set(files))
changed=sorted(n for n in set(before)&set(files) if before[n]!=files[n])
assert added==['audit_tread_sources.py','qa/tread_source_audit.json'] and not removed
oldrig=js(before['rig.json']);rig=js(files['rig.json']);expected=copy.deepcopy(oldrig)
expected['configs']['up']['windows'][0]['origin'][0]=31
expected['configs']['up']['windows'][0]['cross_width']=11
expected['revision']=rig['revision'] # 新增说明字段，不属于运行几何。
assert rig==expected
assert all(files[n]==before[n] for n in before if n.startswith('source/') or n.startswith('provenance/') or n=='SOURCE_RECEIPT.json')
unchanged_code=['rig.gd','tread_flow.gdshader','masked_part.gdshader','preview.gd','preview.tscn','project.godot','capture.gd','verify.gd','inspect_treads.gd','pixel_audit.py']
assert all(files[n]==before[n] for n in unchanged_code)
dirs=rig['directions'];preserved=[]
for d in dirs:
    if d=='up':continue
    for n in [f'output/enemy_tracked_heavy/move_{d}.png']+[f'output/enemy_tracked_heavy/move_{d}/f{i:02d}.png' for i in range(8)]:
        assert files[n]==before[n];preserved.append(n)
assert len(preserved)==63
assert files['output/enemy_tracked_heavy/move_up/f00.png']==before['output/enemy_tracked_heavy/move_up/f00.png']==files['source/up.png']
yy,xx=np.mgrid[:128,:128];oldwin=(xx>=28)&(xx<=43)&(yy>=85)&(yy<=100)
removed_columns=((xx>=28)&(xx<=30)|(xx>=42)&(xx<=43))&(yy>=85)&(yy<=100)
diffrecords=[];opaque_edge_points=[]
source=arr(files['source/up.png'])
for i in range(8):
    old=arr(before[f'output/enemy_tracked_heavy/move_up/f{i:02d}.png']);new=arr(files[f'output/enemy_tracked_heavy/move_up/f{i:02d}.png'])
    delta=np.any(old!=new,axis=2);ys,xs=np.where(delta)
    assert int(delta.sum())==(0 if i==0 else 75) and not np.any(delta&~removed_columns)
    assert np.array_equal(old[:,:,3],new[:,:,3]) and np.array_equal(old[~oldwin],new[~oldwin])
    assert np.array_equal(new[delta],source[delta])
    diffrecords.append({'frame':i,'rgba_changed_pixels':int(delta.sum()),'rgb_only':True,'alpha_difference':0,'outside_original_window_difference':0,'outside_removed_edge_columns_difference':0,'changed_pixels_equal_original_fixed_source':True,'changed_coordinates':[[int(x),int(y)] for y,x in zip(ys,xs)]})
olddefects=json.loads((OUT.parent/'enemy-heavy-v014-move-v001/binding.json').read_text())['P2_up_tread_white_sampling']['observed_output_source_bindings']
for r in olddefects:
    i=r['frame'];x,y=r['dest'];a=arr(files[f'output/enemy_tracked_heavy/move_up/f{i:02d}.png'])
    assert a[y,x].tolist()==source[y,x].tolist() and a[y,x].tolist()!=[255,255,255,255]
    opaque_edge_points.append({'frame':i,'output':[x,y],'v001_rgba':[255,255,255,255],'v002_rgba':a[y,x].tolist(),'source_rgba':source[y,x].tolist(),'closed':True})
assert len(opaque_edge_points)==33
sample_records=[]
for wi,w in enumerate(rig['configs']['up']['windows']):
    assert w['period']==16 and w['sign']==-1 and not w['horizontal'] and w['shear']==0
    x0,y0=w['origin'];invalid=[];count=0;rgbdiff=[]
    for i in range(8):
        a=arr(files[f'output/enemy_tracked_heavy/move_up/f{i:02d}.png'])
        for x in range(x0,x0+w['cross_width']):
            for y in range(y0,y0+16):
                if source[y,x,3]<128:continue
                count+=1;sy=y0+(y-y0-i*2*w['sign'])%16
                if source[sy,x,3]<128:invalid.append({'f':i,'dest':[x,y],'source':[x,sy]})
                if not np.array_equal(a[y,x,:3],source[sy,x,:3]):rgbdiff.append([i,x,y])
    assert not invalid and not rgbdiff
    sample_records.append({'window':wi,'definition':w,'actual_source_samples':count,'transparent_source_sample_count':0,'window_output_rgb_source_difference':0,'flow':'up2px/frame','phase8_equals_phase0':True})
cat=js(files['output/catalog.json']);assert cat['rig_sha256']==sha(files['rig.json'])
catalogsha=sha(files['output/catalog.json']);allframes=[]
for c in cat['clips']:
    atlas=arr(files[path(c['atlas'])]);assert atlas.shape==(128,1024,4) and sha(files[path(c['atlas'])])==c['atlas_sha256']
    assert (c['frame_count'],c['fps'],c['loop'])==(8,8,True)
    for i in range(8):
        n=f'output/enemy_tracked_heavy/{c["action"]}/f{i:02d}.png';a=arr(files[n]);assert np.array_equal(a,atlas[:,128*i:128*(i+1)]) and sha(files[n])==c['frame_hashes'][i]
        allframes.append({'action':c['action'],'frame':i,'atlas_full_rgba_difference':0})
text=files[path(cat['tres'])].decode('utf-8');assert sha(files[path(cat['tres'])])==cat['tres_sha256'] and '[ext_resource' not in text
images=re.findall(r'\[sub_resource type="Image" id="([^\"]+)"\]\s*data = \{\s*"data": PackedByteArray\(([^)]+)\)',text)
atlas_bytes={arr(files[path(c['atlas'])]).tobytes():c['direction'] for c in cat['clips']};mapped=[]
for ident,data in images:
    b=np.array([int(v) for v in data.split(',')],dtype=np.uint8).tobytes();assert b in atlas_bytes;mapped.append({'id':ident,'direction':atlas_bytes[b],'rgba_difference':0})
assert len(mapped)==8 and {r['direction'] for r in mapped}==set(dirs)
contacts=[]
for color in ['white','black']:
    contact=Image.new('RGBA',(512,256),color)
    for i in range(8):contact.alpha_composite(im(files[f'output/enemy_tracked_heavy/move_up/f{i:02d}.png']),((i%4)*128,(i//4)*128))
    for factor in [1,4]:
        n=f'qa/move_up_{color}_{factor}x.png';assert contact.resize((512*factor,256*factor),Image.Resampling.NEAREST).tobytes()==im(files[n]).tobytes();contacts.append({'file':n,'rgba_difference':0})
author=[]
for n in ['qa/gpu_roundtrip.json','qa/pixel_audit.json','qa/runtime.json','qa/tread_source_audit.json']:
    q=js(files[n]);assert q['catalog_sha256']==catalogsha and q['status']=='PASS';author.append({'file':n,'sha256':sha(files[n]),'catalog_sha_same':True,'TA_full_rerun':False})
gpu=js(files['qa/gpu_roundtrip.json'])['records'];fresh=[r for r in gpu if not r.get('preserved',False)];old=[r for r in gpu if r.get('preserved',False)]
assert len(fresh)==96 and len(old)==16 and all(r['live_rig_vs_png']==r['tres_vs_png']==0 for r in fresh) and all(r['tres_vs_png']==0 for r in old)
runtime=js(files['qa/runtime.json']);assert len(runtime['loops'])==16 and all(v>=1 for v in runtime['loops'].values()) and len(runtime['switches'])==8 and all(r['passed'] for r in runtime['switches'])
external=ROOT/'art-source/ember/enemy-heavy-directions-move-v014/qa/cold_receipt_v002.json';cold=js(external.read_bytes());assert cold['zip_sha256']==EXPECTED and cold['payloads']==161
coldroot=Path(cold['cold_project']);cold_same=[];cold_diff=[];cold_missing=[]
for n,r in manifest.items():
    p=coldroot/n
    if not p.is_file():cold_missing.append(n)
    elif sha(p.read_bytes())==r['sha256']:cold_same.append(n)
    else:cold_diff.append({'file':n,'zip_sha256':r['sha256'],'current_sha256':sha(p.read_bytes())})
served=ROOT/'art-source/ember/enemy-sequences-v001/previews/heavy-eight-moves-v014-v002'
serve=[]
for n,m in [('index.html','previews/index.html'),('catalog.json','output/catalog.json'),('output/enemy_tracked_heavy/move_up.png','output/enemy_tracked_heavy/move_up.png')]:
    assert (served/n).read_bytes()==files[m];serve.append({'file':n,'sha256':sha(files[m]),'package_same':True})
# 自有同位置8×旧/新定点图；不改生产图。
diag=Image.new('RGBA',(256,64),'#080b10')
for i in range(8):
    for row,data in enumerate([before,files]):diag.alpha_composite(im(data[f'output/enemy_tracked_heavy/move_up/f{i:02d}.png']).crop((24,82,56,114)),(32*i,32*row))
diag.resize((2048,512),Image.Resampling.NEAREST).save(OUT/'N_left_old_new_8x.png')
result={'status':'P2_PIXEL_SOURCE_CLOSED_PENDING_COLD','zip_sha256':EXPECTED,'zip_bytes':3901897,'entries':162,'payload':161,'manifest_crc_active_162_same':True,'v001_zip_sha256':sha(OLD.read_bytes()),'zipdiff':{'added':added,'removed':removed,'changed':changed},'rig_only_runtime_changes_N_left_origin_x_28_to31_crosswidth16_to11':True,'rig_added_revision_text':rig['revision'],'original_sources_provenance_and_receipt_all_byte_same':True,'unchanged_runtime_code':unchanged_code,'preserved7_moves63_png_atlases':preserved,'N_F00_byte_same':True,'N_pixels':diffrecords,'P2_33_prior_white_points_closed':opaque_edge_points,'N_actual_window_samples':sample_records,'64frames_atlas_rgba_zero':allframes,'tres8embedded_images':mapped,'N_contacts4':contacts,'catalog_sha256':catalogsha,'author_record_bindings':author,'author_GPU_live96_new_and16_old_tres_only':True,'author16player8turn_bind_only':True,'producer_cold':{'receipt_sha256':sha(external.read_bytes()),'claims':cold,'current_same':len(cold_same),'current_different':cold_diff,'current_missing':cold_missing},'served_local':serve,'TA_gpu_rerun':False}
(OUT/'binding.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'N_RGB_changes':[r['rgba_changed_pixels'] for r in diffrecords],'prior33_white_points_closed':len(opaque_edge_points),'invalid_samples':0,'all_N_window_RGB_diff':0,'preserved_pngs':len(preserved),'cold_same':len(cold_same),'cold_different':cold_diff},indent=2))
