"""Read production PNGs only; create nearest-neighbor visual evidence and alpha diagnostics.

Alpha components are measurements, not an automatic verdict. Disconnected icon shapes,
open doors, handle apertures, grass gaps and smoke alpha need semantic review.
"""
from __future__ import annotations
import hashlib
import json
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connected(mask: np.ndarray, diagonal: bool = False) -> list[dict]:
    """Measure actual native pixels with either edge or edge-and-corner connectivity."""
    seen = np.zeros(mask.shape, dtype=bool)
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        offsets += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    groups = []
    h, w = mask.shape
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        seen[y, x] = True
        q = deque([(int(x), int(y))])
        pixels = []
        while q:
            px, py = q.popleft()
            pixels.append((px, py))
            for dx, dy in offsets:
                nx, ny = px + dx, py + dy
                if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((nx, ny))
        xx, yy = zip(*pixels)
        groups.append({"area": len(pixels), "bbox": [min(xx), min(yy), max(xx) + 1, max(yy) + 1],
                       "touches_canvas_edge": min(xx) == 0 or min(yy) == 0 or max(xx) == w - 1 or max(yy) == h - 1,
                       "pixels_if_small": pixels if len(pixels) <= 32 else None})
    return sorted(groups, key=lambda g: g["area"], reverse=True)


