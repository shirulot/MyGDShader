"""只读审核v003：CRC、载荷哈希、生产计数、验收绑定、旧文件保护及复用副本。"""
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
ARCHIVE=ROOT/'art-source/ember/deliveries/ember_assets_v003_2026-10-04.zip'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def main():
    checks=[]
    def check(name,okay,actual=None):
        checks.append({'name':name,'passed':bool(okay),'actual':actual})
    package=read(ARCHIVE.with_suffix('.package.json'))
    check('archive_sha256',digest(ARCHIVE.read_bytes())==package['sha256'],package['sha256'])
    with zipfile.ZipFile(ARCHIVE) as archive:
        names=archive.namelist()
        check('crc',archive.testzip() is None)
        check('unique_paths',len(names)==len(set(names)),len(names))
        manifest=json.loads(archive.read('DELIVERY-MANIFEST.json'))
        check('exact_payload_paths',set(names)==set(manifest['files'])|{'DELIVERY-MANIFEST.json'})
        for name,sha in manifest['files'].items():
            check('zip_sha:'+name,digest(archive.read(name))==sha)
            path=ROOT/name
            check('workspace_sha:'+name,path.is_file() and digest(path.read_bytes())==sha)
        check('no_cache_or_embedded_archive',not any(n.endswith('.zip') or '/.godot/' in n or '/__pycache__/' in n for n in names))
        pngs=sum(n.startswith('assets/ember/') and n.endswith('.png') for n in names)
        resources=sum(n.startswith('assets/ember/') and n.endswith('.tres') for n in names)
        scenes=sum(n.startswith('scenes/ember/') and n.endswith('.tscn') for n in names)
        check('formal_png_count',pngs==65,pngs)
        check('resource_count',resources==11,resources)
        check('editable_scene_count',scenes==3,scenes)
        check('art_units',manifest['completed_art_units']==123 and manifest['remaining_art_units']==0)
        check('actual_master_count',manifest['actual_archived_master_outputs']==77)
        catalog=json.loads(archive.read('assets/ember/ember_additional_catalog_v001.json'))
        review=json.loads(archive.read('art-source/ember/full-art-v001/art-review-v001.json'))
        hashes={a['id']:digest(archive.read(a['file'].removeprefix('res://'))) for a in catalog['assets']}
        check('current_40_art_binding',len(hashes)==40 and hashes==review['asset_sha256'])
        for filename,status in [('validation-candidates-v001.json','NATIVE_40_NUMERIC_PASS'),
                                ('validation-provenance-v001.json','FULL_40_PROVENANCE_PASS'),
                                ('art-review-v001.json','FULL_40_ART_REVIEW_PASS'),
                                ('godot-delivery-summary-v001.json','GODOT_FULL_ART_AND_FRESH_REUSE_PASS')]:
            proof=json.loads(archive.read('art-source/ember/full-art-v001/'+filename).decode('utf-8-sig'))
            check('gate:'+filename,proof.get('status')==status)
        provenance=json.loads(archive.read('art-source/ember/full-art-v001/validation-provenance-v001.json'))
        check('source_dependencies_present',bool(provenance.get('dependency_sha256')))
        for name,sha in provenance.get('dependency_sha256',{}).items():
            check('source_dependency_binding:'+name,name in manifest['files'] and manifest['files'][name]==sha)
        rows=list(csv.DictReader(io.StringIO(archive.read('docs/shader-learning/asset-generation-manifest.csv').decode('utf-8'))))
        art=[row for row in rows if row['category'] in {'ART_2D','ART_3D'}]
        check('ledger_123_completed',sum(int(row['quantity']) for row in art)==123 and all(row['status']!='PLANNED' for row in art))
        check('technical_scope_not_overstated',all(row['status']=='PLANNED' for row in rows if row['id'].startswith('D')))
        check('optional_collect_not_overstated',next(row for row in rows if row['id']=='C02')['status']=='PLANNED')
        check('R01_complete',next(row for row in rows if row['id']=='R01')['status']=='COMPLETE_NATIVE_SCALE_REVIEW')
        # 只核对本轮主入口的局部链接；远程文档和包自身下载链接不属于载荷。
        exclusions=[]
        for doc in ['assets/ember/README.md','docs/shader-learning/asset-production-full-art.md']:
            text=archive.read(doc).decode('utf-8')
            for destination in re.findall(r'\]\(([^)]+)\)',text):
                if destination.startswith(('http://','https://','#')): continue
                local=destination.split('#',1)[0]
                path=(ROOT/doc).parent/local
                resolved=path.resolve()
                name=resolved.relative_to(ROOT).as_posix()
                if name.endswith('.zip'):
                    exclusions.append(name)
                    check('download_link:'+name,resolved.is_file())
                    continue
                check('document_link:'+doc+':'+local,name in manifest['files'] or (resolved.is_dir() and any(n.startswith(name+'/') for n in names)))
        for name,sha in manifest['frozen_previous_archives'].items():
            path=ARCHIVE.parent/name
            check('frozen_zip:'+name,path.is_file() and digest(path.read_bytes())==sha)
    protected=read(BASE/'protected-before.json')
    for name,sha in protected.items():
        if name=='assets/ember/README.md': continue
        path=ROOT/name
        check('protected:'+name,path.is_file() and digest(path.read_bytes())==sha)
    copied=read(BASE/'fresh-copy-manifest.json')
    fresh_root=Path(copied['fresh_project'])
    check('fresh_had_no_godot_cache',copied['godot_cache_present_before_import'] is False)
    check('fresh_had_no_old_autoload',copied['autoload_present'] is False)
    for name,sha in copied['files'].items():
        path=fresh_root/name
        check('fresh_copy_sha:'+name,path.is_file() and digest(path.read_bytes())==sha)
        if name in manifest['files'] and name!='assets/ember/README.md':
            check('fresh_used_packaged_bytes:'+name,sha==manifest['files'][name])
    godot=read(BASE/'godot-delivery-summary-v001.json')
    check('all_actual_godot_stages_pass',len(godot['stages'])==10 and all(s['exit_code']==0 and s['stderr_bytes']==0 for s in godot['stages']))
    failures=[c for c in checks if not c['passed']]
    report={'status':'FULL_123_ART_DELIVERY_AUDIT_PASS' if not failures else 'FULL_123_ART_DELIVERY_AUDIT_FAIL',
            'archive':ARCHIVE.relative_to(ROOT).as_posix(),'sha256':digest(ARCHIVE.read_bytes()),
            'checks':len(checks),'failed_checks':failures,'details':checks,
            'production_png_files':pngs,'resource_files':resources,'editable_scenes':scenes,
            'completed_art_units':123,'remaining_art_units':0,'external_download_links':sorted(set(exclusions)),
            'read_only_audit':True,'payload_modified':False}
    ARCHIVE.with_suffix('.audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='details'},ensure_ascii=False,indent=2))
    raise SystemExit(bool(failures))

if __name__=='__main__':
    main()
