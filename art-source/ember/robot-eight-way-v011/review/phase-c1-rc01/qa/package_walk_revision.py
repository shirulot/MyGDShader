"""封包、逐项核哈希并冷解压到新目录。拒绝覆盖任何既有交付或冷副本。"""
from pathlib import Path
import hashlib
import json
import re
import sys
import zipfile

root = Path(__file__).resolve().parents[1]
revision, date = sys.argv[1:3]
if not re.fullmatch(r"phase-[bc]\d-rc\d{2}", revision) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
    raise ValueError("Invalid revision or date")
frozen = root / "review" / revision
catalog_bytes = (frozen / "sha256-manifest.json").read_bytes()
catalog = json.loads(catalog_bytes)
digest = lambda b: hashlib.sha256(b).hexdigest()
archive = root.parent / "deliveries" / f"robot_eight_way_v011_{revision.replace('-', '_')}_{date}.zip"
cold = root / "review" / f"cold-{revision}"
if archive.exists() or cold.exists():
    raise FileExistsError("Choose a fresh delivery and cold destination")
for item in catalog["files"]:
    data = (frozen / item["file"]).read_bytes()
    if len(data) != item["bytes"] or digest(data) != item["sha256"]:
        raise ValueError("Frozen payload changed: " + item["file"])
archive.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for file in sorted(frozen.rglob("*")):
        if file.is_file():
            z.write(file, file.relative_to(frozen).as_posix())
with zipfile.ZipFile(archive) as z:
    for item in catalog["files"]:
        if digest(z.read(item["file"])) != item["sha256"]:
            raise ValueError("ZIP payload changed: " + item["file"])
    # 目标必须全部落在本次新冷副本内；不接受绝对路径或 .. 条目。
    for name in z.namelist():
        (cold / name).resolve().relative_to(cold.resolve())
    z.extractall(cold)
    entries = len(z.infolist())
metadata_file = "action-pilot-metadata.json" if revision.startswith("phase-c") else "walk-batch-metadata.json"
report = {
    "revision": revision, "zip": str(archive), "zip_sha256": digest(archive.read_bytes()),
    "zip_bytes": archive.stat().st_size, "zip_entries": entries,
    "payload_files": len(catalog["files"]), "payload_hash_mismatches": 0,
    "sha256_manifest_sha256": digest(catalog_bytes),
    "metadata_file": metadata_file,
    "metadata_sha256": digest((frozen / metadata_file).read_bytes()),
    "cold_root": str(cold), "cold_engine_validation": "NOT_RUN_YET"
}
(root / "qa" / f"delivery_{revision}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report))
