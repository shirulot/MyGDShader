"""检查交付文件与帧时长，再打包自生成资源。"""
from pathlib import Path
from PIL import Image
import json,zipfile
ROOT=Path(__file__).resolve().parent
report=[]
for ch in ['A','C']:
    for act,n,ms in [('idle',4,180),('walk',8,120),('run',8,80)]:
        key=f'{ch}-{act}';paths=sorted((ROOT/'frames'/key).glob('*.png'));assert len(paths)==n
        for p in paths:
            im=Image.open(p);assert im.size==(64,96);assert set(im.getchannel('A').getdata())<={0,255}
        for speed,mult in [('normal',1),('slow',3)]:
            gif=Image.open(ROOT/'previews'/f'{key}-{speed}.gif');assert gif.n_frames==n
            durations=[]
            for i in range(gif.n_frames):gif.seek(i);durations.append(gif.info['duration'])
            assert durations==[ms*mult]*n,(key,durations)
        report.append({'clip':key,'frames':n,'duration_ms':ms,'checks':'PASS'})
(ROOT/'qa/delivery-check.json').write_text(json.dumps(report,indent=2))
out=ROOT/'human-ac-basic-v001.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.rglob('*'):
        if p.is_file() and p.suffix!='.zip' and '__pycache__' not in p.parts:z.write(p,p.relative_to(ROOT))
with zipfile.ZipFile(out) as z:assert z.testzip() is None
print(json.dumps({'clips':len(report),'frames':sum(r['frames'] for r in report),'zip_bytes':out.stat().st_size,'zip_integrity':'PASS'}))
