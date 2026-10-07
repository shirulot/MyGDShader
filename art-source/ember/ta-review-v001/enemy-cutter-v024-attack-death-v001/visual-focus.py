"""冻结 ZIP 的局部诊断；固定坐标最近邻放大，不改变生产像素。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image,ImageDraw
import hashlib,json
out=Path(__file__).resolve().parent
z=ZipFile(out.parents[3]/'art-source/ember/deliveries/enemy_cutter_attack_death_v024_v001_2026-10-07.zip')
def read(n):return Image.open(BytesIO(z.read(n))).convert('RGBA')
receipt={}
def sheet(name,paths,roi,cols,bg):
    w,h=(roi[2]-roi[0])*8,(roi[3]-roi[1])*8
    a=Image.new('RGBA',(cols*w,((len(paths)+cols-1)//cols)*(h+28)),bg);dr=ImageDraw.Draw(a)
    for i,(label,p) in enumerate(paths):
        x,y=i%cols*w,i//cols*(h+28)
        dr.text((x+3,y+3),label,fill='black' if bg[0]>100 else 'white')
        a.alpha_composite(read(p).crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+28))
    a.convert('RGB').save(out/name)
    receipt[name]={'sha256':hashlib.sha256((out/name).read_bytes()).hexdigest(),'roi_half_open':roi,'scale':8,'inputs':[{ 'label':l,'path':p,'sha256':hashlib.sha256(z.read(p)).hexdigest()} for l,p in paths]}
cases=[('nw-blade','up_left','attack',(76,65,101,101)),('e-blade','right','attack',(69,72,100,108)),('sw-saw','down_left','attack',(29,73,57,105)),('w-claw','left','attack',(29,76,64,105)),('se-saw','down_right','attack',(45,78,75,108)),('ne-rear','up_right','death',(33,65,57,98)),('se-front-left-attack','down_right','attack',(70,71,100,103)),('se-front-left-death','down_right','death',(70,71,100,103)),('se-saw-death','down_right','death',(43,75,75,108))]
for tag,d,act,roi in cases:
    count=6 if act=='attack' else 8
    paths=[(f'{d} source',f'source/{d}.png')]+[(f'{act} F{n:02}',f'output/enemy_cutter/{act}_{d}/f{n:02}.png') for n in range(count)]
    if 'blade' in tag:paths += [('source saw_blade',f'qa/parts/{d}/saw_blade.png'),('source saw arm',f'qa/parts/{d}/saw.png')]
    for mode,bg in [('light',(238,238,238,255)),('dark',(8,11,16,255))]:
        sheet(f'visual-focus-{tag}-{mode}-8x.png',paths,roi,3 if 'blade' in tag or act=='death' else 4,bg)
(out/'visual-focus-binding.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print('Created',len(receipt),'fixed-coordinate diagnostic sheets')
