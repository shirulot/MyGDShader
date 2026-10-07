"""汇总真实生图与机械切片，生成对照和GPU输入；不绘制或修补美术像素。"""
from collections import deque
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parent
ROOT = P.parents[3]
PREVIOUS = P.parent
TOOL_ROOT = Path('C:/Users/shiru/.codex/generated_images/01a10204-0a39-77b3-b144-9e7a03fd8e93')
FONT = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 16)


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local(path):
    return path.relative_to(ROOT).as_posix()


def intervals(values):
    """测量实际半开区间；阈值只用于诊断，不改变图像Alpha。"""
    indices = np.flatnonzero(values > 127)
    if not len(indices):
        return []
    groups = np.split(indices, np.flatnonzero(np.diff(indices) > 1) + 1)
    return [[int(group[0]), int(group[-1] + 1)] for group in groups]


def measure(image):
    rgba = np.asarray(image.convert('RGBA'))
    alpha = rgba[:, :, 3]
    edges = {'N': alpha[0], 'E': alpha[:, -1], 'S': alpha[-1], 'W': alpha[:, 0]}
    # 真实主体必须内部连通，不能以最外一排接边像素替代完整结构。
    seen = np.zeros(alpha.shape, dtype=bool)
    components = []
    for y, x in zip(*np.where(alpha > 127)):
        if seen[y, x]:
            continue
        queue = deque([(int(x), int(y))])
        seen[y, x] = True
        count = 0
        while queue:
            cx, cy = queue.popleft()
            count += 1
            for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                if 0 <= nx < alpha.shape[1] and 0 <= ny < alpha.shape[0] and not seen[ny, nx] and alpha[ny, nx] > 127:
                    seen[ny, nx] = True
                    queue.append((nx, ny))
        components.append(count)
    rgb = rgba[:, :, :3].astype(float)
    # 对规则四板候选定位最暗的主横缝/竖缝，保留观测值而非假定x/y64。
    luminance = rgb.mean(axis=2)
    return {
        'size': list(image.size),
        'alpha_range': [int(alpha.min()), int(alpha.max())],
        'body_edge_intersections_alpha_gt127': {side: intervals(edge) for side, edge in edges.items()},
        'components4_alpha_gt127': sorted(components, reverse=True),
        'darkest_cross_joint_row_in_48_80': int(np.argmin(luminance[48:81, 16:112].mean(axis=1)) + 48),
        'darkest_cross_joint_column_in_48_80': int(np.argmin(luminance[16:112, 48:81].mean(axis=0)) + 48),
        'joint_detection_scope': 'Heuristic observation for the four-panel floor only; not a visual pass.'
    }


def seam(a, side_a, b, side_b):
    arrays = [np.asarray(im.convert('RGBA')).astype(int) for im in (a, b)]
    def edge(array, side):
        return {'N': array[0], 'E': array[:, -1], 'S': array[-1], 'W': array[:, 0]}[side]
    left, right = edge(arrays[0], side_a), edge(arrays[1], side_b)
    visible = (left[:, 3] > 0) | (right[:, 3] > 0)
    diff = np.abs(left - right)
    return {'rgba_different_positions': int(np.any(diff > 0, axis=1).sum()),
            'alpha_different_positions': int((diff[:, 3] > 0).sum()),
            'max_alpha_difference': int(diff[:, 3].max()),
            'max_visible_rgb_difference': int(diff[visible, :3].max()) if visible.any() else 0,
            'rgb_mean_absolute_difference': float(diff[visible, :3].mean()) if visible.any() else 0.0,
            'numeric_equality_is_not_visual_acceptance': True}


def board(size, title):
    image = Image.new('RGBA', size, '#182631')
    ImageDraw.Draw(image).text((16, 10), title, font=FONT, fill='white')
    return image


def paste(image, tile, x, y):
    image.alpha_composite(tile, (x, y))


