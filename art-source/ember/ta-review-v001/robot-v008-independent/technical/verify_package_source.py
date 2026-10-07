import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
from PIL import Image

WORKSPACE = Path('E:/dev/shader/godot-shader/godot-shader-simple')
BASE_REL = Path('art-source/ember/robot-fixed-rig-v008')
BASE = WORKSPACE / BASE_REL
REVIEW = WORKSPACE / 'art-source/ember/ta-review-v001/robot-v008-independent/technical'
COLD = REVIEW / 'cold-workspace'
ARCHIVE = WORKSPACE / 'art-source/ember/deliveries/robot_fixed_rig_v008_walk_down_candidate_2026-10-06.zip'
checks = []

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def check(scope, name, ok, **details):
    checks.append(dict(scope=scope, name=name, passed=bool(ok), **details))

def pixels(path):
    image = Image.open(path).convert('RGBA')
    return image, list(image.getdata())

check('package', 'frozen_sha256', sha(ARCHIVE.read_bytes()) == 'ac74a58d6ac1751556751046571d5d983a9dcc4f9f85a146b4494706b055ff1b', bytes=ARCHIVE.stat().st_size)
with ZipFile(ARCHIVE) as archive:
    files = [entry for entry in archive.infolist() if not entry.is_dir()]
    check('package', 'entry_count_144', len(files) == 144, count=len(files))
    for entry in files:
        target = (COLD / BASE_REL / entry.filename).resolve()
        if not target.is_relative_to((COLD / BASE_REL).resolve()):
            raise ValueError('Archive path escapes review directory')
        contents = archive.read(entry)
        current = BASE / entry.filename
        check('package_payload', entry.filename, current.exists() and sha(current.read_bytes()) == sha(contents), sha256=sha(contents))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(contents)

manifest = read_json(BASE / 'run-manifest.json')
rig = read_json(BASE / 'source/rig_down_v008.json')
masks = read_json(BASE / 'source/part_masks_v008.json')
ledger = read_json(BASE / 'source/part_reassignment_ledger_v008.json')
original, original_pixels = pixels(BASE / 'source/robot_idle_down_canonical_original.png')
rig_sha = sha((BASE / 'source/rig_down_v008.json').read_bytes())
check('binding', 'rig_frozen_sha', rig_sha == 'e11638a6751cdaab475224cea772aa80425066daadcfab6e71436f84fd1341a4')
check('binding', 'original_mother_sha', sha((BASE / 'source/robot_idle_down_canonical_original.png').read_bytes()) == manifest['source']['original_sha256'])
check('source', 'original_opaque_1492', sum(pixel[3] == 255 for pixel in original_pixels) == 1492)
check('rig', 'canvas_root_and_counts', rig['canvas'] == [64,96] and rig['root_anchor'] == [32,80] and len(rig['parts']) == 23 and len(rig['cap_definitions']) == 17)

for report_name in ['fixed_rig_render_v008.json', 'fixed_rig_playback_v008.json']:
    report = read_json(BASE / report_name)
    for name, expected in report['source_hashes'].items():
        source = WORKSPACE / name.removeprefix('res://')
        check('report_source_binding', report_name + ':' + name, source.exists() and sha(source.read_bytes()) == expected)

atlas, atlas_pixels = pixels(BASE / 'robot_walk_down_atlas_v008.png')
check('atlas', '512x96', atlas.size == (512,96))
for entry in manifest['frozen_frames']:
    index = entry['frame']
    file = WORKSPACE / entry['file'].removeprefix('res://')
    image, data = pixels(file)
    region = atlas.crop((index*64, 0, (index+1)*64, 96))
    check('frame', str(index), image.size == (64,96) and set(pixel[3] for pixel in data) <= {0,255} and sha(file.read_bytes()) == entry['sha256'] and region.tobytes() == image.tobytes(), binary_alpha=True, opaque_pixels=sum(p[3] == 255 for p in data), rgba_sha256=sha(image.tobytes()))
    pose = read_json(BASE / f'poses/walk_down_f{index:02d}_v008.json')
    check('pose', str(index), pose['frame_index'] == index and pose['root_anchor'] == [32,80] and pose['source_rig_sha256'] == rig_sha)

