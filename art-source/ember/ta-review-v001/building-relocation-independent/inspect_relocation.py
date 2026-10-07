"""仅读路径迁移输入；独立冷副本及证据写在本审查目录。"""
from pathlib import Path
from zipfile import ZipFile
import hashlib, json, re, difflib
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
PACK=ROOT/"assets/ember/buildings_final"
OLD_COLD=ROOT/"art-source/ember/ta-review-v001/buildings-final-incremental/cold-project"
OLD_REVIEW=PACK/"review/consolidation-ta"
COLD=OUT/"cold-project"
def sha(data):return hashlib.sha256(data).hexdigest()
def load(path):return json.loads(path.read_text(encoding="utf-8-sig"))
plan=load(PACK/"review/relocation-plan.json")
mapping=plan["mapping"]
def relocate(text):
    for before,after in sorted(mapping.items(),key=lambda p:len(p[0]),reverse=True):text=text.replace(before,after)
    return text
prior_source={i["path"]:i["sha256"] for i in load(OLD_REVIEW/"bound/SOURCE_SYNC_MANIFEST.json")}
prior_integrity=load(OLD_REVIEW/"runtime-integrity.json")
assert sha((ROOT/"project.godot").read_bytes())==plan["main_project_sha256"]==prior_integrity["main_project_sha256"]
report={"main_project_unchanged":True,"main_project_sha256":plan["main_project_sha256"],"mapping":mapping,"code_and_scenes":[],"json_routes":[],"references":[]}
old_paths=["scripts/ember/building_asset.gd","scripts/ember/building_demo.gd","scripts/ember/building_demo_actor.gd","shaders/ember/building_intact.gdshader"]
old_paths += ["tools/"+n for n in ["build_building_coverage_v004r1.gd","export_building_parts_v004r1.gd","validate_capture_buildings_v004r1.gd"]]
old_paths += ["scenes/ember/building_assets_v004r1/"+n+".tscn" for n in ["control_tower","repair_workshop","logistics_warehouse","control_tower_static","repair_workshop_static","logistics_warehouse_static","demo"]]
for old_relative in old_paths:
    old=OLD_COLD/old_relative
    assert sha(old.read_bytes())==prior_source[old_relative]
    new_relative=relocate(old_relative)
    new=ROOT/new_relative
    old_text=old.read_text(encoding="utf-8-sig");new_text=new.read_text(encoding="utf-8-sig")
    assert relocate(old_text)==new_text, "Beyond path replacement: "+new_relative
    report["code_and_scenes"].append({"before":old_relative,"after":new_relative,"before_sha256":sha(old.read_bytes()),"after_sha256":sha(new.read_bytes()),"body_only_declared_path_replacement":True,"byte_equal":old.read_bytes()==new.read_bytes()})
    (OUT/(new.name+".diff.txt")).write_text("\n".join(difflib.unified_diff(old_text.splitlines(),new_text.splitlines(),fromfile=old_relative,tofile=new_relative,lineterm="")),encoding="utf-8")
assert len(report["code_and_scenes"])==14
for suffix in ["catalog_v004r1.json","functional_layers_v004r1.json"]:
    old_relative="assets/ember/building_assets_v004r1/"+suffix
    old=OLD_COLD/old_relative;new=ROOT/relocate(old_relative)
    assert sha(old.read_bytes())==prior_source[old_relative]
    assert json.loads(relocate(old.read_text(encoding="utf-8-sig")))==load(new)
    report["json_routes"].append({"path":str(new.relative_to(ROOT)).replace("\\","/"),"only_declared_path_replacement":True,"sha256":sha(new.read_bytes())})
frozen=PACK/"delivery/building_assets_v004r1_2026-10-06.zip"
assert sha(frozen.read_bytes())=="22dc4017aef594f33350e71b0af723909fbd1c4fde1a88208c9a66e34c9e2a32"
report["approved_zip_sha256"]=sha(frozen.read_bytes())
report["pngs"] = []
with ZipFile(frozen) as archive:
    for item in prior_integrity["images"]:
        new_relative=relocate(item["path"])
        current=(ROOT/new_relative).read_bytes()
        assert sha(current)==item["sha256"] and current==archive.read(item["path"])
        report["pngs"].append({"path":new_relative,"sha256":sha(current),"frozen_r1_byte_equal":True})
