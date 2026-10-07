"""只核冻结包/关键行为来源并冷解包；全PNG/source清单审核由另一独立代理负责。"""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

workspace = Path('E:/dev/shader/godot-shader/godot-shader-simple')
review = workspace / 'art-source/ember/ta-review-v001/building-v002-independent/technical'
cold = review / 'cold-project'
archive = workspace / 'art-source/ember/deliveries/building_assets_v002_2026-10-06.zip'
old_archive = workspace / 'art-source/ember/deliveries/building_assets_v001_2026-10-06.zip'
def sha(data): return hashlib.sha256(data).hexdigest()

assert sha(archive.read_bytes()) == '18fe88a25dc19aaaf7cdae43505ff3eb04c060b5358daf8171fcc300c4832f35'
assert archive.stat().st_size == 72303483
base_preserved = []
with ZipFile(archive) as package, ZipFile(old_archive) as old:
    entries = [entry for entry in package.infolist() if not entry.is_dir()]
    assert len(entries) == 279 and len({entry.filename for entry in entries}) == 279
    for entry in entries:
        target = (cold / entry.filename).resolve()
        assert target.is_relative_to(cold.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(package.read(entry))
    catalog = package.read('assets/ember/building_assets_v002/catalog_v002.json')
    assert sha(catalog) == '9a89de864acdcccaf98e3ed6cefab71a89d1edbb9145ae3ebc1cb32b587ed8c1'
    for path in ['scripts/ember/building_asset_v001.gd','scripts/ember/building_demo_actor_v001.gd','scripts/ember/building_demo_v001.gd']:
        unchanged = package.read(path) == old.read(path)
        assert unchanged
        base_preserved.append({'path':path,'unchanged_vs_frozen_v001':unchanged,'sha256':sha(package.read(path))})
project = cold / 'project.godot'
original_project_sha = sha(project.read_bytes())
text = project.read_text(encoding='utf-8-sig').replace('[application]', '[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="Ember TA Building v002 Independent"')
project.write_text(text, encoding='utf-8')
old_probe = workspace / 'art-source/ember/ta-review-v001/building-v001-independent/technical/cold-project/tools/ta_building_probe.gd'
probe = old_probe.read_text(encoding='utf-8-sig')
routed = probe.replace('res://scripts/ember/building_asset_v001.gd','res://scripts/ember/building_asset_v002.gd').replace('res://scenes/ember/building_assets_v001/demo.tscn','res://scenes/ember/building_assets_v002/demo.tscn')
probe_path = cold / 'tools/ta_building_probe.gd'
probe_path.write_text(routed, encoding='utf-8')
report = {'status':'PASS','zip_sha256':sha(archive.read_bytes()),'zip_bytes':archive.stat().st_size,'entries':279,'payloads':278,'catalog_sha256':sha(catalog),'base_runtime_preserved':base_preserved,'review_project_original_sha256':original_project_sha,'only_config_change':'independent user storage directory','old_probe_sha256':sha(old_probe.read_bytes()),'routed_probe_sha256':sha(probe_path.read_bytes()),'probe_changes':'Only building runtime/demo preload resource routes v001 -> v002; body and output unchanged.'}
(review / 'cold-preparation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
