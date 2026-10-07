"""只读复核三个新批次的实际工具输出、提示词与原生源层，不把母稿当成验收图。"""
import hashlib
import json
from pathlib import Path
from PIL import Image

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
DEPENDENCIES = {}

def digest(path):
    path=path.resolve()
    value=hashlib.sha256(path.read_bytes()).hexdigest()
    if path.is_relative_to(ROOT): DEPENDENCIES[path.relative_to(ROOT).as_posix()]=value
    return value

def read(path):
    digest(path)
    return json.loads(path.read_text(encoding='utf-8-sig'))

def resolve(value, batch=None):
    value = value.removeprefix('res://')
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    result = ROOT / candidate
    if not result.exists() and batch is not None:
        result = batch / candidate
    return result

def main():
    checks, sources, components = [], [], []
    def check(name, okay, actual=None):
        checks.append({'name':name, 'passed':bool(okay), 'actual':actual})
    for folder, expected in [('batch-03-objects',18), ('batch-04-ui',15), ('batch-05-textures',7)]:
        batch = ROOT/'art-source/ember'/folder
        ledger = read(batch/'generation-record.json')
        records = ledger.get('records',ledger.get('assets',[]))
        check(folder+':actual_master_count',len(records)==expected,len(records))
        for record in records:
            identifier = record['id']
            archived = resolve(record.get('file',record.get('master')),batch)
            original = resolve(record.get('source',record.get('actual_tool_output',record.get('tool_output'))),batch)
            prompt = resolve(record.get('prompt_file',record.get('prompt')),batch)
            check(identifier+':actual_tool_output',original.is_file(),str(original))
            check(identifier+':archived_master',archived.is_file(),str(archived))
            archived_sha = digest(archived) if archived.is_file() else None
            check(identifier+':master_sha',archived_sha==record['sha256'],archived_sha)
            check(identifier+':archive_matches_tool_output',original.is_file() and digest(original)==archived_sha)
            check(identifier+':prompt_exists',prompt.is_file(),str(prompt))
            prompt_sha = digest(prompt) if prompt.is_file() else None
            if record.get('prompt_sha256'):
                check(identifier+':prompt_sha',prompt_sha==record['prompt_sha256'])
            if record.get('full_prompt'):
                check(identifier+':full_prompt_matches',prompt.is_file() and prompt.read_text(encoding='utf-8')==record['full_prompt'])
            for reference in record.get('references',[]):
                path = resolve(reference['file'] if isinstance(reference,dict) else reference,batch)
                check(identifier+':reference_exists:'+path.name,path.is_file())
                if path.is_file(): digest(path)
                if isinstance(reference,dict) and reference.get('sha256'):
                    check(identifier+':reference_sha:'+path.name,path.is_file() and digest(path)==reference['sha256'])
            sources.append({'id':identifier,'archived':archived.relative_to(ROOT).as_posix(),
                            'tool_output':str(original),'sha256':archived_sha,
                            'prompt':prompt.relative_to(ROOT).as_posix(),'prompt_sha256':prompt_sha})
    catalog = read(BASE/'candidate-catalog-v001.json')
    check('source_ids_match_40_candidates',{a['id'] for a in catalog['assets']}=={s['id'] for s in sources})
    check('forty_distinct_actual_outputs',len({s['tool_output'] for s in sources})==40)
    by_id = {s['id']:s for s in sources}
    for asset in catalog['assets']:
        identifier = asset['id']
        check(identifier+':current_native_sha',digest(resolve(asset['file']))==asset['sha256'])
        source = asset.get('source_use')
        folders={'objects':'batch-03-objects','ui':'batch-04-ui','textures':'batch-05-textures'}
        batch=ROOT/'art-source/ember'/folders[asset['group']]
        master_sha = asset.get('source_sha256')
        if isinstance(source,dict):
            master_sha = source.get('master_sha256',source.get('mother_sha256',master_sha))
            if source.get('generation_record_sha256'):
                ledger_path=resolve(source['generation_record'],batch)
                check(identifier+':frozen_generation_record',digest(ledger_path)==source['generation_record_sha256'])
        finishing = asset.get('finishing_record')
        if finishing:
            note_path=resolve(finishing,batch)
            check(identifier+':finish_record_exists',note_path.is_file())
            if asset.get('finishing_record_sha256'):
                check(identifier+':finish_record_sha',digest(note_path)==asset['finishing_record_sha256'])
            note=read(note_path)
            output_sha=note.get('output_sha256',note.get('sha256'))
            if output_sha: check(identifier+':finish_record_output',output_sha==asset['sha256'])
        if master_sha:
            check(identifier+':finish_bound_to_master',master_sha==by_id[identifier]['sha256'])
        layers = asset.get('layers',[])
        if not layers:
            continue
        result = Image.new('RGBA',tuple(asset['canvas']))
        for layer in sorted(layers,key=lambda item:item.get('z_index',0)):
            path = resolve(layer['file'])
            check(identifier+':layer_sha:'+layer['name'],path.is_file() and digest(path)==layer['sha256'])
            if not path.is_file():
                continue
            with Image.open(path) as raw:
                check(identifier+':layer_canvas:'+layer['name'],raw.size==tuple(asset['canvas']))
                check(identifier+':layer_anchor:'+layer['name'],layer.get('anchor')==asset.get('anchor'))
                result = Image.alpha_composite(result,raw.convert('RGBA'))
            mask_name = layer.get('selection_mask')
            if mask_name:
                mask = resolve(mask_name)
                digest(mask)
                with Image.open(mask) as raw:
                    check(identifier+':selection_canvas:'+layer['name'],raw.size==tuple(asset['canvas']))
            components.append({'id':identifier,'layer':layer['name'],'file':layer['file'],'sha256':digest(path)})
        with Image.open(resolve(asset['file'])) as final:
            check(identifier+':layer_composite_matches_native',result.tobytes()==final.convert('RGBA').tobytes())
    # 冻结源目录的提示词、标注、脚本和目录。报告通过后变更依赖会使推广/封包门禁失效。
    for folder in ['batch-03-objects','batch-04-ui','batch-05-textures']:
        for path in (ROOT/'art-source/ember'/folder).rglob('*'):
            if path.is_file() and not any(part in {'__pycache__','review','pixel-review'} for part in path.parts):
                digest(path)
    validator_sha=digest(Path(__file__))
    failures = [c for c in checks if not c['passed']]
    report = {'status':'FULL_40_PROVENANCE_PASS' if not failures else 'FULL_40_PROVENANCE_FAIL',
              'actual_outputs':len(sources),'automatic_checks':len(checks),'failed_checks':failures,
              'sources':sources,'components':components,'checks':checks,
              'read_only':True,'validator_sha256':validator_sha,'dependency_sha256':dict(sorted(DEPENDENCIES.items()))}
    (BASE/'validation-provenance-v001.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'outputs':len(sources),'checks':len(checks),'failures':len(failures)}))
    raise SystemExit(bool(failures))

if __name__=='__main__':
    main()
