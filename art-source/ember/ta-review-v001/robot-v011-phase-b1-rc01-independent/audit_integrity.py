"""只读固定候选；独立计算manifest、旧稿、图集及来源合成，证据写在TA目录。"""
from pathlib import Path
from PIL import Image
import collections, hashlib, json, math, re, zipfile

HERE = Path(__file__).resolve().parent
PACK = HERE / 'package'
REPO = HERE.parents[3]
PALETTE = [tuple(bytes.fromhex(h)) for h in ['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A']]
DIRECTIONS = ['up_left','up','up_right','down_right']
W, H = 64, 96
def sha(data): return hashlib.sha256(data).hexdigest()
def load(path): return json.loads((PACK/path).read_text(encoding='utf-8-sig'))
def rgba(path): return Image.open(PACK/path).convert('RGBA')
def mismatch(a,b): return sum(x!=y for x,y in zip(a.getdata(),b.getdata()))

manifest=load('sha256-manifest.json')
listed=[x['file'] for x in manifest['files']]
actual=[p.relative_to(PACK).as_posix() for p in PACK.rglob('*') if p.is_file()]
manifest_result={'listed':len(listed),'unique':len(set(listed)),'extra':sorted(set(actual)-set(listed)-{'sha256-manifest.json'}),'missing':sorted(set(listed)-set(actual)), 'bad':[]}
for x in manifest['files']:
    p=PACK/x['file']
    if not p.is_file() or len(p.read_bytes())!=x['bytes'] or sha(p.read_bytes())!=x['sha256']:manifest_result['bad'].append(x['file'])

old_zip=REPO/'art-source/ember/deliveries/robot_eight_way_v011_phase_a_rc02_2026-10-06.zip'
meta=load('walk-batch-metadata.json');old_meta=load('source/approved-phase-a-rc02-metadata.json')
baseline=[]
with zipfile.ZipFile(old_zip) as z:
    for f in old_meta['source_files']:
        current=(PACK/f['file']).read_bytes(); previous=z.read(f['file'])
        baseline.append({'file':f['file'],'current_sha256':sha(current),'expected_sha256':f['sha256'],'old_zip_exact':current==previous,'metadata_sha_exact':sha(current)==f['sha256']})
    stored_old=z.read('phase-a-metadata.json') if 'phase-a-metadata.json' in z.namelist() else z.read('godot-review/phase-a-metadata.json')
    old_metadata_exact=(PACK/'source/approved-phase-a-rc02-metadata.json').read_bytes()==stored_old
baseline_result={'old_zip_sha256':sha(old_zip.read_bytes()),'approved_metadata_exact_old_zip':old_metadata_exact,'files':baseline}

atlas=rgba(meta['atlas']);atlas_rows=[];format_checks=[]
for f in meta['source_files']:
    im=rgba(f['file']);x,y,w,h=f['region'];region=atlas.crop((x,y,x+w,y+h))
    atlas_rows.append({'file':f['file'],'sha_exact':sha((PACK/f['file']).read_bytes())==f['sha256'],'atlas_rgba_mismatch':mismatch(im,region)})
    colors=collections.Counter(im.getdata());format_checks.append({'file':f['file'],'size':list(im.size),'nonbinary_alpha_pixels':sum(n for p,n in colors.items() if p[3] not in [0,255]),'off_palette_opaque_pixels':sum(n for p,n in colors.items() if p[3] and p[:3] not in PALETTE)})
atlas_result={'size':list(atlas.size),'sha256':sha((PACK/meta['atlas']).read_bytes()),'root_atlas_matches_metadata':sha((PACK/meta['atlas']).read_bytes())==meta['atlas_sha256'],'godot_atlas_byte_exact':(PACK/meta['atlas']).read_bytes()==(PACK/'godot-walk-review/assets'/meta['atlas']).read_bytes(),'godot_metadata_byte_exact':(PACK/'walk-batch-metadata.json').read_bytes()==(PACK/'godot-walk-review/walk-batch-metadata.json').read_bytes(),'frames':atlas_rows,'format':format_checks}

