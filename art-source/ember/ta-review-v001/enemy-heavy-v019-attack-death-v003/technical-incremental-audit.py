"""Frozen H19 v003 delta audit against reviewed v002, without GPU replay."""
from pathlib import Path
from PIL import Image
import hashlib,json

B=Path(__file__).resolve().parent;P=B/'technical-package';OLD=B.parent/'enemy-heavy-v019-attack-death-v002/technical-package'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rgba=lambda p:Image.open(p).convert('RGBA')
manifest=load(P/'manifest.json');listed=manifest['files'];actual={q.relative_to(P).as_posix() for q in P.rglob('*') if q.is_file()}
cat=load(P/'output/catalog.json');oldcat=load(OLD/'output/catalog.json');rig=load(P/'rig.json');oldrig=load(OLD/'rig.json');qa=load(P/'qa/revision_audit_v003.json')
oldclips={c['action']:c for c in oldcat['clips']}
out={'manifest':{'sha256':sha(P/'manifest.json'),'listed':len(listed),'missing':sorted(set(listed)-actual),'extra':sorted(actual-set(listed)-{'manifest.json'}),
                  'bad':[f for f,r in listed.items() if not (P/f).exists() or sha(P/f)!=r['sha256'] or (P/f).stat().st_size!=r['bytes']]},
     'catalog':{'sha256':sha(P/'output/catalog.json'),'rig_sha256':sha(P/'rig.json'),'tres_sha256':sha(P/cat['tres'].removeprefix('res://')),
                'rig_hash_exact':sha(P/'rig.json')==cat['rig_sha256'],'tres_hash_exact':sha(P/cat['tres'].removeprefix('res://'))==cat['tres_sha256'],
                'unit_all_heavy':all(c['unit']=='enemy_tracked_heavy' for c in cat['clips']),'version':cat['version'],'root':cat['root'],'canvas':cat['canvas']},
     'source_files':[],'clips':[],'changed_frames':[],'preserved_frames':[]}
for q in (P/'source').rglob('*'):
    if q.is_file():out['source_files'].append({'file':q.relative_to(P).as_posix(),'sha256':sha(q),'v002_byte_exact':q.read_bytes()==(OLD/q.relative_to(P)).read_bytes()})
normalized=json.loads(json.dumps(rig))
for d,cfg in normalized['configs'].items():
    cfg['gun'].pop('fixed_receiver_pixels',None);cfg['gun'].pop('socket_clip_rect',None)
