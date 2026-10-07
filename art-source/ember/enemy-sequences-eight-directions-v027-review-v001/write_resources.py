"""Write compact portable SpriteFrames referencing byte-exact relative PNG atlases."""
from pathlib import Path
import argparse,json
arg=argparse.ArgumentParser();arg.add_argument('--directory',type=Path,default=Path(__file__).resolve().parent);a=arg.parse_args()
ROOT=a.directory.resolve()
assert not (ROOT/'manifest.json').exists(),'Never edit a frozen package'
recipe=json.loads((ROOT/'assembly_recipe.json').read_text(encoding='utf-8'))
sizes={}
for unit in recipe['units']:
    clips=[c for c in recipe['clips'] if c['unit']==unit]
    assert len(clips)==40
    steps=1+len(clips)+sum(c['frame_count'] for c in clips)
    lines=[f'[gd_resource type="SpriteFrames" load_steps={steps} format=3]','']
    for i,c in enumerate(clips):
        # Godot resolves this path against the .tres folder, including after asset installation.
        lines.append(f'[ext_resource type="Texture2D" path="{unit}/{c["action"]}.png" id="tex_{i:02}"]')
    lines.append('');animations=[]
    for i,c in enumerate(clips):
        frames=[]
        for frame in range(c['frame_count']):
            ident=f'frame_{i:02}_{frame:02}'
            lines.extend([f'[sub_resource type="AtlasTexture" id="{ident}"]',f'atlas = ExtResource("tex_{i:02}")',f'region = Rect2({frame*128}, 0, 128, 128)',''])
            frames.append('{"duration": 1.0, "texture": SubResource("'+ident+'")}')
        animations.append('{\n"frames": ['+', '.join(frames)+'],\n"loop": '+str(c['loop']).lower()+',\n"name": &"'+c['action']+'",\n"speed": '+str(float(c['fps']))+'\n}')
    lines.extend(['[resource]','animations = ['+',\n'.join(animations)+']',''])
    p=ROOT/'output'/f'{unit}.tres';p.write_text('\n'.join(lines),encoding='utf-8');sizes[unit]=p.stat().st_size
print(json.dumps(dict(status='WROTE_RELATIVE_PNG_SPRITEFRAMES',bytes=sizes,total_bytes=sum(sizes.values()))))
