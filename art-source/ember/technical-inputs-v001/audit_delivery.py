"""只读验收v004 ZIP、当前生产输入与历史冻结；仅写包外审计报告。"""
import hashlib,json,zipfile
from pathlib import Path
from assemble_catalog import ROOT,PROOF,sha

def main():
    archive=ROOT/'art-source/ember/deliveries/ember_assets_v004_2026-10-04.zip'
    checks=[]
    def check(name,passed): checks.append({'check':name,'pass':bool(passed)})
    acceptance=json.loads((PROOF/'final-acceptance.json').read_text(encoding='utf-8'))
    catalog_path=ROOT/'assets/ember/data/technical_inputs_catalog_v001.json'
    catalog=json.loads(catalog_path.read_text(encoding='utf-8'))
    check('accepted catalog binding',sha(catalog_path)==acceptance['accepted_catalog_sha256'])
    for a in catalog['assets']:
        check('current PNG:'+a['id'],sha(ROOT/a['file'].removeprefix('res://'))==a['sha256'])
    for field in ('evidence_sha256','delivery_document_sha256'):
        for name,expected in acceptance[field].items():check('current evidence:'+name,sha(ROOT/name)==expected)
    frozen=json.loads((PROOF/'protected-before.json').read_text(encoding='utf-8'))['sha256']
    for name,expected in frozen.items():check('old protected:'+name,sha(ROOT/name)==expected)
    with zipfile.ZipFile(archive) as z:
        check('ZIP CRC',z.testzip() is None)
        manifest=json.loads(z.read('DELIVERY-MANIFEST.json'))
        check('no duplicate entries',len(z.namelist())==len(set(z.namelist())))
        check('payload entry count',len(z.namelist())==len(manifest['files'])+1)
        for name,expected in manifest['files'].items():
            data=z.read(name)
            check('payload SHA:'+name,hashlib.sha256(data).hexdigest()==expected)
        for a in catalog['assets']:
            name=a['file'].removeprefix('res://')
            check('ZIP technical PNG:'+a['id'],manifest['files'][name]==a['sha256'])
        for field in ('evidence_sha256','delivery_document_sha256'):
            for name,expected in acceptance[field].items():
                check('ZIP evidence:'+name,manifest['files'].get(name)==expected)
        for name,expected in frozen.items():
            if name.startswith(('assets/ember/','scenes/ember/','tools/build_ember_')):
                check('ZIP inherited art/resource:'+name,manifest['files'].get(name)==expected)
        pngs=[n for n in manifest['files'] if n.startswith('assets/ember/') and n.endswith('.png')]
        resources=[n for n in manifest['files'] if n.startswith('assets/ember/') and n.endswith('.tres')]
        scenes=[n for n in manifest['files'] if n.startswith('scenes/ember/') and n.endswith('.tscn')]
        check('actual105/16/4',(len(pngs),len(resources),len(scenes))==(105,16,4))
        check('123 art / 40 tech / 0 layouts',(manifest['completed_art_units'],manifest['completed_technical_inputs'],manifest['actual_layout_masks'])==(123,40,0))
        check('portable main scene exists',b'run/main_scene="res://scenes/ember/technical_inputs_sandbox.tscn"' in z.read('project.godot'))
        check('portable project no autoload',b'[autoload]' not in z.read('project.godot'))
        check('accepted proof in ZIP',json.loads(z.read('art-source/ember/technical-inputs-v001/final-acceptance.json'))==acceptance)
    failures=[c['check'] for c in checks if not c['pass']]
    result={'status':'V004_ART_AND_TECHNICAL_ZIP_AUDIT_PASS' if not failures else 'V004_AUDIT_FAILED',
        'checks':len(checks),'failed_checks':len(failures),'failures':failures,'zip_sha256':sha(archive),
        'production_pngs':105,'resources':16,'preview_scenes':4,'art_units':123,'technical_inputs':40,
        'old_protected':len(frozen),'results':checks}
    archive.with_suffix('.audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='results'}))
    if failures: raise SystemExit(1)

if __name__=='__main__': main()
