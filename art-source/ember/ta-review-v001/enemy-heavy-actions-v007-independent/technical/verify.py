"""Incremental read-only audit of the fixed heavy actions v007 ZIP, not its active source tree."""
from pathlib import Path
from PIL import Image
from collections import Counter
import hashlib,json,math,re,zipfile,struct

ROOT=Path(r'E:/dev/shader/godot-shader/godot-shader-simple')
OUT=Path(__file__).parent
PKG=OUT/'package'
ZIP=ROOT/'art-source/ember/deliveries/enemy_heavy_actions_v007_2026-10-06.zip'
def hash_bytes(data):return hashlib.sha256(data).hexdigest()
def sha(p):return hash_bytes(Path(p).read_bytes())
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def diff(a,b):return sum(p!=q for p,q in zip(a.getdata(),b.getdata()))
def visible_diff(a,b):return sum(p[3]!=q[3] or ((p[3] or q[3]) and p[:3]!=q[:3]) for p,q in zip(a.getdata(),b.getdata()))
def sub(a,b):return [a[0]-b[0],a[1]-b[1]]
def add(a,b):return [a[0]+b[0],a[1]+b[1]]
def length(a):return math.hypot(*a)
def roundi(v):return math.floor(v+.5) if v>=0 else math.ceil(v-.5)
def f32(v):return struct.unpack('f',struct.pack('f',v))[0]
def apply(t,v):return add(t['position'],[t['basis_x'][0]*v[0]+t['basis_y'][0]*v[1],t['basis_x'][1]*v[0]+t['basis_y'][1]*v[1]])
def contains(v,poly):
    x,y=v;yes=False
    for i,(a,b) in enumerate(poly):
        c,d=poly[i-1]
        if (b>y)!=(d>y) and x<(c-a)*(y-b)/(d-b)+a:yes=not yes
    return yes
def alpha(a):
    hist=Counter(a.getchannel('A').getdata())
    return {'size':list(a.size),'bbox':a.getchannel('A').getbbox(),'visible':sum(n for v,n in hist.items() if v),'partial':sum(n for v,n in hist.items() if 0<v<255),'alpha_values':sorted(hist),'border_visible':sum(a.getpixel((x,y))[3]>0 for y in range(a.height) for x in range(a.width) if x in (0,a.width-1) or y in (0,a.height-1))}
def transform_for(rest,current,position):
    unit=[v/length(rest) for v in rest];normal=[-unit[1],unit[0]]
    axis=[v/length(rest) for v in current];target_normal=[-current[1]/length(current),current[0]/length(current)]
    return {'position':position,'basis_x':[axis[i]*unit[0]+target_normal[i]*normal[0] for i in range(2)],'basis_y':[axis[i]*unit[1]+target_normal[i]*normal[1] for i in range(2)]}
def identity(pos):return {'position':list(pos),'basis_x':[1,0],'basis_y':[0,1]}
def render_cpu(rig,texture,transforms,float32_uv=False):
    # Independent inverse affine / centre sampling. Boundary pixels can differ
    # from GPU triangle rasterization; differences are retained, never fitted away.
    img=Image.new('RGBA',(128,128));dst=img.load();src=texture.load()
    for p in sorted(rig['parts'],key=lambda p:p['z']):
        t=transforms[p['id']];a,b=t['basis_x'];c,d=t['basis_y'];det=a*d-b*c
        poly=[apply(t,sub(v,p['pivot'])) for v in p['polygon']]
        xmin=max(0,math.floor(min(v[0] for v in poly)));xmax=min(128,math.ceil(max(v[0] for v in poly)))
        ymin=max(0,math.floor(min(v[1] for v in poly)));ymax=min(128,math.ceil(max(v[1] for v in poly)))
        for y in range(ymin,ymax):
            for x in range(xmin,xmax):
                rx=x+.5-t['position'][0];ry=y+.5-t['position'][1]
                uv=[p['pivot'][0]+(d*rx-c*ry)/det,p['pivot'][1]+(-b*rx+a*ry)/det]
                if float32_uv:uv=[f32(v) for v in uv]
                if not contains(uv,p['polygon']):continue
                sx,sy=math.floor(uv[0]),math.floor(uv[1])
                v=src[sx,sy]
                if v[3]>=128:dst[x,y]=(*v[:3],255)
    return img

