"""Read-only checks for bridge pixels, original coordinates, ports and layered landings."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[3]
ASSETS = ROOT / 'assets/ember/environment/tilesets'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(mask):
    todo = set(map(tuple, np.argwhere(mask)))
    count = 0
    while todo:
        count += 1
        stack = [todo.pop()]
        while stack:
            y, x = stack.pop()
            for point in [(y-1, x), (y+1, x), (y, x-1), (y, x+1)]:
                if point in todo:
                    todo.remove(point)
                    stack.append(point)
    return count


def edge(a, side):
    return a[0] if side == 'N' else a[-1] if side == 'S' else a[:, 0] if side == 'W' else a[:, -1]


def main():
    checks, failures = [], []
    def check(name, passed, evidence=None):
        checks.append({'name': name, 'passed': bool(passed), 'evidence': evidence})
        if not passed:
            failures.append(name)
    old = json.loads((ASSETS / 'ember_tiles_catalog_v001.json').read_text(encoding='utf-8'))
    new = json.loads((ASSETS / 'ember_tiles_catalog_v002.json').read_text(encoding='utf-8'))
    source_sha, images, tile_map = {}, {}, {}
    for a in new['atlases']:
        path = ROOT / a['texture'].removeprefix('res://')
        source_sha[str(path.relative_to(ROOT)).replace('\\', '/')] = sha(path)
        atlas = np.array(Image.open(path).convert('RGBA'))
        for t in a['tiles']:
            x, y = t['coord']
            images[t['id']] = atlas[y*32:(y+1)*32, x*32:(x+1)*32]
            tile_map[t['id']] = t
    for a in old['atlases']:
        path = ROOT / a['texture'].removeprefix('res://')
        atlas = np.array(Image.open(path).convert('RGBA'))
        same_atlas = next(b for b in new['atlases'] if b['id'] == a['id'])
        check('source_id_preserved_' + a['id'], a['source_id'] == same_atlas['source_id'])
        for t in a['tiles']:
            x, y = t['coord']
            check('legacy_coord_' + t['id'], tile_map[t['id']]['coord'] == t['coord'])
            check('legacy_raw_rgba_' + t['id'], np.array_equal(images[t['id']], atlas[y*32:y*32+32, x*32:x*32+32]))
    palette = {tuple(bytes.fromhex(h)) for h in ['101820', '182631', '2B3E4B', '4D6470', '829BA3', 'BECBC4', '7B4D35', 'B77C4B', 'E2B77A', '51C5C2', 'E5A44B', 'E65B4A', '566B78', '203A4B', '406B78', 'ECE9D8']}
    added = [t for t in tile_map.values() if t['category'] == 'T06S']
    check('exactly_five_new_tiles', len(added) == 5)
    check('total_67_tiles', len(tile_map) == 67)
    for t in added:
        a = images[t['id']]
        mask = a[:, :, 3] != 0
        colors = {tuple(map(int, c)) for c in a[mask, :3]}
        check(t['id'] + '_32x32', a.shape == (32, 32, 4))
        check(t['id'] + '_binary_alpha', set(np.unique(a[:, :, 3])) == {0, 255})
        check(t['id'] + '_registered_palette', colors <= palette, sorted(colors))
        check(t['id'] + '_transparent_rgb_zero', bool((a[~mask, :3] == 0).all()))
        check(t['id'] + '_one_connected_component', components(mask) == 1)
        for side, spec in t['interfaces'].items():
            actual = edge(a, side)
            declared = set(k for start, end in spec['ports'] for k in range(start, end)) if spec else set()
            check(t['id'] + '_physical_port_' + side, declared == set(np.flatnonzero(actual[:, 3])), {'actual_indices': np.flatnonzero(actual[:, 3]).tolist(), 'declared_indices': sorted(declared)})
    # Only equal kinds and physical sections can connect; this is not arbitrary Terrain coverage.
    bridges = [t for t in tile_map.values() if t['category'] in ['T06', 'T06S']]
    pairs = []
    for first in bridges:
        for side, other in [('E', 'W'), ('S', 'N')]:
            port = first['interfaces'][side]
            if not port:
                continue
            for second in bridges:
                right = second['interfaces'][other]
                if not right or port['kind'] != right['kind'] or port['ports'] != right['ports']:
                    continue
                a, b = edge(images[first['id']], side), edge(images[second['id']], other)
                alpha_equal = np.array_equal(a[:, 3], b[:, 3])
                rgba_equal = np.array_equal(a, b)
                check('pair_alpha_' + first['id'] + side + second['id'], alpha_equal)
                pairs.append({'first': first['id'], 'side': side, 'second': second['id'], 'alpha_equal': alpha_equal, 'rgba_equal': rgba_equal})
    for t in ['bridge_edge_h_s', 'bridge_edge_v_e']:
        a = images[t]
        light, dark = (a[20, 0, :3], a[25, 0, :3]) if t.endswith('_s') else (a[0, 20, :3], a[0, 25, :3])
        check(t + '_world_upper_left_highlight', tuple(light) == tuple(bytes.fromhex('829BA3')) and tuple(dark) == tuple(bytes.fromhex('101820')))
    cases = json.loads((BASE / 'layout-cases.json').read_text(encoding='utf-8'))['cases']
    for case in cases:
        layers = {l['name']: l['cells'] for l in case['layers']}
        ground_cells = {tuple(c['cell']) for c in layers['Ground']}
        decks = {tuple(c['cell']): c['id'] for c in layers['Deck']}
        beams = [{tuple(c['cell']) for c in layers[name]} for name in ['BeamUpperLeft', 'BeamLowerRight']]
        check(case['id'] + '_two_beams_same_cell', beams[0] == beams[1] and len(beams[0]) == 3)
        check(case['id'] + '_both_beams_over_deck', all(decks.get(p) in ['bridge_deck_h', 'bridge_deck_v'] for p in beams[0]))
        caps = {tuple(c['cell']) for c in layers['Deck'] if c['id'].startswith('bridge_end')}
        check(case['id'] + '_both_caps_supported_by_land', caps <= ground_cells and len(caps) == 2)
        check(case['id'] + '_five_explicit_layers', len(layers) == 5)
        native = np.array(Image.open(BASE / 'review' / (case['id'] + '_native.png')).convert('RGBA'))
        for cell in layers['Deck']:
            x, y = cell['cell']
            check(case['id'] + '_solid_walk_section_' + str(cell['cell']), bool((native[y*32+12:y*32+20, x*32+12:x*32+20, 3] == 255).all()))
    protected = json.loads((BASE / 'protected-before.json').read_text(encoding='utf-8'))
    for path, expected in protected.items():
        check('protected_' + path, sha(ROOT / path) == expected)
    report = {'status': 'PIXEL_MEASUREMENTS_PASS' if not failures else 'FAIL', 'checks': checks,
              'check_count': len(checks), 'failures': failures, 'source_sha256': source_sha,
              'catalog_sha256': sha(ASSETS / 'ember_tiles_catalog_v002.json'),
              'new_tiles': 5, 'preserved_structure_cells': 26, 'preserved_all_legacy_cells': 62,
              'legal_directed_connections': pairs,
              'scope': 'Raw PNG, ports, palette, old coordinates and explicit two-layer beams/landings; visual and GPU conclusions separate.'}
    (BASE / 'pixel-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'checks': len(checks), 'failures': failures, 'connections': len(pairs)}, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
