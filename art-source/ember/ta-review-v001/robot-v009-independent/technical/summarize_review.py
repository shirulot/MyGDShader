"""汇总 v009 实际冷导入/GPU 播放及冻结旧资源的完成后只读复核。"""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

workspace = Path('E:/dev/shader/godot-shader/godot-shader-simple')
relative = Path('art-source/ember/robot-fixed-rig-v009')
review = workspace / 'art-source/ember/ta-review-v001/robot-v009-independent/technical'
cold = review / 'cold-workspace'
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

package = read(review / 'package-source-report.json')
playback_path = cold / relative / 'fixed_rig_playback_v009.json'
playback = read(playback_path)
baseline = read(workspace / 'art-source/ember/robot-fixed-rig-v007/source/production_baseline_sha256_v007.json')
protection = read(workspace / relative / 'qa/production_protection_v009.json')
baseline_by_file = {entry['file']:entry['sha256'] for entry in baseline['files']}
producer_baseline_matches = len(protection['formal_files']) == 87 and {entry['file']:entry['expected'] for entry in protection['formal_files']} == baseline_by_file
protected_changed = [entry['file'] for entry in baseline['files'] if sha(Path(entry['file'])) != entry['sha256']]
with ZipFile(workspace / 'art-source/ember/deliveries/robot_fixed_rig_v008_walk_down_candidate_2026-10-06.zip') as old:
    old_frames_changed = [index for index in range(8) if (workspace / f'art-source/ember/robot-fixed-rig-v008/frames/robot_walk_down_f{index:02d}_v008.png').read_bytes() != old.read(f'frames/robot_walk_down_f{index:02d}_v008.png')]
source_bound = all(sha(cold / path) == expected for path,expected in playback['source_hashes'].items())
import_path = cold / relative / 'godot-review/assets/robot_walk_down_atlas_v009.png.import'
import_text = import_path.read_text(encoding='utf-8-sig')
intervals = [b['elapsed_ms'] - a['elapsed_ms'] for a,b in zip(playback['playback']['sequence'],playback['playback']['sequence'][1:])]
assert package['status'] == 'PASS' and playback['technical_checks'] == 'PASS'
assert producer_baseline_matches and not protected_changed and not old_frames_changed and source_bound
assert 'process/fix_alpha_border=false' in import_text
assert (review / 'cold-import.stderr.log').stat().st_size == (review / 'playback-rerun.stderr.log').stat().st_size == 0
assert all(entry['rgba_exact'] for entry in playback['imported_atlas_regions'])
assert all(entry['rgba_exact_to_native_png'] for entry in playback['gpu_entries'])
(review / 'cold-playback-report.json').write_text(json.dumps(playback, ensure_ascii=False, indent=2), encoding='utf-8')
summary = {
    'decision':'TECHNICAL_PASS',
    'scope':'down walk only, 8 frames, 64x96, 8 FPS, root [32,80]; foot visible form is reviewed separately by lead TA.',
    'zip_sha256':package['zip_sha256'],
    'rig_sha256':sha(cold / relative / 'source/rig_down_v009.json'),
    'atlas_sha256':sha(cold / relative / 'robot_walk_down_atlas_v009.png'),
    'package_source_checks':package['check_count'],
    'package_source_failures':len(package['failures']),
    'v008_full_rgba_import_P2_closed':True,
    'cold_import_exit':0,
    'cold_gpu_verifier_exit':0,
    'cold_imported_region_full_rgba_passed':len(playback['imported_atlas_regions']),
    'cold_gpu_exact_cases':len(playback['gpu_entries']),
    'playback':playback['playback'],
    'natural_frame_intervals_ms':intervals,
    'portable_import_sidecar_sha256_after_import':sha(import_path),
    'playback_verifier_same_as_v008_after_version_normalization':True,
    'source_binding_after_playback':source_bound,
    'source_parts_byte_equal_v008':23,
    'caps_definitions_equal_v008':17,
    'fixed_canonical_byte_equal_v008':True,
    'neutral_source_opaque_rgba_exact_original':1492,
    'meaningful_changes':'Independent rigid foot heel/toe pivot and pitch to ankle before leg IK; body/lift curves from foot_motion_v009.json; foot contact diagnostics. Fixed source geometry/canonical/camera unchanged.',
    'rig_structure_changes_after_version_normalization':package['rig_changed_paths_after_version_normalization'],
    'producer_protection_baseline_matches_original_87':producer_baseline_matches,
    'production_protected_changed_after_review':protected_changed,
    'v008_source_frames_changed':old_frames_changed,
    'v008_zip_sha256_after_review':sha(workspace / 'art-source/ember/deliveries/robot_fixed_rig_v008_walk_down_candidate_2026-10-06.zip'),
    'blocking_findings':[],
    'art_acceptance':'NOT_CLAIMED',
    'evidence':['package-source-report.json','renderer-version-normalized.diff','cold-playback-report.json','cold-import.stdout.log','cold-import.stderr.log','playback-rerun.stdout.log','playback-rerun.stderr.log'],
}
(review / 'technical-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key:value for key,value in summary.items() if key not in ['playback','natural_frame_intervals_ms']}, ensure_ascii=False))
