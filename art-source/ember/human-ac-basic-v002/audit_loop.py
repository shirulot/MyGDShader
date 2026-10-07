"""检查周期时间、尾首邻域、接地与裁剪。像素差分只定位异常，不能证明动作自然。"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,numpy as np
ROOT=Path(__file__).resolve().parent
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
results=[]
for ch in ['A','C']:
 for action in ['idle','walk','run']:
  key=f'{ch}-{action}';paths=sorted((ROOT/'frames'/key).glob('*.png'));frames=[Image.open(p).convert('RGBA') for p in paths];arr=[np.array(im) for im in frames];n=len(frames)
  diffs=[int(np.count_nonzero(np.any(arr[i]!=arr[(i+1)%n],axis=2))) for i in range(n)]
  bbox=[im.getbbox() for im in frames]
  assert all(im.size==(64,96) for im in frames)
  assert all(set(np.unique(a[:,:,3]))<={0,255} for a in arr)
  assert all(b[0]>0 and b[1]>0 and b[2]<64 and b[3]<96 for b in bbox)
  assert not np.array_equal(arr[0],arr[-1]),'No duplicated terminal first frame'
  meta=json.loads((ROOT/'final'/f'{key}.json').read_text());ms=meta['duration_ms']
  for speed,mult in [('normal',1),('slow',3)]:
   gif=Image.open(ROOT/'previews'/f'{key}-{speed}.gif');assert gif.n_frames==n
   for i in range(n):gif.seek(i);assert gif.info['duration']==ms*mult
  order=[n-2,n-1,0,1];board=Image.new('RGB',(4*256,420),'#182631');d=ImageDraw.Draw(board)
  for col,i in enumerate(order):
   d.text((col*256+22,12),f'{key} · F{i:02}',font=font,fill='#E2B77A' if i==0 else '#ECE9D8')
   im=frames[i].resize((256,384),Image.Resampling.NEAREST);board.paste(im,(col*256,34),im)
  board.save(ROOT/'qa'/f'{key}-seam.png')
  rec={'clip':key,'frames':n,'period_ms':n*ms,'loop_order':list(range(n)),'wrap':[n-2,n-1,0,1],'duplicate_terminal_frame':False,'foot_bottoms':[b[3] for b in bbox],'head_top':[b[1] for b in bbox],'changed_pixels_each_transition':diffs,'seam_change_over_median':round(diffs[-1]/float(np.median(diffs)),3),'seam_not_largest_transition':diffs[-1]<=max(diffs[:-1]),'note':'Metrics describe exported pixels; do not establish perfect perceptual continuity.'}
  results.append(rec)
  # 浏览器多周期验证单独记录；此处不以算术取模测试冒充实际播放观察。
report={'status':'technical_checks_pass_visual_review_required','clips':results,'total_frames':sum(x['frames'] for x in results),'not_proof_of_perfect_motion':True}
(ROOT/'qa/loop-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(results))
