"""实际 PNG 履带相位/恢复/安装座证据；数值只定位，视觉裁决独立进行。"""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
review=Path('E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-heavy-actions-v007-independent/action-audit')
root=review/'package'
catalog=json.loads((root/'output/catalog_v007.json').read_text(encoding='utf-8'))
sha=lambda data:hashlib.sha256(data).hexdigest()
all_frames={};binding=[]
for action,definition in catalog['actions'].items():
    atlas_path=root/definition['atlas'].removeprefix('res://')
    assert sha(atlas_path.read_bytes())==definition['atlas_sha256']
    atlas=Image.open(atlas_path).convert('RGBA')
    all_frames[action]=[]
    for index in range(definition['frame_count']):
        path=root/f'output/{action}/f{index:02d}.png'
        assert sha(path.read_bytes())==definition['frame_hashes'][index]
        frame=Image.open(path).convert('RGBA')
        assert frame.size==(128,128)
        assert frame.tobytes()==atlas.crop((index*128,0,(index+1)*128,128)).tobytes()
        all_frames[action].append(frame)
        binding.append({'action':action,'frame':index,'sha256':sha(path.read_bytes()),'bounds':frame.getchannel('A').getbbox(),'alpha':sorted(set(frame.getchannel('A').get_flattened_data()))})
windows=[(30,86,42,102),(86,86,98,102)]
phase_results=[]
for index,frame in enumerate(all_frames['move_down']):
    following=(index+1)%8
    for side,region in zip(['left','right'],windows):
        a=frame.crop(region);b=all_frames['move_down'][following].crop(region)
        mismatch=0
        for y in range(16):
            for x in range(12):
                if b.getpixel((x,y))[:3]!=a.getpixel((x,(y-2)%16))[:3]:mismatch+=1
        assert mismatch==0,(index,following,side,mismatch)
        phase_results.append({'from':index,'to':following,'side':side,'observed_same_texel_motion_screen_y':2,'period_px':16,'different_rgb_pixels_vs_exact_cyclic_step':mismatch})
neutral=all_frames['idle_down'][0]
recovery={
    'idle_f02_equal_neutral':all_frames['idle_down'][2].tobytes()==neutral.tobytes(),
    'move_f00_equal_neutral':all_frames['move_down'][0].tobytes()==neutral.tobytes(),
    'hit_f00_equal_neutral':all_frames['hit_down'][0].tobytes()==neutral.tobytes(),
    'hit_f03_equal_neutral':all_frames['hit_down'][3].tobytes()==neutral.tobytes(),
}
assert all(recovery.values())
ground=[]
for action,frames in all_frames.items():
    for index,frame in enumerate(frames):
        same=frame.crop((0,102,128,104)).tobytes()==neutral.crop((0,102,128,104)).tobytes()
        assert same,(action,index)
        ground.append({'action':action,'frame':index,'bottom_y102_103_equal_neutral':same})
overlap=[]
canonical=Image.open(root/'source/canonical.png').convert('RGBA')
for name,x0 in [('left',44),('right',81)]:
    visible=[(x,y) for y in range(128) for x in range(x0,x0+3) if canonical.getpixel((x,y))[3]>=128]
    overlap.append({'side':name,'source_columns':[x0,x0+3],'visible_pixel_count':len(visible),'visible_y_range':[min(y for x,y in visible),max(y for x,y in visible)]})

for action,frames in all_frames.items():
    for bg,color in [('light',(242,242,232)),('dark',(30,38,46))]:
        cols=4;scale=4;cellw=96*scale;cellh=80*scale+25
        rows=(len(frames)+cols-1)//cols
        sheet=Image.new('RGB',(cols*cellw,rows*cellh),color);draw=ImageDraw.Draw(sheet)
        for index,frame in enumerate(frames):
            x,y=(index%cols)*cellw,(index//cols)*cellh
            crop=frame.crop((16,32,112,112)).resize((96*scale,80*scale),Image.Resampling.NEAREST)
            sheet.paste(crop,(x,y+25),crop)
            label=f'f{index:02d} body {catalog["actions"][action]["poses"][index]["body_translation_px"]}'
            draw.text((x+6,y+6),label,fill=(225,225,225) if bg=='dark' else (25,25,25))
        sheet.save(review/f'{action}_all_frames_{bg}_4x.png')
        if action in ['idle_down','hit_down']:
            crop_region=(38,65,90,103);w,h=52,38;zoom=6
            detail=Image.new('RGB',(w*zoom*len(frames),h*zoom+25),color);detail_draw=ImageDraw.Draw(detail)
            for index,frame in enumerate(frames):
                x=index*w*zoom
                crop=frame.crop(crop_region).resize((w*zoom,h*zoom),Image.Resampling.NEAREST)
                detail.paste(crop,(x,25),crop)
                detail_draw.text((x+5,5),f'f{index:02d}',fill=(225,225,225) if bg=='dark' else (25,25,25))
            detail.save(review/f'{action}_mounts_{bg}_6x.png')

frames=all_frames['move_down'];zoom=8;w,h=20,24
for bg,color in [('light',(242,242,232)),('dark',(30,38,46))]:
    detail=Image.new('RGB',(w*zoom*8,(h*zoom+25)*2),color);draw=ImageDraw.Draw(detail)
    for row,region in enumerate([(26,81,46,105),(82,81,102,105)]):
        for index,frame in enumerate(frames):
            x,y=index*w*zoom,row*(h*zoom+25)
            crop=frame.crop(region).resize((w*zoom,h*zoom),Image.Resampling.NEAREST)
            detail.paste(crop,(x,y+25),crop)
            draw.text((x+5,y+5),f'f{index:02d} ph{index*2}',fill=(225,225,225) if bg=='dark' else (25,25,25))
    detail.save(review/f'move_tread_phase_{bg}_8x.png')
result={'status':'PNG_PHASE_AND_RECOVERY_PASS','frame_count':len(binding),'actual_frame_binding':binding,'actual_move_phase_transitions':phase_results,'neutral_recovery':recovery,'fixed_ground_rows':ground,'source_mount_overlap':overlap,'meaning':'Phase measurements establish actual source-pixel displacement; do not alone decide texture seam or weight/readability.'}
(review/'actual-motion-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'frames':len(binding),'phase_transitions':len(phase_results),'recovery':recovery,'overlap':overlap},ensure_ascii=False))
