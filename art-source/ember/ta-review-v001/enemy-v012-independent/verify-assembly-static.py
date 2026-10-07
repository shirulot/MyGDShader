"""Read-only package/resource binding audit; writes evidence only beside this script."""
from pathlib import Path
from io import BytesIO
from collections import Counter
import hashlib
import json
import re
import zipfile
from PIL import Image

BASE = Path('E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/enemy-sequences-v012')
OUT = Path(__file__).resolve().parent
recipe_raw = (BASE / 'assembly_recipe.json').read_bytes()
recipe = json.loads(recipe_raw)
sha = lambda value: hashlib.sha256(value).hexdigest()
expected_sources = {
    'enemy_patrol_actions_v008_2026-10-06.zip': '4a3ab26e04abb5816c505fb0c0f851b8042886d8ea3d2b8516b1923360af74b4',
    'enemy_heavy_actions_v007_2026-10-06.zip': '05350a58ef0a0e44ee19c3c6af69a2f38048f4e1c5d4ce24afae5076ece14494',
    'enemy_heavy_actions_v009_2026-10-06.zip': '329e2fb60b0e7930a5178e92b4fe014e526bc5aa771f1a8b53e69eee8b15bf18',
    'enemy_cutter_actions_v010_r1_2026-10-06.zip': 'c154a145e56aa10cd6394507350a47dc21ead655915c73e7f74131e146f9f948',
    'enemy_drone_actions_v011_2026-10-06.zip': '13a4942d34d0ceabac7473c1689aa4784bc0c6f1555ff68817ed9d93159dab3e',
}
expected_timing = {'idle_down': (4, 4, True), 'move_down': (8, 8, True),
                   'attack_down': (6, 10, False), 'hit_down': (4, 12, False),
                   'death_down': (8, 10, False)}
result = {'scope': 'static assembly binding only, no engine/art rerun',
          'recipe_sha256': sha(recipe_raw), 'sources': [], 'clips': [], 'runtime_records': [], 'bindings': []}
archives = {}
catalogs = {}
for name, expected in expected_sources.items():
    file = BASE / 'reviewed_packages' / name
    actual = sha(file.read_bytes())
    assert actual == expected
    archive = zipfile.ZipFile(file)
    archives[name] = archive
    cats = [n for n in archive.namelist() if re.fullmatch(r'output/catalog[^/]*\.json', n)]
    assert len(cats) == 1
    catalogs[name] = json.loads(archive.read(cats[0]))
    result['sources'].append({'name': name, 'sha256': actual, 'catalog': cats[0]})

# Decode the actual saved SpriteFrames' embedded RGBA images and atlas regions.
resources = {}
for unit in sorted({c['unit'] for c in recipe['clips']}):
    path = BASE / 'output' / (unit + '.tres')
    text = path.read_text(encoding='utf-8')
    blocks = {m.group(2): (m.group(1), m.group(3)) for m in re.finditer(
        r'^\[sub_resource type="([^"]+)" id="([^"]+)"\]\n(.*?)(?=^\[|\Z)', text, re.M | re.S)}
    images = {}
    textures = {}
    regions = {}
    for ident, (kind, block) in blocks.items():
        if kind == 'Image':
            assert '"format": "RGBA8"' in block and '"mipmaps": false' in block
            width = int(re.search(r'"width": (\d+)', block).group(1))
            height = int(re.search(r'"height": (\d+)', block).group(1))
            packed = re.search(r'PackedByteArray\((.*?)\)', block, re.S).group(1)
            raw = bytes(map(int, packed.split(',')))
            assert len(raw) == width * height * 4
            images[ident] = Image.frombytes('RGBA', (width, height), raw)
        elif kind == 'ImageTexture':
            textures[ident] = re.search(r'image = SubResource\("([^"]+)"\)', block).group(1)
        elif kind == 'AtlasTexture':
            atlas = re.search(r'atlas = SubResource\("([^"]+)"\)', block).group(1)
            rect = tuple(int(float(x)) for x in re.search(r'region = Rect2\((.*?)\)', block).group(1).split(','))
            regions[ident] = (atlas, rect)
    payload = text.split('animations = ', 1)[1].strip()
    payload = re.sub(r'SubResource\("([^"]+)"\)', r'"\1"', payload).replace('&"', '"')
    animations = json.loads(payload)
    assert len(animations) == 5 and len({a['name'] for a in animations}) == 5
    resources[unit] = (images, textures, regions, {a['name']: a for a in animations})
    result['bindings'].append({'path': path.relative_to(BASE).as_posix(), 'sha256': sha(path.read_bytes()),
                               'embedded_images': len(images), 'atlas_regions': len(regions)})

