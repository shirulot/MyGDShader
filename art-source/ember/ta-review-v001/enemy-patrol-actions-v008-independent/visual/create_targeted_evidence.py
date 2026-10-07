"""固定 common ROI 的差异帧原生/4倍对照；只写审查图。"""
import io,json
from pathlib import Path
from zipfile import ZipFile
from PIL import Image,ImageDraw
workspace=Path('E:/dev/shader/godot-shader/godot-shader-simple')
review=workspace/'art-source/ember/ta-review-v001/enemy-patrol-actions-v008-independent/visual'
targets={
    'attack_down':('enemy_patrol_actions_v006_2026-10-06.zip','attack_down_v006.png',[2,3]),
    'death_down':('enemy_patrol_actions_v006_2026-10-06.zip','death_down_v006.png',[4,5,6,7]),
    'move_down':('enemy_patrol_move_v004_r1_2026-10-06.zip','move_down_v004.png',[0,1,2,5,7]),
    'hit_down':('enemy_patrol_actions_v005_2026-10-06.zip','hit_down_v005.png',[2]),
}
for action,(zipname,atlas_name,frames) in targets.items():
    with ZipFile(workspace/'art-source/ember/deliveries'/zipname) as package:
        atlas=Image.open(io.BytesIO(package.read('output/'+atlas_name))).convert('RGBA')
    for background_name,color in [('light',(242,242,232)),('dark',(30,38,46))]:
        sheet=Image.new('RGB',(88*len(frames),2*100),color)
        draw=ImageDraw.Draw(sheet)
        for col,index in enumerate(frames):
            old=atlas.crop((index*128+32,32,index*128+120,112))
            current=Image.open(review/f'package/output/{action}/f{index:02d}.png').convert('RGBA').crop((32,32,120,112))
            for row,label,frame in [(0,'old',old),(1,'v008',current)]:
                x,y=col*88,row*100
                sheet.paste(frame,(x,y+20),frame)
                draw.text((x+3,y+3),f'{label} f{index:02d}',fill=(225,225,225) if background_name=='dark' else (25,25,25))
        sheet.save(review/f'{action}_targeted_{background_name}_1x.png')
        sheet.resize((sheet.width*4,sheet.height*4),Image.Resampling.NEAREST).save(review/f'{action}_targeted_{background_name}_4x.png')
print('TARGETED_EVIDENCE_READY')
