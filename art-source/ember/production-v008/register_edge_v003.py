"""登记实际第三版北边原稿；表示转换及完整方块导出不填补生成Alpha。"""
from pathlib import Path
import json
import shutil

P = Path(__file__).resolve().parent
F = P / 'floor'
ROOT = P.parents[2]
original = Path('C:/Users/shiru/.codex/generated_images/01a10204-0a39-77b3-b144-9e7a03fd8e93/exec-0f8faae8-a2a7-451b-a5b2-9811e810dc04.png')
raw = F / 'raw/floor_edge_N_v003.png'
shutil.copy2(original, raw)
prompt_path = F / 'prompts/floor_edge_N_v003.txt'
shutil.copy2(P / 'floor_edge_v003.prompt.txt', prompt_path)
seed_path = F / 'generation-record.seed.json'
seed = json.loads(seed_path.read_text(encoding='utf-8'))
for path in [F / 'candidate-catalog.json', F / 'generation-record.json']:
    backup = path.with_name(path.stem+'.before-edge-v003.json')
    if not backup.exists():
        shutil.copy2(path, backup)
seed['records'] = [r for r in seed['records'] if not (r['id'] == 'floor_edge_N' and r['version'] == 'v003')]
seed['records'].append({
    'id': 'floor_edge_N', 'mask': 124, 'version': 'v003',
    'tool': 'image_gen.imagegen', 'intent': 'precise-object-edit',
    'prompt': prompt_path.read_text(encoding='utf-8'),
    'references': [
        'art-source/ember/production-v008/floor/candidates/floor_edge_N_v001_128.png',
        'art-source/ember/production-v008/raw/floor_center_v001.png',
        'art-source/ember/autotiles-v003/industrial_tile_master_v003.png'],
    'raw_file': raw.relative_to(ROOT).as_posix(),
    'original_tool_path': original.as_posix(),
    'original_tool_output_hint': 'Generated original saved by image_gen.imagegen: '+original.as_posix(),
    'transparent_background_requested': False,
    'adoption': 'CANDIDATE_NOT_ACCEPTED',
    'notes': 'v003全画布RGB实底，去掉北梁切口处半黄铜；南开放端无Alpha渐隐。仍需统一梁宽、板缝和新旧相邻接口，不能登记无缝通过。',
    'interface_status': 'NOT_PASSED', 'visual_status': 'CANDIDATE_NOT_USER_APPROVED',
    'retry_count': 2, 'source_crop_xyxy': [0, 0, 1254, 1254],
    'transparent_padding_added': [0, 0, 0, 0]})
seed['scope'] = 'four floor classes; eight actual raw model outputs with two north-edge repairs'
seed_path.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding='utf-8')
print('floor_edge_N_v003 original saved and full prompt registered.')
