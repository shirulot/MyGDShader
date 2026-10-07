"""建立18项对象的明确生产规格和提示词；不修改任何已验收素材。

spec的尺寸是原生像素，而模型母稿仅作为设计/材料参考。安装点为边界坐标。
脚本可重复运行；generation-record由实际工具返回结果逐项追加，不能推测成功。
"""
import json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[2]
REFS=['assets/ember/buildings/station/station_base_v001.png',
      'assets/ember/characters/robot/robot_idle_down_v001.png']
COMMON='''Use case: stylized-concept.
Make one NEW production design master for the same top-down pixel game Ember Energy Station.
Input image 1 and 2 are STYLE AND MANUFACTURER references only: blue-grey painted steel, pale ceramic armor, small brass fittings. Do not copy the station or robot as the requested object.
Clear pixel clusters, usually one logical pixel dark outline, 3-4 flat material shades; modest top-left volume light. Orthographic top-down three-quarter game view, top and modest front visible, horizontal/vertical world axes, no isometric diamond perspective. Compact coherent industrial design, quiet and maintained, small amounts of wear.
Use only this palette: #101820 #182631 #2B3E4B #4D6470 #829BA3 #BECBC4 #7B4D35 #B77C4B #E2B77A #566B78 #ECE9D8. No cyan orange red active-state indicators; all screens/windows are dark neutral and UNLIT.
Exactly ONE isolated complete object, genuine alpha transparent background with empty margins, no checkerboard painted into image, no scene, ground, cast shadow, text, labels, watermark, glow, fire, smoke, light beam, rain or animation. A larger image is a design master, intended for later native pixel finishing, do not include measurements or guide lines.
'''
ITEMS=[
('console_base','B02',[96,96],[48,80],[60,58],'buildings/console','A squat industrial control console with a sloping dark neutral screen, three simple physical buttons, pale ceramic top cap, sturdy blue-grey pedestal and small brass maintenance socket. Screen must be a single simple blank panel; no letters.'),
('pump_base','B03',[160,192],[80,176],[112,118],'buildings/pump','A substantial drainage pump: square low mounting plinth, round centrifugal pump shell and compact motor housing, clear left inlet and right outlet brass pipe fittings, small dark neutral gauge window. Water and hoses beyond the two fittings are absent.'),
('ventilator_base','B04',[160,192],[80,176],[110,124],'buildings/ventilator','A heat exhaust unit on a square plinth: raised blue-grey cylinder with broad readable open fan mouth, three static metal fan blades and central hub, pale ceramic upper housing, short square exhaust mouth at upper back. Static fan blades must have clean silhouette and legible separation from housing. No smoke or flames.'),
('cooler_base','B05',[160,192],[80,176],[112,126],'buildings/cooler','A cooling heat-exchanger module: square mounting base, three readable vertical U-shaped steel exchange pipes, pale ceramic cylindrical cooling core and side brass plumbing sockets, one small dark neutral service window. Compact top-down orthographic device, no ice/frost/water effects.'),
('relay_base','B06',[192,256],[96,240],[132,188],'buildings/relay','A tall communication relay: sturdy square base, vertical pale ceramic core with one dark neutral energy window, clearly separate narrow upper mast and short symmetric horizontal antenna bar with two small brass tips. Top mast/antenna silhouette must be simple and detachable visually; no radio waves.'),
('wall_lamp','B07',[64,64],[32,56],[30,42],'buildings/lights','An unlit wall-mounted industrial lamp: small vertical bracket, rounded protective steel hood over a dark neutral glass lens, two fastening bolts, small brass cable connector. Top-down three-quarter orthographic, complete isolated wall fixture, no wall surface.'),
('floor_lamp','B07',[64,64],[32,56],[30,44],'buildings/lights','An unlit short industrial floor beacon lamp: square mounting foot, short steel stalk, pale ceramic cage around dark neutral lens, small brass socket. This is a compact ground bollard, not a tall street lamp; no light cone or shadow.'),
('door_closed','B08',[96,128],[48,112],[64,94],'buildings/door','A closed industrial sliding doorway, frontal-facing top-down three-quarter orthographic: straight vertical blue-grey left/right posts, broad pale ceramic lintel, square front feet. Two plain steel closed sliding panels with a center seam and tiny brass handle. Outer frame is a simple rectangle. Blank neutral status inset on the right post. Clear negative space around outer object.'),
('door_open','B08',[96,128],[48,112],[64,94],'buildings/door','An OPEN industrial sliding doorway matching the same straight rectangular frame as the closed doorway: two blue-grey vertical posts, pale ceramic lintel, square front feet. Panels retract into side pockets. The central passage must be a large GENUINE TRANSPARENT hole, without black fill, floor or scenery. Neutral right-post indicator, no light.'),
('telepad_base','B09',[128,160],[64,144],[96,66],'buildings/telepad','A low walkable teleport platform: compact octagonal blue-grey metal plinth with pale ceramic rim segments, broad flat neutral central disc, four small unlit dark neutral marker slots. Low height, viewed from above with small front thickness. No dome, shield, beams or light ring.'),
('terminal_body','B10',[96,96],[48,80],[60,64],'buildings/terminal','An industrial remote diagnostic terminal: compact square blue-grey floor cabinet, pale ceramic screen bezel with single blank dark neutral rectangular screen, shallow physical keyboard ledge and sturdy feet, small brass side service connector. No writing, video content or CRT/glitch effect.'),
('screen_frame','B10',[96,96],[48,80],[64,64],'buildings/terminal','A separate flat front-facing square industrial screen BEZEL for UI display, exactly axis aligned and orthographic: slim blue-grey rim, pale ceramic corners, one small brass screw at each corner. Center is a large genuine transparent rectangular hole, no screen fill or content. All four straight edge strips have constant thickness for nine-slice stretching; no bevel perspective.'),
('fuse','B11',[64,64],[32,56],[38,22],'props/calibration','A single asymmetric industrial fuse cartridge lying horizontally, top-down three-quarter: pale ceramic tube, brass cap at both ends, one end has a projecting notch and other end a tiny dark fastening slot. Clear orientation, compact object, not a weapon; no text.'),
('antenna_coil','B11',[64,64],[32,56],[38,38],'props/calibration','A single small antenna calibration coil: blue-grey square base plate, readable brass wire helix with three thick loops around dark central core, one asymmetric side connector. Clear winding holes and orientation; no signal effects, no text.'),
('split_ring','B11',[64,64],[32,56],[40,36],'props/calibration','A single calibration split ring made of steel with pale ceramic upper surface and one small brass tab: broad C-shaped ring, large true transparent center hole and a clearly open gap at lower right. Asymmetric notch helps observe rotation, no numbers.'),
('log_cartridge','B12',[64,64],[32,56],[32,34],'props/story','A single compact maintenance record cartridge: rectangular pale ceramic casing with blue-grey protective corner caps, two brass contact fingers at top, one recessed dark neutral blank slot and asymmetric lower latch. Physical data module, no letters, no screen content.'),
('toolbox','B12',[64,64],[32,56],[44,32],'props/story','A single small maintenance toolbox: blue-grey rectangular case, pale ceramic lid corners, central steel carry handle with true transparent hole, two brass clasps, one side hinge. Top-down three-quarter orthographic, closed case, no tools outside, no labels.'),
('helmet','B12',[64,64],[32,56],[34,34],'props/story','A single discarded maintenance safety helmet matching the robot pale ceramic head design: rounded pale shell, broad dark neutral visor rim, short blue-grey rear brim, tiny brass side fastener. Compact top-down three-quarter object, without head/person, no logos.')]

def main():
    for directory in ['prompts','generated','finished','annotations','layers','pixel-review','tools']:
        (BASE/directory).mkdir(parents=True,exist_ok=True)
    specs=[]
    for ident,mid,canvas,anchor,target,folder,description in ITEMS:
        prompt=COMMON+'\nAsset: '+ident+'. '+description+f'\nNative final canvas will be {canvas[0]}x{canvas[1]}, subject no larger than {target[0]}x{target[1]}, mounting/ground boundary point {tuple(anchor)}. Preserve reference logical pixel/material density; centered complete object with transparent margin.'
        (BASE/'prompts'/f'{ident}.txt').write_text(prompt,encoding='utf-8')
        specs.append({'id':ident,'manifest_id':mid,'canvas':canvas,'anchor':anchor,'native_target':target,
                      'production_file':f'res://assets/ember/{folder}/{ident}_v001.png',
                      'references':REFS,'prompt':f'prompts/{ident}.txt'})
    (BASE/'planned-catalog-v001.json').write_text(json.dumps({'assets':specs},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'planned_assets':len(specs),'output':str(BASE)},ensure_ascii=False))

if __name__=='__main__': main()
