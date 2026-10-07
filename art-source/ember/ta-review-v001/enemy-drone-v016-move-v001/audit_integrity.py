"""TA只读固定来源及旋转/椭圆投影CPU复核；不调用作者导出器或GPU。"""
from pathlib import Path
from PIL import Image
import hashlib,json,zipfile,math
HERE=Path(__file__).resolve().parent;PACK=HERE/'package';REPO=HERE.parents[3]
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rgba(p):return Image.open(p).convert('RGBA')
def mismatch(a,b):return sum(x!=y for x,y in zip(a.getdata(),b.getdata()))
def blob(z,p):return z.read(p)
manifest=load(PACK/'manifest.json');listed=manifest['files'];actual={p.relative_to(PACK).as_posix() for p in PACK.rglob('*') if p.is_file()}
rig=load(PACK/'rig.json');cat=load(PACK/'output/catalog.json');receipt=load(PACK/'SOURCE_RECEIPT.json')
result={'manifest':{'sha256':sha((PACK/'manifest.json').read_bytes()),'listed':len(listed),'missing':sorted(set(listed)-actual),'extra':sorted(actual-set(listed)-{'manifest.json'}),'bad':[f for f,q in listed.items() if not (PACK/f).exists() or sha((PACK/f).read_bytes())!=q['sha256'] or (PACK/f).stat().st_size!=q['bytes']]},'catalog':{'sha256':sha((PACK/'output/catalog.json').read_bytes()),'rig_sha_exact':sha((PACK/'rig.json').read_bytes())==cat['rig_sha256'],'tres_sha_exact':sha((PACK/cat['tres'].removeprefix('res://')).read_bytes())==cat['tres_sha256'],'canvas':cat['canvas'],'root':cat['root']}}
delivery=REPO/'art-source/ember/deliveries';static_zip=delivery/'enemy_drone_seven_directions_v013_s004_2026-10-06.zip';rotor_zip=delivery/'enemy_drone_actions_v011_2026-10-06.zip';se_zip=delivery/'enemy_eight_directions_v013_pilot_drone_v001_2026-10-06.zip';down_zip=delivery/'enemy_sequences_v012_2026-10-06.zip'
result['reference_zip_hashes']=[{'file':z.name,'sha256':sha(z.read_bytes()),'receipt_sha_exact':sha(z.read_bytes())==receipt[k]} for z,k in [(static_zip,'static_zip_sha256'),(rotor_zip,'rotor_zip_sha256'),(se_zip,'se_zip_sha256'),(down_zip,'down_zip_sha256')]]
sources=[]
with zipfile.ZipFile(static_zip) as z:
    for d in rig['directions']:
        f=f'source/{d}.png';sources.append({'direction':d,'sha256':sha((PACK/f).read_bytes()),'s004_byte_exact':(PACK/f).read_bytes()==blob(z,f'neutral_{d}.png'),'receipt_sha_exact':sha((PACK/f).read_bytes())==receipt['source_hashes'][d+'.png']})
with zipfile.ZipFile(rotor_zip) as z:
    fan_file=rig['fan_source'].removeprefix('res://');b=(PACK/fan_file).read_bytes();result['fan_source']={'file':fan_file,'sha256':sha(b),'v011_byte_exact':b==blob(z,'source/rotor_well_master.png'),'rig_hash_exact':sha(b)==rig['fan_source_sha256'],'rotor_rect':rig['rotor_rect'],'well_rect':rig['well_rect']}
