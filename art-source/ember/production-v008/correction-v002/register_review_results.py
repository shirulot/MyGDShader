"""登记当前实图审查结论；只更新来源SHA相符的状态，不修改美术文件。"""
import json
from pathlib import Path

P = Path(__file__).resolve().parent


def main():
    catalog = json.loads((P / 'candidate-catalog.json').read_text(encoding='utf-8'))
    validation = json.loads((P / 'godot-review/validation.json').read_text(encoding='utf-8'))
    assert catalog['atlas_sha256'] == validation['source_atlas_sha256']
    results = []
    for entry in catalog['entries']:
        identifier = entry['id']
        if identifier.endswith('_registered617'):
            status = 'REJECTED_ALTERNATE_REGISTRATION_SET'
            reason = ('617整套裁框虽保留更多起点倒角，仍存在约65/63px板距交替；'
                      'N边最右铆钉bbox[1220,65,1238,83)跨出整套x1234切线，37个亮铜像素被截去。'
                      '整套未采用，保留作比较，不逐块冒称全部铆钉都被截。')
        elif identifier in ('floor_end_N', 'floor_end_S', 'floor_narrow_NS'):
            status = 'PALETTE_RIM_IMPROVED_STRICT_GRID_NOT_PASSED'
            reason = ('当前v002新端头和中段共享连续母图，蓝灰像素材质与地板更一致；'
                      '主侧梁约8px，完整截面含隔缝/倒角约10~11px。'
                      '首缝中心约66而非64；固定周期及全方向连接仍未通过。')
        else:
            status = 'PALETTE_CONTIGUOUS_ADJACENCY_IMPROVED_REPEAT_NOT_PASSED'
            reason = ('627地板来自同一母图，当前角→边及自然相邻的颜色/像素语言一致性明显改善；'
                      '中心裁框切在[623,633)原稿竖缝内，重复边界半缝与内部完整倒角不一致，'
                      '板距仍轻微交替。不能把自然相邻连续性登记为任意重复通过。')
        results.append({'id': identifier, 'source_sha256': entry['source_sha256'],
                        'status': status, 'reason': reason, 'production_ready': False, 'user_visual_approval': False})
        entry['status'] = status
        entry['review_reason'] = reason
    report = {
        'status': 'COLOR_STYLE_LOCALLY_IMPROVED_STRUCTURE_AND_COVERAGE_NOT_PASSED',
        'evidence_atlas_sha256': catalog['atlas_sha256'],
        'gpu_views': validation['gpu_captures'], 'old_assets_in_corrected_layout': 0,
        'selected_floor_crop_side': 627, 'alternate617_selected': False, 'selected_corridor_revision': 2,
        'local_color_style_observation': '本轮真实GPU组合未见上轮大块写实/像素切换或明显颜色色带。',
        'complete_47': False, 'production_ready': False, 'user_visual_approval': False,
        'independent_review': 'review/independent-floor-source-review.md', 'results': results,
    }
    (P / 'review-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for path in (P / 'candidate-catalog.json', P / 'godot-review/inputs/catalog.json'):
        path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # 来源像素与atlas SHA未改变，GPU技术验收仍有效；这里只补充对应实图的材料判定。
    validation['art_review'] = {
        'color_style_locally_improved': True, 'structure_passed': False,
        'complete_47': False, 'production_ready': False, 'review_results': '../review-results.json',
    }
    (P / 'godot-review/validation.json').write_text(json.dumps(validation, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Registered 7 principal candidates and 4 rejected alternate-crop comparison items; production_ready=false.')


if __name__ == '__main__':
    main()
