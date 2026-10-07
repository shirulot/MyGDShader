"""登记实际弧形岸稿；只整体注册/等比导出，并检查真实主体接边。"""
import importlib.util
import json
from pathlib import Path
import shutil
import hashlib
import numpy as np
from PIL import Image

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
B = P / 'bank'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def main():
    helper_spec = importlib.util.spec_from_file_location('bank_measurements', B / 'prepare_candidates.py')
    helper = importlib.util.module_from_spec(helper_spec)
    helper_spec.loader.exec_module(helper)
    original = Path('C:/Users/shiru/.codex/generated_images/01a10204-0a39-77b3-b144-9e7a03fd8e93/exec-b83357cc-7409-494d-a5b9-8aceeb41be8e.png')
    raw_path = B / 'raw/bank_inner_NW_v003.png'
    shutil.copy2(original, raw_path)
    raw = Image.open(raw_path).convert('RGBA')
    # 模型画稿有约58/72px页面留白。整体方形注册，切口深入8px左右，
    # 去掉画在页内的封口亮边；不裁紧弧段后放大，不局部拉伸两岸。
    box = [66, 80, 1320, 1334]
    candidate = raw.crop(box).resize((128, 128), Image.Resampling.LANCZOS)
    output = B / 'candidates/bank_inner_NW_sample_v003.png'
    candidate.save(output)
    preview = B / 'review/bank_inner_NW_v003_4x.png'
    candidate.resize((512, 512), Image.Resampling.NEAREST).save(preview)
    measurements = helper.measurements(candidate)
    ports = measurements['edge_alpha_above_127_pixel_counts']
    assert ports['N'] > 0 and ports['W'] > 0 and ports['E'] == 0 and ports['S'] == 0
    report = read(B / 'generation-record.json')
    backup = B / 'generation-record.before-inner-v003.json'
    if not backup.exists():
        shutil.copy2(B / 'generation-record.json', backup)
    entries = report['candidate_entries']
    old_entry = next(e for e in entries if e['id'] == 'bank_inner_NW')
    entry = {'id': 'bank_inner_NW', 'mask': 127, 'raw': raw_path.name,
             'crop': box, 'offset': [-66, -80],
             'status': 'VISUAL_SAMPLE_PENDING_CONNECTION_REVIEW',
             'reason': 'v003曲线构件整体注册后N/W有真实主体端口、E/S透明。跨度约半格、弧口与其他方向接口位置仍需统一；不登记正式无缝通过。',
             'raw_path': raw_path.relative_to(ROOT).as_posix(), 'raw_sha256': sha(raw_path),
             'raw_measurements': helper.measurements(raw),
             'candidate_path': output.relative_to(ROOT).as_posix(), 'candidate_sha256': sha(output),
             'candidate_measurements': measurements,
             'candidate_components8_alpha_above_127': helper.components(np.asarray(candidate)[:, :, 3], 127),
             'uniform_scale_factor': 128/1254, 'registered_canvas': [1254, 1254],
             'out_of_bounds_transparency_padding': [0, 0, 66, 80],
             'crop_coordinate_convention': 'XYXY half-open; whole-component square registration',
             'artwork_operations': ['complete square crop/translation with transparent padding', 'uniform complete image reduction'],
             'no_local_pixel_or_alpha_repair': True,
             'previous_candidate_record': backup.relative_to(ROOT).as_posix(),
             'previous_candidate_path': old_entry['candidate_path'],
             'review_preview': preview.relative_to(ROOT).as_posix()}
    report['candidate_entries'] = [entry if e['id'] == 'bank_inner_NW' else e for e in entries]
    report['status'] = 'THREE_ART_CANDIDATES_INTERFACES_NOT_PASSED'
    report['scope'] = 'Three bank directions with v003 registered curved inner artwork; no full pool-loop proof.'
    report['producer_continuation'] = 'root/register_bank_v003.py'
    report['remaining_issues'] = [
        '接口RGBA仍未一致，不能发布正式连接套件。',
        '弧形内岸跨度约半格；其他朝向和邻接弧口位置仍需同尺度统一。',
        '生成的微弱Alpha杂点按原样保留；阈值仅用于主体诊断。',
        '直岸暗立面比例较高，保留美术审查。',
        '未生成全四向池岸，没有用旋转光照拼闭环。']
    report['raw_images'] = [r for r in report['raw_images'] if r['prompt_id'] != 'bank_inner_NW_v003']
    report['raw_images'].append({'path': raw_path.relative_to(ROOT).as_posix(),
                                  'sha256': sha(raw_path), 'measurements': helper.measurements(raw),
                                  'prompt_id': 'bank_inner_NW_v003'})
    prompts = read(B / 'prompts.json')
    prompts['prompts'] = [r for r in prompts['prompts'] if r['id'] != 'bank_inner_NW_v003']
    prompts['prompts'].append({'id': 'bank_inner_NW_v003',
        'prompt': (P / 'bank_inner_v003.prompt.txt').read_text(encoding='utf-8'),
        'output_hint': 'Generated original by image_gen.imagegen: '+original.as_posix(),
        'transparent_background': True, 'tool': 'image_gen.imagegen',
        'referenced_image_paths': ['art-source/ember/autotiles-v003/industrial_tile_master_v003.png',
                                 'art-source/ember/production-v008/bank/raw/bank_straight_N_v001.png'],
        'requested_image_size': [1024, 1024], 'actual_image_size': list(raw.size),
        'default_output_file': original.as_posix(),
        'local_saved_file': raw_path.relative_to(ROOT).as_posix(), 'targeted_repair_round': 2})
    report['raw_generation_count'] = len(prompts['prompts'])
    write(B / 'prompts.json', prompts)
    report['prompts_sha256'] = sha(B / 'prompts.json')
    write(B / 'generation-record.json', report)
    write(P / 'bank_inner_v003_export.json', entry)
    print(json.dumps({'ports_alpha_above127': ports, 'candidate_components': entry['candidate_components8_alpha_above_127'],
                      'crop': box, 'bbox': measurements['alpha_bbox_above_127']}))

if __name__ == '__main__':
    main()
