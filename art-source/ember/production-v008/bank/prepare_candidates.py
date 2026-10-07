"""Register complete bank artwork, then uniformly downsample review candidates.

No local alpha masks, edge copying, rotations, palette reduction or per-arm
stretching are applied. Failed semantic samples remain failed after export.
"""
from __future__ import annotations

from collections import deque
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
CANDIDATES = BASE / "candidates"
REVIEW = BASE / "review"


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def bbox(alpha: np.ndarray, threshold: int) -> list[int] | None:
    y, x = np.where(alpha > threshold)
    return [int(x.min()), int(y.min()), int(x.max()) + 1, int(y.max()) + 1] if len(x) else None


def components(alpha: np.ndarray, threshold: int) -> list[int]:
    remaining = set(map(tuple, np.argwhere(alpha > threshold)))
    areas = []
    while remaining:
        start = remaining.pop()
        queue = deque([start])
        size = 0
        while queue:
            y, x = queue.popleft()
            size += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    q = (y + dy, x + dx)
                    if q in remaining:
                        remaining.remove(q)
                        queue.append(q)
        areas.append(size)
    return sorted(areas, reverse=True)


def measurements(image: Image.Image) -> dict:
    array = np.array(image.convert("RGBA"))
    alpha = array[:, :, 3]
    edges = {"N": array[0], "E": array[:, -1], "S": array[-1], "W": array[:, 0]}
    return {
        "size": list(image.size),
        "alpha_values_count": int(len(np.unique(alpha))),
        "alpha_zero_count": int((alpha == 0).sum()),
        "alpha_bbox_nonzero": bbox(alpha, 0),
        "alpha_bbox_above_4": bbox(alpha, 4),
        "alpha_bbox_above_64": bbox(alpha, 64),
        "alpha_bbox_above_127": bbox(alpha, 127),
        "edge_alpha_above_127_pixel_counts": {name: int((edge[:, 3] > 127).sum()) for name, edge in edges.items()},
        "edge_alpha_nonzero_pixel_counts": {name: int((edge[:, 3] > 0).sum()) for name, edge in edges.items()},
    }


def observed_span(vector: np.ndarray, threshold: int = 127) -> dict:
    p = np.flatnonzero(vector > threshold)
    return {"first": int(p.min()), "last_exclusive": int(p.max()) + 1, "count": int(len(p))} if len(p) else {"first": None, "last_exclusive": None, "count": 0}


def rgba_difference(first: np.ndarray, second: np.ndarray) -> dict:
    # Transparent RGB is reported separately; compare visible RGB and alpha.
    visible = np.maximum(first[:, 3], second[:, 3]) > 0
    alpha_diff = np.abs(first[:, 3].astype(int) - second[:, 3].astype(int))
    rgb_diff = np.abs(first[:, :3].astype(int) - second[:, :3].astype(int))
    mismatch = (alpha_diff > 0) | (visible & np.any(rgb_diff > 0, axis=1))
    return {"samples": int(len(first)), "visible_rgba_mismatch_samples": int(mismatch.sum()), "alpha_mismatch_samples": int((alpha_diff > 0).sum()), "max_alpha_difference": int(alpha_diff.max()), "max_visible_rgb_difference": int(rgb_diff[visible].max()) if visible.any() else 0}


