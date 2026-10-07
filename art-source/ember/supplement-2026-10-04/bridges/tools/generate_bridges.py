"""Extend the editable native bridge recipe, preserving the published v001 atlas.

No published raster is mirrored, recolored, or repaired. The five additions are
drawn on their native pixel grid from the existing code recipe. Cropping and
compositing below only package unchanged accepted cells and make QA boards.
"""
from pathlib import Path
import ast
import copy
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[3]
OLD = ROOT / 'art-source/ember/tilesets-v001'
ASSETS = ROOT / 'assets/ember/environment/tilesets'
SOURCE = OLD / 'tools/finish_structures.py'
OUT = BASE / 'finished-tiles'
REVIEW = BASE / 'review'
CATALOG = ASSETS / 'ember_tiles_catalog_v002.json'
PALETTE = ['101820', '182631', '2B3E4B', '4D6470', '829BA3', 'BECBC4',
           '7B4D35', 'B77C4B', 'E2B77A', '51C5C2', 'E5A44B', 'E65B4A',
           '566B78', '203A4B', '406B78', 'ECE9D8']
C = [tuple(bytes.fromhex(h)) + (255,) for h in PALETTE]
EMPTY = (0, 0, 0, 0)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def native_helpers():
    """Execute only read-only pixel helpers, excluding the old module's exports."""
    names = {'px', 'rect', 'line', 'nearest', 'source_patch', 'bolt'}
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in functions} == names
    space = {'Image': Image, 'ImageDraw': ImageDraw, 'BASE': OLD,
             'C': C, 'EMPTY': EMPTY, 'STEEL': [0, 1, 2, 3, 4, 5, 12]}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(SOURCE), 'exec'), space)
    return space


H = native_helpers()
px, rect, line, bolt = [H[n] for n in ['px', 'rect', 'line', 'bolt']]
MATERIAL = H['source_patch']('bridge_module_master_v001.png', (277, 258, 977, 983), (24, 24), [2, 3, 12])


def deck(vertical):
    """Reproduce the editable v001 deck geometry, with world upper-left shading."""
    im = Image.new('RGBA', (32, 32), EMPTY)
    rect(im, (4, 0, 27, 31) if vertical else (0, 4, 31, 27), 3)
    im.paste(MATERIAL, (4, 4))
    if vertical:
        for x, color in [(4, 4), (5, 3), (26, 2), (27, 0)]:
            line(im, [(x, 0), (x, 31)], color)
        for y in [8, 20]:
            rect(im, (9, y, 22, y + 3), 0)
            line(im, [(10, y + 1), (21, y + 1)], 1)
            line(im, [(10, y + 3), (21, y + 3)], 4)
        bolt(im, 5, 14)
        bolt(im, 24, 14)
        for y in [0, 1, 30, 31]:
            for x in range(6, 26):
                px(im, x, y, 3)
    else:
        for y, color in [(4, 4), (5, 3), (26, 2), (27, 0)]:
            line(im, [(0, y), (31, y)], color)
        for x in [8, 20]:
            rect(im, (x, 9, x + 3, 22), 0)
            line(im, [(x + 1, 10), (x + 1, 21)], 1)
            line(im, [(x + 3, 10), (x + 3, 21)], 4)
        bolt(im, 14, 5)
        bolt(im, 14, 24)
        for x in [0, 1, 30, 31]:
            for y in range(6, 26):
                px(im, x, y, 3)
    return im


def edge(side):
    im = Image.new('RGBA', (32, 32), EMPTY)
    if side == 'S':
        rect(im, (0, 20, 31, 25), 2)
        line(im, [(0, 20), (31, 20)], 4)
        line(im, [(0, 25), (31, 25)], 0)
        bolt(im, 8, 22)
        bolt(im, 24, 22)
    else:
        rect(im, (20, 0, 25, 31), 2)
        line(im, [(20, 0), (20, 31)], 4)
        line(im, [(25, 0), (25, 31)], 0)
        bolt(im, 22, 8)
        bolt(im, 22, 24)
    return im


