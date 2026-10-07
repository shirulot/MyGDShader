"""从冻结继承链核有效方法，与当前合并脚本比较；生产只读，清理完全不操作。"""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import difflib
import re
ROOT=Path("E:/dev/shader/godot-shader/godot-shader-simple")
OUT=Path(__file__).resolve().parent
FINAL=ROOT/"art-source/ember/buildings-final"
COLD=OUT/"cold-project"
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def methods(text):
    found=list(re.finditer(r"^func\s+(\w+)\([^\n]*",text,re.M))
    return {m.group(1):text[m.start():found[i+1].start() if i+1<len(found) else len(text)].rstrip() for i,m in enumerate(found)}
def normalized_body(text):
    lines=text.splitlines()[1:]
    result=[]
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):continue
        indent=len(line)-len(line.lstrip("\t"))
        result.append((indent,re.sub(r"[ \t]+"," ",line.strip())))
    return result
provenance=load(FINAL/"consolidation-provenance.json")
result=load(FINAL/"verification/consolidation-result.json")
baseline=ROOT/provenance["original_approved_zip"]["path"]
assert sha(baseline.read_bytes())==provenance["original_approved_zip"]["sha256"]=="22dc4017aef594f33350e71b0af723909fbd1c4fde1a88208c9a66e34c9e2a32"
report={"frozen_zip_sha256":sha(baseline.read_bytes()),"images":[],"effective_methods":{},"new_sources":[]}
with ZipFile(baseline) as z:
    for entry in provenance["original_runtime"]:
        assert sha(z.read(entry["path"]))==entry["sha256"]
    for item in provenance["retained_art"]:
        current=(ROOT/item["path"]).read_bytes()
        assert sha(current)==item["sha256"] and current==z.read(item["path"])
        report["images"].append({**item,"original_zip_and_current_byte_equal":True})
    assert len(report["images"])==32
    chains={
        "asset":["building_asset_v001.gd","building_asset_v004.gd","building_asset_v004r1.gd"],
        "demo":["building_demo_v001.gd","building_demo_v003.gd","building_demo_v004.gd","building_demo_v004r1.gd"],
        "actor":["building_demo_actor_v001.gd","building_demo_actor_v004.gd"]}
    names={"asset":"building_asset.gd","demo":"building_demo.gd","actor":"building_demo_actor.gd"}
    for group,chain in chains.items():
        effective={}
        oldtexts={}
        for filename in chain:
            text=z.read("scripts/ember/"+filename).decode("utf-8-sig")
            oldtexts[filename]=text
            for key,body in methods(text).items():effective[key]=(filename,body)
        newtext=(ROOT/"scripts/ember"/names[group]).read_text(encoding="utf-8-sig")
        newmethods=methods(newtext)
        records=[]
        diff=[]
        for key,body in newmethods.items():
            assert key in effective
            origin,oldbody=effective[key]
            equal=normalized_body(body)==normalized_body(oldbody)
            records.append({"method":key,"effective_old_source":origin,"body_text_equal_excluding_blank_comment":equal})
            if not equal:
                diff.extend(difflib.unified_diff(oldbody.splitlines(),body.splitlines(),fromfile=origin+"::"+key,tofile=names[group]+"::"+key,lineterm=""))
        (OUT/(group+"-effective-method-diff.txt")).write_text("\n".join(diff),encoding="utf-8")
        report["effective_methods"][group]={"methods":records,"removed_old_methods":sorted(set(effective)-set(newmethods))}
    oldshader=z.read("shaders/ember/building_intact_v004.gdshader")
    newshader=(ROOT/"shaders/ember/building_intact.gdshader").read_bytes()
    assert oldshader==newshader
    report["shader_old_body_byte_equal"]=True
    report["prefabs"]=[]
    for source in sorted((ROOT/"scenes/ember/building_assets_v004r1").glob("*.tscn")):
        relative=source.relative_to(ROOT).as_posix()
        old=z.read(relative).decode("utf-8-sig").replace("\r\n","\n")
        new=source.read_text(encoding="utf-8-sig")
        expected=old.replace("scripts/ember/building_asset_v004r1.gd","scripts/ember/building_asset.gd").replace("scripts/ember/building_demo_v004r1.gd","scripts/ember/building_demo.gd")
        if new!=expected:
            print(relative)
            print("\n".join(difflib.unified_diff(expected.splitlines(),new.splitlines(),lineterm="")))
        assert new==expected
        report["prefabs"].append({"path":relative,"only_expected_runtime_route_replacement":True,"bytes_unchanged":new==old})
    assert len(report["prefabs"])==7
    oldcatalog=z.read("assets/ember/building_assets_v004/catalog_v004.json")
    baseline_copy=(ROOT/"art-source/ember/building-assets-v004/registration_baseline_v004.json").read_bytes()
    report["old_registration_baseline_original_v004_byte_equal"]=oldcatalog==baseline_copy
    assert json.loads(oldcatalog.decode("utf-8-sig"))==json.loads(baseline_copy.decode("utf-8-sig"))
    report["old_registration_baseline_frozen_r1_old_catalog_json_equal"]=True
    report["registration_baseline_sha256"]=sha(baseline_copy)
    for filename in ["validate_capture_buildings_v004r1.gd","export_building_parts_v004r1.gd","build_building_coverage_v004r1.gd"]:
        old=z.read("tools/"+filename).decode("utf-8-sig")
        new=(ROOT/"tools"/filename).read_text(encoding="utf-8-sig")
        (OUT/(filename+".diff.txt")).write_text("\n".join(difflib.unified_diff(old.splitlines(),new.splitlines(),fromfile="frozen/"+filename,tofile="current/"+filename,lineterm="")),encoding="utf-8")
