"""Record manual semantic review of the independently inspected native previews.

This does not label every hole a defect and never edits production images.
"""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


notes = {
    'station_base_v001': ('两侧弯管与圆柱本体之间的成对穿空；管路连接及基座均连续，静态底图不是分层导出丢像素。',
                          [[32, 81, 38, 88], [90, 81, 96, 88]]),
    'relay_base_v001': ('两侧管路与主体间留空；桅杆、横梁及天线实体连续。两孔大小略有差别符合既有左右管路形状。',
                        [[71, 177, 73, 182], [119, 176, 121, 182]]),
    'wall_lamp_v001': ('右侧电缆弯环内孔；原生整理记录明确保留该电缆弯环与孔。', [[37, 23, 39, 28]]),
    'door_open_v001': ('开启状态通路明确为透明区域；横梁连接两侧立框。不得填成实心墙面。', [[26, 38, 70, 112]]),
    'screen_frame_v001': ('九宫格外框中心48×48完整透明；四边连续，源登记 draw_center=false。', [[24, 24, 72, 72]]),
    'antenna_coil_v001': ('两处2×1穿孔是明确登记的绕组外沿穿孔，不是缺失像素。', [[20, 27, 22, 28], [33, 27, 35, 28]]),
    'fuse_v001': ('右端1×3槽和左端叉口为刻意不对称校准结构；源记录有透明孔坐标。', [[48, 48, 49, 51], [13, 49, 16, 51]]),
    'split_ring_v001': ('C形环的开口与内部空间相通；源登记 gap[41,48,44,51)，不可补成闭环。', [[41, 48, 44, 51]]),
    'toolbox_v001': ('手柄内槽形成33像素透明孔，包含登记核心孔[28,33,37,35)；手柄边缘和箱体仍连通。',
                     [[26, 33, 39, 36], [28, 33, 37, 35]]),
    'interact_v001': ('两个1像素透明点位于机械手指/关节之间，指尖2px陶瓷杆与开关连续；没有悬空手指碎片。',
                      [[19, 15, 20, 16], [18, 16, 19, 17]]),
    'communication_v001': ('柱周围通信波瓣留空；1px亮线带暗衬是语义图标结构，柱和底座连续。所有透明孔坐标在测量附件。',
                           [[9, 8, 10, 9], [18, 9, 19, 13], [24, 10, 25, 13], [10, 13, 11, 14],
                            [20, 13, 21, 14], [18, 14, 21, 18], [7, 17, 8, 18], [24, 17, 25, 18], [20, 18, 21, 19]]),
    'cooling_v001': ('左右换热鳍片各有对称1px留空，中央六枝雪花及主体连续，不是线条端部脱落。',
                    [[7, 16, 8, 17], [24, 16, 25, 17]]),
    'teleport_v001': ('空心拱门与中央箭头之间透明；箭头2px杆和阶梯尖连续，底座相接。',
                     [[11, 10, 21, 16], [11, 17, 14, 20], [19, 17, 21, 19]]),
    'foam_strip_v001': ('主泡沫带外7像素小团为喷溅泡沫；两处透明泡孔符合断续双带，不是应连接的硬表面。X边完整配对。',
                       [[40, 28, 43, 32], [9, 33, 19, 38], [35, 36, 37, 38]]),
    'grass_leaf_v001': ('细叶斜线以相邻像素角连接：4邻接9片、8邻接1片，所有叶片属于同一株，根部x31..33/y119会合。叶间细孔和阶梯轮廓不是机器人关节缺口；需在Nearest整数倍下判断。',
                       [[31, 119, 34, 120], [39, 79, 40, 91], [36, 84, 37, 93], [28, 104, 29, 107],
                        [29, 107, 30, 110], [27, 102, 28, 104], [38, 111, 39, 113]]),
}

measure_path = OUT / 'alpha-measurements.json'
data = json.loads(measure_path.read_text(encoding='utf-8'))
assets = []
failures = []
for a in data['assets']:
    if sha(ROOT / a['file']) != a['sha256']:
        failures.append(a['file'] + ': production changed during audit')
    if not (OUT / a['individual_visual']).exists():
        failures.append(a['file'] + ': visual missing')
    for ref in a['native_finished_sources']:
        if not ref['production_bytes_identical']:
            failures.append(ref['file'] + ': production differs from native source')
    for ls in a['independent_layer_reconstruction']:
        if ls['alpha_mismatch_pixels'] or ls['visible_rgb_mismatch_pixels']:
            failures.append(a['file'] + ': layer reconstruction mismatch')
    note, coordinates = notes.get(a['id'], ('原生1×和Nearest4×逐张观察，实体轮廓及内部细线没有发现非预期透明孔、悬空片或中断。', []))
    assets.append({'id': a['id'], 'file': a['file'], 'sha256': a['sha256'],
                   'classification': 'NORMAL_DESIGN' if a['id'] in notes else 'NO_FRACTURE_OBSERVED',
                   'observation_zh': note, 'native_evidence_regions': coordinates,
                   'visual': a['individual_visual'], 'visual_sha256': sha(OUT / a['individual_visual']),
                   'native_visual_inspected': True, 'nearest_4x_visual_inspected': True})
assert not failures, failures
report = {
    'date': '2026-10-04', 'status': 'INDEPENDENT_OTHER_ART_41_NATIVE_PIXEL_FRACTURE_REVIEW_COMPLETE',
    'role': 'Independent reviewer of existing production; not original creator; no production edits.',
    'scope': {'production_pngs': 41, 'building_and_prop_pngs': 19, 'ui_pngs': 15, 'vfx_and_3d_art_pngs': 7,
              'excluded': ['robot frames and atlas', 'three tile atlases', '40 technical data PNGs']},
    'result': {'confirmed_pixel_fracture_assets': 0, 'unresolved_suspect_assets': 0,
               'normal_design_assets_with_holes_or_discontinuous_motifs': len(notes),
               'other_assets_without_observed_fractures': len(assets) - len(notes),
               'production_art_pngs_modified': 0, 'partial_alpha_pixels_all_41': 0,
               'native_finished_pngs_identical_to_production': sum(bool(a['native_finished_sources']) for a in data['assets']),
               'late_object_assets_recomposed_from_real_layers': sum(bool(a['independent_layer_reconstruction']) for a in data['assets']),
               'source_recomposition_alpha_or_visible_rgb_difference_pixels': 0},
    'method': ['Read 41 production PNGs, independent alpha 4/8 connected components and enclosed-hole coordinates.',
               'Actually inspect every production PNG at native 1x and exact nearest 4x; individual images avoid downscaled large-board ambiguity.',
               'Read additional/full-art/batch source catalogs and native finishing records; compare native finished PNG bytes for 40.',
               'Independently alpha-compose the real 18 late object layer sets and compare all alpha and visible RGB to production.',
               'Judge every detected hole/disconnected component by object semantics; do not apply global hole filling.'],
    'limits': ['This covers native static artwork and exact integer enlargement. Runtime sampling, frame anatomy and tile neighbor seams are separate team reviews.',
               'No fracture observed is a scoped visual result, not a guarantee against every possible future shader distortion or display scale.'],
    'coordinate_convention': data['coordinate_convention'],
    'measurement_file': measure_path.name, 'measurement_sha256': sha(measure_path),
    'catalog_sha256': data['catalog_sha256'], 'assets': assets,
}
target = OUT / 'independent-other-art-review.json'
target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report['result'], ensure_ascii=False))
