"""重排作者现有动作帧供姿态对照，不合成动作或绘制角色。"""
from pathlib import Path
from PIL import Image
import json
root=Path(__file__).resolve().parent/'references'
dirs=['down_left','left','up_left','up','up_right','right','down_right','down']
report=[]
for action,folder in [('walk','WalkFoward'),('run','RunForward'),('idle','Idle1'),('push','Push'),('pull','Pull')]:
    for number,direction in enumerate(dirs,1):
        files=list((root/'hormelz'/'MeleeCharacter'/folder).glob(f'*_dir{number}.png'))
        if not files:continue
        im=Image.open(files[0]).convert('RGBA');w,h=im.size
        assert w%126==0 and h%132==0,(files[0],im.size)
        frames=[]
        for y in range(0,h,132):
            for x in range(0,w,126):
                frame=im.crop((x,y,x+126,y+132))
                if frame.getbbox():frames.append(frame)
        sample=[i*len(frames)//8 for i in range(8)]
        out=Image.new('RGBA',(504,264))
        for i,j in enumerate(sample):out.paste(frames[j],((i%4)*126,(i//4)*132))
        out.resize((1512,792),Image.Resampling.NEAREST).save(root/f'pose-{action}-{direction}.png')
        report.append({'action':action,'direction':direction,'source':str(files[0].relative_to(root)),'source_frames':len(frames),'sampled_indices':sample})
(root/'pose-reference-catalog.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report[:3]))