report["main_project_sha256"]=sha((ROOT/"project.godot").read_bytes())
report["main_project_matches_provenance_before"]=report["main_project_sha256"]==provenance["main_project_before"]["sha256"]
assert report["main_project_matches_provenance_before"]
for entry in result["files"]:
    observed=sha((ROOT/entry["path"]).read_bytes())
    if entry["path"]=="docs/shader-learning/ember-building-standard-v002.md":
        assert observed in {entry["sha256"],"ac27621a08fc9ac568188ad66ff99613d520a1ed8bdfe9e4329bffe40ddde9c8"}
        report["new_sources"].append({**entry,"observed_sha256":observed,"known_separate_TA_document_revision":observed!=entry["sha256"]})
    else:
        assert observed==entry["sha256"]
        report["new_sources"].append(entry)
sync=load(FINAL/"demo/SYNC_MANIFEST.json")
report["demo_synced_sources"]=[]
for item in sync:
    demo=(FINAL/"demo"/item["path"]).read_bytes()
    if sha(demo)!=item["sha256"] or demo!=(ROOT/item["path"]).read_bytes():
        print(json.dumps({"sync_difference":item["path"],"manifest":item["sha256"],"demo":sha(demo),"workspace":sha((ROOT/item["path"]).read_bytes())},ensure_ascii=False))
    matched=sha(demo)==item["sha256"] and demo==(ROOT/item["path"]).read_bytes()
    if not matched:
        if item["path"]=="assets/ember/building_assets_v004r1/previews/validation_v004r1.json":
            assert demo==(FINAL/"verification/validation.json").read_bytes()
            report.setdefault("generated_evidence_differences",[]).append({"path":item["path"],"sync_manifest_old_sha256":item["sha256"],"demo_new_generated_sha256":sha(demo),"same_as_verification_validation":True,"not_runtime_change":True})
        elif item["path"]=="docs/shader-learning/ember-building-standard-v002.md":
            report["demo_document_revision_boundary"]={"sync_manifest_sha256":item["sha256"],"demo_sha256":sha(demo),"workspace_known_TA_sha256":sha((ROOT/item["path"]).read_bytes()),"outside_runtime_scope":True}
        else: raise AssertionError("Unexpected runtime demo sync difference: "+item["path"])
    target=COLD/item["path"]
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(demo)
    report["demo_synced_sources"].append(item)
project=(FINAL/"demo/project.godot").read_text(encoding="utf-8-sig")
(COLD/"project.godot").write_text(project.replace("[application]",'[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="Ember TA Final Buildings Independent"',1),encoding="utf-8")
# 冷项目中额外放入冻结运行依赖以供隔离的旧/新状态对照，不污染正式入口。
with ZipFile(baseline) as z:
    for source in [n for n in z.namelist() if n.startswith("scripts/ember/") and n.endswith(".gd")]:
        target=COLD/source
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(z.read(source))
    target=COLD/"shaders/ember/building_intact_v004.gdshader"
    target.write_bytes(z.read("shaders/ember/building_intact_v004.gdshader"))
author=load(FINAL/"verification/validation.json")
report["author_evidence"]={"sha256":sha((FINAL/"verification/validation.json").read_bytes()),"passed":author["passed"],"total":author["total"],"not_independent_rerun":True}
report["cleanup_scope"]="no deletion, move, bypass or cleanup attempt"
(OUT/"runtime-integrity.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"images":32,"prefabs":report["prefabs"],"demo_sources":len(sync),
    "changed_method_bodies":{g:[m["method"] for m in r["methods"] if not m["body_text_equal_excluding_blank_comment"]] for g,r in report["effective_methods"].items()}},ensure_ascii=False,indent=2))
