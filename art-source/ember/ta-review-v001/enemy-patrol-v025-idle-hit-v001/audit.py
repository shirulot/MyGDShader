"""P25独立来源、实际分区、轻动作矩阵与CPU采样核验；保留采样残差。"""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,json,math,numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];P=OUT/'technical-package'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
js=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
arr=lambda p:np.array(Image.open(p).convert('RGBA'))
helper=OUT.with_name('enemy-patrol-v020-four-moves-v002')/'technical-audit.py'
exec(compile(helper.read_text(encoding='utf-8').split('manifest=load(')[0],str(helper),'exec'))
P=OUT/'technical-package'
rig=js(P/'rig.json');cat=js(P/'output/catalog.json');receipt=js(P/'SOURCE_RECEIPT.json');cold=js(OUT/'technical-minimal-cold-load.json')
assert cold['status']=='PASS' and cold['frames']==64
assert sha(P/'rig.json')==cat['rig_sha256'] and sha(P/cat['tres'].removeprefix('res://'))==cat['tres_sha256']
assert cat['canvas']==[128,128] and cat['root']==[64,104]
for n,h in receipt['source_png_hashes'].items():assert sha(P/'source'/n)==h
deliveries=ROOT/'art-source/ember/deliveries'
names={'down_zip_sha256':'enemy_sequences_v012_2026-10-06.zip','se_zip_sha256':'enemy_eight_directions_v013_pilot_patrol_v001_2026-10-06.zip','four_move_zip_sha256':'enemy_patrol_four_moves_v020_v002_2026-10-07.zip','profile_move_zip_sha256':'enemy_patrol_profile_moves_v021_v003_2026-10-07.zip','profile_calibration_zip_sha256':'enemy_patrol_profile_calibration_v021_c002_v003_2026-10-07.zip'}
prior={}
for key,name in names.items():
 path=deliveries/name;assert sha(path)==receipt[key];prior[key]=ZipFile(path)
def unique(z,suffix):
 names=[n for n in z.namelist() if n==suffix or n.endswith('/'+suffix)]
 assert len(names)==1,(suffix,names)
 return z.read(names[0])
old20=json.loads(unique(prior['four_move_zip_sha256'],'rig.json'))
old21=json.loads(unique(prior['profile_move_zip_sha256'],'rig.json'))
directions=js(P/'directions_rig.json')['configs'];profiles=js(P/'profile_rig.json')['configs']
pilot=next(x for x in js(P/'pilot_rigs.json')['units'] if x['unit']=='enemy_patrol')
oldpilot=next(x for x in json.loads(unique(prior['se_zip_sha256'],'pilot_rigs.json'))['units'] if x['unit']=='enemy_patrol')
models={};summary={'status':'PASS','sources':[],'ownership':[],'connectors':[],'poses':[],'cpu_residuals':[],'visible_sole_probes':[],'preserved':[]}
yy,xx=np.indices((128,128));X,Y=xx+.5,yy+.5
def pm(poly):
 return np.array([[inside(x+.5,y+.5,poly) for x in range(128)] for y in range(128)],bool)
