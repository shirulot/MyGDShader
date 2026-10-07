"""Read-only independent audit; write diagnostic evidence only beside this script."""
from pathlib import Path
from collections import deque
from PIL import Image, ImageChops
import hashlib, json, math, zipfile

ROOT = Path(r"E:/dev/shader/godot-shader/godot-shader-simple")
OUT = Path(__file__).parent
SOURCE = ROOT / "art-source/ember/building-assets-v001"
ASSETS = ROOT / "assets/ember/building_assets_v001"

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def path(value):
    return ROOT / value.removeprefix("res://")

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def roundi(value):
    return math.floor(value + .5) if value >= 0 else math.ceil(value - .5)

def rect(values):
    return tuple(map(int, values))

def inside(x, y, values):
    a,b,w,h = rect(values)
    return a <= x < a+w and b <= y < b+h

def polygon_inside(x, y, points):
    hit = False
    for i, (a,b) in enumerate(points):
        c,d = points[i-1]
        cross = (x-a)*(d-b)-(y-b)*(c-a)
        if abs(cross) < 1e-9 and min(a,c) <= x <= max(a,c) and min(b,d) <= y <= max(b,d):
            return True
        if (b > y) != (d > y) and x < (c-a)*(y-b)/(d-b)+a:
            hit = not hit
    return hit

def border_segments(size, target, borders):
    width,height = size
    tx,ty,tw,th = rect(target)
    left,top,right,bottom = rect(borders)
    cols = [(0,0,left),(left+math.floor((width-tw)/2),left,tw-left-right),(width-right,tw-right,right)]
    rows = [(0,0,top),(top+math.floor((height-th)/2),top,th-top-bottom),(height-bottom,th-bottom,bottom)]
    out=[]
    for j,(sy,dy,h) in enumerate(rows):
        for i,(sx,dx,w) in enumerate(cols):
            if w and h:
                out.append({"resized_source_region_px":[sx,sy,w,h],"output_rect_px":[tx+dx,ty+dy,w,h],"border_cell":[i,j]})
    return out

def segmented(crop, target, spec):
    cx,cy,cw,ch = rect(crop)
    tx,ty,tw,th = rect(target)
    columns=spec.get("source_columns_normalized",spec.get("cell_columns_normalized"))
    out=[]
    for i in range(len(columns)-1):
        sl,sr=roundi(cw*columns[i]),roundi(cw*columns[i+1])
        dl,dr=roundi(tw*columns[i]),roundi(tw*columns[i+1])
        rate=max((dr-dl)/(sr-sl),th/ch)
        size=[max(dr-dl,roundi((sr-sl)*rate)),max(th,roundi(ch*rate))]
        for s in border_segments(size,[tx+dl,ty,dr-dl,th],spec['border_px']):
            s.update(original_source_region_px=[cx+sl,cy,sr-sl,ch],resized_cell_size_px=size,source_cell_index=i)
            out.append(s)
    return out

def holes(image, threshold, min_pixels=16):
    width,height=image.size
    pixels=image.load()
    unseen={(x,y) for y in range(height) for x in range(width) if pixels[x,y][3]/255 < threshold}
    result=set(); sizes=[]
    while unseen:
        first=next(iter(unseen)); unseen.remove(first)
        queue=deque([first]); region={first}; edge=False
        while queue:
            x,y=queue.popleft()
            edge |= x in (0,width-1) or y in (0,height-1)
            for v in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if v in unseen:
                    unseen.remove(v);region.add(v);queue.append(v)
        if not edge and len(region)>=min_pixels:
            result.update(region);sizes.append(len(region))
    return result,sorted(sizes)

def diff_pixels(a,b):
    return sum(x!=y for x,y in zip(a.getdata(),b.getdata()))

