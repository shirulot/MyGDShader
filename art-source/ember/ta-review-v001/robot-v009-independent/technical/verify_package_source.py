"""v009 固定包、源复用与八格独立核验；只在 TA 目录解包、输出证据。"""
import difflib
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
from PIL import Image

workspace = Path('E:/dev/shader/godot-shader/godot-shader-simple')
relative = Path('art-source/ember/robot-fixed-rig-v009')
base = workspace / relative
review = workspace / 'art-source/ember/ta-review-v001/robot-v009-independent/technical'
cold = review / 'cold-workspace'
archive_path = workspace / 'art-source/ember/deliveries/robot_fixed_rig_v009_foot_revision_candidate_2026-10-06.zip'
old_archive_path = workspace / 'art-source/ember/deliveries/robot_fixed_rig_v008_walk_down_candidate_2026-10-06.zip'
checks = []

def sha(data): return hashlib.sha256(data).hexdigest()
def read_json(data): return json.loads(data.decode('utf-8-sig'))
def check(name, passed, **details): checks.append(dict(name=name, passed=bool(passed), **details))
def normalize(value):
    if isinstance(value, str): return value.replace('v008', 'v009').replace('V008', 'V009')
    if isinstance(value, list): return [normalize(item) for item in value]
    if isinstance(value, dict): return {normalize(key):normalize(item) for key,item in value.items()}
    return value
def differences(old, new, path=''):
    if type(old) is not type(new): return [path]
    if isinstance(old, dict):
        result = []
        for key in old.keys() | new.keys():
            if key not in old or key not in new: result.append(path + '/' + key)
            else: result += differences(old[key],new[key],path + '/' + key)
        return result
    if isinstance(old, list):
        if len(old) != len(new): return [path]
        return [part for index,(first,second) in enumerate(zip(old,new)) for part in differences(first,second,path + '/' + str(index))]
    return [] if old == new else [path]