for d,s in rig['configs'].items():
 kind=s['base'];c=profiles[d] if kind=='profile' else (pilot if kind=='pilot' else directions[d])
 old=old21['configs'][d] if kind=='profile' else (oldpilot if kind=='pilot' else old20['configs'][d])
 # 继承的实际几何分区与腿登记保持；路径字段单独按字节来源绑定。
 for key in ['parts','legs','protected_body_polygons','occluded_original_polygons','remove_polygons']:
  assert c.get(key)==old.get(key),(d,key)
 if kind=='profile':
  textures={k:arr(P/c[field].removeprefix('res://')) for k,field in [('canonical','body_source'),('near','near_source'),('far','far_source')]}
  for partkind in ['body','near','far']:
   assert (P/f'source/c002_{d}_{partkind}.png').read_bytes()==unique(prior['profile_calibration_zip_sha256'],f'output/{d}_{partkind}.png')
  expected=unique(prior['profile_calibration_zip_sha256'],f'output/neutral_{d}.png')
 else:
  textures={'canonical':arr(P/c['source'].removeprefix('res://'))}
  z=prior['se_zip_sha256'] if kind=='pilot' else prior['four_move_zip_sha256']
  expected=unique(z,f'output/enemy_patrol/neutral_{d}.png') if kind!='pilot' else unique(z,'output/enemy_patrol/rig_neutral_down_right.png')
 assert (P/s['source'].removeprefix('res://')).read_bytes()==expected,(d,'neutral/source')
 excluded=[p['polygon'] for p in c['parts'] if kind!='profile' or p['source_kind']=='canonical']+c.get('occluded_original_polygons',[])+c.get('remove_polygons',[])
 parts=[{'id':'body','pivot':[0,0],'polygon':[],'exclude':excluded,'z':10 if kind=='profile' else 5,'source_kind':'canonical'}]+c['parts']
 masks={};bind=np.full((128,128,4),255,np.uint8);bind[:,:,3]=0
 coldrec=next(r for r in cold['rig_cpu_checks'] if r['direction']==d)
 for part in parts:
  pid=part['id'];sk=part.get('source_kind','canonical');src=textures[sk]
  mask=pm(part['polygon']) if part['polygon'] else np.ones((128,128),bool)
  for polygon in part.get('overlap_polygons',[]):mask|=pm(polygon)
  for polygon in part.get('exclude',[]):mask&=~pm(polygon)
  if sk=='canonical':
   for polygon in c.get('protected_body_polygons',[]):mask[pm(polygon)]=pid=='body'
  # Godot R8 蒙版存为 RGB PNG，着色器读取 r；不能把 RGB 三通道当二维布尔蒙版。
  actualmask=np.array(Image.open(OUT/f'technical-runtime-mask-{d}-{pid}.png').convert('RGB'))[:,:,0]>0
  assert np.array_equal(mask,actualmask),(d,pid,'actual mask')
  assert np.array_equal(src,arr(OUT/f'technical-runtime-source-{d}-{pid}.png')),(d,pid,'actual texture')
  masks[pid]=mask
  if part.get('end') is not None:
   points=np.argwhere(mask&(src[:,:,3]>0));colors=src[mask&(src[:,:,3]>0),:3]
   summary['connectors'].append({'direction':d,'id':pid,'pixels':len(points),'rgb_max':colors.max(axis=0).tolist() if len(points) else [],'source_pixels':[{'xy':[int(x),int(y)],'rgba':src[y,x].tolist()} for y,x in points]})
 for sk,src in textures.items():
  mult=sum(masks[p['id']].astype(int) for p in parts if p.get('source_kind','canonical')==sk)
  opaque=src[:,:,3]>0
  summary['ownership'].append({'direction':d,'source_kind':sk,'unowned':int(np.sum(opaque&(mult==0))),'multiple':int(np.sum(opaque&(mult>1)))})
 for _,part in sorted(enumerate(parts),key=lambda q:(q[1]['z'],q[0])):
  src=textures[part.get('source_kind','canonical')];visible=masks[part['id']]&(src[:,:,3]>0);bind[visible]=src[visible]
 assert np.array_equal(bind,arr(P/s['source'].removeprefix('res://'))),(d,'independent bind')
 summary['sources'].append({'direction':d,'approved_neutral_byte_exact':True,'actual_masks_and_textures':len(parts),'independent_bind_rgba':0})
 for action in ['idle','hit']:
  clip=next(x for x in cat['clips'] if x['action']==action+'_'+d)
  for i in range(4):
   delta=rig['actions'][action]['body'][i];kd=[round_godot(v*.5) for v in delta]
   tr={'body':{'position':delta,'basis_x':[1,0],'basis_y':[0,1]}}
   for part in c['parts']:
    pid=part['id'];pivot=part['pivot']
    if pid.endswith('_thigh'):tr[pid]=segment(part,add(pivot,delta),add(part['end'],kd))
    elif pid.endswith('_shin'):tr[pid]=segment(part,add(pivot,kd),part['end'])
    else:tr[pid]={'position':add(pivot,kd) if pid.endswith('_cap') else pivot,'basis_x':[1,0],'basis_y':[0,1]}
   pose=clip['poses'][i];runtime=next(p for p in coldrec['poses'] if p['action']==action and p['frame']==i)
   assert equal(pose,runtime) and equal(pose['part_transforms'],tr),(d,action,i,'actual pose')
   reconstructed=np.full((128,128,4),255,np.uint8);reconstructed[:,:,3]=0;owner=np.full((128,128),-1,int)
   for index,part in sorted(enumerate(parts),key=lambda q:(q[1]['z'],q[0])):
    t=tr[part['id']];matrix=np.array([t['basis_x'],t['basis_y']]).T
    if abs(np.linalg.det(matrix))<1e-10:continue
    uv=np.linalg.inv(matrix)@np.array([X-t['position'][0],Y-t['position'][1]]).reshape(2,-1)
    uv+=np.array(part['pivot'])[:,None];sx=np.floor(uv[0]).astype(int).reshape(128,128);sy=np.floor(uv[1]).astype(int).reshape(128,128)
    valid=(sx>=0)&(sx<128)&(sy>=0)&(sy<128);sx=np.clip(sx,0,127);sy=np.clip(sy,0,127)
    src=textures[part.get('source_kind','canonical')];valid&=masks[part['id']][sy,sx]&(src[sy,sx,3]>0)
    reconstructed[valid]=src[sy[valid],sx[valid]];owner[valid]=index
   final=arr(P/f'output/enemy_patrol/{action}_{d}/f{i:02d}.png');dif=np.any(reconstructed!=final,axis=2)
   points=[{'xy':[int(x),int(y)],'cpu':reconstructed[y,x].tolist(),'actual':final[y,x].tolist()} for y,x in np.argwhere(dif)]
   summary['cpu_residuals'].append({'direction':d,'action':action,'frame':i,'rgba':len(points),'alpha':int(np.sum(reconstructed[:,:,3]!=final[:,:,3])),'points':points})
   for side,leg in c['legs'].items():
    sole=add(leg['ankle'],leg['sole_offset']);px=int(sole[0]);py=int(sole[1])-1;pid=side+'_foot';part=next(p for p in parts if p['id']==pid);src=textures[part.get('source_kind','canonical')]
    onfoot=bool(masks[pid][py,px] and src[py,px,3]);visible=onfoot and owner[py,px]==parts.index(part)
    summary['visible_sole_probes'].append({'direction':d,'action':action,'frame':i,'side':side,'xy':[px,py],'source_is_foot':onfoot,'visible_actual_owner':bool(visible),'foot_transform_fixed':True})
   summary['poses'].append({'direction':d,'action':action,'frame':i,'independent_math_actual_rig_catalog':True})
