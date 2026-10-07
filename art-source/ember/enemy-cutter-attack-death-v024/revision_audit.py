"""Compare immutable v001 to the corrected candidate without changing image pixels."""
from pathlib import Path
from PIL import Image
import hashlib,json
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'enemy-cutter-attack-death-v024-review-v001'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
records=[]
for clip in catalog['clips']:
    action=clip['action'];changes=[]
    for i in range(clip['frame_count']):
        rel=Path('output/enemy_cutter')/action/f'f{i:02}.png'
        a,b=Image.open(OLD/rel).convert('RGBA'),Image.open(ROOT/rel).convert('RGBA')
        count=sum(x!=y for x,y in zip(a.getdata(),b.getdata()))
        if count:changes.append(dict(frame=i,rgba_pixels=count))
    required_unchanged=clip['direction'] in ['down','left'] or action=='death_up'
    assert not required_unchanged or not changes,action
    records.append(dict(action=action,changed_frames=changes,required_unchanged=required_unchanged))
source_equal={p.name:sha(p)==sha(OLD/'source'/p.name) for p in (ROOT/'source').glob('*.png')}
assert all(source_equal.values())
report=dict(status='PASS',catalog_sha256=sha(ROOT/'output/catalog.json'),previous_zip_sha256='c3c1d9fb84d909fb113ee0a9d7ddac6afa98b8132f669ae0f5be5fa0963d572c',
    source_png_unchanged=source_equal,records=records,
    fixes=['Five visible saw discs registered to actual source gold hubs; full fixed-source disc contours assigned to saw_blade.',
           'N attack uses rigid brace, short release and recovery around body pivot, with fixed feet and hidden tools retained.',
           'SE real foot landmarks separated from previous joint metadata; front_left socket documented as 1 brown opaque pixel plus 3 transparent.'],
    ownership_notes=['NW source (80,76) changes front_right to saw_blade and (82,87) rear_right to saw_blade; both belong to the visible disc edge.',
                     'Source RGB and PNG bytes unchanged; no per-frame repaint or added disc pixels.'],
    limits='Author checks are not independent TA approval. Foot transforms may be occluded. Old down attack retains original y=108 extent.')
(ROOT/'qa/revision_v002.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status='PASS',changed_frames=sum(len(r['changed_frames']) for r in records),changed_pixel_events=sum(c['rgba_pixels'] for r in records for c in r['changed_frames']))))
