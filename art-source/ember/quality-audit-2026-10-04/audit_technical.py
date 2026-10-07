"""技术输入专项只读检查：按通道语义判断连续性，不把测试孔洞或粒子误判为坏图。"""
from collections import Counter, deque
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(mask, diagonal=True):
    """使用8邻接判断像素形状；同时可记录4邻接，保留对角线的合法连接语义。"""
    remaining = set(zip(*np.nonzero(mask)))
    result = []
    offsets = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
               if (dy or dx) and (diagonal or abs(dy) + abs(dx) == 1)]
    while remaining:
        start = remaining.pop()
        queue = deque([start])
        points = [start]
        while queue:
            y, x = queue.popleft()
            for dy, dx in offsets:
                q = (y + dy, x + dx)
                if q in remaining:
                    remaining.remove(q)
                    queue.append(q)
                    points.append(q)
        ys, xs = zip(*points)
        result.append({"pixels": len(points), "bbox_inclusive": [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]})
    return sorted(result, key=lambda p: -p["pixels"])


def main():
    catalog_path = ROOT / "assets/ember/data/technical_inputs_catalog_v001.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    checks, details = [], []

    def check(name, value):
        checks.append({"check": name, "pass": bool(value)})

    for asset in catalog["assets"]:
        path = ROOT / asset["file"].removeprefix("res://")
        with Image.open(path) as image:
            image.load()
            check(asset["id"] + ":source SHA", sha(path) == asset["sha256"])
            check(asset["id"] + ":canvas and mode", list(image.size) == asset["canvas"] and image.mode == asset["mode"])
            array = np.asarray(image)
            info = {"id": asset["id"], "file": asset["file"], "manifest_id": asset["manifest_id"], "sha256": sha(path)}
            if asset["manifest_id"] == "D08":
                base = ROOT / asset["source_file"].removeprefix("res://")
                alpha = np.asarray(Image.open(base).convert("RGBA"))[:, :, 3]
                check(asset["id"] + ":registered base SHA", sha(base) == asset["source_sha256"])
                check(asset["id"] + ":Alpha matches actual base", np.array_equal(array[:, :, 3], alpha))
                check(asset["id"] + ":RGB selection inside base", not np.any((array[:, :, :3] > 0) & (alpha[:, :, None] == 0)))
                info["interpretation"] = "A copies base silhouette exactly; separated R/G windows are intentional selections, not body fragments"
            elif asset["manifest_id"] == "D03":
                info["foreground_components"] = components(array > 0)
                check(asset["id"] + ":connected shape", len(info["foreground_components"]) == 1)
                info["interpretation"] = "Single connected circle/star foreground; L is mask intensity, not Alpha"
            elif asset["manifest_id"] == "D10":
                alpha = array[:, :, 3]
                info["components_8"] = components(alpha > 0)
                info["components_4"] = components(alpha > 0, diagonal=False)
                check(asset["id"] + ":connected particle at 8-neighbor", len(info["components_8"]) == 1)
                check(asset["id"] + ":binary Alpha", set(np.unique(alpha)) <= {0, 255})
                info["interpretation"] = "Diagonal line/rain uses 8-neighbor connectivity; separate 4-neighbor pixels are not missing segments"
            elif asset["manifest_id"] == "D05":
                info["interpretation"] = "Transparent ellipse hole, isolated 1px L-shaped line/test block and partial Alpha ramp are explicitly designed test features"
            elif asset["manifest_id"] == "D04":
                check(asset["id"] + ":X wrap exact", np.array_equal(array[:, 0], array[:, -1]))
                check(asset["id"] + ":Y wrap exact", np.array_equal(array[0], array[-1]))
                info["interpretation"] = "Noise is scalar data; disconnected threshold contours are expected, native wrap edges are checked"
            elif asset["manifest_id"] == "D12":
                base = ROOT / asset["sources"][0]["file"].removeprefix("res://")
                alpha = np.asarray(Image.open(base).convert("RGBA"))[:, :, 3]
                rows = np.arange(array.shape[0], dtype=float)[:, None]
                expected = np.where(alpha > 0, np.rint(np.clip((119 - rows) / 109, 0, 1) * 255), 0).astype(np.uint8)
                check(asset["id"] + ":actual grass registration", np.array_equal(array, expected))
                info["interpretation"] = "Root row 119 and all transparent exterior intentionally have zero weight; root zero is not a hole in grass Alpha"
            elif "normal" in asset["id"]:
                vector = array.astype(float) / 255 * 2 - 1
                unit_error = np.max(np.abs(np.linalg.norm(vector, axis=2) - 1))
                info["max_unit_length_error"] = float(unit_error)
                check(asset["id"] + ":quantized valid normals", unit_error < 0.012)
                info["interpretation"] = "RGB tangent-vector data; blue exterior/flat concrete is neutral normal rather than missing silhouette"
            else:
                info["interpretation"] = "Calibration/ramp/energy/height/material parameter data; assess declared channel semantics rather than single-body Alpha"
            details.append(info)
    check("technical physical PNG count", len(details) == 40)
    check("manifest counts", Counter(a["manifest_id"] for a in details) == Counter({
        "D01": 5, "D02": 2, "D03": 2, "D04": 2, "D05": 1, "D06": 2,
        "D07": 2, "D08": 10, "D09": 3, "D10": 4, "D11": 6, "D12": 1}))
    failures = [c["check"] for c in checks if not c["pass"]]
    result = {"status": "TECHNICAL_CHANNEL_AND_TOPOLOGY_RECHECK_PASS" if not failures else "TECHNICAL_RECHECK_FAILED",
        "catalog_sha256": sha(catalog_path), "physical_pngs": len(details), "checks": len(checks),
        "failed_checks": len(failures), "failures": failures, "assets": details, "results": checks,
        "scope": "Current source PNG and explicit channel geometry; does not certify all future shader effects or recover defects already present in registered base art."}
    (OUT / "technical-report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Technical quality recheck: {len(details)} PNG / {len(checks)} checks / {len(failures)} failed")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