def cap(side):
    im = deck(side in 'NS')
    # A closed end has no external port. Open ends retain the old 24px section.
    if side == 'W':
        rect(im, (0, 4, 3, 27), None)
        rect(im, (4, 4, 6, 27), 0)
        line(im, [(4, 5), (4, 26)], 4)
        bolt(im, 6, 7, True)
        bolt(im, 6, 22, True)
    elif side == 'N':
        rect(im, (4, 0, 27, 3), None)
        rect(im, (4, 4, 27, 6), 0)
        line(im, [(5, 4), (26, 4)], 4)
        bolt(im, 7, 6, True)
        bolt(im, 22, 6, True)
    else:
        rect(im, (4, 28, 27, 31), None)
        rect(im, (4, 25, 27, 27), 0)
        line(im, [(5, 25), (26, 25)], 4)
        bolt(im, 7, 23, True)
        bolt(im, 22, 23, True)
    return im


def port(kind, begin, end):
    return {'kind': kind, 'ports': [[begin, end]], 'alpha_at_ports': 'opaque', 'exact_edge_required': False}


def interfaces(tile_id):
    result = dict.fromkeys('NESW')
    if tile_id == 'bridge_edge_h_s':
        for side in 'EW':
            result[side] = port('bridge-edge-h-s-v002', 20, 26)
    elif tile_id == 'bridge_edge_v_e':
        for side in 'NS':
            result[side] = port('bridge-edge-v-e-v002', 20, 26)
    else:
        closed = tile_id[-1].upper()
        side = {'W': 'E', 'N': 'S', 'S': 'N'}[closed]
        result[side] = port('bridge-deck-h-v001' if closed == 'W' else 'bridge-deck-v-v001', 4, 28)
    return result


