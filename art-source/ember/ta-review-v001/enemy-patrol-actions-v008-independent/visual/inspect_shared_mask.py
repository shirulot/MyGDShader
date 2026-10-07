"""固定 v008 解包；只核本次 UV-mask 可见差异并制作原生/4x 图证。"""
import hashlib
import io
import json
import math
from pathlib import Path
from zipfile import ZipFile
from PIL import Image, ImageDraw

workspace=Path('E:/dev/shader/godot-shader/godot-shader-simple')
review=workspace/'art-source/ember/ta-review-v001/enemy-patrol-actions-v008-independent/visual'
root=review/'package'
archive=workspace/'art-source/ember/deliveries/enemy_patrol_actions_v008_2026-10-06.zip'
sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha(archive.read_bytes())=='4a3ab26e04abb5816c505fb0c0f851b8042886d8ea3d2b8516b1923360af74b4'
with ZipFile(archive) as package:
    entries=[entry for entry in package.infolist() if not entry.is_dir()]
    assert len({entry.filename for entry in entries})==len(entries)
    assert package.testzip() is None
    for entry in entries:
        target=(root/entry.filename).resolve()
        assert target.is_relative_to(root.resolve())
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(package.read(entry))
catalog=json.loads((root/'output/catalog_v008.json').read_text(encoding='utf-8'))
rig=json.loads((root/'rig.json').read_text(encoding='utf-8'))
canonical=Image.open(root/'source/canonical.png').convert('RGBA')

def inside(point,polygon):
    x,y=point;result=False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]: result=not result
    return result

with ZipFile(workspace/'art-source/ember/deliveries/enemy_patrol_actions_v006_2026-10-06.zip') as original_package:
    old_rig=json.loads(original_package.read('rig.json'))
old_knee=next(item for item in old_rig['parts'] if item['id']=='left_knee_cap')
new_knee=next(item for item in rig['parts'] if item['id']=='left_knee_cap')
assert all(inside((76.5,y+.5),old_knee['polygon']) and not inside((76.5,y+.5),new_knee['polygon']) for y in [87,88,89])
excluded_centers=[]
added_centers=[]
for y in range(128):
    for x in range(128):
        old_inside,new_inside=inside((x+.5,y+.5),old_knee['polygon']),inside((x+.5,y+.5),new_knee['polygon'])
        if old_inside and not new_inside: excluded_centers.append([x,y])
        if new_inside and not old_inside: added_centers.append([x,y])
