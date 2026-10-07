"""整矩形裁切真实GPU截图制作对照；只用于审阅，不生成任何美术图块。"""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parent
FONT = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 16)


def main():
    previous_path = P.parent / 'correction-v001/godot-review/pixel_pilot_native_gpu.png'
    current_path = P / 'godot-review/connected_native_gpu.png'
    previous, current = Image.open(previous_path), Image.open(current_path)
    assert previous.size == (1600, 1100) and current.size == (1344, 804)
    catalog = json.loads((P / 'candidate-catalog.json').read_text(encoding='utf-8'))
    validation = json.loads((P / 'godot-review/validation.json').read_text(encoding='utf-8'))
    assert catalog['atlas_sha256'] == validation['source_atlas_sha256'], '对照必须对应当前候选的GPU结果。'
    board = Image.new('RGB', (928, 804), '#182631')
    draw = ImageDraw.Draw(board)
    draw.text((16, 12), '颜色与像素风格订正  |  两侧均为真实Godot GPU截图整矩形裁切', font=FONT, fill='white')
    draw.text((16, 48), '修前：独立角块／旧写实端头', font=FONT, fill='white')
    draw.text((488, 48), '本轮：同源地板／全新像素端头', font=FONT, fill='white')
    parts = [
        ('previous_corner_edge', previous, previous_path, [32, 530, 288, 658], [16, 84]),
        ('previous_mixed_corridor', previous, previous_path, [1120, 80, 1248, 720], [304, 84]),
        ('current_corner_edge', current, current_path, [24, 88, 280, 216], [488, 84]),
        ('current_all_pixel_corridor', current, current_path, [1064, 88, 1192, 728], [776, 84]),
    ]
    sources = []
    for name, image, path, box, position in parts:
        board.paste(image.crop(box).convert('RGB'), tuple(position))
        sources.append({'id': name, 'gpu_source_path': path.as_posix(),
                        'gpu_source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'whole_rectangle_crop_xyxy': box, 'destination_xy': position,
                        'resampling': None, 'art_pixel_mutation': False})
    draw.text((16, 242), '角→边存在板缝／色阶差异', font=FONT, fill='white')
    draw.text((488, 242), '颜色与材质更一致', font=FONT, fill='white')
    draw.text((488, 270), '重复边界半缝仍未通过', font=FONT, fill='#f3d086')
    draw.text((16, 758), '本轮解决明显材质跳变；结构相位和完整47型仍未完成，不作为正式通用套装发布。', font=FONT, fill='white')
    board.save(P / 'review/style_before_after_gpu.png')
    (P / 'review/style_before_after_sources.json').write_text(json.dumps({
        'kind': 'DIAGNOSTIC_GPU_CROP_COMPARISON_ONLY', 'current_atlas_sha256': catalog['atlas_sha256'],
        'sources': sources, 'production_art': False,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('GPU comparison saved; original captures preserved; no resampling or artwork edits.')


if __name__ == '__main__':
    main()
