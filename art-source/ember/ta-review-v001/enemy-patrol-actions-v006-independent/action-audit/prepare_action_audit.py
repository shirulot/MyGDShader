"""只在动作意图审查目录中解包固定送审资源。"""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

workspace = Path('E:/dev/shader/godot-shader/godot-shader-simple')
review = workspace / 'art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/action-audit'
package_dir = review / 'package'
archive = workspace / 'art-source/ember/deliveries/enemy_patrol_actions_v006_2026-10-06.zip'
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(archive.read_bytes()) == '1bae7e4fa6932b2479274abecabe247c7efa7efbd7a8b50bbd49b864eea15295'
with ZipFile(archive) as package:
    entries = [item for item in package.infolist() if not item.is_dir()]
    for entry in entries:
        target = (package_dir / entry.filename).resolve()
        assert target.is_relative_to(package_dir.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(package.read(entry))
catalog_path = next(package_dir.rglob('catalog_v006.json'))
root = catalog_path.parent.parent
catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
records = {}
for name, action in catalog['actions'].items():
    records[name] = {'fps': action['fps'], 'loop': action['loop'], 'frame_count': action['frame_count'], 'poses': []}
    for pose, pixels in zip(action['poses'], action['pixel_reports']):
        records[name]['poses'].append({key: pose[key] for key in ['frame', 'phase', 'pose_definition', 'legs', 'arms', 'events', 'sensor_power']})
        records[name]['poses'][-1]['pixel_report'] = pixels
        for key in ['shoulder_contact_landmark_px', 'ground_y']:
            if key in pose: records[name]['poses'][-1][key] = pose[key]
record = {'zip_sha256': sha(archive.read_bytes()), 'zip_bytes': archive.stat().st_size, 'entries': len(entries), 'package_root': str(root), 'actions': records}
(review / 'action-evidence.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'package_root': str(root), 'entries': len(entries), 'output_files': sorted(p.name for p in (root / 'output').iterdir()), 'contact_sheets': sorted(p.name for p in (root / 'qa').glob('*down*4x.png'))}, ensure_ascii=False))
