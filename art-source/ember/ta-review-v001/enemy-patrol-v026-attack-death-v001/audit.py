"""独立核对固定源、实际分区、全98姿态、112输出格及落地边界。"""
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
P=OUT/'technical-package';OLD=OUT.with_name('enemy-patrol-v025-idle-hit-v001')
rig=js(P/'rig.json');cat=js(P/'output/catalog.json');cold=js(OUT/'technical-minimal-cold-load.json');receipt=js(P/'SOURCE_RECEIPT.json')
assert cold['status']=='PASS' and cold['frames']==112 and cat['canvas']==[128,128] and cat['root']==[64,104]
assert sha(P/'rig.json')==cat['rig_sha256'] and sha(P/cat['tres'].removeprefix('res://'))==cat['tres_sha256']
prior=ROOT/'art-source/ember/deliveries/enemy_patrol_idle_hit_v025_v001_2026-10-07.zip'
assert sha(prior)=='677b7b0747267f1c3ce36216d838696fb617184007c562bcc63e30d9e1380e0d'
with ZipFile(prior) as z:
 for n,h in receipt['source_png_hashes'].items():assert sha(P/'source'/n)==h and (P/'source'/n).read_bytes()==z.read('source/'+n)
 for n in ['directions_rig.json','directions_rig.gd','profile_rig.json','profile_rig.gd','pilot_rigs.json','pilot_rig.gd']:
  assert (P/n).read_bytes()==z.read(n),(n,'baseline rig changed')
cfgs=js(P/'directions_rig.json')['configs'];profiles=js(P/'profile_rig.json')['configs'];pilot=next(c for c in js(P/'pilot_rigs.json')['units'] if c['unit']=='enemy_patrol')
out={'status':'PASS','sources_byte_exact_to_approved_P25':list(receipt['source_png_hashes']),'ownership':[],'transfers':[],'bind':[],'socket_sources':[],'poses':[],'clips':[]}
def pm(poly):return np.array([[inside(x+.5,y+.5,poly)for x in range(128)]for y in range(128)],bool)
def mask(base,d,p):return np.array(Image.open(base/f'technical-runtime-mask-{d}-{p}.png').convert('RGB'))[:,:,0]>0
def mat(t):return np.array([[t['basis_x'][0],t['basis_y'][0],t['position'][0]],[t['basis_x'][1],t['basis_y'][1],t['position'][1]],[0,0,1]],float)
def rec(m):return {'position':m[:2,2].tolist(),'basis_x':m[:2,0].tolist(),'basis_y':m[:2,1].tolist()}
def transform(angle,pos):
 c,s=math.cos(angle),math.sin(angle);return np.array([[c,-s,pos[0]],[s,c,pos[1]],[0,0,1]],float)
