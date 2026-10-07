"""用已验收PNG做统一2倍比例板；不重绘或改写任何生产像素。"""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
OUT = ROOT/'art-source/ember/references/full_native_scale_v003.png'
PALETTE = ['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','7B4D35','B77C4B',
           'E2B77A','51C5C2','E5A44B','E65B4A','566B78','203A4B','406B78','ECE9D8']

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    catalog = json.loads((ROOT/'assets/ember/ember_additional_catalog_v001.json').read_text(encoding='utf-8'))
    items = {a['id']:a for a in catalog['assets']}
    image = Image.new('RGB',(1536,1024),'#182631')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24)
    small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    draw.text((32,24),'余烬采能站 · 完整原生比例验收 R01',font=font,fill='#BECBC4')
    draw.text((32,64),'以下对象统一 Nearest 2×；共用接地点基线，未分别缩放设备或机器人。',font=small,fill='#829BA3')
    baseline = 560
    draw.line((32,baseline,1504,baseline),fill='#4D6470',width=2)
    records = []
    entries = [
        ('robot','机器人',210,'assets/ember/characters/robot/robot_idle_down_v001.png',[32,80]),
        ('station','采能站',510,'assets/ember/buildings/station/station_base_v001.png',[64,144]),
        ('door_closed','关闭门',820,items['door_closed']['file'].removeprefix('res://'),[48,112]),
        ('door_open','开启门',1060,items['door_open']['file'].removeprefix('res://'),[48,112]),
        ('console_base','控制台',1350,items['console_base']['file'].removeprefix('res://'),[48,80]),
    ]
    for identifier,label,x,relative,anchor in entries:
        path = ROOT/relative
        with Image.open(path) as raw:
            patch = raw.convert('RGBA').resize((raw.width*2,raw.height*2),Image.Resampling.NEAREST)
            origin = (x-anchor[0]*2,baseline-anchor[1]*2)
            image.paste(patch,origin,patch)
            records.append({'id':identifier,'file':relative,'sha256':digest(path),
                            'canvas':list(raw.size),'anchor':anchor,'scale':2,'board_origin':list(origin)})
            draw.text((x-90,baseline+52),label,font=font,fill='#BECBC4')
            draw.text((x-95,baseline+90),f'{raw.width}×{raw.height} · {anchor[0]}/{anchor[1]}',font=small,fill='#829BA3')
    atlas_path = ROOT/'assets/ember/environment/tilesets/ground_details_v001.png'
    with Image.open(atlas_path) as atlas:
        for index,label in enumerate(['整洁','磨损','格栅','湿面']):
            patch = atlas.crop((index*32,0,index*32+32,32)).resize((64,64),Image.Resampling.NEAREST)
            image.paste(patch,(80+index*152,726))
            draw.text((80+index*152,800),label,font=small,fill='#BECBC4')
    records.append({'id':'floor_clean_worn_grate_wet','file':atlas_path.relative_to(ROOT).as_posix(),
                    'sha256':digest(atlas_path),'native_tile':[32,32],'scale':2})
    draw.text((32,686),'四种地板：32×32 原生瓦片，与上方对象使用同一像素尺度',font=small,fill='#829BA3')
    for index,color in enumerate(PALETTE):
        x = 34+index*93
        draw.rectangle((x,900,x+70,930),fill='#'+color)
        draw.text((x,940),color,font=small,fill='#BECBC4')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    image.save(OUT)
    proof = {'status':'R01_COMPLETE_NATIVE_SCALE_BOARD_VISUAL_REQUIRED','file':OUT.relative_to(ROOT).as_posix(),
             'sha256':digest(OUT),'canvas':[1536,1024],'uniform_scale':2,
             'baseline_y':baseline,'sources':records,'art_units_added':0,'production_png_modified':False}
    OUT.with_suffix('.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'reference':proof['file'],'sha256':proof['sha256'],'new_art_units':0}))

if __name__=='__main__':
    main()
