"""核对固定包65载荷、来源与同母图分层，创建独立冷副本；生产目录只读。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from collections import Counter
import hashlib
import json
from PIL import Image

ROOT=Path('E:/dev/shader/godot-shader/godot-shader-simple')
OUT=Path(__file__).resolve().parent
COLD=OUT/'cold-project'
ZIP=ROOT/'art-source/ember/deliveries/building_assets_v004_2026-10-06.zip'
EXPECTED='7d0b44613858a073ecb2696f88e4c4188dc7a58b38aa3d7a6f20279ae6d70ff5'
def sha(data):return hashlib.sha256(data).hexdigest()
def strip(value):return value.removeprefix('res://')
def decode(raw):return raw.decode('utf-8-sig')
def image(package,path):return Image.open(BytesIO(package.read(strip(path)))).convert('RGBA')
def flat(img):return list(img.get_flattened_data())
assert ZIP.stat().st_size==27605384 and sha(ZIP.read_bytes())==EXPECTED
report={'zip_sha256':EXPECTED,'zip_bytes':ZIP.stat().st_size,'manifest_checks':[],'building_sources':[],'composition':[],'author_evidence':{}}
with ZipFile(ZIP) as package:
    entries=[e for e in package.infolist() if not e.is_dir()]
    names={e.filename for e in entries}
    assert len(entries)==len(names)==66
    manifest=json.loads(decode(package.read('DELIVERY_MANIFEST.json')))
    assert len(manifest['files'])==65
    assert names=={r['path'] for r in manifest['files']}|{'DELIVERY_MANIFEST.json'}
    for entry in entries:
        target=(COLD/entry.filename).resolve()
        assert target.is_relative_to(COLD.resolve())
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(package.read(entry))
    for record in manifest['files']:
        raw=package.read(record['path'])
        assert len(raw)==record['bytes'] and sha(raw)==record['sha256']
        relative=record['path']
        local=ROOT/relative
        if relative=='README.md':local=ROOT/'art-source/ember/building-assets-v004/README.md'
        if relative=='project.godot':local=ROOT/'art-source/ember/building-assets-v004/godot-review/project.godot'
        same=local.is_file() and local.read_bytes()==raw
        assert same,relative
        report['manifest_checks'].append({'path':relative,'bytes':len(raw),'sha256':sha(raw),'zip_and_workspace_match':same})
    catalog=json.loads(decode(package.read('assets/ember/building_assets_v004/catalog_v004.json')))
    functional=json.loads(decode(package.read('assets/ember/building_assets_v004/functional_layers_v004.json')))
    records={r['building_id']:r for r in functional['buildings']}
    layer_count=0
    for building in catalog['buildings']:
        bid=building['id'];complete=image(package,building['complete_texture'])
        assert list(complete.size)==building['canvas_px']==[1254,1254]
        raw=package.read(strip(building['complete_texture']))
        assert sha(raw)==building['complete_sha256']
        master=package.read(f'art-source/ember/building-assets-v004/masters/{bid}_intact_v004.png')
        assert master==raw
        entry=records[bid]
        assert entry['source_pivot_px']==building['source_pivot_px'] and abs(entry['uniform_scale']-building['uniform_scale'])<1e-12
        for layer in entry['layers']:
            for region in layer['regions']:
                assert all(float(v).is_integer() for v in region)
            layer['regions']=[list(map(int,region)) for region in layer['regions']]
        layers=[('fixed_architecture',image(package,entry['fixed_architecture']),entry['fixed_sha256'])]+[(layer['id'],image(package,layer['texture']),layer['sha256']) for layer in entry['layers']]
        rebuilt=Image.new('RGBA',complete.size)
        owners=[0]*(complete.width*complete.height)
        source_pixels=flat(complete)
        declared=set()
        for layer in entry['layers']:
            for x,y,w,h in layer['regions']:
                bevel=layer['chamfer']
                for yy in range(y,y+h):
                    for xx in range(x,x+w):
                        qx=xx+0.5-x;qy=yy+0.5-y
                        if qx+qy<bevel or w-qx+qy<bevel:continue
                        index=yy*complete.width+xx
                        assert index not in declared,(bid,index)
                        declared.add(index)
        layers_proven=[]
        for lid,img,digest in layers:
            fn=entry['fixed_architecture'] if lid=='fixed_architecture' else next(layer['texture'] for layer in entry['layers'] if layer['id']==lid)
            assert sha(package.read(strip(fn)))==digest
            assert img.size==complete.size
            mismatch=0
            raw_hidden_difference=0
            examples=[]
            for index,(p,s) in enumerate(zip(flat(img),source_pixels)):
                expected_here=(index not in declared) if lid=='fixed_architecture' else any(
                    x<=index%complete.width<x+w and y<=index//complete.width<y+h and
                    index%complete.width+0.5-x+index//complete.width+0.5-y>=layer['chamfer'] and
                    w-(index%complete.width+0.5-x)+index//complete.width+0.5-y>=layer['chamfer']
                    for layer in entry['layers'] if layer['id']==lid for x,y,w,h in layer['regions'])
                if expected_here:
                    if p!=s:
                        if p[3]==s[3]==0:raw_hidden_difference+=1
                        else:
                            mismatch+=1
                            if len(examples)<8:examples.append({'xy':[index%complete.width,index//complete.width],'layer':p,'source':s})
                elif p[3]!=0:
                    mismatch+=1
                elif p[:3]!=(0,0,0):
                    # 未分配像素只要求透明；Godot Color.TRANSPARENT 可保留白色隐藏 RGB。
                    raw_hidden_difference+=1
                if p[3]:
                    owners[index]+=1
                    rebuilt.putpixel((index%complete.width,index//complete.width),p)
            assert mismatch==0,(bid,lid,mismatch,examples)
            layers_proven.append({'id':lid,'visible_source_pixel_or_cleared_rgba_mismatch':mismatch,'both_alpha0_hidden_rgba_difference':raw_hidden_difference})
        rgb_alpha_diff=sum(a!=b and (a[3]!=0 or b[3]!=0) for a,b in zip(flat(rebuilt),source_pixels))
        assert rgb_alpha_diff==0
        overlap=sum(n>1 for n in owners)
        omitted=sum(p[3]>0 and n==0 for p,n in zip(source_pixels,owners))
        assert overlap==omitted==0
        layer_count+=len(layers)
        report['composition'].append({'building':bid,'layers':layers_proven,'visible_rgba_different_pixels':rgb_alpha_diff,'multiple_visible_owners':overlap,'omitted_source_visible_pixels':omitted,'declared_moving_regions_disjoint':True,'source_partial_alpha_pixels':sum(0<p[3]<255 for p in source_pixels)})
        door_values=[]
        for d in building['doors']:
            x,y,w,h=d['source_rect_px'];scale=building['uniform_scale'];pivot=building['source_pivot_px']
            expected_clear=[w*scale,h*scale];expected_x=(x+w/2-pivot[0])*scale
            assert all(abs(a-b)<1e-6 for a,b in zip(expected_clear,d['clear_world_px']))
            assert abs(expected_x-d['center_world_x'])<1e-6
            door_values.append({'id':d['id'],'derived_clear_world':expected_clear,'derived_center_x':expected_x})
        report['building_sources'].append({'building':bid,'master_and_complete_bytes_equal':True,'master_sha256':sha(master),'source_pivot_px':building['source_pivot_px'],'uniform_scale':building['uniform_scale'],'footprint_px':building['footprint_px'],'doors':door_values})
    assert layer_count==15
    author=json.loads(decode(package.read('assets/ember/building_assets_v004/previews/validation_v004.json')))
    assert author['passed']==author['total']==60 and all(c['pass'] for c in author['checks'])
    for capture in author['captures']:
        assert sha(package.read(strip(capture['path'])))==capture['sha256']
    report['author_evidence']={'manifest_cold_runtime':manifest['cold_runtime'],'bound_report_passed':author['passed'],'bound_report_total':author['total'],'report_sha256':sha(package.read('assets/ember/building_assets_v004/previews/validation_v004.json')),'capture_hashes_checked':len(author['captures']),'meaning':'Producer evidence reviewed and bound, not counted as an independent rerun.'}
    report['prefabs']=[n for n in sorted(names) if n.startswith('scenes/ember/building_assets_v004/') and n.endswith('.tscn')]
    assert len(report['prefabs'])==7
    project=COLD/'project.godot'
    raw=project.read_bytes();report['original_project_sha256']=sha(raw)
    adjusted=decode(raw).replace('[application]','[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="Ember TA Building v004 Independent"')
    project.write_text(adjusted,encoding='utf-8')
    report['review_copy_config_change']='Only an isolated user-data directory for independent state probes.'
report['status']='STATIC_PACKAGE_AND_SAME_MASTER_LAYER_PASS'
(OUT/'static-integrity-evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':report['status'],'manifest_payloads':len(report['manifest_checks']),'layers':layer_count,'prefabs':len(report['prefabs']),'composition':[{k:v for k,v in entry.items() if k!='layers'} for entry in report['composition']]},ensure_ascii=False))
