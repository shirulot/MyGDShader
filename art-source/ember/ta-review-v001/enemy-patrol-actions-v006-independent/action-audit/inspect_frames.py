"""为人工动作审查制作有帧号的最近邻证据图，并记录独立端点/支撑观察。"""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

review = Path('E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/action-audit')
package = review / 'package'
catalog = json.loads((package / 'output/catalog_v006.json').read_text(encoding='utf-8'))
observations = {'frame_evidence': [], 'muzzle_path': [], 'death_contacts': []}
for action, definition in catalog['actions'].items():
    frames = []
    for index in range(definition['frame_count']):
        path = package / f'output/{action}/f{index:02d}.png'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == definition['frame_hashes'][index]
        frame = Image.open(path).convert('RGBA')
        frames.append(frame)
        observations['frame_evidence'].append({'action': action, 'frame': index, 'path': str(path), 'size': frame.size, 'visible_bounds': frame.getchannel('A').getbbox(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    scale = 3
    cols = 3 if action == 'attack_down' else 4
    cellw, cellh = 128*scale, 128*scale+35
    sheet = Image.new('RGB', (cols*cellw, ((len(frames)+cols-1)//cols)*cellh), (46, 51, 57))
    draw = ImageDraw.Draw(sheet)
    for index, frame in enumerate(frames):
        x, y = (index % cols)*cellw, (index // cols)*cellh
        large = frame.resize((128*scale,128*scale), Image.Resampling.NEAREST)
        sheet.paste(large, (x,y+35), large)
        draw.text((x+8,y+5), f'f{index:02d} {definition["poses"][index]["phase"]}', fill=(245,245,245))
        draw.line((x,y+35+104*scale,x+cellw-1,y+35+104*scale), fill=(91,125,144))
        draw.line((x+64*scale-5,y+35+104*scale,x+64*scale+5,y+35+104*scale), fill=(208,124,109))
    sheet.save(review / f'{action}_full_frames_3x_guide.png')
    for pose in definition['poses']:
        if action == 'attack_down':
            transform = pose['part_transforms']['right_arm_gun']
            p, bx, by = transform['position'], transform['basis_x'], transform['basis_y']
            muzzle = [p[i]-bx[i]+12*by[i] for i in range(2)]
            observations['muzzle_path'].append({'frame': pose['frame'], 'muzzle_px': muzzle, 'visual_gun_axis_px': by, 'events': pose['events']})
        else:
            observations['death_contacts'].append({'frame': pose['frame'], 'support': pose['legs']['right']['support'], 'left_sole': pose['legs']['left']['sole_marker_px'], 'right_sole': pose['legs']['right']['sole_marker_px'], 'shoulder_marker': pose['shoulder_contact_landmark_px'], 'bounds': frames[pose['frame']].getchannel('A').getbbox()})

# 枪口局部按全帧固定坐标裁切；独立事件交叉标记不会写入资产。
crop = (38,68,59,98)
detail = Image.new('RGB',(21*10*3,30*10+35),(235,235,235))
draw = ImageDraw.Draw(detail)
for col,index in enumerate([2,3,4]):
    frame = Image.open(package / f'output/attack_down/f{index:02d}.png').convert('RGBA')
    large = frame.crop(crop).resize((210,300),Image.Resampling.NEAREST)
    detail.paste(large,(col*210,35),large)
    draw.text((col*210+8,8),f'f{index:02d}',fill=(30,30,30))
    if index == 3:
        event = catalog['actions']['attack_down']['poses'][index]['events'][0]
        mx,my = event['muzzle_px']
        x,y = col*210+(mx-crop[0])*10+5,35+(my-crop[1])*10+5
        draw.line((x-8,y,x+8,y), fill=(200,30,30),width=2)
        draw.line((x,y-8,x,y+8), fill=(200,30,30),width=2)
detail.save(review / 'attack_f02_f03_f04_muzzle_detail_10x.png')

# 对视觉代理发现的位置做独立 PNG 放大核对；不以连通数单独判美术。
for action, indices, region in [
    ('attack_down', [1,2,3,4], (72,78,88,98)),
    ('death_down', [4,5,6,7], (48,86,80,108)),
]:
    w,h = region[2]-region[0],region[3]-region[1]
    localized = Image.new('RGB',(w*10*len(indices),h*10+35),(245,245,245))
    drawing = ImageDraw.Draw(localized)
    for col,index in enumerate(indices):
        frame = Image.open(package / f'output/{action}/f{index:02d}.png').convert('RGBA')
        enlarged = frame.crop(region).resize((w*10,h*10),Image.Resampling.NEAREST)
        localized.paste(enlarged,(col*w*10,35),enlarged)
        drawing.text((col*w*10+8,8),f'f{index:02d}',fill=(25,25,25))
    localized.save(review / f'{action}_localized_edges_10x.png')
(review / 'frame-action-observations.json').write_text(json.dumps(observations,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'muzzle_path':observations['muzzle_path'],'death_contacts':observations['death_contacts']},ensure_ascii=False))