def stamp(canvas,part,t):
    # 独立按公开的像素中心逆映射规则重算刚体最近邻；不调用制作方render函数。
    out=canvas.load();src=part.load();c=math.cos(t['radians']);s=math.sin(t['radians'])
    px,py=t['sourcePivot'];tx,ty=t['targetPivot']
    for y in range(H):
        for x in range(W):
            dx=x+.5-tx;dy=y+.5-ty;sx=math.floor(dx*c+dy*s+px);sy=math.floor(-dx*s+dy*c+py)
            if 0<=sx<W and 0<=sy<H and src[sx,sy][3]:out[x,y]=src[sx,sy]
def render(parts,rig,state):
    out=Image.new('RGBA',(W,H))
    for id in rig['limb_order']:
        if id=='body':stamp(out,parts['body'],state['transforms']['body']);continue
        for seg in ['end','lower','upper']:
            key=id+'_'+seg
            if key in parts:stamp(out,parts[key],state['transforms'][key])
    return out
def protection(part,lo,hi):
    pts=[(x,y) for y in range(max(0,math.ceil(lo)),min(H-1,math.floor(hi))+1) for x in range(W) if part.getpixel((x,y))[3]]
    im=Image.new('RGBA',(W,H))
    if pts:
        x0=max(0,min(x for x,y in pts)-1);x1=min(W-1,max(x for x,y in pts)+1);y0=min(y for x,y in pts);y1=max(y for x,y in pts)
        for y in range(y0,y1+1):
            for x in range(x0,x1+1):im.putpixel((x,y),(255,255,255,255))
    return im

