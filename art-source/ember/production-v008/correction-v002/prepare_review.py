"""机械整格裁切与铺图诊断；不绘制、调色或修补素材中的艺术像素。"""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parent
ROOT = P.parents[3]
FONT = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 17)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local(path):
    return path.relative_to(ROOT).as_posix()


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def measure(image):
    """均值用于观察全局色调；主缝定位仅是启发式诊断，不充当视觉验收。"""
    rgba = np.asarray(image.convert('RGBA'))
    rgb = rgba[:, :, :3].astype(float)
    luminance = rgb.mean(axis=2)
    return {
        'size': list(image.size),
        'alpha_range': [int(rgba[:, :, 3].min()), int(rgba[:, :, 3].max())],
        'interior_rgb_mean': rgb[16:112, 16:112].mean(axis=(0, 1)).round(3).tolist(),
        'darkest_joint_row_48_80': int(luminance[48:81, 16:112].mean(axis=1).argmin() + 48),
        'darkest_joint_column_48_80': int(luminance[16:112, 48:81].mean(axis=0).argmin() + 48),
        'numeric_measurement_is_not_visual_acceptance': True,
    }


def floor_cells(width, height):
    """合法的北/西边与NW外角组合；东/南暂时是未封闭的开放板面。"""
    result = []
    for y in range(height):
        for x in range(width):
            identifier = 'floor_center'
            if y == 0:
                identifier = 'floor_outer_NW' if x == 0 else 'floor_edge_N'
            elif x == 0:
                identifier = 'floor_edge_W'
            result.append([x, y, identifier])
    return result


def passage_cells(middle_count):
    return [[0, 0, 'floor_end_N']] + [[0, y, 'floor_narrow_NS'] for y in range(1, middle_count + 1)] + [[0, middle_count + 1, 'floor_end_S']]


def paint_case(canvas, images, cells, origin, pixel_size):
    """仅将整块构件铺到诊断画布，不把画布或拼接片段当新艺术素材。"""
    for x, y, identifier in cells:
        tile = images[identifier].resize((pixel_size, pixel_size), Image.Resampling.NEAREST)
        canvas.alpha_composite(tile, (origin[0] + x * pixel_size, origin[1] + y * pixel_size))


