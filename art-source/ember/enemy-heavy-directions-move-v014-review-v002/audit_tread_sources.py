"""Verify every moving tread lookup and confine the v002 change to the N-left window."""
from pathlib import Path
import hashlib
import json
import math
from PIL import Image
ROOT=Path(__file__).resolve().parent
spec=json.loads((ROOT/'rig.json').read_text(encoding='utf-8'))
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
windows=[]
for direction,config in spec['configs'].items():
    source=Image.open(ROOT/config['source'].removeprefix('res://')).convert('RGBA')
    for number,window in enumerate(config['windows']):
        x0,y0=window['origin'];bad=[];samples=0
        for frame in range(8):
            if window['horizontal']:
                points=[(x,y,x0+((x-x0-frame*2*window['sign'])%window['period']),y)
                        for y in range(y0,y0+window['thickness']) for x in range(x0,x0+window['period'])]
            else:
                points=[]
                for x in range(x0,x0+window['cross_width']):
                    top=y0+math.floor((x-x0)*window['shear'])
                    points.extend((x,y,x,top+((y-top-frame*2*window['sign'])%window['period']))
                                  for y in range(top,top+window['period']))
            for x,y,sx,sy in points:
                if source.getpixel((x,y))[3]:
                    samples+=1
                    if source.getpixel((int(sx),int(sy)))[3]!=255:bad.append([frame,x,y,int(sx),int(sy)])
        windows.append(dict(direction=direction,window=number,opaque_target_samples=samples,invalid_source_samples=bad,passed=not bad))
previous=ROOT.parent/'enemy-heavy-directions-move-v014-review-v001'
changed=[];preserved=[]
for clip in catalog['clips']:
    action=clip['action'];folder=Path('output/enemy_tracked_heavy')/action
    if clip['direction']!='up':
        identical=all(sha(ROOT/folder/f'f{i:02}.png')==sha(previous/folder/f'f{i:02}.png') for i in range(8))
        identical=identical and sha(ROOT/folder.with_suffix('.png'))==sha(previous/folder.with_suffix('.png'))
        preserved.append(dict(action=action,all_frames_and_atlas_identical=identical))
        continue
    for index in range(8):
        old=Image.open(previous/folder/f'f{index:02}.png').convert('RGBA')
        new=Image.open(ROOT/folder/f'f{index:02}.png').convert('RGBA')
        coordinates=[];escaped=[]
        for y in range(128):
            for x in range(128):
                if old.getpixel((x,y))!=new.getpixel((x,y)):
                    coordinates.append([x,y])
                    if not(28<=x<44 and 85<=y<101):escaped.append([x,y])
        changed.append(dict(frame=index,changed_pixels=len(coordinates),outside_original_n_left_window=escaped,
                            alpha_identical=old.getchannel('A').tobytes()==new.getchannel('A').tobytes()))
passed=all(x['passed'] for x in windows) and all(x['all_frames_and_atlas_identical'] for x in preserved)
passed=passed and all(not x['outside_original_n_left_window'] and x['alpha_identical'] for x in changed)
report=dict(status='PASS' if passed else 'FAIL',catalog_sha256=sha(ROOT/'output/catalog.json'),
            old_confirmed_invalid_source_samples=33,windows=windows,changed_up_frames=changed,preserved_actions=preserved)
(ROOT/'qa/tread_source_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status=report['status'],invalid_source_samples=sum(len(x['invalid_source_samples']) for x in windows),
                     preserved_actions=len(preserved),changed_up_frames=changed)))
raise SystemExit(0 if passed else 1)
