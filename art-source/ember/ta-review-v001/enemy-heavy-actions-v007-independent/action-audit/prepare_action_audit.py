"""独立重装机动作审查：只在指定证据目录解固定包。"""
import hashlib,json
from pathlib import Path
from zipfile import ZipFile
workspace=Path('E:/dev/shader/godot-shader/godot-shader-simple')
review=workspace/'art-source/ember/ta-review-v001/enemy-heavy-actions-v007-independent/action-audit'
package_root=review/'package'
archive=workspace/'art-source/ember/deliveries/enemy_heavy_actions_v007_2026-10-06.zip'
sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha(archive.read_bytes())=='05350a58ef0a0e44ee19c3c6af69a2f38048f4e1c5d4ce24afae5076ece14494'
with ZipFile(archive) as package:
    files=[item for item in package.infolist() if not item.is_dir()]
    assert len(files)==len({item.filename for item in files}) and package.testzip() is None
    for item in files:
        target=(package_root/item.filename).resolve()
        assert target.is_relative_to(package_root.resolve())
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(package.read(item))
catalog=json.loads((package_root/'output/catalog_v007.json').read_text(encoding='utf-8'))
compact={'zip_sha256':sha(archive.read_bytes()),'zip_bytes':archive.stat().st_size,'entries':len(files),'catalog_sha256':sha((package_root/'output/catalog_v007.json').read_bytes()),'actions':{}}
for action,spec in catalog['actions'].items():
    compact['actions'][action]={key:spec[key] for key in ['frame_count','fps','loop']}
    compact['actions'][action]['poses']=[{key:value for key,value in pose.items() if key!='part_transforms'} for pose in spec['poses']]
(review/'binding-and-pose-evidence.json').write_text(json.dumps(compact,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'zip_bytes':compact['zip_bytes'],'entries':compact['entries'],'root':str(package_root),'qa':sorted(p.name for p in (package_root/'qa').glob('*4x.png')),'poses':compact['actions']},ensure_ascii=False))
