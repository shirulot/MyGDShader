"""Read-only production audit; all output is confined to this TA directory."""
from pathlib import Path
from PIL import Image, ImageSequence
from collections import Counter
import hashlib, io, json, math, re, zipfile

ROOT=Path('E:/dev/shader/godot-shader/godot-shader-simple')
OUT=Path(__file__).parent
ZIP=ROOT/'art-source/ember/deliveries/robot_joint_repair_v010_walk_down_candidate_2026-10-06.zip'
PREFIX='art-source/ember/robot-joint-repair-v010/'
UNPACK=OUT/'package'
BASE=UNPACK/PREFIX
LIVE=ROOT/PREFIX

def h(data):return hashlib.sha256(data).hexdigest()
def sha(path):return h(Path(path).read_bytes())
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def rgba(path):return Image.open(path).convert('RGBA')
def diff(a,b):
    if a.size!=b.size:return None
    return sum(p!=q for p,q in zip(a.getdata(),b.getdata()))
def components(image,diagonal):
    remaining={(x,y) for y in range(image.height) for x in range(image.width) if image.getpixel((x,y))[3]}
    sizes=[]
    while remaining:
        todo=[remaining.pop()];size=0
        while todo:
            x,y=todo.pop();size+=1
            for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]+([(-1,-1),(-1,1),(1,-1),(1,1)] if diagonal else []):
                q=(x+dx,y+dy)
                if q in remaining:remaining.remove(q);todo.append(q)
        sizes.append(size)
    return sorted(sizes,reverse=True)

result={'scope':'Independent fixed ZIP, local RGBA composite/ledger/regions, preserved identity, frame mapping and bound producer cold GPU evidence. No visual acceptance.'}
with zipfile.ZipFile(ZIP) as z:
    names=z.namelist()
    assert all(not Path(n).is_absolute() and '..' not in Path(n).parts and n.startswith(PREFIX) for n in names)
    z.extractall(UNPACK)
    payloads=[{'path':n,'bytes':len(z.read(n)),'sha256':h(z.read(n)),
               'extracted_sha_match':sha(UNPACK/n)==h(z.read(n)),
               'current_production_sha_match':sha(ROOT/n)==h(z.read(n)) if (ROOT/n).is_file() else None} for n in names]
    result['archive']={'sha256':sha(ZIP),'bytes':ZIP.stat().st_size,'entries':len(names),'duplicates':len(names)-len(set(names)),
                       'crc_failure':z.testzip(),'cache_payloads':[n for n in names if '/.godot/' in n],
                       'payloads':payloads,'explicit_file_hashes_manifest':any(n.endswith('file_hashes.json') for n in names)}

manifest=read(BASE/'run-manifest.json');validation=read(BASE/'qa/export_validation_v010.json');ledger=read(BASE/'qa/local_composite_v010.json')
rig=read(BASE/'source/reference-v009/source/rig_down_v009.json')
palette=[tuple(bytes.fromhex(s[1:])) for s in rig['palette']]
protected={i+1:p['id'] for i,p in enumerate(rig['parts']) if p['id'] in ['head','chest_shell','left_wrist_tool','hand_left','hand_right']}
patch=rgba(BASE/'source/joint_edit_quantized_fixed_grid_1x.png');raw=rgba(BASE/'source/joint_edit_raw_v010.png')
result['generation']={'raw_sha':sha(BASE/'source/joint_edit_raw_v010.png'),'raw_sha_ledger_match':sha(BASE/'source/joint_edit_raw_v010.png')==ledger['raw_ai_sha256']==manifest['generation']['raw_sha256'],
    'raw_size':list(raw.size),'quantized_size':list(patch.size),'raw_aspect':raw.width/raw.height,'uniform_scale':256/raw.width==192/raw.height,
    'registered_transform_match':ledger['single_global_grid_transform']==[256/raw.width,192/raw.height],
    'quantized_partial_alpha':sum(0<p[3]<255 for p in patch.getdata()),'quantized_unknown_colors':sorted({p[:3] for p in patch.getdata() if p[3]}-set(palette)),
    'pipeline_declaration':manifest['generation']['actual_pipeline']}
