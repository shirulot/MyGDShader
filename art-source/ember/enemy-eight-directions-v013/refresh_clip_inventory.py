"""Build a complete 160-slot inventory; missing/static directions never count as clips."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
UNITS = ["enemy_patrol", "enemy_tracked_heavy", "enemy_cutter", "enemy_scout_drone"]
DIRECTIONS = ["down", "down_left", "left", "up_left", "up", "up_right", "right", "down_right"]
ACTIONS = {"idle": (4, 4, True), "move": (8, 8, True), "attack": (6, 10, False),
           "hit": (4, 12, False), "death": (8, 10, False)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


baseline = json.loads((ROOT / "approved_down_baseline.json").read_text(encoding="utf-8"))
approved = {(clip["unit"], clip["action"]): clip for clip in baseline["clips"]}
# Each accepted new batch must be explicitly entered with the TA report and fixed package.
# This file does not infer art approval from successful export or matching hashes.
ledger_path = ROOT / "animation_review_ledger.json"
ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {"batches": []}
new_clips = {}
for batch in ledger["batches"]:
    package = ROOT.parent / batch["folder"]
    catalog = json.loads((package / batch["catalog"]).read_text(encoding="utf-8"))
    for clip in catalog["clips"]:
        # A comparison package may include earlier approved actions; only ledger scope is new.
        if batch.get("include_actions") and clip["action"] not in batch["include_actions"]:
            continue
        new_clips[(clip["unit"], clip["action"])] = (batch, package, clip)

slots = []
for unit in UNITS:
    for direction in DIRECTIONS:
        for action, (count, fps, loop) in ACTIONS.items():
            name = f"{action}_{direction}"
            slot = {"unit": unit, "direction": direction, "action": name,
                    "frame_count": count, "fps": fps, "loop": loop, "status": "NOT_MADE"}
            if direction == "down":
                clip = approved[(unit, name)]
                package = ROOT.parent / "enemy-sequences-v012"
                assert sha(package / "output" / unit / f"{name}.png") == clip["atlas_sha256"]
                for index, expected in enumerate(clip["frame_hashes"]):
                    assert sha(package / "output" / unit / name / f"f{index:02}.png") == expected
                slot.update(status="PRESERVED_TA_APPROVED", source="enemy-sequences-v012",
                            atlas_sha256=clip["atlas_sha256"], frame_hashes=clip["frame_hashes"])
            elif (unit, name) in new_clips:
                batch, package, clip = new_clips[(unit, name)]
                assert count == clip["frame_count"] and fps == clip["fps"] and loop == clip["loop"]
                atlas = package / clip["atlas"].removeprefix("res://")
                assert sha(atlas) == clip["atlas_sha256"]
                for index, expected in enumerate(clip["frame_hashes"]):
                    assert sha(atlas.with_suffix("") / f"f{index:02}.png") == expected
                slot.update(status=batch["status"], source=batch["folder"],
                            review_report=batch.get("review_report"),
                            atlas_sha256=clip["atlas_sha256"], frame_hashes=clip["frame_hashes"])
            slots.append(slot)

counts = {key: sum(item["status"] == key for item in slots) for key in sorted({x["status"] for x in slots})}
result = {"target_clips": len(slots), "target_frames": sum(x["frame_count"] for x in slots),
          "counts": counts, "clips": slots}
(ROOT / "clip_inventory_v013.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
# Keep the small status view derived from the same reviewed ledger.
status_path = ROOT / 'STATUS.json'
status = json.loads(status_path.read_text(encoding='utf-8'))
status['new_approved_clips'] = sum(x['status'] == 'TA_APPROVED' for x in slots)
status['new_approved_frames'] = sum(x['frame_count'] for x in slots if x['status'] == 'TA_APPROVED')
status['clip_counts'] = counts
status['frame_counts'] = {key: sum(x['frame_count'] for x in slots if x['status'] == key) for key in counts}
status['approved_by_unit'] = {unit: {'clips': sum(x['status'] in ['TA_APPROVED', 'PRESERVED_TA_APPROVED'] for x in slots if x['unit']==unit), 'frames': sum(x['frame_count'] for x in slots if x['unit']==unit and x['status'] in ['TA_APPROVED', 'PRESERVED_TA_APPROVED'])} for unit in UNITS}
status['last_update_note'] = 'Counts verified from immutable catalogs and explicit TA receipts in animation_review_ledger.json.'
status_path.write_text(json.dumps(status, indent=2), encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != "clips"}))
