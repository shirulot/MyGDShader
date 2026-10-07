"""检查路径图块内部是否真的连通，防止只对齐最外一行像素的假接缝。"""
from collections import deque
from pathlib import Path
import json
import argparse
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--revision',default='v006',choices=['v006','v007'])
args = parser.parse_args()
OUT = ROOT/f'assets/ember/environment/autotiles_{args.revision}'
catalog = json.loads((OUT/'catalog.json').read_text())
size = catalog['tile_size']
report = {'checked_tiles':0,'failures':[]}
for atlas in catalog['atlases']:
    if atlas['mode'] != 'sides':
        continue
    image = Image.open(ROOT/atlas['texture'].removeprefix('res://')).convert('RGBA')
    for entry in atlas['tiles']:
        x,y = entry['coord']
        tile = image.crop((x*size,y*size,(x+1)*size,(y+1)*size))
        opaque = {(px,py) for py in range(size) for px in range(size) if tile.getpixel((px,py))[3] > 127}
        components = []
        while opaque:
            seed = opaque.pop()
            queue, component = deque([seed]), {seed}
            while queue:
                px,py = queue.popleft()
                for neighbor in [(px-1,py),(px+1,py),(px,py-1),(px,py+1)]:
                    if neighbor in opaque:
                        opaque.remove(neighbor)
                        component.add(neighbor)
                        queue.append(neighbor)
            components.append(component)
        main = max(components,key=len) if components else set()
        # 检查完整端口宽度：栈桥中间是透空格栅、栏杆是双梁，不能
        # 假设中央必须有实心板。主体连通域要真正抵达每一个开放端。
        for side in range(4):
            if not entry['mask'] & (1 << side):
                continue
            port = [(p,0) if side == 0 else (size-1,p) if side == 1 else (p,size-1) if side == 2 else (0,p)
                    for p in range(size)]
            if sum(p in main for p in port) < 4:
                report['failures'].append({'atlas':atlas['id'],'mask':entry['mask'],'side':side})
        report['checked_tiles'] += 1
(OUT/'port_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
assert not report['failures']