sample=Image.frombytes('RGBA',(256,192),(OUT/'independent_patch_sample.rgba').read_bytes())
quantized=sample.copy();nearest_cache={}
for y in range(192):
    for x in range(256):
        p=sample.getpixel((x,y))
        if p[3]<160:q=(0,0,0,0)
        else:
            if p[:3] not in nearest_cache:nearest_cache[p[:3]]=min(palette,key=lambda c:sum((c[k]-p[k])**2 for k in range(3)))
            q=(*nearest_cache[p[:3]],255)
        quantized.putpixel((x,y),q)
result['generation']['independent_declared_sharp_nearest_python_quantized_diff']=diff(quantized,patch)
quantized.save(OUT/'independent_quantized_patch.png')
old_zip=ROOT/'art-source/ember/deliveries/robot_fixed_rig_v009_foot_revision_candidate_2026-10-06.zip'
with zipfile.ZipFile(old_zip) as old:
    refs=[]
    for f in (BASE/'source/reference-v009').rglob('*'):
        if not f.is_file():continue
        relative=f.relative_to(BASE/'source/reference-v009').as_posix()
        refs.append({'path':relative,'same_old_fixed_zip':f.read_bytes()==old.read('robot-fixed-rig-v009/'+relative)})
result['v009_source_binding']={'archive_sha256':sha(old_zip),'references':refs}