def rotate(angle,pos):
    a=math.radians(angle);return {'position':list(pos),'basis_x':[math.cos(a),math.sin(a)],'basis_y':[-math.sin(a),math.cos(a)]}
def linear(t,v):return [t['basis_x'][j]*v[0]+t['basis_y'][j]*v[1] for j in [0,1]]
def compose(a,b):return {'position':apply(a,b['position']),'basis_x':linear(a,b['basis_x']),'basis_y':linear(a,b['basis_y'])}
def matrix_error(a,b):return max(abs(a[k][j]-b[k][j]) for k in ['position','basis_x','basis_y'] for j in [0,1])
def sensor_texture(source,power):
    texture=source.copy();scale=.35+.65*power
    for y in [62,63]:
        for x in [64,65,66]:
            p=source.getpixel((x,y));texture.putpixel((x,y),(*[math.floor(v*scale+.5) for v in p[:3]],p[3]))
    return texture

result={'scope':'Fixed heavy v007 package, independent source/region/tread shader reconstruction and bound GPU/cold evidence. No visual approval.'}
LIVE=ROOT/'art-source/ember/enemy-heavy-actions-v007'
with zipfile.ZipFile(ZIP) as z:
    names=z.namelist();manifest=json.loads(z.read('file_hashes.json'))
    assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names)
    z.extractall(PKG)
    checks=[{'path':r['path'],'bytes_match':len(z.read(r['path']))==r['bytes'],'sha_match':hash_bytes(z.read(r['path']))==r['sha256'],
        'extracted_sha_match':sha(PKG/r['path'])==r['sha256'],'current_same':sha(LIVE/r['path'])==r['sha256']} for r in manifest['files']]
    result['archive']={'sha256':sha(ZIP),'bytes':ZIP.stat().st_size,'entries':len(names),'manifest_entries':len(checks),'crc_failure':z.testzip(),
        'duplicate_paths':len(names)-len(set(names)),'unlisted':sorted(set(names)-{r['path'] for r in manifest['files']}),'checks':checks}
rig=read(PKG/'rig.json');cat=read(PKG/'output/catalog_v007.json');source=Image.open(PKG/'source/canonical.png').convert('RGBA');parts={p['id']:p for p in rig['parts']}
with zipfile.ZipFile(ROOT/'art-source/ember/deliveries/enemy_sequences_v001_2026-10-06.zip') as old:
    b=old.read('art-source/ember/enemy-sequences-v001/templates/enemy_tracked_heavy_canonical_down_v001.png')
    result['canonical']={'sha256':sha(PKG/'source/canonical.png'),'same_original_v001_canonical_bytes':b==(PKG/'source/canonical.png').read_bytes(),
        'original_sha256':hash_bytes(b),'original_archive_sha256':sha(ROOT/'art-source/ember/deliveries/enemy_sequences_v001_2026-10-06.zip'),
        'catalog_source_sha_matches':cat['source_sha256']==sha(PKG/'source/canonical.png'),'catalog_rig_sha_matches':cat['rig_sha256']==sha(PKG/'rig.json')}
def region(p):return {(x,y) for y in range(128) for x in range(128) if source.getpixel((x,y))[3]>=128 and contains([x+.5,y+.5],p['polygon'])}
def bounds(points):return [min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points)+1,max(p[1] for p in points)+1] if points else None
regions={n:region(p) for n,p in parts.items()};all_source={(x,y) for y in range(128) for x in range(128) if source.getpixel((x,y))[3]>=128}
overlaps=[]
for track in ['left_track_mount','right_track_mount']:
    points=regions[track]&regions['tower_projector'];overlaps.append({'track':track,'count':len(points),'bbox':bounds(points),'source_xy':sorted(points),
        'x_columns':sorted({p[0] for p in points})})
result['source_regions']={'parts':rig['parts'],'source_visible_pixels':len(all_source),'part_visible_pixels':{n:len(p) for n,p in regions.items()},
    'uncovered_source_pixels':sorted(all_source-set.union(*regions.values())),'overlaps':overlaps,
    'left_right_track_overlap':sorted(regions['left_track_mount']&regions['right_track_mount']),
    'duplicate_pixels_outside_declared_mount_strips':sorted({p for e in overlaps for p in map(tuple,e['source_xy']) if not (44<=p[0]<47 or 81<=p[0]<84)})}
