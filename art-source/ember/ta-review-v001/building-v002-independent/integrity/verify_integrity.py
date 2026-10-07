"""Read only fixed package/production; write evidence only beside this script."""
from pathlib import Path
from PIL import Image
from collections import Counter
import json, hashlib, zipfile, math, re

ROOT = Path('E:/dev/shader/godot-shader/godot-shader-simple')
OUT = Path(__file__).parent
PKG = OUT / 'package'
GROUPS = ['RearShell','Roof','FrontWall','DoorLeaves','DoorFrames','FrontAccessories']

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def path(value): return PKG / value.removeprefix('res://')
def img(value): return Image.open(path(value)).convert('RGBA')
def diff(a,b):
    assert a.size == b.size
    return sum(p != q for p,q in zip(a.getdata(),b.getdata()))
def copy_mask(dst, src, xy=(0,0)):
    # All accepted parts are binary-alpha. Copy actual RGBA, with no blend/scale.
    dp,sp=dst.load(),src.load(); dx,dy=map(int,xy); lost=0
    for y in range(src.height):
        for x in range(src.width):
            p=sp[x,y]
            if not p[3]: continue
            if not (0 <= x+dx < dst.width and 0 <= y+dy < dst.height): lost+=1;continue
            dp[x+dx,y+dy]=p
    return lost
def rgba_stats(image):
    pixels=list(image.getdata()); bb=image.getchannel('A').getbbox()
    return {'canvas':list(image.size),'visible':sum(p[3]>0 for p in pixels),'partial_alpha':sum(0<p[3]<255 for p in pixels),'alpha_values':sorted(set(p[3] for p in pixels)),'bbox_xywh':None if bb is None else [bb[0],bb[1],bb[2]-bb[0],bb[3]-bb[1]]}
def snake(value): return re.sub(r'(?<!^)(?=[A-Z])','_',value).lower()

archive=ROOT/'art-source/ember/deliveries/building_assets_v002_2026-10-06.zip'
old_archive=ROOT/'art-source/ember/deliveries/building_assets_v001_2026-10-06.zip'
result={'scope':'Independent fixed ZIP source/composition/prefab-definition increment. No Godot runtime or production mutation.'}
with zipfile.ZipFile(archive) as z,zipfile.ZipFile(old_archive) as old:
    names=z.namelist(); manifest=json.loads(z.read('portable_file_manifest_v002.json'))
    entries=manifest['files']; checks=[]
    for e in entries:
        b=z.read(e['path'])
        checks.append({'path':e['path'],'sha_match':hashlib.sha256(b).hexdigest()==e['sha256'],'bytes_match':len(b)==e['bytes'],'extracted_sha_match':sha(PKG/e['path'])==e['sha256']})
    shared=set(names)&set(old.namelist())
    same=sorted(n for n in shared if z.read(n)==old.read(n));changed=sorted(shared-set(same))
    protected_source_prefixes=('art-source/ember/building-assets-v001/','art-source/ember/selected-buildings-v001/references/','assets/ember/building_assets_v001/')
    inherited=[{'path':n,'same_v001_bytes':z.read(n)==old.read(n)} for n in sorted(shared) if n.startswith(protected_source_prefixes)]
    original_resources=[{'path':n,'same_v001_bytes':z.read(n)==old.read(n),'same_workspace_bytes':sha(ROOT/n)==hashlib.sha256(z.read(n)).hexdigest()} for n in sorted(names) if n.startswith('assets/') and not n.startswith(('assets/ember/building_assets_v001/','assets/ember/building_assets_v002/'))]
    result['archive']={'sha256':sha(archive),'bytes':archive.stat().st_size,'entries':len(names),'manifest_entries':len(entries),'duplicates':len(names)-len(set(names)),'crc_failure':z.testzip(),'unlisted':sorted(set(names)-{e['path'] for e in entries}),'cache_or_import_paths':[n for n in names if n.endswith('.import') or '/.godot/' in n],'checks':checks,'unchanged_common_count':len(same),'changed_common':changed,'old_archive_sha256':sha(old_archive)}
    result['inherited_source_payloads']=inherited
    result['inherited_nonbuilding_resources']=original_resources

