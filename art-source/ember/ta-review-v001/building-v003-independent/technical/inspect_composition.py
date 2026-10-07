"""固定包只读审计：独立重组功能层并定位屋顶/墙双重倒角；不启动 Godot。"""
import difflib
import hashlib
import json
import math
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
from PIL import Image, ImageDraw

ROOT = Path('E:/dev/shader/godot-shader/godot-shader-simple')
OUT = Path(__file__).resolve().parent
NEW = ROOT / 'art-source/ember/deliveries/building_assets_v003_2026-10-06.zip'
OLD = ROOT / 'art-source/ember/deliveries/building_assets_v002_2026-10-06.zip'
EXPECTED = '624e62421ada6b468fe7324991ba8c563602ea875a46678f96f44af7f0901ff9'
def sha(data): return hashlib.sha256(data).hexdigest()
def path(value): return value.removeprefix('res://')
def png(package, value): return Image.open(BytesIO(package.read(path(value)))).convert('RGBA')
def pixels(image): return list(image.get_flattened_data())
def difference(a, b):
    assert a.size == b.size
    return sum(x != y for x, y in zip(pixels(a), pixels(b)))
def mask_paste(dst, src, at=(0, 0)):
    # 正式来源为二值 Alpha；Godot blit_rect_mask 等价于按不透明像素替换。
    assert set(src.getchannel('A').get_flattened_data()).issubset({0,255})
    dst.paste(src, at, src.getchannel('A'))
def tint(src, factors):
    result = Image.new('RGBA', src.size)
    result.putdata([tuple(math.floor(v*f+0.5) for v,f in zip(p,factors)) if p[3] else p for p in pixels(src)])
    return result
def matte(src, background):
    dst = Image.new('RGBA', src.size, background)
    dst.alpha_composite(src)
    return dst.convert('RGB')

