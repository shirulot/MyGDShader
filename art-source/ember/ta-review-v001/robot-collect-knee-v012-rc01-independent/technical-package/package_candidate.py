"""固定候选包与逐文件SHA；独立美术回执将存包外，不回写候选ZIP。"""
from pathlib import Path
import hashlib
import json
import zipfile

root=Path(__file__).resolve().parent
base=root.parents[1]
read=lambda file: json.loads(file.read_text(encoding='utf-8'))
sha=lambda data: hashlib.sha256(data).hexdigest()
validation=read(root/'qa/validation.json')
assert validation['technical_checks']=='PASS' and validation['unchanged_frames']==96 and validation['changed_frames']==16
archive=base.parent/'deliveries/robot_collect_knee_v012_rc01_2026-10-07.zip'
manifest_file=root/'sha256-manifest.json'
if archive.exists() or manifest_file.exists():
    raise FileExistsError('Candidate already frozen; use another revision for further changes')
files=sorted(file for file in root.rglob('*') if file.is_file() and '.godot' not in file.parts and file.suffix!='.log')
manifest={'revision':'collect-knee-v012-rc01','status':'PENDING_NEW_VISUAL_REVIEW','preserved_frames':96,'changed_frames':16,
          'files':[{'file':file.relative_to(root).as_posix(),'bytes':file.stat().st_size,'sha256':sha(file.read_bytes())} for file in files]}
manifest_file.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as pack:
    for file in files+[manifest_file]: pack.write(file,file.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as pack:
    for item in manifest['files']: assert sha(pack.read(item['file']))==item['sha256'],item['file']
receipt={'status':'TECHNICAL_PASS_VISUAL_REVIEW_PENDING','zip':str(archive),'zip_sha256':sha(archive.read_bytes()),
         'zip_bytes':archive.stat().st_size,'payload_files':len(files),'manifest_sha256':sha(manifest_file.read_bytes()),
         'runtime_atlas_sha256':read(root/'runtime/full-action-metadata.json')['atlas_sha256'],
         'preserved_frames':96,'changed_frames':16,'gpu_samples':64,'collect_recoveries':8,'payload_hash_mismatches':0}
(base/'qa/delivery_collect_knee_v012_rc01.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt))
