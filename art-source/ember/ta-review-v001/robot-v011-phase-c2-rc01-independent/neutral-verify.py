"""C2仅S新中性来源/五像素补丁/固定源和足部接续；生产只读，不跑生成或Godot。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image
import numpy as np
import json, hashlib, math

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
DEL = ROOT / 'art-source/ember/deliveries'
ZP = DEL / 'robot_eight_way_v011_phase_c2_rc01_2026-10-07.zip'
CP = DEL / 'robot_eight_way_v011_phase_c1_rc01_2026-10-07.zip'
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(ZP.read_bytes()) == 'e0a5fe91bcd62509d0f342e45334ce34cf374ebea1ac0203162d9b90f79b5643'
assert sha(CP.read_bytes()) == '0c62177198973b24bb3fbfcc306ba4617af3ad754eb5a0696bdfddb4f19f51df'
z, old = ZipFile(ZP), ZipFile(CP)
js = lambda name: json.loads(z.read(name))
image = lambda name: np.array(Image.open(BytesIO(z.read(name))).convert('RGBA'))
W, H = 64, 96
yy, xx = np.indices((H, W))

def stamp(source, transform):
    angle = transform['radians']
    c, s = math.cos(angle), math.sin(angle)
    dx, dy = xx+.5-transform['targetPivot'][0], yy+.5-transform['targetPivot'][1]
    sx = np.floor(dx*c+dy*s+transform['sourcePivot'][0]).astype(int)
    sy = np.floor(-dx*s+dy*c+transform['sourcePivot'][1]).astype(int)
    out = np.zeros_like(source)
    valid = (sx >= 0) & (sy >= 0) & (sx < W) & (sy < H)
    out[valid] = source[sy[valid], sx[valid]]
    return out

def put(out, layer):
    opaque = layer[:, :, 3] > 0
    out[opaque] = layer[opaque]

def polygon(shape):
    X, Y = xx+.5, yy+.5
    mask = np.zeros((H, W), bool)
    for (x1, y1), (x2, y2) in zip(shape, shape[1:]+shape[:1]):
        if y1 != y2:
            mask ^= ((y1 > Y) != (y2 > Y)) & (X < (x2-x1)*(Y-y1)/(y2-y1)+x1)
    return mask

def render(parts, rig, state):
    result = np.zeros((H, W, 4), np.uint8)
    for limb in rig['limb_order']:
        ids = ['pelvis', 'body'] if limb == 'body' else [limb+'_'+s for s in ['end', 'lower', 'upper'] if limb+'_'+s in parts]
        for p in ids:
            put(result, stamp(parts[p], state['transforms'][p]))
    return result

def point(p, transform):
    c, s = math.cos(transform['radians']), math.sin(transform['radians'])
    x, y = np.array(p)-transform['sourcePivot']
    return np.array(transform['targetPivot'])+[c*x-s*y, s*x+c*y]

old_meta = json.loads(old.read('walk-batch-metadata.json'))
old_walks = [f['file'] for c in old_meta['clips'] if c['action'] == 'walk' for f in c['frames']]
old_identities = [f['file'] for c in old_meta['clips'] if c['action'] == 'pose' for f in c['frames']]
assert len(old_walks) == 64 and len(old_identities) == 8
assert all(z.read(n) == old.read(n) for n in old_walks+old_identities)
source_file = 'frames/walk/down/robot_walk_down_f02_v010.png'
source = image(source_file)
assert sha(z.read(source_file)) == '31aef53af6a5552d9adae69f5afefab25ee35cc30059bf285dffc375f374dc79'
assert z.read(source_file) == z.read('source/candidate-masters/robot_idle_down_v011.png')
registration = js('source/down-neutral-candidate/registration.json')
lower = np.zeros_like(source)
lower[68:, :31] = source[68:, :31]
upper = source.copy()
upper[70:, :31] = 0
assert np.array_equal(lower, image('source/down-neutral-candidate/right_lower_original.png'))
assert np.array_equal(upper, image('source/down-neutral-candidate/other_original.png'))
raw = np.zeros_like(source)
put(raw, stamp(lower, {'sourcePivot': [22, 75.2], 'targetPivot': [22, 76.2], 'radians': 0}))
put(raw, upper)
assert np.array_equal(raw, image('source/down-neutral-candidate/neutral_rig_raw.png'))
changes = np.argwhere(np.any(raw != source, axis=2))[:, [1, 0]].tolist()
assert len(changes) == 67 and changes == registration['changed_coordinates']
assert sha(raw.tobytes()) == registration['raw_rgba_sha256']
assert not np.any(np.any(raw != source, axis=2) & ~((xx <= 30) & (yy >= 68)))
assert np.array_equal(image('source/down-neutral-candidate/edit_target_8x.png'), np.repeat(np.repeat(raw, 8, 0), 8, 1))
assert np.array_equal(image('source/down-neutral-candidate/identity_f02_8x.png'), np.repeat(np.repeat(source, 8, 0), 8, 1))

patch_report = js('source/down-neutral-candidate/joint_patch.json')
entry = next(g for g in js('run-manifest.json')['generation'] if g['scope'] == 'S double-support neutral knee seam')
assert entry['sha256'] == sha(z.read(entry['source'])) == patch_report['imagegen_sha256']
assert entry['input_sha256'] == sha(z.read(entry['actual_input']))
assert entry['actual_input'] == patch_report['input'] and entry['prompt'] == patch_report['prompt']
assert (OUT/'neutral-imagegen-source.png').read_bytes() == z.read(entry['source'])
patch = np.frombuffer((OUT/'neutral-patch-nearest.rgba').read_bytes(), np.uint8).reshape(H, W, 4)
palette = np.array([[int(h[i:i+2], 16) for i in (0, 2, 4)] for h in ['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A']])
luma = lambda rgb: rgb @ np.array([.2126, .7152, .0722])
distance = ((patch[:, :, None, :3].astype(int)-palette[None, None, :, :])**2).sum(axis=3)
colors = palette[np.argmin(distance, axis=2)]
mask = (((xx+.5-24)/4.5)**2+((yy+.5-70)/4)**2 <= 1) & (xx >= 17) & (xx <= 29) & (yy >= 66) & (yy <= 74)
mask &= (raw[:, :, 3] > 0) & (patch[:, :, 3] >= 160) & (luma(raw[:, :, :3]) < 125) & (luma(colors) >= 60) & (luma(colors) < 150)
final = raw.copy()
final[mask, :3] = colors[mask]
final[mask, 3] = 255
neutral_file = 'source/action-candidate-masters/robot_neutral_down_v011.png'
neutral = image(neutral_file)
assert np.array_equal(final, neutral)
assert np.array_equal(mask, image('source/down-neutral-candidate/joint_mask.png')[:, :, 3] > 0)
patch_changes = np.argwhere(np.any(neutral != raw, axis=2))[:, [1, 0]].tolist()
assert patch_changes == [[24,66],[25,66],[24,67],[27,71],[27,72]] == patch_report['changed_coordinates']
assert sha(z.read(neutral_file)) == patch_report['sha256'] == entry['final_sha256']
assert np.array_equal(neutral[:, :, 3], raw[:, :, 3])
assert np.array_equal(neutral[(luma(raw[:, :, :3]) >= 125) | (raw[:, :, 3] == 0)], raw[(luma(raw[:, :, :3]) >= 125) | (raw[:, :, 3] == 0)])
assert not np.any(np.any(neutral != raw, axis=2) & ~mask)

fixed = js('source/action-source-registration/down/registration.json')
rig = fixed['rig']
assert fixed['source_file'] == neutral_file and fixed['source_sha256'] == sha(z.read(neutral_file))
expected_parts = {'body': neutral.copy()}
owner = np.full((H, W), 'body', dtype=object)
hits = sum(polygon(l['polygon']).astype(int) for l in rig['limbs'].values())
assert not np.any((neutral[:, :, 3] > 0) & (hits > 1))
for limb, l in rig['limbs'].items():
    owned = polygon(l['polygon']) & (neutral[:, :, 3] > 0)
    owner[owned] = limb
    expected_parts['body'][owned] = 0
    spans = {'upper': yy < l['split'][0]+2, 'lower': (yy >= l['split'][0]-2) & ((yy < l['split'][1]+.5) if l['end_part'] else True)}
    if l['end_part']:
        spans['end'] = yy >= l['split'][1]-.5
    for suffix, span in spans.items():
        part = np.zeros_like(neutral)
        part[owned & span] = neutral[owned & span]
        expected_parts[limb+'_'+suffix] = part
whole = expected_parts['body'].copy()
expected_parts['body'][60:] = 0
expected_parts['pelvis'] = whole.copy()
expected_parts['pelvis'][:58] = 0
parts = {}
for p in fixed['parts']:
    part = image(p['file'])
    assert np.array_equal(part, expected_parts[p['id']]) and sha(part.tobytes()) == p['raw_sha256']
    parts[p['id']] = part
assert len(parts) == 12 and not whole[64:, :, 3].any()

frame_checks, maximum_endpoint_error, maximum_bone_error = [], 0., 0.
for action in ['idle', 'collect']:
    ledger = js(f'source/action-rig-batch/{action}/down/rig_and_poses.json')
    for state, f in zip(ledger['states'], ledger['frames']):
        assert np.array_equal(render(parts, rig, state), image(f['file']))
        assert sha(image(f['file']).tobytes()) == f['raw_sha256']
        for limb, l in rig['limbs'].items():
            joints = state['joints'][limb]
            end_key = 'ankle' if l['kind'] == 'leg' else 'wrist'
            for p, t, target in [(l['root'], limb+'_upper', joints['root']), (l['joint'], limb+'_upper', joints['joint']), (l['joint'], limb+'_lower', joints['joint']), (l['end'], limb+'_lower', joints[end_key])]:
                maximum_endpoint_error = max(maximum_endpoint_error, float(np.max(np.abs(point(p, state['transforms'][t])-target))))
            for p, q, target_p, target_q in [(l['root'], l['joint'], joints['root'], joints['joint']), (l['joint'], l['end'], joints['joint'], joints[end_key])]:
                maximum_bone_error = max(maximum_bone_error, abs(np.linalg.norm(np.subtract(p,q))-np.linalg.norm(np.subtract(target_p,target_q))))
            if l['kind'] == 'leg':
                end_transform = state['transforms'][limb+'_end']
                assert end_transform['radians'] == 0 and end_transform['sourcePivot'] == end_transform['targetPivot'] == l['end']
                assert joints['contact'] and joints['lift'] == 0
        final_file = f'frames/{action}/down/robot_{action}_down_f{state["frame"]:02}_v011.png'
        final_frame = image(final_file)
        # 固定的是完整靴拆件及其位置，不把正常小腿覆盖鞋口误报成鞋重绘。
        # F1/F2 的左小腿旋转后覆盖 y76 两个原靴像素；先独立定位再记录例外。
        lower_band_changes = np.argwhere(np.any(final_frame != neutral, axis=2) & (yy >= 76))[:, [1, 0]].tolist()
        expected_overlap = [[42,76],[43,76]] if action == 'collect' and state['frame'] in [1,2] else []
        assert lower_band_changes == expected_overlap
        assert np.array_equal(final_frame[77:], neutral[77:])
        assert np.array_equal(final_frame[76:], image(f['file'])[76:])
        for side in ['right', 'left']:
            boot_name = 'leg_'+side+'_end'
            assert np.array_equal(stamp(parts[boot_name], state['transforms'][boot_name]), parts[boot_name])
        for x, y in expected_overlap:
            left_shin = stamp(parts['leg_left_lower'], state['transforms']['leg_left_lower'])
            assert np.array_equal(left_shin[y,x], final_frame[y,x])
        frame_checks.append({'action': action, 'frame': state['frame'], 'raw_rig_RGBA_diff': 0,
                             'boots_end_transform_identity': True, 'boots_layer_RGBA_diff': 0,
                             'sole_band_y77_RGBA_diff': 0, 'y76plus_final_vs_raw_rig_RGBA_diff': 0,
                             'y76plus_vs_neutral_changed_coordinates': lower_band_changes,
                             'y76_shin_over_boot_is_rig_occlusion_not_AI_patch': bool(expected_overlap),
                             'png_sha256': sha(z.read(final_file))})
assert maximum_endpoint_error < 1e-10 and maximum_bone_error < 1e-10
assert z.read('frames/idle/down/robot_idle_down_f00_v011.png') == z.read(neutral_file) == z.read('frames/collect/down/robot_collect_down_f03_v011.png')
assert np.array_equal(image('frames/collect/down/robot_collect_down_f01_v011.png')[64:], image('frames/collect/down/robot_collect_down_f02_v011.png')[64:])
soles = {}
for name, a in [('old_walk_f02', source), ('raw_registered_neutral', raw), ('final_neutral', neutral)]:
    soles[name] = {}
    for side, x0, x1 in [('right',0,31),('left',31,64)]:
        ys = np.argwhere(a[72:, x0:x1, 3] > 0)[:,0]+72
        soles[name][side] = int(ys.max())
assert soles['old_walk_f02'] == {'right':78,'left':79}
assert soles['final_neutral'] == {'right':79,'left':79}
# 绑定恢复后实际观看的诊断图，避免把旧图或未经核对的缩略图写成当前视觉证据。
def on_background(a, background, scale=8):
    canvas = Image.new('RGBA', (a.shape[1], a.shape[0]), background)
    canvas.alpha_composite(Image.fromarray(a))
    return np.array(canvas.resize((a.shape[1]*scale, a.shape[0]*scale), Image.Resampling.NEAREST))

board = np.array(Image.open(OUT/'neutral-source-rig-final-8x.png').convert('RGBA'))
for i, a in enumerate([source, raw, neutral]):
    assert np.array_equal(board[:,i*512:(i+1)*512], on_background(a, (236,233,216,255)))
six_frames = [image(f'frames/{a}/down/robot_{a}_down_f{f:02}_v011.png') for a, frames in [('idle',range(2)),('collect',range(4))] for f in frames]
for variant, bg in [('light',(236,233,216,255)),('dark',(24,38,49,255))]:
    board = np.array(Image.open(OUT/f'neutral-s-legs-{variant}-8x.png').convert('RGBA'))
    for i, a in enumerate(six_frames):
        x, y = i%3*368, i//3*256
        assert np.array_equal(board[y:y+256,x:x+368], on_background(a[52:84,10:56], bg))
bindings = [source_file, neutral_file, entry['source'], entry['actual_input'], entry['prompt'], 'source/down-neutral-candidate/registration.json', 'source/down-neutral-candidate/joint_patch.json', 'source/action-source-registration/down/registration.json']
report = {'status': 'S_NEUTRAL_LIMITED_SOURCE_SUPPORT_AND_STATIC_VISUAL_PASS', 'zip_sha256': sha(ZP.read_bytes()),
          'scope': 'S neutral, 12S fixed parts, 6S raw rig/support continuity only; old64walk/8identity byte comparison, no other-direction visual re-review/full112GPU/cold/manifest',
          'old_c1_zip_sha256': sha(CP.read_bytes()), 'old_walk64_and_identity8_byte_same': True,
          'old_walk_f02_is_neutral': False, 'old_f02_source_support_author_record': registration['source_support'],
          'translation': [0,1], 'scale': 1, 'rotation': 0, 'source_region': {'x':[0,30],'y':[68,95]}, 'retained_original_overlap_rows':[68,69],
          'raw_registration_changed': 67, 'outside_registered_region_RGBA_diff': 0,
          'patch_source_size': patch_report['source_size'], 'patch_global_scale':[.0625,.0625], 'actual_input_exact_raw_neutral8x': True,
          'patch_eligible_mask_pixels': int(mask.sum()), 'patch_changed_pixels': [{'point':[x,y],'before':raw[y,x].tolist(),'after':neutral[y,x].tolist()} for x,y in patch_changes],
          'mask_outside_RGBA_diff': 0, 'opaque_silhouette_alpha_diff': 0, 'luminance125plus_armor_and_transparent_RGBA_diff': 0,
          'fixed_source_parts12_RGBA_diff': 0, 'fixed_owner_cross_limb_opaque_overlap': 0, 'waist_overlap_rows':[58,59],
          'source_sole_raster_bottom': soles, 'sole_pixel_bottom_edge_and_root_y':80, 'frames':frame_checks,
          'endpoint_max_error': maximum_endpoint_error, 'bone_length_max_error': maximum_bone_error,
          'idle00_equals_new_neutral_equals_collect03_bytes':True, 'collect01_02_lower_y64_RGBA_diff':0,
          'corrected_old_assumption':'Whole y76+ region is not identical to neutral: collect01/02 each has 2 pixels at (42,76),(43,76) covered by rigidly rotated leg_left_lower; boot layers remain exactly unchanged, final equals raw rig in y76+, and y77+ is unchanged. These are not AI patch pixels.',
          'bindings':{n:sha(z.read(n)) for n in bindings},
          'diagnostic_verified_RGBA_against_frozen_zip': {n:sha((OUT/n).read_bytes()) for n in ['neutral-source-rig-final-8x.png','neutral-s-legs-light-8x.png','neutral-s-legs-dark-8x.png']},
          'visual_scope':'Source/rig/final8x and six S leg contact poses on light/dark8x: preserved original boot silhouettes, attached knee/ankle, no confirmed P1/P2 within S neutral/support check. This is not all-action visual approval or timed browser playback.',
          'diagnostic_crop':'neutral-s-legs-{light,dark}-8x.png source ROI[10,52,46,32], row-major idle00,idle01,collect00,collect01,collect02,collect03; fixed original positions, nearest8x',
          'full_delivery_boundary':'Author metadata says 24clips112frames authored with42new_pending_TA. This report cannot promote that to full production PASS.'}
(OUT/'neutral-binding.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','raw_registration_changed','patch_eligible_mask_pixels','patch_changed_pixels','source_sole_raster_bottom','endpoint_max_error','bone_length_max_error']}))
