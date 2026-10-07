"""按冷工程实际结果汇总，并只读复核冻结包、生产保护及截图绑定。"""
import hashlib
import json
from pathlib import Path

workspace = Path('E:/dev/shader/godot-shader/godot-shader-simple')
review = workspace / 'art-source/ember/ta-review-v001/ui-v004-independent/technical'
cold = review / 'cold-project'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

integrity = read(review / 'package-integrity.json')
interaction = read(cold / 'art-source/ember/ui-interactions-v004/interaction-validation.json')
lifecycle = read(cold / 'art-source/ember/ui-edge-v001/lifecycle-validation-v003.json')
reuse = read(cold / 'art-source/ember/ui-edge-v001/reuse-validation-v002.json')
layout = read(cold / 'art-source/ember/ui-edge-v001/layout-audit-v002.json')
independent = read(cold / 'ta-ui-probe/independent-results.json')
gpu = read(cold / 'art-source/ember/ui-interactions-v004/gpu-validation.json')
original_gpu = read(workspace / 'art-source/ember/ui-interactions-v004/gpu-validation.json')
original_summary = read(workspace / 'art-source/ember/ui-interactions-v004/validation-summary.json')
protected = [{'path':path,'unchanged':sha(workspace / path).lower() == expected.lower()} for path,expected in original_summary['protected_source_hashes'].items()]
fixed_summary = read(cold / 'art-source/ember/ui-interactions-v004/validation-summary.json')
source_bound = [{'path':path,'cold_matches_frozen_v004':sha(cold / path.removeprefix('res://')) == expected,'workspace_matches_frozen_v004':sha(workspace / path.removeprefix('res://')) == expected} for path,expected in fixed_summary['source_sha256'].items()]
original_capture_sha = {entry['path']: entry['sha256'] for entry in original_gpu['captures']}
captures = [{'path':entry['path'],'sha256':sha(cold / entry['path'].removeprefix('res://')),'matches_capture_report':sha(cold / entry['path'].removeprefix('res://')) == entry['sha256'],'matches_original_fixed_capture':entry['sha256'] == original_capture_sha[entry['path']]} for entry in gpu['captures']]
logs = [{'path':str(path.relative_to(review)), 'bytes':path.stat().st_size} for path in review.glob('*.stderr.log')]
assert integrity['status'] == interaction['status'] == lifecycle['status'] == reuse['status'] == independent['status'] == 'PASS'
assert layout['tested_layout_result'] == 'PASS' and layout['geometry_error_count'] == 0
assert all(entry['unchanged'] for entry in protected)
assert all(entry['cold_matches_frozen_v004'] for entry in source_bound)
assert all(entry['matches_capture_report'] for entry in captures)
assert all(entry['bytes'] == 0 for entry in logs)
summary = {
    'decision': 'MOUSE_KEYBOARD_TECHNICAL_PASS_GAMEPAD_REPAIR_IN_V005',
    'scope': 'Declared UI v004: horizontal life, details, terminal, pause/settings/help, restart/title confirms, title/results/toast, dedicated host preview; no full-game/M0 acceptance.',
    'fixed_zip_sha256': sha(workspace / 'art-source/ember/deliveries/ui_edge_interactions_v004_2026-10-06.zip'),
    'package_integrity_checks': integrity['check_count'],
    'runtime_replayed': {'interactions':interaction['check_count'], 'lifecycle':lifecycle['check_count'], 'reuse':reuse['check_count']},
    'independent_runtime_checks': independent['check_count'],
    'runtime_total_replayed_and_independent': interaction['check_count'] + lifecycle['check_count'] + reuse['check_count'] + independent['check_count'],
    'independent_probe_sha256': sha(cold / 'tools/ta_ui_v004_probe.gd'),
    'layout_samples': layout['sample_count'],
    'layout_geometry_errors': layout['geometry_error_count'],
    'legacy_safe_elision_notes': layout['limitation_count'],
    'gpu_captures': captures,
    'gpu_capture_count': len(captures),
    'gpu_capture_sha_equal_to_original_count': sum(entry['matches_original_fixed_capture'] for entry in captures),
    'protected_source_after_review': protected,
    'source_bound_after_review': source_bound,
    'stderr_logs': logs,
    'blocking_findings': [{'priority':'P2', 'scope':'v004 real gamepad A/B', 'reproduction':'ta-ui-probe/gamepad-v004-repro.json', 'result':'A does not open focused details; B does not close pause. Built-in ui_accept/ui_cancel contain only keyboard events. Producer submitted v005 local mapping repair.'}],
    'nonblocking_limits': ['Windows system CJK fonts; other platforms not claimed.', 'Dedicated UI host preview, not a full movement/collision game.', 'Existing safe text elision / minimum-width notes in legacy components remain bounded behavior.'],
    'visual_acceptance': 'PRIMARY_ART_REVIEW_SEPARATE',
    'review_writes_only': str(review),
}
(review / 'technical-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key:value for key,value in summary.items() if key not in ['gpu_captures', 'source_bound_after_review', 'protected_source_after_review', 'stderr_logs']}, ensure_ascii=False))
