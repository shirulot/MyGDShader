"""Bind the old frozen collect knee pixels to previously rendered TA evidence."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image
import hashlib,json

base=Path(__file__).resolve().parent
root=base.parents[3]
old=root/'art-source/ember/ta-review-v001/robot-v011-phase-c2-rc01-independent/visual-package'
fixed=root/'art-source/ember/robot-eight-way-v011/review/phase-c2-rc02'
archive=root/'art-source/ember/deliveries/robot_eight_way_v011_phase_c2_rc02_2026-10-07.zip'
sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha(archive.read_bytes())=='64a3a18625dccc2fc1bde35ae44388a7acfb92ddb9aa4c83db811d2e5c10aa1b'
roi=(12,56,50,82)
report={'scope':'old accepted collect only; no v012 candidate inspection',
        'zip_sha256':sha(archive.read_bytes()),'leg_roi_half_open':roi,'frames':{},'directions':{}}
with ZipFile(archive) as z:
    meta=json.loads(z.read('full-action-metadata.json'))
    for clip in meta['clips']:
        if clip['action']!='collect':continue
        images=[]
        for item in clip['frames']:
            data=z.read(item['file']);im=Image.open(BytesIO(data)).convert('RGBA')
            assert sha(data)==item['sha256']
            assert data==(fixed/item['file']).read_bytes()
            prev=Image.open(old/item['file']).convert('RGBA')
            assert im.crop(roi).tobytes()==prev.crop(roi).tobytes()
            images.append(im)
            report['frames'][item['file']]={'sha256':sha(data),'rc01_leg_roi_rgba_same':True,
                'whole_png_same_as_rc01':data==(old/item['file']).read_bytes()}
        a,b=images[1].crop(roi),images[2].crop(roi)
        changed=[(x+roi[0],y+roi[1]) for y in range(a.height) for x in range(a.width) if a.getpixel((x,y))!=b.getpixel((x,y))]
        report['directions'][clip['direction']]={'f01_f02_lower_roi_changed_pixels':len(changed),
            'f01_f02_lower_roi_changed_xy':changed,'f00_f03_rgba_same':images[0].tobytes()==images[3].tobytes()}
(base/'triage-binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'frames':len(report['frames']),'directions':report['directions']}))
