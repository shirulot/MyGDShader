"""绑定最终像素、实际Godot结果与主审复核；不修改任何生产素材。"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
PROOF = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets/ember/characters/robot'
CATALOG = ASSETS / 'robot_frames_catalog_v002.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def rel(path):
    return path.relative_to(ROOT).as_posix()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    catalog = read(CATALOG)
    record = read(PROOF / 'repair-record-v002.json')
    pixels = read(PROOF / 'independent/candidate-pixel-measurements.json')
    rigs = read(PROOF / 'independent/independent-rig-ownership.json')
    prior_path = ROOT / 'art-source/ember/quality-audit-2026-10-04/robot/robot-quality-review.json'
    prior = read(prior_path)
    checks = []

    def check(name, passed):
        checks.append({'check': name, 'pass': bool(passed)})

    check('published new revision only', record['status'] == 'V002_PUBLISHED_NEW_FILES_ONLY')
    check('20 measured frames / no numerical failures', len(pixels['frames']) == 20 and not pixels['failures'])
    check('51 explicit rig ownership / motion checks', rigs['status'] == 'PASS' and len(rigs['checks']) == 51 and not rigs['failed_checks'])
    for name, expected in rigs['source_sha256'].items():
        check('rig dependency ' + name, sha(ROOT / name) == expected)
    check('rig ownership proof image', sha(ROOT / rigs['ownership_visual']) == rigs['ownership_visual_sha256'])
    check('10 pixel-changed walk frames', sum(f['changed_pixel_count'] > 0 for f in record['frames']) == 10)
    check('all 16 source motions unchanged', all(f['old_gait']['phase'] == f['new_gait']['phase'] for f in record['frames']))
    check('catalog binds published repair record', catalog['repair_record_sha256'] == sha(PROOF / 'repair-record-v002.json'))
    for name, expected in catalog['repair_dependency_sha256'].items():
        check('native source dependency ' + name, sha(ROOT / name) == expected)
    sheet = Image.open(ROOT / catalog['sheet']['texture'].removeprefix('res://')).convert('RGBA')
    check('native atlas SHA', sha(ROOT / catalog['sheet']['texture'].removeprefix('res://')) == catalog['sheet']['sha256'])
    check('native atlas size', sheet.size == (320, 384))
    by_id = {f['id']: f for f in catalog['frames']}
    measurements = {f['id']: f for f in pixels['frames']}
    for frame in catalog['frames']:
        path = ROOT / frame['file'].removeprefix('res://')
        check('published PNG ' + frame['id'], sha(path) == frame['sha256'] == pixels['asset_sha256'][frame['id']])
        x, y = frame['coord']
        image = Image.open(path).convert('RGBA')
        check('raw atlas crop ' + frame['id'], sheet.crop((x * 64, y * 96, (x + 1) * 64, (y + 1) * 96)).tobytes() == image.tobytes())
        m = measurements[frame['id']]
        check('one connected body / binary alpha / palette ' + frame['id'],
              len(m['components_8']) == 1 and set(m['alpha_values']) <= {0, 255} and not m['off_palette_pixels'])
        check('unchanged head and bronze tool ' + frame['id'],
              m['unchanged_head_region']['changed_rgba_pixels'] == 0 and m['bronze_tool_regions_changed_pixels'] == 0)
    for frame in record['frames']:
        check('formal equals editable-source output ' + frame['id'],
              sha(ROOT / frame['new_file']) == sha(ROOT / frame['finished_file']) == frame['new_sha256'] and frame['formal_output_written'])
        for field in ['old_file', 'old_annotation', 'new_annotation', 'rig']:
            digest_key = field.replace('_file', '') + '_sha256' if field == 'old_file' else field + '_sha256'
            if field == 'rig': digest_key = 'rig_sha256'
            check('source record ' + frame['id'] + ' ' + field, sha(ROOT / frame[field]) == frame[digest_key])
    # 固定调色板GIF与精确125ms APNG逐帧解码，防止预览量化引入新颜色。
    background = (81, 101, 112, 255)
    for direction in ['down', 'left', 'right', 'up']:
        for suffix, timings in [('8fps_4x.apng', [125] * 4), ('fixed_palette_4x.gif', [120, 130, 120, 130])]:
            preview = Image.open(PROOF / 'previews' / f'walk_{direction}_v002_{suffix}')
            check(direction + ' preview frame count ' + suffix, preview.n_frames == 4)
            for number in range(4):
                preview.seek(number)
                current = preview.convert('RGB')
                source = Image.open(ROOT / by_id[f'robot_walk_{direction}_f{number:02d}']['file'].removeprefix('res://')).convert('RGBA')
                bg = Image.new('RGBA', source.size, background)
                bg.alpha_composite(source)
                expected = bg.convert('RGB').resize((256, 384), Image.Resampling.NEAREST)
                check(f'{direction} preview exact pixels {suffix} f{number}', current.tobytes() == expected.tobytes())
                check(f'{direction} preview timing {suffix} f{number}', preview.info['duration'] == timings[number])
    # 主审实际查看过的图像清单；这不是另一代理完成最终视觉审查的声明。
    viewed = [PROOF / 'independent' / (f['id'] + '-current-1x-4x.png') for f in catalog['frames']]
    viewed += [PROOF / 'independent' / (d + '-complete-loop-4x.png') for d in ['down', 'left', 'right', 'up']]
    reviewed_ids = ['robot_walk_left_f02', 'robot_walk_down_f01', 'robot_walk_down_f03',
                    'robot_walk_left_f00', 'robot_walk_right_f02', 'robot_walk_left_f01',
                    'robot_walk_left_f03', 'robot_walk_right_f03']
    viewed += [PROOF / 'independent' / (i + '-before-after-diff-4x.png') for i in reviewed_ids]
    viewed += [PROOF / 'independent/left-boot-native-ownership-before-after-12x.png',
               PROOF / 'godot-robot-v002.png', PROOF / 'fresh-godot-robot-v002.png']
    viewed += [PROOF / 'render' / (i + '_2x.png') for i in ['robot_walk_left_f02', 'robot_walk_down_f01', 'robot_walk_right_f02']]
    decisions = {
        'ROBOT_LEFT_02_DETACHED': '近侧靴子的14个源像素统一归入left_leg；完整靴边随同一位移移动，原14像素游离块已消失。',
        'ROBOT_DOWN_01_DETACHED': '中央髋部源像素随torso移动；原1像素游离块消失，保留腿间开口。',
        'ROBOT_DOWN_03_DETACHED': '中央髋部源像素随torso移动；原2像素游离块消失，保留腿间开口。',
        'ROBOT_LEFT_00_SHOULDER_VERTICAL_CUT': '左右肩连接逐像素补齐；胸侧负空间仍保留，完整循环无肩片游离。',
        'ROBOT_RIGHT_02_SHOULDER_VERTICAL_CUT': '双肩连接逐像素补齐；外轮廓和抬臂相位保持一致。',
        'ROBOT_LEFT_01_HIP_HORIZONTAL_CUT': '髋部局部连接带恢复；两腿分离轮廓保留。',
        'ROBOT_LEFT_03_HIP_HORIZONTAL_CUT': '髋部支撑腿连接恢复；完整近侧靴抬高2px，bbox底边78是原固定步态下的正确投影。',
        'ROBOT_RIGHT_03_HIP_HORIZONTAL_CUT': '髋部局部连接带恢复；整周期保持腿间开口和支撑相位。',
    }
    check('all 3 confirmed + 5 seam candidates explicitly reviewed', set(decisions) == {i['id'] for i in prior['issues']})
    regression = read(PROOF / 'independent/other-art-and-tiles-after.json')
    check('204 other art / tile dependencies unchanged', regression['status'] == 'PASS' and regression['checked_files'] == 204)
    baseline = read(PROOF / 'protected-before.json')
    allowed = set(baseline['allowed_document_updates'])
    changed_allowed = []
    for name, expected in baseline['sha256'].items():
        identical = (ROOT / name).is_file() and sha(ROOT / name) == expected
        if name in allowed:
            if not identical: changed_allowed.append(name)
        else:
            check('prior protected ' + name, identical)
    check('only two authorized delivery pointers changed', set(changed_allowed) == allowed)
    for baseline_name in ['protected-inputs-before.json', 'godot-protected-before.json']:
        before = read(PROOF / baseline_name)
        hashes = before['sha256'] if 'sha256' in before else before
        for name, expected in hashes.items():
            # 各冻结清单有交叠；同一授权文档入口在所有清单中使用相同例外。
            if name not in allowed: check(baseline_name + ' ' + name, sha(ROOT / name) == expected)
    stages = read(PROOF / 'godot-stage-exits.json')
    check('all 9 actual Godot stages', {s['stage'] for s in stages['stages']} ==
          {'syntax', 'import', 'import-settings', 'build', 'verify', 'render', 'fresh-import', 'fresh-verify', 'fresh-render'})
    builder = ROOT / 'tools/build_ember_robot_animation_v002.gd'
    check('executed builder SHA', stages['builder_sha256'] == sha(builder))
    for stage in stages['stages']:
        check('stage exit and stderr ' + stage['stage'], stage['exit_code'] == 0 and stage['stderr_bytes'] == 0)
        for kind in ['stdout', 'stderr']:
            check('stage log ' + stage['stage'] + ' ' + kind, sha(PROOF / stage[kind + '_log']) == stage[kind + '_sha256'])
    reports = ['godot-validation.json', 'godot-verify-only.json', 'godot-render.json', 'fresh-godot-verify.json', 'fresh-godot-render.json']
    for report_name in reports:
        report = read(PROOF / report_name)
        observed = report['observed']
        check('Godot result ' + report_name, report['status'] == 'GODOT_ROBOT_ANIMATION_VALIDATED' and
              report['catalog_sha256'] == sha(CATALOG) and report['builder_sha256'] == sha(builder))
        check('20 native regions and 8 clips ' + report_name, observed['native_regions_equal_to_source'] == 20 and observed['sprite_frames_clip_count'] == 8)
        check('8 complete walk cycles / 8 static idle ' + report_name, observed['runtime_walk_complete_cycle_count'] == 8 and observed['runtime_idle_static_count'] == 8)
        check('20 connected native frames ' + report_name, len(observed['native_frame_8_components']) == 20 and all(n == 1 for n in observed['native_frame_8_components'].values()))
        for name, expected in observed['source_sha256'].items(): check('Godot source ' + report_name + ' ' + name, by_id[name]['sha256'] == expected)
        readbacks = observed['source_import_readbacks']
        check('21 import readbacks ' + report_name, len(readbacks) == 21)
        for texture in readbacks:
            check('import unchanged visible pixels ' + report_name + ' ' + texture['path'],
                  texture['alpha_changed'] == texture['visible_rgb_changed'] == 0 and sha(ROOT / texture['path'].removeprefix('res://')) == texture['sha256'])
        if 'gpu_frame_cases' in observed:
            check('40 actual GPU cases ' + report_name, observed['gpu_frame_case_count'] == len(observed['gpu_frame_cases']) == 40)
            for case in observed['gpu_frame_cases']:
                gpu_path = Path(case['file'])
                factor = case['factor']
                source = Image.open(ROOT / by_id[case['id']]['file'].removeprefix('res://')).convert('RGBA').resize((64 * factor, 96 * factor), Image.Resampling.NEAREST)
                actual = np.asarray(Image.open(gpu_path).convert('RGBA'))
                expected = np.asarray(source)
                # Alpha=0处的RGB无视觉意义；旧idle保留原导入策略导致边缘RGB填充。
                check('actual GPU pixel comparison ' + report_name + ' ' + case['id'] + str(factor),
                      sha(gpu_path) == case['screenshot_sha256'] and case['source_sha256'] == by_id[case['id']]['sha256'] and
                      case['visible_rgb_changed'] == case['alpha_changed'] == 0 and
                      actual.shape == expected.shape and np.array_equal(actual[:, :, 3], expected[:, :, 3]) and
                      np.array_equal(actual[:, :, :3][expected[:, :, 3] > 0], expected[:, :, :3][expected[:, :, 3] > 0]))
    fresh = read(PROOF / 'fresh-copy-before.json')
    check('fresh no previous cache / no autoload / 84 copies', fresh['cache_absent_before_import'] and fresh['autoload_absent'] and len(fresh['sha256']) == 84)
    for name, expected in fresh['sha256'].items(): check('fresh copied input unchanged ' + name, sha(PROOF / 'fresh-project-v001' / name) == expected)
    rendered = list((PROOF / 'render').glob('*.png'))
    check('main/fresh 40 identical raw screenshots', len(rendered) == 40 and all(sha(p) == sha(PROOF / 'fresh-render' / p.name) for p in rendered))
    totals = (len(list((ROOT / 'assets/ember').rglob('*.png'))), len(list((ROOT / 'assets/ember').rglob('*.tres'))), len(list((ROOT / 'scenes/ember').rglob('*.tscn'))))
    check('122 PNG / 17 resources / 5 scenes including retained versions', totals == (122, 17, 5))
    review = {'status': 'ROOT_VISUAL_AND_STANDALONE_MEASUREMENT_REVIEW_PASS', 'date': '2026-10-04',
        'producer': '/root/robot_break_audit', 'integration_author': '/root/tile_break_audit',
        'standalone_measurement_author': '/root/other_art_break_audit', 'final_visual_reviewer': '/root',
        'independent_agent_final_visual_review_completed': False,
        'reviewer_note': 'Delegated final reviewer reached usage limits. Root viewed the final20 native/4x boards,4 complete-loop strips,8 before/after comparisons,ownership proof,2 engine overviews and3 raw GPU examples; root extended the standalone ownership checker for the additional11 wrist pixels. Numerical checker does not import producer code.',
        'asset_sha256': pixels['asset_sha256'], 'catalog_sha256': sha(CATALOG), 'prior_quality_review_sha256': sha(prior_path),
        'closed_confirmed_issues': [i for i in decisions if i.endswith('_DETACHED')],
        'resolved_joint_seam_candidates': [i for i in decisions if not i.endswith('_DETACHED')],
        'decisions': decisions, 'additional_wrist_review': '11 steel forearm/wrist pixels now belong to the contiguous left_arm; tool colours/ownership and all original motion offsets are preserved.',
        'retained_negative_space': 'Leg separation, tool/background openings and small back-view shoulder openings retain their intended silhouette; no whole-image hole filling.',
        'viewed_image_sha256': {rel(p): sha(p) for p in viewed},
        'measurement_report_sha256': sha(PROOF / 'independent/candidate-pixel-measurements.json'),
        'ownership_report_sha256': sha(PROOF / 'independent/independent-rig-ownership.json')}
    # 只有所有自动证据通过，才发布这份已完成的主审结论。
    failures = [c['check'] for c in checks if not c['pass']]
    if failures:
        write(PROOF / 'acceptance-failure.json', {'failures': failures, 'checks': checks})
        raise SystemExit('Acceptance failed: ' + str(failures))
    failure_path = PROOF / 'acceptance-failure.json'
    if failure_path.is_file(): failure_path.unlink()  # 仅清除本工具上一次生成的临时失败诊断。
    write(PROOF / 'independent-repair-review.json', review)
    evidence = {}
    for path in PROOF.rglob('*'):
        if not path.is_file() or path.name in {'final-acceptance.json', 'acceptance-failure.json'}: continue
        if any(part.startswith('fresh-project-') or part in {'.godot', '__pycache__'} for part in path.parts): continue
        if path.suffix == '.pyc': continue
        evidence[rel(path)] = sha(path)
    for path in [CATALOG, ASSETS / 'robot_sprite_frames_v002.tres', ROOT / 'scenes/ember/robot_animation_sandbox_v002.tscn', builder, Path(str(builder) + '.uid')]:
        evidence[rel(path)] = sha(path)
    for path in ASSETS.glob('*_v002.png*'): evidence[rel(path)] = sha(path)
    documents = {name: sha(ROOT / name) for name in list(allowed) + ['docs/shader-learning/asset-production-robot-repair-v002.md']}
    write(PROOF / 'final-acceptance.json', {'status': 'ROBOT_V002_REPAIR_FINAL_ACCEPTANCE_PASS',
        'date': '2026-10-04', 'checks': len(checks), 'failed_checks': 0, 'failures': [],
        'accepted_catalog_sha256': sha(CATALOG), 'accepted_review_sha256': sha(PROOF / 'independent-repair-review.json'),
        'confirmed_issues_closed': 3, 'joint_seam_candidates_resolved': 5, 'current_frames': 20,
        'new_walk_pngs': 16, 'new_atlases': 1, 'pixel_changed_frames': 10,
        'main_gpu_cases': 40, 'fresh_gpu_cases': 40, 'byte_identical_main_fresh_screenshots': 40,
        'godot_stage_count': 9, 'complete_walk_cycles_observed': 8,
        'prior_protected_files': len(baseline['sha256']), 'allowed_document_updates': sorted(allowed),
        'other_art_tile_dependency_regression': 204, 'fresh_preserved_copy_count': 84,
        'physical_production_pngs': 122, 'physical_resources': 17, 'physical_scenes': 5,
        'art_units': 123, 'technical_inputs': 40, 'additional_art_units': 0, 'new_imagegen_calls': 0,
        'frozen_previous_archives': {name: h for name, h in baseline['sha256'].items() if name.endswith('.zip')},
        'evidence_sha256': dict(sorted(evidence.items())), 'delivery_document_sha256': documents, 'results': checks})
    print(json.dumps({'status': 'ROBOT_V002_REPAIR_FINAL_ACCEPTANCE_PASS', 'checks': len(checks), 'failed_checks': 0, 'evidence_files': len(evidence)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