windows=[(30,86,12,16),(86,86,12,16)]
def tread_texture(phase):
    image=source.copy()
    for sx,sy,w,h in windows:
        for y in range(sy,sy+h):
            for x in range(sx,sx+w):
                rgb=source.getpixel((x,sy+(y-sy-phase)%h))[:3]
                image.putpixel((x,y),(*rgb,source.getpixel((x,y))[3]))
    return image
def components(image):
    left={(x,y) for y in range(128) for x in range(128) if image.getpixel((x,y))[3]};sizes=[]
    while left:
        todo=[left.pop()];count=0
        while todo:
            x,y=todo.pop();count+=1
            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    p=(x+dx,y+dy)
                    if p in left:left.remove(p);todo.append(p)
        sizes.append(count)
    return sorted(sizes,reverse=True)
clip_text=(PKG/'action_rig.gd').read_text(encoding='utf8');clips=json.JSONDecoder().raw_decode(clip_text[clip_text.index('{',clip_text.index('const CLIPS')):])[0]
neutral=Image.open(PKG/'output/idle_down/f00.png').convert('RGBA');frames=[];roundtrip=[];pose_checks=[];tread_checks=[]
for action,clip in cat['actions'].items():
    atlas=Image.open(PKG/f'output/{action}_v007.png').convert('RGBA')
    for i,pose in enumerate(clip['poses']):
        definition=clips[action]['poses'][i];expected={p['id']:identity(p['pivot']) for p in rig['parts']};expected['tower_projector']['position']=add(parts['tower_projector']['pivot'],definition['body'])
        pose_checks.append({'action':action,'frame':i,'matrix_max_error':max(matrix_error(pose['part_transforms'][n],t) for n,t in expected.items()),
            'body_translation_same':pose['body_translation_px']==definition['body'],'tread_same':pose['tread_phase_px']==definition['tread'],
            'root_same':pose['root_px']==[64,104],'supports_same':pose['supports']==[[36,104],[92,104]]})
        texture=tread_texture(definition['tread']);cpu=render_cpu(rig,texture,expected)
        for y in range(128):
            for x in range(128):
                if cpu.getpixel((x,y))[3]==0:cpu.putpixel((x,y),(255,255,255,0))
        actual=Image.open(PKG/f'output/{action}/f{i:02}.png').convert('RGBA')
        roi_alpha=sum(actual.getpixel((x,y))[3]!=neutral.getpixel((x,y))[3] for xstart in [24,86] for y in range(64,104) for x in range(xstart,xstart+18))
        static_roi=sum(actual.getpixel((x,y))!=neutral.getpixel((x,y)) for xstart in [24,86] for y in range(64,104) for x in range(xstart,xstart+18)) if action!='move_down' else None
        frame={'action':action,'frame':i,'alpha':alpha(actual),'cpu_full_rgba_diff':diff(cpu,actual),'catalog_frame_sha_match':sha(PKG/f'output/{action}/f{i:02}.png')==clip['frame_hashes'][i],
            'atlas_full_rgba_diff':diff(actual,atlas.crop((i*128,0,(i+1)*128,128))),'track_envelope_alpha_diff':roi_alpha,'static_track_roi_rgba_diff':static_roi,
            'sole_band_full_rgba_diff':diff(actual.crop((24,102,104,104)),neutral.crop((24,102,104,104))),'components8':components(actual)}
        frames.append(frame)
        if action=='move_down':
            pixels=[]
            for sx,sy,w,h in windows:
                for y in range(sy,sy+h):
                    for x in range(sx,sx+w):
                        expected_rgba=(*texture.getpixel((x,y))[:3],255 if source.getpixel((x,y))[3]>=128 else 0)
                        pixels.append({'xy':[x,y],'source_xy':[x,sy+(y-sy-definition['tread'])%h],'rgb_matches':actual.getpixel((x,y))[:3]==expected_rgba[:3],
                            'alpha_preserved':actual.getpixel((x,y))[3]==expected_rgba[3]})
            outside_changes=[]
            # Compare to a static-phase render with the same body shift so that
            # suspension does not get mistaken for tread-window colour drift.
            static=render_cpu(rig,source,expected)
            for y in range(128):
                for x in range(128):
                    inwindow=any(sx<=x<sx+w and sy<=y<sy+h for sx,sy,w,h in windows)
                    if not inwindow and (actual.getpixel((x,y))[3]!=static.getpixel((x,y))[3] or (actual.getpixel((x,y))[3] and actual.getpixel((x,y))[:3]!=static.getpixel((x,y))[:3])):outside_changes.append([x,y])
            tread_checks.append({'frame':i,'phase':definition['tread'],'window_pixels':len(pixels),'rgb_mismatches':[p for p in pixels if not p['rgb_matches']],
                'alpha_mismatches':[p for p in pixels if not p['alpha_preserved']],'nonwindow_visible_differences':outside_changes})
        for background,color in [('black',0),('white',255)]:
            pair=Image.open(PKG/f'qa/roundtrip_{action}_f{i:02}_{background}.png').convert('RGBA');left=pair.crop((0,0,384,320));right=pair.crop((384,0,768,320))
            direct=Image.alpha_composite(Image.new('RGBA',(128,128),(color,color,color,255)),actual).crop((16,32,112,112)).resize((384,320),Image.Resampling.NEAREST)
            roundtrip.append({'action':action,'frame':i,'background':background,'size':list(pair.size),'left_right_diff':diff(left,right),'left_direct_diff':diff(left,direct),'right_direct_diff':diff(right,direct)})
