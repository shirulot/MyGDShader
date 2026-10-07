"""只读复核原生瓦片轮廓与声明端口；输出只放在本次质量审计目录。

不调用旧验收工具，不修改已交付 PNG/TileSet/源图/报告/ZIP。
4 连通会把斜向 1px 裂纹误报成碎片，因此同时记录 4 和 8 连通。
连接检查不仅比较边缘，还检查端口内侧两行/列的 Alpha。
"""
from collections import Counter, deque
from pathlib import Path
from math import ceil
import hashlib
import json

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
CAT = ROOT / "assets/ember/environment/tilesets/ember_tiles_catalog_v001.json"
OPPOSITE = {"N": "S", "E": "W", "S": "N", "W": "E"}
STRUCTURAL_CATEGORIES = {"T01", "T02", "T03", "T04", "T05", "T06", "T07"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(mask, connectivity):
    """显式 BFS；返回像素坐标，可定位独立块而不凭组件数判定美术错误。"""
    visited = np.zeros(mask.shape, dtype=bool)
    result = []
    offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if connectivity == 8:
        offsets += [(1, 1), (-1, 1), (1, -1), (-1, -1)]
    height, width = mask.shape
    for y, x in zip(*np.nonzero(mask)):
        if visited[y, x]:
            continue
        queue = deque([(int(x), int(y))])
        visited[y, x] = True
        pixels = []
        while queue:
            u, v = queue.popleft()
            pixels.append((u, v))
            for dx, dy in offsets:
                xx, yy = u + dx, v + dy
                if 0 <= xx < width and 0 <= yy < height and mask[yy, xx] and not visited[yy, xx]:
                    visited[yy, xx] = True
                    queue.append((xx, yy))
        result.append(pixels)
    return sorted(result, key=len, reverse=True)


def summarize_component(pixels):
    return {"pixels": len(pixels), "bbox_inclusive": [min(x for x, y in pixels), min(y for x, y in pixels),
                                                       max(x for x, y in pixels), max(y for x, y in pixels)],
            "coordinates": pixels if len(pixels) <= 8 else None}


def edge(pixels, side, depth=0):
    if side == "N":
        return pixels[depth, :, :]
    if side == "S":
        return pixels[31 - depth, :, :]
    if side == "E":
        return pixels[:, 31 - depth, :]
    return pixels[:, depth, :]


def checker(width, height, step=4):
    im = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(im)
    for y in range(0, height, step):
        for x in range(0, width, step):
            color = (35, 48, 58, 255) if (x // step + y // step) % 2 else (65, 78, 88, 255)
            draw.rectangle((x, y, x + step - 1, y + step - 1), fill=color)
    return im


def main():
    catalog = json.loads(CAT.read_text(encoding="utf-8"))
    snapshot_paths = [CAT]
    snapshot_paths += sorted((ROOT / "assets/ember/environment/tilesets").glob("*.png"))
    snapshot_paths += sorted((ROOT / "assets/ember/environment/tilesets").glob("*.tres"))
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in snapshot_paths}
    records, tiles, imgs = [], {}, {}
    failures = []
    checks = []

    def check(label, passed, actual=None):
        item = {"check": label, "passed": bool(passed), "actual": actual}
        checks.append(item)
        if not passed:
            failures.append(item)

    for atlas in catalog["atlases"]:
        path = ROOT / atlas["texture"][6:]
        source = Image.open(path).convert("RGBA")
        pixels = np.asarray(source)
        check(atlas["id"] + ": binary_alpha", set(np.unique(pixels[:, :, 3])) <= {0, 255})
        board = Image.new("RGBA", (4 * 196, ceil(len(atlas["tiles"]) / 4) * 164), (20, 26, 34, 255))
        draw = ImageDraw.Draw(board)
        for index, tile in enumerate(atlas["tiles"]):
            x, y = tile["coord"]
            crop = source.crop((x * 32, y * 32, (x + 1) * 32, (y + 1) * 32))
            data = np.asarray(crop)
            mask = data[:, :, 3] > 0
            c4, c8 = components(mask, 4), components(mask, 8)
            holes = [c for c in components(~mask, 4) if not any(x in (0, 31) or y in (0, 31) for x, y in c)]
            record = {"id": tile["id"], "atlas": atlas["id"], "coord": tile["coord"],
                      "pixel_rect": [x * 32, y * 32, 32, 32], "category": tile["category"],
                      "components_4": [summarize_component(c) for c in c4],
                      "components_8": [summarize_component(c) for c in c8],
                      "enclosed_transparent_regions_4": [summarize_component(c) for c in holes]}
            records.append(record)
            tiles[tile["id"]] = (tile, data)
            imgs[tile["id"]] = crop
            if tile["category"] in STRUCTURAL_CATEGORIES:
                check(tile["id"] + ": whole_outline_8_connected", len(c8) == 1, len(c8))
            for side, interface in tile["interfaces"].items():
                if interface is None:
                    continue
                positions = [i for start, end in interface["ports"] for i in range(start, end)]
                for depth in range(3):
                    bad = [i for i in positions if edge(data, side, depth)[i, 3] != 255]
                    check(f"{tile['id']}:{side}: port_alpha_depth_{depth}", not bad, bad)
            bx, by = index % 4 * 196, index // 4 * 164
            display = checker(32, 32)
            display.alpha_composite(crop)
            board.alpha_composite(display.resize((128, 128), Image.Resampling.NEAREST), (bx + 4, by + 28))
            draw.text((bx + 4, by + 3), tile["id"], fill="white")
            draw.text((bx + 4, by + 15), f"atlas {x},{y}; 8c={len(c8)} 4c={len(c4)}", fill=(180, 197, 206))
        board.save(OUT / f"{atlas['id']}_all_tiles_4x.png")

    pairs = []
    for tile_id, (tile, pixels) in tiles.items():
        for side, interface in tile["interfaces"].items():
            if interface is None:
                continue
            for other_id, (other, other_pixels) in tiles.items():
                other_interface = other["interfaces"][OPPOSITE[side]]
                if not other_interface or interface["kind"] != other_interface["kind"]:
                    continue
                positions = [i for start, end in interface["ports"] for i in range(start, end)]
                first = edge(pixels, side)
                second = edge(other_pixels, OPPOSITE[side])
                gaps = [i for i in positions if first[i, 3] != 255 or second[i, 3] != 255]
                full_alpha_mismatch = np.nonzero(first[:, 3] != second[:, 3])[0].tolist()
                delta = np.abs(first.astype(int) - second.astype(int))
                color_mismatch = np.nonzero(np.any(delta[:, :3] != 0, axis=1))[0].tolist()
                exact_required = interface["exact_edge_required"] or other_interface["exact_edge_required"]
                record = {"first": tile_id, "side": side, "second": other_id, "kind": interface["kind"],
                          "port_gaps": gaps, "alpha_mismatch_anywhere": full_alpha_mismatch,
                          "rgb_mismatch_offsets": color_mismatch, "max_channel_rgb_delta": int(delta[:, :3].max()),
                          "exact_color_required": exact_required}
                pairs.append(record)
                check(f"pair:{tile_id}:{side}:{other_id}: opaque_ports", not gaps)
                check(f"pair:{tile_id}:{side}:{other_id}: full_edge_alpha", not full_alpha_mismatch)
                if exact_required:
                    check(f"pair:{tile_id}:{side}:{other_id}: exact_rgba", not np.any(delta))

    # E/S 展开正好覆盖每种物理拼接一次；N/W 是反向相同 PNG 拼接。
    canonical = [p for p in pairs if p["side"] in ("E", "S")]
    for page in range(ceil(len(canonical) / 20)):
        board = Image.new("RGBA", (4 * 264, 5 * 206), (20, 26, 34, 255))
        draw = ImageDraw.Draw(board)
        for i, pair in enumerate(canonical[page * 20:(page + 1) * 20]):
            first, second = imgs[pair["first"]], imgs[pair["second"]]
            horizontal = pair["side"] == "E"
            im = checker(64 if horizontal else 32, 32 if horizontal else 64)
            im.alpha_composite(first)
            im.alpha_composite(second, (32, 0) if horizontal else (0, 32))
            bx, by = i % 4 * 264, i // 4 * 206
            draw.text((bx + 3, by + 2), pair["first"] + " " + pair["side"], fill="white")
            draw.text((bx + 3, by + 15), pair["second"], fill="white")
            draw.text((bx + 3, by + 28), f"alpha gaps 0; RGB differs {len(pair['rgb_mismatch_offsets'])}", fill=(180, 197, 206))
            board.alpha_composite(im.resize((im.width * 2, im.height * 2), Image.Resampling.NEAREST), (bx + 4, by + 48))
        board.save(OUT / f"all_connections_{page + 1:02d}_2x.png")

    after = {p.relative_to(ROOT).as_posix(): sha(p) for p in snapshot_paths}
    check("read_only_source_files_unchanged", before == after)
    check("actual_declared_directed_connections", len(pairs) == 556, len(pairs))
    check("actual_physical_connection_previews", len(canonical) == 278, len(canonical))
    report = {"status": "PIXEL_MEASUREMENTS_PASS_VISUAL_REVIEW_PENDING" if not failures else "MEASUREMENT_FAILURE",
              "source_sha256_before": before, "source_sha256_after": after,
              "scope": {"atlas_pngs": 3, "tiles": len(records), "tile_pixels": [32, 32],
                        "directed_declared_connections": len(pairs), "physical_connection_previews": len(canonical)},
              "checks_count": len(checks), "failed_checks": failures, "checks": checks,
              "tile_measurements": records, "connection_measurements": pairs,
              "connection_kind_counts": dict(Counter(p["kind"] for p in pairs)),
              "rgb_mismatch_physical_connections": sum(bool(p["rgb_mismatch_offsets"]) for p in canonical),
              "interpretation": ["端口透明缺失是结构断裂；RGB 明暗不同另行视觉判断，不自动判为缺像素。",
                                 "只测声明连接。不同 kind 不是登记的合法拼法；岸线还区分水面方向。",
                                 "八连通适用于像素斜线。四连通多块不自动等于断裂。",
                                 "锈迹、散落螺栓、碎屑允许分散，记录具体坐标后人工判断。",
                                 "诊断棋盘格只是透明衬底，未写入正式素材。"]}
    (OUT / "tile-pixel-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "scope", "checks_count", "failed_checks", "rgb_mismatch_physical_connections")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