for d,s in rig['configs'].items():
 kind=s['base'];cfg=profiles[d] if kind=='profile' else pilot if kind=='pilot' else cfgs[d];combat=rig['combat'][d]
 parts=[{'id':'body','pivot':[0,0],'z':10 if kind=='profile' else 5,'source_kind':'canonical'}]+cfg['parts']
 before={p['id']:mask(OLD,d,p['id']) for p in parts};expected={k:v.copy() for k,v in before.items()}
 for x,y in combat['ownership_transfers']:
  owners=[pid for pid,m in before.items() if m[y,x]]
  for pid in expected:expected[pid][y,x]=pid=='body'
  out['transfers'].append({'direction':d,'xy':[x,y],'before':owners})
 for arm in combat['arms']:
  a=pm(arm['polygon'])&expected['body'];expected[arm['id']]=a;expected['body']&=~a
  parts.append(dict(arm,z=12,source_kind='canonical'))
 textures={};actual={};runtime=next(r for r in cold['rig_checks'] if r['direction']==d)
 for p in parts:
  pid=p['id'];actual[pid]=mask(OUT,d,pid);assert np.array_equal(expected[pid],actual[pid]),(d,pid,'ownership')
  sk=p.get('source_kind','canonical');src=arr(OUT/f'technical-runtime-source-{d}-{pid}.png')
  ref=arr(OLD/f'technical-runtime-source-{d}-{pid if pid not in ["gun","claw"] else "body"}.png')
  assert np.array_equal(src,ref),(d,pid,'actual source RGB')
  textures[sk]=src
  mr=next(m for m in runtime['masks'] if m['id']==pid)
  assert mr['pivot']==p['pivot'] and mr['z']==p['z'] and not mr['centered'],(d,pid,'node registration')
 for sk,src in textures.items():
  mult=sum(actual[p['id']].astype(int)for p in parts if p.get('source_kind','canonical')==sk);opaque=src[:,:,3]>0
  miss=int(np.sum(opaque&(mult==0)));dup=int(np.sum(opaque&(mult>1)));assert not miss and not dup,(d,sk,'incomplete source')
  out['ownership'].append({'direction':d,'source_kind':sk,'unowned':miss,'multiple':dup})
 bind=np.full((128,128,4),255,np.uint8);bind[:,:,3]=0
 for _,p in sorted(enumerate(parts),key=lambda q:(q[1]['z'],q[0])):
  src=textures[p.get('source_kind','canonical')];v=actual[p['id']]&(src[:,:,3]>0);bind[v]=src[v]
 neutral=arr(P/s['source'].removeprefix('res://'));assert np.array_equal(bind,neutral),(d,'bind')
 out['bind'].append({'direction':d,'rgba_difference':0,'actual_masks':len(parts)})
 for arm in combat['arms']:
  x,y,w,h=arm['socket_uv'];uv=[[x+.001,y+.001],[x+w-.001,y+.001],[x+w-.001,y+h-.001],[x+.001,y+h-.001]]
  lr=next(r for r in runtime['links'] if r['id']==arm['id']);assert equal(uv,lr['uv']) and lr['z']==-10
  src=textures['canonical'];out['socket_sources'].append({'direction':d,'arm':arm['id'],'uv_rect':[x,y,w,h],'rgba':src[y:y+h,x:x+w].tolist()})
 for action in ['attack','death']:
  values=rig['actions'][action];clip=next(c for c in cat['clips'] if c['action']==action+'_'+d)
  for i in range(values['frame_count']):
   body=values['body_y'][i];delta=[0,body];kd=[0,round_godot(body*.6)];local={'body':transform(0,delta)}
   for p in cfg['parts']:
    pid=p['id'];pivot=p['pivot']
    if pid.endswith('_thigh'):local[pid]=mat(segment(p,add(pivot,delta),add(p['end'],kd)))
    elif pid.endswith('_shin'):local[pid]=mat(segment(p,add(pivot,kd),p['end']))
    else:local[pid]=transform(0,add(pivot,kd)if pid.endswith('_cap')else pivot)
   links={}
   for arm in combat['arms']:
    travel=[round_godot(v*values['raise_arm'][i])for v in arm['raise_vector']]if arm['id']=='gun'else[0,0]
    angle=math.radians(values['fold'][i]*arm['fold_sign'])if action=='death' or arm['id']=='claw'else 0
    pos=add(add(arm['pivot'],delta),travel);local[arm['id']]=transform(angle,pos)
    start=np.array(add(arm['socket_start'],delta),float);end=np.array(pos,float);axis=end-start;length=np.linalg.norm(axis)
    normal=np.array([-axis[1],axis[0]])/length*arm['socket_width']*.5 if length else np.zeros(2)
    links[arm['id']]=[start-normal,start+normal,end+normal,end-normal]
   world=np.eye(3)
   if action=='death':
    sign=combat['fall_sign'];origin=[64+[0,0,0,2,4,6,6,6][i]*sign,combat['fall_origin_y_keys'][i]]
    world=transform(math.radians(values['roll'][i]*sign),origin)@transform(0,[-64,-80-body])
   tr={pid:rec(world@m)for pid,m in local.items()};polys={pid:[(world@np.append(v,1))[:2].tolist()for v in verts]for pid,verts in links.items()}
   pose=clip['poses'][i];run=next(p for p in runtime['poses']if p['pose']['action']==action and p['pose']['frame']==i)
   # Godot Vector2 为 float32，多次全身矩阵组合后约 2e-5 的误差并非像素位移。
   # 采用 1e-4 像素上限，并保留每帧实际最大误差，实际读回与目录仍用原严格比较。
   err=max([float(np.max(np.abs(mat(t)-mat(pose['part_transforms'][pid]))))for pid,t in tr.items()]+[float(np.max(np.abs(np.array(v)-pose['socket_polygons'][pid])))for pid,v in polys.items()])
   assert equal(tr,pose['part_transforms'],1e-4) and equal(polys,pose['socket_polygons'],1e-4) and equal(pose,run['pose']),(d,action,i,'math/runtime')
   assert equal(run['actual_material_powers'],[values['power'][i]])
   out['poses'].append({'direction':d,'action':action,'frame':i,'independent_math_actual_rig_catalog':True,'max_numeric_error':err})