result['frames']=frames;result['pose_checks']=pose_checks;result['tread_checks']=tread_checks;result['saved_gpu_pairs']=roundtrip
result['neutral_source_coverage_rgb_differences']=sum((p[3]>=128)!=(n[3]==255) or (n[3]>0 and p[:3]!=n[:3]) for p,n in zip(source.getdata(),neutral.getdata()))
result['recovery_hold']={'idle_f00_f02_diff':diff(neutral,Image.open(PKG/'output/idle_down/f02.png').convert('RGBA')),
    'hit_terminal_neutral_diff':diff(neutral,Image.open(PKG/'output/hit_down/f03.png').convert('RGBA')),'all_action_neutral_starts_diff':[diff(neutral,Image.open(PKG/f'output/{a}/f00.png').convert('RGBA')) for a in cat['actions']]}
result['tread_cycle']={'windows':windows,'phases':[p['phase'] for p in tread_checks],'uniform_forward_step_mod16':all((tread_checks[(i+1)%8]['phase']-tread_checks[i]['phase'])%16==2 for i in range(8)),
    'phase16_texture_equal0':diff(tread_texture(16),tread_texture(0))==0,'phase8_unique_rgb_windows':len({tuple(tread_texture(i*2).getpixel((x,y)) for sx,sy,w,h in windows for y in range(sy,sy+h) for x in range(sx,sx+w)) for i in range(8)})}

tres=(PKG/'output/heavy_actions_v007.tres').read_text(encoding='utf8')
resources={m.group(3):(m.group(1),m.group(4)) for m in re.finditer(r'\[(sub_resource|resource)(?: type="([^"]+)" id="([^"]+)")?\]\n([\s\S]*?)(?=\n\[|\Z)',tres)}
animations=[]
for match in re.finditer(r'"frames": \[([\s\S]*?)\],\n"loop": ([01]),\n"name": &"([^"]+)",\n"speed": ([\d.]+)',tres):
    fs,loop,action,fps=match.groups();texture_ids=re.findall(r'"texture": SubResource\("([^"]+)"\)',fs);actual=[];regions=[];atlas=Image.open(PKG/f'output/{action}_v007.png').convert('RGBA')
    for tid in texture_ids:
        block=resources[tid][1];region=list(map(int,re.search(r'region = Rect2\((\d+), (\d+), (\d+), (\d+)\)',block).groups()));regions.append(region)
        iid=re.search(r'atlas = SubResource\("([^"]+)"\)',block).group(1);image_id=re.search(r'image = SubResource\("([^"]+)"\)',resources[iid][1]).group(1);block=resources[image_id][1]
        width=int(re.search(r'"width": (\d+)',block).group(1));height=int(re.search(r'"height": (\d+)',block).group(1));data=bytes(map(int,re.search(r'PackedByteArray\(([^)]*)\)',block).group(1).split(',')))
        image=Image.frombytes('RGBA',(width,height),data);x,y,w,h=region;actual.append(image.crop((x,y,x+w,y+h)))
    animations.append({'action':action,'fps':float(fps),'loop':loop=='1','frame_count':len(actual),'durations':list(map(float,re.findall(r'"duration": ([\d.]+)',fs))),'regions':regions,'embedded_atlas_rgba_diff':sum(diff(f,atlas.crop((i*128,0,(i+1)*128,128))) for i,f in enumerate(actual))})
