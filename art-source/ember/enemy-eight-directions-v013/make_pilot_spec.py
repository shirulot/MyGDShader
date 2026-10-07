"""Write rig metadata only. Images are untouched; Godot samples the fixed sources."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def rect(x, y, w, h):
    return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]

def part(name, polygon, pivot, end=None, exclude=None, z=0):
    return dict(id=name, polygon=polygon, pivot=pivot, end=end, exclude=exclude or [], z=z)

near_cap = rect(55,85,10,7)
far_cap = rect(66,85,9,7)
patrol_parts = [
    part('right_thigh',rect(57,82,8,10),[59,82],[59,90],[near_cap],1),
    part('right_shin',rect(56,92,9,2),[59,90],[58,97],z=1),
    part('right_cap',near_cap,[59,90],z=3),
    part('right_foot',rect(53,94,12,34),[58,97],z=2),
    part('left_thigh',rect(66,82,9,10),[69,82],[71,90],[far_cap],0),
    part('left_shin',rect(66,92,11,2),[71,90],[71,97],z=0),
    part('left_cap',far_cap,[71,90],z=2),
    part('left_foot',rect(65,94,13,34),[71,97],z=1),
]
patrol = dict(unit='enemy_patrol',parts=patrol_parts,
    legs={'right':{'hip':[59,82],'knee':[59,90],'ankle':[58,97],'sole_offset':[0,7]},
          'left':{'hip':[69,82],'knee':[71,90],'ankle':[71,97],'sole_offset':[0,7]}},
    phases=json.loads((ROOT.parent/'enemy-patrol-actions-v008/rig.json').read_text())['phases'],
    note='Rebuilt on approved s002/c002 southeast master. Same anatomical gait phase as approved down; large ivory kneecaps and complete boots keep rigid dimensions; only small dark hinge shafts use endpoint mapping.')

heavy_parts = [
    part('near_track',[[0,60],[45,60],[49,67],[53,73],[57,82],[57,128],[0,128]],[41,83],z=2),
    part('far_track',[[81,50],[128,50],[128,128],[82,128],[82,82],[85,72],[82,64],[81,64]],[93,76],z=0),
]
heavy = dict(unit='enemy_tracked_heavy',parts=heavy_parts,
    note='Two fixed track silhouettes. Original tread RGB is sampled cyclically inside two registered sheared windows. Tower suspension moves one pixel only.',
    tread_windows=[{'x':[43,55],'top_y':84,'shear_y_per_x':-.25,'period':16},
                   {'x':[90,102],'top_y':72,'shear_y_per_x':-.25,'period':16}])

# These masks remove only the original partially occluded support-leg pixels.
# Tools and central chassis remain from the registered southeast master.
cutter_masks = [
    [[0,0],[50,0],[50,68],[49,68],[49,77],[48,77],[48,85],[0,85]],
    [[72,0],[83,0],[83,75],[80,79],[78,81],[78,74],[76,74],[76,70],[72,70]],
    rect(44,90,11,5),rect(73,85,6,5),
]
cutter_legs = [
    {'id':'front_right','source_rect':[803,172,226,327],'target_origin':[47.5,81], 'scale':.04,'z':1,'phase_offset':4,'hip':[55,82],'sole':[52,94]},
    {'id':'front_left','source_rect':[225,172,295,327],'target_origin':[72,78], 'scale':.04,'z':0,'phase_offset':0,'hip':[74,79],'sole':[81,91]},
    {'id':'rear_right','registered':True,'phase_offset':0,'hip':[49,77],'sole':[44,85]},
    {'id':'rear_left','registered':True,'phase_offset':4,'hip':[78,75],'sole':[79,79]},
]
cutter_parts=[part('rear_right',cutter_masks[0],[49,77],z=0),part('rear_left',cutter_masks[1],[78,75],z=-1)]
# Duplicate only two small original joint areas underneath the unchanged chassis.
# This source overlap keeps the concealed mounting socket covered during 1-2 px travel.
cutter_parts[0]['overlap_polygons']=[rect(47,75,5,5)]
cutter_parts[1]['overlap_polygons']=[rect(74,73,6,6)]
cutter=dict(unit='enemy_cutter',parts=cutter_parts,remove_polygons=cutter_masks[2:],legs=cutter_legs,
    leg_source='res://source/parts/cutter_down_right_legs_v001.png',
    note='Original registered rear legs and all their visible armor are preserved. Only occluded front legs use the fixed generated parts. Pairs rear_right/front_left versus rear_left/front_right; concealed mounts travel <=2 px. No tool is counted as a support leg.')
drone=dict(unit='enemy_scout_drone',parts=[],
    fan_source='res://source/parts/rotor_well_master.png',
    rotor_rect=[223,165,583,584],well_rect=[1000,192,535,528],
    fans=[{'id':'near_right','center':[48.5,69.5],'radius':[6.5,4.5],'spin':1},
          {'id':'far_left','center':[79.5,58.5],'radius':[6.5,4.5],'spin':-1}],
    note='Same approved v011 four-blade rotor source, no probe-neck experiment. Rotor turns before fixed fan-plane projection; housing stays rigid.')

units=[patrol,heavy,cutter,drone]
for unit in units:
    unit['source']=f"res://source/registered/{unit['unit']}_down_right.png"
    if unit['unit']=='enemy_patrol':
        unit['source']='res://source/registered/enemy_patrol_down_right_s002.png'
    if unit['unit']=='enemy_scout_drone':
        unit['source']='res://source/registered/enemy_scout_drone_down_right_s004.png'
        unit['fan_source_sha256']=hashlib.sha256((ROOT/unit['fan_source'][6:]).read_bytes()).hexdigest()
    unit['source_sha256']=hashlib.sha256((ROOT/unit['source'][6:]).read_bytes()).hexdigest()
spec={'version':'v013-pilot-drone-v001','status':'FIRST_GATE_CANDIDATE','enabled_pilot_units':['enemy_scout_drone'],'paused_for_static_revision':[],'direction':'down_right','canvas':[128,128],'root':[64,104],
      'fps':8,'frames':8,'loop':True,'units':units}
(ROOT/'pilot_rigs.json').write_text(json.dumps(spec,indent=2),encoding='utf8')
print('WROTE_FOUR_FIXED_PILOT_RIGS')
