"""归档一张真实内置 imagegen 输出，保存完整提示词、参考哈希和原始工具路径。"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from PIL import Image

BATCH = Path(__file__).resolve().parents[1]
ROOT = BATCH.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--version", default=1, type=int)
    args = parser.parse_args()
    plan = json.loads((BATCH / "planned-catalog-v001.json").read_text(encoding="utf-8"))
    spec = next((entry for entry in plan["assets"] if entry["id"] == args.id), None)
    if spec is None or not args.source.is_file():
        raise SystemExit("未知资产或实际工具输出不存在")
    prompt_path = BATCH / "prompts" / f"{args.id}_v{args.version:03d}.txt"
    if not prompt_path.is_file():
        raise SystemExit("对应完整提示词缺失")
    target = BATCH / "generated" / f"{args.id}_master_v{args.version:03d}.png"
    digest = sha(args.source)
    if target.exists() and sha(target) != digest:
        raise SystemExit("不覆盖已有母稿；使用新版本")
    shutil.copyfile(args.source, target)
    with Image.open(target) as source:
        rgba = source.convert("RGBA")
        channel = rgba.getchannel("A")
        alpha = Counter(channel.get_flattened_data() if hasattr(channel, "get_flattened_data") else channel.getdata())
        measurement = {"canvas": list(source.size), "mode": source.mode,
                       "bbox": rgba.getchannel("A").getbbox(), "alpha_zero": alpha[0],
                       "alpha_opaque": alpha[255], "partial_alpha": sum(n for a, n in alpha.items() if 0 < a < 255)}
    record_path = BATCH / "generation-record.json"
    ledger = json.loads(record_path.read_text(encoding="utf-8")) if record_path.exists() else {"tool": "image_gen.imagegen", "records": []}
    record = {"id": args.id, "version": args.version, "tool": "image_gen.imagegen",
              "actual_tool_output": str(args.source.resolve()), "file": target.relative_to(ROOT).as_posix(),
              "sha256": digest, "prompt_file": prompt_path.relative_to(ROOT).as_posix(),
              "full_prompt": prompt_path.read_text(encoding="utf-8"),
              "references": [{"file": path, "sha256": sha(ROOT / path), "role": "STYLE_MATERIAL_REFERENCE"} for path in spec["references"]],
              "measurement": measurement, "archived_utc": datetime.now(timezone.utc).isoformat(),
              "status": "ACTUAL_TOOL_MASTER_NOT_NATIVE_ACCEPTANCE"}
    ledger["records"] = [old for old in ledger["records"] if (old["id"], old["version"]) != (args.id, args.version)] + [record]
    ledger["successful_outputs"] = len(ledger["records"])
    record_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"id": args.id, "file": record["file"], "sha256": digest, "measurement": measurement}, ensure_ascii=False))


if __name__ == "__main__":
    main()
