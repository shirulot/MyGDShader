"""小包只读绑定审计；不运行导出器，不使用 GPU，不写生产目录。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from collections import Counter
import hashlib
import json
import math
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
ACTIVE = ROOT/'art-source/ember/enemy-eight-directions-v013/static_preflight_v002_patrol'
ZIP = ROOT/'art-source/ember/deliveries/enemy_patrol_seven_directions_v013_s002_2026-10-06.zip'
BASE = ROOT/'art-source/ember/deliveries/enemy_calibration_v013_c002_2026-10-06.zip'
EXPECTED = '28951089e1403c65f6a8446aed5f049fdba704809175da36a391c6c5fa1e99a1'

def sha(data): return hashlib.sha256(data).hexdigest()
def load(data): return json.loads(data.decode('utf-8-sig'))
def im(data): return Image.open(BytesIO(data)).convert('RGBA')
def arr(data): return np.array(im(data))

assert sha(ZIP.read_bytes()) == EXPECTED
with ZipFile(ZIP) as z, ZipFile(BASE) as baseline:
    assert z.testzip() is None
    files = {n:z.read(n) for n in z.namelist()}
    manifest = load(files['manifest.json'])['files']
    assert len(manifest) == 23 and set(manifest) == set(files)-{'manifest.json'}
    for name,row in manifest.items():
        assert len(files[name]) == row['bytes'] and sha(files[name]) == row['sha256']
    assert all((ACTIVE/name).read_bytes() == data for name,data in files.items())
    copies = {'neutral_down.png':'enemy_patrol/approved_down.png',
        'generated_front.png':'enemy_patrol/generated_front.png',
        'neutral_down_left.png':'enemy_patrol/down_left.png',
        'neutral_down_right.png':'enemy_patrol/down_right.png'}
    assert all(files[n] == baseline.read(old) for n,old in copies.items())
    provenance = load(files['source_provenance.json'])
    for name,row in provenance.items():
        assert sha(files['source/'+name]) == row['sha256']
        assert Path(row['original']).read_bytes() == files['source/'+name]

    reg,cat = load(files['registration.json']),load(files['catalog.json'])
    qa = load(files['native_static_qa.json'])
    assert cat['registration_sha256'] == sha(files['registration.json'])
    assert len(reg['entries']) == len(cat['entries']) == 9 and reg['columns'] == cat['columns'] == 3
    source = arr(files['source/enemy_patrol_remaining_five_v004.png'])
    assert source.shape == (1024,1536,4)
    records = []
    for entry,catentry in zip(reg['entries'],cat['entries']):
        name = entry['key']
        assert name == catentry['key']
        data = files[name+'.png']
        rgba = arr(data)
        assert rgba.shape == (128,128,4) and set(np.unique(rgba[:,:,3])) == {0,255}
        assert catentry['sha256'] == qa[name]['sha256'] == sha(data)
        counts = {str(k):int(v) for k,v in Counter(rgba[:,:,3].ravel()).items()}
        assert counts == qa[name]['alpha_counts']
        ys,xs = np.where(rgba[:,:,3]>0)
        bounds = [int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1]
        assert bounds == qa[name]['bounds']
        record = {'key':name,'sha256':sha(data),'alpha_counts':counts,'bounds':bounds,
            'transparent_rgb_nonzero_pixels':int(((rgba[:,:,3]==0)&np.any(rgba[:,:,:3]!=0,axis=2)).sum())}
        if 'scale' in entry:
            assert entry['scale'] == 52/392 and entry['target_anchor'] == [64,104]
            assert entry['source_sha256'] == sha(files['source/enemy_patrol_remaining_five_v004.png'])
            # JSON 重存时的小数末位舍入不会被当成注册改变。
            for field in ['source_rect','source_anchor','target_anchor']:
                assert catentry['registration'][field] == entry[field]
            assert abs(catentry['registration']['scale']-entry['scale']) < 1e-14
            exact_coverage_diff,exact_visible_rgb_diff = 0,0
            boundary_cases,nonboundary_onecode,unexplained = 0,0,[]
            for y in range(128):
                for x in range(128):
                    fx=(x+.5-entry['target_anchor'][0])/entry['scale']+entry['source_anchor'][0]
                    fy=(y+.5-entry['target_anchor'][1])/entry['scale']+entry['source_anchor'][1]
                    sx,sy=math.floor(fx),math.floor(fy)
                    target=rgba[y,x].astype(int)
                    # 标准 Nearest 的整数 texel 边界，在浮点 GPU 中可落在任一侧。
                    cx=[round(fx)-1,round(fx)] if abs(fx-round(fx))<1e-7 else [sx]
                    cy=[round(fy)-1,round(fy)] if abs(fy-round(fy))<1e-7 else [sy]
                    def sample(ix,iy):
                        if not(0<=ix<512 and 0<=iy<512): return np.zeros(4,dtype=int)
                        return source[iy+entry['source_rect'][1],ix+entry['source_rect'][0]].astype(int)
                    first=sample(sx,sy)
                    coverage_same=(first[3]>=128)==(target[3]>0)
                    if not coverage_same: exact_coverage_diff+=1
                    delta=int(np.max(np.abs(first[:3]-target[:3]))) if first[3]>=128 and target[3] else 0
                    if first[3]>=128 and target[3] and delta: exact_visible_rgb_diff+=1
                    if coverage_same and delta==0: continue
                    matches=[]
                    for iy in cy:
                        for ix in cx:
                            value=sample(ix,iy)
                            if (value[3]>=128)==(target[3]>0) and (not target[3] or np.max(np.abs(value[:3]-target[:3]))<=1):
                                matches.append((ix,iy))
                    if not matches: unexplained.append([x,y])
                    elif not coverage_same or delta>1: boundary_cases+=1
                    elif len(cx)==len(cy)==1: nonboundary_onecode+=1
            assert not unexplained
            record['source_mapping']={'fixed_scale':entry['scale'],'source_anchor':entry['source_anchor'],
                'target_anchor':entry['target_anchor'],'source_rect':entry['source_rect'],
                'ideal_floor_coverage_differences':exact_coverage_diff,
                'ideal_floor_visible_rgb_pixel_differences':exact_visible_rgb_diff,
                'differences_accounted_by_integer_texel_boundary_sampling':boundary_cases,
                'nonboundary_rgb_one_code_value_pixels':nonboundary_onecode,
                'unexplained_source_samples':unexplained}
        records.append(record)

    contacts = []
    for color in ['white','black']:
        composed = Image.new('RGBA',(384,384),color)
        for i,entry in enumerate(reg['entries']):
            composed.alpha_composite(im(files[entry['key']+'.png']),((i%3)*128,(i//3)*128))
        for factor in [1,4]:
            expected = composed.resize((384*factor,384*factor),Image.Resampling.NEAREST)
            name=f'comparison_{color}_{factor}x.png'
            assert expected.tobytes() == im(files[name]).tobytes()
            contacts.append({'file':name,'independent_composition_full_rgba_difference':0,'sha256':sha(files[name])})
    result={'status':'STATIC_SMALL_PACKAGE_BINDING_PASS','zip_sha256':EXPECTED,'zip_bytes':ZIP.stat().st_size,
        'entries':len(files),'manifest_payloads':len(manifest),'crc':'PASS','fixed_snapshot_byte_identical_files':len(files),
        'preserved_c002_pngs':copies,'baseline_zip_sha256':sha(BASE.read_bytes()),
        'source_provenance_original_and_package_identical_files':list(provenance),
        'native_records':records,'contact_reconstruction':contacts,
        'scope':'Static image/source registration audit. No animation, rig, frame support, Godot import or GPU replay acceptance.',
        'source_sampling_contract':'Opaque Alpha >=128 becomes255. Nearest float boundaries may sample either adjacent texel; visible RGB one-code readback quantization disclosed rather than claiming exact CPU/GPU RGBA.'}
    (OUT/'binding.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['status','zip_bytes','entries','manifest_payloads','fixed_snapshot_byte_identical_files']},ensure_ascii=False,indent=2))
    print(json.dumps(records,ensure_ascii=False,indent=2))
