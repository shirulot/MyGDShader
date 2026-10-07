"""汇总独立包核验、原包冷运行、隔离参数对照；再次只读核验生产保护。"""
import hashlib
import json
from pathlib import Path

workspace = Path('E:/dev/shader/godot-shader/godot-shader-simple')
review = workspace / 'art-source/ember/ta-review-v001/robot-v008-independent/technical'
base_rel = Path('art-source/ember/robot-fixed-rig-v008')

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

package = read(review / 'package-source-report.json')
cold = read(review / 'cold-playback-report.json')
control = read(review / 'control-playback-report.json')
diagnosis = read(review / 'cold-import-diagnosis.json')
baseline = read(workspace / 'art-source/ember/robot-fixed-rig-v007/source/production_baseline_sha256_v007.json')
protected_changed = [entry['file'] for entry in baseline['files'] if sha(Path(entry['file'])) != entry['sha256']]
intervals = [b['elapsed_ms'] - a['elapsed_ms'] for a, b in zip(cold['playback']['sequence'], cold['playback']['sequence'][1:])]

summary = {
    'decision': 'CONDITIONAL_TECHNICAL_PASS_REPAIR_COLD_FULL_RGBA_EVIDENCE',
    'finding_priority': 'P2',
    'scope': 'walk_down only, eight 64x96 frames, 8 FPS loop, fixed root [32,80]',
    'zip_sha256': sha(workspace / 'art-source/ember/deliveries/robot_fixed_rig_v008_walk_down_candidate_2026-10-06.zip'),
    'rig_sha256': sha(workspace / base_rel / 'source/rig_down_v008.json'),
    'package_source_checks': package['check_count'],
    'package_source_failures': package['failure_count'],
    'cold_import_exit': 0,
    'cold_verifier_exit': 1,
    'cold_full_rgba_imported_regions_passed': sum(entry['rgba_exact'] for entry in cold['imported_atlas_regions']),
    'cold_gpu_exact_cases': sum(entry['rgba_exact_to_native_png'] for entry in cold['gpu_entries']),
    'cold_gpu_total_cases': len(cold['gpu_entries']),
    'transparent_rgb_modified_count': sum(entry['transparent_rgb_changed'] for entry in diagnosis['frames']),
    'opaque_rgba_modified_count': sum(entry['opaque_changed'] for entry in diagnosis['frames']),
    'alpha_modified_count': sum(entry['alpha_changed'] for entry in diagnosis['frames']),
    'cold_natural_playback': cold['playback'],
    'cold_frame_intervals_ms': intervals,
    'control_change': 'Only add existing production PNG .import settings sidecar; do not modify native PNG, SpriteFrames, rig, poses or verifier.',
    'control_verifier_exit': 0,
    'control_technical_checks': control['technical_checks'],
    'control_full_rgba_imported_regions_passed': sum(entry['rgba_exact'] for entry in control['imported_atlas_regions']),
    'control_gpu_exact_cases': sum(entry['rgba_exact_to_native_png'] for entry in control['gpu_entries']),
    'control_natural_loops': control['playback']['actual_loops'],
    'production_protected_count': len(baseline['files']),
    'production_changed_after_audit': protected_changed,
    'original_neutral_source_opaque_pixels': 1492,
    'source_layers': 23,
    'semantic_ownership_changes': 37,
    'authored_cap_definitions': 17,
    'derived_canonical_opaque_pixels': package['canonical_opaque_pixels'],
    'derived_canonical_rgba_positions_different_to_original': package['canonical_original_rgba_difference_count'],
    'art_acceptance': 'NOT_CLAIMED',
    'minimal_repair': 'Ship portable texture import settings (fix_alpha_border=false) or explicitly revise import fidelity comparison contract to visible RGBA plus Alpha. Cold-run the declared contract and submit newly hash-bound evidence/package.',
    'evidence': ['package-source-report.json', 'cold-playback-report.json', 'cold-import-diagnosis.json', 'control-playback-report.json', 'playback-rerun.stderr.log', 'control-playback.stderr.log'],
}
assert package['failure_count'] == 0
assert summary['cold_gpu_exact_cases'] == 16
assert summary['opaque_rgba_modified_count'] == summary['alpha_modified_count'] == 0
assert summary['control_full_rgba_imported_regions_passed'] == 8
assert summary['control_gpu_exact_cases'] == 16
assert not protected_changed
(review / 'technical-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key:value for key,value in summary.items() if key not in ['cold_natural_playback', 'cold_frame_intervals_ms']}, ensure_ascii=False))
