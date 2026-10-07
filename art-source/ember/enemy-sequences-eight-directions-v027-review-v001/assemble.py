"""Assemble only explicitly approved immutable clips; never regenerate image pixels."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
arg=argparse.ArgumentParser();arg.add_argument('--rehearsal',action='store_true');options=arg.parse_args()
SCRIPT_ROOT=Path(__file__).resolve().parent
BASE=SCRIPT_ROOT.parent;REPO=SCRIPT_ROOT.parents[2];W=BASE/'enemy-eight-directions-v013'
ROOT=BASE/'qa-cold/enemy_eight_direction_assembly_rehearsal_v001' if options.rehearsal else SCRIPT_ROOT
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inventory=json.loads((W/'clip_inventory_v013.json').read_text(encoding='utf-8'))
ledger=json.loads((W/'animation_review_ledger.json').read_text(encoding='utf-8'))
assert len(inventory['clips'])==160 and sum(c['frame_count'] for c in inventory['clips'])==960
unapproved=[(c['unit'],c['action'],c['status']) for c in inventory['clips'] if c['status'] not in ['TA_APPROVED','PRESERVED_TA_APPROVED']]
assert options.rehearsal or not unapproved,unapproved
if options.rehearsal:
    # 隔离彩排仅调试新汇总代码，绝不写入最终包、审核台账或项目资源。
    assert not ROOT.exists(),'Rehearsal already exists'
    ROOT.mkdir(parents=True)
    for p in SCRIPT_ROOT.iterdir():
        if p.is_file() and (p.suffix in ['.gd','.tscn','.md'] or p.name=='project.godot'):shutil.copy2(p,ROOT/p.name)
assert not (ROOT/'manifest.json').exists(),'Do not overwrite a frozen assembly'
for d in ['output','qa','previews','reviewed_packages','review_reports']:(ROOT/d).mkdir(parents=True,exist_ok=True)
def copy(source,target,expected=None):
    if expected:assert sha(source)==expected,str(source)
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    assert sha(target)==sha(source)
batches={b['folder']:b for b in ledger['batches']}
clips=[];used={}
for c in inventory['clips']:
    source=BASE/c['source'];rel=Path('output')/c['unit']/c['action']
    copy(source/rel.with_suffix('.png'),ROOT/rel.with_suffix('.png'),c['atlas_sha256'])
    for i,expected in enumerate(c['frame_hashes']):copy(source/rel/f'f{i:02}.png',ROOT/rel/f'f{i:02}.png',expected)
    if c['action'].startswith('idle_'):copy(ROOT/rel/'f00.png',ROOT/'output'/c['unit']/f"neutral_{c['direction']}.png")
    clip=dict(c);clip['atlas']='res://'+rel.with_suffix('.png').as_posix()
    # 每条动作直接携带ZIP与回执，不要求使用者从全局表猜它属于哪一批。
    if c['source']=='enemy-sequences-v012':
        clip.update(source_zip_sha256='42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe',source_catalog='assembly_recipe.json',review_report='art-source/ember/ta-review-v001/enemy-v012-independent/assembly-review.md')
    else:
        batch=batches[c['source']]
        clip.update(source_zip_sha256=batch['zip_sha256'],source_catalog=batch['catalog'],review_report=batch.get('review_report'))
    if clip['review_report']:
        clip['included_review']='review_reports/'+c['source']+'/'+Path(clip['review_report']).name
    clips.append(clip)
    if c['source']!='enemy-sequences-v012':used[c['source']]=batches[c['source']]
source_packages={b['zip_sha256']:dict(folder=b['folder'],review_report=b.get('review_report'),status=b['status']) for b in used.values()}
source_packages['42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe']=dict(folder='enemy-sequences-v012',review_report='art-source/ember/ta-review-v001/enemy-v012-independent/assembly-review.md')
remaining=set() if options.rehearsal else set(source_packages)
for p in (BASE/'deliveries').glob('*.zip'):
    digest=sha(p)
    if digest not in remaining:continue
    copy(p,ROOT/'reviewed_packages'/p.name,digest)
    source_packages[digest]['zip']='reviewed_packages/'+p.name
    remaining.remove(digest)
assert not remaining,remaining
for digest,m in source_packages.items():
    if options.rehearsal:continue
    p=REPO/m['review_report'];assert p.exists(),p
    relative=Path('review_reports')/m['folder']/p.name
    copy(p,ROOT/relative)
    m['included_review']=relative.as_posix();m['review_sha256']=sha(p)
for name in ['c22_v002_source_receipt_correction.json','p21_v003_preview_title_erratum.json']:
    p=W/'qa'/name
    if p.exists():copy(p,ROOT/'review_reports/errata'/name)
recipe=dict(version='v027-eight-directions-assembly',status='INTEGRATION_REHEARSAL_NOT_APPROVED' if options.rehearsal else 'ALL_ART_APPROVED_ASSEMBLY_PENDING_TA_REVIEW',canvas=[128,128],root=[64,104],target_clips=160,target_frames=960,units=['enemy_patrol','enemy_tracked_heavy','enemy_cutter','enemy_scout_drone'],directions=['down','down_left','left','up_left','up','up_right','right','down_right'],clips=clips,source_packages=source_packages)
(ROOT/'assembly_recipe.json').write_text(json.dumps(recipe,indent=2),encoding='utf-8')
(ROOT/'output/catalog.json').write_text(json.dumps(recipe,indent=2),encoding='utf-8')
(ROOT/'TA_ACCEPTANCE.json').write_text(json.dumps(dict(status=recipe['status'],clips=[dict(unit=c['unit'],action=c['action'],status=c['status'],source=c['source'],source_zip_sha256=c['source_zip_sha256'],review_report=c.get('review_report'),included_review=c.get('included_review')) for c in clips],source_packages=source_packages),indent=2),encoding='utf-8')
subprocess.run([sys.executable,str(SCRIPT_ROOT/'write_resources.py'),'--directory',str(ROOT)],check=True)
print(json.dumps(dict(status=recipe['status'],clips=len(clips),frames=sum(c['frame_count'] for c in clips),reviewed_archives=0 if options.rehearsal else len(source_packages),destination=str(ROOT))))
