"""TA独立只读：固定源归属、原纹理隐藏重叠、整数平移输出重建。"""
from pathlib import Path
from PIL import Image
import hashlib,json,zipfile,collections

HERE=Path(__file__).resolve().parent;PACK=HERE/'package';REPO=HERE.parents[3]
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rgba(p):return Image.open(p).convert('RGBA')
def mismatch(a,b):return sum(x!=y for x,y in zip(a.getdata(),b.getdata()))
def inside(x,y,poly):
    # 独立标准射线奇偶法，边界点记为内部；不调用作者rig或导出器。
    result=False
    for i,a in enumerate(poly):
        b=poly[(i+1)%len(poly)];ax,ay=a;bx,by=b
        cross=(x-ax)*(by-ay)-(y-ay)*(bx-ax)
        if abs(cross)<1e-10 and min(ax,bx)<=x<=max(ax,bx) and min(ay,by)<=y<=max(ay,by):return True
        if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:result=not result
    return result

manifest=load(PACK/'manifest.json');actual={p.relative_to(PACK).as_posix() for p in PACK.rglob('*') if p.is_file()};listed=manifest['files']
result={'manifest':{'sha256':sha((PACK/'manifest.json').read_bytes()),'listed':len(listed),'missing':sorted(set(listed)-actual),'extra':sorted(actual-set(listed)-{'manifest.json'}),'bad':[f for f,q in listed.items() if not (PACK/f).exists() or sha((PACK/f).read_bytes())!=q['sha256'] or (PACK/f).stat().st_size!=q['bytes']]}}
rig=load(PACK/'rig.json');catalog=load(PACK/'output/catalog.json');receipt=load(PACK/'SOURCE_RECEIPT.json')
result['catalog']={'sha256':sha((PACK/'output/catalog.json').read_bytes()),'rig_hash_exact':sha((PACK/'rig.json').read_bytes())==catalog['rig_sha256'],'tres_hash_exact':sha((PACK/catalog['tres'].removeprefix('res://')).read_bytes())==catalog['tres_sha256'],'clips':len(catalog['clips']),'root':catalog['root'],'canvas':catalog['canvas']}
static=load(REPO/'art-source/ember/enemy-eight-directions-v013/static_preflight_v001/master_catalog_v013.json');masters={x['direction']:x for x in static['masters'] if x['unit']=='enemy_tracked_heavy'}
source_records=[];direction_models={}
for d in rig['directions']:
    src=rgba(PACK/f'source/{d}.png');source_records.append({'direction':d,'sha256':sha((PACK/f'source/{d}.png').read_bytes()),'reviewed_static_sha_exact':sha((PACK/f'source/{d}.png').read_bytes())==masters[d]['sha256'],'receipt_sha_exact':sha((PACK/f'source/{d}.png').read_bytes())==receipt['source_png_hashes'][d+'.png'],'nonbinary_alpha':sum(p[3] not in [0,255] for p in src.getdata())})
    if d not in rig['configs']:continue
    cfg=rig['configs'][d];base={(x,y) for y in range(128) for x in range(128) if any(inside(x+.5,y+.5,s) for s in cfg['track_polygons'])};extended=set(base);mo=rig['mount_overlap']
    for y in range(mo['y_min'],mo['y_max']+1):
        for x in range(128):
            if any((x+dx,y+dy) in base for dx in range(-mo['radius_x'],mo['radius_x']+1) for dy in range(-mo['radius_y'],mo['radius_y']+1)):extended.add((x,y))
    added=extended-base;body={(x,y) for y in range(128) for x in range(128) if (x,y) not in base}
    added_opaque=[q for q in sorted(added) if src.getpixel(q)[3]]
    # 诊断源mask保持原位置；绿色=履带，黄铜色=新增原纹理重叠，蓝=壳体。
    diagnostic=Image.new('RGBA',(128,128))
    for xy in body:
        if src.getpixel(xy)[3]:diagnostic.putpixel(xy,(80,130,210,255))
    for xy in base:
        if src.getpixel(xy)[3]:diagnostic.putpixel(xy,(80,190,100,255))
    for xy in added_opaque:diagnostic.putpixel(xy,(220,160,60,255))
    diagnostic.resize((512,512),Image.Resampling.NEAREST).save(HERE/f'ownership_{d}_4x.png')
    direction_models[d]=(src,base,extended,body,added)
    source_records[-1].update({'base_track_opaque':sum(src.getpixel(q)[3]>0 for q in base),'body_opaque':sum(src.getpixel(q)[3]>0 for q in body),'added_overlap_opaque':len(added_opaque),'added_overlap_opaque_xy':added_opaque,'new_overlap_y_bounds':[min(y for x,y in added_opaque),max(y for x,y in added_opaque)] if added_opaque else None,'config_source_hash_exact':sha((PACK/f'source/{d}.png').read_bytes())==cfg['source_sha256']})
