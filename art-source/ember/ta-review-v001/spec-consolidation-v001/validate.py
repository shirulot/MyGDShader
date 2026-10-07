"""验证本次文档链接、原文快照和参考图绑定，不运行或重导入游戏。"""
from pathlib import Path
import hashlib,json,re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
MAIN=ROOT/'docs/shader-learning/ember-art-unified-v001.md'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
index=json.loads((HERE/'source-index.json').read_text(encoding='utf-8'))
errors=[]
for entry in index['files']:
    original=ROOT/entry['path'];snapshot=HERE/entry['snapshot']
    if sha(original)!=entry['sha256'] or sha(snapshot)!=entry['sha256']:
        errors.append('source changed: '+entry['path'])
links=[];references=[]
for doc in [MAIN,HERE/'source-index.md',HERE/'parameters.md',HERE/'collection-notes.md']:
    for raw in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        if re.match(r'^(https?://|#|res://)',raw):continue
        path=(doc.parent/raw.split('#')[0]).resolve()
        exists=path.exists()
        links.append({'document':doc.relative_to(ROOT).as_posix(),'target':raw,'exists':exists})
        if not exists:errors.append('missing link: '+raw)
        if exists and path.suffix.lower() in ['.png','.jpg','.webp']:
            references.append({'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path),'purpose':'see associated reference-role row in unified document'})
(HERE/'reference-images.json').write_text(json.dumps(references,ensure_ascii=False,indent=2),encoding='utf-8')
result={'status':'PASS' if not errors else 'FAIL','source_files':len(index['files']),'checked_local_links':len(links),'bound_reference_images':len(references),'source_sha_match':not any(x.startswith('source changed') for x in errors),'errors':errors,'links':links,'scope':'documentation/source binding only; no new art/engine acceptance','main_document_sha256':sha(MAIN)}
(HERE/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='links'},ensure_ascii=False))
