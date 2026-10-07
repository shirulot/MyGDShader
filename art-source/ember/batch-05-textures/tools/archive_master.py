"""原样归档一次内置 imagegen 的单资产输出；只测量母稿，不改其像素。"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

BATCH = Path(__file__).resolve().parents[1]
ROOT = BATCH.parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    planned = json.loads((BATCH / "planned-catalog-v001.json").read_text(encoding="utf-8"))
    item = next(a for a in planned.get("assets", planned.get("textures", [])) if a["id"] == args.id)
    raw = args.source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    target = BATCH / "generated" / f"{args.id}_master_v001.png"
    # 保留工具原始文件；归档绝不对 PNG 重编码，已存在时只接受同字节。
    if target.exists() and target.read_bytes() != raw:
        raise SystemExit("已有归档不同，拒绝覆盖：" + str(target))
    target.write_bytes(raw)
    with Image.open(target) as image:
        rgba = image.convert("RGBA")
        histogram = rgba.getchannel("A").histogram()
        measurement = {
            "size": list(image.size), "mode": image.mode,
            "alpha_zero": histogram[0], "alpha_opaque": histogram[255],
            "partial_alpha": sum(histogram[1:255]),
        }
    ledger_path = BATCH / "generation-record.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if any(r["id"] == args.id for r in ledger["records"]):
        raise SystemExit("重复来源登记，拒绝重复计调用：" + args.id)
    ledger["records"].append({
        "id": args.id, "manifest_id": item["manifest_id"],
        "source": str(args.source.resolve()), "file": target.relative_to(ROOT).as_posix(),
        "prompt": item["prompt"], "sha256": digest, "measurement": measurement,
        "references": ledger["references"], "version": 1,
        "status": "ACTUAL_TOOL_MASTER_NOT_NATIVE_ACCEPTANCE",
        "archived_utc": datetime.now(timezone.utc).isoformat(),
    })
    ledger["calls"].append({"id": args.id, "tool": "image_gen.imagegen", "success": True,
                            "output_sha256": digest, "transparent_requested": item["transparent_requested"]})
    ledger["successful_outputs"] = len(ledger["records"])
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"id": args.id, "sha256": digest, **measurement}, ensure_ascii=False))


if __name__ == "__main__":
    main()
