"""限定固定来源/所有权/32登记姿态；只追踪几个正式PNG点，不全帧重建或运行Godot。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image
import numpy as np
import json, hashlib, math

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
DEL = ROOT / 'art-source/ember/deliveries'
ZP = DEL / 'enemy_patrol_four_moves_v020_v001_2026-10-07.zip'
SP = DEL / 'enemy_patrol_seven_directions_v013_s002_2026-10-06.zip'
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(ZP.read_bytes()) == '6a22203fde428f0820e3019ad5ae859159b4b39c35bcfe111190fc96c75c1e52'
assert sha(SP.read_bytes()) == '28951089e1403c65f6a8446aed5f049fdba704809175da36a391c6c5fa1e99a1'
z, static = ZipFile(ZP), ZipFile(SP)
rig = json.loads(z.read('rig.json'))
catalog = json.loads(z.read('output/catalog.json'))
image = lambda name: np.array(Image.open(BytesIO(z.read(name))).convert('RGBA'))
yy, xx = np.indices((128, 128))
X, Y = xx + .5, yy + .5

def poly(shape):
    result = np.zeros((128, 128), bool)
    for (x1, y1), (x2, y2) in zip(shape, shape[1:] + shape[:1]):
        if y1 != y2:
            result ^= ((y1 > Y) != (y2 > Y)) & (X < (x2-x1)*(Y-y1)/(y2-y1)+x1)
    return result

def masks_for(config):
    protected = np.zeros((128, 128), bool)
    for shape in config['protected_body_polygons']:
        protected |= poly(shape)
    masks = {'body': np.ones((128, 128), bool)}
    for p in config['parts']:
        masks['body'] &= ~poly(p['polygon'])
    masks['body'] |= protected
    for p in config['parts']:
        m = poly(p['polygon'])
        for exclusion in p['exclude']:
            m &= ~poly(exclusion)
        masks[p['id']] = m & ~protected
    return masks, protected

def knee(bob, depth, lift):
    hip, ankle = np.array([32-bob/.75, 0.]), np.array([8+lift, depth])
    axis = ankle-hip
    length = np.linalg.norm(axis)
    unit = axis/length
    return hip+axis/2+np.array([unit[1], -unit[0]])*math.sqrt(max(0, 169-length*length/4))

def round_away(value):
    return math.copysign(math.floor(abs(value)+.5), value)

def projected(delta, config):
    return np.array([round_away(delta[1]*config['heading'][0]*.7),
                     round_away(-delta[0]*.75+delta[1]*.35*config['heading'][1])])

sources, owners, rigid, segments, tool_samples = [], [], [], [], []
source_masks = {}
pose_error = endpoint_error = 0.
for d, c in rig['configs'].items():
    name = c['source'].replace('res://', '')
    assert z.read(name) == static.read('neutral_'+d+'.png')
    assert sha(z.read(name)) == c['source_sha256']
    sources.append({'direction': d, 's002_byte_same': True, 'sha256': c['source_sha256']})
    native, opaque = image(name), image(name)[:, :, 3] >= 128
    masks, protected = masks_for(c)
    source_masks[d] = masks
    counts = {p: int((mask & opaque).sum()) for p, mask in masks.items()}
    multiplicity = sum(mask.astype(int) for mask in masks.values())
    missing = np.argwhere(opaque & (multiplicity == 0))[:, [1, 0]].tolist()
    overlap = np.argwhere(opaque & (multiplicity > 1))[:, [1, 0]].tolist()
    assert not missing and (len(overlap) == 20 if d == 'up_right' else not overlap)
    assert all(not mask[protected].any() for p, mask in masks.items() if p != 'body')
    owners.append({'direction': d, 'protected_body_opaque': int((protected & opaque).sum()),
                   'counts': counts, 'missing_opaque': missing,
                   'shared_opaque': [{'source': [x, y], 'RGBA': native[y, x].tolist(),
                                     'owners': [p for p, mask in masks.items() if mask[y, x]]}
                                    for x, y in overlap]})
    clip = next(q for q in catalog['clips'] if q['direction'] == d)
    by_id = {p['id']: p for p in c['parts']}
    for pose in clip['poses']:
        f, transforms = pose['frame'], pose['part_transforms']
        phase = rig['phases'][f]
        assert transforms['body']['basis_x'] == [1., 0.] and transforms['body']['basis_y'] == [0., 1.]
        assert transforms['body']['position'] == [0., phase['body_y']]
        for side in ['left', 'right']:
            rest, support, foot = c['legs'][side], pose['supports'][side], phase[side]
            expected_hip = np.array(rest['hip'])+[0, phase['body_y']]
            expected_knee = np.array(rest['knee'])+projected(knee(phase['body_y'], foot['depth'], foot['lift'])-knee(0, 0, 0), c)
            expected_ankle = np.array(rest['ankle'])+projected(np.array([foot['lift'], foot['depth']]), c)
            for key, expected in [('hip', expected_hip), ('knee', expected_knee), ('ankle', expected_ankle)]:
                pose_error = max(pose_error, float(np.max(np.abs(np.array(support[key])-expected))))
            for suffix, joint in [('cap', 'knee'), ('foot', 'ankle')]:
                t = transforms[side+'_'+suffix]
                assert t['basis_x'] == [1., 0.] and t['basis_y'] == [0., 1.] and t['position'] == support[joint]
            if support['support']:
                assert support['sole'] == support['ground']
            for suffix in ['thigh', 'shin']:
                p = by_id[side+'_'+suffix]
                t = transforms[p['id']]
                basis = np.array([t['basis_x'], t['basis_y']]).T
                source_axis = np.array(p['end'])-p['pivot']
                start = np.array(t['position'])
                end = start+basis@source_axis
                expected_start = expected_hip if suffix == 'thigh' else expected_knee+np.array(p['pivot'])-rest['knee']
                expected_end = expected_knee+np.array(p['end'])-rest['knee'] if suffix == 'thigh' else expected_ankle+np.array(p['end'])-rest['ankle']
                error = max(float(np.max(np.abs(start-expected_start))), float(np.max(np.abs(end-expected_end))))
                endpoint_error = max(endpoint_error, error)
                unit = source_axis/np.linalg.norm(source_axis)
                normal = np.array([-unit[1], unit[0]])
                axis_ratio, normal_ratio = float(np.linalg.norm(basis@unit)), float(np.linalg.norm(basis@normal))
                collapsed = axis_ratio == normal_ratio == 0
                assert collapsed or (abs(normal_ratio-1) < 1e-5 and np.linalg.det(basis) > 0)
                segments.append({'direction': d, 'frame': f, 'part': p['id'],
                                 'source_pivot': p['pivot'], 'source_end': p['end'], 'source_opaque': counts[p['id']],
                                 'target_start': start.tolist(), 'target_end': end.tolist(), 'endpoint_error': error,
                                 'axis_ratio': axis_ratio, 'normal_ratio': normal_ratio, 'collapsed': collapsed})
        rigid.append({'direction': d, 'frame': f, 'body_tools_caps_boots_basis_identity': True})
    ys, xs = np.where(protected & opaque)
    for f in [2, 6]:
        out = image(f'output/enemy_patrol/move_{d}/f{f:02}.png')
        dy = rig['phases'][f]['body_y']
        assert np.array_equal(out[ys+dy, xs], native[ys, xs])
        tool_samples.append({'direction': d, 'frame': f, 'opaque_count': len(xs), 'RGBA_diff': 0})
assert pose_error < 1e-5 and endpoint_error < 1e-5

config = rig['configs']['up_right']
poses = next(q['poses'] for q in catalog['clips'] if q['direction'] == 'up_right')
native = image('source/up_right.png')
order = [('body', 5, [0, 0])]+[(p['id'], p['z'], p['pivot']) for p in config['parts']]
order = sorted(enumerate(order), key=lambda v: (v[1][1], v[0]))

def trace(frame, output_xy):
    pose = poses[frame]
    contributions = []
    for i, (part, zi, pivot) in order:
        t = pose['part_transforms'][part]
        basis = np.array([t['basis_x'], t['basis_y']]).T
        if abs(np.linalg.det(basis)) < 1e-9:
            continue
        source = np.floor(np.linalg.solve(basis, np.array(output_xy)+.5-t['position'])+pivot).astype(int)
        sx, sy = source
        if 0 <= sx < 128 and 0 <= sy < 128 and source_masks['up_right'][part][sy, sx] and native[sy, sx, 3] >= 128:
            contributions.append({'part': part, 'source': source.tolist(), 'RGBA': native[sy, sx].tolist(), 'z': zi})
    out = image(f'output/enemy_patrol/move_up_right/f{frame:02}.png')
    actual = out[output_xy[1], output_xy[0]].tolist()
    assert contributions and actual == contributions[-1]['RGBA']
    return {'frame': frame, 'output': output_xy, 'actual_RGBA': actual, 'visible': contributions[-1], 'stack': contributions}

duplicates = [trace(f, p) for f, points in [(2, [[62, 89], [64, 86], [62, 96], [62, 92]]),
                                          (4, [[60, 91], [63, 88], [59, 97], [65, 95]])] for p in points]
white_strip = [trace(f, p) for f, points in [(3, [[61, 83], [61, 84], [59, 85]]),
                                           (4, [[61, 84], [61, 85], [59, 86]])] for p in points]
source_light_mask = source_masks['up_right']['left_thigh'] & (native[:, :, 3] >= 128) & (native[:, :, 0] >= 170) & (native[:, :, 1] >= 160) & (native[:, :, 2] >= 140)
report = {
    'status': 'NEEDS_REVISION_P2_NE_SHARED_SOURCE_AND_SCALED_PALE_ARMOR',
    'scope': 'Source/code/registration32 poses; 8 toolROI sets, 8 NE duplication points, 6 NE pale-thigh points only. No full32 raster reconstruction, manifest, cold, GPU or browser.',
    'zip_sha256': sha(ZP.read_bytes()), 's002_zip_sha256': sha(SP.read_bytes()),
    'bindings': {n: sha(z.read(n)) for n in ['rig.gd', 'rig.json', 'masked_part.gdshader', 'output/catalog.json']},
    'sources': sources, 'source_ownership': owners, 'rigid_core_poses': rigid, 'tool_output_samples': tool_samples,
    'pose_math_max_error': pose_error, 'connector_endpoint_max_error': endpoint_error, 'connectors': segments,
    'collapsed_connectors': [s for s in segments if s['collapsed']],
    'NE_visible_shared_source_points': duplicates, 'NE_visible_pale_thigh_points': white_strip,
    'NE_left_thigh_pale_source_pixels': [[int(x), int(y), native[y, x].tolist()] for y, x in np.argwhere(source_light_mask)],
    'NE_left_thigh_f03_f04_axis_scale': [s for s in segments if s['direction'] == 'up_right' and s['part'] == 'left_thigh' and s['frame'] in [3, 4]],
    'interpretation': 'Four native sources are byte-identical to accepted S002. Tools/body/caps/boots use translation-only identity bases. Short thigh/shin strips stretch axially; two N strips collapse at coincident endpoints. NE has20 opaque source pixels assigned to both legs, with actual dual visible cap/boot source samples in F02/F04. NE left_thigh also contains15 pale armor pixels, so claiming all scaled connector source is only dark internal strips would be inaccurate.',
    'visual_boundary': 'Do not reject solely by matrix scale or overlap count. Actual neighboring-leg fragment assignment and pale upper armor continuity must be adjudicated at the listed visible coordinates by root/visual TA; neutral RGBA0 does not rule out the confirmed dual posed reuse.',
    'root_disposition': 'Root TA subsequently confirmed both NE findings as local P2 using actual8x images and browser F03, and notified producer. N zero-determinant joining strips were explicitly excluded from the rejection. No further testing after this decision.',
    'minimum_repair_if_confirmed': 'Disambiguate NE left/right source masks using the actual leg edges; keep mother RGB and phase/support unchanged. Separate rigid pale armor from the stretched seam strip if its visible extension is rejected. No new generation of whole frames.'
}
(OUT/'technical-rigidity-crosscheck.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'status': report['status'], 'owners': [{k:v for k,v in o.items() if k != 'shared_opaque'} | {'shared_count': len(o['shared_opaque'])} for o in owners],
                  'pose_error': pose_error, 'endpoint_error': endpoint_error, 'pale_source_count': int(source_light_mask.sum())}))