sources=[]
for direction in DIRECTIONS:
    ledger=load(f'source/fixed-rig-pilot/{direction}/rig_and_poses.json');rig=ledger['rig'];parts={x['id']:rgba(x['file']) for x in ledger['parts']}
    master=rgba(ledger['source_file']);neutral=Image.new('RGBA',(W,H));part_check=[]
    for id in rig['limb_order']:
        ids=['body'] if id=='body' else [id+'_'+seg for seg in ['end','lower','upper'] if id+'_'+seg in parts]
        for key in ids:
            part=parts[key]
            for y in range(H):
                for x in range(W):
                    if part.getpixel((x,y))[3]:neutral.putpixel((x,y),part.getpixel((x,y)))
    for x in ledger['parts']:
        part=parts[x['id']];part_check.append({'part':x['id'],'raw_sha_exact':sha(part.tobytes())==x['raw_sha256'],'opaque_rgba_not_from_same_master':sum(part.getpixel((px,py))[3]>0 and part.getpixel((px,py))!=master.getpixel((px,py)) for py in range(H) for px in range(W))})
    guards={}
    for key,part in parts.items():
        if key=='body':guards[key]=part.copy();continue
        lid=re.sub(r'_(upper|lower|end)$','',key);l=rig['limbs'][lid]
        if key.endswith('_end'):lo,hi=0,H-1
        elif l['kind']=='leg':lo,hi=(0,math.floor(l['joint'][1]-2.5)) if key.endswith('_upper') else (math.ceil(l['joint'][1]+2),math.floor(l['end'][1]-2))
        else:lo,hi=(0,math.floor(l['joint'][1]-1.5)) if key.endswith('_upper') else (math.ceil(l['joint'][1]+2),H-1)
        guards[key]=protection(part,lo,hi)
    # Sharp/Vips与Pillow的nearest注册规则不同，不将Pillow重采样当生产差异。
    # 量化源的raw→Sharp重算由单独TA脚本核查；此处独立核其固定格合成。
    patch_report=load(f'qa/{direction}_joint_patch_v011.json')
    quantized=rgba(f'source/walk_{direction}_joint_edit_quantized_v011.png')
    fs=[]
    for i,state in enumerate(ledger['states']):
        original=render(parts,rig,state);name=f'robot_walk_{direction}_f{i:02d}_v011.png';stored_raw=rgba(f'source/fixed-rig-pilot/{direction}/{name}');final=rgba(f'frames/walk/{direction}/{name}');guard=render(guards,rig,state);mask=Image.new('RGBA',(W,H));expected=original.copy();regions=[]
        for lid,j in state['joints'].items():
            if lid.startswith('leg'):
                regions.extend([{'id':lid+'_hip','center':j['root'],'rx':3.2,'ry':3.2},{'id':lid+'_knee','center':j['joint'],'rx':4.8,'ry':4.8},{'id':lid+'_ankle','center':j['ankle'],'rx':4,'ry':3.5}])
            else:
                regions.extend([{'id':lid+'_shoulder','center':j['root'],'rx':3.4,'ry':3.4},{'id':lid+'_elbow','center':j['joint'],'rx':3.5,'ry':3.5}])
        # 独立重算可编辑区域；补丁采样固定整张4×2网格，无逐帧bbox注册。
        for y in range(H):
            for x in range(W):
                if y<45 or guard.getpixel((x,y))[3] or not any(((x+.5-q['center'][0])/q['rx'])**2+((y+.5-q['center'][1])/q['ry'])**2<=1 for q in regions):continue
                patch_pixel=quantized.getpixel(((i%4)*W+x,(i//4)*H+y))
                if not patch_pixel[3] and original.getpixel((x,y))[3]:continue
                mask.putpixel((x,y),(255,255,255,255));expected.putpixel((x,y),patch_pixel)
        changed=[(x,y) for y in range(H) for x in range(W) if original.getpixel((x,y))!=final.getpixel((x,y))]
        fs.append({'frame':i,'raw_rigid_reconstruction_mismatch':mismatch(original,stored_raw),'joint_composite_reconstruction_mismatch':mismatch(expected,final),'declared_mask_reconstruction_mismatch':mismatch(mask,rgba(f'qa/{direction}_joint_mask_f{i:02d}.png')),'declared_regions_match_independent_ledger_regions':regions==patch_report['records'][i]['regions'],'changed_pixels':len(changed),'protected_pixels_changed':sum(guard.getpixel(xy)[3]>0 for xy in changed),'outside_mask_changed':sum(mask.getpixel(xy)[3]==0 for xy in changed),'opaque_joint_erased':sum(original.getpixel(xy)[3]>0 and final.getpixel(xy)[3]==0 for xy in changed)})
    sources.append({'direction':direction,'source_sha_exact':sha((PACK/ledger['source_file']).read_bytes())==ledger['source_sha256'],'parts_count':len(parts),'parts':part_check,'neutral_reassembly_mismatch':mismatch(neutral,master),'body_opaque_below_y64':sum(parts['body'].getpixel((x,y))[3]>0 for y in range(64,H) for x in range(W)),'joint_raw_source_sha_exact':sha((PACK/patch_report['source_file']).read_bytes())==patch_report['source_sha256'],'joint_quantization_note':'raw→quantized independently checked with the declared Sharp/Vips nearest API by check_quantized_sources.cjs','qa_fixed_ledger_byte_equal':(PACK/f'source/fixed-rig-pilot/{direction}/rig_and_poses.json').read_bytes()==(PACK/f'qa/{direction}_fixed_rig_v011.json').read_bytes(),'frames':fs})

result={'manifest':manifest_result,'approved_baseline':baseline_result,'atlas':atlas_result,'new_direction_sources':sources,'scope':'independent file/decoded pixel/source-mask audit only; no visual approval or GPU replay'}
(HERE/'independent-pixel-integrity.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('MANIFEST',manifest_result)
print('BASELINE',len(baseline),'oldZIP',baseline_result['old_zip_sha256'],'metadata exact',old_metadata_exact,'all files exact',all(x['old_zip_exact'] and x['metadata_sha_exact'] for x in baseline))
print('ATLAS',atlas.size,'56 frame mismatches',sum(x['atlas_rgba_mismatch'] for x in atlas_rows),'copies',atlas_result['godot_atlas_byte_exact'],atlas_result['godot_metadata_byte_exact'])
for x in sources:
    print('SOURCE',x['direction'],'parts',x['parts_count'],'neutral',x['neutral_reassembly_mismatch'],'frames',[(q['frame'],q['raw_rigid_reconstruction_mismatch'],q['joint_composite_reconstruction_mismatch'],q['declared_mask_reconstruction_mismatch'],q['protected_pixels_changed'],q['outside_mask_changed'],q['opaque_joint_erased']) for q in x['frames']])
