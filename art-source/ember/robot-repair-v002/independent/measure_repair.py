"""Independent candidate-pixel measurements and original/repair review boards.

Run only after the producer declares finished-frames ready. This reads PNGs and
never imports the producer's builder or modifies source/production assets.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
REPAIR = OUT.parent
ROBOT = ROOT / 'assets/ember/characters/robot'
DIRECTIONS = ['down', 'left', 'right', 'up']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(mask, diagonal=True):
    h, w = mask.shape
    seen = np.zeros(mask.shape, bool)
    result = []
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        offsets += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        q = deque([(int(x), int(y))]); seen[y, x] = True; pixels = []
        while q:
            px, py = q.popleft(); pixels.append([px, py])
            for dx, dy in offsets:
                nx, ny = px + dx, py + dy
                if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True; q.append((nx, ny))
        xs, ys = zip(*pixels)
        result.append({'area': len(pixels), 'bbox': [min(xs), min(ys), max(xs) + 1, max(ys) + 1],
                       'pixels': pixels})
    return sorted(result, key=lambda x: x['area'], reverse=True)


def checker(w, h, scale=1):
    y, x = np.indices((h, w))
    grey = np.where((x // (8 * scale) + y // (8 * scale)) % 2, 64, 42).astype('uint8')
    return Image.fromarray(np.dstack([grey, grey, grey, np.full_like(grey, 255)]), 'RGBA')


def show(im, scale=1):
    image = im.convert('RGBA').resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)
    bg = checker(image.width, image.height, scale); bg.alpha_composite(image)
    return bg.convert('RGB')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidates', type=Path, required=True)
    args = parser.parse_args()
    candidate_dir = args.candidates.resolve()
    if not candidate_dir.is_dir():
        raise FileNotFoundError(candidate_dir)
    source_catalog = json.loads((ROBOT / 'robot_frames_catalog_v001.json').read_text(encoding='utf-8'))
    palette = {tuple(bytes.fromhex(c.removeprefix('#'))) for c in source_catalog['palette']}
    records = []
    failures = []
    all_images = {}
    for direction in DIRECTIONS:
        for state, f in [('idle', 0)] + [('walk', x) for x in range(4)]:
            asset_id = f'robot_{state}_{direction}' + (f'_f{f:02d}' if state == 'walk' else '')
            old = ROBOT / (asset_id + '_v001.png')
            new = old if state == 'idle' else candidate_dir / (asset_id + '_v002.png')
            before = Image.open(old).convert('RGBA')
            after = Image.open(new).convert('RGBA')
            a = np.asarray(after); old_a = np.asarray(before)
            parts8 = components(a[:, :, 3] > 0)
            parts4 = components(a[:, :, 3] > 0, False)
            opaque = a[:, :, 3] == 255
            ys, xs = np.nonzero(opaque)
            off_palette = [(int(x), int(y)) for y, x in zip(ys, xs) if tuple(a[y, x, :3]) not in palette]
            changed = np.any(a != old_a, axis=2)
            cy, cx = np.nonzero(changed)
            r = {'id': asset_id, 'direction': direction, 'state': state, 'frame_index': f,
                 'file': new.relative_to(ROOT).as_posix(), 'sha256': sha(new), 'old_file': old.relative_to(ROOT).as_posix(),
                 'old_sha256': sha(old), 'size': list(after.size), 'alpha_values': list(map(int, np.unique(a[:, :, 3]))),
                 'components_8': parts8, 'components_4': parts4,
                 'bbox': [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1],
                 'anchor_expected': [32, 80], 'foot_bottom_boundary': int(ys.max()) + 1,
                 'old_foot_bottom_boundary': int(np.nonzero(old_a[:, :, 3] == 255)[0].max()) + 1,
                 'off_palette_pixels': off_palette, 'changed_pixel_count': int(changed.sum()),
                 'changed_pixel_bbox': [int(cx.min()), int(cy.min()), int(cx.max()) + 1, int(cy.max()) + 1] if len(cx) else None}
            bronze = np.zeros(opaque.shape, bool)
            old_bronze = np.zeros(opaque.shape, bool)
            for colour in [(123, 77, 53), (183, 124, 75), (226, 183, 122)]:
                bronze |= np.all(a[:, :, :3] == colour, axis=2) & opaque
                old_bronze |= np.all(old_a[:, :, :3] == colour, axis=2) & (old_a[:, :, 3] == 255)
            bronze_changed = np.any(a != old_a, axis=2) & (bronze | old_bronze)
            r['unchanged_head_region'] = {'bounds': [0, 0, 64, 41], 'changed_rgba_pixels': int(changed[:41, :].sum())}
            r['bronze_tool_regions_changed_pixels'] = int(bronze_changed.sum())
            if after.size != (64, 96): failures.append(asset_id + ': canvas')
            if len(parts8) != 1: failures.append(asset_id + ': detached fragment')
            if set(r['alpha_values']) - {0, 255}: failures.append(asset_id + ': partial alpha')
            if off_palette: failures.append(asset_id + ': palette')
            # A lifted side-view foot may end above y80. Compare the existing pose,
            # while the virtual anchor is checked separately in rig/scene metadata.
            # left f03's old lower edge belonged to the wrong leg. After all 14
            # near-boot pixels share one owner, the full lifted boot ends at y78.
            # This specific geometry repair is reviewed separately from anchor drift.
            if asset_id == 'robot_walk_left_f03':
                r['foot_extent_review'] = 'Old boundary79 -> new78; must verify all14 boot pixels move with near leg offset(0,-2), fixed virtual anchor(32,80).'
                if r['foot_bottom_boundary'] != 78: failures.append(asset_id + ': corrected lifted foot extent')
            elif r['foot_bottom_boundary'] != r['old_foot_bottom_boundary']:
                failures.append(asset_id + ': foot extent changed')
            if r['bbox'][2] - r['bbox'][0] > 40 or r['bbox'][3] - r['bbox'][1] > 64: failures.append(asset_id + ': bbox limit')
            if state == 'idle' and changed.any(): failures.append(asset_id + ': idle changed')
            # Native full canvas plus exact 4x; source images are never resized on disk.
            board = Image.new('RGB', (352, 440), '#141a20'); d = ImageDraw.Draw(board)
            d.text((8, 8), asset_id + '  current 1x + 4x', fill='white')
            board.paste(show(after), (8, 34)); board.paste(show(after, 4), (88, 34))
            visual = OUT / (asset_id + '-current-1x-4x.png'); board.save(visual)
            r['current_visual'] = visual.relative_to(ROOT).as_posix()
            if state == 'walk':
                diff_image = Image.new('RGB', after.size, '#151b21')
                diff_arr = np.asarray(diff_image).copy()
                diff_arr[changed] = [255, 64, 128]
                diff_image = Image.fromarray(diff_arr).resize((256, 384), Image.Resampling.NEAREST)
                compare = Image.new('RGB', (800, 438), '#141a20'); d = ImageDraw.Draw(compare)
                for n, label, image in [(0, 'v001 old', show(before, 4)), (1, 'v002 repair', show(after, 4)), (2, 'changed pixels', diff_image)]:
                    d.text((8 + n * 264, 8), label + ' ' + asset_id, fill='white')
                    compare.paste(image, (8 + n * 264, 34))
                visual = OUT / (asset_id + '-before-after-diff-4x.png'); compare.save(visual)
                r['before_after_visual'] = visual.relative_to(ROOT).as_posix()
            all_images[asset_id] = after
            records.append(r)
    for direction in DIRECTIONS:
        # The final repeated f00 exposes the wrap transition, rather than hiding it.
        seq = [all_images[f'robot_walk_{direction}_f{i:02d}'] for i in [0, 1, 2, 3, 0]]
        strip = Image.new('RGB', (1328, 438), '#141a20'); d = ImageDraw.Draw(strip)
        for n, (frame, number) in enumerate(zip(seq, [0, 1, 2, 3, 0])):
            d.text((8 + n * 264, 8), direction + f' f{number:02d}' + (' wrap' if n == 4 else ''), fill='white')
            strip.paste(show(frame, 4), (8 + n * 264, 34))
        strip.save(OUT / (direction + '-complete-loop-4x.png'))
        frames = [show(frame, 4) for frame in seq[:4]]
        frames[0].save(OUT / (direction + '-complete-loop-4x.gif'), save_all=True, append_images=frames[1:], duration=125, loop=0)
    result = {'status': 'PNG_MEASUREMENTS_PASS_PENDING_INDEPENDENT_SEMANTIC_REVIEW' if not failures else 'PNG_MEASUREMENTS_FAIL',
              'checks_scope': '20 current frames: 4 preserved v001 idle + 16 candidate v002 walk',
              'failures': failures, 'asset_sha256': {r['id']: r['sha256'] for r in records}, 'frames': records}
    (OUT / 'candidate-pixel-measurements.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': result['status'], 'frame_count': len(records), 'failures': failures}, ensure_ascii=False))
    raise SystemExit(bool(failures))


if __name__ == '__main__':
    main()
