"""只读绑定最终同步证据；不运行同步工具，不复制或删除正式文件。"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
FINAL = ROOT / "art-source/ember/buildings-final"
def sha(data): return hashlib.sha256(data).hexdigest()
def read(path): return json.loads(path.read_text(encoding="utf-8-sig"))
snapshot_path = FINAL / "verification/review-snapshot.json"
snapshot = read(snapshot_path)
bound = []
for item in snapshot["files"]:
    data = (ROOT / item["path"]).read_bytes()
    assert sha(data) == item["sha256"] and len(data) == item["bytes"]
    bound.append(item)
source = read(FINAL / "demo/SOURCE_SYNC_MANIFEST.json")
final = read(FINAL / "demo/SYNC_MANIFEST.json")
assert len(source) == len(final) == 59
assert {i["path"] for i in source} == {i["path"] for i in final}
source_checks = []
final_checks = []
for item in source:
    assert sha((ROOT / item["path"]).read_bytes()) == item["sha256"]
    source_checks.append({"path": item["path"], "source_hash_matches": True})
for item in final:
    assert sha((FINAL / "demo" / item["path"]).read_bytes()) == item["sha256"]
    final_checks.append({"path": item["path"], "demo_hash_matches": True})
changed = [item["path"] for item in final if item["sha256"] != next(i["sha256"] for i in source if i["path"] == item["path"])]
assert changed == ["assets/ember/building_assets_v004r1/previews/validation_v004r1.json"]
integrity = read(OUT / "runtime-integrity.json")
runtime = [i for i in bound if i["path"].startswith(("scripts/", "shaders/"))]
for item in runtime:
    assert next(i["sha256"] for i in integrity["new_sources"] if i["path"] == item["path"]) == item["sha256"]
    assert sha((OUT / "cold-project" / item["path"]).read_bytes()) == item["sha256"]
checks = read(OUT / "cold-project/ta-runtime-incremental.json")
assert checks["total"] == checks["passed"] == 23 and checks["failures"] == []
assert (OUT / "cold-runtime-rendered.stderr.log").stat().st_size == 0
report = {
    "snapshot_sha256": sha(snapshot_path.read_bytes()),
    "snapshot_files": bound,
    "source_manifest_59": source_checks,
    "final_manifest_59": final_checks,
    "generated_evidence_changes_only": changed,
    "independent_runtime_tested_sources_match_final_snapshot": runtime,
    "independent_checks": {"passed": 23, "total": 23, "result_sha256": sha((OUT / "cold-project/ta-runtime-incremental.json").read_bytes()), "rendered_stderr_bytes": 0},
    "tool_review": "Whitelist copy; SOURCE hashes immediately after copy; final SYNC hashes after optional verification; no deletion or gameplay method changes.",
    "author_94": {"passed": snapshot["runtime_checks"]["passed"], "total": snapshot["runtime_checks"]["total"], "hash_bound_only_not_independent_rerun": True},
    "cleanup": "read-only evidence; no move, deletion, approval bypass or tool execution",
}
(OUT / "final-snapshot-binding.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "bound").mkdir(exist_ok=True)
for path in [snapshot_path, ROOT / "tools/sync_building_demo.ps1", FINAL / "verification/consolidation-result.json", FINAL / "demo/SOURCE_SYNC_MANIFEST.json", FINAL / "demo/SYNC_MANIFEST.json"]:
    (OUT / "bound" / path.name).write_bytes(path.read_bytes())
print("FINAL_BINDING 9 snapshot files; SOURCE 59/59; final SYNC 59/59; independent rendered 23/23")