for clip in cat['clips']:
 p=P/clip['atlas'].removeprefix('res://');a=arr(p);frames=[]
 assert sha(p)==clip['atlas_sha256'] and a.shape==(128,512,4)
 for i in range(4):
  f=p.with_suffix('')/f'f{i:02d}.png';v=arr(f);frames.append(v)
  assert sha(f)==clip['frame_hashes'][i] and np.array_equal(v,a[:,i*128:(i+1)*128]) and set(np.unique(v[:,:,3]))<=set([0,255])
  if clip['direction']=='down':assert f.read_bytes()==unique(prior['down_zip_sha256'],f.relative_to(P).as_posix().removeprefix('output/'));summary['preserved'].append(f.relative_to(P).as_posix())
 if clip['direction']=='down':assert p.read_bytes()==unique(prior['down_zip_sha256'],p.relative_to(P).as_posix().removeprefix('output/'));summary['preserved'].append(p.relative_to(P).as_posix())
 else:assert np.array_equal(frames[0],frames[2 if clip['action'].startswith('idle') else 3])
summary['totals']={'poses':len(summary['poses']),'actual_masks':sum(s['actual_masks_and_textures'] for s in summary['sources']),'cpu_rgba':sum(s['rgba'] for s in summary['cpu_residuals']),'cpu_alpha':sum(s['alpha'] for s in summary['cpu_residuals']),'sole_probes':len(summary['visible_sole_probes'])}
(OUT/'technical-integrity.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary['totals']));print('Ownership:',summary['ownership']);print('Connector RGB maxima:',[(r['direction'],r['id'],r['rgb_max']) for r in summary['connectors']])
