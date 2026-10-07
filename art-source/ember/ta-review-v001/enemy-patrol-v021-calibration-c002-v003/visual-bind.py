"""Read the frozen C002 ZIP and produce independent static identity diagnostics."""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from io import BytesIO
from PIL import Image, ImageDraw
import hashlib, json
import numpy as np

base=Path(__file__).resolve().parent
root=base.parents[3]
package=base/'visual-package'
deliveries=root/'art-source/ember/deliveries'
archive=deliveries/'enemy_patrol_profile_calibration_v021_c002_v003_2026-10-07.zip'
previous=deliveries/'enemy_patrol_profile_moves_v021_v001_2026-10-07.zip'
original=deliveries/'enemy_patrol_seven_directions_v013_s002_2026-10-06.zip'
sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha(archive.read_bytes())=='87d0ecf437c93451eddcdad59387f6f03191efcdfdfa1cb197b6e41e819f4ab2'
assert sha(previous.read_bytes())=='4c907f50f6851787d84e7212a0cd7c64215566baf482a520fde937212db10b61'
assert sha(original.read_bytes())=='28951089e1403c65f6a8446aed5f049fdba704809175da36a391c6c5fa1e99a1'
with ZipFile(archive) as z:
    assert z.testzip() is None
    entries=[i for i in z.infolist() if not i.is_dir()]
    assert len({i.filename.casefold() for i in entries})==len(entries)
    for entry in entries:
        rel=PurePosixPath(entry.filename)
        assert not rel.is_absolute() and '..' not in rel.parts and ':' not in entry.filename and '\\' not in entry.filename
        p=package.joinpath(*rel.parts)
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(z.read(entry))
manifest=json.loads((package/'manifest.json').read_text(encoding='utf-8-sig'))
assert {entry.filename for entry in entries}==set(manifest['files'])|{'manifest.json'}
fixed=root/'art-source/ember/enemy-patrol-profile-calibration-v021-c002-review-v003'
for n,entry in manifest['files'].items():
    data=(package/n).read_bytes()
    assert sha(data)==entry['sha256'] and len(data)==entry['bytes']
    assert data==(fixed/n).read_bytes()
spec=json.loads((package/'calibration.json').read_text(encoding='utf-8-sig'))
report={'scope':'two-direction static source, actual pieces and neutral identity; zero new animation clips',
        'zip_sha256':sha(archive.read_bytes()),'bytes':archive.stat().st_size,'members':len(entries),
        'payload':len(manifest['files']),'manifest_sha256':sha((package/'manifest.json').read_bytes()),
        'calibration_sha256':sha((package/'calibration.json').read_bytes()),'manifest_pass':True,
        'fixed_directory_payload_bytes_equal_zip':True,
        'directions':{},'diagnostics':{}}
images={}
with ZipFile(previous) as old,ZipFile(original) as src:
    for d in ['left','right']:
        assert (package/f'source/{d}.png').read_bytes()==src.read(f'neutral_{d}.png')==old.read(f'source/{d}.png')
        pics={name:Image.open(package/path).convert('RGBA') for name,path in {
            'source':f'source/{d}.png','candidate':f'output/neutral_{d}.png',
            'near':f'output/{d}_near.png','far':f'output/{d}_far.png','body':f'output/{d}_body.png'}.items()}
        pics['P21_v001']=Image.open(BytesIO(old.read(f'qa/bind_{d}.png'))).convert('RGBA')
        assert all(im.size==(128,128) and set(im.getchannel('A').tobytes())=={0,255} for im in pics.values())
        # Use the actual delivered pieces in their original canvas and rendering order.
        assembled=Image.new('RGBA',(128,128))
        for part in ['far','near','body']:assembled.alpha_composite(pics[part])
        assembled_a=np.array(assembled);candidate_a=np.array(pics['candidate'])
        assert np.array_equal(assembled_a[:,:,3],candidate_a[:,:,3])
        assert np.array_equal(assembled_a[candidate_a[:,:,3]>0],candidate_a[candidate_a[:,:,3]>0])
        shifted=Image.new('RGBA',(128,128));shifted.alpha_composite(pics['near'],tuple(spec['configs'][d]['offset']))
        shifted_a=np.array(shifted);far_a=np.array(pics['far'])
        assert np.array_equal(shifted_a[:,:,3],far_a[:,:,3])
        assert np.array_equal(shifted_a[far_a[:,:,3]>0],far_a[far_a[:,:,3]>0])
        a,b=np.array(pics['source']),np.array(pics['candidate'])
        diff=np.any(a!=b,axis=2);ys,xs=np.nonzero(diff)
        assert int(diff.sum())=={'left':49,'right':50}[d]
        assert np.array_equal(a[103],b[103])
        x,y=(66,94) if d=='left' else (59,94)
        assert np.array_equal(a[y,x],b[y,x])
        report['directions'][d]={'source_s002_and_p21_bytes_exact':True,
            'source_sha256':sha((package/f'source/{d}.png').read_bytes()),
            'neutral_sha256':sha((package/f'output/neutral_{d}.png').read_bytes()),
            'changed_rgba_pixels':int(diff.sum()),'changed_bbox_inclusive':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],
            'actual_pieces_composite_alpha_and_opaque_rgba_exact':True,
            'far_is_same_direction_near_integer_translation_alpha_and_opaque_rgba_exact':spec['configs'][d]['offset'],
            'transparent_rgb_composite_difference_count':int(np.any(assembled_a!=candidate_a,axis=2).sum()),
            'y103_complete_rgba_exact':True,'y103_opaque_x':np.flatnonzero(b[103,:,3]).tolist(),
            'named_shin_sample':{'xy':[x,y],'original_and_candidate_rgba':b[y,x].tolist()},
            'part_bounds':{name:im.getbbox() for name,im in pics.items()}}
        images[d]=pics

def chart(name,items,cols,roi,scale,bg):
    w,h=(roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale
    pic=Image.new('RGBA',(cols*w,((len(items)+cols-1)//cols)*(h+24)),bg)
    draw=ImageDraw.Draw(pic);ink=(16,16,16,255) if bg[0]>100 else (240,240,240,255)
    for i,(label,im) in enumerate(items):
        x,y=(i%cols)*w,(i//cols)*(h+24)
        draw.text((x+3,y+4),label,fill=ink)
        pic.alpha_composite(im.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
    pic.convert('RGB').save(base/name)
    report['diagnostics'][name]={'sha256':sha((base/name).read_bytes()),'roi_half_open':roi,'scale':scale,'labels':[label for label,_ in items]}

for color,bg in {'light':(236,233,216,255),'dark':(25,42,52,255)}.items():
    comparison=[(f'{d} {name}',images[d][name]) for d in images for name in ['source','P21_v001','candidate']]
    chart(f'visual-identity-{color}-1x.png',comparison,3,[0,0,128,128],1,bg)
    chart(f'visual-identity-{color}-4x.png',comparison,3,[44,44,85,108],4,bg)
    chart(f'visual-leg-identity-{color}-8x.png',comparison,3,[47,75,79,107],8,bg)
    parts=[(f'{d} {name}',images[d][name]) for d in images for name in ['body','near','far','candidate']]
    chart(f'visual-actual-parts-{color}-4x.png',parts,4,[44,44,85,108],4,bg)
    chart(f'visual-actual-leg-parts-{color}-8x.png',parts,4,[47,75,79,107],8,bg)
(base/'visual-binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['bytes','members','payload','directions']},ensure_ascii=False))