out['rig_old_fields_all_unchanged']=normalized==oldrig
out['actions_exact']=rig['actions']==oldrig['actions']
out['preserved_registration_exact']=rig['preserved']==oldrig['preserved']
out['new_config_fields']={d:{'fixed_receiver_pixels':c['gun']['fixed_receiver_pixels'],'socket_clip_rect':c['gun']['socket_clip_rect']} for d,c in rig['configs'].items()}
for c in cat['clips']:
    path=c['atlas'].removeprefix('res://');atlas=rgba(P/path);kind=c['action'].removesuffix('_'+c['direction']);state=rig['actions'][kind]
    row={'action':c['action'],'direction':c['direction'],'atlas_sha_exact':sha(P/path)==c['atlas_sha256'],'atlas_byte_preserved':(P/path).read_bytes()==(OLD/path).read_bytes(),
         'configuration_exact':c['frame_count']==state['frame_count'] and c['fps']==state['fps'] and c['loop']==state['loop'],
         'poses_v002_exact':c['poses']==oldclips[c['action']]['poses'],'frames':[]}
    for i in range(c['frame_count']):
        f=path[:-4]+f'/f{i:02d}.png';im=rgba(P/f);before=rgba(OLD/f);pix=list(im.getdata());bpix=list(before.getdata());
        change={'action':c['action'],'frame':i,'pixels':[{'xy':[n%128,n//128],'before':a,'after':z} for n,(a,z) in enumerate(zip(bpix,pix)) if a!=z]}
        if change['pixels']:
            change['count']=len(change['pixels']);out['changed_frames'].append(change)
        else:out['preserved_frames'].append({'action':c['action'],'frame':i,'byte_exact':(P/f).read_bytes()==(OLD/f).read_bytes()})
        row['frames'].append({'frame':i,'file':f,'hash_exact':sha(P/f)==c['frame_hashes'][i],'atlas_difference':sum(a!=z for a,z in zip(pix,atlas.crop((i*128,0,(i+1)*128,128)).getdata())),
                              'nonbinary_alpha':sum(a[3] not in [0,255] for a in pix),'size':list(im.size),
                              'neutral_source_rgba_difference':sum(a!=z for a,z in zip(pix,rgba(P/f'source/{c["direction"]}.png').getdata())) if i==0 else None})
    out['clips'].append(row)
expected={('attack_down_left',i) for i in [3,4]}|{('death_down_left',i) for i in range(1,8)}|{('attack_right',i) for i in [1,3,4]}|{('death_right',i) for i in range(3,8)}
out['expected_17_frame_scope_exact']={(r['action'],r['frame']) for r in out['changed_frames']}==expected
canonical=lambda obj:json.loads(json.dumps(obj))
out['revision_audit']={'sha256':sha(P/'qa/revision_audit_v003.json'),'catalog_binding_exact':qa['catalog_sha256']==out['catalog']['sha256'],
                       'baseline_zip_sha_exact':qa['baseline_zip_sha256']=='c16edaeb70592d03cd8426a584399d815bb00fd7791e3242a606abdf9ff8d192',
                       'independent_pixel_ledger_exact':canonical(qa['changed_frames'])==canonical(out['changed_frames']),
                       'author_other_keys':{k:v for k,v in qa.items() if k not in ['changed_frames']}}
oldres=load(B.parent/'enemy-heavy-v019-attack-death-v002/technical-cpu-residual-classification.json')
out['baseline_12_residual_pixels']=[{'action':r['action'],'frame':r['frame'],'xy':r['xy'],'actual_rgba':rgba(P/f'output/enemy_tracked_heavy/{r["action"]}/f{r["frame"]:02d}.png').getpixel(tuple(r['xy'])),
                                    'v002_rgba_unchanged':rgba(P/f'output/enemy_tracked_heavy/{r["action"]}/f{r["frame"]:02d}.png').getpixel(tuple(r['xy']))==tuple(r['actual_rgba'])} for r in oldres['records']]
(B/'technical-incremental-integrity.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
summary={'payload':len(listed),'manifest_failures':sum(len(out['manifest'][k]) for k in ['missing','extra','bad']),
         'source_files':len(out['source_files']),'all_sources_byte_preserved':all(r['v002_byte_exact'] for r in out['source_files']),
         'old_rig_fields_unchanged':out['rig_old_fields_all_unchanged'],'poses_all_unchanged':all(c['poses_v002_exact'] for c in out['clips']),
         'frames':sum(len(c['frames']) for c in out['clips']),'changed_frames':len(out['changed_frames']),
         'changed_rgba_pixels':sum(r['count'] for r in out['changed_frames']),'preserved_frames':len(out['preserved_frames']),
         'all_95_frame_bytes_preserved':all(r['byte_exact'] for r in out['preserved_frames']),
         'expected_frame_scope_exact':out['expected_17_frame_scope_exact'],'author_ledger_exact':out['revision_audit']['independent_pixel_ledger_exact'],
         'atlas_pixel_difference':sum(f['atlas_difference'] for c in out['clips'] for f in c['frames']),
         'nonbinary_alpha':sum(f['nonbinary_alpha'] for c in out['clips'] for f in c['frames']),
         'all_pose_configuration_and_frame_hashes_exact':all(c['configuration_exact'] and c['atlas_sha_exact'] and all(f['hash_exact'] for f in c['frames']) for c in out['clips']),
         'neutral_16_rgba_difference':sum(f['neutral_source_rgba_difference'] for c in out['clips'] for f in c['frames'] if f['frame']==0),
         'all_12_baseline_residual_rgba_unchanged':all(r['v002_rgba_unchanged'] for r in out['baseline_12_residual_pixels']),
         'changed_atlases':[c['action'] for c in out['clips'] if not c['atlas_byte_preserved']]}
(B/'technical-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
