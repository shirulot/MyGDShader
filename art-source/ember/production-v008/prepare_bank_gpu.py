"""完整复制三张池岸样稿到独立GPU检查项目；水底与岸沿分别绘制。"""
from pathlib import Path
import hashlib
import json
from PIL import Image

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
G = P / 'godot-review/inputs'
G.mkdir(exist_ok=True)
catalog = json.loads((P / 'candidate-catalog.json').read_text(encoding='utf-8'))
entries = [e for e in catalog['entries'] if e['family'] == 'bank']
atlas = Image.new('RGBA', (384, 128))
for i, e in enumerate(entries):
    source = ROOT / e['candidate_path']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == e['candidate_sha256']
    image = Image.open(source).convert('RGBA')
    assert image.size == (128, 128)
    atlas.paste(image, (i*128, 0))
atlas.save(G / 'bank_samples_diagnostic.png')
old = json.loads((ROOT / 'assets/ember/environment/autotiles_v007/catalog.json').read_text(encoding='utf-8'))
water = next(a for a in old['atlases'] if a['id'] == 'water')
coord = next(e['coord'] for e in water['tiles'] if e['mask'] == 255)
source = ROOT / water['texture'].removeprefix('res://')
box = [coord[0]*128, coord[1]*128, (coord[0]+1)*128, (coord[1]+1)*128]
Image.open(source).crop(box).save(G / 'water_v007_diagnostic.png')
report = {'status': 'THREE_BANK_SAMPLES_DIAGNOSTIC_ONLY', 'bank_entries': entries,
          'atlas_sha256': hashlib.sha256((G / 'bank_samples_diagnostic.png').read_bytes()).hexdigest(),
          'water_source': source.relative_to(ROOT).as_posix(), 'water_crop_xyxy': box,
          'water_sha256': hashlib.sha256((G / 'water_v007_diagnostic.png').read_bytes()).hexdigest(),
          'operations': 'Copy complete 128px candidates; no resizing or pixel correction.',
          'full_bank_terrain': False}
(P / 'godot-review/bank-input-provenance.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('Bank diagnostic atlas and independent water background copied.')
