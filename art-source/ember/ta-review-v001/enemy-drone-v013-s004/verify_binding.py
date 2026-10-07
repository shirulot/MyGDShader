"""无人机 s004 固定包静态只读复核；不运行引擎或生产导出器。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from collections import Counter
import json, hashlib, math
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
WORK = ROOT/'art-source/ember/enemy-eight-directions-v013'
ACTIVE = WORK/'static_preflight_s004_drone'
DELIVERY = ROOT/'art-source/ember/deliveries'
ZIP = DELIVERY/'enemy_drone_seven_directions_v013_s004_2026-10-06.zip'
EXPECTED = '3a6dc8a5ab9c16dc5e71d083568768ff3cabefae2675d5385e552149acb79342'

def sha(data): return hashlib.sha256(data).hexdigest()
def js(data): return json.loads(data.decode('utf-8-sig'))
def im(data): return Image.open(BytesIO(data)).convert('RGBA')
def rgba(data): return np.array(im(data))
def bbox(mask):
    y,x=np.where(mask)
    return [int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1] if len(x) else None

assert sha(ZIP.read_bytes()) == EXPECTED
with ZipFile(ZIP) as z:
    assert z.testzip() is None
    files = {n:z.read(n) for n in z.namelist()}
manifest=js(files['manifest.json'])['files']
assert len(files)==40 and len(manifest)==39 and set(manifest)==set(files)-{'manifest.json'}
for n,r in manifest.items():
    assert sha(files[n])==r['sha256'] and len(files[n])==r['bytes']
assert all((ACTIVE/n).read_bytes()==data for n,data in files.items())
provenance=[]
for n,s in js(files['source_provenance.json']).items():
    packaged='provenance/'+n
    assert sha(files[packaged])==s
    # 包内 provenance/ 的脚本和登记原件位于制作工程根。
    original=WORK/n
    assert original.is_file() and original.read_bytes()==files[packaged]
    provenance.append({'path':packaged,'sha256':s,'original_relative':str(original.relative_to(ROOT)).replace('\\','/'),'original_byte_same':True})

copies=[]
for base_name,mapping in [
 ('enemy_calibration_v013_c002_2026-10-06.zip',{'neutral_down.png':'enemy_scout_drone/approved_down.png','generated_front.png':'enemy_scout_drone/generated_front.png'}),
 ('enemy_drone_diagonal_calibration_v013_c003_2026-10-06.zip',{'neutral_down_left.png':'neutral_down_left.png','neutral_down_right.png':'neutral_down_right.png'})]:
    base=DELIVERY/base_name
    with ZipFile(base) as z:
        for target,old in mapping.items():
            assert files[target]==z.read(old)
            copies.append({'file':target,'baseline_zip':base_name,'baseline_zip_sha256':sha(base.read_bytes()),'baseline_member':old,'sha256':sha(files[target]),'byte_same':True})

reg=js(files['provenance/static_registration_drone_s004.json'])
cat=js(files['catalog.json'])
qa={r['key']:r for r in js(files['native_static_qa.json'])}
assert cat['registration_sha256']==sha(files['provenance/static_registration_drone_s004.json'])
assert len(reg['entries'])==len(cat['entries'])==9 and reg['columns']==cat['columns']==3
pre_reg=js(files['provenance/drone_profile_preassembly_registration.json'])
pre_cat=js(files['provenance/source/registered/drone_profile_preassembly_v001/catalog.json'])
assert pre_cat['registration_sha256']==sha(files['provenance/drone_profile_preassembly_registration.json'])
assert len(pre_reg['entries'])==len(pre_cat['entries'])==2
pre_bind=[]
for e,c in zip(pre_reg['entries'],pre_cat['entries']):
    assert e['key']==c['key'] and e['scale']==26/244*724/887
    assert sha(files['provenance/'+e['source'].removeprefix('res://')])==e['source_sha256']
    name='provenance/source/registered/drone_profile_preassembly_v001/'+e['key']+'.png'
    assert c['sha256']==sha(files[name])
    pre_bind.append({'key':e['key'],'source':e['source'],'source_sha256':e['source_sha256'],'registered_png_sha256':sha(files[name]),'isotropic_scale':e['scale'],'source_rect':e['source_rect'],'source_anchor':e['source_anchor'],'target_anchor':e['target_anchor'],'catalog_registration_hash_same':True})
records=[]
diagnostics=[]
for e,c in zip(reg['entries'],cat['entries']):
    key=e['key']; target=rgba(files[key+'.png'])
    assert key==c['key'] and target.shape==(128,128,4)
    assert sha(files[key+'.png'])==c['sha256']==qa[key]['sha256']
    assert set(np.unique(target[:,:,3]))=={0,255}
    assert bbox(target[:,:,3]>0)==qa[key]['bounds']
    r={'key':key,'sha256':sha(files[key+'.png']),'bounds':bbox(target[:,:,3]>0),'alpha_counts':{str(k):int(v) for k,v in Counter(target[:,:,3].ravel()).items()},'transparent_nonzero_rgb_pixels':int(((target[:,:,3]==0)&np.any(target[:,:,:3]!=0,axis=2)).sum())}
    if 'scale' not in e:
        original=WORK/e['copy_path'].removeprefix('res://')
        assert original.read_bytes()==files[key+'.png']
        r['copy_path_byte_same']=True
    else:
        source_name=e['source'].removeprefix('res://')
        assert sha(files['provenance/'+source_name])==e['source_sha256']
        for field in ['source_rect','source_anchor','target_anchor','scale']:
            assert np.max(np.abs(np.array(c['registration'][field])-np.array(e[field])))<1e-12
        source=rgba(files['provenance/'+source_name])
        if 'assembly_parts' in e:
            assert e['scale']==1 and e['source_anchor']==[0,0] and e['source_rect']==[0,0,128,128]
            part=e['assembly_parts'][0]
            assert len(e['assembly_parts'])==1 and len(part['rows'])==16
            mask=np.zeros((128,128),dtype=bool)
            for y,x0,x1 in part['rows']:
                assert all(int(v)==v for v in [y,x0,x1]) and not mask[y,x0:x1].any()
                mask[y,x0:x1]=True # Godot range 起点包含、终点不包含。
            visible=source[:,:,3]>=128
            body=visible&~mask; pod=visible&mask
            predicted=np.full((128,128,4),255,dtype=np.uint8); predicted[:,:,3]=0
            owner=np.full((128,128),-1,dtype=int)
            overlap=[]; clipped=[]
            whole=np.array(e['target_anchor'],dtype=int); offset=np.array(part['offset'],dtype=int)
            assert list(whole)==([2,2] if key=='neutral_left' else [-1,2])
            assert list(offset)==([-3,-4] if key=='neutral_left' else [3,-4])
            for layer,select,shift in [(0,body,whole),(1,pod,whole+offset)]:
                for sy,sx in zip(*np.where(select)):
                    dx,dy=np.array([sx,sy])+shift
                    if not (0<=dx<128 and 0<=dy<128): clipped.append([int(sx),int(sy),layer]); continue
                    if owner[dy,dx]>=0: overlap.append({'dest':[int(dx),int(dy)],'body_rgb':predicted[dy,dx,:3].tolist(),'pod_rgb':source[sy,sx,:3].tolist()})
                    predicted[dy,dx]=source[sy,sx]; predicted[dy,dx,3]=255
                    owner[dy,dx]=layer
            assert not clipped and np.array_equal(predicted,target)
            # RGB 原样整数平移；仅近舱合法覆盖机体，源区没有重复归属。
            assert int(body.sum())+int(pod.sum())==int(visible.sum()) and not np.any(body&pod)
            unmoved_old_pod=[]
            for sy,sx in zip(*np.where(pod)):
                dx,dy=np.array([sx,sy])+whole
                if owner[dy,dx]==0: unmoved_old_pod.append([int(dx),int(dy)])
            assert not unmoved_old_pod
            axes=np.array(e['assembled_axes'])+whole
            assert np.max(np.abs(axes-np.array(c['axis_centers_native'])))<1e-5
            r['rigid_assembly']={'source_visible_pixels':int(visible.sum()),'body_pixels':int(body.sum()),'near_pod_pixels':int(pod.sum()),'mask_pixels':int(mask.sum()),'mask_rows_half_open':part['rows'],'whole_translation':whole.tolist(),'near_translation':offset.tolist(),'body_near_overlap_dest_pixels':len(overlap),'overlap':overlap,'clipped_source_pixels':clipped,'duplicate_source_ownership':0,'missing_source_ownership':0,'old_near_pod_body_residue_pixels':unmoved_old_pod,'full_rgba_difference':0,'visible_rgb_difference':0,'per_pod_scale':1,'axis_centers_native':axes.tolist()}
            display=Image.new('RGBA',(384,128),'white')
            display.alpha_composite(Image.fromarray(source),(0,0))
            colored=source.copy(); colored[pod,:3]=[231,62,159]; colored[body,:3]=[37,138,171]
            display.alpha_composite(Image.fromarray(colored),(128,0))
            display.alpha_composite(Image.fromarray(target),(256,0))
            name=key+'_source_ownership_final_8x.png'
            display.resize((3072,1024),Image.Resampling.NEAREST).save(OUT/name)
            diagnostics.append(name)
        else:
            # 独立 Nearest 逆映射，不以浮点 texel 边界的任一侧采样误认重绘。
            diffalpha=0; diffrgb=0; boundary=0; onecode=0; unexplained=[]; boundary_samples=[]
            rx,ry,rw,rh=e['source_rect']
            for y in range(128):
                for x in range(128):
                    fx=(x+.5-e['target_anchor'][0])/e['scale']+e['source_anchor'][0]
                    fy=(y+.5-e['target_anchor'][1])/e['scale']+e['source_anchor'][1]
                    sx,sy=math.floor(fx),math.floor(fy); actual=target[y,x].astype(int)
                    cx=[round(fx)-1,round(fx)] if abs(fx-round(fx))<1e-7 else [sx]
                    cy=[round(fy)-1,round(fy)] if abs(fy-round(fy))<1e-7 else [sy]
                    def sample(ix,iy): return source[iy+ry,ix+rx].astype(int) if 0<=ix<rw and 0<=iy<rh else np.zeros(4,dtype=int)
                    first=sample(sx,sy); coverage=(first[3]>=128)==bool(actual[3])
                    delta=int(np.max(np.abs(first[:3]-actual[:3]))) if first[3]>=128 and actual[3] else 0
                    diffalpha+=int(not coverage); diffrgb+=int(delta>0)
                    if coverage and delta==0: continue
                    matches=[(ix,iy) for iy in cy for ix in cx if (sample(ix,iy)[3]>=128)==bool(actual[3]) and (not actual[3] or np.max(np.abs(sample(ix,iy)[:3]-actual[:3]))<=1)]
                    if not matches:
                        # 记录实际相邻 texel 的源值和离边界距离，不能把理想 CPU 误写成 GPU 0 差。
                        neighbors=[]
                        for iy in range(sy-1,sy+2):
                            for ix in range(sx-1,sx+2):
                                value=sample(ix,iy)
                                if (value[3]>=128)!=bool(actual[3]) or (actual[3] and np.max(np.abs(value[:3]-actual[:3]))>1): continue
                                distance=max(max(ix-fx,0,fx-(ix+1)),max(iy-fy,0,fy-(iy+1)))
                                neighbors.append((distance,int(np.max(np.abs(value[:3]-actual[:3]))) if actual[3] else 0,ix,iy))
                        if neighbors and min(neighbors)[0]<0.01:
                            distance,delta2,ix,iy=min(neighbors)
                            boundary+=1
                            boundary_samples.append({'output':[x,y],'ideal_source_float':[fx,fy],'ideal_floor_texel':[sx,sy],'actual_neighbor_texel':[ix,iy],'distance_source_pixel':distance,'source_rgb':sample(ix,iy)[:3].tolist(),'png_rgb':actual[:3].tolist(),'rgb_max_code_difference':delta2,'coverage_same_as_neighbor':True})
                        else: unexplained.append([x,y,first.tolist(),actual.tolist()])
                    elif len(cx)>1 or len(cy)>1: boundary+=1
                    else: onecode+=1
            assert not unexplained, (key,unexplained)
            r['nearest_source_mapping']={'source':source_name,'scale':e['scale'],'ideal_floor_coverage_diff':diffalpha,'ideal_floor_visible_rgb_pixel_diff':diffrgb,'texel_boundary_cases':boundary,'neighbor_boundary_samples':boundary_samples,'max_neighbor_boundary_distance_source_pixels':max((s['distance_source_pixel'] for s in boundary_samples),default=0),'nonboundary_onecode_rgb_pixels':onecode,'unexplained':unexplained}
    records.append(r)

contacts=[]
for color in ['white','black']:
    composed=Image.new('RGBA',(384,384),color)
    for i,e in enumerate(reg['entries']): composed.alpha_composite(im(files[e['key']+'.png']),((i%3)*128,(i//3)*128))
    for factor in [1,4]:
        n=f'comparison_{color}_{factor}x.png'
        assert composed.resize((384*factor,384*factor),Image.Resampling.NEAREST).tobytes()==im(files[n]).tobytes()
        contacts.append({'file':n,'independent_full_rgba_difference':0})
roi=Image.new('RGBA',(1088,720),'white')
for i,key in enumerate(['neutral_left','neutral_right']):
    tile=Image.new('RGBA',(34,45),'white')
    tile.alpha_composite(im(files[key+'.png']).crop((48,45,82,90)))
    roi.alpha_composite(tile.resize((544,720),Image.Resampling.NEAREST),(544*i,0))
assert roi.tobytes()==im(files['profiles_roi_white_16x.png']).tobytes()
result={'status':'STATIC_PACKAGE_SOURCE_AND_RIGID_ASSEMBLY_PASS','zip_sha256':EXPECTED,'zip_bytes':ZIP.stat().st_size,'entries':len(files),'manifest_payload':len(manifest),'crc_pass':True,'manifest_pass':True,'active_all_40_byte_same':True,'source_provenance':provenance,'preassembly_source_registration_bindings':pre_bind,'old_4_copies':copies,'registration_sha256':sha(files['provenance/static_registration_drone_s004.json']),'catalog_sha256':sha(files['catalog.json']),'outputs':records,'contacts':contacts,'profiles_roi':[48,45,34,45],'profiles_roi_full_rgba_difference':0,'diagnostics':diagnostics,'engine_run':False}
(OUT/'binding.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'entries':len(files),'payload':len(manifest),'provenance':len(provenance),'old_copies':len(copies),'profiles_full_rgba_difference':[r['rigid_assembly']['full_rgba_difference'] for r in records if 'rigid_assembly' in r],'unexplained_source_samples':sum(len(r['nearest_source_mapping']['unexplained']) for r in records if 'nearest_source_mapping' in r),'contacts_full_rgba_difference':[c['independent_full_rgba_difference'] for c in contacts],'profiles_roi_full_rgba_difference':0,'engine_run':False},ensure_ascii=False,indent=2))
