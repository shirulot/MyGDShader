"""只在 TA 审查目录建隔离对照；冻结包不改，补回遗漏的生产导入配置。"""
from pathlib import Path
from zipfile import ZipFile
import shutil

workspace = Path('E:/dev/shader/godot-shader/godot-shader-simple')
review = workspace / 'art-source/ember/ta-review-v001/robot-v008-independent/technical'
relative = Path('art-source/ember/robot-fixed-rig-v008')
control = review / 'import-control-workspace' / relative
archive = workspace / 'art-source/ember/deliveries/robot_fixed_rig_v008_walk_down_candidate_2026-10-06.zip'
with ZipFile(archive) as package:
    for entry in package.infolist():
        if entry.is_dir():
            continue
        target = (control / entry.filename).resolve()
        assert target.is_relative_to(control.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(package.read(entry))
    assert not any(entry.filename.endswith('.import') for entry in package.infolist())
import_relative = Path('godot-review/assets/robot_walk_down_atlas_v008.png.import')
shutil.copyfile(workspace / relative / import_relative, control / import_relative)
print('Control copy ready; original archive contains zero .import sidecars.')
