"""Read the frozen package; write bounded visual diagnostics only in this review."""
from pathlib import Path
import hashlib, json
from PIL import Image, ImageDraw

base = Path(__file__).resolve().parent
pkg = base / 'package'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rows = {}
for direction in ['up_left', 'up', 'up_right', 'down_right']:
    p = pkg / 'source' / 'fixed-rig-pilot' / direction / 'rig_and_poses.json'
    data = json.loads(p.read_text(encoding='utf-8-sig'))
    a, b = data['states'][0], data['states'][4]
    row = {'rig_sha256': sha(p), 'f00_bob': a['bob'], 'f04_bob': b['bob'], 'sides': {}}
    for side in ['left', 'right']:
        wrist_a = a['joints']['arm_' + side]['wrist']
        wrist_b = b['joints']['arm_' + side]['wrist']
        ankle_a = a['joints']['leg_' + side]['ankle']
        ankle_b = b['joints']['leg_' + side]['ankle']
        row['sides'][side] = {
            'f00_wrist': wrist_a, 'f04_wrist': wrist_b,
            'f00_ankle': ankle_a, 'f04_ankle': ankle_b,
            'wrist_delta': [wrist_b[i] - wrist_a[i] for i in range(2)],
            'ankle_delta': [ankle_b[i] - ankle_a[i] for i in range(2)],
            'both_contact': a['joints']['leg_' + side]['contact'] and b['joints']['leg_' + side]['contact'],
        }
    rows[direction] = row

# All sprites keep the original canvas and anchor; no bounding-box alignment.
for bg_name, bg in [('light', (232, 232, 228, 255)), ('dark', (25, 42, 52, 255))]:
    out = Image.new('RGBA', (64 * 8 * 4, (96 * 8 + 30) * 2), bg)
    draw = ImageDraw.Draw(out)
    for r, direction in enumerate(['up_right', 'down_right']):
        for c, frame in enumerate([0, 4, 7, 0]):
            p = pkg / 'frames' / 'walk' / direction / f'robot_walk_{direction}_f{frame:02}_v011.png'
            im = Image.open(p).convert('RGBA').resize((64 * 8, 96 * 8), Image.Resampling.NEAREST)
            x, y = c * 64 * 8, r * (96 * 8 + 30)
            out.alpha_composite(im, (x, y + 30))
            draw.text((x + 8, y + 8), f'{direction} F{frame:02}', fill=(20, 20, 20, 255) if bg_name == 'light' else (240, 240, 240, 255))
    out.convert('RGB').save(base / f'arm_leg_phase_and_loop_{bg_name}_8x.png')

binding = json.loads((base / 'visual-binding.json').read_text(encoding='utf-8-sig'))
binding.pop('catalog_sha256', None)
binding['walk_batch_metadata_sha256'] = sha(pkg / 'walk-batch-metadata.json')
binding['sha256_manifest_sha256'] = sha(pkg / 'sha256-manifest.json')
binding['atlas_sha256'] = sha(pkg / 'robot_walk_batch_atlas_v011.png')
binding['reviewed_frame_sha256'] = {
    str(p.relative_to(pkg)).replace('\\', '/'): sha(p)
    for d in rows for p in sorted((pkg / 'frames' / 'walk' / d).glob('*.png'))
}
binding['evidence_sha256'] = {p.name: sha(p) for p in base.glob('arm_leg_phase_and_loop_*_8x.png')}
binding['status'] = 'NEEDS_REVISION_WITHDRAWN_RC01'
(base / 'visual-binding.json').write_text(json.dumps(binding, indent=2, ensure_ascii=False), encoding='utf-8')
(base / 'arm-leg-phase-evidence.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
print(json.dumps({'walk_batch_metadata_sha256': binding['walk_batch_metadata_sha256'], 'sha256_manifest_sha256': binding['sha256_manifest_sha256'], 'atlas_sha256': binding['atlas_sha256'], 'reviewed_frames': len(binding['reviewed_frame_sha256'])}, ensure_ascii=False))
