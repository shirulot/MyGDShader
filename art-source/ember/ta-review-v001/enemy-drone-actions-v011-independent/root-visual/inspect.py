"""Read the frozen candidate; create review-only, fixed-ROI contact sheets."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import zipfile
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[4]
ZIP = PROJECT / 'art-source/ember/deliveries/enemy_drone_actions_v011_2026-10-06.zip'
ROI = (24, 40, 104, 112)
binding = {'zip_sha256': hashlib.sha256(ZIP.read_bytes()).hexdigest(), 'roi': ROI, 'files': []}
assert binding['zip_sha256'] == '13a4942d34d0ceabac7473c1689aa4784bc0c6f1555ff68817ed9d93159dab3e'
with zipfile.ZipFile(ZIP) as archive:
    names = archive.namelist()
    for action in ('idle_down', 'move_down', 'attack_down', 'hit_down', 'death_down'):
        paths = sorted(n for n in names if n.startswith('output/' + action + '/') and n.endswith('.png'))
        assert len(paths) in (4, 6, 8)
        for scale in (1, 4):
            for theme, background in (('light', '#ffffff'), ('dark', '#182631')):
                cell_w, cell_h = 80 * scale, 72 * scale + 20
                cols = 4
                sheet = Image.new('RGB', (cols * cell_w, ((len(paths)+3)//4) * cell_h), background)
                draw = ImageDraw.Draw(sheet)
                for i, name in enumerate(paths):
                    raw = archive.read(name)
                    frame = Image.open(BytesIO(raw)).convert('RGBA')
                    # Inspect the fixed region, but prove no visible pixels were omitted.
                    visible = frame.getchannel('A').getbbox()
                    assert visible and visible[0] >= ROI[0] and visible[1] >= ROI[1] and visible[2] <= ROI[2] and visible[3] <= ROI[3]
                    crop = frame.crop(ROI).resize((80*scale, 72*scale), Image.Resampling.NEAREST)
                    x, y = (i % cols)*cell_w, (i // cols)*cell_h
                    sheet.paste(crop, (x, y+20), crop)
                    draw.text((x+3,y+3), f'{action} f{i:02d}', fill='#101820' if theme == 'light' else '#ece9d8')
                    if scale == 1 and theme == 'light':
                        binding['files'].append({'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'visible_bbox':visible})
                out = ROOT / f'{action}_{theme}_{scale}x.png'
                sheet.save(out)
                binding.setdefault('contacts',[]).append({'path':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
    for name in ('source/canonical.png','source/rotor_well_master.png','source/rotor_well_prompt.txt'):
        raw = archive.read(name)
        (ROOT / Path(name).name).write_bytes(raw)
        binding['files'].append({'path':name,'sha256':hashlib.sha256(raw).hexdigest()})
(ROOT / 'image-binding.json').write_text(json.dumps(binding,indent=2),encoding='utf-8')
print(json.dumps({'zip_sha256':binding['zip_sha256'],'frame_count':30,'contacts':len(binding['contacts']),'omitted_visible_pixels':0}))