def main() -> None:
    CANDIDATES.mkdir(exist_ok=True)
    REVIEW.mkdir(exist_ok=True)
    prompts = json.loads((BASE / "prompts.json").read_text(encoding="utf-8"))
    # Each crop stays 1254x1254. Straight is translated as one whole graphic.
    # Out-of-source coordinates are transparent padding supplied by PIL crop.
    specs = [
        {"id": "bank_straight_N", "mask": 124, "raw": "bank_straight_N_v001.png", "crop": [0, 203, 1254, 1457], "offset": [0, -203], "status": "VISUAL_SAMPLE_PENDING_CONNECTION_REVIEW", "reason": "Complete N bank registered as one image; sidewall is relatively tall; exact interfaces pending."},
        {"id": "bank_outer_NW", "mask": 28, "raw": "bank_outer_NW_v002.png", "crop": [0, 0, 1254, 1254], "offset": [0, 0], "status": "VISUAL_SAMPLE_PENDING_CONNECTION_REVIEW", "reason": "One targeted repair improved north/west total width; exact connection interfaces remain pending."},
        {"id": "bank_inner_NW", "mask": 127, "raw": "bank_inner_NW_v002.png", "crop": [0, 0, 1254, 1254], "offset": [0, 0], "status": "REJECTED_SEMANTIC_AND_EDGE_CONTACT", "reason": "Still a short capped L, not a compact true NW concave-water corner; all four source edges have zero Alpha>127 contact. One repair round exhausted."},
    ]
    entries = []
    for spec in specs:
        raw_path = BASE / "raw" / spec["raw"]
        raw = Image.open(raw_path).convert("RGBA")
        registered = raw.crop(spec["crop"])
        candidate = registered.resize((128, 128), Image.Resampling.LANCZOS)
        destination = CANDIDATES / (spec["id"] + "_sample_v001.png")
        candidate.save(destination)
        candidate.resize((512, 512), Image.Resampling.NEAREST).save(REVIEW / (spec["id"] + "_4x.png"))
        alpha = np.array(candidate)[:, :, 3]
        entries.append({**spec, "raw_path": raw_path.relative_to(ROOT).as_posix(), "raw_sha256": digest(raw_path), "raw_measurements": measurements(raw), "crop_coordinate_convention": "left,top,right_exclusive,bottom_exclusive", "full_graphic_offset_native_pixels": spec["offset"], "registered_canvas": [1254, 1254], "out_of_bounds_transparency_padding": [0, 0, 0, max(0, spec["crop"][3] - raw.height)], "uniform_scale_factor": 128 / 1254, "resampling": "PIL LANCZOS", "candidate_path": destination.relative_to(ROOT).as_posix(), "candidate_sha256": digest(destination), "candidate_measurements": measurements(candidate), "candidate_components8_alpha_above_0": components(alpha, 0), "candidate_components8_alpha_above_127": components(alpha, 127), "observed_north_band_at_90_percent_width": observed_span(alpha[:, 115]), "observed_west_band_at_90_percent_height": observed_span(alpha[115]), "artwork_operations": ["one complete-image crop/translation with transparent padding", "uniform complete-image scale"], "no_local_pixel_or_alpha_repair": True})

    # Preview assembly only: these images deliberately reveal actual seams.
    straight = Image.open(CANDIDATES / "bank_straight_N_sample_v001.png").convert("RGBA")
    outer = Image.open(CANDIDATES / "bank_outer_NW_sample_v001.png").convert("RGBA")
    inner = Image.open(CANDIDATES / "bank_inner_NW_sample_v001.png").convert("RGBA")
    plane = Image.new("RGBA", (128 * 5, 128), (21, 49, 61, 255))
    for x in range(5):
        plane.alpha_composite(straight, (128 * x, 0))
    plane.save(REVIEW / "north_straight_repeat_1x.png")
    plane.resize((128 * 5 * 2, 256), Image.Resampling.NEAREST).save(REVIEW / "north_straight_repeat_2x.png")
    join = Image.new("RGBA", (128 * 4, 128 * 2), (21, 49, 61, 255))
    join.alpha_composite(outer, (0, 0))
    for x in range(1, 4):
        join.alpha_composite(straight, (128 * x, 0))
    join.save(REVIEW / "nw_outer_to_north_partial_1x.png")
    join.resize((128 * 4 * 2, 128 * 2 * 2), Image.Resampling.NEAREST).save(REVIEW / "nw_outer_to_north_partial_2x.png")
    review = Image.new("RGBA", (512 * 3, 552), (21, 49, 61, 255))
    drawing = ImageDraw.Draw(review)
    for i, (spec, image) in enumerate(zip(specs, (straight, outer, inner))):
        review.alpha_composite(image.resize((512, 512), Image.Resampling.NEAREST), (i * 512, 0))
        drawing.text((i * 512 + 8, 520), f'{spec["id"]} mask={spec["mask"]}', fill=(226, 235, 238, 255))
        drawing.text((i * 512 + 8, 536), "REJECTED: wrong corner/ports" if spec["mask"] == 127 else "CANDIDATE: exact seams pending", fill=(226, 185, 126, 255))
    review.save(REVIEW / "three_samples_4x.png")
    a, b = np.array(straight), np.array(outer)
    report = {"status": "TWO_VISUAL_CANDIDATES_ONE_REJECTED_NO_ATLAS_RELEASE", "tool": "image_gen.imagegen built-in", "producer": "v008_bank_samples", "user_visual_approval": False, "is_atlas": False, "single_component_images": True, "texture_size": [128, 128], "world_cell": [32, 32], "scope": "Only N straight, NW outer and failed NW inner sample. No rotated/mirrored full pool-loop proof.", "reference_files": [{"path": "art-source/ember/autotiles-v003/industrial_tile_master_v003.png", "role": "approved material/style", "sha256": digest(ROOT / "art-source/ember/autotiles-v003/industrial_tile_master_v003.png")}, {"path": "art-source/ember/autotiles-v007/bank_master.png", "role": "read-only prior raw comparison", "sha256": digest(ROOT / "art-source/ember/autotiles-v007/bank_master.png")}, {"path": "art-source/ember/autotiles-v007/bank_normalized.png", "role": "read-only prior normalized comparison", "sha256": digest(ROOT / "art-source/ember/autotiles-v007/bank_normalized.png")}], "prompts_path": (BASE / "prompts.json").relative_to(ROOT).as_posix(), "prompts_sha256": digest(BASE / "prompts.json"), "raw_generation_count": len(prompts["prompts"]), "raw_images": [{"path": p.relative_to(ROOT).as_posix(), "sha256": digest(p), "measurements": measurements(Image.open(p)), "prompt_id": p.stem} for p in sorted((BASE / "raw").glob("*.png"))], "candidate_entries": entries, "connection_observations": {"repeated_straight_E_to_W": rgba_difference(a[:, -1], a[:, 0]), "outer_E_to_straight_W": rgba_difference(b[:, -1], a[:, 0]), "numeric_results_are_not_visual_approval": True, "interfaces_not_forced": True}, "rejected_originals": {"bank_outer_NW_v001": "North complete side band was about304px while west255px; directional thickness inconsistent.", "bank_inner_NW_v001": "Over-large approximately44% span, capped short L, wrong mask127 footprint.", "bank_inner_NW_v002": "Still capped short L and source four edges lack Alpha>127 contact; semantic rejection."}, "remaining_issues": ["Exact RGBA interface equality is not yet achieved; do not publish as connected production atlas.", "Straight bank dark vertical sidewall is visually tall relative to coping; compare at 128px.", "Generated raw files contain faint alpha=1 stray pixels; preserved rather than threshold/mask cleaned.", "Inner NW remains rejected after one targeted imagegen repair, requires future genuinely correct complete artwork.", "No south/east other-direction art generated and no lighting-rotated full loop claimed."], "review_composition": "PIL diagnostic compositing only, flat-color water placeholder; no image geometry or interfaces repaired", "script_sha256": digest(Path(__file__)), "previews": [p.relative_to(ROOT).as_posix() for p in sorted(REVIEW.glob("*.png"))]}
    (BASE / "generation-record.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "entries": len(entries), "connections": report["connection_observations"]}))


if __name__ == "__main__":
    main()