legacy=read(PKG/'assets/ember/building_assets_v001/catalog_v001.json')
new=read(PKG/'assets/ember/building_assets_v002/catalog_v002.json')
la={a['id']:a for a in legacy['assets']}; na={a['id']:a for a in new['assets']}
nb={b['id']:b for b in new['buildings']}
generation=read(PKG/'art-source/ember/building-assets-v001/generation_manifest_v001.json')
result['binding']={'catalog_sha256':sha(PKG/'assets/ember/building_assets_v002/catalog_v002.json'),'expected_catalog_sha_match':sha(PKG/'assets/ember/building_assets_v002/catalog_v002.json')=='9a89de864acdcccaf98e3ed6cefab71a89d1edbb9145ae3ebc1cb32b587ed8c1','source_catalog_match':sha(path(new['source_catalog']))==new['source_catalog_sha256'],'source_runtime_match':sha(PKG/'scripts/ember/building_asset_v001.gd')==new['source_runtime_sha256'],'composition_tool_match':sha(PKG/'tools/compose_buildings_v002.gd')==new['composition_tool_sha256'],'accepted_sources':len(generation['sources']),'rejected_sources':len(generation['rejected']),'legacy_asset_count':len(la),'new_functional_layer_count':len(na),'new_ids_unique':len(new['assets'])==len(na),'source_alpha_partial_total':sum(rgba_stats(img(a['texture']))['partial_alpha'] for a in la.values())}

