"""Update the mutable current preview only after final TA approval and verified installation."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'enemy-sequences-v001/previews'
FROZEN=BASE/'enemy-eight-directions-v027-v001'
CURRENT=BASE/'review-current'
ARCHIVE=BASE/'review-v012-before-v027-2026-10-07'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
approval=json.loads((ROOT/'FINAL_ACCEPTANCE.json').read_text(encoding='utf-8'))
submission=json.loads((ROOT/'qa/submission_receipt_v001.json').read_text(encoding='utf-8'))
installed=json.loads((ROOT/'qa/installed_resource_load.json').read_text(encoding='utf-8'))
assert approval['status']=='TA_APPROVED_FINAL_ASSEMBLY' and approval['zip_sha256']==submission['zip_sha256']
assert installed['status']=='PASS' and installed['frames']==960
for relative,digest in submission['web_hashes'].items():assert sha(FROZEN/relative)==digest
if not ARCHIVE.exists():shutil.copytree(CURRENT,ARCHIVE)
for p in FROZEN.rglob('*'):
    if p.is_file():
        q=CURRENT/p.relative_to(FROZEN);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
catalog=json.loads((CURRENT/'catalog.json').read_text(encoding='utf-8'))
status=dict(updated='2026-10-07',status='TA_APPROVED_FINAL_ASSEMBLY',version='v027-v001',zip_sha256=approval['zip_sha256'],review_report=approval['review_report'],clips=160,frames=960,approved={u:[c['action'] for c in catalog['clips'] if c['unit']==u] for u in catalog['units']},prior_front_only_preview='../review-v012-before-v027-2026-10-07/index.html')
(CURRENT/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
for relative,digest in submission['web_hashes'].items():assert sha(CURRENT/relative)==digest
receipt=dict(status='PASS',url='http://127.0.0.1:6106/review-current/index.html',fixed_url=submission['url'],zip_sha256=approval['zip_sha256'],files_match_frozen_web=len(submission['web_hashes']),prior_preview=str(ARCHIVE))
(ROOT/'qa/current_preview_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt))