def main():
    for folder in ('candidates', 'review', 'godot-review/inputs'):
        (P / folder).mkdir(parents=True, exist_ok=True)
    raw_path = P / 'raw/floor_connected_v001.png'
    raw = Image.open(raw_path)
    assert raw.size == (1254, 1254), '此裁框仅适用于登记的实际母图。'
    original = Path('C:/Users/shiru/.codex/generated_images/01a10204-0a39-77b3-b144-9e7a03fd8e93/exec-7bdc5cb5-d807-4a6b-8833-6e3682ada20d.png')
    assert sha(raw_path) == sha(original), '保存的母图必须是工具原稿的字节副本。'
    boxes = {
        'floor_outer_NW': [0, 0, 627, 627],
        'floor_edge_N': [627, 0, 1254, 627],
        'floor_edge_W': [0, 627, 627, 1254],
        'floor_center': [627, 627, 1254, 1254],
    }
    images, entries = {}, []
    for identifier, box in boxes.items():
        path = P / 'candidates' / (identifier + '_connected_v001_128.png')
        # 先整格裁切、再等比Nearest；不整张缩小后切、不移板缝、不补边梁。
        image = raw.crop(box).convert('RGBA').resize((128, 128), Image.Resampling.NEAREST)
        image.save(path)
        images[identifier] = image
        entries.append({'id': identifier, 'source_path': local(path), 'source_sha256': sha(path),
                        'raw_path': local(raw_path), 'crop_xyxy': box, 'resampling': 'NEAREST',
                        'atlas_coord': [len(entries), 0], 'measurement': measure(image),
                        'status': 'CONNECTED_MOTHER_DIAGNOSTIC_VISUAL_REVIEW_PENDING', 'production_ready': False})
    for identifier in ('floor_end_N', 'floor_narrow_NS', 'floor_end_S'):
        path = P / 'corridor-correction/candidates' / (identifier + '_pixel_v002_128.png')
        image = Image.open(path).convert('RGBA')
        assert image.size == (128, 128)
        images[identifier] = image
        entries.append({'id': identifier, 'source_path': local(path), 'source_sha256': sha(path),
                        'raw_path': local(P / 'corridor-correction/corridor_master_pixel_v002.png'),
                        'atlas_coord': [len(entries), 0], 'measurement': measure(image),
                        'status': 'WHOLE_MOTHER_RIM_CORRECTION_VISUAL_REVIEW_PENDING', 'production_ready': False})
    # 独立审查建议的617方框：仅作完整裁框比较，未被预先视为修复成功。
    for identifier, baseline_box in boxes.items():
        x, y = baseline_box[0] // 627, baseline_box[1] // 627
        box = [x * 617, y * 617, (x + 1) * 617, (y + 1) * 617]
        comparison_id = identifier + '_registered617'
        path = P / 'candidates' / (comparison_id + '_128.png')
        image = raw.crop(box).convert('RGBA').resize((128, 128), Image.Resampling.NEAREST)
        image.save(path)
        images[comparison_id] = image
        entries.append({'id': comparison_id, 'source_path': local(path), 'source_sha256': sha(path),
                        'raw_path': local(raw_path), 'crop_xyxy': box, 'resampling': 'NEAREST',
                        'atlas_coord': [len(entries), 0], 'measurement': measure(image),
                        'status': 'WHOLE_SQUARE_REGISTRATION_COMPARISON_ONLY', 'production_ready': False})
    atlas_path = P / 'godot-review/inputs/pilot_samples.png'
    atlas = Image.new('RGBA', (128 * len(entries), 128))
    for entry in entries:
        atlas.paste(images[entry['id']], (entry['atlas_coord'][0] * 128, 0))
    atlas.save(atlas_path)
    # 复现整理只继承来源SHA一致的审核，避免把旧审查套到新图，或覆盖已审结论。
    review_path = P / 'review-results.json'
    if review_path.exists():
        decisions = {row['id']: row for row in json.loads(review_path.read_text(encoding='utf-8'))['results']}
        for entry in entries:
            decision = decisions.get(entry['id'])
            if decision and decision['source_sha256'] == entry['source_sha256']:
                entry['status'] = decision['status']
                entry['review_reason'] = decision['reason']
    catalog = {'entries': entries, 'atlas_sha256': sha(atlas_path), 'old_assets_in_corrected_layout': 0,
               'texture_size': 128, 'world_size': 32, 'production_ready': False, 'complete_47': False}
    save_json(P / 'candidate-catalog.json', catalog)
    save_json(P / 'godot-review/inputs/catalog.json', catalog)
    def registered(cells):
        return [[x, y, identifier + '_registered617'] for x, y, identifier in cells]
    save_json(P / 'godot-review/inputs/cases.json', {'floor_2x2': floor_cells(2, 2), 'floor_4x4': floor_cells(4, 4),
              'floor_8x5': floor_cells(8, 5), 'corridor_original_three': passage_cells(1), 'corridor_repeated_five': passage_cells(3)})
    case_path = P / 'godot-review/inputs/cases.json'
    case_data = json.loads(case_path.read_text(encoding='utf-8'))
    case_data.update({'floor_repeat_627': floor_cells(3, 3), 'floor_repeat_617': registered(floor_cells(3, 3)),
                      'floor_world_617': registered(floor_cells(8, 5))})
    save_json(case_path, case_data)

    # 清楚区分工具母图直接相邻与可重复铺图：重复相位问题必须在右侧暴露。
    board = Image.new('RGBA', (1344, 804), '#182631')
    draw = ImageDraw.Draw(board)
    draw.text((20, 12), '同像素参考 / 连续母图切片  |  板缝与侧梁仍待验收', font=FONT, fill='white')
    draw.text((20, 48), '地板母图2×2完整复原', font=FONT, fill='white')
    paint_case(board, images, floor_cells(2, 2), (20, 82), 128)
    draw.text((320, 48), '地板重复4×4：观察相位与接头', font=FONT, fill='white')
    paint_case(board, images, floor_cells(4, 4), (320, 82), 128)
    draw.text((880, 48), '新端头/新直条', font=FONT, fill='white')
    paint_case(board, images, passage_cells(1), (880, 82), 128)
    draw.text((1056, 48), '重复中段×3', font=FONT, fill='white')
    paint_case(board, images, passage_cells(3), (1056, 82), 128)
    draw.text((20, 390), '实际32世界格', font=FONT, fill='white')
    paint_case(board, images, floor_cells(8, 5), (20, 424), 32)
    paint_case(board, images, passage_cells(3), (288, 424), 32)
    draw.text((20, 752), '全部修后构件均来自本轮像素母图。此图是诊断组合，不是完整47型或正式可用套装。', font=FONT, fill='white')
    board.save(P / 'review/connected_candidates_cpu.png')
    reference = P.parent / 'correction-v001/raw/floor_center_pixel_v001.png'
    prompt_path = P / 'floor_connected_v001.prompt.txt'
    record = {'id': 'floor_connected_v001', 'tool': 'image_gen.imagegen built-in',
              'original_tool_path': original.as_posix(), 'raw_path': local(raw_path), 'raw_sha256': sha(raw_path),
              'actual_raw_size': list(raw.size), 'actual_raw_mode': raw.mode, 'transparent_background_requested': False,
              'references': [{'path': local(reference), 'sha256': sha(reference)}],
              'prompt_path': local(prompt_path), 'prompt_sha256': sha(prompt_path),
              'prompt': prompt_path.read_text(encoding='utf-8'),
              'complete_cell_crops': [{'id': entry['id'], 'crop_xyxy': entry['crop_xyxy'], 'candidate_path': entry['source_path'],
                                       'candidate_sha256': entry['source_sha256']} for entry in entries if 'crop_xyxy' in entry],
              'production_ready': False}
    save_json(P / 'floor-generation-record.json', record)
    save_json(P / 'prompts.json', {'tool': 'image_gen.imagegen built-in', 'prompts': [
        {'id': 'floor_connected_v001', 'prompt': record['prompt'], 'references': record['references']},
        {'id': 'corridor_master_pixel_v001', 'prompt': (P / 'corridor/corridor_master_pixel_v001.prompt.txt').read_text(encoding='utf-8'),
         'references': record['references']},
        {'id': 'corridor_master_pixel_v002', 'prompt': (P / 'corridor-correction/corridor_master_pixel_v002.prompt.txt').read_text(encoding='utf-8'),
         'references': [{'path': local(P / 'corridor/raw/corridor_master_pixel_v001.png'), 'sha256': sha(P / 'corridor/raw/corridor_master_pixel_v001.png')},
                        {'path': local(raw_path), 'sha256': sha(raw_path)}]}], 'builtin_generation_count_this_revision': 3})
    corridor_records = [P / 'corridor/generation-record.json', P / 'corridor-correction/generation-record.json']
    if all(path.exists() for path in corridor_records):
        save_json(P / 'generation-record.json', {
            'tool': 'image_gen.imagegen built-in', 'actual_builtin_generation_count_this_revision': 3,
            'root_floor_record': local(P / 'floor-generation-record.json'),
            'corridor_records': [local(path) for path in corridor_records],
            'selected_corridor_revision': 2, 'selected_floor_crop_side': 627,
            'comparison_floor_crop_side': 617, 'old_assets_in_corrected_layout': 0,
            'art_pixel_repainting': False, 'alpha_repair': False, 'nonuniform_stretch': False,
            'production_ready': False,
        })
    print(json.dumps({'atlas_size': list(atlas.size), 'entries': len(entries), 'measurements': {row['id']: row['measurement'] for row in entries}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
