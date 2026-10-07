"""将完整美术单块登记到官方47模板槽位；不修改图块轮廓或接口。

先运行本脚本生成旧版官方排列基线；加 --with-samples 则生成五块新样混合的诊断图集。
后者用于暴露实际铺刷问题，不表示47张新母稿已完成。
"""
from pathlib import Path
import argparse
import hashlib
import json
from PIL import Image

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
OUT = P / 'official'
OUT.mkdir(exist_ok=True)

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build(with_samples=False):
    guide = load(P / 'inputs/official-template-layout.json')
    old_catalog = load(ROOT / 'assets/ember/environment/autotiles_v007/catalog.json')
    old_floor = next(a for a in old_catalog['atlases'] if a['id'] == 'floor')
    old_path = ROOT / old_floor['texture'].removeprefix('res://')
    old_image = Image.open(old_path).convert('RGBA')
    old_entries = {int(e['mask']): e for e in old_floor['tiles'] if e.get('variant', 0) == 0}
    samples = {}
    if with_samples:
        samples = {int(e['mask']): e for e in load(P / 'candidate-catalog.json')['entries']
                   if e['family'] == 'floor' and not e['status'].startswith('REJECTED')}
        assert len(samples) == 5, '五个地板样稿必须先登记，不静默用旧块冒充。'
    atlases = []
    for identifier in (['baseline', 'trial'] if with_samples else ['baseline']):
        image = Image.new('RGBA', (12*128, 4*128))
        entries = []
        for y, row in enumerate(guide['layout_rows']):
            for x, mask in enumerate(row):
                if mask is None:
                    continue
                old_coord = old_entries[mask]['coord']
                box = [old_coord[0]*128, old_coord[1]*128,
                       (old_coord[0]+1)*128, (old_coord[1]+1)*128]
                sample = samples.get(mask) if identifier == 'trial' else None
                if sample:
                    path = ROOT / sample['candidate_path']
                    tile = Image.open(path).convert('RGBA')
                    source = {'kind': 'v008_generated_sample', 'id': sample['id'],
                              'path': sample['candidate_path'], 'sha256': sha(path),
                              'source_status': sample['status']}
                else:
                    tile = old_image.crop(box)
                    source = {'kind': 'v007_reused_complete_tile',
                              'path': old_path.relative_to(ROOT).as_posix(),
                              'sha256': sha(old_path), 'original_coord': old_coord,
                              'actual_crop_xyxy': box}
                assert tile.size == (128, 128)
                # 只移动完整的128px方块，不缩放整张atlas，不重画接口。
                image.paste(tile, (x*128, y*128))
                entries.append({'mask': mask, 'coord': [x, y], 'source': source})
        filename = 'floor_v007_official_order.png' if identifier == 'baseline' else 'floor_trial_mixed.png'
        path = OUT / filename
        image.save(path)
        atlases.append({'id': identifier, 'texture': filename, 'sha256': sha(path),
                        'status': 'V007_REORDERED_BASELINE' if identifier == 'baseline' else 'MIXED_DIAGNOSTIC_ONLY',
                        'new_sample_count': 0 if identifier == 'baseline' else len(samples),
                        'reused_v007_count': 47 if identifier == 'baseline' else 47-len(samples),
                        'tiles': entries})
    catalog = {'tile_size': 128, 'logical_tile_size': 32, 'display_scale': 0.25,
               'columns': 12, 'rows': 4, 'blank_coord': [10, 1],
               'bit_order_8': 'N NE E SE S SW W NW',
               'mode': 'Match Corners And Sides',
               'template': '../inputs/official_autotile_template_3x3_minimal.png',
               'template_source_url': guide['source_url'],
               'user_visual_approval': False, 'production_ready': False,
               'artwork_operations': 'Repack complete 128px tiles only; no painting, blending or shape masks.',
               'atlases': atlases}
    (OUT / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'atlases': [(a['id'], len(a['tiles']), a['new_sample_count']) for a in atlases]}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--with-samples', action='store_true')
    build(parser.parse_args().with_samples)