down=ROOT/'art-source/ember/deliveries/enemy_sequences_v012_2026-10-06.zip';assert sha(down)==receipt['down_zip_sha256']
with ZipFile(down) as z:
 for c in cat['clips']:
  action=c['action'].split('_')[0];n=6 if action=='attack'else 8;p=P/c['atlas'].removeprefix('res://');atlas=arr(p);frames=[];records=[]
  assert sha(p)==c['atlas_sha256'] and c['fps']==10 and not c['loop'] and c['frame_count']==n and atlas.shape==(128,128*n,4)
  for i in range(n):
   fp=p.with_suffix('')/f'f{i:02d}.png';im=Image.open(fp).convert('RGBA');v=np.array(im);frames.append(v)
   assert sha(fp)==c['frame_hashes'][i]and np.array_equal(v,atlas[:,i*128:(i+1)*128])and set(np.unique(v[:,:,3]))<=set([0,255])
   bbox=im.getchannel('A').getbbox();records.append({'frame':i,'alpha_bbox':bbox,'bottom_pixels':int(np.sum(v[bbox[3]-1,:,3]>0))})
   if c['direction']=='down':assert fp.read_bytes()==z.read(fp.relative_to(P).as_posix())
  if c['direction']=='down':assert p.read_bytes()==z.read(p.relative_to(P).as_posix())
  else:
   assert np.array_equal(frames[0],arr(P/rig['configs'][c['direction']]['source'].removeprefix('res://')))
   assert np.array_equal(frames[0]if action=='attack'else frames[-2],frames[-1])
   if action=='death':assert records[-1]['alpha_bbox'][3]==104
  out['clips'].append({'action':c['action'],'frames':records,'preserved_down':c['direction']=='down'})
out['final_contact_pixels']=[]
for d in rig['configs']:
 c=next(c for c in cat['clips']if c['action']=='death_'+d);pose=c['poses'][7];runtime=next(r for r in cold['rig_checks']if r['direction']==d)
 im=arr(P/f'output/enemy_patrol/death_{d}/f07.png');rows=[]
 for x in np.flatnonzero(im[103,:,3]):
  matches=[]
  for node in runtime['masks']:
   pid=node['id'];matrix=mat(pose['part_transforms'][pid])
   # 屈膝后的投影短杆可降为零面积；其退化几何没有可见覆盖，不求逆。
   if abs(np.linalg.det(matrix))<1e-10:continue
   uv=np.linalg.inv(matrix)@np.array([x+.5,103.5,1]);uv[:2]+=node['pivot'];sx,sy=np.floor(uv[:2]).astype(int)
   if 0<=sx<128 and 0<=sy<128 and mask(OUT,d,pid)[sy,sx]:
    pixel=arr(OUT/f'technical-runtime-source-{d}-{pid}.png')[sy,sx]
    if pixel[3] and np.array_equal(pixel,im[103,x]):matches.append({'part':pid,'uv':[int(sx),int(sy)],'rgba':pixel.tolist()})
  rows.append({'x':int(x),'y':103,'actual_rgba':im[103,x].tolist(),'source_matches':matches})
 out['final_contact_pixels'].append({'direction':d,'pixels':rows})
out['totals']={'poses':len(out['poses']),'actual_masks':sum(r['actual_masks']for r in out['bind']),'frames':sum(len(c['frames'])for c in out['clips']),'max_numeric_error':max(p['max_numeric_error']for p in out['poses'])}
(OUT/'technical-integrity.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(out['totals']);print(out['transfers'])
