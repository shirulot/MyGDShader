"""绘制独立骨架示意图；不重画、变形或修补任何角色源像素。"""
from pathlib import Path
from PIL import Image, ImageDraw
import json

ROOT = Path(__file__).resolve().parent

def make(key, action, facing):
    count = 4 if action == 'idle' else 8
    columns = 2 if count == 4 else 4
    cell_w, cell_h = (128 if count == 4 else 96), 128
    root_x = cell_w // 2
    board = Image.new('RGB', (cell_w * columns * 4, 1024), '#182631')
    draw = ImageDraw.Draw(board)
    records = []
    # 两次换步连续地跨越最后一帧；足部坐标是相对角色的轨迹，不是世界锁脚。
    foot = [(7, 109), (3, 109), (-2, 107), (-6, 103),
            (-7, 101), (-3, 101), (2, 104), (6, 107)]
    if action == 'run':
        foot = [(10, 109), (4, 109), (-5, 105), (-10, 97),
                (-8, 94), (-1, 97), (7, 103), (11, 106)]
    for frame in range(count):
        bob = [0, 1, 0, -1][frame % 4] if action != 'idle' else [0, -1, -1, 0][frame]
        if action == 'run': bob *= 2
        x, y = root_x, 83 + bob
        pts = {'root': (x, 108), 'head': (x + facing, 51 + bob),
               'neck': (x, 61 + bob), 'chest': (x, 69 + bob),
               'pelvis': (x, y), 'near_shoulder': (x - 7, 65 + bob),
               'far_shoulder': (x + 6, 64 + bob),
               'near_hip': (x - 4, y + 1), 'far_hip': (x + 4, y - 1)}
        for side, shift, phase in [('near', -4, frame), ('far', 4, (frame + 4) % 8)]:
            fx, fy = foot[phase] if action != 'idle' else (0, 109 if side == 'near' else 106)
            ankle = (x + shift + fx * facing, fy - (2 if side == 'far' else 0))
            # 膝盖沿朝向前侧弯曲；只画姿态草案，投影长度须另做视觉核验。
            knee = (round((x + shift + ankle[0]) / 2) + facing * (3 if phase in [3, 4, 5] and action != 'idle' else 1),
                    round((y + ankle[1]) / 2) - (1 if side == 'far' else 0))
            pts[f'{side}_knee'], pts[f'{side}_ankle'] = knee, ankle
            pts[f'{side}_toe'] = (ankle[0] + facing * 5, ankle[1] + 2)
            swing = -fx * facing if action != 'idle' else 0
            sx, sy = pts[f'{side}_shoulder']
            pts[f'{side}_elbow'] = (sx + round(swing * .5), sy + 11)
            pts[f'{side}_wrist'] = (sx + swing, sy + (15 if action == 'run' else 21))
        origin = ((frame % columns) * cell_w * 4, (frame // columns) * cell_h * 4)
        def screen(name):
            a, b = pts[name]
            return (origin[0] + a * 4, origin[1] + b * 4)
        draw.rectangle((origin[0], origin[1], origin[0] + cell_w * 4 - 1, origin[1] + 511), outline='#4d6470')
        draw.line((origin[0], origin[1] + 432, origin[0] + cell_w * 4, origin[1] + 432), fill='#4d6470')
        for names in [('pelvis', 'chest', 'neck', 'head')]:
            draw.line([screen(n) for n in names], fill='#BECBC4', width=12)
        for side, color in [('far', '#829BA3'), ('near', '#E2B77A')]:
            for chain in [('chest', f'{side}_shoulder', f'{side}_elbow', f'{side}_wrist'),
                          ('pelvis', f'{side}_hip', f'{side}_knee', f'{side}_ankle', f'{side}_toe')]:
                draw.line([screen(n) for n in chain], fill=color, width=10)
                for name in chain[1:]:
                    a, b = screen(name)
                    draw.ellipse((a-7, b-7, a+7, b+7), fill=color)
        hx, hy = screen('head')
        draw.ellipse((hx-28, hy-32, hx+28, hy+28), outline='#ECE9D8', width=5)
        rx, ry = screen('root')
        draw.line((rx-12, ry, rx+12, ry), fill='#51C5C2', width=3)
        draw.text((origin[0]+12, origin[1]+12), f'F{frame:02}  {action}  fixed view', fill='white')
        records.append({'frame': frame, 'points': pts, 'phase': frame / count,
                        'support': 'both' if action == 'idle' else ('near' if frame < 4 else 'far'),
                        'note': 'Draft guide, not measured source skeleton; support labels need per-frame refinement.'})
    board.save(ROOT / 'poses' / f'{key}.png')
    (ROOT / 'poses' / f'{key}.json').write_text(json.dumps({
        'key': key, 'cell': [cell_w, cell_h], 'scale': 4, 'root': [root_x, 108],
        'columns': columns, 'frames': records, 'status': 'draft_not_approved',
        'final_crop': [root_x-32, 28, root_x+32, 124]}, indent=2))

make('A-idle-down_right', 'idle', 1)
make('A-walk-down_right', 'walk', 1)
make('C-run-down_left', 'run', -1)
