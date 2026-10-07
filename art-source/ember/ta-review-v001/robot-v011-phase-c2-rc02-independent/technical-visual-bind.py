"""Bind C2 rc02 and independently isolate the six restored contour pixels."""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from io import BytesIO
from PIL import Image, ImageDraw
import hashlib
import json

out=Path(__file__).resolve().parent
root=out.parents[3]
package=out/'technical-package'
fixed=root/'art-source/ember/robot-eight-way-v011/review/phase-c2-rc02'
newzip=root/'art-source/ember/deliveries/robot_eight_way_v011_phase_c2_rc02_2026-10-07.zip'
oldzip=root/'art-source/ember/deliveries/robot_eight_way_v011_phase_c2_rc01_2026-10-07.zip'
sha=lambda b:hashlib.sha256(b).hexdigest()
expected='64a3a18625dccc2fc1bde35ae44388a7acfb92ddb9aa4c83db811d2e5c10aa1b'
assert sha(newzip.read_bytes())==expected
assert sha(oldzip.read_bytes())=='e0a5fe91bcd62509d0f342e45334ce34cf374ebea1ac0203162d9b90f79b5643'
with ZipFile(newzip) as z,ZipFile(oldzip) as oz:
    assert z.testzip() is None and oz.testzip() is None
    new={i.filename:z.read(i) for i in z.infolist() if not i.is_dir()}
    old={i.filename:oz.read(i) for i in oz.infolist() if not i.is_dir()}
assert len({n.casefold() for n in new})==len(new)
manifest=json.loads(new['sha256-manifest.json'])
assert len(manifest['files'])==1723 and len(new)==1724 and newzip.stat().st_size==35321800
assert set(new)=={r['file'] for r in manifest['files']}|{'sha256-manifest.json'}
for name,data in new.items():
    rel=PurePosixPath(name)
    assert not rel.is_absolute() and '..' not in rel.parts and ':' not in name and '\\' not in name
    p=package.joinpath(*rel.parts);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
for row in manifest['files']:
    assert len(new[row['file']])==row['bytes'] and sha(new[row['file']])==row['sha256']
    assert (fixed/row['file']).read_bytes()==new[row['file']]
meta=json.loads(new['full-action-metadata.json']);oldmeta=json.loads(old['full-action-metadata.json'])
assert meta['canvas']==[64,96] and meta['root_anchor']==[32,80]
im=lambda data:Image.open(BytesIO(data)).convert('RGBA')
atlas=im(new[meta['atlas']]);oldatlas=im(old[oldmeta['atlas']])
assert atlas.size==(512,2304) and sha(new[meta['atlas']])==meta['atlas_sha256']
assert new['godot-full-review/assets/'+meta['atlas']]==new[meta['atlas']]
assert new['godot-full-review/full-action-metadata.json']==new['full-action-metadata.json']
changed=[];exports=[];regions=[];clips=[]
for clip in meta['clips']:
    previous=next(c for c in oldmeta['clips'] if c['name']==clip['name'])
    assert all(clip[k]==previous[k] for k in ['name','direction','action','fps','loop'])
    frames=clip['frames']
    assert len(frames)=={'idle':2,'walk':8,'collect':4}[clip['action']]
    assert clip['fps']=={'idle':2,'walk':8,'collect':6}[clip['action']] and clip['loop']==(clip['action']!='collect')
    for f,pf in zip(frames,previous['frames']):
        assert all(f[k]==pf[k] for k in ['file','frame','region'])
        pic=im(new[f['file']]);prior=im(old[f['file']])
        assert pic.size==(64,96) and set(pic.getchannel('A').tobytes())=={0,255}
        assert all(pixel==(0,0,0,0) for pixel in pic.getdata() if pixel[3]==0)
        assert sha(new[f['file']])==f['sha256']
        x,y,w,h=f['region'];region=(x,y,x+w,y+h);regions.append(region)
        assert atlas.crop(region).tobytes()==pic.tobytes()
        if new[f['file']]!=old[f['file']]:
            delta=[{'xy':[x,y],'old':list(prior.getpixel((x,y))),'new':list(pic.getpixel((x,y)))} for y in range(96) for x in range(64) if pic.getpixel((x,y))!=prior.getpixel((x,y))]
            assert clip['name']=='collect_down_right' and f['frame'] in [1,2]
            assert [d['xy'] for d in delta]==[[14,52],[14,53],[14,54]]
            raw=im(new[f"source/action-rig-batch/collect/down_right/robot_collect_down_right_f{f['frame']:02d}_v011.png"])
            assert all(d['old']==[236,233,216,255] and d['new']==[16,24,32,255] and raw.getpixel(tuple(d['xy']))==tuple(d['new']) for d in delta)
            changed.append({'file':f['file'],'old_sha256':sha(old[f['file']]),'new_sha256':sha(new[f['file']]),'pixels':delta,'restored_from_same_raw_rig':True})
        exports.append({'file':f['file'],'sha256':f['sha256'],'atlas_exact':True})
    clips.append({'name':clip['name'],'fps':clip['fps'],'loop':clip['loop'],'frames':len(frames)})
