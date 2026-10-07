"""保存逐张参考稿的完整规范；实际输出另由内置image_gen生成并登记。"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
COMMON = '''Use case: stylized-concept
Asset type: reference-only atmosphere board for the same pixel-art game Ember Energy Station.
Primary request: one landscape 16:9 composition, exactly1536x864 pixels if supported.
Input images: Image1 is the established native pixel-scale/material/palette board; use it as a design guide, omit every caption/letter and its board layout. Other images are the actual native devices. Extend their industrial design faithfully.
Style: top-down three-quarter ORTHOGRAPHIC pixel art, square grid aligned horizontally and vertically, visible object tops and small fronts. Clean deliberate pixel clusters, thin contours, modest detail, blue-grey steel, pale ceramic armour and sparse brass fittings. Same compact rounded maintenance robot as the reference, no weapons.
Lighting/mood: quiet old industrial facility after rain, gentle upper-left form lighting, restrained cool ambient light. This board may suggest eventual water/light/weather effects but is not a baked production background.
Palette guide: #101820,#182631,#2B3E4B,#4D6470,#829BA3,#BECBC4,#7B4D35,#B77C4B,#E2B77A,#51C5C2,#E5A44B,#E65B4A,#566B78,#203A4B,#406B78,#ECE9D8. Restrict saturated accent areas and preserve clear route readability.
Constraints: one coherent game-view composition, no panel divisions, no text, no UI, no labels, no logos, no watermark, no isometric diamond grid, no camera perspective/vanishing point, no photorealistic texture, no depth of field. Do not invent a new character or enemies. Ground remains quiet. Equipment larger than the robot, reused modular square bases, pipes, rails and bridges. Do not turn the reference sheet captions into scene text.
'''
SCENES = {
    'R02_courtyard': '''Scene: maintenance forecourt. Broad square-grid steel walkway entering from the lower centre; one pale cylindrical energy station slightly above centre, a small wall console, a simple industrial door at the upper exit and two restrained floor lights. The compact maintenance robot waits on the approach. Show an unobstructed walking route, a few shallow wet floor patches and quiet wall/pipe boundaries. Readable player first, target station second, route third. Small warm lamp window, no dominant glow or piles of rubble.''',
    'R02_pump_yard': '''Scene: open-air pump yard. Calm dark water canals divide two blue-grey steel platforms. One horizontal bridge and one vertical bridge visibly link safe landings, each with narrow side beams on the same tile grid. A pale/blue-grey pump with brass pipe couplings is the repair target, with a small console on dry ground. The small robot stands by the pump. Water remains low-contrast and subtly rippled; preserve clear walkable bridge decks and banks. Exit walkway at the upper right. No waterfall, no giant bridge, no diagonal or isometric floor.''',
    'R02_thermal_yard': '''Scene: thermal treatment courtyard. Square steel walking route bends around a compact large ventilation unit and cooling pipe assembly. The fan housing, vents and brass pipe connectors match the existing industrial family. The robot stands at a small repair console. A few distant thin wisps suggest future exhaust and heat effects without obscuring the route or foreground edges. Keep safe floor broad and quiet, warm accent restricted to neutral device apertures, no fire inferno or red glowing floors. Clearly visible upper exit.''',
    'R02_relay_core': '''Scene: relay core. A tall slender pale relay tower with cylindrical core, compact square base and simple antenna arms forms the upper-centre focal device, matching the native relay reference. A clear steel approach from below, low rail borders, a small terminal, two restrained lamps and minimal cable routing frame the repair area. Place the small maintenance robot close enough to establish scale; the tower remains notably taller. Suggest restored warmth with one small brass-toned window, no neon forest or giant energy beams. Side walkway leads onward.''',
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    style = 'art-source/ember/references/full_native_scale_v003.png'
    refs = {
        'R02_courtyard': [style, 'assets/ember/buildings/station/station_base_v001.png', 'assets/ember/buildings/console/console_base_v001.png'],
        'R02_pump_yard': [style, 'assets/ember/buildings/pump/pump_base_v001.png', 'assets/ember/environment/tilesets/structures_v001.png'],
        'R02_thermal_yard': [style, 'assets/ember/buildings/ventilator/ventilator_base_v001.png', 'assets/ember/buildings/cooler/cooler_base_v001.png'],
        'R02_relay_core': [style, 'assets/ember/buildings/relay/relay_base_v001.png'],
        'R03_design': [style, 'assets/ember/buildings/station/station_base_v001.png', 'assets/ember/buildings/ventilator/ventilator_base_v001.png', 'assets/ember/buildings/pump/pump_base_v001.png'],
    }
    items = []
    for ident, scene in SCENES.items():
        items.append({'id': ident, 'prompt': COMMON + scene, 'requested_size': [1536, 864], 'references': refs[ident]})
    items.append({'id': 'R03_design', 'requested_size': [1536, 1024], 'references': refs['R03_design'], 'prompt': '''Use case: stylized-concept
Asset type: reference-only low-poly 3D shape board for Ember Energy Station, landscape1536x1024.
Primary request: exactly four separate model concepts arranged as four evenly spaced objects on a clean neutral blue-grey background: a compact rounded maintenance robot, a cylindrical energy beacon on a square base, a ventilation/fan unit with clear outlet, and a water pump with inlet/outlet pipe couplings. The input images are the native 2D pixel-art design family and scale guide. Preserve the pale ceramic armour, blue-grey steel bodies, rounded compact joints, simple square platform bases and occasional brass couplings. Convert the existing shapes into clearly readable low-poly volumes rather than inventing replacements. The robot is much smaller than the equipment.
Style: modest low-poly 3D industrial props, orthographic three-quarter views, clear construction-friendly silhouette and broad material regions; gentle neutral upper-left lighting, matte surfaces, no complex realistic details. Neutral dark apertures for unlit status windows, simple fan rotor visible. Keep each whole object separated with empty space around it. No scene walls, no floor grid, no tiny alternate models, no text, no labels, no wireframe, no UI, no watermark, no weapons, no neon, no holographic shield or live fire. This is a shape reference, not a finished model, UV sheet or implemented 3D game.'''} )
    for item in items:
        item['status'] = 'PROMPT_READY_NOT_GENERATED'
        item['reference_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in item['references']}
        (OUT / (item['id'] + '.prompt.txt')).write_text(item['prompt'], encoding='utf-8')
    (OUT / 'prompt-manifest.json').write_text(json.dumps({'status': 'PROMPTS_READY_NOT_PRODUCTION', 'items': items}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Prepared5 separate reference prompts; generated outputs remain0.')


if __name__ == '__main__': main()
