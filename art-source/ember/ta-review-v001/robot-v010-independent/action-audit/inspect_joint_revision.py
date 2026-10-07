"""独立绑定 v010 导出帧，比较冻结 v009；只在审查目录写结果和最近邻图。"""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
from PIL import Image, ImageDraw

workspace = Path('E:/dev/shader/godot-shader/godot-shader-simple')
source = workspace / 'art-source/ember/robot-joint-repair-v010'
review = workspace / 'art-source/ember/ta-review-v001/robot-v010-independent/action-audit'
snapshot = review / 'snapshot'
sha = lambda data: hashlib.sha256(data).hexdigest()
snapshot.mkdir(parents=True,exist_ok=True)
export_bytes = (source / 'qa/export_validation_v010.json').read_bytes()
export = json.loads(export_bytes)
assert export['status'] == 'TECHNICAL_EXPORT_PASS' and export['cell'] == [64,96] and export['fps'] == 8
(snapshot / 'export_validation_v010.json').write_bytes(export_bytes)
manifest_bytes = (source / 'run-manifest.json').read_bytes()
manifest = json.loads(manifest_bytes)
(snapshot / 'run-manifest.json').write_bytes(manifest_bytes)
ledger_bytes = (source / 'qa/local_composite_v010.json').read_bytes()
ledger = json.loads(ledger_bytes)
(snapshot / 'local_composite_v010.json').write_bytes(ledger_bytes)
archive = workspace / 'art-source/ember/deliveries/robot_fixed_rig_v009_foot_revision_candidate_2026-10-06.zip'
assert sha(archive.read_bytes()) == '1abc164e76abc5e7f59978ae0d3062d07b37bd6edfe55c69335ec3f61318c60f'

