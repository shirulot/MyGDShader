"""Install a formally accepted fixed assembly into a new asset folder, preserving older sets."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
PACKAGE=ROOT.parent/'enemy-sequences-eight-directions-v027-review-v001'
TARGET=REPO/'assets/ember/characters/enemies_v003'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
approval=json.loads((ROOT/'FINAL_ACCEPTANCE.json').read_text(encoding='utf-8'))
submission=json.loads((ROOT/'qa/submission_receipt_v001.json').read_text(encoding='utf-8'))
assert approval['status']=='TA_APPROVED_FINAL_ASSEMBLY' and approval['zip_sha256']==submission['zip_sha256']
assert (REPO/approval['review_report']).exists()
assert sha(Path(submission['zip']))==approval['zip_sha256']
records=[]
for p in (PACKAGE/'output').rglob('*'):
    if not p.is_file() or p.suffix not in ['.png','.tres','.json']:continue
    q=TARGET/p.relative_to(PACKAGE/'output')
    # 重跑时只接受已存在的完全相同文件，避免覆盖别的工作。
    if q.exists():assert sha(q)==sha(p),f'Unrelated existing file: {q}'
    else:q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    assert sha(q)==sha(p)
    records.append(dict(path=q.relative_to(REPO).as_posix(),sha256=sha(q),bytes=q.stat().st_size))
    if q.suffix=='.png':
        # 只设置新资源的导入参数。UID与缓存路径交给主项目Godot首次导入生成。
        meta=q.with_suffix(q.suffix+'.import')
        if not meta.exists():
            meta.write_text('[remap]\nimporter="texture"\ntype="CompressedTexture2D"\n\n[params]\ncompress/mode=0\ndetect_3d/compress_to=0\nmipmaps/generate=false\nprocess/fix_alpha_border=false\nprocess/premult_alpha=false\n',encoding='utf-8')
        else:
            import re
            text=meta.read_text(encoding='utf-8')
            for key,value in [('compress/mode','0'),('detect_3d/compress_to','0'),('mipmaps/generate','false'),('process/fix_alpha_border','false'),('process/premult_alpha','false')]:
                text=re.sub(r'^'+re.escape(key)+r'=.*$',key+'='+value,text,flags=re.M)
            meta.write_text(text,encoding='utf-8')
for name in ['README.md','TA_ACCEPTANCE.json']:
    q=TARGET/name
    if q.exists():assert sha(q)==sha(PACKAGE/name)
    else:shutil.copy2(PACKAGE/name,q)
shutil.copy2(ROOT/'FINAL_ACCEPTANCE.json',TARGET/'FINAL_ACCEPTANCE.json')
receipt=dict(status='PASS_BYTE_EXACT_INSTALL',target=str(TARGET),zip_sha256=approval['zip_sha256'],files=records,scope='PNG and SpriteFrames assets; gameplay logic is unchanged.')
(ROOT/'qa/project_asset_copy_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(dict(status=receipt['status'],files=len(records),target=str(TARGET))))