region_sizes={'shoulder':(3.5,3.5),'elbow':(4,5),'wrist':(3,3.2),'hip':(4,4),'knee':(5.5,8),'ankle':(4.5,4)}
atlas=rgba(BASE/'robot_walk_down_atlas_v010.png');frames=[];gpu=[];frame_hashes=[]
for i in range(8):
    file=f'frames/robot_walk_down_f{i:02}_v010.png';current=rgba(BASE/file);original=rgba(BASE/f'source/reference-v009/frames/robot_walk_down_f{i:02}_v009.png')
    owner=rgba(BASE/f'source/reference-v009/owner_maps/walk_down_f{i:02}_owner_v009.png');mask=rgba(BASE/f'qa/edit_mask_f{i:02}_v010.png')
    pose=read(BASE/f'source/reference-v009/poses/walk_down_f{i:02}_v009.json');record=ledger['frames'][i]
    expected_regions=[{'id':f'{j}_{side}','viewer_side':'right' if side=='left' else 'left','center':pose['keypoints_projected'][f'{j}_{side}'],'rx':radius[0],'ry':radius[1]}
                      for side in ['left','right'] for j,radius in region_sizes.items()]
    expected_mask=Image.new('RGBA',(64,96));expected=original.copy();changed=[];outside=[];protected_changed=[];protected_counts=Counter()
    expected_mask_diffs=[];unexplained=[];deleted=[];added=[]
    for y in range(96):
        for x in range(64):
            before=original.getpixel((x,y));after=current.getpixel((x,y));own=owner.getpixel((x,y))[0];patch_pixel=patch.getpixel(((i%4)*64+x,(i//4)*96+y))
            selected=[r for r in expected_regions if ((x+.5-r['center'][0])/r['rx'])**2+((y+.5-r['center'][1])/r['ry'])**2<=1]
            redraw=any(r['id'].startswith(('knee_','ankle_','elbow_')) for r in selected)
            old_light=sum(v*c for v,c in zip(before[:3],[.2126,.7152,.0722]));patch_light=sum(v*c for v,c in zip(patch_pixel[:3],[.2126,.7152,.0722]))
            allowed=bool(selected) and own not in protected and y>43 and (redraw or ((before[3]==0 or old_light<125) and patch_pixel[3]==255 and patch_light>=65))
            if allowed:expected_mask.putpixel((x,y),(255,255,255,255));expected.putpixel((x,y),patch_pixel)
            if mask.getpixel((x,y))!=expected_mask.getpixel((x,y)):expected_mask_diffs.append([x,y])
            if own in protected:
                protected_counts[protected[own]]+=1
                if before!=after:protected_changed.append([x,y])
            if before!=after:
                changed.append({'xy':[x,y],'joint_regions':[r['id'] for r in selected],'before':list(before),'after':list(after)})
                if not mask.getpixel((x,y))[3]:outside.append([x,y])
                if not allowed:unexplained.append([x,y])
                if before[3] and not after[3]:deleted.append([x,y])
                if not before[3] and after[3]:added.append([x,y])
    changed_map={tuple(p['xy']):p for p in changed};declared_map={tuple(p['xy']):p for p in record['changes']}
    frame_hash=sha(BASE/file);frame_hashes.append(frame_hash)
    entry={'frame':i,'sha256':frame_hash,'size':list(current.size),'validation_sha_match':frame_hash==validation['frames'][i]['sha256'],
        'manifest_sha_match':frame_hash==manifest['frozen_frames'][i]['sha256'],'ledger_output_sha_match':frame_hash==record['output_sha256'],
        'ledger_original_sha_match':sha(BASE/f'source/reference-v009/frames/robot_walk_down_f{i:02}_v009.png')==record['source_v009_sha256'],
        'same_current_frozen_frame':sha(LIVE/file)==frame_hash,'atlas_rgba_diff':diff(current,atlas.crop((i*64,0,(i+1)*64,96))),
        'composite_rgba_diff':diff(current,expected),'mask_rgba_diff':len(expected_mask_diffs),'unexplained_changed_points':unexplained,
        'outside_mask_full_rgba_changes':outside,'protected_original_visible_changes':protected_changed,'protected_pixel_counts':dict(protected_counts),
        'top_rows_0_43_rgba_diff':diff(current.crop((0,0,64,44)),original.crop((0,0,64,44))),
        'changed_pixels':len(changed),'ledger_exact_changes_match':changed_map==declared_map,'ledger_duplicate_coordinates':len(record['changes'])-len(declared_map),
        'regions_registered_from_v009_match':record['regions']==expected_regions,'deleted_original_opaque_pixels':len(deleted),'deleted_coordinates':deleted,'added_visible_pixels':len(added),
        'alpha_values':sorted(set(current.getchannel('A').getdata())),'hidden_rgb_nonzero':sum(p[3]==0 and any(p[:3]) for p in current.getdata()),
        'unknown_visible_palette':sorted({p[:3] for p in current.getdata() if p[3]}-set(palette)),
        'components8':components(current,True),'components4':components(current,False),
        'compare_reference_same':sha(BASE/f'reference-v009/robot_walk_down_f{i:02}_v009.png')==sha(BASE/f'source/reference-v009/frames/robot_walk_down_f{i:02}_v009.png')}
    frames.append(entry)
    for scale in [1,4]:
        g=rgba(BASE/f'gpu-playback/robot_walk_down_f{i:02}_{scale}x_v010.png')
        gpu.append({'frame':i,'scale':scale,'size':list(g.size),'full_rgba_diff_to_exact_nearest_frame':diff(g,current.resize((64*scale,96*scale),Image.Resampling.NEAREST))})
result['frames']=frames;result['stored_gpu']=gpu
result['frame_set_sha256']=h('\n'.join(frame_hashes).encode())
result['frame_set_manifest_match']=result['frame_set_sha256']==manifest['frame_set_sha256']
result['atlas']={'size':list(atlas.size),'sha256':sha(BASE/'robot_walk_down_atlas_v010.png'),'manifest_match':sha(BASE/'robot_walk_down_atlas_v010.png')==manifest['atlas']['sha256'],
    'same_godot_atlas_bytes':sha(BASE/'robot_walk_down_atlas_v010.png')==sha(BASE/'godot-review/assets/robot_walk_down_atlas_v010.png'),
    'current_production_same':sha(BASE/'robot_walk_down_atlas_v010.png')==sha(LIVE/'robot_walk_down_atlas_v010.png')}
resource=(BASE/'godot-review/robot_sprite_frames_v010.tres').read_text(encoding='utf8');scene=(BASE/'godot-review/preview_joint_v010.tscn').read_text(encoding='utf8');config=(BASE/'godot-review/project.godot').read_text(encoding='utf8')
result['registration']={'regions':[list(map(int,m)) for m in re.findall(r'region = Rect2\((\d+), (\d+), (\d+), (\d+)\)',resource)],
    'animation_texture_order':re.findall(r'"texture":SubResource\("([^"]+)"\)',resource),'durations':list(map(float,re.findall(r'"duration":([\d.]+)',resource))),
    'loop_true':'"loop":true' in resource,'speed':float(re.search(r'"speed":([\d.]+)',resource).group(1)),
    'animation_names':re.findall(r'"name":&"([^"]+)"',resource),'scene_offset_root':re.findall(r'(?:offset|centered|texture_filter|scale|animation|autoplay)\s*=\s*[^\n]+',scene),
    'atlas_ext_resource':'path="res://assets/robot_walk_down_atlas_v010.png"' in resource,
    'compatibility_renderer':'renderer/rendering_method="gl_compatibility"' in config,'default_nearest':'textures/canvas_textures/default_texture_filter=0' in config}
dependency_paths=[{'declaring':str(f.relative_to(BASE)),'resource':p,'package_exists':(BASE/'godot-review'/p.removeprefix('res://')).is_file()}
    for f in [BASE/'godot-review/project.godot',BASE/'godot-review/preview_joint_v010.tscn',BASE/'godot-review/robot_sprite_frames_v010.tres']
    for p in re.findall(r'"(res://[^"]+)"',f.read_text(encoding='utf8'))]
result['registration']['runtime_dependencies']=dependency_paths
result['registration']['standalone_runtime_dependencies_all_present']=all(p['package_exists'] for p in dependency_paths)

# Independent decoding of convenience GIFs proves their pixels and timing only.
previews=[]
for name,color in [('dark',(24,38,49,255)),('light',(236,233,216,255))]:
    for factor in [1,4]:
        gif=Image.open(BASE/f'previews/walk_down_v010_{name}_{factor}x.gif');durations=[];differences=[]
        for i,page in enumerate(ImageSequence.Iterator(gif)):
            durations.append(page.info.get('duration'));native=rgba(BASE/f'frames/robot_walk_down_f{i:02}_v010.png')
            expected=Image.alpha_composite(Image.new('RGBA',(64,96),color),native).resize((64*factor,96*factor),Image.Resampling.NEAREST)
            differences.append(diff(page.convert('RGBA'),expected))
        previews.append({'background':name,'factor':factor,'loop':gif.info.get('loop'),'durations_ms':durations,'rgba_frame_differences':differences})
result['gif_previews']=previews

receipt=read(ROOT/'art-source/ember/deliveries/robot_joint_repair_v010_package_receipt_2026-10-06.json')
sidecar_file=ROOT/'art-source/ember/deliveries/robot_joint_repair_v010_cold_unpack_validation_2026-10-06.json';sidecar=read(sidecar_file)
cold_report_path=Path(sidecar['cold_report_file']);cold_report=read(cold_report_path);cold_root=Path(sidecar['cold_workspace']);cold_base=cold_root/PREFIX
producer=read(BASE/'fixed_rig_playback_v010.json')
# Independently decode the lossless WebP embedded in the actual cold-import
# .ctex container. This reads the cache from the producer cold workspace;
# it does not trigger or claim a new Godot import.
ctex_file=next((cold_base/'godot-review/.godot/imported').glob('*.ctex'))
ctex_bytes=ctex_file.read_bytes();webp_offset=ctex_bytes.find(b'RIFF')
assert webp_offset>=0 and ctex_bytes[webp_offset+8:webp_offset+12]==b'WEBP'
cold_imported_image=Image.open(io.BytesIO(ctex_bytes[webp_offset:])).convert('RGBA')
cold_imported_image.save(OUT/'bound-cold-imported-atlas-decoded.png')
result['cold_import_cache']={'ctex_file':str(ctex_file),'ctex_sha256':sha(ctex_file),'embedded_webp_offset':webp_offset,
    'decoded_size':list(cold_imported_image.size),'full_atlas_rgba_diff':diff(cold_imported_image,atlas),
    'region_full_rgba_diffs':[diff(cold_imported_image.crop((i*64,0,(i+1)*64,96)),rgba(BASE/f'frames/robot_walk_down_f{i:02}_v010.png')) for i in range(8)]}
bound_sources=[]
for path,digest in cold_report['source_hashes'].items():
    bound_sources.append({'path':path,'cold_report_sha_match':sha(cold_root/path)==digest,'fixed_package_sha_match':sha(UNPACK/path)==digest})
cold_gpu=[]
for e in cold_report['gpu_entries']:
    g=rgba(cold_root/e['file']);native=rgba(BASE/f'frames/robot_walk_down_f{e["frame"]:02}_v010.png');scale=e['scale']
    cold_gpu.append({'frame':e['frame'],'scale':scale,'cold_file_sha_match':sha(cold_root/e['file'])==e['sha256'],
        'full_rgba_diff_to_fixed_frame':diff(g,native.resize((64*scale,96*scale),Image.Resampling.NEAREST))})
sequence=cold_report['playback']['sequence'];times=[e['elapsed_ms'] for e in sequence]
result['cold_evidence_binding']={'sidecar_sha256':sha(sidecar_file),'receipt_sidecar_sha_match':sha(sidecar_file)==receipt['cold_validation_sha256'],
    'archive_sha_matches_sidecar_receipt':sha(ZIP)==receipt['sha256']==sidecar['archive_sha256'],
    'cold_report_sha_match':sha(cold_report_path)==sidecar['cold_report_sha256'],'cold_source_bindings':bound_sources,
    'cold_verifier_matches_package':cold_report['verifier_sha256']==sha(BASE/'godot-review/verify_joint_playback_v010.gd'),
    'cold_gpu_files':cold_gpu,'cold_imported_rgba_reports':cold_report['imported_atlas_regions'],
    'cold_godot_imported_png_sha':sha(cold_base/'godot-review/assets/robot_walk_down_atlas_v010.png'),
    'cold_no_errors':cold_report['errors']==[],'cold_technical_checks':cold_report['technical_checks'],
    'frame_set_matches':result['frame_set_sha256']==sidecar['frame_set_sha256'],'atlas_matches':sha(BASE/'robot_walk_down_atlas_v010.png')==sidecar['atlas_sha256'],
    'playback_sequence':sequence,'natural_loops':cold_report['playback']['actual_loops'],'visited_frames':cold_report['playback']['visited_frames'],
    'sequence_continuous':all(sequence[i]['frame']==(sequence[i-1]['frame']+1)%8 for i in range(1,len(sequence))),
    'timestamps_monotonic':times==sorted(times),'intervals_ms':[times[i]-times[i-1] for i in range(1,len(times))],
    'author_original_report_source_binding':producer['source_hashes']==cold_report['source_hashes'],'independent_gpu_rerun':False}
# Capture reports, not mutable production folders, as audit evidence.
(OUT/'bound-cold-unpack-validation.json').write_text(json.dumps(sidecar,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'bound-cold-playback.json').write_text(json.dumps(cold_report,ensure_ascii=False,indent=2),encoding='utf8')

protection=read(BASE/'qa/production_protection_v010.json');baseline=read(ROOT/'art-source/ember/robot-fixed-rig-v007/source/production_baseline_sha256_v007.json')
baseline_map={p['file']:p['sha256'] for p in baseline['files']};checks=[]
for kind in ['production','prior_frames','prior_archives']:
    for p in protection[kind]:
        entry={'kind':kind,'file':p['file'],'current_sha_matches':sha(Path(p['file']))==p['sha256']}
        if kind=='production':entry['baseline_v007_sha_matches']=baseline_map[p['file']]==p['sha256']
        checks.append(entry)
result['protected_resources']={'production_count':len(protection['production']),'prior_frame_count':len(protection['prior_frames']),
    'prior_archive_count':len(protection['prior_archives']),'checks':checks}
result['summary']={'changed_pixels':[f['changed_pixels'] for f in frames],'deleted_original_opaque_pixels':[f['deleted_original_opaque_pixels'] for f in frames],
    'all_ledgers_exact':all(f['ledger_exact_changes_match'] and f['ledger_duplicate_coordinates']==0 for f in frames),
    'composite_rgba_diffs':sum(f['composite_rgba_diff'] for f in frames),'mask_rgba_diffs':sum(f['mask_rgba_diff'] for f in frames),
    'outside_mask_rgba_changes':sum(len(f['outside_mask_full_rgba_changes']) for f in frames),
    'protected_original_visible_changes':sum(len(f['protected_original_visible_changes']) for f in frames),
    'frame_atlas_rgba_diffs':sum(f['atlas_rgba_diff'] for f in frames),'stored_gpu_rgba_diffs':sum(g['full_rgba_diff_to_exact_nearest_frame'] for g in gpu),
    'cold_gpu_rgba_diffs':sum(g['full_rgba_diff_to_fixed_frame'] for g in cold_gpu)}
(OUT/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'archive':{k:v for k,v in result['archive'].items() if k!='payloads'},'generation':result['generation'],'summary':result['summary'],
    'frame_set':result['frame_set_sha256'],'atlas':result['atlas'],'registration':result['registration'],
    'current_changed_package_paths':[p['path'] for p in payloads if not p['current_production_sha_match']],
    'frozen_source_mismatches':[p for p in refs if not p['same_old_fixed_zip']],
    'protected_resource_failures':[c for c in checks if not all(v for k,v in c.items() if k.endswith('_matches'))]},ensure_ascii=False,indent=2))
