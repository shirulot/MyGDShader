"""v005 增量结论绑定固定包及实际手柄/GPU证据；不扩张功能验收范围。"""
import hashlib
import json
from pathlib import Path

workspace = Path('E:/dev/shader/godot-shader/godot-shader-simple')
review = workspace / 'art-source/ember/ta-review-v001/ui-v005-independent/technical'
cold = review / 'cold-project'
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

integrity = read(review / 'incremental-integrity.json')
navigation = read(cold / 'art-source/ember/ui-interactions-v004/navigation-supplement.json')
gamepad = read(cold / 'ta-ui-probe/gamepad-v005-results.json')
original_probe = read(cold / 'ta-ui-probe/independent-results.json')
gpu = read(review / 'gpu-focus-layout/focus-layout-gpu.json')
frozen_summary = read(cold / 'art-source/ember/ui-interactions-v004/validation-summary.json')
protected = [{'path':path,'unchanged':sha(workspace / path).lower() == value.lower()} for path,value in frozen_summary['protected_source_hashes'].items()]
source_sha = sha(cold / 'scripts/ember/ui_edge_v004/interaction_ui.gd')
assert all(protected_item['unchanged'] for protected_item in protected)
assert all(report['status'] == 'PASS' for report in [integrity,navigation,gamepad,original_probe])
assert navigation['ui_source_sha256'] == gamepad['ui_source_sha256'] == gpu['interaction_ui_sha256'] == source_sha
assert gamepad['input_map_before'] == gamepad['input_map_after']
assert sha(cold / 'tools/ta_ui_v004_probe.gd') == '21f5e6b1459b9336eb7ec94dba3f628e80518246a0ce6ab495f381ac9c457205'
stderr = [{'path':str(path.relative_to(review)), 'bytes':path.stat().st_size} for path in review.glob('*.stderr.log')]
assert all(entry['bytes'] == 0 for entry in stderr)
summary = {
    'decision':'INPUT_RUNTIME_PASS_VISIBLE_SLIDER_FOCUS_REQUIRES_P2_REPAIR',
    'fixed_zip_sha256':integrity['zip_sha256'],
    'interaction_ui_sha256':source_sha,
    'package_checks':integrity['check_count'],
    'changed_existing_scripts':integrity['changed_existing_scripts'],
    'existing_pngs_identical':integrity['existing_png_count'],
    'runtime_checks':{'author_navigation':navigation['check_count'],'independent_joypad':gamepad['check_count'],'unchanged_original_ta_probe':original_probe['check_count']},
    'runtime_total':navigation['check_count'] + gamepad['check_count'] + original_probe['check_count'],
    'input_map_unchanged':True,
    'v004_gamepad_P2_closed':True,
    'new_gpu_capture_count':len(gpu['captures']),
    'slider_focus_comparison':gpu['slider_focus_comparison'],
    'compact_hud_geometry':gpu['compact_hud_geometry'],
    'large_margin_geometry':gpu['large_margin_geometry'],
    'protected_source_after_review':protected,
    'stderr':stderr,
    'blocking_findings':[{'priority':'P2','file':'scripts/ember/ui_edge_v004/interaction_ui.gd','line':367,'issue':'HSlider has no visible keyboard/gamepad focus distinction. Actual focus=true/false, identical 552x44 slider GPU ROI (0 pixels changed).','minimal_fix':'Add explicit independent focused visual using current palette/skin; preserve input routing and source assets; submit newly frozen evidence.'}],
    'scope':'Declared UI and dedicated preview host only; unchanged v004 technical checks inherited via exact source/resource diff. Art reviewer handles final visual conclusion.',
    'inherited_review':'../../ui-v004-independent/technical/review-technical.md',
    'evidence':['incremental-integrity.json','interaction-ui-v004-to-v005.diff','cold-project/ta-ui-probe/gamepad-v005-results.json','cold-project/ta-ui-probe/independent-results.json','gpu-focus-layout/focus-layout-gpu.json'],
}
(review / 'technical-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key:value for key,value in summary.items() if key not in ['protected_source_after_review','stderr','evidence']}, ensure_ascii=False))
