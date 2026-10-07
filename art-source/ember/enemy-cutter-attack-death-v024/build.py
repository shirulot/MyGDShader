"""Register fixed visible parts; copies approved pixels and writes rig data only."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'enemy-cutter-idle-hit-v023'
TEMPLATE=ROOT.parent/'enemy-heavy-attack-death-v019'
OLD=ROOT.parent/'enemy-sequences-v012/output/enemy_cutter'
UNIT='enemy_cutter'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rect=lambda x,y,w,h:[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]
for folder in ['source','output/'+UNIT,'reference/'+UNIT,'qa','previews']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
spec=json.loads((BASE/'rig.json').read_text(encoding='utf-8'))
spec['version']='v024-cutter-attack-death'
spec['method']='Single fixed canonical texture per direction; disjoint visible body/tool/leg ownership; fixed UV blue-gray joint links; no frame regeneration or mirroring.'
spec['actions']={
 'attack':dict(frame_count=6,fps=10,loop=False,body_y=[0,-1,-1,1,0,0],swing=[0,-.35,-.6,1,.3,0],blade=[0,15,30,45,15,0],fold=[0]*6,power=[1]*6),
 'death':dict(frame_count=8,fps=10,loop=False,body_y=[0,1,2,4,6,7,7,7],swing=[0,.2,.4,.65,.85,1,1,1],blade=[0,15,25,30,32,32,32,32],fold=[0,5,12,25,42,55,55,55],power=[1,.6,.2,0,0,0,0,0])}
tool_defs={
 'down_left':[('saw',0,[49,81],-22,55,[[39,83],[44,83],[44,84],[45,84],[45,85],[46,85],[46,88],[48,88],[48,94],[46,96],[44,98],[35,98],[34,89],[36,85]],[41.5,90.5],[6.5,7.5]),('claw',1,[78,85],15,65,[],[0,0],[1,1])],
 'left':[('claw',0,[54,87],-18,55,[],[0,0],[1,1])],
 'up_left':[('claw',0,[54,84],-16,45,[],[0,0],[1,1]),('saw',1,[84,74],20,-45,[[83,73],[87,73],[90,76],[92,78],[92,82],[90,85],[86,88],[82,88],[79,84],[79,78],[80,76],[82,76]],[84.5,79.5],[6.5,7.5])],
 'up':[],
 'up_right':[('saw',0,[75,84],18,-50,[[83,81],[90,81],[94,84],[94,92],[90,96],[84,96],[81,91],[81,87],[82,83]],[86.5,87.5],[6.5,7.5]),('claw',1,[78,75],-12,-35,[],[0,0],[1,1])],
 'right':[('saw',0,[69,87],10,-50,[[78,85],[84,85],[88,88],[89,95],[86,99],[80,100],[75,97],[74,92],[74,89],[76,87]],[80.5,92],[7,8])],
 'down_right':[('saw',0,[56,85],-20,-80,[[55,90],[61,90],[65,93],[65,99],[62,103],[58,104],[52,101],[51,95],[51,92]],[59.5,96.5],[6.5,7.5]),('claw',1,[82,82],16,-55,[],[0,0],[1,1])]}
se_parts=[
 dict(id='rear_right',polygon=[[0,0],[50,0],[50,68],[49,68],[49,77],[48,77],[48,85],[0,85]],pivot=[49,77],sole=[44,85],socket=dict(start=[51,76],end=[47,78],width=3,source_rect=[49,79,2,2])),
 dict(id='rear_left',polygon=[[72,0],[83,0],[83,75],[80,79],[78,81],[78,74],[76,74],[76,70],[72,70]],pivot=[78,75],sole=[79,79],socket=dict(start=[77,74],end=[79,76],width=3,source_rect=[76,77,2,2])),
 dict(id='front_right',polygon=rect(47,81,11,14),pivot=[54,83],sole=[52,94],socket=dict(start=[55,83],end=[52,87],width=3,source_rect=[51,90,2,2])),
 dict(id='front_left',polygon=rect(72,78,12,14),pivot=[75,80],sole=[81,91],socket=dict(start=[75,79],end=[78,85],width=3,source_rect=[77,86,2,2]))]
spec['configs']['down_right'].update(parts=se_parts,hidden_legs=[],protected_body_polygons=[
 [[53,81],[61,81],[61,87],[64,87],[64,89],[69,89],[69,105],[51,105],[51,90],[53,90]],
 [[81,77],[86,77],[86,81],[90,81],[90,84],[96,84],[96,97],[83,97],[83,90],[80,90],[80,82]],
 rect(56,80,18,8)])
for d,c in spec['configs'].items():
 shutil.copy2(BASE/'source'/f'{d}.png',ROOT/'source'/f'{d}.png')
 c['source']=f'res://source/{d}.png'
 c['source_sha256']=sha(ROOT/'source'/f'{d}.png')
 c['tools']=[]
 for name,poly_index,pivot,attack,death,blade,hub,radius in tool_defs[d]:
  extra={('down_left','claw'):[rect(68,90,15,15)],('left','claw'):[rect(32,91,20,10)],('up_left','claw'):[rect(32,75,24,16)],('down_right','claw'):[rect(80,83,16,16)]}.get((d,name),[])
  c['tools'].append(dict(id=name,polygon=c['protected_body_polygons'][poly_index],extra_polygons=extra,pivot=pivot,attack_angle=attack,death_angle=death,blade_polygon=blade,hub=hub,radius=radius))
  if (d,name)==('down_left','saw'):
   c['tools'][-1]['socket']=dict(start=[54,82],end=[49,82],width=3,source_rect=[55,87,2,2])
   c['tools'][-1]['spindle']=dict(start=[48,84],end=hub,width=3,source_rect=[55,87,2,2])
 for p in c['parts']:
  p['foot_cut_y']=p['sole'][1]-4 if p['sole'] is not None else 128
  p['fold_sign']=1 if p['pivot'][0]<64 else -1
  p['fold_multiplier']=1.6 if p['sole'] is not None and p['sole'][1]<90 else .85
  p['ankle']={('down_right','front_right'):[50,90],('down_right','front_left'):[79,87]}.get((d,p['id']),[p['sole'][0],p['foot_cut_y']] if p['sole'] is not None else p['pivot'])
 c['sensor_rect']={'down_left':[58,77,5,5],'down_right':[65,76,5,5]}.get(d,[0,0,0,0])
 c['ownership_overrides']={
  'down_left':[dict(polygon=rect(81,82,4,4),owner='front_left')],
  'down_right':[dict(polygon=rect(45,85,2,5),owner='front_right'),dict(polygon=rect(72,88,1,1),owner='body')],
  'up':[dict(polygon=rect(50,97,1,1),owner='rear_left'),dict(polygon=rect(86,95,1,1),owner='front_right_foot'),dict(polygon=rect(41,95,2,1),owner='front_left_foot')]
 }.get(d,[])
 c['attack_note']='Rear tools remain occluded; body anticipation/recovery is visible.' if d=='up' else 'Only originally visible tools are articulated.'
 if d=='up':
  # 背向的隐藏工具不外露；机身预扭与反向短促释放区别于待机起伏。
  c['attack_body_poses']=[[0,0,0],[1,0,3],[2,1,5],[-2,-1,-7],[-1,0,-2],[0,0,0]]
  c['attack_body_pivot']=[64,85]
 if d=='down_right':
  # 仅更正支撑标记，不改已经注册的脚掌切分、踝轴、腿壳折叠轨迹。
  actual={'front_right':[50,94],'front_left':[79,91],'rear_left':[78,81],'rear_right':[44,85]}
  for p in c['parts']:
   p['nominal_previous_sole']=p['sole'];p['sole']=actual[p['id']]
   if p['id']=='front_left':p['socket']['material_note']='Fixed UV has one opaque dark-brown source pixel and three transparent pixels; not a solid 2x2 blue patch.'
spec['preserved']=[]
for d in spec['directions']:
 shutil.copy2(BASE/'output'/UNIT/f'neutral_{d}.png',ROOT/'output'/UNIT/f'neutral_{d}.png')
for kind in spec['actions']:
 action=kind+'_down';dst=ROOT/'output'/UNIT/action
 shutil.copytree(OLD/action,dst,dirs_exist_ok=True)
 shutil.copy2(OLD/(action+'.png'),dst.with_suffix('.png'))
 shutil.copy2(dst.with_suffix('.png'),ROOT/'reference'/UNIT/(action+'.png'))
 spec['preserved'].append(dict(action=action,atlas_sha256=sha(dst.with_suffix('.png')),frame_hashes=[sha(dst/f'f{i:02}.png') for i in range(spec['actions'][kind]['frame_count'])]))
(ROOT/'rig.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
for name in ['export.gd','verify.gd','capture.gd','preview.gd','preview.tscn','previews/index.html']:
 text=(TEMPLATE/name).read_text(encoding='utf-8').replace('v019','v024').replace('enemy_tracked_heavy',UNIT).replace('heavy','cutter').replace('HEAVY','CUTTER').replace('重装机','切割机')
 text=text.replace('攻击炮口回坐；死亡炮塔下沉、炮管垂落，履带接地不移动。后方炮口保持遮挡；各方向使用固定零件。','攻击挥动工具并复位；死亡机身下沉、腿部折叠，脚掌保持接地。背向工具保留遮挡。')
 (ROOT/name).write_text(text,encoding='utf-8')
text=(TEMPLATE/'pixel_audit.py').read_text(encoding='utf-8').replace('enemy_tracked_heavy',UNIT).replace('.read_text()',".read_text(encoding='utf-8')")
(ROOT/'pixel_audit.py').write_text(text,encoding='utf-8')
shutil.copy2(BASE/'project.godot',ROOT/'project.godot')
p=ROOT/'project.godot';p.write_text(p.read_text(encoding='utf-8').replace('idle and hit v023','attack and death v024'),encoding='utf-8')
text=(ROOT.parent/'enemy-cutter-directions-move-v022/inspect_actions.gd').read_text(encoding='utf-8').replace('range(8)','range(int(clip.frame_count))').replace('24,52,80,56','16,48,96,64').replace('80*','96*').replace('56*','64*').replace(')*80',' )*96').replace(')*56',' )*64')
(ROOT/'inspect_actions.gd').write_text(text,encoding='utf-8')
print('CUTTER_V024_PREPARED')
