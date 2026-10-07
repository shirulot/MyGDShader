"""冻结包 UI 定点审查准备：解冷副本，绑定增量源码与旧运行几何。生产只读。"""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json

ROOT = Path("E:/dev/shader/godot-shader/godot-shader-simple")
OUT = Path(__file__).resolve().parent
COLD = OUT / "cold-project"
OLD = ROOT / "art-source/ember/deliveries/building_assets_v004_2026-10-06.zip"
NEW = ROOT / "art-source/ember/deliveries/building_assets_v004r1_2026-10-06.zip"
EXPECTED = "22dc4017aef594f33350e71b0af723909fbd1c4fde1a88208c9a66e34c9e2a32"
def sha(raw): return hashlib.sha256(raw).hexdigest()
def load(z, name): return json.loads(z.read(name).decode("utf-8-sig"))
def equivalent(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= 1e-12
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equivalent(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(equivalent(a[k], b[k]) for k in a)
    return a == b
assert NEW.stat().st_size == 28875505 and sha(NEW.read_bytes()) == EXPECTED
report = {"zip_sha256": EXPECTED, "zip_bytes": NEW.stat().st_size}
with ZipFile(NEW) as new, ZipFile(OLD) as old:
    files = [r for r in new.infolist() if not r.is_dir()]
    assert len(files) == len({r.filename for r in files}) == 79
    manifest = load(new, "DELIVERY_MANIFEST.json")
    assert len(manifest["files"]) == 78
    assert set(new.namelist()) == {r["path"] for r in manifest["files"]} | {"DELIVERY_MANIFEST.json"}
    for item in manifest["files"]:
        data = new.read(item["path"])
        assert len(data) == item["bytes"] and sha(data) == item["sha256"]
    for item in files:
        target = (COLD / item.filename).resolve()
        assert target.is_relative_to(COLD.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(new.read(item))
    common_code = sorted({n for n in new.namelist() if n.endswith((".gd", ".gdshader"))} & set(old.namelist()))
    comparison = [{"path": n, "old_sha256": sha(old.read(n)), "new_sha256": sha(new.read(n)), "same": old.read(n) == new.read(n)} for n in common_code]
    report["common_code"] = comparison
    report["changed_common_code"] = [r["path"] for r in comparison if not r["same"]]
    old_catalog = load(old, "assets/ember/building_assets_v004/catalog_v004.json")
    new_catalog = load(new, "assets/ember/building_assets_v004r1/catalog_v004r1.json")
    report["catalog_top_level_keys"] = {"old": list(old_catalog), "new": list(new_catalog)}
    # 名称、脚印、源枢轴、统一比例、门洞/净口及各活动区均逐字段对照；生产贴图路由允许改变。
    geometry_keys = ["id", "name", "uniform_scale", "source_pivot_px", "footprint_px", "doors",
                     "service_rect", "hatch_rect", "lens_rects", "glass_rects", "service_mount_x"]
    report["geometry"] = []
    for a, b in zip(old_catalog["buildings"], new_catalog["buildings"]):
        fields = {key: equivalent(a.get(key), b.get(key)) for key in geometry_keys}
        assert all(fields.values())
        report["geometry"].append({"id": a["id"], "unchanged_fields": fields,
            "numeric_tolerance_px": 1e-12, "exact_doors_match": a["doors"] == b["doors"],
            "old_texture": a["complete_texture"], "new_texture": b["complete_texture"]})
    report["new_code_paths"] = sorted({n for n in new.namelist() if n.endswith((".gd", ".gdshader"))} - set(old.namelist()))
    # 作者新94项仅绑定报告，不记作独立执行。
    candidate_reports = [n for n in new.namelist() if n.endswith(".json") and "validation" in n]
    report["author_validation_paths"] = candidate_reports
    for path in candidate_reports:
        data = load(new, path)
        report.setdefault("author_evidence", []).append({"path": path, "sha256": sha(new.read(path)),
            "passed": data.get("passed"), "total": data.get("total"), "not_independent_rerun": True})
    report["manifest_cold_runtime"] = manifest.get("cold_runtime")
    project = COLD / "project.godot"
    config = project.read_text(encoding="utf-8-sig")
    report["original_project_sha256"] = sha(project.read_bytes())
    config = config.replace("[application]", '[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="Ember TA v004r1 UI Independent"', 1)
    project.write_text(config, encoding="utf-8")
report["manifest_payload_verified"] = 78
report["status"] = "INCREMENTAL_BINDING_PASS"
(OUT / "incremental-binding.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: report[k] for k in ["status", "changed_common_code", "new_code_paths", "author_evidence", "manifest_cold_runtime"]}, ensure_ascii=False, indent=2))
