"""Prepare the six prop briefs; no generated image or delivery is fabricated.

This script writes only the new supplement/props source directory.  The existing
native PNGs are read-only style references and the protection snapshot is narrow
enough to remain useful while other supplement workers add their own outputs.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[3]

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()

def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

REFERENCES = [
    "assets/ember/props/story/toolbox_v001.png",
    "assets/ember/buildings/console/console_base_v001.png",
    "assets/ember/buildings/pump/pump_base_v001.png",
    "assets/ember/characters/robot/robot_idle_down_v001.png",
]

COMMON = """Use case: stylized-concept.
Asset type: one isolated game prop design master for Ember Energy Station.
Input images 1-4 are STYLE, MATERIAL AND MANUFACTURER references only, all from the project's approved NEW native artwork. Do not copy a robot, console or pump as the requested object.
Orthographic top-down three-quarter view: modest top and front surfaces, straight horizontal and vertical world axes; not isometric diamond perspective.
Hand-finished pixel clusters, restrained detail density and usually one logical pixel dark outline. Blue-grey painted steel, pale ceramic corners and small brass fittings; three or four flat material shades with subtle top-left volume light.
Palette only: #101820 #182631 #2B3E4B #4D6470 #829BA3 #BECBC4 #7B4D35 #B77C4B #E2B77A #51C5C2 #E5A44B #E65B4A #566B78 #203A4B #406B78 #ECE9D8. Prefer the neutral steel, ceramic and brass subset; do not use cyan/orange/red as lit operational indicators.
Exactly ONE complete coherent object centered in genuine transparent Alpha background, with substantial empty margins. No painted checkerboard, ground, cast shadow, scene, text, letters, numbers, logo, watermark, UI, guide lines or measurements. No glow, light beam, rain, fire, smoke, shield or active-state effects.
This is a larger design master for later explicit native pixel finishing, not an already accepted 64x64 production PNG. Preserve the logical pixel and material density of the references.
"""

SPECS = [
    ("S-P01", "cable_spool", [42, 34], "A single squat industrial cable spool laid upright on a small steel foot: two steel side flanges, a clearly wound dark blue-grey cable around a horizontal hub, one small brass connector parked against the coil. Keep the cable end attached to the coil, no detached floating pieces, no wire spilling outside the object."),
    ("S-P02", "junction_box", [36, 32], "A single compact sealed junction box on a low base: rectangular blue-grey steel housing, pale ceramic corner guards, a closed removable lid, two modest brass cable glands and a neutral dark recessed service slot. Closed and unpowered, no running cables or illuminated screen."),
    ("S-P03", "safety_bollard", [26, 44], "A single low industrial safety bollard: narrow rounded rectangular steel post mounted on a stable rectangular foot, two pale ceramic horizontal safety bands and a small dark screw panel. No glowing beacon, no detached barrier tape, no extra bollards."),
    ("S-P04", "tool_tray", [46, 24], "A single open shallow maintenance tool tray: rectangular steel tray with pale rim corners, containing one short wrench, one socket handle and a small brass coupling. The tools remain inside the tray footprint and visibly rest on the tray, no floating or scattered tools, no additional toolbox."),
    ("S-P05", "spare_elbow_pipe", [42, 32], "A single spare ninety-degree elbow pipe lying on its small steel mounting cradle: blue-grey cylindrical elbow with visible top-facing curve, a brass coupling at each end, neutral dark pipe openings. Both ends and the elbow form one continuous part. No liquid, no steam, no arrows, no running hoses."),
    ("S-P06", "maintenance_sign", [30, 42], "A single freestanding compact maintenance sign: pale ceramic rectangular sign plate attached to a narrow blue-grey stand with a stable foot. The plate contains ONLY one bold dark wrench silhouette, a purely graphical maintenance symbol. Absolutely no letters, numbers, pseudo-writing, text lines or labels. No illuminated sign."),
]

def main() -> None:
    for name in ("prompts", "generated", "annotations", "finished", "layers", "review", "tools", "godot-logs"):
        (BASE / name).mkdir(parents=True, exist_ok=True)
    reference_records = [{"file": p, "sha256": sha(ROOT / p), "role": "read_only_new_native_style_reference", "visually_inspected": True} for p in REFERENCES]
    assets = []
    for manifest_id, asset_id, target, subject in SPECS:
        prompt = COMMON + f"\nSubject: {subject}\nNative final canvas will be 64x64, subject no larger than {target[0]}x{target[1]} pixels and never larger than 48x48. All sides retain at least 8 native pixels of transparent margin. Ground boundary anchor is (32,56), centered horizontally. Do not paint this coordinate into the image.\n"
        path = BASE / "prompts" / (asset_id + ".txt")
        path.write_text(prompt, encoding="utf-8")
        assets.append({"id": asset_id, "manifest_id": manifest_id, "canvas": [64,64], "native_target": target, "maximum_extent": [48,48], "minimum_margin": 8, "anchor": [32,56], "anchor_convention": "pixel boundary; bottom visible pixel is y=55", "production_file": f"assets/ember/environment/props/{asset_id}_v001.png", "prompt": rel(path), "prompt_sha256": sha(path), "references": reference_records, "status": "BRIEF_READY_WAITING_PRECEDING_SUB_BATCH", "new_art_units": 1, "runtime_emission_baked": False, "new_gameplay_rules": False})
    write_json(BASE / "planned-catalog-v001.json", {"status": "BRIEFS_READY_NOT_GENERATED", "required_assets": 6, "delivered_assets": 0, "scope": "six environment props, no gameplay expansion", "assets": assets, "generation_method": "six distinct built-in image_gen calls after preceding bridge/collect batch", "native_finish_method": "explicit editable annotations/components on the native grid; full-master downsample is never the final acceptance"})
    baseline = BASE / "protected-before.json"
    if not baseline.exists():
        paths = list((ROOT / "assets/ember/buildings").rglob("*")) + list((ROOT / "assets/ember/props").rglob("*"))
        paths += [ROOT / p for p in REFERENCES]
        paths += [ROOT / "project.godot", ROOT / "docs/shader-learning/progress.md"]
        paths = sorted({p for p in paths if p.is_file()}, key=str)
        write_json(baseline, {"protected_files": {rel(p): sha(p) for p in paths}, "scope": "existing structures/story/calibration props, exact four references, project and learner progress; new sibling outputs excluded"})
    print(json.dumps({"status": "BRIEFS_READY", "assets": len(assets), "protected_files": len(json.loads(baseline.read_text(encoding="utf-8"))["protected_files"]), "catalog": rel(BASE / "planned-catalog-v001.json")}, ensure_ascii=False))

if __name__ == "__main__":
    main()
