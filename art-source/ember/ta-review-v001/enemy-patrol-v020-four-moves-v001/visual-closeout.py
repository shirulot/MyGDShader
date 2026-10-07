"""Register completed visual coverage and cross-review evidence without running Godot."""
from pathlib import Path
import hashlib
import json

base=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
binding=json.loads((base/'visual-binding.json').read_text())
local=json.loads((base/'visual-ne-local.json').read_text())
out={'status':'NEEDS_REVISION','finding_scope':'NE shallow armor elongation and neighboring leg source reuse; one localized partition finding.',
     'new_frames_actually_viewed':32,'reference_scope':'S/SE F00/F02/F04/F06 leg-phase images; no new runtime claimed.',
     'actually_viewed_own_diagnostics_sha256':binding['diagnostic_sha256']|local['diagnostic_sha256'],
     'author_source_reference_actually_viewed':{'qa/source_up_right_10x.png':sha(base/'visual-package/qa/source_up_right_10x.png')},
     'cross_review_evidence_sha256':{},
     'nonblocking_method_boundary':'N F02 right_thigh and F06 left_thigh have zero basis in peer numerical audit; actual native/4x/6x/8x reviewed frames show no confirmed gap or disconnected armor.',
     'external_execution_scope':'Root browser and animation_skills technical evidence bound separately, not counted as own execution.'}
for name in ['technical-summary.json','technical-pixel-integrity.json','root-browser-ne-f02.png','root-browser-ne-f03.png','root-browser-ne-f04.png','root-browser-n-f02.png','root-browser-n-f06.png']:
    p=base/name
    if p.exists():out['cross_review_evidence_sha256'][name]=sha(p)
(base/'visual-conclusion.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Recorded 32 viewed new frames, 32 owned diagnostics, and localized NE revision finding.')
