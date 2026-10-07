"""绑定已验收 C23 与候选 C24，检查背向攻击的实际辨识信息。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image,ImageDraw
import hashlib,json
out=Path(__file__).resolve().parent;root=out.parents[3]
sha=lambda b:hashlib.sha256(b).hexdigest()
p23=root/'art-source/ember/deliveries/enemy_cutter_idle_hit_v023_v001_2026-10-07.zip'
p24=root/'art-source/ember/deliveries/enemy_cutter_attack_death_v024_v001_2026-10-07.zip'
assert sha(p23.read_bytes())=='ec2c8806c16271f55ee584749abe0166ac80e00985816150feb2b2369e934973'
assert sha(p24.read_bytes())=='c3c1d9fb84d909fb113ee0a9d7ddac6afa98b8132f669ae0f5be5fa0963d572c'
z23,z24=ZipFile(p23),ZipFile(p24)
def read(z,n):return Image.open(BytesIO(z.read(n))).convert('RGBA')
mapping=[0,1,1,3,0,0];attack=[];idle=[];rows=[]
for i,j in enumerate(mapping):
    p=f'output/enemy_cutter/attack_up/f{i:02}.png';q=f'output/enemy_cutter/idle_up/f{j:02}.png'
    a,b=read(z24,p),read(z23,q);attack.append(a);idle.append(b)
    diffs=[(x,y) for y in range(128) for x in range(128) if a.getpixel((x,y))!=b.getpixel((x,y))]
    rows.append({'attack_frame':i,'matching_idle_frame':j,'rgba_diff_count':len(diffs),'rgba_diff_xy':diffs,'attack_sha256':sha(z24.read(p)),'idle_sha256':sha(z23.read(q))})
for scale,roi in [(1,(0,0,128,128)),(4,(32,65,96,105))]:
    for mode,bg in [('light',(238,238,238,255)),('dark',(8,11,16,255))]:
        w,h=(roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale
        img=Image.new('RGBA',(6*w,2*(h+24)),bg);dr=ImageDraw.Draw(img)
        for r,images in enumerate([attack,idle]):
            for i,a in enumerate(images):
                x,y=i*w,r*(h+24)
                dr.text((x+3,y+3),f'C24 attack F{i:02}' if r==0 else f'C23 idle F{mapping[i]:02}',fill='black' if mode=='light' else 'white')
                img.alpha_composite(a.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
        img.convert('RGB').save(out/f'visual-n-attack-idle-{mode}-{scale}x.png')
(out/'visual-n-attack-idle.json').write_text(json.dumps({'C23_zip_sha256':sha(p23.read_bytes()),'C24_zip_sha256':sha(p24.read_bytes()),'mapping':rows},indent=2),encoding='utf-8')
print(json.dumps(rows))
