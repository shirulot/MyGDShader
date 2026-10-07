"""只做完整单块导出及诊断试铺，不绘制/替换生成稿中的美术轮廓。"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parent
ROOT = P.parents[2]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = P / 'candidates'; out.mkdir(exist_ok=True)
    review = P / 'review'; review.mkdir(exist_ok=True)
    raw = P / 'raw/floor_center_v001.png'
    original = Image.open(raw).convert('RGBA')
    box = [0, 0, original.width, original.height]
    # 开放边本来就延续至母稿边缘；不裁掉边缘或对接口重新填色。
    tile = original.crop(box).resize((128, 128), Image.Resampling.LANCZOS)
    candidate = out / 'floor_center_v001.png'; tile.save(candidate)
    old = Image.open(P / 'inputs/v007_floor_mask255.png').convert('RGBA')
    board = Image.new('RGB', (824, 466), '#182631'); draw = ImageDraw.Draw(board)
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 18)
    for column, (name, image) in enumerate([('v007中心：128px原生重复', old), ('v008中心小样：128px原生重复', tile)]):
        draw.text((16 + column * 408, 10), name, font=font, fill='white')
        for row in range(3):
            for col in range(3): board.paste(image.convert('RGB'), (16 + column * 408 + col * 128, 44 + row * 128))
    draw.text((16, 436), '源图试铺；非GPU渲染。仅完整单块缩放，没有接口重绘。', font=font, fill='#BECBC4')
    board_path = review / 'floor_center_repeat_before_after.png'; board.save(board_path)
    a = np.asarray(tile)
    deltas = {}
    for axis, first, second in [('horizontal', a[:, 0], a[:, -1]), ('vertical', a[0], a[-1])]:
        delta = np.abs(first.astype(int) - second.astype(int))
        deltas[axis] = {'rgba_equal': bool(np.array_equal(first, second)),
                        'different_positions': int(np.any(delta > 0, axis=1).sum()),
                        'rgb_mean_absolute_difference': float(delta[:, :3].mean()),
                        'alpha_differences': int((delta[:, 3] > 0).sum())}
    metadata = {'id': 'floor_center', 'mask': 255, 'source': raw.relative_to(ROOT).as_posix(),
        'source_sha256': sha(raw), 'source_size': list(original.size), 'actual_crop_xyxy': box,
        'export': candidate.relative_to(ROOT).as_posix(), 'export_sha256': sha(candidate), 'target_size': [128, 128],
        'export_operations': 'Whole single-tile full-canvas crop then LANCZOS export; no palette reduction, Alpha template or interface pixel painting.',
        'opaque_pixels': int((a[:, :, 3] == 255).sum()), 'partial_alpha_pixels': int(((a[:, :, 3] > 0) & (a[:, :, 3] < 255)).sum()),
        'rgba_opposite_edge_measurements': deltas,
        'status': 'CENTER_GEOMETRY_CANDIDATE_EXACT_RGBA_SEAMS_NOT_VALIDATED',
        'review': board_path.relative_to(ROOT).as_posix()}
    (P / 'floor_center_export.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'source_size': metadata['source_size'], 'opaque_pixels': metadata['opaque_pixels'], 'interfaces': deltas}, ensure_ascii=False))


if __name__ == '__main__': main()