keys = [(c['unit'], c['action']) for c in recipe['clips']]
assert len(keys) == 20 and len(set(keys)) == 20
assert recipe['root'] == [64, 104] and recipe['canvas'] == [128, 128]
for clip in recipe['clips']:
    unit, action, name = clip['unit'], clip['action'], clip['reviewed_zip']
    source = catalogs[name]
    assert source['root'] == [64, 104] and source['canvas'] == [128, 128]
    spec = source['actions'][action]
    timing = (clip['frame_count'], clip['fps'], bool(clip['loop']))
    assert timing == expected_timing[action] == (spec['frame_count'], spec['fps'], bool(spec['loop']))
    assert clip['reviewed_zip_sha256'] == expected_sources[name]
    atlas_path = BASE / clip['atlas'].removeprefix('res://')
    source_atlas = archives[name].read(spec['atlas'].removeprefix('res://'))
    assert atlas_path.read_bytes() == source_atlas
    assert sha(source_atlas) == clip['atlas_sha256'] == spec['atlas_sha256']
    images, textures, regions, animations = resources[unit]
    animation = animations[action]
    assert (len(animation['frames']), animation['speed'], bool(animation['loop'])) == timing
    decoded = []
    for i, frame in enumerate(animation['frames']):
        source_name = f'output/{action}/f{i:02}.png'
        original = archives[name].read(source_name)
        saved = BASE / 'output' / unit / action / f'f{i:02}.png'
        assert saved.read_bytes() == original
        assert sha(original) == clip['frame_hashes'][i] == spec['frame_hashes'][i]
        atlas_id, (x, y, w, h) = regions[frame['texture']]
        assert frame['duration'] == 1.0 and (x, y, w, h) == (i * 128, 0, 128, 128)
        raw = images[textures[atlas_id]].crop((x, y, x + w, y + h)).tobytes()
        actual = Image.open(BytesIO(original)).convert('RGBA')
        assert actual.size == (128, 128) and raw == actual.tobytes()
        decoded.append({'frame': i, 'png_sha256': sha(original), 'decoded_rgba_sha256': sha(raw)})
    result['clips'].append({'unit': unit, 'action': action, 'source_zip': name, 'atlas_sha256': sha(source_atlas),
                            'fps': timing[1], 'loop': timing[2], 'decoded_frames': decoded})
    result['bindings'].append({'path': atlas_path.relative_to(BASE).as_posix(), 'sha256': sha(source_atlas)})

# Verify the existing log's completeness and recipe binding; do not claim a new runtime observation.
runtime = json.loads((BASE / 'qa/assembly_runtime.json').read_bytes())
integrity = json.loads((BASE / 'qa/assembly_integrity.json').read_bytes())
assert runtime['recipe_sha256'] == integrity['recipe_sha256'] == result['recipe_sha256']
for clip in recipe['clips']:
    for speed in ['normal', 'slow']:
        key = f"{clip['unit']}/{clip['action']}/{speed}"
        assert sorted(runtime['seen'][key]) == list(range(clip['frame_count']))
        assert len(runtime['seen'][key]) == clip['frame_count']
        loops, finished = runtime['loops'][key], runtime['finished'][key]
        assert (loops >= 1 and finished == 0) if clip['loop'] else (finished >= 1 and loops == 0)
        result['runtime_records'].append({'key': key, 'seen': runtime['seen'][key], 'loops': loops, 'finished': finished})
assert len(runtime['seen']) == len(runtime['loops']) == len(runtime['finished']) == 40
preview = (BASE / 'preview.gd').read_text(encoding='utf-8')
assert 'sprite.centered=false' in preview and 'sprite.offset=Vector2(-64,-104)' in preview
assert 'texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST' in preview
for item in ['project.godot', 'preview.tscn', 'preview.gd', 'build.gd', 'capture.gd', 'assembly_recipe.json',
             'TA_ACCEPTANCE.json', 'qa/assembly_integrity.json', 'qa/assembly_runtime.json', 'qa/assembly_runtime.png']:
    path = BASE / item
    result['bindings'].append({'path': item, 'sha256': sha(path.read_bytes())})
for archive in archives.values():
    archive.close()
result['counts'] = {'clips': 20, 'png_frames': 120, 'atlases': 20, 'resources': 4, 'decoded_rgba_frames': 120,
                    'existing_runtime_records': 40, 'missing_clips': 0, 'duplicate_clip_keys': 0}
result['status'] = 'PASS_STATIC_ASSEMBLY_BINDING_ONLY'
(OUT / 'assembly-binding.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({'status': result['status'], 'counts': result['counts'], 'recipe_sha256': result['recipe_sha256']}))
