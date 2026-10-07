"""只读验收剩余40项的原生图像与目录，不生成或修正任何PNG。

自动规则只覆盖数值和来源版本；图形语义、设备比例、9slice及平铺观感另做视觉审查。
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
from PIL import Image

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
PALETTE = {tuple(bytes.fromhex(v)) for v in [
    '101820','182631','2B3E4B','4D6470','829BA3','BECBC4','7B4D35','B77C4B',
    'E2B77A','51C5C2','E5A44B','E65B4A','566B78','203A4B','406B78','ECE9D8']}
STATE = {tuple(bytes.fromhex(v)) for v in ['51C5C2','E5A44B','E65B4A']}
GROUPS = {'objects':18, 'ui':15, 'textures':7}
FIXED_ANCHORS = {'console_base':[48,80], 'pump_base':[80,176], 'ventilator_base':[80,176],
                 'cooler_base':[80,176], 'relay_base':[96,240], 'door_closed':[48,112],
                 'door_open':[48,112], 'telepad_base':[64,144], 'terminal_body':[48,80],
                 'screen_frame':[48,80]}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def resolve(value):
    path = (ROOT / value.removeprefix('res://')).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('资产路径越出项目')
    return path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding='utf-8'))
    rows = list(csv.DictReader((ROOT/'docs/shader-learning/asset-generation-manifest.csv').open(encoding='utf-8')))
    specs = {variant:row for row in rows if row['id'] in {
        'B02','B03','B04','B05','B06','B07','B08','B09','B10','B11','B12',
        'U01','U02','U03','U04','V01','V02','V03','X01','X02','X03'}
        for variant in row['variants'].split('|')}
    checks, measured = [], []
    def check(name, ok, actual, expected):
        checks.append({'name':name, 'passed':bool(ok), 'actual':actual, 'expected':expected})
    assets = catalog.get('assets', [])
    ids = [item['id'] for item in assets]
    check('all_40_unique_expected_variants',len(ids)==40 and len(set(ids))==40 and set(ids)==set(specs),ids,sorted(specs))
    for item in assets:
        identifier = item['id']
        spec = specs.get(identifier)
        if spec is None:
            continue
        check(identifier+':manifest_id',item.get('manifest_id')==spec['id'],item.get('manifest_id'),spec['id'])
        if identifier in FIXED_ANCHORS:
            check(identifier+':fixed_anchor',item.get('anchor')==FIXED_ANCHORS[identifier],item.get('anchor'),FIXED_ANCHORS[identifier])
        path = resolve(item['file'])
        check(identifier+':exists',path.is_file(),str(path),'actual PNG')
        if not path.is_file():
            continue
        check(identifier+':sha',sha(path)==item.get('sha256'),sha(path),item.get('sha256'))
        with Image.open(path) as raw:
            expected_size = tuple(map(int,spec['final_size'].split('x')))
            check(identifier+':canvas',raw.size==expected_size,list(raw.size),list(expected_size))
            required_mode = spec['alpha_or_channels']
            check(identifier+':mode',raw.mode==required_mode,raw.mode,required_mode)
            rgba = raw.convert('RGBA')
            pixels = [rgba.getpixel((x,y)) for y in range(raw.height) for x in range(raw.width)]
            alphas = {p[3] for p in pixels}
            soft_smoke = identifier=='smoke_blob' and item.get('alpha_policy')=='REGISTERED_SOFT_SMOKE'
            check(identifier+':alpha',soft_smoke or alphas<={0,255},sorted(alphas),'binary or explicitly registered soft smoke')
            off = sum(p[3]>0 and p[:3] not in PALETTE for p in pixels)
            check(identifier+':palette',off==0,off,0)
            visible_colors=len({p[:3] for p in pixels if p[3]})
            if item.get('rgb_count') is not None:
                check(identifier+':declared_color_count',visible_colors==item['rgb_count'],visible_colors,item['rgb_count'])
            bbox = rgba.getchannel('A').getbbox()
            check(identifier+':nonempty',bbox is not None,bbox,'visible content')
            if bbox is None:
                continue
            check(identifier+':declared_bbox',list(bbox)==item.get('bbox'),list(bbox),item.get('bbox'))
            if spec['id'].startswith('B'):
                margin = 8 if raw.size==(64,64) else 16
                x0,y0,x1,y1 = bbox
                check(identifier+':object_margin',x0>=margin and y0>=margin and x1<=raw.width-margin and y1<=raw.height-margin,
                      list(bbox),f'at least {margin}px each side')
                if identifier not in {'screen_frame'}:
                    check(identifier+':base_neutral',not any(p[3]>0 and p[:3] in STATE for p in pixels),
                          sum(p[3]>0 and p[:3] in STATE for p in pixels),0)
            if raw.size==(32,32):
                check(identifier+':icon_margin',bbox[0]>=4 and bbox[1]>=4 and bbox[2]<=28 and bbox[3]<=28,list(bbox),'within [4,4,28,28)')
                check(identifier+':icon_center',item.get('anchor')==[16,16],item.get('anchor'),[16,16])
            if identifier=='panel_9slice':
                check(identifier+':slice_margins',item.get('slice_margins')==[8]*4,item.get('slice_margins'),[8]*4)
            if identifier=='screen_frame':
                check(identifier+':slice_region',item.get('slice_region')==[16,16,64,64],item.get('slice_region'),[16,16,64,64])
                check(identifier+':slice_margins',item.get('slice_margins')==[8]*4,item.get('slice_margins'),[8]*4)
                check(identifier+':transparent_center',rgba.getchannel('A').crop((24,24,72,72)).getbbox() is None,item.get('draw_center'),False)
            if identifier=='grass_leaf':
                check(identifier+':root_anchor',item.get('anchor')==[32,120],item.get('anchor'),[32,120])
                # 草叶规范只要求真实透明边及根部120，不套用64×64小道具的8px留边。
                check(identifier+':leaf_margin',bbox[0]>0 and bbox[1]>0 and bbox[2]<64 and bbox[3]==120,list(bbox),'transparent outer border; root boundary y120')
            seam_axes = 'XY' if identifier in {'water_calm','water_directional','metal_albedo','concrete_albedo'} else 'X' if identifier=='foam_strip' else ''
            seam = {}
            for axis in seam_axes:
                mismatch = sum(rgba.getpixel((0,y))!=rgba.getpixel((raw.width-1,y)) for y in range(raw.height)) if axis=='X' else sum(rgba.getpixel((x,0))!=rgba.getpixel((x,raw.height-1)) for x in range(raw.width))
                seam[axis] = mismatch
                check(identifier+':seam_'+axis,mismatch==0,mismatch,0)
            measured.append({'id':identifier,'sha256':sha(path),'file':item['file'],'canvas':list(raw.size),
                             'bbox':list(bbox),'visible_colors':visible_colors,
                             'alpha_levels':sorted(alphas),'seam_mismatches':seam})
        check(identifier+':source_use',bool(item.get('source_use')),item.get('source_use'),'explicit source semantics')
    failed = [c for c in checks if not c['passed']]
    report = {'status':'NATIVE_40_NUMERIC_PASS' if not failed else 'NATIVE_40_NUMERIC_FAIL',
              'count':len(measured),'automatic_checks':len(checks),'failed_checks':failed,
              'checks':checks,'assets':measured,'images_modified':False,
              'visual_review':'SEPARATE_REQUIRED','validator_sha256':sha(Path(__file__))}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'count':len(measured),'checks':len(checks),'failures':len(failed)}))
    raise SystemExit(bool(failed))

if __name__=='__main__':
    main()
