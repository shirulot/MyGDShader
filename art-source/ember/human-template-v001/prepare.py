"""准备公开动作研究资料及独立人类角色生产目录。"""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import json,urllib.request,re,html
ROOT=Path(__file__).resolve().parent
for name in ['source','references','prompts','frames','previews','qa']:(ROOT/name).mkdir(exist_ok=True)
OLD=ROOT.parent/'robot-eight-way-v011/revisions'
sources={'idle':OLD/'action-studies-v015/references/idle.gif','walk':OLD/'action-studies-v015/references/walk.gif','run':OLD/'action-studies-v015/references/run.gif','crouch':OLD/'collect-knee-v014-pilot/references/deadrevolver-crouch.gif'}
records={}
for action,path in sources.items():
 gif=Image.open(path);count=gif.n_frames;cols=4 if count in (7,8) else 3;sheet=Image.new('RGB',(cols*192,2*184),'#182631');dur=[]
 for i in range(count):
  gif.seek(i);dur.append(gif.info.get('duration',100));frame=ImageOps.mirror(gif.convert('RGB'));sheet.paste(frame,(i%cols*192,i//cols*184));ImageDraw.Draw(sheet).text((i%cols*192+5,i//cols*184+168),f'F{i} / {dur[-1]}ms',fill='white')
 sheet.save(ROOT/'references'/f'{action}-poses.png');(ROOT/'references'/f'{action}.gif').write_bytes(path.read_bytes());records[action]={'count':count,'durations_ms':dur,'preview_dimensions':gif.size,'cols':cols,'reference_source':'Dead Revolver public GIF; mirrored left for pose study'}
records['idle']['note']='7 decoded GIF frames; looping holds retained, not assumed to equal original Aseprite tags.'
(ROOT/'references/timing.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
gif=Image.open(sources['idle']);frame=ImageOps.mirror(gif.convert('RGB'));frame.resize((768,672),Image.Resampling.NEAREST).save(ROOT/'references/human-proportions.png')
page=urllib.request.urlopen('https://deadrevolver.itch.io/pixel-prototype-player-sprites').read().decode()
start=page.find('More than 100');end=page.find('More animations and sprites',start);section=page[start:end]
labels=[html.unescape(re.sub('<[^>]+>',' ',s)).strip() for s in re.findall(r'<li[^>]*>(.*?)</li>',section,re.S)]
labels=[' '.join(s.split()) for s in labels]
(ROOT/'animation-inventory.json').write_text(json.dumps({'source':'https://deadrevolver.itch.io/pixel-prototype-player-sprites','scope':'Public listing labels, NOT verified complete original animation tags','items':[{'label':s,'status':'public_preview_pilot' if s in ['Idle','Run','Walk','Crouching'] else 'not_started_requires_source_audit'} for s in labels]},ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'run-manifest.json').write_text(json.dumps({'status':'CANONICAL_IN_PROGRESS','character':'human industrial field technician; new character separate from robot','scope':'canonical design + idle/walk/run/crouch public-preview pilots','direction':'left profile','cell':[64,96],'root':[32,80],'method':'imagegen','full_animation_match':'DEFERRED_UNTIL_ORIGINAL_SOURCE_AVAILABLE','main_project_modified':False},indent=2),encoding='utf-8')
print(json.dumps({'timing':records,'public_labels':len(labels)},indent=2))
