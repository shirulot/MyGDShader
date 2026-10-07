"""rc02 独立增量核验：从两个固定 ZIP 取值，不运行生产脚本或引擎。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import hashlib
import json
import math
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
DELIVERIES = ROOT / 'art-source/ember/deliveries'
ACTIVE = ROOT / 'art-source/ember/robot-eight-way-v011/review/phase-a-rc02'
OLD = DELIVERIES / 'robot_eight_way_v011_phase_a_rc01_2026-10-06.zip'
NEW = DELIVERIES / 'robot_eight_way_v011_phase_a_rc02_2026-10-06.zip'
EXPECTED = 'df9884f9668dc89b8c74cf746dbd975a87e9a5b566b6783b5582cb2c78b4d521'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def parse(data):
    return json.loads(data.decode('utf-8-sig'))

def image(data):
    return Image.open(BytesIO(data)).convert('RGBA')

def arr(data):
    return np.array(image(data))

def count_diff(a, b):
    return int(np.any(a != b, axis=2).sum())

assert sha(NEW.read_bytes()) == EXPECTED
with ZipFile(OLD) as old, ZipFile(NEW) as new:
    assert old.testzip() is None and new.testzip() is None
    oldfiles = {n: old.read(n) for n in old.namelist() if not n.endswith('/')}
    files = {n: new.read(n) for n in new.namelist() if not n.endswith('/')}
    manifest = parse(files['sha256-manifest.json'])['files']
    assert len(manifest) == 210
    assert {r['file'] for r in manifest} == set(files) - {'sha256-manifest.json'}
    for row in manifest:
        data = files[row['file']]
        assert len(data) == row['bytes'] and sha(data) == row['sha256']
    active_match = []
    for name, data in files.items():
        assert (ACTIVE/name).read_bytes() == data
        active_match.append(name)
    # 解压仅在本审查目录；完整 ZIP 是审查事实来源。
    package = OUT/'package'
    package.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        dest = package/name
        assert dest.resolve().is_relative_to(package.resolve())
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    common = set(oldfiles) & set(files)
    changed = sorted(n for n in common if oldfiles[n] != files[n])
    added = sorted(set(files)-set(oldfiles))
    assert not set(oldfiles)-set(files)
    immutable_source = sorted(n for n in oldfiles if n.startswith('source/'))
    assert all(oldfiles[n] == files[n] for n in immutable_source)
    # 源拆分/rig/参考与原先完整技术审查完全一致，故继承其分区结果。
    rigpath = 'source/fixed-rig-pilot/down_left/rig_and_poses.json'
    ledger = parse(files[rigpath])
    part = arr(files['source/fixed-parts/down_left/leg_right_upper.png'])
    selected = part[:, :, 3] > 0
    selected[63:] = False
    ys, xs = np.where(selected)
    rect = [int(xs.min())-1, int(ys.min()), int(xs.max()-xs.min())+3, 63-int(ys.min())]
    assert rect == [20, 54, 12, 9]
    source_mask = np.zeros((96, 64, 4), np.uint8)
    x, y, w, h = rect
    source_mask[y:y+h, x:x+w] = 255
    patch = parse(files['qa/down_left_joint_patch_v011.json'])
    assert patch['rigid_armor_rule'] == {'part':'leg_right_upper', 'max_source_y':62,
        'contour_margin_x':1, 'source_protection_rect':rect}
    records = []
    for i, state in enumerate(ledger['states']):
        t = state['transforms']['leg_right_upper']
        assert set(t) == {'sourcePivot', 'targetPivot', 'radians'}
        c, s = math.cos(t['radians']), math.sin(t['radians'])
        sp, tp = t['sourcePivot'], t['targetPivot']
        mask = np.zeros_like(source_mask)
        # 独立逆映射源矩形；没有拿作者导出的 mask 决定允许区域。
        for py in range(96):
            for px in range(64):
                dx, dy = px+.5-tp[0], py+.5-tp[1]
                sx, sy = math.floor(dx*c+dy*s+sp[0]), math.floor(-dx*s+dy*c+sp[1])
                if 0 <= sx < 64 and 0 <= sy < 96 and source_mask[sy, sx, 3]:
                    mask[py, px] = source_mask[sy, sx]
        assert np.array_equal(mask, arr(files[f'qa/down_left_rigid_armor_mask_f{i:02d}.png']))
        frame = f'frames/walk/down_left/robot_walk_down_left_f{i:02d}_v011.png'
        before, after = arr(oldfiles[frame]), arr(files[frame])
        assert files[f'source/reference-phase-a-rc01/frames/robot_walk_down_left_f{i:02d}_v011.png'] == oldfiles[frame]
        pilot = arr(files[f'source/fixed-rig-pilot/down_left/robot_walk_down_left_f{i:02d}_v011.png'])
        allowed = mask[:, :, 3] > 0
        expected = before.copy()
        expected[allowed] = pilot[allowed]
        assert np.array_equal(expected, after)
        diff = np.any(before != after, axis=2)
        assert not np.any(diff & ~allowed)
        oldmask = arr(oldfiles[f'qa/down_left_joint_patch_mask_f{i:02d}.png'])
        expected_mask = oldmask.copy()
        expected_mask[allowed] = 0
        assert np.array_equal(expected_mask, arr(files[f'qa/down_left_joint_patch_mask_f{i:02d}.png']))
        actualchanges = []
        for py, px in zip(*np.where(np.any(pilot != after, axis=2))):
            actualchanges.append({'xy':[int(px),int(py)], 'before':pilot[py,px].tolist(), 'after':after[py,px].tolist()})
        claimed = patch['records'][i]
        assert [{k:row[k] for k in ['xy','before','after']} for row in claimed['changes']] == actualchanges
        assert claimed['changed_pixels'] == len(actualchanges)
        assert claimed['restored_armor_pixels_from_rc01'] == int(diff.sum())
        assert claimed['output_sha256'] == sha(files[frame])
        records.append({'frame':i, 'rc01_to_rc02_full_rgba_changed_pixels':int(diff.sum()),
            'outside_independently_rebuilt_armor_mask_changed_pixels':int((diff & ~allowed).sum()),
            'inside_armor_fixed_rig_rgba_difference':count_diff(after*allowed[:,:,None],pilot*allowed[:,:,None]),
            'restoration_exact_full_frame':True, 'changed_pixels_vs_unedited_rig':len(actualchanges),
            'change_coordinates':[[int(px),int(py)] for py,px in zip(*np.where(diff))]})
    assert [r['rc01_to_rc02_full_rgba_changed_pixels'] for r in records] == [41,36,25,18,17,16,31,47]

    meta = parse(files['phase-a-metadata.json'])
    assert meta['canvas'] == [64,96] and meta['root_anchor'] == [32,80] and meta['texture_scale'] == 1
    assert meta == parse(files['godot-review/phase-a-metadata.json'])
    atlas = arr(files[meta['atlas']])
    assert atlas.shape == (288,512,4)
    assert sha(files[meta['atlas']]) == meta['atlas_sha256']
    assert files['godot-review/assets/robot_phase_a_atlas_v011.png'] == files[meta['atlas']]
    clips = {c['name']:c for c in meta['clips']}
    assert len(clips) == 10
    allframes = []
    for clip in meta['clips']:
        walk = clip['name'].startswith('walk_')
        assert (len(clip['frames']),clip['fps'],clip['loop']) == ((8,8,True) if walk else (1,1,False))
        for frame in clip['frames']:
            data = files[frame['file']]
            rgba = arr(data)
            assert rgba.shape == (96,64,4) and set(np.unique(rgba[:,:,3])) <= {0,255}
            assert sha(data) == frame['sha256']
            x,y,w,h = frame['region']
            assert np.array_equal(rgba,atlas[y:y+h,x:x+w])
            allframes.append(frame['file'])
    assert len(set(allframes)) == 24
    immutable_final = [n for n in allframes if not n.startswith('frames/walk/down_left/')]
    assert len(immutable_final) == 16 and all(oldfiles[n] == files[n] for n in immutable_final)
    runtime = sorted(n for n in common if n.startswith('godot-review/') and n.endswith(('.tres','.gd','.tscn','.godot')))
    assert all(files[n] == oldfiles[n] for n in runtime)

    # 静态验证作者保存的 48 张 GPU 回读，不冒充本轮引擎重跑。
    gpu = parse(files['qa/godot_phase_a_v011.json'])
    assert gpu['atlas_sha256'] == meta['atlas_sha256'] and len(gpu['cases']) == 48
    gpu_cases = []
    for case in gpu['cases']:
        frame = clips[case['clip']]['frames'][int(case['frame'])]
        im = image(files[frame['file']])
        factor = case['scale']
        expected = im.resize((im.width*factor,im.height*factor),Image.Resampling.NEAREST)
        actual = image(files[case['file']])
        assert expected.size == actual.size and expected.tobytes() == actual.tobytes()
        gpu_cases.append({'clip':case['clip'],'frame':int(case['frame']),'scale':factor,
            'file':case['file'],'sha256':sha(files[case['file']]),'saved_capture_full_rgba_difference':0})
    assert len({(r['clip'],r['frame'],r['scale']) for r in gpu_cases}) == 48
    assert len(gpu['natural_playback']) == 2
    for playback in gpu['natural_playback']:
        assert playback['actual_loops'] == 2
        assert [r['frame'] for r in playback['sequence']] == list(range(8))*2+[0,1]
        assert all(b['elapsed_ms'] > a['elapsed_ms'] for a,b in zip(playback['sequence'],playback['sequence'][1:]))
    result = {'status':'RC02_LOCAL_TECHNICAL_INCREMENT_PASS', 'zip_sha256':EXPECTED,
        'zip_bytes':NEW.stat().st_size,'zip_entries':len(new.namelist()),'manifest_payloads':len(manifest),
        'crc':'all entries pass','active_fixed_snapshot_same_files':len(active_match),
        'old_zip_sha256':sha(OLD.read_bytes()),'common_changed_files':changed,'added_files':added,
        'removed_files':[], 'unchanged_old_source_payloads':immutable_source,'unchanged_runtime_files':runtime,
        'immutable_non_SW_final_pngs':immutable_final,'armor_source_rect':rect,'records':records,
        'full_rgba_restored_pixels_total':sum(r['rc01_to_rc02_full_rgba_changed_pixels'] for r in records),
        'frame_pngs':24,'clips':10,'atlas_sha256':meta['atlas_sha256'],
        'saved_gpu_capture_cases':gpu_cases,'producer_natural_playback_records':gpu['natural_playback'],
        'ta_engine_rerun':False,'acceptance_limit':'Local pixel/source/resource verification; motion/visual acceptance remains the root TA review.'}
    (OUT/'evidence-increment.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['status','zip_bytes','zip_entries','manifest_payloads',
        'active_fixed_snapshot_same_files','armor_source_rect','full_rgba_restored_pixels_total','frame_pngs','clips','atlas_sha256']},ensure_ascii=False,indent=2))
    print('restored_by_frame', [r['rc01_to_rc02_full_rgba_changed_pixels'] for r in records])
    print('immutable_source',len(immutable_source),'unchanged_runtime',len(runtime),'saved_gpu',len(gpu_cases))
