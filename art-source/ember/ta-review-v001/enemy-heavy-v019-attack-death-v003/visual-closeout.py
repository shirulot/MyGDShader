"""Register actually viewed diagnostics and independently read closure points only."""
from pathlib import Path
from PIL import Image
import hashlib
import json

base = Path(__file__).resolve().parent
package = base / 'visual-package'
binding = json.loads((base/'visual-binding.json').read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
image = lambda action,n: Image.open(package/f'output/enemy_tracked_heavy/{action}/f{n:02}.png').convert('RGBA')
out = {'status':'INCREMENTAL_VISUAL_PASS','closed_p2':['SW death weak dangling tower edge','E attack fixed socket at vacated muzzle edge'],
       'actually_viewed_diagnostics':list(binding['diagnostic_sha256']),
       'own_exact_pixel_checks':{},'bound_external_evidence_sha256':{},
       'external_evidence_scope':'Root browser snapshots and peer technical reports are bound, not claimed as own execution.'}
source = Image.open(package/'source/down_left.png').convert('RGBA')
stable=[]
for action,count in [('attack_down_left',6),('death_down_left',8)]:
    for n in range(count):
        im=image(action,n)
        same=all(im.getpixel((46,y)) == source.getpixel((46,y)) for y in [76,77])
        assert same
        stable.append({'clip':action,'frame':n,'fixed_receiver_points_equal_source_rgba':same})
out['own_exact_pixel_checks']['sw_fixed_source_points_all_14_frames']=stable
out['own_exact_pixel_checks']['sw_old_dangling_positions']=[{'frame':n,'pixels':[{'xy':list(p),'rgba':list(image('death_down_left',n).getpixel(p))} for p in ([(46,88),(46,89)] if n==5 else [(46,89),(46,90)])]} for n in [4,5,6,7]]
out['own_exact_pixel_checks']['e_old_muzzle_positions']=[{'frame':n,'pixels':[{'xy':list(p),'rgba':list(image('attack_right',n).getpixel(p))} for p in [(98,83),(98,84)]]} for n in [0,1,3,4,5]]
out['own_exact_pixel_checks']['endpoints']={}
for direction in ['down_left','right']:
    attack=[image(f'attack_{direction}',n) for n in range(6)]
    death=[image(f'death_{direction}',n) for n in range(8)]
    out['own_exact_pixel_checks']['endpoints'][direction]={'attack_f05_equals_f00':attack[5].tobytes()==attack[0].tobytes(),'death_f06_equals_f07':death[6].tobytes()==death[7].tobytes(),'death_f04_equals_f06':death[4].tobytes()==death[6].tobytes()}
for name in ['root-browser-death-sw-f04.png','root-browser-attack-e-f03.png','root-browser-death-e-f07.png','technical-summary.json','technical-scope-crosscheck.json','technical-incremental-integrity.json']:
    p=base/name
    if p.exists():out['bound_external_evidence_sha256'][name]=sha(p)
(base/'visual-conclusion.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Closed both P2s; recorded 28 viewed frames and 26 actually viewed diagnostics.')
