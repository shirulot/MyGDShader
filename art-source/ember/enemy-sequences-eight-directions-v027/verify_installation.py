"""汇总实际安装、旧版本保护和预览发布证据，供技术美术总监增量复核。"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
QA = ROOT / "qa"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding="utf-8"))

before = read(QA / "protected_files_before_install.json")
after = {}
for relative, expected in before["files"].items():
    p = REPO / relative
    actual = dict(sha256=sha(p), bytes=p.stat().st_size)
    assert actual == expected, f"Protected file changed: {relative}"
    after[relative] = dict(before=expected, after=actual, unchanged=True)

copy_receipt = read(QA / "project_asset_copy_receipt.json")
for row in copy_receipt["files"]:
    p = REPO / row["path"]
    assert sha(p) == row["sha256"] and p.stat().st_size == row["bytes"]
assert len(copy_receipt["files"]) == 1157

settings = []
target = Path(copy_receipt["target"])
for p in sorted(target.rglob("*.png.import")):
    meta = p.read_text(encoding="utf-8")
    for key, value in [
        ("compress/mode", "0"), ("detect_3d/compress_to", "0"),
        ("mipmaps/generate", "false"), ("process/fix_alpha_border", "false"),
        ("process/premult_alpha", "false"),
    ]:
        assert re.search(r"^" + re.escape(key) + "=" + value + r"$", meta, re.M), p
    cache = re.search(r'^path="res://([^"]+)"', meta, re.M)
    assert cache and (REPO / cache.group(1)).is_file(), p
    settings.append(dict(path=p.relative_to(REPO).as_posix(), sha256=sha(p)))
assert len(settings) == 1152

loaded = read(QA / "installed_resource_load.json")
assert loaded["status"] == "PASS" and loaded["frames"] == 960
assert len(loaded["records"]) == 960 and all(r["passed"] for r in loaded["records"])
web = read(QA / "current_preview_receipt.json")
assert web["status"] == "PASS" and web["files_match_frozen_web"] == 1154
archived = {}
for relative, digest in before["current_preview_before"].items():
    p = Path(web["prior_preview"]) / relative
    assert sha(p) == digest
    archived[relative] = dict(before=digest, archived=sha(p), unchanged=True)

protection = dict(status="PASS", protected_count=len(after), files=after, legacy_preview=archived)
(QA / "installation_protection_receipt.json").write_text(
    json.dumps(protection, indent=2), encoding="utf-8"
)
evidence_names = [
    "project_asset_copy_receipt.json", "installed_import_receipt.json",
    "installed_resource_load.json", "current_preview_receipt.json",
    "protected_files_before_install.json", "installation_protection_receipt.json",
]
receipt = dict(
    status="AUTHOR_INSTALLATION_CHECK_PASS_AWAITING_TA_INCREMENTAL_REVIEW",
    zip_sha256=copy_receipt["zip_sha256"], target=str(target),
    clips=160, frames=960, installed_payload_files=1157,
    imported_png_files=len(settings), protected_files_unchanged=len(after),
    current_preview=web["url"], fixed_preview=web["fixed_url"],
    preview_files_match_frozen_web=1154, legacy_preview_preserved=True,
    import_settings=settings,
    evidence={name: dict(path=(QA/name).relative_to(REPO).as_posix(), sha256=sha(QA/name)) for name in evidence_names},
    scope="Actual installed visual resources and preview; main gameplay was not launched or changed.",
)
(QA / "installation_submission_receipt_v001.json").write_text(
    json.dumps(receipt, indent=2), encoding="utf-8"
)
print(json.dumps({k:v for k,v in receipt.items() if k not in ["import_settings", "evidence"]}))