assert excluded_centers==[[76,87],[76,88],[76,89]] and not added_centers
baseline_specs={
    'move_down':('enemy_patrol_move_v004_r1_2026-10-06.zip','33792f03eb316f7dc82618e226da2eddb9491d504b6803636d04c9e3c7633608','move_down_v004.png',[1,1,1,0,0,1,0,1]),
    'idle_down':('enemy_patrol_actions_v005_2026-10-06.zip','6a3687783823cfd3e9db4b5c04d26b47c91a70df825ec74f8d195378b6c01468','idle_down_v005.png',[0,0,0,0]),
    'hit_down':('enemy_patrol_actions_v005_2026-10-06.zip','6a3687783823cfd3e9db4b5c04d26b47c91a70df825ec74f8d195378b6c01468','hit_down_v005.png',[0,0,1,0]),
    'attack_down':('enemy_patrol_actions_v006_2026-10-06.zip','1bae7e4fa6932b2479274abecabe247c7efa7efbd7a8b50bbd49b864eea15295','attack_down_v006.png',[0,3,3,3,3,0]),
    'death_down':('enemy_patrol_actions_v006_2026-10-06.zip','1bae7e4fa6932b2479274abecabe247c7efa7efbd7a8b50bbd49b864eea15295','death_down_v006.png',[0,0,1,2,2,3,3,3]),
}
records=[];bindings=[]
for action,spec in baseline_specs.items():
    zipname,expected_sha,atlas_name,expected_counts=spec
    baseline_archive=workspace/'art-source/ember/deliveries'/zipname
    assert sha(baseline_archive.read_bytes())==expected_sha
    with ZipFile(baseline_archive) as old_package:
        baseline_bytes=old_package.read('output/'+atlas_name)
    assert baseline_bytes==(root/'references'/atlas_name).read_bytes()
    old_atlas=Image.open(io.BytesIO(baseline_bytes)).convert('RGBA')
    definition=catalog['actions'][action]
    current_atlas_path=root/definition['atlas'].removeprefix('res://')
    assert sha(current_atlas_path.read_bytes())==definition['atlas_sha256']
    current_atlas=Image.open(current_atlas_path).convert('RGBA')
    assert definition['frame_count']==len(expected_counts)
    bindings.append({'action':action,'baseline_zip':zipname,'baseline_zip_sha256':expected_sha,'reference_bytes_equal_baseline_atlas':True,'current_atlas_sha256':sha(current_atlas_path.read_bytes())})
    old_frames=[];new_frames=[]
    for frame_index,expected_count in enumerate(expected_counts):
        old=old_atlas.crop((frame_index*128,0,(frame_index+1)*128,128))
        frame_path=root/f'output/{action}/f{frame_index:02d}.png'
        assert sha(frame_path.read_bytes())==definition['frame_hashes'][frame_index]
        current=Image.open(frame_path).convert('RGBA')
        assert current.size==(128,128)
        assert current_atlas.crop((frame_index*128,0,(frame_index+1)*128,128)).tobytes()==current.tobytes()
        old_frames.append(old);new_frames.append(current)
        pose=definition['poses'][frame_index]
        transform=pose['part_transforms']['left_knee_cap']
        px,py=transform['position'];bx=transform['basis_x'];by=transform['basis_y']
        determinant=bx[0]*by[1]-bx[1]*by[0]
        part=next(item for item in rig['parts'] if item['id']=='left_knee_cap')
        pivot=part['pivot']
        changes=[];hidden_rgb_diff=0
        for y in range(128):
            for x in range(128):
                a,b=old.getpixel((x,y)),current.getpixel((x,y))
                if a==b:continue
                if a[3]==b[3]==0:
                    hidden_rgb_diff+=1
                    continue
                dx,dy=x+.5-px,y+.5-py
                u=pivot[0]+(by[1]*dx-by[0]*dy)/determinant
                v=pivot[1]+(-bx[1]*dx+bx[0]*dy)/determinant
                source_pixel=[math.floor(u),math.floor(v)]
                source_rgba=canonical.getpixel(tuple(source_pixel))
                changes.append({'screen_px':[x,y],'before':a,'after':b,'inverse_knee_uv':[u,v],'source_pixel':source_pixel,'source_rgba':source_rgba,'source_rgb_matches_old':a[:3]==source_rgba[:3]})
        assert len(changes)==expected_count,(action,frame_index,changes)
        assert all(change['before'][3]==255 and change['after'][3]==0 for change in changes)
        assert all(change['source_pixel'][0]==76 and change['source_pixel'][1] in [87,88,89] and change['source_rgb_matches_old'] for change in changes),(action,frame_index,changes)
        records.append({'action':action,'frame':frame_index,'visible_changes':len(changes),'hidden_rgb_differences':hidden_rgb_diff,'current_frame_sha256':sha(frame_path.read_bytes()),'changes':changes,'visible_bounds':current.getchannel('A').getbbox()})
    # 固定全画布坐标对照；四倍图不改帧注册。
    for background_name,color in [('dark',(30,38,46)),('light',(242,242,232))]:
        sheet=Image.new('RGB',(128*len(old_frames),128*2+30*2),color)
        drawing=ImageDraw.Draw(sheet)
        for row,label,frames in [(0,'old',old_frames),(1,'v008',new_frames)]:
            y=row*158
            for index,image in enumerate(frames):
                sheet.paste(image,(index*128,y+30),image)
                drawing.text((index*128+5,y+8),f'{label} f{index:02d}',fill=(225,225,225) if background_name=='dark' else (25,25,25))
        sheet.save(review/f'{action}_old_v008_{background_name}_1x.png')
        sheet.resize((sheet.width*4,sheet.height*4),Image.Resampling.NEAREST).save(review/f'{action}_old_v008_{background_name}_4x.png')
    # 本次有差异处的紧凑黑白底局部，便于看到单像素删除而不只信计数。
    for background_name,color in [('dark',(30,38,46)),('light',(242,242,232))]:
        region=(48,82,84,108) if action=='death_down' else (65,78,86,99)
        w,h=region[2]-region[0],region[3]-region[1]
        scale=8
        sheet=Image.new('RGB',(w*scale*len(old_frames),2*(h*scale+25)),color)
        drawing=ImageDraw.Draw(sheet)
        for row,label,frames in [(0,'old',old_frames),(1,'v008',new_frames)]:
            y=row*(h*scale+25)
            for index,image in enumerate(frames):
                crop=image.crop(region).resize((w*scale,h*scale),Image.Resampling.NEAREST)
                sheet.paste(crop,(index*w*scale,y+25),crop)
                drawing.text((index*w*scale+5,y+5),f'{label} f{index:02d}',fill=(225,225,225) if background_name=='dark' else (25,25,25))
        sheet.save(review/f'{action}_old_v008_{background_name}_local_8x.png')

report={'status':'VISIBLE_DELTA_SOURCE_AND_REFERENCE_PASS','v008_zip_sha256':sha(archive.read_bytes()),'v008_zip_bytes':archive.stat().st_size,'entries':len(entries),'catalog_sha256':sha((root/'output/catalog_v008.json').read_bytes()),'rig_sha256':sha((root/'rig.json').read_bytes()),'baseline_bindings':bindings,'frame_count':len(records),'visible_deleted_pixels':sum(record['visible_changes'] for record in records),'added_or_recolored_visible_pixels':0,'shared_deleted_source_pixels':[[76,87],[76,88],[76,89]],'mask_excluded_texel_centers':excluded_centers,'mask_added_texel_centers':added_centers,'frames':records,'meaning':'This establishes exact delta and source, not visual acceptance; inspect actual registered native/4x light/dark frames.'}
(review/'shared-mask-delta.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':report['status'],'zip_bytes':report['v008_zip_bytes'],'entries':report['entries'],'frame_count':len(records),'visible_deleted_pixels':report['visible_deleted_pixels'],'counts':{action:[record['visible_changes'] for record in records if record['action']==action] for action in baseline_specs}},ensure_ascii=False))
