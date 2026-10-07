"""Read-only hash regression for 41 other art PNGs and the 62-tile reusable sets.

Record current native sources/resources before repair; verification never re-renders
or changes already reviewed assets. New robot v002 files are outside this baseline.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
BASE = OUT / 'other-art-and-tiles-before.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        baseline = json.loads(BASE.read_text(encoding='utf-8'))
        failures = []
        for rel, digest in baseline['file_sha256'].items():
            path = ROOT / rel
            if not path.is_file() or sha(path) != digest:
                failures.append(rel)
        result = {'status': 'PASS' if not failures else 'FAIL', 'checked_files': len(baseline['file_sha256']),
                  'baseline_sha256': sha(BASE), 'changed_or_missing_files': failures,
                  'art_production_pngs': 41, 'reusable_tile_units': 62, 'tile_atlases': 3}
        (OUT / 'other-art-and-tiles-after.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False))
        raise SystemExit(bool(failures))
    if BASE.exists():
        raise FileExistsError('Preserve the existing pre-repair baseline: ' + str(BASE))
    measurement = json.loads((ROOT / 'art-source/ember/quality-audit-2026-10-04/other-art/alpha-measurements.json').read_text(encoding='utf-8'))
    paths = set()
    for asset in measurement['assets']:
        paths.add(asset['file'])
        for ref in asset['native_finished_sources']:
            paths.add(ref['file'])
        for layer in asset['independent_layer_reconstruction']:
            paths.update(layer['source_sha256'])
    paths.update(measurement['catalog_sha256'])
    tile_root = ROOT / 'assets/ember/environment/tilesets'
    paths.update(p.relative_to(ROOT).as_posix() for p in tile_root.iterdir() if p.suffix in {'.png', '.tres', '.json'})
    # Preserve all current non-robot resources too, including new technical material inputs.
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT / 'assets/ember').rglob('*.tres') if 'characters' not in p.parts)
    for rel in ['art-source/ember/tilesets-v001/native-catalog-v001.json',
                'art-source/ember/tilesets-v001/planned-catalog-v001.json']:
        paths.add(rel)
    # Actual editable tile sources are PNGs beneath sources/ and layers/, not review boards.
    for p in (ROOT / 'art-source/ember/tilesets-v001').rglob('*.png'):
        if any(part in {'source', 'sources', 'layers', 'native', 'finished', 'finished-tiles'} for part in p.parts):
            paths.add(p.relative_to(ROOT).as_posix())
    result = {'scope': '41 non-robot/non-tile art PNGs, their native finished/object layers, 62 tile units in 3 atlases, current non-robot resources and catalogs',
              'art_production_pngs': 41, 'reusable_tile_units': 62, 'tile_atlases': 3,
              'file_sha256': {rel: sha(ROOT / rel) for rel in sorted(paths)}}
    BASE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Pre-repair baseline files:', len(paths))


if __name__ == '__main__':
    main()