assert sha(NEW.read_bytes()) == EXPECTED
report = {'zip_sha256': EXPECTED, 'zip_bytes': NEW.stat().st_size, 'scope':'static frozen-package source/composition and seam ownership; no runtime replay', 'base_preserved':[], 'incremental_scripts':[], 'layers':[], 'buildings':[]}
with ZipFile(NEW) as package, ZipFile(OLD) as old:
    entries = [e for e in package.infolist() if not e.is_dir()]
    assert len(entries) == 346 and len({e.filename for e in entries}) == 346
    report['entries'] = len(entries)
    cold = OUT / 'package'
    for entry in entries:
        target = (cold / entry.filename).resolve()
        assert target.is_relative_to(cold.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(package.read(entry))
    for name in ['scripts/ember/building_asset_v001.gd','scripts/ember/building_demo_v001.gd','scripts/ember/building_demo_actor_v001.gd']:
        preserved = package.read(name) == old.read(name)
        assert preserved
        report['base_preserved'].append({'path':name,'same_as_v002':preserved,'sha256':sha(package.read(name))})
    for stem in ['building_asset','building_demo','building_evidence_player']:
        a = f'scripts/ember/{stem}_v002.gd'
        b = f'scripts/ember/{stem}_v003.gd'
        delta = ''.join(difflib.unified_diff(old.read(a).decode('utf-8-sig').splitlines(True), package.read(b).decode('utf-8-sig').splitlines(True), fromfile=a, tofile=b))
        (OUT / f'{stem}_v002_v003.diff').write_text(delta, encoding='utf-8')
        report['incremental_scripts'].append({'old_path':a,'new_path':b,'diff_file':f'{stem}_v002_v003.diff','old_sha256':sha(old.read(a)),'new_sha256':sha(package.read(b))})
    raw = package.read('assets/ember/building_assets_v003/catalog_v003.json')
    catalog = json.loads(raw)
    old_catalog = json.loads(old.read('assets/ember/building_assets_v002/catalog_v002.json'))
    old_specs = {b['id']:b for b in old_catalog['buildings']}
    old_assets = {a['id']:a for a in old_catalog['assets']}
    report['catalog_sha256'] = sha(raw)
    assets = {a['id']:a for a in catalog['assets']}
    for spec in catalog['buildings']:
        size = tuple(map(int,spec['canvas_px']))
        whole, shell, roof, wall = [Image.new('RGBA', size) for _ in range(4)]
        bid = spec['id']
        unchanged_keys = ['canvas_px','pivot_px','footprint_px','wall_height_px','doors','mounts']
        structural_preserved = {key:spec[key] == old_specs[bid][key] for key in unchanged_keys}
        assert all(structural_preserved.values())
        roof_members = []
        wall_members = []
        for recipe in spec['render_layers']:
            entry = assets[recipe['asset']]
            actual = png(package, entry['texture'])
            assert sha(package.read(path(entry['texture']))) == entry['texture_sha256']
            rebuilt = Image.new('RGBA',size)
            for member in entry['source_members']:
                assert sha(package.read(path(member['source_texture']))) == member['source_sha256']
                source = png(package, member['source_texture'])
                x,y,w,h = map(int,member['source_rect_px'])
                mask_paste(rebuilt, source.crop((x,y,x+w,y+h)), tuple(map(int,member['destination_px'])))
                if recipe['group'] == 'Roof': roof_members.append(member)
                if recipe['group'] == 'FrontWall': wall_members.append(member)
            changed = difference(actual,rebuilt)
            assert changed == 0
            report['layers'].append({'id':entry['id'],'source_members':len(entry['source_members']),'rgba_different_pixels':changed})
            if recipe['group'] == 'Roof': mask_paste(roof,actual)
            if recipe['group'] == 'FrontWall': mask_paste(wall,actual)
            visible = recipe['group'] != 'RearShell' and bool(entry['initial_visible'])
            if not visible: continue
            if recipe['kind'] == 'static': mask_paste(shell,actual)
            visual = actual
            if recipe['kind'] == 'lens':
                active = entry['source_asset_id'] == 'lamp_lens_mask' and entry.get('device_id') in {d['id'] for d in spec['doors']}
                visual = tint(actual, (0.72,0.49,0.29,1) if active else (0.32,0.77,0.75,1))
            mask_paste(whole,visual)
        # 切出共享坐标下的接合带：独立屋顶、独立墙体、最终合成，保留圆角所有列。
        px,py = map(int,spec['pivot_px'])
        width = int(spec['footprint_px'][0])
        seam = py-int(spec['wall_height_px'])
        roi = (px-width//2-3,seam-18,px+width//2+3,seam+22)
        sheet = Image.new('RGB', ((roi[2]-roi[0])*4+28,(roi[3]-roi[1])*4*3+78),(242,241,236))
        draw = ImageDraw.Draw(sheet)
        for row,(label,img) in enumerate([('ROOF only',roof),('FRONT WALL only',wall),('COMPLETE',whole)]):
            draw.text((8,row*(160+26)+5),label,fill=(30,36,43))
            part = matte(img.crop(roi),(242,241,236,255)).resize(((roi[2]-roi[0])*4,160),Image.Resampling.NEAREST)
            sheet.paste(part,(14,row*186+24))
        sheet.save(OUT / f'{bid}_seam_source_4x.png')
        whole.save(OUT / f'{bid}_independent_complete.png')
        shell.save(OUT / f'{bid}_independent_shell.png')
        complete_changed = difference(whole,png(package,spec['complete_closed_texture']))
        shell_changed = difference(shell,png(package,spec['fixed_shell_texture']))
        assert complete_changed == shell_changed == 0
        source_ids = [m['source_id'] for m in roof_members+wall_members]
        rear_id = next(r['asset'] for r in spec['render_layers'] if r['group']=='RearShell')
        rear = assets[rear_id]
        old_rear = old_assets[rear_id]
        rear_pixels_unchanged = difference(png(package,rear['texture']),png(old,old_rear['texture'])) == 0
        assert rear_pixels_unchanged
        # 外轮廓按相同世界坐标逐行记录，定位两侧相接处向内再外的轮廓变化。
        outline = []
        for y in range(seam-9,seam+13):
            visible = [x for x in range(size[0]) if whole.getpixel((x,y))[3]]
            outline.append({'canvas_y':y,'left_x':min(visible),'right_x':max(visible)})
        report['buildings'].append({'id':bid,'canvas_px':list(size),'seam_canvas_y':seam,'seam_roi':list(roi),'complete_rgba_different_pixels':complete_changed,'shell_rgba_different_pixels':shell_changed,'unchanged_structural_fields':structural_preserved,'rear_shell_rgba_unchanged_vs_v002':rear_pixels_unchanged,'rear_shell_source_members':rear['source_members'],'seam_outline_rows':outline,'roof_source_members':roof_members,'wall_source_members':wall_members,'source_ids':source_ids})
    assert len(report['layers']) == 41
report['static_composition_status'] = 'PASS_41_LAYERS_AND_6_MAIN_PNGS'
report['art_status'] = 'NEEDS_REVISION_USER_CORNER_SEAM_FEEDBACK'
(OUT / 'composition-evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':report['static_composition_status'],'entries':report['entries'],'layers':len(report['layers']),'buildings':[{k:v for k,v in b.items() if k in ['id','seam_canvas_y','complete_rgba_different_pixels','shell_rgba_different_pixels']} for b in report['buildings']]},ensure_ascii=False))
