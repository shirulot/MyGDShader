"""Read frozen H19 pixels and bind localized visual findings; no production edits."""
from pathlib import Path
from PIL import Image
import hashlib
import json

base = Path(__file__).resolve().parent
package = base / 'visual-package'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
frame = lambda action, n: Image.open(package / f'output/enemy_tracked_heavy/{action}/f{n:02}.png').convert('RGBA')
sw_source = Image.open(package / 'source/down_left.png').convert('RGBA')
hidden_source = Image.open(package / 'source/hidden_chassis_eight_views_v001.png').convert('RGBA')
sw = []
for n in [3, 4, 5, 6, 7]:
    im = frame('death_down_left', n)
    positions = [(46, 88), (46, 89)] if n == 5 else [(46, 89), (46, 90)]
    row = {'frame': n, 'points': [{'xy': list(p), 'rgba': list(im.getpixel(p))} for p in positions]}
    if n >= 4:
        row['source_points'] = [{'xy': [46, y], 'rgba': list(sw_source.getpixel((46, y)))} for y in [76, 77]]
        row['rgba_equals_source'] = all(im.getpixel(p) == sw_source.getpixel((46, y)) for p, y in zip(positions, [76, 77]))
        assert row['rgba_equals_source']
    sw.append(row)
east = []
for n in range(6):
    im = frame('attack_right', n)
    east.append({'frame': n, 'points': [{'xy': list(p), 'rgba': list(im.getpixel(p))} for p in [(98, 83), (98, 84)]]})
hidden = [{'xy': list(p), 'raw_rgba': list(hidden_source.getpixel(p))} for p in [(1131, 703), (1131, 705)]]
assert all(tuple(x['raw_rgba'][:3]) == frame('attack_right', 3).getpixel(p)[:3] for x, p in zip(hidden, [(98, 83), (98, 84)]))
bound = {}
for name in ['technical-sw-death-receiver-ownership.json', 'technical-east-muzzle-ownership.json', 'root-browser-attack-e-f03.png', 'visual-detail-death_down_left-light-8x.png', 'visual-detail-death_down_left-dark-8x.png', 'visual-detail-attack_right-dark-6x.png', 'visual-detail-attack_right-light-6x.png', 'visual-detail-attack_left-dark-6x.png']:
    path = base / name
    assert path.exists()
    bound[name] = sha(path)
out = {
    'status': 'NEEDS_REVISION',
    'coordinate_contract': '128x128 original frame coordinates; zero based f00; no bbox registration',
    'sw_death': sw,
    'east_attack': east,
    'east_hidden_socket_raw_source': hidden,
    'bound_cross_review_evidence_sha256': bound,
    'scope': 'Own read-only exact pixel checks; peer ownership trace and root browser evidence bound separately, not claimed as own execution.'
}
(base / 'visual-local-observations.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print('Bound 2 local visual findings; SW source RGBA and E hidden-source RGB independently confirmed.')
