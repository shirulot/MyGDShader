"""Incremental fixed-ZIP r1 crop closure; no producer script or GPU rerun."""
from pathlib import Path
from PIL import Image
import zipfile,json,hashlib,difflib
ROOT=Path(r'E:/dev/shader/godot-shader/godot-shader-simple');OUT=Path(__file__).parent;PKG=OUT/'package';BASE=OUT.parent/'package'
OLD=ROOT/'art-source/ember/deliveries/enemy_cutter_actions_v010_2026-10-06.zip';NEW=ROOT/'art-source/ember/deliveries/enemy_cutter_actions_v010_r1_2026-10-06.zip'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def diff(a,b):return sum(p!=q for p,q in zip(a.getdata(),b.getdata()))
with zipfile.ZipFile(OLD) as a,zipfile.ZipFile(NEW) as b:
 names=b.namelist();m=json.loads(b.read('file_hashes.json'));b.extractall(PKG);changed=[n for n in sorted(set(names)&set(a.namelist())) if a.read(n)!=b.read(n)]
 checks=[{'path':f['path'],'bytes_match':len(b.read(f['path']))==f['bytes'],'sha_matches':hashlib.sha256(b.read(f['path'])).hexdigest()==f['sha256'],'unpacked_sha_matches':sha(PKG/f['path'])==f['sha256']} for f in m['files']]
 result={'archive':{'sha256':sha(NEW),'bytes':NEW.stat().st_size,'entries':len(names),'payloads':len(checks),'crc_failure':b.testzip(),'duplicates':len(names)-len(set(names)),'unlisted':sorted(set(names)-{f['path'] for f in m['files']}),'checks':checks},'zip_diff':{'added':sorted(set(names)-set(a.namelist())),'removed':sorted(set(a.namelist())-set(names)),'changed':changed}}
 frozen=[n for n in a.namelist() if n.startswith('output/') or n.startswith('source/')]+['rig.json','action_rig.gd','entity_cutout.gdshader','verify.gd','capture.gd','preview.gd','preview.tscn','project.godot']
 result['frozen_source_art_runtime']=[{'path':n,'same_bytes':a.read(n)==b.read(n)} for n in frozen]
 text_diffs={n:''.join(difflib.unified_diff(a.read(n).decode('utf8').splitlines(True),b.read(n).decode('utf8').splitlines(True),fromfile='v010/'+n,tofile='v010-r1/'+n)) for n in ['export.gd','preview.html']}
 (OUT/'text-diff.txt').write_text(json.dumps(text_diffs,ensure_ascii=False,indent=2),encoding='utf8')
cat=read(PKG/'output/catalog_v010.json');frames=[];contacts=[]
for action,clip in cat['actions'].items():
 atlas=Image.open(PKG/f'output/{action}_v010.png').convert('RGBA');count=clip['frame_count']
 for i in range(count):
  image=Image.open(PKG/f'output/{action}/f{i:02}.png').convert('RGBA');points=[[x,y] for y in range(128) for x in range(128) if image.getpixel((x,y))[3] and not(24<=x<104 and 32<=y<112)]
  frames.append({'action':action,'frame':i,'omitted_points':points,'atlas_rgba_diff':diff(image,atlas.crop((i*128,0,(i+1)*128,128)))})
 for background,c in [('black',0),('white',255)]:
  contact=Image.new('RGBA',(80*count,80),(c,c,c,255))
  for i in range(count):
   frame=Image.open(PKG/f'output/{action}/f{i:02}.png').convert('RGBA');part=Image.alpha_composite(Image.new('RGBA',(128,128),(c,c,c,255)),frame).crop((24,32,104,112));contact.paste(part,(i*80,0))
  for scale in [1,4]:
   expected=contact if scale==1 else contact.resize((contact.width*4,320),Image.Resampling.NEAREST);actual=Image.open(PKG/f'qa/{action}_{background}_{scale}x.png').convert('RGBA');contacts.append({'action':action,'background':background,'scale':scale,'expected_size':list(expected.size),'actual_size':list(actual.size),'rgba_diff':diff(expected,actual)})
result['roi_frames']=frames;result['contact_recomputation']=contacts
receipt=read(ROOT/'art-source/ember/enemy-cutter-actions-v010/qa/cold_receipt_v010.json');result['inherited_cold_core_to_r1']=[{'path':f['path'],'same_original_cold_sha':sha(PKG/f['path'])==f['sha256']} for f in receipt['core_files']]
result['inherited_validation']=read(PKG/'qa/inherited_validation_r1.json')
result['inherited_receipt_sha_matches']=sha(ROOT/result['inherited_validation']['cold_receipt'])==result['inherited_validation']['cold_receipt_sha256']
served=ROOT/'art-source/ember/enemy-sequences-v001/previews/cutter-actions-v010-r1';paths=['preview.html','output/catalog_v010.json']+[f'output/{a}_v010.png' for a in cat['actions']]+[f'qa/{a}_{bg}_4x.png' for a in cat['actions'] for bg in ['black','white']]
result['served_bindings']=[{'package_path':p,'served_path':'index.html' if p=='preview.html' else p,'same_package_sha':sha(served/('index.html' if p=='preview.html' else p))==sha(PKG/p)} for p in paths]
result['html_roi_confirmed']='canvas.width=80*scale;canvas.height=80*scale' in (PKG/'preview.html').read_text(encoding='utf8') and 'phase(fps)*128+24,32,80,80' in (PKG/'preview.html').read_text(encoding='utf8')
result['summary']={'all_manifest':all(all(c[k] for k in ['bytes_match','sha_matches','unpacked_sha_matches']) for c in checks),'frozen_files':len(result['frozen_source_art_runtime']),'frozen_all_same':all(c['same_bytes'] for c in result['frozen_source_art_runtime']),'frames':len(frames),'omitted_pixels':sum(len(f['omitted_points']) for f in frames),'contacts':len(contacts),'contacts_rgba_diff':sum(c['rgba_diff'] for c in contacts),'served_all_same':all(c['same_package_sha'] for c in result['served_bindings']),'cold_core_changed_paths':[f['path'] for f in result['inherited_cold_core_to_r1'] if not f['same_original_cold_sha']]}
(OUT/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'archive':{k:v for k,v in result['archive'].items() if k!='checks'},'summary':result['summary']},ensure_ascii=False,indent=2))