result['sources']=sources;fan_master=rgba(PACK/fan_file);frame_records=[];center_records=[]
for c in cat['clips']:
    file=c['atlas'].removeprefix('res://');atlas=rgba(PACK/file);d=c['direction'];cr={'action':c['action'],'atlas_sha_exact':sha((PACK/file).read_bytes())==c['atlas_sha256'],'configuration_exact':c['frame_count']==8 and c['fps']==8 and c['loop'] is True,'atlas_size':list(atlas.size),'frames':[]}
    if d in rig['configs']:
        cfg=rig['configs'][d];source=rgba(PACK/cfg['source'].removeprefix('res://'));center_colors={f['id']:[] for f in cfg['fans']}
        windows=[{(x,y) for y in range(128) for x in range(128) if ((x+.5-f['center'][0])/f['radius'][0])**2+((y+.5-f['center'][1])/f['radius'][1])**2<1} for f in cfg['fans']];aperture=set.union(*windows)
    for i in range(8):
        f=Path(file).with_suffix('')/f'f{i:02d}.png';final=rgba(PACK/f);row={'frame':i,'file':f.as_posix(),'sha_exact':sha((PACK/f).read_bytes())==c['frame_hashes'][i],'atlas_mismatch':mismatch(final,atlas.crop((i*128,0,(i+1)*128,128))),'nonbinary_alpha':sum(q[3] not in [0,255] for q in final.getdata())}
        if d in rig['configs']:
            hover=rig['body_y'][i];expected=Image.new('RGBA',(128,128),(255,255,255,0));baseline=Image.new('RGBA',(128,128),(255,255,255,0));sampled={}
            for y in range(128):
                for x in range(128):
                    q=(x,y);ty=y+hover
                    if not 0<=ty<128:continue
                    baseline.putpixel((x,ty),source.getpixel(q))
                    if q not in aperture:expected.putpixel((x,ty),source.getpixel(q));continue
                    for n,fan in enumerate(cfg['fans']):
                        if q not in windows[n]:continue
                        dx=(x+.5-fan['center'][0])*6.5/fan['radius'][0];dy=(y+.5-fan['center'][1])*6.5/fan['radius'][1]
                        angle=math.radians(i*rig['angle_step_degrees']*fan['spin']);cs,sn=math.cos(angle),math.sin(angle)
                        sample_info=[]
                        for layer in ['well','rotor']:
                            u,v=(dx,dy) if layer=='well' else (dx*cs+dy*sn,-dx*sn+dy*cs)
                            rect=rig[layer+'_rect'];sx=rect[0]+(u+6.5)/13*rect[2];sy=rect[1]+(v+6.5)/13*rect[3]
                            pixel=fan_master.getpixel((math.floor(sx),math.floor(sy)));sample_info.append({'layer':layer,'source_uv':[sx,sy],'sampled_texel':[math.floor(sx),math.floor(sy)],'rgba':list(pixel)})
                            if pixel[3]>=128:expected.putpixel((x,ty),(*pixel[:3],255))
                        sampled[(x,ty)]=sample_info
            active={(x,y+hover) for x,y in aperture if 0<=y+hover<128};outside_visible=[];outside_hidden=[];alpha=[];residual=[]
            for y in range(128):
                for x in range(128):
                    q=(x,y);a,b=baseline.getpixel(q),final.getpixel(q);e=expected.getpixel(q)
                    if a[3]!=b[3]:alpha.append([x,y])
                    if q not in active and a!=b:
                        (outside_visible if a[3] or b[3] else outside_hidden).append([x,y])
                    if e!=b:residual.append({'xy':[x,y],'expected':list(e),'actual':list(b),'inside_aperture':q in active,'samples':sampled.get(q)})
            source_delta=sum(baseline.getpixel((x,y))!=final.getpixel((x,y)) for y in range(128) for x in range(128) if baseline.getpixel((x,y))[3] or final.getpixel((x,y))[3])
            angles={fan['id']:i*rig['angle_step_degrees']*fan['spin'] for fan in cfg['fans']}
            row.update({'hover_y':hover,'aperture_pixels':len(active),'visible_delta_from_source':source_delta,'alpha_differences':alpha,'outside_aperture_visible_rgba_differences':outside_visible,'outside_aperture_transparent_rgb_only':outside_hidden,'cpu_rgba_residual_count':len(residual),'cpu_rgba_residual':residual,'catalog_pose_exact':c['poses'][i]['body_translation']==[0,hover] and c['poses'][i]['rotor_angles_degrees']==angles and c['poses'][i]['fans']==cfg['fans']})
            for fan in cfg['fans']:
                x,y=map(math.floor,fan['center']);center_colors[fan['id']].append({'frame':i,'xy':[x,y+hover],'rgba':list(final.getpixel((x,y+hover)))})
            if i==0:row['neutral_visible_rgba_delta']=source_delta
        cr['frames'].append(row)
    if d in rig['configs']:center_records.append({'direction':d,'fans':[{'id':fan['id'],'center':fan['center'],'radius':fan['radius'],'spin':fan['spin'],'colors':center_colors[fan['id']],'all_eight_center_rgba_constant':len({tuple(q['rgba']) for q in center_colors[fan['id']]})==1} for fan in cfg['fans']]})
    frame_records.append(cr)
result['clips']=frame_records;result['axis_center']=center_records
preserved=[]
for d,zfile in [('down',down_zip),('down_right',se_zip)]:
    with zipfile.ZipFile(zfile) as z:
        f=f'output/enemy_scout_drone/move_{d}.png';preserved.append({'file':f,'old_zip':zfile.name,'byte_exact':(PACK/f).read_bytes()==blob(z,f)})
        for i in range(8):
            f=f'output/enemy_scout_drone/move_{d}/f{i:02d}.png';preserved.append({'file':f,'old_zip':zfile.name,'byte_exact':(PACK/f).read_bytes()==blob(z,f)})
result['preserved']=preserved
(HERE/'independent-pixel-integrity.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('MANIFEST',result['manifest']);print('REFERENCES',result['reference_zip_hashes']);print('SOURCES',all(q['s004_byte_exact'] and q['receipt_sha_exact'] for q in sources),'FAN',result['fan_source']['v011_byte_exact']);print('PRESERVED',len(preserved),all(q['byte_exact'] for q in preserved))
for cr in frame_records:
    if cr['frames'][0].get('hover_y') is not None:print(cr['action'],'CPU',[q['cpu_rgba_residual_count'] for q in cr['frames']],'alpha',[len(q['alpha_differences']) for q in cr['frames']],'outside visible',[len(q['outside_aperture_visible_rgba_differences']) for q in cr['frames']],'bind',cr['frames'][0]['neutral_visible_rgba_delta'])
print('CENTERS',all(q['all_eight_center_rgba_constant'] for c in center_records for q in c['fans']))