check('fixed_zip_sha', sha(archive_path.read_bytes()) == '1abc164e76abc5e7f59978ae0d3062d07b37bd6edfe55c69335ec3f61318c60f')
check('fixed_zip_size', archive_path.stat().st_size == 778425)
check('v008_zip_preserved', sha(old_archive_path.read_bytes()) == 'ac74a58d6ac1751556751046571d5d983a9dcc4f9f85a146b4494706b055ff1b')
with ZipFile(archive_path) as package, ZipFile(old_archive_path) as old:
    # v009 ZIP 比 v008 多了一层候选目录，按包实际布局解析，不假定同一根布局。
    prefix = 'robot-fixed-rig-v009/'
    read_new = lambda path: package.read(prefix + path)
    entries = [entry for entry in package.infolist() if not entry.is_dir()]
    names = [entry.filename for entry in entries]
    check('entry_count_157_no_duplicate', len(entries) == 157 and len(set(names)) == len(names))
    for entry in entries:
        assert entry.filename.startswith(prefix)
        local_path = entry.filename.removeprefix(prefix)
        data = package.read(entry)
        file = base / local_path
        check('payload:' + entry.filename, file.exists() and sha(file.read_bytes()) == sha(data), sha256=sha(data))
        target = (cold / relative / local_path).resolve()
        assert target.is_relative_to((cold / relative).resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    manifest = read_json(read_new('run-manifest.json'))
    for entry in manifest['evidence']:
        check('manifest_evidence:' + entry['file'], sha(read_new(entry['file'])) == entry['sha256'])
    import_path = 'godot-review/assets/robot_walk_down_atlas_v009.png.import'
    import_config = read_new(import_path).decode('utf-8-sig')
    check('portable_import_parameters_present', 'process/fix_alpha_border=false' in import_config and 'process/premult_alpha=false' in import_config and 'mipmaps/generate=false' in import_config and 'compress/mode=0' in import_config)
    rig = read_json(read_new('source/rig_down_v009.json'))
    old_rig = normalize(read_json(old.read('source/rig_down_v008.json')))
    check('rig_frozen_sha', sha(read_new('source/rig_down_v009.json')) == '2a08e84f86bd3611afad19b1573ff12a844615e2d987aa8053c5a1e3cbb343f3')
    check('rig_canvas_root', rig['canvas'] == [64,96] and rig['root_anchor'] == [32,80])
    check('23_part_definitions_unchanged', rig['parts'] == old_rig['parts'] and len(rig['parts']) == 23)
    check('17_cap_definitions_unchanged', rig['cap_definitions'] == old_rig['cap_definitions'] and len(rig['cap_definitions']) == 17)
    check('keypoints_bones_projection_unchanged', rig['keypoints'] == old_rig['keypoints'] and rig['bones'] == old_rig['bones'] and rig['projection_contract'] == old_rig['projection_contract'])
    rig_changed_paths = differences(old_rig, rig)
    old_renderer = old.read('godot-review/render_fixed_rig_v008.gd').decode('utf-8-sig').replace('v008','v009').replace('V008','V009')
    new_renderer = read_new('godot-review/render_fixed_rig_v009.gd').decode('utf-8-sig')
    (review / 'renderer-version-normalized.diff').write_text(''.join(difflib.unified_diff(old_renderer.splitlines(True),new_renderer.splitlines(True),fromfile='v008-normalized-to-v009',tofile='fixed-v009-renderer')), encoding='utf-8')
    old_verifier = old.read('godot-review/verify_fixed_rig_playback_v008.gd').decode('utf-8-sig').replace('v008','v009').replace('V008','V009')
    check('original_playback_verifier_contract_unchanged', old_verifier == read_new('godot-review/verify_fixed_rig_playback_v009.gd').decode('utf-8-sig'))
    for path in ['source/robot_idle_down_canonical_original.png','source/robot_idle_down_fixed_rig_canonical_v009.png']:
        old_path = path.replace('v009','v008')
        check('frozen_source:' + path, read_new(path) == old.read(old_path))
    for part in rig['parts']:
        local = part['path'].removeprefix('res://art-source/ember/robot-fixed-rig-v009/')
        check('unchanged_source_part:' + part['id'], read_new(local) == old.read(local))
    masks = read_json(read_new('source/part_masks_v009.json'))
    check('source_masks_unchanged', masks == normalize(read_json(old.read('source/part_masks_v008.json'))))
    check('semantic_ledger_unchanged', read_json(read_new('source/part_reassignment_ledger_v009.json')) == normalize(read_json(old.read('source/part_reassignment_ledger_v008.json'))))

def pixels(path):
    image = Image.open(path).convert('RGBA')
    return image, list(image.get_flattened_data())

original, original_pixels = pixels(base / 'source/robot_idle_down_canonical_original.png')
composed = [(0,0,0,0)] * (64*96)
owners = set()
for part in masks['parts']:
    file = workspace / part['path'].removeprefix('res://')
    image, data = pixels(file)
    points = {(index%64,index//64) for index,pixel in enumerate(data) if pixel[3] == 255}
    passed = image.size == (64,96) and set(point for point in points) == {tuple(point) for point in part['pixels']} and not points.intersection(owners) and all(data[y*64+x] == original_pixels[y*64+x] for x,y in points) and sha(file.read_bytes()) == part['png_sha256'] and sha(image.tobytes()) == part['rgba_sha256']
    check('neutral_layer:' + part['id'], passed)
    for x,y in points: composed[y*64+x] = data[y*64+x]
    owners.update(points)
check('1492_neutral_original_rgba_exact', composed == original_pixels and len(owners) == 1492)
atlas, _ = pixels(base / 'robot_walk_down_atlas_v009.png')
check('atlas_frozen_512x96', atlas.size == (512,96) and sha((base / 'robot_walk_down_atlas_v009.png').read_bytes()) == '50669508acd565455c8b0834a4f90c1d93ec5a1ff2a2721da3e4f5ca1d9c51e3')
for entry in manifest['frozen_frames']:
    index = entry['frame']
    file = workspace / entry['file'].removeprefix('res://')
    image, data = pixels(file)
    check('frame:' + str(index), image.size == (64,96) and set(p[3] for p in data) <= {0,255} and sha(file.read_bytes()) == entry['sha256'] and atlas.crop((index*64,0,(index+1)*64,96)).tobytes() == image.tobytes())
    pose = read_json((base / f'poses/walk_down_f{index:02d}_v009.json').read_bytes())
    check('pose_binding:' + str(index), pose['frame_index'] == index and pose['root_anchor'] == [32,80] and pose['source_rig_sha256'] == '2a08e84f86bd3611afad19b1573ff12a844615e2d987aa8053c5a1e3cbb343f3' and pose['keypoints3d']['root'] == [32,80,0])
for name in ['fixed_rig_render_v009.json','fixed_rig_playback_v009.json']:
    report = read_json((base / name).read_bytes())
    for file, expected in report['source_hashes'].items():
        check('report_binding:' + name + ':' + file, sha((workspace / file.removeprefix('res://')).read_bytes()) == expected)
baseline = read_json((workspace / 'art-source/ember/robot-fixed-rig-v007/source/production_baseline_sha256_v007.json').read_bytes())
for entry in baseline['files']:
    check('protected:' + entry['file'], sha(Path(entry['file']).read_bytes()) == entry['sha256'])
failures = [entry for entry in checks if not entry['passed']]
report = {'status':'PASS' if not failures else 'FAIL','check_count':len(checks),'failures':failures,'checks':checks,'zip_sha256':sha(archive_path.read_bytes()),'rig_changed_paths_after_version_normalization':rig_changed_paths,'source_layer_count':23,'cap_count':17,'original_neutral_opaque_count':1492,'protected_count':len(baseline['files']),'fixed_canonical_byte_equal_to_v008':True,'source_and_canonical_reuse_is_not_art_acceptance':True}
(review / 'package-source-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key:value for key,value in report.items() if key != 'checks'}, ensure_ascii=False))
