"""封装123艺术单元的新v003交付；验收门禁不齐就停止，旧包不覆盖。"""
import csv
import hashlib
import json
from pathlib import Path
import zipfile

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
DELIVERIES=ROOT/'art-source/ember/deliveries'
ARCHIVE=DELIVERIES/'ember_assets_v003_2026-10-04.zip'
FROZEN={
    'ember_reusable_tilesets_v001_2026-10-04.zip':'5df49112a6827163037719d6bbfffae6c56eaeeb9b594313131ce86ed1237c61',
    'ember_assets_v002_2026-10-04.zip':'972de3397234047366127fb123acb0591293b5da1585d7ee7d2a7e3b2b91f342'}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def permitted(path):
    relative=path.relative_to(ROOT)
    return (path.is_file() and not any(part in {'.godot','__pycache__'} or part.startswith('fresh-')
                for part in relative.parts[:-1])
            and path.suffix not in {'.pyc','.zip','.tmp'})

def main():
    if ARCHIVE.exists():
        raise SystemExit('v003已存在；请审核现有包或显式使用新版本，禁止覆盖已交付包')
    required=[('validation-candidates-v001.json','NATIVE_40_NUMERIC_PASS'),
              ('validation-provenance-v001.json','FULL_40_PROVENANCE_PASS'),
              ('art-review-v001.json','FULL_40_ART_REVIEW_PASS'),
              ('godot-delivery-summary-v001.json','GODOT_FULL_ART_AND_FRESH_REUSE_PASS')]
    for name,status in required:
        if read(BASE/name).get('status')!=status: raise SystemExit('缺验收门禁：'+name)
    dependencies=read(BASE/'validation-provenance-v001.json').get('dependency_sha256',{})
    if not dependencies: raise SystemExit('来源依赖绑定缺失')
    for name,sha in dependencies.items():
        path=ROOT/name
        if not path.is_file() or digest(path)!=sha: raise SystemExit('来源审查后依赖已变：'+name)
    review=read(BASE/'art-review-v001.json')
    catalog=read(ROOT/'assets/ember/ember_additional_catalog_v001.json')
    current={a['id']:digest(ROOT/a['file'].removeprefix('res://')) for a in catalog['assets']}
    if current!=review['asset_sha256']: raise SystemExit('正式PNG已变更，当前美术审查失效')
    # 旧游戏、机器人和已交付文件保持字节原样；README为本轮授权的当前文档更新。
    protected=read(BASE/'protected-before.json')
    changes=[name for name,sha in protected.items() if digest(ROOT/name)!=sha]
    if any(name!='assets/ember/README.md' for name in changes):
        raise SystemExit('旧资源意外变更：'+str(changes))
    for name,sha in FROZEN.items():
        if digest(DELIVERIES/name)!=sha: raise SystemExit('旧ZIP已变：'+name)
    (BASE/'protected-after.json').write_text(json.dumps({'status':'OLD_PRODUCTION_AND_GAME_BYTES_PRESERVED',
        'checked_files':len(protected),'authorized_document_changes':changes,'frozen_archives':FROZEN},indent=2)+'\n',encoding='utf-8')
    rows=list(csv.DictReader((ROOT/'docs/shader-learning/asset-generation-manifest.csv').open(encoding='utf-8')))
    art=[row for row in rows if row['category'] in {'ART_2D','ART_3D'}]
    if sum(int(row['quantity']) for row in art)!=123 or any(row['status']=='PLANNED' for row in art):
        raise SystemExit('当前生产清单未登记123项完成')
    source_count=0
    for folder,count in [('batch-01',7),('tilesets-v001',11),('batch-02-robot',19),
                         ('batch-03-objects',18),('batch-04-ui',15),('batch-05-textures',7)]:
        ledger=read(ROOT/'art-source/ember'/folder/'generation-record.json')
        records=ledger.get('records',ledger.get('assets',[]))
        if len(records)!=count: raise SystemExit('母稿数量不符：'+folder)
        for record in records:
            archived=ROOT/record.get('file',record.get('master'))
            original=Path(record.get('source',record.get('actual_tool_output',record.get('tool_output'))))
            if digest(archived)!=record['sha256'] or not original.is_file() or digest(original)!=record['sha256']:
                raise SystemExit('实际母稿输出不符：'+folder+'/'+record['id'])
            source_count+=1
    files=set()
    for folder in ['assets/ember','scenes/ember','art-source/ember/batch-01','art-source/ember/tilesets-v001',
                   'art-source/ember/batch-02-robot','art-source/ember/batch-03-objects','art-source/ember/batch-04-ui',
                   'art-source/ember/batch-05-textures','art-source/ember/references','art-source/ember/tilesets',
                   'art-source/ember/full-art-v001']:
        files.update(path for path in (ROOT/folder).rglob('*') if permitted(path))
    for path in (ROOT/'art-source/ember/audit-2026-10-04').iterdir():
        if permitted(path): files.add(path)
    for name in ['art-generation-standard.md','asset-generation-manifest.csv','resources.md',
                 'asset-production-batch-01.md','asset-production-batch-02-robot.md',
                 'tilemap-reusable-tilesets.md','asset-production-full-art.md']:
        files.add(ROOT/'docs/shader-learning'/name)
    for name in ['build_ember_tilesets.gd','build_ember_robot_animation.gd','build_ember_asset_library.gd']:
        path=ROOT/'tools'/name
        files.add(path)
        if path.with_suffix(path.suffix+'.uid').is_file(): files.add(path.with_suffix(path.suffix+'.uid'))
    files.add(ROOT/'art-source/ember/.gdignore')
    files=sorted(files)
    names=[path.relative_to(ROOT).as_posix() for path in files]
    pngs=sum(n.startswith('assets/ember/') and n.endswith('.png') for n in names)
    resources=sum(n.startswith('assets/ember/') and n.endswith('.tres') for n in names)
    scenes=sum(n.startswith('scenes/ember/') and n.endswith('.tscn') for n in names)
    if (pngs,resources,scenes,source_count)!=(65,11,3,77):
        raise SystemExit(f'正式文件计数不符：{pngs}/{resources}/{scenes}/{source_count}')
    manifest={'date':'2026-10-04','completed_art_units':123,'remaining_art_units':0,
              'tiles':62,'robot_frames':20,'building_prop_objects':19,'ui':15,'vfx_2d':4,'textures_3d':3,
              'production_png_files':pngs,'resource_files':resources,'editable_scenes':scenes,
              'actual_archived_master_outputs':source_count,'frozen_previous_archives':FROZEN,
              'files':{path.relative_to(ROOT).as_posix():digest(path) for path in files}}
    DELIVERIES.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(ARCHIVE,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in files: archive.write(path,path.relative_to(ROOT).as_posix())
        archive.writestr('DELIVERY-MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(ARCHIVE) as archive:
        if archive.testzip() is not None or len(archive.namelist())!=len(set(archive.namelist())):
            raise SystemExit('ZIP损坏或路径重复')
        for name,sha in manifest['files'].items():
            if hashlib.sha256(archive.read(name)).hexdigest()!=sha: raise SystemExit('ZIP载荷SHA不符：'+name)
    report={'status':'PACKAGED_123_ART_UNITS','archive':ARCHIVE.relative_to(ROOT).as_posix(),
            'sha256':digest(ARCHIVE),'bytes':ARCHIVE.stat().st_size,'crc_passed':True,
            'payload_files':len(files),'archive_entries':len(files)+1,'production_png_files':pngs,
            'resource_files':resources,'editable_scenes':scenes,'actual_master_outputs':source_count,
            'completed_art_units':123,'remaining_art_units':0,'payload_sha256_match':True}
    ARCHIVE.with_suffix('.package.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
