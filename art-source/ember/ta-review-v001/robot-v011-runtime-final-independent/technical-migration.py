"""只读正式 ZIP 与已通过 C2rc02；验证迁移白名单并准备独立冷副本。"""
from pathlib import Path,PurePosixPath
from zipfile import ZipFile
import json,hashlib,difflib,re
from collections import Counter

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
DEL=ROOT/'art-source/ember/deliveries'
runtime=DEL/'robot_eight_way_v011_final_2026-10-07.zip'
source=DEL/'robot_eight_way_v011_phase_c2_rc02_2026-10-07.zip'
live=ROOT/'art-source/ember/robot-eight-way-v011/delivery/robot-v011'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(runtime.read_bytes())=='8dc65a715b41b2c61a09eb6e2afbcd31134db60228f4b3081a0a39e4d153f4bb'
assert runtime.stat().st_size==1398383
assert sha(source.read_bytes())=='64a3a18625dccc2fc1bde35ae44388a7acfb92ddb9aa4c83db811d2e5c10aa1b'
z,old=ZipFile(runtime),ZipFile(source)
assert z.testzip() is None
names=[i.filename for i in z.infolist() if not i.is_dir()]
assert len(names)==337 and len({n.casefold() for n in names})==337
for n in names:
    path=PurePosixPath(n)
    assert not path.is_absolute() and '..' not in path.parts and ':' not in n and '\\' not in n
manifest=json.loads(z.read('sha256-manifest.json'))
assert sha(z.read('sha256-manifest.json'))=='d605101d0e668796995599a44f9cd86010220f108ef0e21adec62faf20797235'
assert len(manifest['files'])==336 and {x['file'] for x in manifest['files']}==set(names)-{'sha256-manifest.json'}
for x in manifest['files']:
    data=z.read(x['file']);assert len(data)==x['bytes'] and sha(data)==x['sha256']
assert all(z.read(n)==(live/n).read_bytes() for n in names)
report={'status':'PASS_SOURCE_MIGRATION_BINDING','runtime_zip_sha256':sha(runtime.read_bytes()),'bytes':runtime.stat().st_size,'source_zip_sha256':sha(source.read_bytes()),'runtime_manifest_sha256':sha(z.read('sha256-manifest.json')),'payloads_verified':336,'fixed_directory_manifest_files_byte_identical':337,'preserved':[],'path_only':[],'metadata_changes':[]}
meta=json.loads(z.read('full-action-metadata.json'));prev=json.loads(old.read('full-action-metadata.json'))
assert meta['canvas']==[64,96] and meta['root_anchor']==[32,80] and meta['total_clips']==24 and meta['total_frames']==112
for clip in meta['clips']:
    for frame in clip['frames']:
        n=frame['file'];assert z.read(n)==old.read(n)
        assert sha(z.read(n))==frame['sha256'];report['preserved'].append({'kind':'frame_png','source':n,'runtime':n,'sha256':sha(z.read(n))})
previews=sorted(n for n in names if n.startswith('previews/') and n.endswith(('.gif','.webp')))
assert len(previews)==192
for n in previews:
    assert z.read(n)==old.read(n);report['preserved'].append({'kind':'animated_preview','source':n,'runtime':n,'sha256':sha(z.read(n))})
atlas=meta['atlas'];assert z.read(atlas)==old.read(prev['atlas'])
assert sha(z.read(atlas))=='0340a11ca59efdb18c64385fa24ec8faa833f0c3c6b056b5c6a97d3f3f5b4268'
report['preserved'].append({'kind':'atlas_png','source':prev['atlas'],'runtime':atlas,'sha256':sha(z.read(atlas))})
pairs=[
 ('godot-full-review/robot_eight_way_v011.tres','assets/ember/robot_v011/robot_eight_way_v011.tres','res://assets/robot_eight_way_actions_atlas_v011.png','res://assets/ember/robot_v011/robot_eight_way_actions_atlas_v011.png'),
 ('godot-full-review/preview_full_actions.gd','preview/preview_full_actions.gd','res://robot_eight_way_v011.tres','res://assets/ember/robot_v011/robot_eight_way_v011.tres'),
 ('godot-full-review/preview_full_actions.tscn','preview/preview_full_actions.tscn','res://preview_full_actions.gd','res://preview/preview_full_actions.gd'),
 ('godot-full-review/project.godot','project.godot','res://preview_full_actions.tscn','res://preview/preview_full_actions.tscn')]
