"""逐张归档实际 imagegen 输出及来源；复制字节，不编辑图片。"""
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--reference", action="append", default=[])
    parser.add_argument("--version", type=int, default=1)
    args = parser.parse_args()
    plan = json.loads((BATCH / "planned-catalog-v001.json").read_text(encoding="utf-8"))
    if args.id not in {item["id"] for item in plan["frames"]} or args.id == "robot_idle_down":
        raise SystemExit("只能归档本批新增19帧，已验收的原朝下待机不重做")
    if args.version < 1:
        raise SystemExit("版本必须大于0")
    suffix = f"v{args.version:03d}"
    target = BATCH / "generated" / f"{args.id}_master_{suffix}.png"
    prompt = BATCH / "prompts" / f"{args.id}_{suffix}.txt"
    if not prompt.is_file() or not args.source.is_file():
        raise SystemExit("缺少实际工具输出或对应完整提示词")
    digest = hashlib.sha256(args.source.read_bytes()).hexdigest()
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
        raise SystemExit("已有同版本母稿，使用新的版本号以保留历史")
    target.parent.mkdir(exist_ok=True)
    shutil.copyfile(args.source, target)
    if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
        raise SystemExit("母稿复制校验失败")
    with Image.open(target) as im:
        alpha = Counter(im.convert("RGBA").getchannel("A").getdata())
        measurement = {"size": list(im.size), "mode": im.mode,
                       "alpha_zero": alpha[0], "alpha_opaque": alpha[255],
                       "partial_alpha": sum(count for level, count in alpha.items() if 0 < level < 255)}
    path = BATCH / "generation-record.json"
    record = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
        "tool": "image_gen.imagegen", "date": "2026-10-04", "timezone": "Asia/Irkutsk",
        "scope": "C01补19帧；所有母稿为实际逐资产工具输出，不等同原生生产PNG。",
        "references": "本项目新机器人，未引用旧游戏资源。",
        "records": [], "approved_new_production_frames": 0,
    }
    item = {"id": args.id, "version": args.version, "source": str(args.source.resolve()),
            "file": target.relative_to(ROOT).as_posix(), "prompt": prompt.relative_to(ROOT).as_posix(),
            "sha256": digest, "references": args.reference, "measurement": measurement,
            "archived_utc": datetime.now(timezone.utc).isoformat(),
            "status": "ACTUAL_TOOL_MASTER_NOT_NATIVE_ACCEPTANCE"}
    record["records"] = [old for old in record["records"]
                         if (old["id"], old["version"]) != (args.id, args.version)] + [item]
    record["successful_outputs"] = len(record["records"])
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"id": args.id, "file": item["file"], "sha256": digest, **measurement}, ensure_ascii=False))


if __name__ == "__main__":
    main()
