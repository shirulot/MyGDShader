"""首批素材交付封装：校验原稿复制一致性，并打包PNG、提示词与验收记录。
这里只读PNG字节，不生成、不编辑图片。输出目录固定在当前项目内。
"""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parents[4]
batch = root / "art-source/ember/batch-01"
record_path = batch / "generation-record.json"
record = json.loads(record_path.read_text(encoding="utf-8"))
checksums = []
for asset in record["assets"]:
    archived = root / asset["file"]
    digest = hashlib.sha256(archived.read_bytes()).hexdigest()
    original = Path(asset["source"])
    matched = original.exists() and hashlib.sha256(original.read_bytes()).hexdigest() == digest
    if not matched:
        raise SystemExit(f"母稿与工具原始输出不一致或来源已丢失：{asset['id']}")
    asset["sha256"] = digest
    asset["copy_matches_original_tool_output"] = matched
    checksums.append(f"{digest}  {asset['file']}")
record["archive_integrity"] = "7 source PNGs match original tool output byte-for-byte"
record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(batch / "masters.sha256").write_text("\n".join(checksums) + "\n", encoding="utf-8")

required = [
    root / "docs/shader-learning/asset-production-batch-01.md",
    root / "docs/shader-learning/resources.md",
    root / "docs/shader-learning/asset-generation-manifest.csv",
    root / "assets/ember/README.md",
    batch / "validation-masters.json",
    batch / "validation-native-probes.json",
]
for file in required:
    if not file.is_file():
        raise SystemExit(f"交付文件尚未完成：{file.relative_to(root)}")
delivery_dir = root / "art-source/ember/deliveries"
delivery_dir.mkdir(parents=True, exist_ok=True)
archive = delivery_dir / "ember_batch01_candidates_2026-10-03.zip"
files = set(required)
for directory in [batch, root / "art-source/ember/references"]:
    files.update(file for file in directory.rglob("*")
                 if file.is_file() and "__pycache__" not in file.parts)
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipped:
    for file in sorted(files):
        zipped.write(file, file.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as zipped:
    if zipped.testzip() is not None:
        raise SystemExit("ZIP完整性校验失败")
    names = zipped.namelist()
    # 每份素材母稿、提示词、诊断和报告都必须随包交付。
    assert len([name for name in names if "/generated/" in name and name.endswith(".png")]) == 7
    assert len([name for name in names if "/prompts/" in name and name.endswith(".txt")]) == 7
    assert not any(name.startswith("assets/ember/") and name.endswith(".png") for name in names)
print(json.dumps({"archive": archive.relative_to(root).as_posix(),
                  "bytes": archive.stat().st_size, "files": len(names),
                  "source_png_hashes_matched": 7, "approved_production_pngs": 0},
                 ensure_ascii=False, indent=2))