for src,dst,a,b in pairs:
    assert old.read(src).count(a.encode())==1
    assert old.read(src).replace(a.encode(),b.encode())==z.read(dst)
    report['path_only'].append({'source':src,'runtime':dst,'old_path':a,'new_path':b,'source_sha256':sha(old.read(src)),'runtime_sha256':sha(z.read(dst))})
def walk_diff(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        for k in a.keys()|b.keys():
            if k not in a or k not in b:report['metadata_changes'].append({'path':path+'/'+k,'old':a.get(k),'new':b.get(k)})
            else:walk_diff(a[k],b[k],path+'/'+k)
    elif isinstance(a,list) and isinstance(b,list):
        assert len(a)==len(b)
        for i,(x,y) in enumerate(zip(a,b)):walk_diff(x,y,path+'/'+str(i))
    elif a!=b:report['metadata_changes'].append({'path':path,'old':a,'new':b})
walk_diff(prev,meta)
allowed={'/status','/atlas','/release','/art_acceptance'}|{'/clips/'+str(i)+'/art_status' for i in range(24)}
assert {r['path'] for r in report['metadata_changes']}==allowed
assert meta['art_acceptance']['receipt_sha256']==sha(z.read(meta['art_acceptance']['receipt']))
assert z.read('evidence/ta-c2-final.md')==(OUT.parent/'robot-v011-phase-c2-rc02-independent/review-c2-rc02.md').read_bytes()
before_import=old.read('godot-full-review/assets/robot_eight_way_actions_atlas_v011.png.import').decode('utf-8-sig')
after_import=z.read(atlas+'.import').decode('utf-8-sig')
assert before_import.split('[params]',1)[1]==after_import.split('[params]',1)[1]
norm=lambda t:re.sub(r'res://\.godot/imported/[^"\]\r\n]+','res://.godot/imported/PATH_DERIVED_CACHE',t).replace('res://assets/robot_eight_way_actions_atlas_v011.png','res://assets/ember/robot_v011/robot_eight_way_actions_atlas_v011.png')
assert norm(before_import)==norm(after_import)
report['import']={'params_byte_same':True,'only_source_and_path_derived_cache_changed':True,'mipmaps':False,'fix_alpha_border':False}
a=old.read('action-batch-review.html').decode('utf-8-sig').splitlines();b=z.read('preview.html').decode('utf-8-sig').splitlines()
assert len(a)==len(b)
changes=[(i,x,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y];assert len(changes)==3
for i,x,y in changes:
    assert (x.startswith('<p>24') and y.startswith('<p>24')) or (x.replace('godot-full-review/project.godot','project.godot')==y) or ("$('status').textContent=" in x and x.split("$('status').textContent=",1)[0]==y.split("$('status').textContent=",1)[0])
report['web_changed_lines']=[{'line':i+1,'old':x,'new':y} for i,x,y in changes]
report['counts']=dict(Counter(x['kind'] for x in report['preserved']))
report['gdignore_files']=[n for n in names if n.endswith('.gdignore')]
assert set(report['gdignore_files'])=={'frames/.gdignore','previews/.gdignore','evidence/.gdignore'}
report['author_bound_only']={n:sha(z.read(n)) for n in names if n.startswith('evidence/')}
author_cold=ROOT/'art-source/ember/robot-eight-way-v011/qa/cold-runtime-final-validation/receipt.json'
report['author_external_cold_receipt_sha256']=sha(author_cold.read_bytes())
report['author_external_cold_receipt']=json.loads(author_cold.read_text(encoding='utf-8-sig'))
assert report['author_external_cold_receipt']['zip_sha256']==report['runtime_zip_sha256']
(OUT/'technical-migration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':report['status'],'payloads':336,'preserved':report['counts'],'path_only':len(report['path_only']),'metadata_changes':len(report['metadata_changes']),'web_changed_lines':[r['line'] for r in report['web_changed_lines']]}))