def main():
    for folder in ('review', 'godot-review/inputs'):
        (P / folder).mkdir(parents=True, exist_ok=True)
    root_sources = [
        ('floor_center_pixel_v001', 255, 'exec-1eb8568d-aac3-4314-acd4-8a750b742b21.png', False, ['art-source/ember/production-v008/raw/floor_center_v001.png']),
        ('floor_edge_N_pixel_v001', 124, 'exec-f789967f-cbeb-4b57-a121-114ead738fa6.png', False, [local(P / 'raw/floor_center_pixel_v001.png')]),
        ('floor_narrow_NS_pixel_v001', 17, 'exec-18032380-a9a5-48b6-9231-ccd3eede98db.png', True, [local(P / 'raw/floor_center_pixel_v001.png'), 'art-source/ember/production-v008/floor/raw/floor_narrow_NS_v002.png']),
        ('floor_edge_N_pixel_v002', 124, 'exec-0f42edbe-f91c-431a-a1df-212e299ce1fe.png', False, [local(P / 'raw/floor_edge_N_pixel_v001.png'), local(P / 'raw/floor_center_pixel_v001.png')]),
        ('floor_outer_NW_pixel_v001', 28, 'exec-b5f17c47-3e9a-4f48-b37e-d0f706d30cb9.png', True, [local(P / 'raw/floor_edge_N_pixel_v002.png'), local(P / 'raw/floor_center_pixel_v001.png')]),
        ('floor_outer_NW_pixel_v002', 28, 'exec-1dfc7662-60b5-4235-8e2b-2d9c79c61ed4.png', True, [local(P / 'raw/floor_outer_NW_pixel_v001.png'), local(P / 'raw/floor_center_pixel_v001.png'), local(P / 'raw/floor_edge_N_pixel_v002.png')]),
    ]
    records = []
    for identifier, mask, original_name, transparent, refs in root_sources:
        raw_path = P / 'raw' / (identifier + '.png')
        original = TOOL_ROOT / original_name
        assert sha(original) == sha(raw_path), 'Original raw copy must remain unchanged.'
        image = Image.open(raw_path)
        assert image.width == image.height
        # 每个完整构件独立等比导出，绝不缩放整个atlas后再切片。
        output = P / 'candidates' / (identifier + '.png')
        image.convert('RGBA').resize((128, 128), Image.Resampling.NEAREST).save(output)
        prompt = P / (identifier + '.prompt.txt')
        records.append({'id': identifier, 'mask': mask, 'tool': 'image_gen.imagegen built-in',
                        'original_tool_path': original.as_posix(), 'raw_path': local(raw_path),
                        'raw_sha256': sha(raw_path), 'actual_raw_size': list(image.size),
                        'crop_xyxy': [0, 0, image.width, image.height], 'resampling': 'NEAREST',
                        'candidate_path': local(output), 'candidate_sha256': sha(output),
                        'transparent_background_requested': transparent,
                        'prompt_file': local(prompt), 'prompt_sha256': sha(prompt),
                        'prompt': prompt.read_text(encoding='utf-8'),
                        'references': [{'path': ref, 'sha256': sha(ROOT / ref)} for ref in refs],
                        'measurement': measure(Image.open(output))})
    bank_catalog = read(P / 'bank/candidate-catalog.json')
    bank_prompts = read(P / 'bank/prompts.json')
    write(P / 'generation-record.json', {'actual_builtin_call_count': len(records) + bank_prompts['built_in_call_count'],
          'root_records': records, 'bank_generation_record': local(P / 'bank/generation-record.json'),
          'bank_registered_candidates': bank_catalog['entries'], 'production_ready': False})
    write(P / 'prompts.json', {'prompts': [{'id': row['id'], 'prompt': row['prompt'], 'references': row['references']} for row in records]
          + bank_prompts['prompts'], 'tool': 'image_gen.imagegen built-in'})

    old_catalog = read(PREVIOUS / 'candidate-catalog.json')
    old = {row['id']: Image.open(ROOT / row['candidate_path']).convert('RGBA') for row in old_catalog['entries']}
    bank_by_id = {row['id']: row for row in bank_catalog['entries']}
    registered_id = 'bank_straight_N_pixel_registered_v002'
    bank_straight = bank_by_id.get(registered_id, bank_by_id['bank_straight_N_pixel_v001'])
    bank_inner = bank_by_id['bank_inner_NW_pixel_v001']
    selected = [
        ('floor_center', '地板中心', P / 'candidates/floor_center_pixel_v001.png', 'PIXEL_STYLE_CANDIDATE_REPEAT_PENDING'),
        ('floor_edge_N', '北直边', P / 'candidates/floor_edge_N_pixel_v002.png', 'CANDIDATE_SHARED_SEAM_PHASE_PENDING'),
        ('floor_narrow_NS', '南北窄条', P / 'candidates/floor_narrow_NS_pixel_v001.png', 'PORT_GEOMETRY_PASS_MATERIAL_PENDING'),
        ('floor_outer_NW', '西北外角', P / 'candidates/floor_outer_NW_pixel_v002.png', 'FOUR_PLATES_RESTORED_JOINT_PHASE_NOT_PASSED'),
        ('bank_straight_N', '北直岸', ROOT / bank_straight['candidate_path'], bank_straight['status']),
        ('bank_inner_NW', '岸凹角：拒收', ROOT / bank_inner['candidate_path'], bank_inner['status']),
    ]
    samples, entries = [], []
    # 视觉判定是人工/独立复核的快照。只在来源SHA完全相同时沿用，
    # 防止复现整理覆盖已审状态，或把旧审核套到新生成图片上。
    prior_review_path = P / 'review-results.json'
    prior_decisions = {row['id']: row for row in read(prior_review_path)['results']} if prior_review_path.exists() else {}
    for i, (identifier, name, path, status) in enumerate(selected):
        image = Image.open(path).convert('RGBA')
        samples.append(image)
        connection_sides = {'floor_center': ['N', 'E', 'S', 'W'], 'floor_edge_N': ['E', 'S', 'W'],
                            'floor_narrow_NS': ['N', 'S'], 'floor_outer_NW': ['E', 'S'],
                            'bank_straight_N': ['E', 'W'], 'bank_inner_NW': ['N', 'W']}
        entries.append({'id': identifier, 'name': name, 'atlas_coord': [i, 0], 'source_path': local(path),
                        'intended_connection_sides': connection_sides[identifier],
                        'source_sha256': sha(path), 'status': status, 'measurement': measure(image),
                        'production_ready': False, 'user_visual_approval': False})
        decision = prior_decisions.get(identifier)
        if decision and decision['source_sha256'] == sha(path):
            entries[-1]['status'] = decision['status']
            entries[-1]['review_reason'] = decision['reason']
    baseline = read(PREVIOUS / 'official/catalog.json')['atlases'][0]
    baseline_image = Image.open(PREVIOUS / 'official' / baseline['texture']).convert('RGBA')
    def old_floor(mask):
        row = next(row for row in baseline['tiles'] if row['mask'] == mask)
        x, y = row['coord']
        return baseline_image.crop((x * 128, y * 128, (x + 1) * 128, (y + 1) * 128)), row
    # 旧端头用于验证几何；图集记录来源，绝不计入新版形态数量。
    for identifier, mask in [('old_floor_cap_N', 16), ('old_floor_cap_S', 1)]:
        image, row = old_floor(mask)
        entries.append({'id': identifier, 'atlas_coord': [len(samples), 0], 'source_kind': 'V007_DIAGNOSTIC_ONLY',
                        'mask': mask, 'source': row['source'], 'measurement': measure(image)})
        samples.append(image)
    # “修前46px”是v008窄条，不能误用v007的126px直条。
    previous_narrow_path = ROOT / next(row['candidate_path'] for row in old_catalog['entries'] if row['id'] == 'floor_narrow_NS')
    previous_narrow = old['floor_narrow_NS']
    entries.append({'id': 'old_floor_narrow_NS', 'atlas_coord': [len(samples), 0],
                    'source_path': local(previous_narrow_path), 'source_sha256': sha(previous_narrow_path),
                    'source_kind': 'V008_PRE_CORRECTION_46PX_DIAGNOSTIC', 'measurement': measure(previous_narrow)})
    samples.append(previous_narrow)
    water_path = PREVIOUS / 'godot-review/inputs/water_v007_diagnostic.png'
    for identifier, image, path in [('water_reference', Image.open(water_path).convert('RGBA'), water_path),
                                    ('old_bank_straight_N', old['bank_straight_N'], ROOT / next(row['candidate_path'] for row in old_catalog['entries'] if row['id'] == 'bank_straight_N'))]:
        entries.append({'id': identifier, 'atlas_coord': [len(samples), 0], 'source_path': local(path), 'source_sha256': sha(path), 'source_kind': 'DIAGNOSTIC_REFERENCE'})
        samples.append(image)
    atlas = Image.new('RGBA', (len(samples) * 128, 128))
    for i, image in enumerate(samples):
        # 无mask粘贴完整RGBA，避免把半透明Alpha乘第二次。
        atlas.paste(image, (i * 128, 0))
        assert np.array_equal(np.asarray(image), np.asarray(atlas.crop((i * 128, 0, (i + 1) * 128, 128))))
    atlas_path = P / 'godot-review/inputs/pilot_samples.png'
    atlas.save(atlas_path)
    write(P / 'candidate-catalog.json', {'status': 'PIXEL_STYLE_PILOT_NOT_FULL_TILESET', 'production_ready': False,
          'new_diagnostic_samples': 6, 'production_accepted_samples': 0,
          'review_results': 'review-results.json' if prior_review_path.exists() else None,
          'rejected_art_included_for_diagnosis': True, 'entries': entries,
          'atlas_path': local(atlas_path), 'atlas_sha256': sha(atlas_path), 'texture_tile_size': 128,
          'world_grid_units': 32, 'layer_scale': 0.25, 'terrain_coverage_complete': False})
    write(P / 'godot-review/inputs/catalog.json', {'entries': entries, 'count': len(samples), 'atlas_sha256': sha(atlas_path)})

    comparisons = [('floor_center', 'E', 'floor_center', 'W'), ('floor_center', 'S', 'floor_center', 'N'),
                   ('floor_edge_N', 'E', 'floor_edge_N', 'W'), ('floor_edge_N', 'S', 'floor_center', 'N'),
                   ('floor_outer_NW', 'E', 'floor_edge_N', 'W'), ('floor_narrow_NS', 'S', 'floor_narrow_NS', 'N'),
                   ('bank_straight_N', 'E', 'bank_straight_N', 'W')]
    new = {row[0]: image for row, image in zip(selected, samples[:6])}
    write(P / 'interface-observations.json', {'measurements': [{'a': a, 'a_edge': ae, 'b': b, 'b_edge': be,
          **seam(new[a], ae, new[b], be)} for a, ae, b, be in comparisons],
          'alpha_or_rgb_modified': False, 'scope': 'Selected actual pairings only, not a full compatibility matrix.'})

    overview = board((1088, 448), '像素风订正 | 左：修前 / 右：本轮 | 每格128px，来源拼接，非GPU')
    draw = ImageDraw.Draw(overview)
    for i, (identifier, name, _, status) in enumerate(selected):
        x, y = 16 + (i % 3) * 360, 46 + (i // 3) * 196
        draw.text((x, y), name, font=FONT, fill='#edbd79')
        paste(overview, old[identifier], x, y + 28)
        paste(overview, new[identifier], x + 144, y + 28)
        draw.text((x, y + 160), '修前                 本轮候选', font=FONT, fill='#a3b9c3')
    draw.text((16, 426), '角块及共享板缝未全部通过；本图不是正式完整瓦片集。', font=FONT, fill='#ffb4a1')
    overview.save(P / 'review/six_candidates_before_after.png')
    passage = board((752, 476), '窄条接端头：只验证宽度，端头沿用旧稿 | 源图拼接，非GPU')
    draw = ImageDraw.Draw(passage)
    for column, middle in enumerate([samples[8], samples[2]]):
        x = 40 + column * 360
        draw.text((x, 42), '修前：46px接126px' if column == 0 else '修后：126px接126px', font=FONT, fill='#edbd79')
        for y, image in enumerate([samples[6], middle, samples[7]]):
            paste(passage, image, x, 74 + y * 128)
    passage.save(P / 'review/narrow_width_before_after.png')

    # 在本轮开始检查时冻结实际状态；不沿用可能被其他任务更新的历史哈希。
    before = P / 'protected-before.json'
    if not before.exists():
        names = read(PREVIOUS / 'protected-before.json')['sha256']
        write(before, {'scope': 'Shared norms, v007, main project and learner work',
                       'sha256': {name: sha(ROOT / name) for name in names}})
    print(json.dumps({'actual_generation_calls': len(records) + bank_prompts['built_in_call_count'],
          'packed_full_tiles': len(samples), 'selected_measurements': [{key: row[key] for key in ('id', 'status', 'measurement')} for row in entries[:6]]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
