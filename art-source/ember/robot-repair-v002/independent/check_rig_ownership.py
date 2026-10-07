"""Independent rig-pixel ownership and preserved-joint-motion checks.

Read JSON and PNG directly. Never import or call the producer's pose builder.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
REPAIR = OUT.parent
OLD = ROOT / 'art-source/ember/batch-02-robot/annotations'
COLOURS = {'head': [190, 190, 215, 255], 'torso': [120, 190, 235, 255],
           'left_arm': [235, 175, 85, 255], 'right_arm': [190, 120, 215, 255],
           'left_leg': [245, 155, 130, 255], 'right_leg': [125, 220, 145, 255]}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def owners(rig):
    result = {}
    duplicate = []
    for part in rig['parts']:
        for xy in part['pixels']:
            xy = tuple(xy)
            if xy in result: duplicate.append(xy)
            result[xy] = part['name']
    return result, duplicate


def coloured(owner):
    a = np.zeros((96, 64, 4), dtype=np.uint8)
    for (x, y), name in owner.items():
        a[y, x] = COLOURS[name]
    return Image.fromarray(a, 'RGBA')


def part_components(owner, name):
    """按原生像素检查每个部件；不借用制作器的连通性结论。"""
    pending = {xy for xy, part in owner.items() if part == name}
    count = 0
    while pending:
        count += 1
        todo = [pending.pop()]
        while todo:
            x, y = todo.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    point = (x + dx, y + dy)
                    if point in pending:
                        pending.remove(point)
                        todo.append(point)
    return count


def main():
    issue_path = ROOT / 'art-source/ember/quality-audit-2026-10-04/robot/robot-quality-review.json'
    prior = json.loads(issue_path.read_text(encoding='utf-8'))
    boot_issue = next(i for i in prior['issues'] if i['id'] == 'ROBOT_LEFT_02_DETACHED')
    boot = {tuple(p['idle_xy']) for p in boot_issue['rig_trace']}
    down_pelvis = {(30, 62), (31, 62), (32, 62)}
    # 主审接手最终候选后补充核验：这11个前臂/腕部像素应随左臂移动。
    # 显式列出坐标，并验证整个部件连通，避免直接采信制作记录的变化列表。
    down_wrist = {(42, 49), (43, 49), (43, 50), (43, 51), (43, 52),
                  (43, 53), (43, 54), (43, 55), (43, 56), (43, 61), (43, 62)}
    checks = []; source_sha = {issue_path.relative_to(ROOT).as_posix(): sha(issue_path)}
    maps = {}
    for direction in ['down', 'left', 'right', 'up']:
        old_path = OLD / f'rig_{direction}_v001.json'
        new_path = REPAIR / 'annotations' / f'rig_{direction}_v002.json'
        old_rig = json.loads(old_path.read_text(encoding='utf-8'))
        new_rig = json.loads(new_path.read_text(encoding='utf-8'))
        old_map, _ = owners(old_rig); new_map, duplicate = owners(new_rig)
        idle_path = ROOT / new_rig['idle_source']
        idle = Image.open(idle_path).convert('RGBA'); a = np.asarray(idle)
        visible = {(int(x), int(y)) for y, x in zip(*np.nonzero(a[:, :, 3] == 255))}
        ownership_changes = [{'xy': list(xy), 'old': old_map[xy], 'new': new_map[xy]} for xy in sorted(old_map) if old_map[xy] != new_map[xy]]
        expected = boot if direction == 'left' else down_pelvis | down_wrist if direction == 'down' else set()
        checks.append({'id': direction + '_rig_exact_unique_opaque_coverage', 'pass': not duplicate and set(new_map) == visible,
                       'duplicates': duplicate, 'opaque_pixels': len(visible), 'owned_pixels': len(new_map)})
        checks.append({'id': direction + '_only_diagnosed_ownership_changes', 'pass': {tuple(p['xy']) for p in ownership_changes} == expected,
                       'changes': ownership_changes})
        if direction == 'left':
            same_near = all(new_map[p] == 'left_leg' for p in boot)
            checks.append({'id': 'all14_near_boot_pixels_share_near_leg_owner', 'pass': len(boot) == 14 and same_near and new_map[(34, 76)] == 'left_leg',
                           'boot_pixels': [list(p) for p in sorted(boot)], 'reference_inside_near_boot': [34, 76], 'reference_owner': new_map[(34, 76)]})
        if direction == 'down':
            checks.append({'id': 'all3_central_pelvis_pixels_follow_torso', 'pass': all(new_map[p] == 'torso' for p in down_pelvis)})
            checks.append({'id': 'all11_forearm_wrist_pixels_follow_left_arm', 'pass': all(new_map[p] == 'left_arm' for p in down_wrist),
                           'reviewed_pixels': [list(p) for p in sorted(down_wrist)]})
        counts = {name: part_components(new_map, name) for name in COLOURS}
        checks.append({'id': direction + '_all6_semantic_parts_connected', 'pass': all(n == 1 for n in counts.values()),
                       'new_components8': counts, 'old_components8': {name: part_components(old_map, name) for name in COLOURS}})
        colour_tool_owner_changes = []
        bronze = {(123, 77, 53), (183, 124, 75), (226, 183, 122)}
        for xy in visible:
            x, y = xy
            if tuple(a[y, x, :3]) in bronze and old_map[xy] != new_map[xy]: colour_tool_owner_changes.append(xy)
        checks.append({'id': direction + '_bronze_tool_original_part_owner_unchanged', 'pass': not colour_tool_owner_changes})
        for path in [old_path, new_path, idle_path]: source_sha[path.relative_to(ROOT).as_posix()] = sha(path)
        maps[direction] = (old_map, new_map)
        for frame in range(4):
            old_pose_path = OLD / f'walk_{direction}_f{frame:02d}.json'
            new_pose_path = REPAIR / 'annotations' / f'walk_{direction}_f{frame:02d}.json'
            old_pose = json.loads(old_pose_path.read_text(encoding='utf-8'))
            new_pose = json.loads(new_pose_path.read_text(encoding='utf-8'))
            checks.append({'id': f'{direction}_{frame:02d}_integer_part_motion_and_draw_order_preserved',
                           'pass': old_pose['offsets'] == new_pose['offsets'] and old_pose['draw_order'] == new_pose['draw_order']})
            checks.append({'id': f'{direction}_{frame:02d}_fixed_virtual_anchor_and_phase',
                           'pass': new_pose['gait']['virtual_ground_anchor'] == [32, 80] and
                           all(new_pose['gait'][k] == old_pose['gait'][k] for k in ['support_leg', 'lifted_leg', 'phase'])})
            for path in [old_pose_path, new_pose_path]: source_sha[path.relative_to(ROOT).as_posix()] = sha(path)
    # Native source boot colours expose the old incorrect cut and corrected ownership.
    old_map, new_map = maps['left']
    board = Image.new('RGB', (720, 440), '#171d24'); draw = ImageDraw.Draw(board)
    for i, mapping in enumerate([old_map, new_map]):
        crop = coloured(mapping).crop((22, 54, 44, 82)).resize((264, 336), Image.Resampling.NEAREST)
        bg = Image.new('RGBA', crop.size, '#333c45'); bg.alpha_composite(crop)
        draw.text((12 + i * 350, 9), 'old rig' if i == 0 else 'new rig / same near boot owner', fill='white')
        board.paste(bg.convert('RGB'), (12 + i * 350, 35))
    draw.text((12, 385), 'pink=near left_leg; green=far right_leg. Native crop starts x22,y54, scale12.', fill='white')
    visual = OUT / 'left-boot-native-ownership-before-after-12x.png'; board.save(visual)
    report = {'status': 'PASS' if all(c['pass'] for c in checks) else 'FAIL',
              'reviewer_note': 'Standalone checker authored by other_art_break_audit; root extended explicit down wrist coordinates and semantic-part connectivity for the final candidate after delegated reviewer hit usage limits.',
              'checks': checks, 'failed_checks': [c for c in checks if not c['pass']],
              'source_sha256': source_sha, 'ownership_visual': visual.relative_to(ROOT).as_posix(), 'ownership_visual_sha256': sha(visual)}
    (OUT / 'independent-rig-ownership.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'checks': len(checks), 'failed_checks': report['failed_checks']}, ensure_ascii=False))
    raise SystemExit(bool(report['failed_checks']))


if __name__ == '__main__':
    main()
