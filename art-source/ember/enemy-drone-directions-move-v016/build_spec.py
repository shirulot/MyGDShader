"""Bind reviewed s004 direction masters to the approved v011 rotor plane assembly."""
from pathlib import Path
import hashlib
import json
import shutil
ROOT=Path(__file__).resolve().parent
EMBER=ROOT.parent
W=EMBER/'enemy-eight-directions-v013'
UNIT='enemy_scout_drone'
DIRS=['down','down_left','left','up_left','up','up_right','right','down_right']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Each pair is anatomical right (+ spin), then anatomical left (- spin).
# Centers are registered to the visible native hub pixel centers, not bounding boxes.
centers={'down_left':[[48.5,58.5],[79.5,69.5]],'left':[[64.5,57.5],[64.5,72.5]],
         'up_left':[[79.5,58.5],[48.5,70.5]],'up':[[85.5,64.5],[41.5,64.5]],
         'up_right':[[79.5,70.5],[48.5,58.5]],'right':[[64.5,72.5],[64.5,57.5]]}
for folder in ['source','output',f'output/{UNIT}',f'reference/{UNIT}','qa','previews']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
configs={}
for direction in DIRS:
    source=W/f'static_preflight_s004_drone/neutral_{direction}.png'
    shutil.copy2(source,ROOT/f'source/{direction}.png')
    shutil.copy2(source,ROOT/f'output/{UNIT}/neutral_{direction}.png')
    if direction in centers:
        configs[direction]={'source':f'res://source/{direction}.png','source_sha256':sha(source),
                            'fans':[{'id':side,'center':center,'radius':[6.5,4.5],'spin':spin}
                                    for side,center,spin in zip(['anatomical_right','anatomical_left'],centers[direction],[1,-1])]}
preserved=[]
for direction,folder in [('down','enemy-sequences-v012'),('down_right','enemy-eight-directions-v013-pilot-drone-v001')]:
    action='move_'+direction;source=EMBER/f'{folder}/output/{UNIT}'
    shutil.copytree(source/action,ROOT/f'output/{UNIT}/{action}',dirs_exist_ok=True)
    shutil.copy2(source/(action+'.png'),ROOT/f'output/{UNIT}/{action}.png')
    preserved.append({'action':action,'source':folder,'atlas_sha256':sha(source/(action+'.png')),
                      'frame_hashes':[sha(source/action/f'f{i:02}.png') for i in range(8)]})
shutil.copy2(ROOT/f'output/{UNIT}/move_down.png',ROOT/f'reference/{UNIT}/move_down.png')
shutil.copy2(ROOT/'source/down.png',ROOT/f'reference/{UNIT}/neutral_down.png')
shutil.copy2(W/'source/parts/rotor_well_master.png',ROOT/'source/rotor_well_master.png')
for shader in ['pilot_fan_body.gdshader','pilot_fan.gdshader']:shutil.copy2(W/shader,ROOT/shader)
spec={'version':'v016-drone-six-new-moves','unit':UNIT,'canvas':[128,128],'root':[64,104],
      'directions':DIRS,'frame_count':8,'fps':8,'loop':True,'configs':configs,'preserved':preserved,
      'fan_source':'res://source/rotor_well_master.png','fan_source_sha256':sha(ROOT/'source/rotor_well_master.png'),
      'rotor_rect':[223,165,583,584],'well_rect':[1000,192,535,528],
      'body_y':[0,-1,-1,0,1,1,0,0],'angle_step_degrees':11.25,
      'method':'Approved fixed direction silhouettes; only rotor apertures replaced by fixed v011 well and rotor samples. Counter-rotation in source plane, then ellipse projection. No per-frame generated artwork.'}
(ROOT/'rig.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
print('DRONE_SIX_MOVE_SPEC_READY')
