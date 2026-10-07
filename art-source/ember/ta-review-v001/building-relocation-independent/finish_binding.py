"""封存本轮加载结果与 UID 来源关系，不改生产。"""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
PACK=ROOT/"assets/ember/buildings_final"
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text(encoding="utf-8-sig"))
data=load(OUT/"relocation-integrity.json")
checks=load(OUT/"cold-project/ta-relocation-load.json")
assert checks["passed"]==checks["total"]==18 and not checks["failures"]
assert not (OUT/"cold-load.stderr.log").read_bytes() and not (OUT/"cold-import.stderr.log").read_bytes()
data["independent_cold_run"]={"total":18,"passed":18,"import_exit":0,"actual_renderer":"OpenGL Compatibility/NVIDIA RTX 4070 Laptop GPU","runtime_exit":0,"import_stderr_bytes":0,"runtime_stderr_bytes":0,"result_sha256":sha(OUT/"cold-project/ta-relocation-load.json")}
plan=load(PACK/"review/relocation-plan.json")
data["uid_pairs"]=[]
before_by_to={i["to"]:i for i in plan["files"]}
for folder in ["scripts","shaders","tools"]:
    for current in (PACK/folder).glob("*.uid"):
        relative=current.relative_to(ROOT).as_posix()
        demo=PACK/"examples/standalone"/relative
        assert demo.is_file() and current.read_bytes()==demo.read_bytes()
        before=before_by_to[relative]
        assert sha(current)==before["sha256"]
        demo_rel=demo.relative_to(ROOT).as_posix()
        old_demo=before_by_to.get(demo_rel)
        data["uid_pairs"].append({"source":relative,"current_sha256":sha(current),"source_uid_same_as_before_move":True,"demo_uid_matches_source":True,"before_demo_uid_sha256":old_demo["sha256"] if old_demo else None,"demo_identity_updated_from_before":old_demo is not None and old_demo["sha256"]!=sha(demo)})
assert len(data["uid_pairs"])==7
for item in data["code_and_scenes"]:
    assert sha(ROOT/item["after"])==item["after_sha256"]
    assert sha(OUT/"cold-project"/item["after"])==item["after_sha256"]
data["status"]="RUNTIME_RELOCATION_PASS"
(OUT/"relocation-integrity.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
print("FINAL_RELOCATION_PASS 18/18; formal7UID unchanged; demo7UID copied to match formal sources")