assert len(changed)==2 and len(exports)==112 and len(clips)==24
atlas_changed=sum(a!=b for a,b in zip(atlas.getdata(),oldatlas.getdata()))
assert atlas_changed==6
mask_checks=[]
for index in [1,2]:
    name=f'qa/collect_down_right_joint_mask_f{index:02d}.png'
    a=im(old[name]);b=im(new[name])
    points=[[x,y] for y in range(96) for x in range(64) if a.getpixel((x,y))!=b.getpixel((x,y))]
    assert points==[[14,52],[14,53],[14,54]]
    assert all(a.getpixel(tuple(p))[3]==255 and b.getpixel(tuple(p))[3]==0 for p in points)
    mask_checks.append({'frame':index,'removed_mask_pixels':points})
patch=json.loads(new['qa/collect_down_right_joint_patch_v011.json'])
assert all(patch['records'][i]['restored_source_outer_elbow_pixels']==[[14,52],[14,53],[14,54]] for i in [1,2])
unused=atlas.copy()
for region in regions:unused.paste((0,0,0,0),region)
assert not any(unused.tobytes())
palette=sorted(set(atlas.getdata()));assert len([p for p in palette if p[3]])==11
preserved={}
for prefix in ['source/','prompts/']:
    names=[n for n in old if n.startswith(prefix)]
    diffs=[n for n in names if n not in new or old[n]!=new[n]]
    assert not diffs
    preserved[prefix]={'count':len(names),'changed':diffs}
pose_names=[n for n in old if n.endswith('rig_and_poses.json')]
assert all(old[n]==new[n] for n in pose_names)
mother_names=[n for n in old if n.startswith('source/candidate-masters/') and n.endswith('.png')]
assert len(mother_names)==8
assert all(old[n]==new[n] for n in mother_names)
oldrun=json.loads(old['run-manifest.json']);newrun=json.loads(new['run-manifest.json'])
run_changes=sorted(k for k in set(oldrun)|set(newrun) if oldrun.get(k)!=newrun.get(k))
assert run_changes==['current_candidate_revision','current_revision_fix','frozen_review','full_action_delivery','status']
assert {k:v for k,v in oldrun['full_action_delivery'].items() if k!='atlas_sha256'}=={k:v for k,v in newrun['full_action_delivery'].items() if k!='atlas_sha256'}
all_changed=sorted(n for n in set(old)&set(new) if old[n]!=new[n])
added=sorted(set(new)-set(old));removed=sorted(set(old)-set(new))
report={'zip_sha256':expected,'bytes':newzip.stat().st_size,'members':len(new),'manifest_payload':len(manifest['files']),
        'manifest_sha256':sha(new['sha256-manifest.json']),'metadata_sha256':sha(new['full-action-metadata.json']),'atlas_sha256':sha(new[meta['atlas']]),
        'fixed_directory_payloads_match':True,'changed_final_frames':changed,'unchanged_final_pngs':110,'exports112':exports,'clips24':clips,
        'atlas_changed_pixels':atlas_changed,'mask_repairs':mask_checks,
        'unused_cells_all_rgba_zero':True,'palette_opaque_count':11,'preserved_groups':preserved,'preserved_pose_files':pose_names,
        'identity_mothers_unchanged':mother_names,'run_manifest_changed_top_level_keys':run_changes,'run_manifest_generation_records_unchanged':True,
        'all_changed_payloads':all_changed,'added_payloads':added,'removed_payloads':removed,'diagnostics':{}}
def save(name,pic):
    path=out/name;pic.convert('RGB').save(path);report['diagnostics'][name]=sha(path.read_bytes())
for color,bg in {'light':(236,233,216,255),'dark':(25,42,52,255)}.items():
    ink=(20,20,20,255) if color=='light' else (240,240,240,255)
    for scale in [1,4]:
        w,h=64*scale,96*scale;chart=Image.new('RGBA',(w*4,(h+24)*2),bg);draw=ImageDraw.Draw(chart)
        for row,(label,data) in enumerate([('rc01',old),('rc02',new)]):
            for f in range(4):
                pic=im(data[f'frames/collect/down_right/robot_collect_down_right_f{f:02d}_v011.png'])
                draw.text((f*w+2,row*(h+24)+4),f'{label} F{f:02d}',fill=ink)
                chart.alpha_composite(pic.resize((w,h),Image.Resampling.NEAREST),(f*w,row*(h+24)+24))
        save(f'visual-se-collect-before-after-{color}-{scale}x.png',chart)
    roi=(11,45,24,62);w,h=13*12,17*12;chart=Image.new('RGBA',(w*4,(h+24)*3),bg);draw=ImageDraw.Draw(chart)
    for row,(label,data,prefix) in enumerate([('RAW RIG',new,'source/action-rig-batch/collect'),('rc01',old,'frames/collect'),('rc02',new,'frames/collect')]):
        for f in range(4):
            pic=im(data[f'{prefix}/down_right/robot_collect_down_right_f{f:02d}_v011.png'])
            draw.text((f*w+2,row*(h+24)+4),f'{label} F{f:02d}',fill=ink)
            chart.alpha_composite(pic.crop(roi).resize((w,h),Image.Resampling.NEAREST),(f*w,row*(h+24)+24))
    save(f'visual-se-elbow-source-before-after-{color}-12x.png',chart)
(out/'technical-visual-binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['exports112','clips24','all_changed_payloads','preserved_pose_files','identity_mothers_unchanged','diagnostics','changed_final_frames']}))
