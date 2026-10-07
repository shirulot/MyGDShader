"""Create versioned editable rig/annotations without modifying v001 inputs.

The corrections are semantic part reassignments and explicit native-pixel joint
drawings. There is no dilation, closing, interpolation, automatic hole fill or
deletion of detached fragments.
"""
from pathlib import Path
import json, hashlib

SOURCE=Path(__file__).resolve().parents[1]
ROOT=SOURCE.parents[2]
OLD=ROOT/'art-source/ember/batch-02-robot'
ANN=SOURCE/'annotations'

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,data):
    if path.exists():raise FileExistsError(f'Editable input already exists: {path}')
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def relocate(rig,old_name,new_name,pixels):
    mapping={p['name']:p for p in rig['parts']}
    for pixel in pixels:
        assert pixel in mapping[old_name]['pixels'] and pixel not in mapping[new_name]['pixels']
        mapping[old_name]['pixels'].remove(pixel)
        mapping[new_name]['pixels'].append(pixel)
    for p in rig['parts']:p['pixels'].sort(key=lambda xy:(xy[1],xy[0]))

ANN.mkdir(parents=True,exist_ok=True)
baseline={}
for p in list((ROOT/'assets/ember/characters/robot').iterdir())+list((OLD/'annotations').glob('*.json'))+[OLD/'tools/finish_robot_frames.py']:
    if p.is_file():baseline[p.relative_to(ROOT).as_posix()]=sha(p)
write(SOURCE/'protected-inputs-before.json',baseline)

for direction in ('down','left','right','up'):
    old_rig=OLD/'annotations'/f'rig_{direction}_v001.json'
    rig=read(old_rig)
    rig['repair_version']='v002'
    rig['source_rig']=old_rig.relative_to(ROOT).as_posix()
    rig['source_rig_sha256']=sha(old_rig)
    rig['semantic_repairs']=[]
    if direction=='left':
        # This piece is physically the left edge of the near-side left boot.
        # The old x<32 split erroneously put it into the unrelated far leg.
        pixels=[[31,73],[30,74],[31,74],[29,75],[30,75],[31,75],
                [29,76],[30,76],[31,76],[29,77],[30,77],[31,77],[30,78],[31,78]]
        relocate(rig,'right_leg','left_leg',pixels)
        rig['semantic_repairs'].append({'id':'LEFT_NEAR_BOOT_COMPLETE_PART','from':'right_leg','to':'left_leg',
            'pixels_xy':pixels,'reason':'Keep all pixels of the same near-side boot under the same leg transform.'})
    if direction=='down':
        # These centerline crotch pixels belong to the pelvis, not either boot.
        relocate(rig,'right_leg','torso',[[30,62],[31,62]])
        relocate(rig,'left_leg','torso',[[32,62]])
        rig['semantic_repairs'].append({'id':'DOWN_PELVIS_CENTRAL_PIXELS','from':'right_leg/left_leg','to':'torso',
            'pixels_xy':[[30,62],[31,62],[32,62]],'reason':'Central pelvis moves with torso; keep both actual legs independent.'})
        forearm=[[42,49],[43,49],[43,50],[43,51],[43,52],[43,53],[43,54],[43,55],[43,56],[43,61]]
        relocate(rig,'torso','left_arm',forearm)
        relocate(rig,'left_leg','left_arm',[[43,62]])
        rig['semantic_repairs'].append({'id':'DOWN_LEFT_FOREARM_COMPLETE_PART','from':'torso/left_leg','to':'left_arm',
            'pixels_xy':forearm+[[43,62]],'reason':'The actual forearm inner edge and wrist pixels must move with their own arm/tool, not torso or leg.'})
    write(ANN/f'rig_{direction}_v002.json',rig)
    for frame in range(4):
        old_ann=OLD/'annotations'/f'walk_{direction}_f{frame:02d}.json'
        annotation=read(old_ann)
        annotation['parts_file']=f'annotations/rig_{direction}_v002.json'
        annotation['repair_version']='v002'
        annotation['source_annotation']=old_ann.relative_to(ROOT).as_posix()
        annotation['source_annotation_sha256']=sha(old_ann)
        annotation['repair_edits']=[]
        if direction=='left':
            annotation['gait']['camera_depth']='left side: near left boot reaches row79 in contact/support phases; in f03 its complete boot lifts by2px to row77, giving visible bbox bottom78. Far right boot projects higher. Virtual anchor stays (32,80).'
        def pixel(x,y,color,repair_id,purpose):
            annotation['patches'].append({'type':'pixel','at':[x,y],'color':color})
            annotation['repair_edits'].append({'repair_id':repair_id,'at':[x,y],'color':color,'purpose':purpose})
        if direction=='left' and frame==0:
            for x in (25,35):
                for y,c in [(44,1),(45,2),(46,1)]:
                    pixel(x,y,c,'LEFT_00_SHOULDER_COUPLINGS','Draw a three-pixel dark mechanical shoulder coupling; preserve upper/lower axillary negative space.')
        if direction=='right' and frame==2:
            for x in (27,40):
                for y,c in [(44,1),(45,2),(46,1)]:
                    pixel(x,y,c,'RIGHT_02_SHOULDER_COUPLINGS','Draw a three-pixel dark mechanical shoulder coupling; do not fill the entire arm/body gap.')
        if direction=='left' and frame==1:
            for x,c in [(33,1),(34,2),(35,2),(36,2),(37,1)]:
                pixel(x,55,c,'LEFT_01_HIP_COUPLING','Reconnect raised torso to supporting near-side leg with a narrow dark joint row.')
        if direction=='left' and frame==3:
            for x,c in [(29,1),(30,2),(31,1)]:
                pixel(x,59,c,'LEFT_03_HIP_COUPLING','Reconnect torso to supporting far-side leg while preserving the inter-leg opening below.')
        if direction=='right' and frame==3:
            for x in range(27,35):
                pixel(x,59,1 if x in (27,34) else 2,'RIGHT_03_HIP_COUPLING','Reconnect the pelvic edge to its near-side supporting leg using one dark native row.')
        if direction=='left' and frame==2:
            for x,y,c in [(27,56,1),(28,56,2),(33,56,1),(33,57,2)]:
                pixel(x,y,c,'LEFT_02_HIP_TOP_COUPLINGS','Repair only the proximal hip join after opposite horizontal leg displacement; retain the deeper leg/arm negative space.')
        if direction=='down' and frame in (0,2):
            x=23 if frame==0 else 40
            pixel(x,43,2,f'DOWN_{frame:02d}_SHOULDER_PIN','Close one exposed interior shoulder pin pixel; no background gap or silhouette dilation.')
        annotation['adjustments'].append('V002_SOURCE_REPAIR: semantic boot/pelvis rig reassignment and individually drawn native joint pixels; original body shape, palette, gait offsets and draw order preserved.')
        write(ANN/f'walk_{direction}_f{frame:02d}.json',annotation)
print('Created 4 editable rigs and 16 editable frame annotations.')