composed = [(0,0,0,0)] * (64*96)
owners = {}
for part in masks['parts']:
    file = WORKSPACE / part['path'].removeprefix('res://')
    image, data = pixels(file)
    specified = {tuple(point) for point in part['pixels']}
    actual = {(i % 64, i // 64) for i, pixel in enumerate(data) if pixel[3] == 255}
    overlap = actual.intersection(owners)
    same_source = all(data[y*64+x] == original_pixels[y*64+x] for x,y in actual)
    ok = image.size == (64,96) and actual == specified and not overlap and same_source and sha(file.read_bytes()) == part['png_sha256'] and sha(image.tobytes()) == part['rgba_sha256']
    check('source_layer', part['id'], ok, pixel_count=len(actual), overlap_count=len(overlap))
    for point in actual:
        owners[point] = part['id']
        composed[point[1]*64+point[0]] = data[point[1]*64+point[0]]
check('source', '23_layers_recompose_original_rgba', composed == original_pixels and len(owners) == 1492, owned_pixel_count=len(owners), composed_rgba_sha256=sha(bytes(channel for pixel in composed for channel in pixel)))

v007_file = WORKSPACE / 'art-source/ember/robot-fixed-rig-v007/source/part_masks_v007.json'
v007 = read_json(v007_file)
check('provenance', 'v007_masks_bound', sha(v007_file.read_bytes()) == ledger['source_v007_masks_sha256'])
old_owners = {tuple(point): part['id'] for part in v007['parts'] for point in part['pixels']}
changes = {point: (old_owners.get(point), owner) for point,owner in owners.items() if old_owners.get(point) != owner}
declared = {tuple(entry['pixel']): (entry['from_part'],entry['to_part']) for entry in ledger['semantic_reassignment_ledger']}
check('provenance', '37_semantic_changes_only', changes == declared and len(changes) == 37 and len(old_owners) == len(owners), reassigned_pixel_count=len(changes))
check('provenance', 'ledger_rgba_is_original', all(tuple(entry['rgba']) == original_pixels[entry['pixel'][1]*64+entry['pixel'][0]] for entry in ledger['semantic_reassignment_ledger']))

canonical, canonical_pixels = pixels(BASE / 'source/robot_idle_down_fixed_rig_canonical_v008.png')
check('canonical', 'derived_hash_binary_alpha', sha((BASE / 'source/robot_idle_down_fixed_rig_canonical_v008.png').read_bytes()) == read_json(BASE / 'fixed_rig_render_v008.json')['canonical']['sha256'] and canonical.size == (64,96) and set(pixel[3] for pixel in canonical_pixels) <= {0,255})
canonical_difference = sum(a != b for a,b in zip(original_pixels, canonical_pixels))

baseline_path = WORKSPACE / 'art-source/ember/robot-fixed-rig-v007/source/production_baseline_sha256_v007.json'
baseline = read_json(baseline_path)
for entry in baseline['files']:
    file = Path(entry['file'])
    check('production_protection', str(file), file.exists() and sha(file.read_bytes()) == entry['sha256'])

failures = [entry for entry in checks if not entry['passed']]
report = dict(status='PASS' if not failures else 'FAIL', check_count=len(checks), failure_count=len(failures), failures=failures, checks=checks, protected_file_count=len(baseline['files']), canonical_original_rgba_difference_count=canonical_difference, canonical_opaque_pixels=sum(p[3] == 255 for p in canonical_pixels), semantic_reassignment_count=len(changes), source_layer_count=len(masks['parts']), authored_cap_count=len(rig['cap_definitions']), art_acceptance='NOT_CLAIMED', limitation='1492 original RGBA exactness applies to neutral 23 source layers; rig-derived fixed canonical includes authored geometry/projection and is not original-mother pixel equality.')
(REVIEW / 'package-source-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key: value for key,value in report.items() if key not in ['checks','failures']}, ensure_ascii=False))
if failures:
    print(json.dumps(failures, ensure_ascii=False))