before,after,frame_results = [],[],[]
with ZipFile(archive) as package:
    prefix = 'robot-fixed-rig-v009/'
    rig = json.loads(package.read(prefix+'source/rig_down_v009.json'))
    protected = {i+1:p['id'] for i,p in enumerate(rig['parts']) if p['id'] in ['head','chest_shell','left_wrist_tool','hand_left','hand_right']}
    for row in export['frames']:
        frame = row['frame']
        filename = f'robot_walk_down_f{frame:02d}'
        old_bytes = package.read(prefix+f'frames/{filename}_v009.png')
        new_bytes = (source / row['file']).read_bytes()
        assert sha(new_bytes) == row['sha256'] == manifest['frozen_frames'][frame]['sha256'] == ledger['frames'][frame]['output_sha256']
        assert sha(old_bytes) == ledger['frames'][frame]['source_v009_sha256']
        assert old_bytes == (source / f'source/reference-v009/frames/{filename}_v009.png').read_bytes()
        for version,data in [('v009',old_bytes),('v010',new_bytes)]:
            dest = snapshot / f'{filename}_{version}.png'
            dest.write_bytes(data)
        a=Image.open(snapshot/f'{filename}_v009.png').convert('RGBA')
        b=Image.open(snapshot/f'{filename}_v010.png').convert('RGBA')
        assert a.size == b.size == (64,96)
        before.append(a);after.append(b)
        owner_bytes = package.read(prefix+f'owner_maps/walk_down_f{frame:02d}_owner_v009.png')
        owner_path = snapshot/f'owner_f{frame:02d}_v009.png'
        owner_path.write_bytes(owner_bytes)
        owner=Image.open(owner_path).convert('RGBA')
        ap,bp,op = list(a.get_flattened_data()),list(b.get_flattened_data()),list(owner.get_flattened_data())
        protected_changes = {name:0 for name in protected.values()}
        changed=[];added=removed=0
        for index,(left,right,label) in enumerate(zip(ap,bp,op)):
            if left == right: continue
            if label[0] in protected: protected_changes[protected[label[0]]] += 1
            if left[3] == 0 and right[3] > 0: added += 1
            if left[3] > 0 and right[3] == 0: removed += 1
            changed.append([index%64,index//64])
        assert not any(protected_changes.values())
        assert len(changed) == ledger['frames'][frame]['changed_pixels']
        frame_results.append({'frame':frame,'new_sha256':sha(new_bytes),'old_sha256':sha(old_bytes),'changed_pixels':len(changed),'old_opaque':sum(p[3]>0 for p in ap),'new_opaque':sum(p[3]>0 for p in bp),'added_pixels':added,'removed_pixels':removed,'protected_identity_changed':protected_changes,'changed_bounds':[min(p[0] for p in changed),min(p[1] for p in changed),max(p[0] for p in changed)+1,max(p[1] for p in changed)+1]})

atlas_bytes=(source/'robot_walk_down_atlas_v010.png').read_bytes()
assert sha(atlas_bytes) == manifest['atlas']['sha256']
(snapshot/'robot_walk_down_atlas_v010.png').write_bytes(atlas_bytes)
atlas=Image.open(snapshot/'robot_walk_down_atlas_v010.png').convert('RGBA')
assert atlas.size==(512,96)
assert all(atlas.crop((index*64,0,(index+1)*64,96)).tobytes()==frame.tobytes() for index,frame in enumerate(after))

# 同帧上下对照，一次固定放大；没有按bbox重注册。
scale=4;cols=4;cellw=64*scale;cellh=96*scale+30
sheet=Image.new('RGB',(cols*cellw,cellh*4),(225,225,216));draw=ImageDraw.Draw(sheet)
for frame in range(8):
    col=frame%4;group=frame//4
    for row,version,frames in [(0,'v009',before),(1,'v010',after)]:
        x=col*cellw;y=(group*2+row)*cellh
        enlarged=frames[frame].resize((64*scale,96*scale),Image.Resampling.NEAREST)
        sheet.paste(enlarged,(x,y+30),enlarged)
        draw.text((x+8,y+8),f'{version} f{frame:02d}',fill=(20,30,40))
sheet.save(review/'same_frame_v009_v010_4x.png')

for name,region in [('knees',(18,61,48,84)),('arms',(9,43,54,65))]:
    w,h=region[2]-region[0],region[3]-region[1]
    scale=5
    strip=Image.new('RGB',(w*scale*8,h*scale*2+60),(34,42,50));draw=ImageDraw.Draw(strip)
    for row,version,frames in [(0,'v009',before),(1,'v010',after)]:
        for index,frame in enumerate(frames):
            x,y=index*w*scale,row*(h*scale+30)
            enlarged=frame.crop(region).resize((w*scale,h*scale),Image.Resampling.NEAREST)
            strip.paste(enlarged,(x,y+30),enlarged)
            draw.text((x+5,y+5),f'{version} f{index:02d}',fill=(235,235,235))
    strip.save(review/f'{name}_v009_v010_all8_5x.png')

transitions=[]
for index in range(8):
    following=(index+1)%8
    changes={}
    for version,frames in [('v009',before),('v010',after)]:
        a,b=list(frames[index].get_flattened_data()),list(frames[following].get_flattened_data())
        changes[version]=sum(p!=q for p,q in zip(a,b))
    transitions.append({'from':index,'to':following,'rgba_different_pixels':changes})
result={'status':'BINDING_AND_PROTECTED_IDENTITY_PASS','export_validation_sha256':sha(export_bytes),'manifest_sha256':sha(manifest_bytes),'v009_zip_sha256':sha(archive.read_bytes()),'v010_atlas_sha256':sha(atlas_bytes),'scope':manifest['scope'],'frames':frame_results,'adjacent_rgba_change_diagnostic_only':transitions,'meaning':'Identity checks and pixel-change counts do not decide joint readability or temporal patch artifacts; review the actual full images.'}
(review/'joint-action-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
assert export_bytes==(source/'qa/export_validation_v010.json').read_bytes()
assert all(sha((source / row['file']).read_bytes())==row['sha256'] for row in export['frames'])
print(json.dumps({'status':result['status'],'export_sha256':result['export_validation_sha256'],'atlas_sha256':result['v010_atlas_sha256'],'frames':frame_results,'transitions':transitions},ensure_ascii=False))
