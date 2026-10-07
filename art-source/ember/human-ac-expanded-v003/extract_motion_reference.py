"""安全提取公开 CC0 参考，仅作动作研究，保留作者来源。"""
from pathlib import Path
from zipfile import ZipFile
import json
root=Path(__file__).resolve().parent/'references'
with ZipFile(root/'MeleeCharacter.zip') as z:
    names=sorted({n.split('/')[1] for n in z.namelist() if len(n.split('/'))>2})
    print(names)
    out=root/'hormelz'
    for name in z.namelist():
        rel=Path(name)
        if not name.endswith(('.png','.gif','.txt')):continue
        target=(out/rel).resolve()
        assert target.is_relative_to(out.resolve()),name
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
(root/'motion-reference-license.json').write_text(json.dumps({'author':'Hormelz','url':'https://hormelz.itch.io/8-directional-melee-character','license':'CC0 1.0 per author page','purpose':'pose reference only','directions':{'1':'down_left','2':'left','3':'up_left','4':'up','5':'up_right','6':'right','7':'down_right','8':'down'}},indent=2))