def layouts():
    """Explicit layer cases: end caps overlap land; two beam layers overlap decks."""
    cases = []
    for orientation in ['horizontal', 'vertical']:
        width, height = (7, 5) if orientation == 'horizontal' else (5, 7)
        ground, shore, body, upper, lower = [], [], [], [], []
        for y in range(height):
            for x in range(width):
                land = x in [0, 1, 5, 6] if orientation == 'horizontal' else y in [0, 1, 5, 6]
                if land:
                    ground.append({'id': 'floor_clean', 'cell': [x, y]})
        left, right, top, bottom = (1, 5, 0, 4) if orientation == 'horizontal' else (0, 4, 1, 5)
        for x in range(left + 1, right):
            shore.extend([{'id': 'channel_edge_s', 'cell': [x, top]}, {'id': 'channel_edge_n', 'cell': [x, bottom]}])
        for y in range(top + 1, bottom):
            shore.extend([{'id': 'channel_edge_e', 'cell': [left, y]}, {'id': 'channel_edge_w', 'cell': [right, y]}])
        shore.extend([{'id': 'channel_inner_se', 'cell': [left, top]},
                      {'id': 'channel_inner_sw', 'cell': [right, top]},
                      {'id': 'channel_inner_ne', 'cell': [left, bottom]},
                      {'id': 'channel_inner_nw', 'cell': [right, bottom]}])
        if orientation == 'horizontal':
            body = [{'id': 'bridge_end_cap_w', 'cell': [1, 2]}, {'id': 'bridge_end_cap', 'cell': [5, 2]}]
            for x in range(2, 5):
                body.append({'id': 'bridge_deck_h', 'cell': [x, 2]})
                upper.append({'id': 'bridge_edge_h', 'cell': [x, 2]})
                lower.append({'id': 'bridge_edge_h_s', 'cell': [x, 2]})
        else:
            body = [{'id': 'bridge_end_cap_n', 'cell': [2, 1]}, {'id': 'bridge_end_cap_s', 'cell': [2, 5]}]
            for y in range(2, 5):
                body.append({'id': 'bridge_deck_v', 'cell': [2, y]})
                upper.append({'id': 'bridge_edge_v', 'cell': [2, y]})
                lower.append({'id': 'bridge_edge_v_e', 'cell': [2, y]})
        cases.append({'id': orientation, 'size_cells': [width, height], 'background_rgba': list(C[13]),
                      'layers': [{'name': 'Ground', 'cells': ground}, {'name': 'Shore', 'cells': shore},
                                 {'name': 'Deck', 'cells': body}, {'name': 'BeamUpperLeft', 'cells': upper},
                                 {'name': 'BeamLowerRight', 'cells': lower}]})
    return cases


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    REVIEW.mkdir(parents=True, exist_ok=True)
    protected = [ASSETS / 'structures_v001.png', ASSETS / 'ember_tiles_catalog_v001.json',
                 ASSETS / 'structures_tileset_v001.tres', ASSETS / 'ember_common_tileset_v001.tres',
                 ROOT / 'project.godot', SOURCE, OLD / 'generated/bridge_module_master_v001.png']
    before = {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in protected}
    baseline_path = BASE / 'protected-before.json'
    if baseline_path.exists():
        assert json.loads(baseline_path.read_text(encoding='utf-8')) == before
    else:
        dump(baseline_path, before)
    old_catalog = json.loads((ASSETS / 'ember_tiles_catalog_v001.json').read_text(encoding='utf-8'))
    catalog = copy.deepcopy(old_catalog)
    catalog['status'] = 'NATIVE_SUPPLEMENT_GENERATED_PENDING_REVIEW'
    catalog['version'] = 'v002'
    catalog['supplement'] = {'added_units': 5, 'legacy_units': 62, 'total_units': 67,
                             'source': str(BASE.relative_to(ROOT)).replace('\\', '/'),
                             'approval_report': 'art-source/ember/supplement-2026-10-04/bridges/acceptance.json'}
    structure = next(a for a in catalog['atlases'] if a['id'] == 'structures')
    atlas = Image.open(ASSETS / 'structures_v001.png').convert('RGBA')
    # Prove code recipe equivalence before extending it, without invoking old exporters.
    old_tiles = {t['id']: t for t in structure['tiles']}
    for tile_id, vertical in [('bridge_deck_h', False), ('bridge_deck_v', True)]:
        x, y = old_tiles[tile_id]['coord']
        assert deck(vertical).tobytes() == atlas.crop((x*32, y*32, x*32+32, y*32+32)).tobytes(), tile_id
    additions = [('bridge_edge_h_s', '下边梁', edge('S')),
                 ('bridge_edge_v_e', '右边梁', edge('E')),
                 ('bridge_end_cap_w', '左封口', cap('W')),
                 ('bridge_end_cap_n', '上封口', cap('N')),
                 ('bridge_end_cap_s', '下封口', cap('S'))]
    records = []
    for i, (tile_id, name, image) in enumerate(additions):
        coord = [i+2, 3]
        assert not atlas.crop((coord[0]*32, 96, coord[0]*32+32, 128)).getbbox()
        output = OUT / (tile_id + '_v002.png')
        image.save(output)
        atlas.paste(image, (coord[0]*32, 96))
        record = {'id': tile_id, 'name': name, 'category': 'T06S', 'variant': tile_id.removeprefix('bridge_'),
                  'alpha_mode': 'binary', 'status': 'NATIVE_GENERATED_PENDING_REVIEW', 'coord': coord,
                  'interfaces': interfaces(tile_id), 'native_size': [32, 32], 'sha256': sha(output),
                  'source_file': str(output.relative_to(ROOT)).replace('\\', '/'),
                  'pixel_finish_record': 'art-source/ember/supplement-2026-10-04/bridges/production-record.json',
                  'layout_topology': {'overlay_on_deck': tile_id.startswith('bridge_edge'),
                                      'closed_side': tile_id[-1].upper() if tile_id.startswith('bridge_end') else None,
                                      'ground_under_closed_end': tile_id.startswith('bridge_end')},
                  'source_use': 'EXISTING_EDITABLE_NATIVE_RECIPE_EXTENDED_UPPER_LEFT_RELIT'}
        structure['tiles'].append(record)
        records.append(record)
    output_atlas = ASSETS / 'structures_v002.png'
    atlas.save(output_atlas)
    structure['texture'] = 'res://assets/ember/environment/tilesets/structures_v002.png'
    structure['sha256'] = sha(output_atlas)
    structure['size'] = list(atlas.size)
    structure['status'] = 'NATIVE_SUPPLEMENT_GENERATED_PENDING_REVIEW'
    dump(CATALOG, catalog)
    assert before == {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in protected}
    cases = layouts()
    dump(BASE / 'layout-cases.json', {'scope': 'EXPLICIT_LAYERED_HORIZONTAL_AND_VERTICAL_BRIDGES', 'cases': cases})
    tiles = {}
    for a in catalog['atlases']:
        source = Image.open(ROOT / a['texture'].removeprefix('res://')).convert('RGBA')
        for tile in a['tiles']:
            x, y = tile['coord']
            tiles[tile['id']] = source.crop((x*32, y*32, x*32+32, y*32+32))
    for case in cases:
        w, h = case['size_cells']
        board = Image.new('RGBA', (w*32, h*32), tuple(case['background_rgba']))
        for layer in case['layers']:
            for cell in layer['cells']:
                x, y = cell['cell']
                board.alpha_composite(tiles[cell['id']], (x*32, y*32))
        board.save(REVIEW / (case['id'] + '_native.png'))
        board.resize((board.width*4, board.height*4), Image.Resampling.NEAREST).save(REVIEW / (case['id'] + '_4x.png'))
    contact = Image.new('RGB', (5*144+16, 172), '#607079')
    draw = ImageDraw.Draw(contact)
    font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 12)
    for i, (tile_id, name, image) in enumerate(additions):
        contact.paste(image.resize((128, 128), Image.Resampling.NEAREST), (i*144+8, 8), image.resize((128, 128), Image.Resampling.NEAREST))
        draw.text((i*144+8, 144), ['beam S', 'beam E', 'cap W', 'cap N', 'cap S'][i], fill='#ece9d8', font=font)
    contact.save(REVIEW / 'new_five_4x.png')
    atlas.resize((1024, 512), Image.Resampling.NEAREST).save(REVIEW / 'structures_v002_4x.png')
    dump(BASE / 'production-record.json', {'status': 'NATIVE_GENERATED_PENDING_VISUAL_AND_GODOT_REVIEW',
          'added_units': 5, 'old_cells_exactly_preserved': 26, 'catalog': str(CATALOG.relative_to(ROOT)).replace('\\', '/'),
          'catalog_sha256': sha(CATALOG), 'atlas_sha256': sha(output_atlas), 'tiles': records,
          'editable_recipe': str(SOURCE.relative_to(ROOT)).replace('\\', '/'), 'editable_recipe_sha256': sha(SOURCE),
          'generator_sha256': sha(Path(__file__)), 'source_master': str((OLD / 'generated/bridge_module_master_v001.png').relative_to(ROOT)).replace('\\', '/'),
          'source_master_sha256': sha(OLD / 'generated/bridge_module_master_v001.png'),
          'original_prompt': 'art-source/ember/tilesets-v001/prompts/05_bridge_deck_master_v001.txt',
          'tool': 'NATIVE_EDITABLE_CODE_RECIPE_EXTENSION', 'new_imagegen_calls': 0,
          'adjustments': ['Draw lower/right beams at section [20,26) with highlight still upper/left.',
                          'Redraw three closed caps and brass fasteners without mirroring direction light.',
                          'Retain all original atlas coordinates/source IDs and old PNGs.',
                          'Ground supports caps, beams overlap deck on separate layers; water sides face inward.'],
          'protected_inputs_unchanged': True})
    print(json.dumps({'generated': 5, 'old_cells_preserved': 26, 'catalog_units': 67, 'atlas': str(output_atlas)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
