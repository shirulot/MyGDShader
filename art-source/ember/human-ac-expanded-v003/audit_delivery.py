"""只检查导出及制作检查图；技术检查不代替动作和角色一致性审查。"""
from pathlib import Path
from PIL import Image, ImageDraw
import json, hashlib, numpy as np

ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
clips=data['clips']; results=[]
directions=['down','down_left','left','up_left','up','up_right','right','down_right']
expected={f'{ch}-{action}-{direction}' for ch in ['A','C'] for action in ['idle','walk','run'] for direction in directions}
expected|={f'{ch}-{action}-left' for ch in ['A','C'] for action in ['crouch','jump','collect','push','pull']}
assert {c['key'] for c in clips}==expected
for c in clips:
    atlas=Image.open(ROOT/c['atlas']).convert('RGBA')
    assert atlas.size==(64*c['frame_count'],96)
    arrays=[]
    for i in range(c['frame_count']):
        im=Image.open(ROOT/'frames'/c['key']/f'f{i:02d}.png').convert('RGBA');a=np.array(im)
        assert im.size==(64,96)
        assert set(np.unique(a[:,:,3])).issubset({0,255})
        assert not a[0,:,3].any() and not a[-1,:,3].any() and not a[:,0,3].any() and not a[:,-1,3].any()
        assert np.array_equal(a,np.array(atlas.crop((i*64,0,(i+1)*64,96))))
        arrays.append(a)
    # 包括尾→首的像素变化量，仅标出复审位置，不用阈值宣称关节或循环合格。
    delta=[int(np.any(arrays[i]!=arrays[(i+1)%len(arrays)],axis=2).sum()) for i in range(len(arrays))]
    results.append({'key':c['key'],'export_checks':'pass','adjacent_pixel_changes':delta,'seam_change':delta[-1],'visual_status':'pending','production_ready':False})
    for scale in [1,4]:
        strip=atlas.resize((atlas.width*scale,96*scale),Image.Resampling.NEAREST)
        for bg,colour in [('dark',(24,38,49)),('light',(236,233,216))]:
            board=Image.new('RGB',strip.size,colour);board.paste(strip,mask=strip.getchannel('A'))
            board.save(ROOT/'qa'/f"{c['key']}-{scale}x-{bg}.png")

baseline=ROOT.parent/'human-ac-basic-v002'
for c in clips:
    if c.get('source_version'):
        for i in range(c['frame_count']):
            assert (ROOT/'frames'/c['key']/f'f{i:02d}.png').read_bytes()==(baseline/'frames'/c['key'].removesuffix('-left')/f'f{i:02d}.png').read_bytes()
old_zip=baseline/'human-ac-basic-v002.zip'
assert hashlib.sha256(old_zip.read_bytes()).hexdigest().upper()=='5CE1F48B55ADB01A2E66CF18B40FBDCC9E1669C05964F7952C5EC725A8AABFA6'

review={'status':'candidate_needs_visual_revision','production_ready':False,'clip_count':len(clips),'frame_count':data['total_frames'],'technical_checks':'58 atlases / 456 frames: dimensions, binary alpha, border safety, atlas correspondence, scope and preserved baseline pass','visual_limits':['新增斜向走跑的上下半周期仍有体态朝向摆幅和水平定位漂移；未通过无缝循环视觉验收。','新增待机存在轮廓细节跳动；尚未建立同一可编辑像素母稿。','推、拉当前仅原地施力试样；带位移的推拉版本出现露肤和支撑问题，未纳入预览。','64×96 是高分辨率 AI 候选共同缩放后的诊断导出，不是原生逐像素绘制完成稿。','本次浏览器自动化连接失败，未完成真实浏览器十周期观察；未做 Godot 运行验收。'],'clips':results}
(ROOT/'qa'/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')

# 把真实帧平铺为动图，方便一次对比八向；不插帧、不倒放、不对齐各帧 bbox。
for action in ['walk','run']:
    boards=[]
    for f in range(8):
        b=Image.new('RGB',(1024,432),(24,38,49));d=ImageDraw.Draw(b)
        for row,ch in enumerate(['A','C']):
            for col,direction in enumerate(directions):
                key=f'{ch}-{action}-{direction}';x=128*col;y=216*row
                im=Image.open(ROOT/'frames'/key/f'f{f:02d}.png').convert('RGBA').resize((128,192),Image.Resampling.NEAREST)
                b.paste(im,(x,y+20),im);d.text((x+5,y+3),f'{ch} {direction}',fill=(236,233,216))
        boards.append(b)
    boards[0].save(ROOT/'previews'/f'{action}-eight-directions.webp',save_all=True,append_images=boards[1:],duration=120 if action=='walk' else 80,loop=0,lossless=True)
    boards[0].save(ROOT/'qa'/f'{action}-eight-directions.png')
print(json.dumps({'clips':len(clips),'frames':data['total_frames'],'technical':'pass','visual':'needs revision'}))