assert len(report["pngs"])==32
before_tool=OLD_REVIEW/"bound/sync_building_demo.ps1"
new_tool=PACK/"tools/sync_building_demo.ps1"
diff="\n".join(difflib.unified_diff(before_tool.read_text(encoding="utf-8-sig").splitlines(),new_tool.read_text(encoding="utf-8-sig").splitlines(),fromfile="before_sync",tofile="relocated_sync",lineterm=""))
(OUT/"sync-tool.diff.txt").write_text(diff,encoding="utf-8")
report["sync_tool"]={"before_sha256":sha(before_tool.read_bytes()),"after_sha256":sha(new_tool.read_bytes()),"read_diff_separately_not_claimed_literal_path_only":True,"not_executed_by_auditor":True}
source_manifest=load(PACK/"examples/standalone/SOURCE_SYNC_MANIFEST.json")
final_manifest=load(PACK/"examples/standalone/SYNC_MANIFEST.json")
assert len(source_manifest)==len(final_manifest)==66
source_map={i["path"]:i["sha256"] for i in source_manifest};final_map={i["path"]:i["sha256"] for i in final_manifest}
assert len(source_map)==len(final_map)==66 and source_map.keys()==final_map.keys()
report["source_sync"]=[];report["final_sync"]=[];report["source_final_differences"]=[]
for relative,expected in source_map.items():
    assert sha((ROOT/relative).read_bytes())==expected
    report["source_sync"].append({"path":relative,"source_hash_matches":True})
for relative,expected in final_map.items():
    final_path=PACK/"examples/standalone"/relative
    data=final_path.read_bytes()
    assert sha(data)==expected
    report["final_sync"].append({"path":relative,"final_demo_hash_matches":True})
    if expected!=source_map[relative]:
        assert relative.endswith((".uid","previews/validation_v004r1.json"))
        report["source_final_differences"].append({"path":relative,"source_sha256":source_map[relative],"final_sha256":expected,"kind":"regenerated_uid" if relative.endswith(".uid") else "generated_validation_evidence"})
    target=COLD/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
# 避免历史baseline引用造成假警报：它是原v004冻结JSON，工具只取数值对照，
# 不把该文档的旧source路径当现行运行入口。检查当前脚本/场景和两份正式JSON。
for relative in [i["after"] for i in report["code_and_scenes"]]+[i["path"] for i in report["json_routes"]]:
    text=(ROOT/relative).read_text(encoding="utf-8-sig")
    refs=re.findall(r'res://[^"\s\)]+',text)
    for ref in refs:
        if any(marker in ref for marker in ["%","{","+"]):continue
        path=ref[6:]
        assert (ROOT/path).exists(), (relative,ref,"main missing")
        assert (COLD/path).exists(), (relative,ref,"standalone missing")
        report["references"].append({"file":relative,"reference":ref,"main_and_standalone_exist":True})
assert all("uid://" not in (ROOT/i["after"]).read_text(encoding="utf-8-sig") for i in report["code_and_scenes"])
report["uid_reference_contract"]="Current gd/tscn/shader refs use explicit res paths; no uid:// coupling to sidecar changes."
project=(PACK/"examples/standalone/project.godot").read_text(encoding="utf-8-sig")
assert 'run/main_scene="res://assets/ember/buildings_final/scenes/demo.tscn"' in project
(COLD/"project.godot").write_text(project.replace("[application]",'[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="Ember TA Building Relocation Independent"',1),encoding="utf-8")
author=load(PACK/"verification/validation.json")
report["author_evidence"]={"sha256":sha((PACK/"verification/validation.json").read_bytes()),"total":author["total"],"passed":author["passed"],"hash_bound_only_not_independent_rerun":True}
report["bound_files"]={}
(OUT/"bound").mkdir(exist_ok=True)
for relative in ["README.md","review/relocation-plan.json","verification/relocation-result.json","verification/validation.json","examples/standalone/SOURCE_SYNC_MANIFEST.json","examples/standalone/SYNC_MANIFEST.json","tools/sync_building_demo.ps1"]:
    source=PACK/relative
    (OUT/"bound"/source.name).write_bytes(source.read_bytes())
    report["bound_files"][relative]=sha(source.read_bytes())
(OUT/"relocation-integrity.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"code_scene":14,"jsons":2,"r1_pngs":32,"source_final_manifests":[66,66],"source_final_differences":report["source_final_differences"],"literal_references":len(report["references"]),"author_passed":author["passed"]},ensure_ascii=False,indent=2))