result['sources']=source_records
frame_records=[]
for clip in catalog['clips']:
    path=PACK/clip['atlas'].removeprefix('res://');atlas=rgba(path);d=clip['direction'];kind=clip['action'].removesuffix('_'+d);action=rig['actions'][kind]
    clip_check={'action':clip['action'],'atlas_sha_exact':sha(path.read_bytes())==clip['atlas_sha256'],'fps_loop_count_exact':clip['fps']==action['fps'] and clip['loop']==action['loop'] and clip['frame_count']==action['frames'],'atlas_size':list(atlas.size),'frames':[]}
    for i in range(4):
        f=path.with_suffix('')/f'f{i:02d}.png';final=rgba(f);colors=collections.Counter(final.getdata());row={'frame':i,'file':f.relative_to(PACK).as_posix(),'sha_exact':sha(f.read_bytes())==clip['frame_hashes'][i],'atlas_mismatch':mismatch(final,atlas.crop((i*128,0,(i+1)*128,128))),'nonbinary_alpha':sum(n for p,n in colors.items() if p[3] not in [0,255]),'size':list(final.size)}
        if d in direction_models:
            # Godot Color.TRANSPARENT=(1,1,1,0)，导出器将Alpha0统一成白RGB；透明RGB本身不改变外观。
            src,base,extended,body,added=direction_models[d];dx,dy=action['body'][i];expect=Image.new('RGBA',(128,128),(255,255,255,0));owner={}
            for xy in extended:
                if src.getpixel(xy)[3]:expect.putpixel(xy,src.getpixel(xy));owner[xy]={'part':'original_overlap' if xy in added else 'track','source_xy':xy}
            for x,y in body:
                target=(x+dx,y+dy)
                if 0<=target[0]<128 and 0<=target[1]<128 and src.getpixel((x,y))[3]:expect.putpixel(target,src.getpixel((x,y)));owner[target]={'part':'body','source_xy':(x,y)}
            exposed=[xy for xy,q in owner.items() if q['part']=='original_overlap']
            row.update({'body_delta':[dx,dy],'cpu_reconstruction_mismatch':mismatch(expect,final),'unattributed_opaque_pixels':sum(final.getpixel((x,y))[3]>0 and (x,y) not in owner for y in range(128) for x in range(128)),'exact_source_rgb_violations':sum(final.getpixel(xy)!=src.getpixel(tuple(q['source_xy'])) for xy,q in owner.items()),'exposed_overlap_opaque_pixels':len(exposed),'exposed_overlap_xy':sorted(exposed),'catalog_pose_exact':clip['poses'][i]['body_translation']==[dx,dy] and clip['poses'][i]['tread_phase']==0 and clip['poses'][i]['root']==[64,104]})
            if i==0:row['neutral_vs_source_mismatch']=mismatch(final,src);row['neutral_bind_png_mismatch']=mismatch(final,rgba(PACK/f'qa/bind_{d}.png'))
        clip_check['frames'].append(row)
    frame_records.append(clip_check)
result['clips']=frame_records
zpath=REPO/'art-source/ember/deliveries/enemy_sequences_v012_2026-10-06.zip';preserved=[]
with zipfile.ZipFile(zpath) as z:
    for clip in catalog['clips']:
        if clip['direction']!='down':continue
        file=clip['atlas'].removeprefix('res://');preserved.append({'file':file,'old_zip_byte_exact':(PACK/file).read_bytes()==z.read(file)})
        for i in range(4):
            f=str(Path(file).with_suffix('')).replace('\\','/')+f'/f{i:02d}.png';preserved.append({'file':f,'old_zip_byte_exact':(PACK/f).read_bytes()==z.read(f)})
result['preserved']={'source_zip_sha256':sha(zpath.read_bytes()),'receipt_zip_exact':sha(zpath.read_bytes())==receipt['down_zip_sha256'],'files':preserved}
old_se=load(REPO/'art-source/ember/ta-review-v001/enemy-v013-pilot-hc-v001/package/pilot_rigs.json');old_cfg=next(x for x in old_se['units'] if x['unit']=='enemy_tracked_heavy')
result['se_cutline_comparison']={'old_polygons':[x['polygon'] for x in old_cfg['parts']],'new_polygons':rig['configs']['down_right']['track_polygons'],'source_sha_unchanged':old_cfg['source_sha256']==rig['configs']['down_right']['source_sha256'],'note':'New idle/hit masking is separate from previously frozen move rig; changed ownership is not a changed source PNG.'}
result['provenance']={'registration_byte_exact_old_static':(PACK/'provenance/registration.json').read_bytes()==(REPO/'art-source/ember/enemy-eight-directions-v013/static_preflight_v001/registration.json').read_bytes(),'turnaround_sha256':sha((PACK/'provenance/source/turnarounds/enemy_tracked_heavy_eight_views_v001.png').read_bytes())}
(HERE/'independent-pixel-integrity.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('MANIFEST',result['manifest']);print('SOURCES',[(q['direction'],q['reviewed_static_sha_exact'],q.get('added_overlap_opaque')) for q in source_records])
for c in frame_records:print(c['action'],[(q['frame'],q.get('cpu_reconstruction_mismatch'),q.get('unattributed_opaque_pixels'),q.get('exact_source_rgb_violations'),q.get('exposed_overlap_opaque_pixels')) for q in c['frames']])
print('PRESERVED',len(preserved),all(x['old_zip_byte_exact'] for x in preserved));print('PROVENANCE',result['provenance'])
