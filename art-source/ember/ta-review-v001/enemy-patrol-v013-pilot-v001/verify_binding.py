"""巡逻SE pilot：从固定包独立核来源、源mask、端点及原生导出，不运行生产器。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from collections import Counter
import hashlib, json, math, re
import numpy as np
from PIL import Image, ImageDraw

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
ZIP=ROOT/'art-source/ember/deliveries/enemy_eight_directions_v013_pilot_patrol_v001_2026-10-06.zip'
ACTIVE=ROOT/'art-source/ember/enemy-eight-directions-v013-pilot-patrol-v001'
PKG=OUT/'cold-project'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(b):return json.loads(b.decode('utf-8-sig'))
def im(b):return Image.open(BytesIO(b)).convert('RGBA')
def arr(b):return np.array(im(b))
def path(v):return v.removeprefix('res://')
EXPECTED='c7cf9683604740953a48d43b6fd2fbf7cd5d11767ee3af1fbc65171d4493dd21'
assert sha(ZIP.read_bytes())==EXPECTED
assert not (PKG/'.godot').exists(), '独立冷工程必须从无导入缓存开始'
with ZipFile(ZIP) as z:
 assert z.testzip() is None
 files={n:z.read(n) for n in z.namelist()}
 manifest=load(files['manifest.json'])['files']
 assert len(files)==53 and len(manifest)==52 and set(manifest)==set(files)-{'manifest.json'}
 for name,row in manifest.items():
  assert len(files[name])==row['bytes'] and sha(files[name])==row['sha256']
  assert (ACTIVE/name).read_bytes()==files[name]
 for name,data in files.items():
  dest=PKG/name
  assert dest.resolve().is_relative_to(PKG.resolve())
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)

 rig=load(files['pilot_rigs.json']);unit=rig['units'][0]
 assert rig['enabled_pilot_units']==['enemy_patrol']
 assert rig['canvas']==[128,128] and rig['root']==[64,104] and (rig['frames'],rig['fps'],rig['loop'])==(8,8,True)
 assert unit['unit']=='enemy_patrol' and sha(files[path(unit['source'])])==unit['source_sha256']=='e1916f467c4493bab2b95b57b558f18ab2090c45721c48cff590422139cb93f2'
 source=arr(files[path(unit['source'])]);assert source.shape==(128,128,4)
 basezip=ROOT/'art-source/ember/deliveries/enemy_patrol_seven_directions_v013_s002_2026-10-06.zip'
 assert sha(basezip.read_bytes())=='28951089e1403c65f6a8446aed5f049fdba704809175da36a391c6c5fa1e99a1'
 with ZipFile(basezip) as baseline:
  assert baseline.read('neutral_down_right.png')==files[path(unit['source'])]
  for direction in ['down','down_left','left','up_left','up','up_right','right','down_right']:
   assert baseline.read('neutral_'+direction+'.png')==files['output/enemy_patrol/neutral_'+direction+'.png']
 downzip=ROOT/'art-source/ember/deliveries/enemy_patrol_actions_v008_2026-10-06.zip'
 assert sha(downzip.read_bytes())=='4a3ab26e04abb5816c505fb0c0f851b8042886d8ea3d2b8516b1923360af74b4'
 with ZipFile(downzip) as down:
  assert unit['phases']==load(down.read('rig.json'))['phases']
  assert files['reference/enemy_patrol/move_down.png']==down.read('output/move_down_v008.png')
 assert files['output/enemy_patrol/rig_neutral_down_right.png']==files[path(unit['source'])]

 def inside(x,y,poly):
  hit=False;j=len(poly)-1
  for i,a in enumerate(poly):
   b=poly[j]
   if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:hit=not hit
   j=i
  return hit
 masks={};defs={p['id']:p for p in unit['parts']}
 assert len(defs)==8
 for part in unit['parts']:
  masks[part['id']]=np.array([[any(inside(x+.5,y+.5,p) for p in [part['polygon']]+part.get('overlap_polygons',[]))
      and not any(inside(x+.5,y+.5,p) for p in part['exclude']) for x in range(128)] for y in range(128)])
 masks['body']=np.array([[not any(inside(x+.5,y+.5,p['polygon']) for p in unit['parts'])
     and not any(inside(x+.5,y+.5,p) for p in unit.get('remove_polygons',[])) for x in range(128)] for y in range(128)])
 visible=source[:,:,3]>0
 owners=sum(m.astype(np.uint8) for m in masks.values())
 assert not np.any((owners!=1)&visible)
 ownership={k:int((v&visible).sum()) for k,v in masks.items()}
 ownership_png=Image.new('RGB',(128,128),'white')
 colors={'body':(100,100,100),'right_thigh':(200,50,50),'right_shin':(240,100,40),'right_cap':(230,200,40),
  'right_foot':(100,210,40),'left_thigh':(40,170,220),'left_shin':(60,70,220),'left_cap':(190,70,230),'left_foot':(70,210,190)}
 colors_arr=np.ones((128,128,3),np.uint8)*255
 for name,mask in masks.items():colors_arr[mask&visible]=colors[name]
 ownership_png=Image.fromarray(colors_arr).crop((43,76,87,107)).resize((704,496),Image.Resampling.NEAREST)
 ownership_png.save(OUT/'source-owner-legs-16x.png')
 # 固定源工具邻域的实测归属；邻域矩形只是诊断，人工仍需看源像素结构。
 tool_records={}
 for name,roi in {'gun_adjacent':[46,79,54,96],'claw_adjacent':[76,84,84,94]}.items():
  x0,y0,x1,y1=roi
  tool_records[name]={'roi':roi,'visible_ownership':{k:int((m[y0:y1,x0:x1]&visible[y0:y1,x0:x1]).sum()) for k,m in masks.items()},
   'movable_source_coordinates':[[x,y,k] for k,m in masks.items() if k!='body' for y in range(y0,y1) for x in range(x0,x1) if m[y,x] and visible[y,x]]}

 catalog=load(files['output/pilot_catalog_v013.json']);clip=catalog['clips'][0]
 assert sha(files['output/pilot_catalog_v013.json'])=='b20ac1a75f5eefef42deee8dfbac324418967ab6e76a8c4d5af65e9f10ce348f'
 assert catalog['rig_script_sha256']==sha(files['pilot_rig.gd']) and catalog['rig_spec_sha256']==sha(files['pilot_rigs.json'])
 assert (clip['frame_count'],clip['fps'],clip['loop'])==(8,8,True) and clip['unit']=='enemy_patrol'
 atlas=arr(files[path(clip['atlas'])]);assert atlas.shape==(128,1024,4)
 assert sha(files[path(clip['atlas'])])==clip['atlas_sha256']
 tres=files['output/enemy_patrol_pilot_v013.tres'].decode('utf-8-sig')
 assert '[ext_resource' not in tres
 raw_match=re.search(r'"data": PackedByteArray\((.*?)\)',tres,re.S)
 embedded=np.fromstring(raw_match.group(1),sep=',',dtype=np.uint8).reshape(128,1024,4)
 assert np.array_equal(embedded,atlas)
 assert re.findall(r'region = Rect2\(([^)]+)\)',tres)==[f'{i*128}, 0, 128, 128' for i in range(8)]
 assert '"name": &"move_down_right"' in tres and '"speed": 8.0' in tres and '"loop": 1' in tres
 assert re.findall(r'"duration": ([0-9.]+)',tres)==['1.0']*8
 frames=[];endpoints=[];cpu=[]
 for i,pose in enumerate(clip['poses']):
  png=files[f'output/enemy_patrol/move_down_right/f{i:02d}.png'];a=arr(png)
  assert sha(png)==clip['frame_hashes'][i] and a.shape==(128,128,4)
  assert np.array_equal(a,atlas[:,i*128:(i+1)*128]) and set(np.unique(a[:,:,3]))=={0,255}
  assert not np.any(a[[0,-1],:,3]) and not np.any(a[:,[0,-1],3])
  frames.append({'frame':i,'sha256':sha(png),'visible_pixels':int((a[:,:,3]>0).sum()),'atlas_and_embedded_tres_rgba_difference':0})
  for side in ['left','right']:
   support=pose['supports'][side]
   for segment,startkey,endkey in [('thigh','hip','knee'),('shin','knee','ankle')]:
    name=side+'_'+segment;t=pose['part_transforms'][name];d=defs[name]
    basis=np.array([t['basis_x'],t['basis_y']]).T
    actual=np.array(t['position'])+basis@(np.array(d['end'])-np.array(d['pivot']))
    error=float(np.linalg.norm(actual-np.array(support[endkey])))
    assert error<1e-5 and t['position']==support[startkey]
    rest=np.array(d['end'])-np.array(d['pivot']);normal=np.array([-rest[1],rest[0]])/np.linalg.norm(rest)
    normal_scale=float(np.linalg.norm(basis@normal));axis_scale=float(np.linalg.norm(basis@rest)/np.linalg.norm(rest))
    assert abs(normal_scale-1)<2e-6
    endpoints.append({'frame':i,'part':name,'actual_basis_endpoint_error':error,'axis_scale':axis_scale,'normal_scale':normal_scale})
   for suffix,key in [('cap','knee'),('foot','ankle')]:
    t=pose['part_transforms'][side+'_'+suffix]
    assert t['basis_x']==[1,0] and t['basis_y']==[0,1] and t['position']==support[key]
   assert support['support']==unit['phases'][i][side]['support']
   if support['support']:assert support['sole']==support['ground']
  # 源RGBA+固定mask+已登记实际basis，独立CPU逆映射得到可见图。
  out=np.zeros((128,128,4),np.uint8);out[:,:,:3]=255
  sampled={}
  order=sorted(['body']+list(defs),key=lambda k:5 if k=='body' else defs[k]['z'])
  for name in order:
   t=pose['part_transforms'][name];basis=np.array([t['basis_x'],t['basis_y']]).T;inv=np.linalg.inv(basis)
   pivot=np.array([0,0] if name=='body' else defs[name]['pivot']);position=np.array(t['position'])
   for y in range(128):
    for x in range(128):
     sample=inv@(np.array([x+.5,y+.5])-position)+pivot
     sx,sy=math.floor(sample[0]),math.floor(sample[1])
     if 0<=sx<128 and 0<=sy<128 and masks[name][sy,sx] and source[sy,sx,3]:
      out[y,x]=source[sy,sx];sampled[(x,y)]={'part':name,'source_float':sample.tolist(),'floor_source':[sx,sy]}
  delta_records=[]
  for y,x in zip(*np.where(np.any(out!=a,axis=2))):
   rec=sampled[(x,y)].copy();rec['xy']=[int(x),int(y)];rec['cpu_rgba']=out[y,x].tolist();rec['png_rgba']=a[y,x].tolist()
   fx,fy=rec['source_float'];cxs=[round(fx)-1,round(fx)] if abs(fx-round(fx))<1e-5 else [math.floor(fx)]
   cys=[round(fy)-1,round(fy)] if abs(fy-round(fy))<1e-5 else [math.floor(fy)]
   rec['matching_integer_boundary_samples']=[[int(sx),int(sy)] for sy in cys for sx in cxs
     if 0<=sx<128 and 0<=sy<128 and masks[rec['part']][sy,sx] and np.array_equal(source[sy,sx],a[y,x])]
   assert rec['matching_integer_boundary_samples'],rec
   delta_records.append(rec)
  cpu.append({'frame':i,'ideal_cpu_full_rgba_changed_pixels':int(np.any(out!=a,axis=2).sum()),
    'ideal_cpu_coverage_changed_pixels':int((out[:,:,3]!=a[:,:,3]).sum()),'difference_records':delta_records})

 author_gpu=load(files['qa/pilot_gpu_roundtrip.json']);author_runtime=load(files['qa/pilot_runtime.json'])
 assert len(author_gpu['records'])==16 and all(r['live_rig_vs_png_differing_channels']==r['tres_vs_png_differing_channels']==0 for r in author_gpu['records'])
 assert {r['background'] for r in author_gpu['records']}=={'white','black'}
 assert len({(r['frame'],r['background']) for r in author_gpu['records']})==16
 assert author_gpu['catalog_sha256']==author_runtime['catalog_sha256']==sha(files['output/pilot_catalog_v013.json'])
 assert len(author_runtime['seen_frames'])==4 and len(author_runtime['direction_switches'])==8
 for seen in author_runtime['seen_frames'].values():assert seen==list(range(8))
 receipt={'status':'FIXED_SOURCE_MASK_EXPORT_BINDING_PASS','zip_sha256':EXPECTED,'zip_bytes':ZIP.stat().st_size,
  'entries':53,'manifest_payloads':52,'fixed_source_sha256':unit['source_sha256'],'catalog_sha256':sha(files['output/pilot_catalog_v013.json']),
  'fixed_snapshot_manifest_files_identical':52,'s002_direction_pngs_identical':8,'v008_down_atlas_and_phase_identical':True,
  'source_unique_ownership_counts':ownership,'opaque_source_pixels':int(visible.sum()),'source_overlap_or_unowned_pixels':0,
  'tool_neighbor_diagnostics':tool_records,'frame_records':frames,'actual_endpoints':endpoints,
  'ideal_cpu_render_differences':cpu,'author_gpu_records':author_gpu,'author_runtime_record':author_runtime,
  'author_gpu_scope_limit':'16 numerical comparison records catalog-bound; no16 individual roundtrip images in fixed package. Not a TA GPU rerun.',
  'cold_project_initial_no_godot_cache':True,'ta_gpu_rerun':False,
  'acceptance_limit':'Integrity and source registration only; no extension of visual/animation acceptance.'}
 (OUT/'binding.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:receipt[k] for k in ['status','zip_bytes','entries','manifest_payloads','source_unique_ownership_counts','tool_neighbor_diagnostics','ideal_cpu_render_differences']},ensure_ascii=False,indent=2))
