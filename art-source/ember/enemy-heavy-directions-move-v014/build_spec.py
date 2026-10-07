"""Register six reviewed heavy direction masters; approved two movement clips are copied."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent
EMBER = ROOT.parent
MASTER = EMBER / "enemy-eight-directions-v013"
UNIT = "enemy_tracked_heavy"
DIRS = ["down", "down_left", "left", "up_left", "up", "up_right", "right", "down_right"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rectangle(x, y, width, height):
    return [[x, y], [x + width, y], [x + width, y + height], [x, y + height]]


def window(x, y, width, period=16, shear=0, sign=1, horizontal=False, thickness=2):
    return dict(origin=[x, y], cross_width=width, period=period, shear=shear,
                sign=sign, horizontal=horizontal, thickness=thickness)


# These are source-region ownership boundaries, not mirrored or redrawn sprites.
right_tracks = [
    [[84, 0], [128, 0], [128, 128], [70, 128], [70, 86], [73, 76], [77, 68], [81, 63], [84, 60]],
    [[0, 0], [43, 0], [43, 60], [46, 60], [46, 65], [47, 73], [46, 79], [47, 82], [47, 128], [0, 128]],
]
left_tracks = [
    [[0, 0], [45, 0], [45, 60], [49, 67], [53, 73], [57, 82], [57, 128], [0, 128]],
    [[81, 0], [128, 0], [128, 128], [82, 128], [82, 82], [85, 72], [82, 64], [81, 64]],
]
side_west = [
    [[34, 128], [128, 128], [128, 83], [92, 83], [90, 70], [87, 68], [57, 68], [50, 70], [44, 72], [39, 77], [34, 82]],
    [[79, 60], [82, 60], [87, 64], [87, 68], [79, 68]],
]
side_east = [[[123 - x, y] for x, y in polygon] for polygon in side_west]
configs = {
    "down_left": dict(track_polygons=right_tracks, windows=[window(75, 83, 12, shear=.25), window(25, 73, 13, shear=.15)], supports=[[81, 104], [31, 93]]),
    "left": dict(track_polygons=side_west, windows=[window(48, 85, 0, sign=-1, horizontal=True), window(64, 85, 0, sign=-1, horizontal=True), window(48, 101, 0, sign=1, horizontal=True), window(64, 101, 0, sign=1, horizontal=True)], supports=[[43, 104], [85, 104]]),
    "up_left": dict(track_polygons=left_tracks, windows=[window(41, 83, 12, shear=.25, sign=-1), window(90, 72, 11, shear=-.15, sign=-1)], supports=[[44, 104], [97, 93]]),
    "up": dict(track_polygons=[rectangle(0, 0, 49, 128), rectangle(80, 0, 48, 128)], windows=[window(31, 85, 11, sign=-1), window(85, 85, 14, sign=-1)], supports=[[36, 104], [92, 104]]),
    "up_right": dict(track_polygons=right_tracks, windows=[window(75, 83, 12, shear=.25, sign=-1), window(25, 73, 13, shear=.15, sign=-1)], supports=[[81, 104], [31, 93]]),
    "right": dict(track_polygons=side_east, windows=[window(43, 85, 0, sign=1, horizontal=True), window(59, 85, 0, sign=1, horizontal=True), window(43, 101, 0, sign=-1, horizontal=True), window(59, 101, 0, sign=-1, horizontal=True)], supports=[[38, 104], [80, 104]]),
}
for name in ["source", "output", "qa", "previews", f"output/{UNIT}", f"reference/{UNIT}"]:
    (ROOT / name).mkdir(parents=True, exist_ok=True)
for direction in DIRS:
    source = MASTER / f"output/{UNIT}/neutral_{direction}.png"
    shutil.copy2(source, ROOT / f"source/{direction}.png")
    shutil.copy2(source, ROOT / f"output/{UNIT}/neutral_{direction}.png")
    if direction in configs:
        configs[direction].update(source=f"res://source/{direction}.png", source_sha256=sha(source))

preserved = []
for direction, folder in [("down", "enemy-sequences-v012"), ("down_right", "enemy-eight-directions-v013-pilot-hc-v001")]:
    action = "move_" + direction
    source_folder = EMBER / folder / "output" / UNIT
    shutil.copytree(source_folder / action, ROOT / "output" / UNIT / action, dirs_exist_ok=True)
    shutil.copy2(source_folder / (action + ".png"), ROOT / "output" / UNIT / (action + ".png"))
    preserved.append(dict(action=action, source=folder, atlas_sha256=sha(source_folder / (action + ".png")),
                          frame_hashes=[sha(source_folder / action / f"f{i:02}.png") for i in range(8)]))
shutil.copy2(ROOT / f"output/{UNIT}/move_down.png", ROOT / f"reference/{UNIT}/move_down.png")
shutil.copy2(ROOT / "source/down.png", ROOT / f"reference/{UNIT}/neutral_down.png")
for filename in ["masked_part.gdshader", "entity_cutout.gdshader"]:
    shutil.copy2(MASTER / filename, ROOT / filename)
spec = dict(version="v014-heavy-six-new-moves", unit=UNIT, canvas=[128, 128], root=[64, 104],
            directions=DIRS, frame_count=8, fps=8, loop=True, body_y=[0, 0, 1, 0, 0, 0, 1, 0],
            method="Fixed reviewed direction textures and ownership masks; cyclic source sampling confined to tread windows. No directional image mirroring or new per-frame artwork.",
            configs=configs, preserved=preserved)
(ROOT / "rig.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
print("HEAVY_MOVE_SPEC_READY: six new directions and two byte-preserved clips")