# Recreate v001 registration from its independently accepted catalog and actual
# source runtime rules; do not accept v002 source_members as geometry authority.
result['buildings']=[]; result['layer_checks']=[]
for b in legacy['buildings']:
    bid=b['id']; size=tuple(map(int,b['canvas_px']));pivot=tuple(map(int,b['pivot_px'])); expected={g:[] for g in GROUPS}
    door_ids={d['id'] for d in b['doors']}
    def add(sid,group,point,rank,kind='static',device='',door=None):
        a=la[sid]; source_rect=list(map(int,[0,0,*a['canvas_px']]))
        dest=[int(pivot[i]+point[i]-a['pivot_px'][i]) for i in (0,1)]
        extra={}
        if door is not None:
            source_rect=list(map(int,a['visible_rect_px']))
            dest=[int(pivot[0]+door['center_x']-door['clear_px'][0]/2),int(pivot[1]-door['clear_px'][1])]
            extra['door_id']=door['id']
        if kind=='rotor':
            r=a['visible_rect_px']; center=[r[0]+r[2]/2,r[1]+r[3]/2]
            extra['rotation_center_local_px']=[point[i]+center[i]-a['pivot_px'][i] for i in (0,1)]
        if kind=='lens':
            extra['device_id']=device
            r=a['visible_rect_px'];extra['visible_rect_px']=[dest[0]+int(r[0])-source_rect[0],dest[1]+int(r[1])-source_rect[1],int(r[2]),int(r[3])]
        member={'source_id':sid,'source_texture':a['texture'],'source_sha256':sha(path(a['texture'])),'source_rect_px':source_rect,'destination_px':dest}
        expected[group].append({'member':member,'rank':rank,'kind':kind,'extra':extra})
    add(bid+'_rear_wall','RearShell',[0,-b['footprint_px'][1]],-10)
    for suffix in ['roof_center','roof_trim']:add(bid+'_'+suffix,'Roof',[0,-b['wall_height_px']+8],-10)
    if bid=='control_tower':
        for suffix in ['lower_wall','upper_wall','storey_band']:add(bid+'_'+suffix,'FrontWall',[0,0],-10)
    else:add(bid+'_front_wall','FrontWall',[0,0],-10)
    for m in b['mounts']:
        sid=m['asset']; group='Roof' if m.get('layer')=='roof' else 'FrontWall'
        if m.get('layer')=='front' and sid in ['control_panel','lamp_housing']:group='FrontAccessories'
        rank=0 if sid.endswith(('glass','interior')) or sid=='fan_rotor' else 1
        if sid.endswith('lid'):rank=2
        kind='glass' if sid.endswith('glass') else {'fan_rotor':'rotor','maintenance_lid':'maintenance_lid','maintenance_interior':'maintenance_interior','roof_hatch_lid':'roof_hatch_lid'}.get(sid,'static')
        add(sid,group,m['position_px'],rank,kind)
        mask={'lamp_housing':'lamp_lens_mask','control_panel':'panel_display_mask','service_unit':'service_unit_indicator_mask'}.get(sid)
        if mask:add(mask,group,m['position_px'],2,'lens',m.get('device_id',''))
    for d in b['doors']:
        add(d['frame'],'DoorFrames',[d['center_x'],0],1)
        add(d['leaf'],'DoorLeaves',[d['center_x'],0],0,'door_leaf',door=d)
    whole=Image.new('RGBA',size);shell=Image.new('RGBA',size); recipe=[]; groups={}
    def placed(member):
        r=member['source_rect_px']; source=img(member['source_texture']).crop((r[0],r[1],r[0]+r[2],r[1]+r[3])); dest=Image.new('RGBA',size)
        assert copy_mask(dest,source,member['destination_px'])==0
        return dest
    def emit(group,kind,items):
        global_counter=len(recipe)
        lid=bid+'_'+snake(group)+'_'+kind+'_'+str(global_counter).zfill(2)
        a=na[lid]; pixels=Image.new('RGBA',size)
        members=[item['member'] for item in items]
        for member in members:copy_mask(pixels,placed(member))
        actual=img(a['texture']);stats=rgba_stats(actual);extra=items[0]['extra'] if kind not in ['static','glass'] else {}
        check={'id':lid,'source_members_match_actual_v001_registration':a['source_members']==members,'whole_canvas_pivot_match':a['canvas_px']==b['canvas_px'] and a['pivot_px']==b['pivot_px'],'role_group_kind_match':a['group']==group and a['kind']==kind and a['role']==kind,'extra_fields_match':all(a[k]==v for k,v in extra.items()),'initial_visible':a['initial_visible']==True,'texture_sha_match':sha(path(a['texture']))==a['texture_sha256'],'rgba_diff':diff(pixels,actual),'visible_rect_match':stats['bbox_xywh']==a['visible_rect_px'],'stats':stats}
        result['layer_checks'].append(check);recipe.append({'asset':lid,'group':group,'kind':kind})
    for group in GROUPS:
        items=sorted(expected[group],key=lambda x:x['rank']);groups[group]=items; batch=[];kind=None
        for item in items:
            pixels=placed(item['member']);visual=pixels.copy()
            if item['kind']=='lens':
                is_active=item['member']['source_id']=='lamp_lens_mask' and item['extra']['device_id'] in door_ids
                tint=(.72,.49,.29,1) if is_active else (.32,.77,.75,1)
                visual.putdata([tuple(math.floor(p[i]*tint[i]+.5) for i in range(4)) if p[3] else p for p in visual.getdata()])
            copy_mask(whole,visual)
            if item['kind']=='static':copy_mask(shell,pixels)
            if item['kind'] in ['static','glass']:
                if batch and kind!=item['kind']:emit(group,kind,batch);batch=[]
                kind=item['kind'];batch.append(item)
            else:
                if batch:emit(group,kind,batch);batch=[]
                emit(group,item['kind'],[item])
        if batch:emit(group,kind,batch)
    definition=nb[bid];actualwhole=img(definition['complete_closed_texture']);actualshell=img(definition['fixed_shell_texture'])
    # Parse static scene registration, and interactive script/catalog chain.
    static=(PKG/f'scenes/ember/building_assets_v002/{bid}_static.tscn').read_text(encoding='utf8')
    interactive=(PKG/f'scenes/ember/building_assets_v002/{bid}.tscn').read_text(encoding='utf8')
    inheritance=(PKG/'scripts/ember/building_asset_v002.gd').read_text(encoding='utf8')
    source_fields=['id','canvas_px','pivot_px','footprint_px','wall_height_px','doors','mounts']
    entry={'id':bid,'recipe_layer_count':len(recipe),'kind_counts':dict(Counter(x['kind'] for x in recipe)),'definition_source_geometry_same':all(definition[k]==b[k] for k in source_fields),'recipe_match':definition['render_layers']==recipe,'whole_rgba_diff':diff(whole,actualwhole),'shell_rgba_diff':diff(shell,actualshell),'whole_sha_match':sha(path(definition['complete_closed_texture']))==definition['complete_closed_sha256'],'shell_sha_match':sha(path(definition['fixed_shell_texture']))==definition['fixed_shell_sha256'],'whole_stats':rgba_stats(actualwhole),'shell_stats':rgba_stats(actualshell),'static_one_sprite':len(re.findall(r'^\[node ',static,re.M))==1 and 'type="Sprite2D"' in static,'static_texture_bound':definition['complete_closed_texture'] in static,'static_pivot_bound':f'offset = Vector2({-pivot[0]}, {-pivot[1]})' in static and 'centered = false' in static,'static_no_scale_or_rotation':not re.search(r'^\s*(scale|rotation)\s*=',static,re.M),'interactive_script_id_bound':'res://scripts/ember/building_asset_v002.gd' in interactive and f'building_id = "{bid}"' in interactive,'new_runtime_catalog_bound':'catalog_path = "res://assets/ember/building_assets_v002/catalog_v002.json"' in inheritance,'new_runtime_loads_recipe': 'for layer: Dictionary in definition.render_layers:' in inheritance,'reconstructed_geometry':{g:[i['member'] for i in items] for g,items in groups.items()}}
    result['buildings'].append(entry)
    whole.save(OUT/f'independent_{bid}_complete_closed.png');shell.save(OUT/f'independent_{bid}_fixed_shell.png')