def nearest(image, size):
    # Exact centre coordinates avoid Pillow's accumulated floating-point tie drift.
    # This remains an independent byte-to-byte sampling calculation.
    width,height=map(int,size)
    src=image.load(); output=Image.new('RGBA',(width,height)); dest=output.load()
    xs=[min(image.width-1,((2*x+1)*image.width)//(2*width)) for x in range(width)]
    ys=[min(image.height-1,((2*y+1)*image.height)//(2*height)) for y in range(height)]
    for y,sy in enumerate(ys):
        for x,sx in enumerate(xs):dest[x,y]=src[sx,sy]
    return output

spec=read(SOURCE/'source_specs_v001.json')
catalog=read(ASSETS/'catalog_v001.json')
registration=read(ASSETS/'registration_v001.json')
manifest=read(SOURCE/'generation_manifest_v001.json')
delivery=read(SOURCE/'delivery_manifest_v001.json')
entries={a['id']:a for a in catalog['assets']}
checks=[]
failures=[]
rebuilt={}

# Archive payloads are read without extracting or invoking the runtime.
archive=path(delivery['archive']['path'])
archive_report={'sha256':sha(archive),'expected_sha256':delivery['archive']['sha256'],'bytes':archive.stat().st_size}
with zipfile.ZipFile(archive) as z:
    names=[i.filename for i in z.infolist() if not i.is_dir()]
    package=read(SOURCE/'portable_file_manifest_v001.json')
    archive_report.update(entries=len(names),payloads=len(package['files']),duplicate_paths=len(names)-len(set(names)),crc_failure=z.testzip())
    archive_report['payload_failures']=[]
    archive_report['workspace_payload_failures']=[]
    archive_report['workspace_files_compared']=0
    archive_report['portable_root_project_matches']=sha(SOURCE/'godot-review/project.godot')==hashlib.sha256(z.read('project.godot')).hexdigest()
    packager=(ROOT/'tools/package_building_assets_v001.ps1').read_text(encoding='utf-8-sig')
    declared_readme=packager.split("$readme = @'\n",1)[1].split("\n'@",1)[0]+'\n'
    archive_report['portable_root_readme_matches_packager_text']=z.read('README_PORTABLE.md').decode('utf-8').replace('\r\n','\n')==declared_readme
    for row in package['files']:
        data=z.read(row['path'])
        if hashlib.sha256(data).hexdigest()!=row['sha256'] or len(data)!=row['bytes']:
            archive_report['payload_failures'].append(row['path'])
        current=ROOT/row.get('source_path',row['path'])
        # Portable root files deliberately differ from the production project's root.
        if current.is_file() and row['path']!='project.godot':
            archive_report['workspace_files_compared']+=1
            if sha(current)!=row['sha256']:
                archive_report['workspace_payload_failures'].append(row['path'])
    archive_report['unlisted_files']=sorted(set(names)-{r['path'] for r in package['files']})
    archive_report['package_manifest_sha256']=hashlib.sha256(z.read('portable_file_manifest_v001.json')).hexdigest()
    archive_report['manifest_source_sha256']=sha(SOURCE/'portable_file_manifest_v001.json')
    archive_report['forbidden_entries']=[n for n in names if '/.godot/' in n or n.endswith('.import') or 'godot-review' in n or 'prototype' in n.lower() or 'precheck' in n.lower()]

bindings=[]
for name,obj,fields in [
    ('catalog',catalog,{'source_specs_sha256':SOURCE/'source_specs_v001.json'}),
    ('registration',registration,{'source_specs_sha256':SOURCE/'source_specs_v001.json','tool_sha256':ROOT/'tools/build_building_assets_v001.gd'}),
    ('validation',read(ASSETS/'validation_v001.json'),{'source_specs_sha256':SOURCE/'source_specs_v001.json','catalog_sha256':ASSETS/'catalog_v001.json','registration_sha256':ASSETS/'registration_v001.json','validator_sha256':ROOT/'tools/validate_building_assets_v001.gd'}),
]:
    for field,file in fields.items():
        bindings.append({'record':name,'field':field,'file':str(file),'match':obj[field]==sha(file),'actual_sha256':sha(file)})

source_checks=[]
for row in manifest['sources']:
    p=path(row['path']); original=Path(row['tool_original_path'])
    source_checks.append({'id':row['id'],'manifest_sha_match':sha(p)==row['sha256'],'tool_original_exists':original.is_file(),'tool_original_sha_match':sha(p)==sha(original) if original.is_file() else None,'prompt_exists':path(row['prompt_file']).is_file(),'reference_files_exist':all(Path(x).is_file() for x in row['references'])})

for s in spec['assets']:
    e=entries[s['id']]
    actual=Image.open(path(e['texture'])).convert('RGBA')
    expected=Image.new('RGBA',rect(s['canvas_px']),(0,0,0,0))
    info={'id':s['id'],'output_sha_match':sha(path(e['texture']))==e['texture_sha256'],'canvas_match':list(actual.size)==s['canvas_px'],'pivot_match':e['pivot_px']==s['pivot_px']}
    if s.get('generated_data_mask'):
        p=expected.load()
        for x,y,w,h in map(rect,s['mask_rects_px']):
            for yy in range(y,y+h):
                for xx in range(x,x+w):p[xx,yy]=(255,255,255,255)
        info.update(kind='data_mask',source_sha_match=e['source_sha256']==sha(SOURCE/'source_specs_v001.json'))
    else:
        source=Image.open(path(e['source_path'])).convert('RGBA')
        crop=rect(e['source_crop_px']); cx,cy,cw,ch=crop
        target=rect(s['visible_rect_px']);tx,ty,tw,th=target
        mode=s.get('fit_mode','contain')
        threshold=s.get('alpha_threshold',.5)
        rate=min(tw/cw,th/ch) if mode=='contain' else max(tw/cw,th/ch)
        if mode=='border_preserve':rate=th/ch
        size=[max(1,roundi(cw*rate)),max(1,roundi(ch*rate))]
        if mode=='cover':size=[max(tw,size[0]),max(th,size[1])]
        align=s.get('align','center')
        if isinstance(align,str):align={'bottom_center':[.5,1],'top_left':[0,0],'top_center':[.5,0]}.get(align,[.5,.5])
        offset=[tx+roundi((tw-size[0])*align[0]),ty+roundi((th-size[1])*align[1])]
        info.update(kind='artist_rgb',fit_mode=mode,source_sha_match=sha(path(e['source_path']))==e['source_sha256'],resized_geometry_match=size==e['resized_size_px'] and offset==e['resized_offset_px'])
        bounding=source.getchannel('A').point(lambda a:255 if a/255>=threshold else 0).getbbox()
        auto_crop=[bounding[0],bounding[1],bounding[2]-bounding[0],bounding[3]-bounding[1]]
        info['crop_match']=list(crop)==s.get('source_crop_px',auto_crop)
        info.update(source_crop_px=list(crop),resized_size_px=size,visible_rect_px=list(target),uniform_scale_ratio=rate)
        info['uniform_scale_rounding_error_px']=[round(size[0]-cw*rate,7),round(size[1]-ch*rate,7)]
        resized=nearest(source.crop((cx,cy,cx+cw,cy+ch)),size)
        segs=[]
        if mode=='segmented_frame':
            segs=segmented(crop,target,s);cells={}
            for seg in segs:
                index=seg['source_cell_index']
                if index not in cells:
                    a,b,w,h=rect(seg['original_source_region_px'])
                    cells[index]=nearest(source.crop((a,b,a+w,b+h)),seg['resized_cell_size_px'])
                a,b,w,h=rect(seg['resized_source_region_px']);dx,dy,_,_=rect(seg['output_rect_px'])
                expected.paste(cells[index].crop((a,b,a+w,b+h)),(dx,dy))
        elif mode=='border_preserve':
            segs=border_segments(size,target,s['border_px'])
            for seg in segs:
                a,b,w,h=rect(seg['resized_source_region_px']);dx,dy,_,_=rect(seg['output_rect_px'])
                expected.paste(resized.crop((a,b,a+w,b+h)),(dx,dy))
        else:expected.paste(resized,tuple(offset))
        info['segment_geometry_match']=segs==e.get('region_segments',[])
        info['segments']=len(segs)
        if segs:info['independent_segments']=segs
        frame_id=s.get('frame_mask_asset'); frame_holes=set()
        if frame_id:
            frame_holes,areas=holes(rebuilt[frame_id],threshold,s.get('frame_min_hole_pixels',16))
            info['frame_hole_areas']=areas
        pixels=expected.load()
        polygon=s.get('mask_polygon_px',[]);keep=s.get('keep_rects_px',[]);cut=s.get('cutouts_px',s.get('apertures_px',[]))
        for y in range(expected.height):
            for x in range(expected.width):
                v=pixels[x,y]
                retain=inside(x,y,target)
                if retain and polygon:retain=polygon_inside(x+.5,y+.5,polygon)
                if retain and keep:retain=any(inside(x,y,r) for r in keep)
                if retain and cut:retain=not any(inside(x,y,r) for r in cut)
                if retain and frame_id:
                    ox,oy=s.get('frame_mask_offset_px',[0,0]);fp=(x+ox,y+oy)
                    retain=inside(*fp,s['frame_inner_rect_px']) and fp in frame_holes
                retain=retain and v[3]/255>=threshold
                pixels[x,y]=(*v[:3],255 if s.get('alpha_mode','binary')=='binary' else v[3]) if retain else (0,0,0,0)
    rebuilt[s['id']]=expected
    info['rgba_mismatch_pixels']=diff_pixels(expected,actual)
    histogram=actual.getchannel('A').histogram()
    info['partial_alpha_pixels']=sum(histogram[1:255])
    info['aperture_visible_pixels']=sum(actual.getpixel((x,y))[3]>0 for a,b,w,h in map(rect,s.get('cutouts_px',s.get('apertures_px',[]))) for y in range(b,b+h) for x in range(a,a+w))
    info['pass']=all(v for k,v in info.items() if k.endswith('_match')) and info['rgba_mismatch_pixels']==0 and info['partial_alpha_pixels']==0 and info['aperture_visible_pixels']==0
    if not info['pass']:failures.append(s['id'])
    checks.append(info)

unions=[]
for parent in sorted({s['union_parent_asset'] for s in spec['assets'] if 'union_parent_asset' in s}):
    layers=[s['id'] for s in spec['assets'] if s.get('union_parent_asset')==parent]
    parent_img=Image.open(path(entries[parent]['texture'])).convert('RGBA')
    images=[Image.open(path(entries[i]['texture'])).convert('RGBA') for i in layers]
    output=Image.new('RGBA',parent_img.size,(0,0,0,0));dest=output.load();overlap=0
    for y in range(output.height):
        for x in range(output.width):
            visible=[i.getpixel((x,y)) for i in images if i.getpixel((x,y))[3]]
            overlap+=len(visible)>1
            if visible:dest[x,y]=visible[0]
    unions.append({'parent':parent,'layers':layers,'overlap_pixels':overlap,'rgba_mismatch_pixels':diff_pixels(parent_img,output)})

old=read(ROOT/'art-source/ember/ta-review-v001/ui-v003-integrity/integrity-v003.json')
protected=[]
for c in old['checks']:
    if c.get('scope')=='protected_workspace':
        p=ROOT/c['path'];protected.append({'path':c['path'],'historical_sha256':c['expected'],'current_sha256':sha(p),'match':sha(p)==c['expected'],'baseline':'ui-v003-integrity/integrity-v003.json'})

visual=read(SOURCE/'visual_review_v001.json')
refs=[{'path':r['path'],'expected_sha256':r['sha256'],'current_sha256':sha(ROOT/r['path']),'match':sha(ROOT/r['path'])==r['sha256']} for r in visual['authoritative_references']]
result={'scope':'source identity, registered pixels, explicit geometry, archive integrity; no interaction/runtime or full visual approval','archive':archive_report,'counts':{'spec_sources':len(spec['masters']),'manifest_sources':len(manifest['sources']),'spec_assets':len(spec['assets']),'catalog_assets':len(entries),'artist_rgb_assets':sum(not s.get('generated_data_mask',False) for s in spec['assets']),'explicit_masks':sum(s.get('generated_data_mask',False) for s in spec['assets'])},'bindings':bindings,'source_checks':source_checks,'references':refs,'protected_files':protected,'asset_checks':checks,'layer_unions':unions,'asset_failures':failures}
result['source_id_sets_match']={m['id'] for m in spec['masters']}=={m['id'] for m in manifest['sources']}
result['all_accepted_masters_consumed']={m['source_path'] for m in spec['masters']}=={a['source_path'] for a in spec['assets'] if not a.get('generated_data_mask')}
result['source_originals_verified']=sum(s['tool_original_sha_match'] is True for s in source_checks)
result['current_policy_snapshot_note']='Current TA standard adds section 4.1 after ZIP freeze. Fixed payload is internally valid; this policy update is not source/art payload drift.'
(OUT/'integrity-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'archive':archive_report,'counts':result['counts'],'binding_failures':[b for b in bindings if not b['match']],'source_failures':[s for s in source_checks if not s['manifest_sha_match'] or s['tool_original_sha_match'] is False],'asset_failures':failures,'layer_unions':unions,'protected_files':protected,'reference_failures':[r for r in refs if not r['match']]},ensure_ascii=False,indent=2))