result['spriteframes']=animations
receipt_path=LIVE/'qa/cold_receipt_v007.json';receipt=read(receipt_path);cold=Path(receipt['cold_workspace']);cold_report=read(receipt['actual_playback_report'])
result['cold_bindings']={'receipt_sha256':sha(receipt_path),'zip_sha_match':sha(ZIP)==receipt['zip_sha256'],'report_sha_matches':sha(receipt['actual_playback_report'])==receipt['playback_report_sha256'],
    'report_sha256':sha(receipt['actual_playback_report']),'report_matches_receipt_embedded':cold_report==receipt['gpu'],'catalog_bound':cold_report['catalog_sha256']==sha(PKG/'output/catalog_v007.json'),
    'core_files':[{'path':p['path'],'cold_sha_matches':sha(cold/p['path'])==p['sha256'],'fixed_package_sha_matches':sha(PKG/p['path'])==p['sha256']} for p in receipt['core_files']],
    'logs':[{'path':p['path'],'bytes':Path(p['path']).stat().st_size,'bytes_matches':Path(p['path']).stat().st_size==p['bytes'],'sha_matches':sha(p['path'])==p['sha256']} for p in receipt['logs']],
    'import_exit':receipt['import_exit'],'capture_exit':receipt['capture_exit'],'cold_report':cold_report,'independent_gpu_rerun':False}
(OUT/'bound-cold-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'bound-cold-playback.json').write_text(json.dumps(cold_report,ensure_ascii=False,indent=2),encoding='utf8')
served_root=ROOT/'art-source/ember/enemy-sequences-v001/previews';served=served_root/'heavy-actions-v007'
paths={'index.html':'preview.html','output/catalog_v007.json':'output/catalog_v007.json',**{f'output/{a}_v007.png':f'output/{a}_v007.png' for a in cat['actions']}}
result['served_binding']={'config':read(served_root/'preview_server.json'),'files':[{'path':p,'exists':(served/p).is_file(),'same_package_sha':sha(served/p)==sha(PKG/q) if (served/p).is_file() else False} for p,q in paths.items()]}
result['summary']={'all_manifest_checks':all(all(c[k] for k in ['bytes_match','sha_match','extracted_sha_match','current_same']) for c in checks),
    'cpu_full_rgba_diffs':sum(f['cpu_full_rgba_diff'] for f in frames),'atlas_full_rgba_diffs':sum(f['atlas_full_rgba_diff'] for f in frames),
    'track_envelope_alpha_diffs':sum(f['track_envelope_alpha_diff'] for f in frames),'static_track_roi_rgba_diffs':sum(f['static_track_roi_rgba_diff'] or 0 for f in frames),
    'sole_band_full_rgba_diffs':sum(f['sole_band_full_rgba_diff'] for f in frames),'tread_window_rgb_mismatches':sum(len(t['rgb_mismatches']) for t in tread_checks),
    'tread_window_alpha_mismatches':sum(len(t['alpha_mismatches']) for t in tread_checks),'nonwindow_visible_differences':sum(len(t['nonwindow_visible_differences']) for t in tread_checks),
    'saved_gpu_pairs':len(roundtrip),'gpu_pair_rgba_diffs':sum(p['left_right_diff']+p['left_direct_diff']+p['right_direct_diff'] for p in roundtrip),
    'all_embedded_atlas_rgba_diffs':sum(a['embedded_atlas_rgba_diff'] for a in animations)}
(OUT/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'archive':{k:v for k,v in result['archive'].items() if k!='checks'},'canonical':result['canonical'],'summary':result['summary'],
    'region_overlaps':[{k:v for k,v in p.items() if k!='source_xy'} for p in overlaps],'tread_cycle':result['tread_cycle'],'served':result['served_binding']},ensure_ascii=False,indent=2))