history=read(ROOT/'art-source/ember/ta-review-v001/ui-v003-integrity/integrity-v003.json')
result['protected_workspace_history']=[{'path':e['path'],'baseline_sha256':e['sha256'],'current_sha256':sha(ROOT/e['path']),'same_baseline':sha(ROOT/e['path'])==e['sha256']} for e in history['checks'] if e['scope']=='protected_workspace']
result['user_reference_current']=[{'path':str(p.relative_to(PKG)).replace('\\','/'),'same_workspace':sha(p)==sha(ROOT/p.relative_to(PKG)),'sha256':sha(p)} for p in (PKG/'art-source/ember/selected-buildings-v001/references').glob('*.png')]
result['summary']={'archive_checks_pass':all(all(e[k] for k in ['sha_match','bytes_match','extracted_sha_match']) for e in result['archive']['checks']),'inherited_source_equal':all(e['same_v001_bytes'] for e in result['inherited_source_payloads']),'all_layers_rgba_diff':sum(e['rgba_diff'] for e in result['layer_checks']),'all_whole_rgba_diff':sum(e['whole_rgba_diff'] for e in result['buildings']),'all_shell_rgba_diff':sum(e['shell_rgba_diff'] for e in result['buildings']),'all_source_geometry_recipe_match':all(e['source_members_match_actual_v001_registration'] for e in result['layer_checks']) and all(e['recipe_match'] and e['definition_source_geometry_same'] for e in result['buildings']),'all_partial_alpha':sum(e['stats']['partial_alpha'] for e in result['layer_checks'])+sum(e['whole_stats']['partial_alpha']+e['shell_stats']['partial_alpha'] for e in result['buildings'])}
(OUT/'integrity-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'archive':{k:v for k,v in result['archive'].items() if k!='checks'},'binding':result['binding'],'summary':result['summary'],'buildings':[{k:v for k,v in e.items() if k!='reconstructed_geometry'} for e in result['buildings']],'protection':result['protected_workspace_history'],'nonbuilding_resources':result['inherited_nonbuilding_resources']},ensure_ascii=False,indent=2))
