"""汇总实际生图来源、候选登记及可重复的图像诊断，不修补美术像素。"""
from collections import deque
from pathlib import Path
import hashlib
import json
import shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
REVIEW = P / 'review'
REVIEW.mkdir(exist_ok=True)
FONT = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 16)

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(name, data):
    (P / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def local(path):
    return path.relative_to(ROOT).as_posix()

def whole_components(image):
    # Alpha>127仅用于主体诊断；生成图本身保留全部过渡Alpha。
    opaque = np.asarray(image)[:, :, 3] > 127
    seen = np.zeros(opaque.shape, dtype=bool)
    components = []
    h, w = opaque.shape
    for y, x in np.argwhere(opaque):
        if seen[y, x]:
            continue
        seen[y, x] = True
        queue = deque([(int(y), int(x))])
        area, edges = 0, set()
        while queue:
            cy, cx = queue.popleft()
            area += 1
            if cy == 0: edges.add('N')
            if cx == w-1: edges.add('E')
            if cy == h-1: edges.add('S')
            if cx == 0: edges.add('W')
            for dy, dx in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                ny, nx = cy+dy, cx+dx
                if 0 <= ny < h and 0 <= nx < w and opaque[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    queue.append((ny, nx))
        components.append({'pixels': area, 'touched_edges': sorted(edges)})
    return sorted(components, key=lambda c: c['pixels'], reverse=True)

def edge(image, side):
    a = np.asarray(image)
    return {'N': a[0], 'S': a[-1], 'W': a[:, 0], 'E': a[:, -1]}[side]

def seam(a, side_a, b, side_b):
    first, second = edge(a, side_a), edge(b, side_b)
    delta = np.abs(first.astype(int)-second.astype(int))
    visible = (first[:, 3] > 0) | (second[:, 3] > 0)
    return {'rgba_equal': bool(np.array_equal(first, second)),
            'rgba_different_positions': int(np.any(delta > 0, axis=1).sum()),
            'visible_rgba_different_positions': int((np.any(delta > 0, axis=1) & visible).sum()),
            'alpha_different_positions': int((delta[:, 3] > 0).sum()),
            'max_alpha_difference': int(delta[:, 3].max()),
            'rgb_mean_absolute_difference': float(delta[:, :3][visible].mean()) if visible.any() else 0.0}

def main():
    center_record = read(P / 'floor_center_record.json')
    center = read(P / 'floor_center_export.json')
    floor_cat = read(P / 'floor/candidate-catalog.json')
    floor_records = read(P / 'floor/generation-record.json')['records']
    bank_records = read(P / 'bank/generation-record.json')
    bank_prompts = read(P / 'bank/prompts.json')['prompts']
    entries = [{
        'id': 'floor_center', 'family': 'floor', 'mask': 255,
        'source_path': center['source'], 'actual_crop_xyxy': center['actual_crop_xyxy'],
        'candidate_path': center['export'], 'open_sides': ['N', 'E', 'S', 'W'],
        'closed_sides': [], 'corner_semantics': 'All four diagonals filled; no hole or outside perimeter.',
        'status': 'VISUAL_SAMPLE_INTERFACES_NOT_PASSED',
        'issues': ['无真实Alpha孔洞；新旧相邻块板缝与RGB接口仍不同。'],
        'producer_record': 'floor_center_record.json', 'export_record': 'floor_center_export.json'}]
    for e in floor_cat['candidates']:
        entries.append({'id': e['id'], 'family': 'floor', 'mask': e['mask'],
                        'source_path': e['raw_file'], 'actual_crop_xyxy': e['source_crop_xyxy'],
                        'candidate_path': e['candidate_file'], 'open_sides': e['open_sides'],
                        'closed_sides': e['closed_sides'], 'corner_semantics': e['corner'],
                        'status': 'VISUAL_SAMPLE_INTERFACES_NOT_PASSED', 'issues': e['issues'],
                        'producer_record': 'floor/generation-record.json',
                        'export_record': 'floor/candidate-catalog.json'})
    for e in bank_records['candidate_entries']:
        open_sides = {124: ['E', 'S', 'W'], 28: ['E', 'S'], 127: ['N', 'E', 'S', 'W']}[e['mask']]
        entries.append({'id': e['id'], 'family': 'bank', 'mask': e['mask'],
                        'source_path': e['raw_path'], 'actual_crop_xyxy': e['crop'],
                        'candidate_path': e['candidate_path'], 'open_sides': open_sides,
                        'closed_sides': [s for s in ['N', 'E', 'S', 'W'] if s not in open_sides],
                        'corner_semantics': {124: 'North bank; water continues E/S/W.',
                                             28: 'Northwest outer bank; water southeast.',
                                             127: 'Only local NW curved bank, N/W cut ports, E/S water; exact neighboring profiles pending.'}[e['mask']],
                        'status': e['status'], 'issues': [e['reason']],
                        'producer_record': 'bank/generation-record.json',
                        'export_record': 'bank/generation-record.json'})
    order = ['floor_center', 'floor_edge_N', 'floor_outer_NW', 'floor_inner_NW',
             'floor_narrow_NS', 'bank_straight_N', 'bank_outer_NW', 'bank_inner_NW']
    entries.sort(key=lambda e: order.index(e['id']))
    images = {}
    for e in entries:
        source = ROOT / e['source_path']
        candidate = ROOT / e['candidate_path']
        image = Image.open(candidate).convert('RGBA')
        assert image.size == (128, 128)
        images[e['id']] = image
        e.update({'source_sha256': sha(source), 'source_size': list(Image.open(source).size),
                  'candidate_sha256': sha(candidate), 'target_size': [128, 128],
                  'logical_tile_size': 32, 'layer_scale': 0.25,
                  'candidate_components_4_alpha_above_127': whole_components(image),
                  'user_visual_approval': False})
    write('candidate-catalog.json', {'status': 'EIGHT_ART_CANDIDATES_INTERFACES_NOT_PASSED',
                                    'bit_order_8': 'N NE E SE S SW W NW',
                                    'production_ready': False, 'entries': entries})

    # 将12个实际原稿保留到统一raw入口；不删除代理记录的原文件。
    generations = [{'id': 'floor_center_v001', 'source': center['source'],
                    'prompt': center_record['prompt'], 'references': center_record['referenced_image_paths'],
                    'original_tool_output': center_record['output_hint'],
                    'adoption': 'VISUAL_SAMPLE_INTERFACES_NOT_PASSED'}]
    for r in floor_records:
        generations.append({'id': r['id']+'_'+r['version'], 'source': r['raw_file'],
                            'prompt': r['prompt'], 'references': r['references'],
                            'original_tool_output': r['original_tool_output_hint'],
                            'adoption': r['adoption'], 'notes': r['notes']})
    for r in bank_prompts:
        adoption = bank_records['rejected_originals'].get(r['id'], 'VISUAL_SAMPLE_INTERFACES_NOT_PASSED')
        generations.append({'id': r['id'], 'source': r['local_saved_file'], 'prompt': r['prompt'],
                            'references': r['referenced_image_paths'],
                            'original_tool_output': r['output_hint'], 'adoption': adoption})
    for g in generations:
        source = ROOT / g['source']
        canonical = P / 'raw' / (g['id']+'.png')
        if canonical != source:
            shutil.copy2(source, canonical)
        g.update({'raw': local(canonical), 'sha256': sha(canonical),
                  'actual_size': list(Image.open(canonical).size), 'tool': 'image_gen.imagegen',
                  'reference_sha256': {r: sha(ROOT/r) for r in g['references']}})
    # 后续定向修正也逐次留档，数量从实际生成记录计算。
    assert len(generations) == 1 + len(floor_records) + len(bank_prompts)
    write('prompts.json', {'tool': 'image_gen.imagegen', 'prompts': [
        {'id': g['id'], 'prompt': g['prompt'], 'references': g['references']} for g in generations]})
    write('generation-record.json', {'date': '2026-10-05', 'raw_generation_count': len(generations),
                                    'sample_types': 8, 'production_ready': False,
                                    'records': generations,
                                    'adoption_meaning': 'Candidate or rejected art; no interface/user approval inferred.'})

    tests = [('floor_center', 'E', 'floor_center', 'W'),
             ('floor_center', 'S', 'floor_center', 'N'),
             ('floor_edge_N', 'E', 'floor_edge_N', 'W'),
             ('floor_edge_N', 'S', 'floor_center', 'N'),
             ('floor_outer_NW', 'E', 'floor_edge_N', 'W'),
             ('floor_inner_NW', 'E', 'floor_center', 'W'),
             ('floor_inner_NW', 'S', 'floor_center', 'N'),
             ('floor_narrow_NS', 'S', 'floor_narrow_NS', 'N'),
             ('bank_straight_N', 'E', 'bank_straight_N', 'W'),
             ('bank_outer_NW', 'E', 'bank_straight_N', 'W')]
    observations = [{'a': a, 'a_edge': sa, 'b': b, 'b_edge': sb,
                     **seam(images[a], sa, images[b], sb)} for a, sa, b, sb in tests]
    write('interface-observations.json', {'measurements': observations,
                                         'artwork_pixels_modified': False,
                                         'scope': 'Measured sample pairings only. Not a complete47 visual acceptance.'})

    names = ['中心', '北外边', '西北外角', '西北凹角', '南北窄条', '北池岸', '池岸外角', '池岸凹角候选']
    board = Image.new('RGB', (1184, 476), '#182631')
    draw = ImageDraw.Draw(board)
    draw.text((16, 12), '首批8类：v007 / v008同尺度128px对比；源图诊断，非引擎截图', font=FONT, fill='white')
    for i, (e, name) in enumerate(zip(entries, names)):
        x, y = 16+(i % 4)*292, 52+(i//4)*206
        draw.text((x, y), name+'  mask '+str(e['mask']), font=FONT, fill='#edbd79')
        for j, (label, image) in enumerate([
            ('v007', Image.open(P / f'inputs/v007_{e["family"]}_mask{e["mask"]}.png').convert('RGBA')),
            ('v008', images[e['id']])]):
            px = x+j*136
            draw.rectangle((px, y+28, px+127, y+155), fill='#203a4b' if e['family'] == 'bank' else '#31424c')
            board.paste(image, (px, y+28), image)
            draw.text((px, y+162), label, font=FONT, fill='white')
    draw.text((16, 458), '保留生成Alpha和材质；接口未通过，尚未发布正式47套。', font=FONT, fill='#ffb4a1')
    board.save(REVIEW / 'eight_samples_before_after.png')
    print(json.dumps({'raw': len(generations), 'entries': len(entries),
                      'seams_equal': sum(o['rgba_equal'] for o in observations),
                      'seams_measured': len(observations)}))

if __name__ == '__main__':
    main()
