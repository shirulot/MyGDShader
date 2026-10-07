"""在冻结v003基础上创建完整v004；旧ZIP不覆盖，所有载荷逐项哈希。"""
from pathlib import Path
import hashlib
import json
import zipfile
from assemble_catalog import ROOT, PROOF, sha

DELIVERIES = ROOT/"art-source/ember/deliveries"
BASE = DELIVERIES/"ember_assets_v003_2026-10-04.zip"
TARGET = DELIVERIES/"ember_assets_v004_2026-10-04.zip"

def main():
    assert not TARGET.exists(), "Refusing to overwrite an existing release"
    acceptance = json.loads((PROOF/"final-acceptance.json").read_text(encoding="utf-8"))
    assert acceptance["status"] == "TECHNICAL_40_FINAL_ACCEPTANCE_PASS"
    catalog_path = ROOT/"assets/ember/data/technical_inputs_catalog_v001.json"
    assert sha(catalog_path) == acceptance["accepted_catalog_sha256"]
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    for asset in catalog["assets"]: assert sha(ROOT/asset["file"].removeprefix("res://")) == asset["sha256"], asset["id"]
    for path, expected in catalog["producer_dependency_sha256"].items(): assert sha(ROOT/path) == expected, path
    for field in ("evidence_sha256", "delivery_document_sha256"):
        for path, expected in acceptance[field].items(): assert sha(ROOT/path) == expected, path
    frozen = json.loads((PROOF/"protected-before.json").read_text(encoding="utf-8"))["sha256"]
    for path, expected in frozen.items(): assert sha(ROOT/path) == expected, path
    payload = {}
    with zipfile.ZipFile(BASE) as archive:
        assert archive.testzip() is None
        previous = json.loads(archive.read("DELIVERY-MANIFEST.json"))
        for path, expected in previous["files"].items():
            data = archive.read(path)
            assert hashlib.sha256(data).hexdigest() == expected, path
            payload[path] = data
    # 旧艺术与来源沿用已验证快照；当前导入元数据、文档与本批新增输入写入新包。
    for directory in (ROOT/"assets/ember", ROOT/"scenes/ember", PROOF):
        for path in directory.rglob("*"):
            if not path.is_file(): continue
            if any(p.startswith("fresh-project-") or p in (".godot", "__pycache__") for p in path.parts): continue
            if path.suffix == ".pyc": continue
            payload[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for name in ("tools/build_ember_technical_inputs.gd", "tools/build_ember_technical_inputs.gd.uid",
                 "docs/shader-learning/asset-generation-manifest.csv", "docs/shader-learning/resources.md",
                 "docs/shader-learning/art-generation-standard.md", "docs/shader-learning/asset-production-full-art.md",
                 "docs/shader-learning/asset-production-technical-inputs.md"):
        path = ROOT/name
        if path.is_file(): payload[name] = path.read_bytes()
    for path in (ROOT/"tools").glob("build_ember_*"):
        if path.is_file() and path.name.endswith((".gd", ".gd.uid")):
            payload[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    # 包里的最小工程可直接打开全部预览，无学习项目Autoload；不改工作区project.godot。
    payload["project.godot"] = b'''config_version=5
[application]
config/name="Ember reusable assets v004"
run/main_scene="res://scenes/ember/technical_inputs_sandbox.tscn"
[display]
window/size/viewport_width=1440
window/size/viewport_height=1040
[rendering]
renderer/rendering_method="gl_compatibility"
'''
    files = {name:hashlib.sha256(data).hexdigest() for name,data in sorted(payload.items())}
    pngs = [name for name in files if name.startswith("assets/ember/") and name.endswith(".png")]
    resources = [name for name in files if name.startswith("assets/ember/") and name.endswith(".tres")]
    scenes = [name for name in files if name.startswith("scenes/ember/") and name.endswith(".tscn")]
    assert (len(pngs),len(resources),len(scenes)) == (105,16,4)
    manifest = {"date":"2026-10-04","completed_art_units":123,"remaining_art_units":0,
        "completed_technical_inputs":40,"actual_layout_masks":0,"layout_mask_budget_upper_bound":30,
        "production_png_files":105,"art_png_files":65,"technical_png_files":40,
        "resource_files":16,"editable_scenes":4,"actual_archived_master_outputs":77,
        "new_imagegen_calls":0,"base_archive_sha256":sha(BASE),
        "frozen_previous_archives":{Path(p).name:h for p,h in frozen.items() if p.endswith(".zip")},
        "historical_proofs":"Previous version reports describe their frozen release; current technical acceptance is technical-inputs-v001/final-acceptance.json",
        "files":files}
    with zipfile.ZipFile(TARGET,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,data in sorted(payload.items()): archive.writestr(name,data)
        archive.writestr("DELIVERY-MANIFEST.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    summary = {"status":"FULL_ART_AND_TECHNICAL_V004_PACKAGED","file":TARGET.relative_to(ROOT).as_posix(),
        "sha256":sha(TARGET),"bytes":TARGET.stat().st_size,"payload_files":len(files),
        "production_pngs":105,"resources":16,"scenes":4,"art_units":123,"technical_inputs":40}
    TARGET.with_suffix(".package.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False))

if __name__ == "__main__": main()