def checker(size: tuple[int, int], step: int = 8) -> Image.Image:
    w, h = size
    y, x = np.indices((h, w))
    a = np.where(((x // step) + (y // step)) % 2 == 0, 42, 62).astype(np.uint8)
    return Image.fromarray(np.dstack((a, a, a, np.full_like(a, 255))), 'RGBA')


def native_board(records: list[dict], group: str, per_page: int = 6) -> None:
    """Both 1x and exact 4x previews derive directly from the production file."""
    for page, start in enumerate(range(0, len(records), per_page)):
        batch = records[start:start + per_page]
        cell_w = max(520, max(max(r['size'][0] + 28, 208) + 4 * r['size'][0] + 12 for r in batch))
        cell_h = 4 * max(r['size'][1] for r in batch) + 78
        cols = 2
        board = Image.new('RGB', (cols * cell_w, ((len(batch) + 1) // 2) * cell_h), '#151a20')
        draw = ImageDraw.Draw(board)
        for i, r in enumerate(batch):
            ox, oy = (i % cols) * cell_w, (i // cols) * cell_h
            draw.text((ox + 10, oy + 10), r['id'] + '  native 1x / nearest 4x', fill='white')
            draw.text((ox + 10, oy + 29), f"{r['size']}  alpha={r['alpha_values']}  4c={len(r['opaque_components_4'])}  8c={len(r['opaque_components_8'])}", fill='#b4c0ca')
            im = Image.open(ROOT / r['file']).convert('RGBA')
            for scale, dx in [(1, 10), (4, max(r['size'][0] + 28, 208))]:
                scaled = im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)
                bg = checker(scaled.size, 8 * scale)
                bg.alpha_composite(scaled)
                board.paste(bg.convert('RGB'), (ox + dx, oy + 58))
        name = f'{group}-native-and-nearest4x-{page + 1:02d}.png'
        board.save(OUT / name)
        for r in batch:
            r['visual_board'] = name


def individual_preview(r: dict) -> None:
    """Bound the image size so UI rendering cannot obscure the native pixel grid."""
    im = Image.open(ROOT / r['file']).convert('RGBA')
    box = im.getbbox()
    if box is None:
        return
    # Add native context; all coordinates in measurements still refer to full production canvas.
    x0, y0, x1, y1 = box
    box = (max(0, x0 - 4), max(0, y0 - 4), min(im.width, x1 + 4), min(im.height, y1 + 4))
    crop = im.crop(box)
    native = checker(im.size)
    native.alpha_composite(im)
    large = crop.resize((crop.width * 4, crop.height * 4), Image.Resampling.NEAREST)
    bg = checker(large.size, 32)
    bg.alpha_composite(large)
    ox = im.width + 24
    board = Image.new('RGB', (max(560, ox + large.width + 12), max(im.height, large.height) + 62), '#151a20')
    draw = ImageDraw.Draw(board)
    draw.text((10, 9), r['id'] + '  original canvas 1x / nearest 4x body crop', fill='white')
    draw.text((10, 28), '4x crop native origin: ' + str(list(box[:2])), fill='#bbc7cc')
    board.paste(native.convert('RGB'), (10, 50))
    board.paste(bg.convert('RGB'), (ox, 50))
    name = r['id'] + '-native-and-nearest4x.png'
    board.save(OUT / name)
    r['individual_visual'] = name


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # The three catalogs preserve native sources and finishing records for 40 late assets.
    catalog_paths = ['assets/ember/ember_additional_catalog_v001.json',
                     'art-source/ember/full-art-v001/candidate-catalog-v001.json',
                     'art-source/ember/batch-03-objects/native-catalog-v001.json',
                     'art-source/ember/batch-04-ui/ui-catalog-v001.json',
                     'art-source/ember/batch-05-textures/textures-catalog-v001.json']
    metadata = {}
    for rel in catalog_paths:
        catalog = json.loads((ROOT / rel).read_text(encoding='utf-8'))
        for entry in catalog.get('assets', []):
            prod = entry.get('production_file', entry.get('file', '')).removeprefix('res://')
            metadata.setdefault(prod, []).append({'catalog': rel, 'entry': entry})
    first_finish = 'art-source/ember/batch-01/pixel-finish-v001/finishing-record.json'
    for entry in json.loads((ROOT / first_finish).read_text(encoding='utf-8')):
        if entry.get('id') == 'B01':
            metadata.setdefault(entry['output'], []).append({'catalog': first_finish, 'entry': entry})
    paths = []
    for group in ['buildings', 'props', 'ui', 'vfx', 'three_d']:
        for path in sorted((ROOT / 'assets/ember' / group).rglob('*.png')):
            # Four 16px particles and normal/PBR/grass-weight technical inputs are another audit scope.
            if 'particles' in path.parts or any(s in path.name for s in ['_normal_', '_roughness_', '_metallic_', '_height_weight_']):
                continue
            paths.append(path)
    records = []
    groups = {'objects': [], 'ui': [], 'textures': []}
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        original = Image.open(path)
        image = original.convert('RGBA')
        a = np.asarray(image)[:, :, 3]
        opaque = a == 255
        transparent_groups = connected(a == 0)
        holes = [g for g in transparent_groups if not g['touches_canvas_edge']]
        r = {'id': path.stem, 'file': rel, 'sha256': sha(path), 'size': list(image.size),
             'original_mode': original.mode, 'alpha_values': [int(v) for v in np.unique(a)],
             'partial_alpha_pixels': int(np.count_nonzero((a > 0) & (a < 255))),
             'opaque_components_4': connected(opaque), 'opaque_components_8': connected(opaque, True),
             'enclosed_alpha_zero_components': holes, 'registered_sources': metadata.get(rel, [])}
        refs = metadata.get(rel, [])
        native_sources = []
        layer_reviews = []
        for ref in refs:
            entry = ref['entry']
            src_rel = entry.get('file', '').removeprefix('res://')
            if src_rel.startswith('art-source/') and (ROOT / src_rel).suffix == '.png':
                src = ROOT / src_rel
                native_sources.append({'file': src_rel, 'sha256': sha(src), 'production_bytes_identical': src.read_bytes() == path.read_bytes()})
            if entry.get('layers') and not layer_reviews:
                # Rebuild using source pixels, not the old PASS flag, to rule out export/layer loss.
                composite = Image.new('RGBA', image.size)
                source_sha = {}
                for layer in sorted(entry['layers'], key=lambda x: x['z_index']):
                    p = ROOT / layer['file']
                    source_sha[layer['file']] = sha(p)
                    composite.alpha_composite(Image.open(p).convert('RGBA'))
                comp = np.asarray(composite)
                actual = np.asarray(image)
                visible_diff = np.any(comp[:, :, :3] != actual[:, :, :3], axis=2) & ((comp[:, :, 3] > 0) | (a > 0))
                layer_reviews.append({'layer_count': len(entry['layers']), 'source_sha256': source_sha,
                                      'alpha_mismatch_pixels': int(np.count_nonzero(comp[:, :, 3] != a)),
                                      'visible_rgb_mismatch_pixels': int(np.count_nonzero(visible_diff))})
        r['native_finished_sources'] = native_sources
        r['independent_layer_reconstruction'] = layer_reviews
        records.append(r)
        group = 'objects' if '/buildings/' in rel or '/props/' in rel else 'ui' if '/ui/' in rel else 'textures'
        groups[group].append(r)
    for group, rs in groups.items():
        native_board(rs, group)
    for r in records:
        individual_preview(r)
    report = {'scope': '41 non-robot non-tile art production PNGs; no technical data PNGs',
              'production_png_count': len(records), 'group_counts': {k: len(v) for k, v in groups.items()},
              'coordinate_convention': 'native x,y; bbox x0,y0,x1,y1 exclusive end',
              'caution': 'Component and hole counts require semantic judgement; a count alone is not a fracture.',
              'catalog_sha256': {p: sha(ROOT / p) for p in catalog_paths + [first_finish]}, 'assets': records}
    (OUT / 'alpha-measurements.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    for r in records:
        small = [g for g in r['opaque_components_8'][1:] if g['area'] <= 32]
        print(r['id'], r['size'], '4c', len(r['opaque_components_4']), '8c', len(r['opaque_components_8']),
              'partial', r['partial_alpha_pixels'], 'holes', [(g['area'], g['bbox']) for g in r['enclosed_alpha_zero_components']],
              'small8c', [(g['area'], g['bbox']) for g in small])


if __name__ == '__main__':
    main()
