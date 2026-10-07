"""独立候选包核验；只读生产图，写TA证据目录。"""
from pathlib import Path
import hashlib,json,zipfile,io,shutil
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SOURCE=ROOT/'art-source/ember/human-ac-expanded-v003'
OLD=ROOT/'art-source/ember/human-ac-basic-v002'
sha=lambda b:hashlib.sha256(b).hexdigest()
errors=[]
def check(ok,label):
    if not ok:errors.append(label)
package=SOURCE/'human-ac-expanded-v003-review.zip'
check(sha(package.read_bytes())=='ae1496c795dbbb11b512694ab11710f4a3cf2301da7bc963c7d098f9cc81290f','ZIP SHA')
count=preserved=0
with zipfile.ZipFile(package) as z:
    check(z.testzip() is None,'ZIP CRC')
    checksums=json.loads(z.read('checksums.json'))
    for path,h in checksums.items():
        name=path.replace('\\','/')
        check(sha(z.read(name))==h,'manifest '+name)
        check((SOURCE/name).read_bytes()==z.read(name),'worktree '+name)
    catalog=json.loads(z.read('catalog.json'))
    clips=catalog['clips']
    check(len(clips)==58 and len({c['key'] for c in clips})==58,'unique clip count')
    for c in clips:
        check(c['cell']==[64,96] and c['root']==[32,80],'registration '+c['key'])
        atlas=Image.open(io.BytesIO(z.read(c['atlas']))).convert('RGBA')
        check(atlas.size==(64*c['frame_count'],96),'atlas '+c['key'])
        for i in range(c['frame_count']):
            name=f"frames/{c['key']}/f{i:02d}.png"
            raw=z.read(name);im=Image.open(io.BytesIO(raw)).convert('RGBA')
            check(im.size==(64,96),'frame size '+name)
            check(set(im.getchannel('A').getdata())<={0,255},'alpha '+name)
            check(im.tobytes()==atlas.crop((i*64,0,(i+1)*64,96)).tobytes(),'atlas/frame '+name)
            if c.get('source_version')=='v002 unchanged':
                old=OLD/f"frames/{c['character']}-{c['action']}/f{i:02d}.png"
                check(old.read_bytes()==raw,'old preserved '+name);preserved+=1
            count+=1
    check(count==456 and preserved==40,'frame counts')
    for name in ['README.md','catalog.json','qa/review.json','qa/player-check.json']:
        p=HERE/'submitted'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
    viewed=['A-walk-down_right-4x-light.png','A-idle-down_right-4x-dark.png','C-walk-up_right-4x-light.png','C-run-down_left-4x-light.png','C-idle-down-4x-light.png','C-idle-down_right-4x-light.png','C-walk-down_right-4x-light.png']
    for name in viewed:
        (HERE/name).write_bytes(z.read('qa/'+name))
oldzip=OLD/'human-ac-basic-v002.zip'
check(sha(oldzip.read_bytes())=='5ce1f48b55adb01a2e66cf18b40fbdcc9e1669c05964f7952c5ec725a8aabfa6','old ZIP unchanged')
report=dict(technical_status='PASS' if not errors else 'FAIL',zip_sha256=sha(package.read_bytes()),zip_bytes=package.stat().st_size,manifest_files=len(checksums),clips=len(clips),frames=count,old_frames_byte_exact=preserved,independently_viewed_clips=7,errors=errors,visual_verdict='NEEDS_REVISION',scope='technical package and targeted static visual gate; no whole-set visual pass, browser loop or Godot verification')
(HERE/'technical.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
