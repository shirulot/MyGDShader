"""18对象的AI辅助原生像素整理与可编辑组件导出（只写本batch）。

大母稿提供设计与材料候选：5x5多数Alpha/中值色采样只生成未验收草案。
最终必须有逐资产视觉标注；本脚本做固定调色板、原生1px轮廓、孤点简化，
再执行窗口/孔洞/安装点/可动件的语义像素修正。它不会声称缩图就是生产定稿。
所有矩形默认[x0,y0,x1,y1)右下排除；slice_region另明确采用[x,y,w,h]。
组件是同画布RGBA PNG和二值选择mask，可重新编辑并按z序合成；不伪报PSD。
"""
from __future__ import annotations
import argparse
from collections import Counter,deque
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[2]
EMPTY=(0,0,0,0)
HEX=('101820','182631','2B3E4B','4D6470','829BA3','BECBC4','7B4D35','B77C4B',
     'E2B77A','51C5C2','E5A44B','E65B4A','566B78','203A4B','406B78','ECE9D8')
COLORS=[tuple(bytes.fromhex(h))+(255,) for h in HEX]
STATIC=(0,1,2,3,4,5,6,7,8,12,15)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rel(path):return Path(path).resolve().relative_to(ROOT).as_posix()
def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save_json(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def nearest(rgb):return COLORS[min(STATIC,key=lambda i:sum((rgb[c]-COLORS[i][c])**2 for c in range(3)))]

def keep_subject(im):
    """清除8邻域孤立alpha碎片，不对孔洞填充，不扩张轮廓。"""
    remaining={(x,y) for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3]}
    components=[]
    while remaining:
        p=remaining.pop();q=deque([p]);part={p}
        while q:
            x,y=q.popleft()
            for dx,dy in ((-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)):
                z=(x+dx,y+dy)
                if z in remaining:remaining.remove(z);part.add(z);q.append(z)
        components.append(part)
    if not components:raise ValueError('采样主体为空')
    # 当前18物均单个相连实体；开门两侧由真实lintel连接，小孤点不是悬浮部件。
    largest=max(components,key=len)
    removed=0
    for part in components:
        if part is largest:continue
        for p in part:im.putpixel(p,EMPTY);removed+=1
    return removed

def sample_material(source,spec,annotation):
    alpha=source.getchannel('A')
    if alpha.getextrema()[0]>=240:raise ValueError('母稿无真实透明背景，禁止自动把绘制棋盘格算合格')
    crop=annotation.get('source_subject_crop') or alpha.point(lambda a:255 if a>=240 else 0).getbbox()
    if not crop:raise ValueError('无高alpha主体')
    x0,y0,x1,y1=crop;limitw,limith=spec['native_target']
    ratio=min(limitw/(x1-x0),limith/(y1-y0))
    w=max(1,round((x1-x0)*ratio));h=max(1,round((y1-y0)*ratio))
    x=spec['anchor'][0]-w//2;y=spec['anchor'][1]-h
    result=Image.new('RGBA',tuple(spec['canvas']),EMPTY)
    for j in range(h):
        for i in range(w):
            group=[source.getpixel((min(x1-1,int(x0+(i+(u+.5)/5)*(x1-x0)/w)),
                                   min(y1-1,int(y0+(j+(v+.5)/5)*(y1-y0)/h))))
                   for v in range(5) for u in range(5)]
            solid=[p for p in group if p[3]>=240]
            if len(solid)>=13:
                rgb=tuple(sorted(p[c] for p in solid)[len(solid)//2] for c in range(3))
                result.putpixel((x+i,y+j),nearest(rgb))
    removed=keep_subject(result)
    return result,{'source_subject_crop':list(crop),'material_sampling_size':[w,h],
                   'native_origin':[x,y],'sampled_fragment_pixels_removed':removed,
                   'sampling_role':'未验收材质/轮廓起点，仍需以下原生修正'}

def native_cleanup(im):
    """只在原生网格整理：孤立中间色并入邻域主色，4邻域边界统一1px轮廓。"""
    old=im.copy();changed=0
    for y in range(1,im.height-1):
        for x in range(1,im.width-1):
            p=old.getpixel((x,y))
            if not p[3]:continue
            neighbors=[old.getpixel((x+dx,y+dy)) for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]]
            if p not in neighbors and all(q[3] for q in neighbors):
                c,n=Counter(neighbors).most_common(1)[0]
                if n>=3 and p not in (COLORS[0],COLORS[6],COLORS[7],COLORS[8]):
                    im.putpixel((x,y),c);changed+=1
    old=im.copy();outlined=0
    for y in range(im.height):
        for x in range(im.width):
            if not old.getpixel((x,y))[3]:continue
            if any(not(0<=x+dx<im.width and 0<=y+dy<im.height) or
                   not old.getpixel((x+dx,y+dy))[3] for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]):
                if im.getpixel((x,y))!=COLORS[0]:im.putpixel((x,y),COLORS[0]);outlined+=1
    return {'native_singleton_color_pixels_simplified':changed,'native_outline_pixels_corrected':outlined}

def patches(im,items):
    """按视觉标注重画真正原生像素，rect不包含右/下边界，无抗锯齿。"""
    draw=ImageDraw.Draw(im)
    for p in items:
        c=EMPTY if p['color']=='transparent' else COLORS[p['color']]
        if p['type']=='rect':
            x0,y0,x1,y1=p['bounds'];draw.rectangle([x0,y0,x1-1,y1-1],fill=c)
        elif p['type']=='line':draw.line([tuple(q) for q in p['points']],fill=c,width=p.get('width',1))
        elif p['type']=='polygon':draw.polygon([tuple(q) for q in p['points']],fill=c)
        elif p['type']=='pixel':im.putpixel(tuple(p['at']),c)
        else:raise ValueError('未知patch类型')

def selection(size,item):
    mask=Image.new('L',size,0);draw=ImageDraw.Draw(mask)
    for b in item.get('rects',[]):draw.rectangle([b[0],b[1],b[2]-1,b[3]-1],fill=255)
    for pts in item.get('polygons',[]):draw.polygon([tuple(p) for p in pts],fill=255)
    for p in item.get('pixels',[]):mask.putpixel(tuple(p),255)
    return mask

def layer_export(im,spec,annotation):
    """真实PNG组件与像素mask；互斥拆层，按z从底到上可精确重组最终PNG。"""
    folder=BASE/'layers'/spec['id'];folder.mkdir(parents=True,exist_ok=True)
    remainder=im.copy();outputs=[]
    # 后指定的前景优先切取，避免交叠语义mask造成重复实体。
    for item in reversed(annotation.get('components',[])):
        region=selection(im.size,item);piece=Image.new('RGBA',im.size,EMPTY);binary=Image.new('L',im.size,0)
        for y in range(im.height):
            for x in range(im.width):
                if region.getpixel((x,y)) and remainder.getpixel((x,y))[3]:
                    piece.putpixel((x,y),remainder.getpixel((x,y)));binary.putpixel((x,y),255)
                    # 风机可动叶片下补中性腔底：未来移开叶片不会出现机壳缺洞。
                    # 当前合成仍由不透明叶片遮住下补色，逐像素验证完全相同。
                    remainder.putpixel((x,y),COLORS[item['underpaint']] if 'underpaint' in item else EMPTY)
        if not piece.getbbox():raise ValueError(f'组件为空: {item["name"]}')
        path=folder/(item['name']+'.png');mask_path=folder/(item['name']+'_selection.png')
        piece.save(path);binary.save(mask_path)
        outputs.append({'name':item['name'],'file':rel(path),'selection_mask':rel(mask_path),
                        'sha256':sha(path),'z_index':item['z_index'],'canvas':list(im.size),
                        'anchor':spec['anchor'],'purpose':item['purpose'],'editable_source':True,
                        'hidden_underpaint_color_index':item.get('underpaint')})
    path=folder/'foundation_body.png';remainder.save(path)
    outputs.append({'name':'foundation_body','file':rel(path),'sha256':sha(path),'z_index':0,
                    'canvas':list(im.size),'anchor':spec['anchor'],'purpose':'地基与主体余下像素','editable_source':True})
    outputs.sort(key=lambda l:l['z_index'])
    merged=Image.new('RGBA',im.size,EMPTY)
    for item in outputs:merged.alpha_composite(Image.open(ROOT/item['file']).convert('RGBA'))
    if merged.tobytes()!=im.tobytes():raise ValueError('源组件重组不等于成品')
    save_json(folder/'layers.json',{'canvas':list(im.size),'anchor':spec['anchor'],
          'rect_coordinate_convention':'left/top included; right/bottom excluded','layers':outputs,
          'exact_recomposition':True,'type':'editable_same_canvas_RGBA_components_with_explicit_selection_masks'})
    return outputs

def measurement(im,spec):
    bbox=im.getbbox()
    if not bbox:raise ValueError('空对象')
    w,h=im.size;margin=8 if (w,h)==(64,64) else 16
    pixels=list(im.get_flattened_data());used={p for p in pixels if p[3]}
    rules={'size':list(im.size)==spec['canvas'],'binary_alpha':{p[3] for p in pixels}<={0,255},
       'fixed_palette':used<={COLORS[i] for i in STATIC},
       'min_margins':bbox[0]>=margin and bbox[1]>=margin and bbox[2]<=w-margin and bbox[3]<=h-margin,
       'ground_or_install_boundary':bbox[3]==spec['anchor'][1]}
    if not all(rules.values()):raise ValueError(f'{spec["id"]}不满足规则:{rules},bbox={bbox}')
    return {'canvas':list(im.size),'bbox':list(bbox),'anchor':spec['anchor'],
            'anchor_convention':'pixel boundary coordinate; source components share canvas and anchor',
            'rgb_count':len(used),'alpha_values':sorted({p[3] for p in pixels}),'rules':rules}

def review_one(im,ident):
    for scale in (1,2):
        view=Image.new('RGBA',im.size,'#4D6470');view.alpha_composite(im)
        view.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST).save(BASE/'pixel-review'/f'{ident}_{scale}x.png')

def finish(spec,draft=False):
    source=BASE/'generated'/f'{spec["id"]}_master_v001.png'
    if not source.is_file():raise FileNotFoundError(f'真实母稿未到位，不生成假占位: {source}')
    annotation_path=BASE/'annotations'/f'{spec["id"]}.json'
    annotation=load(annotation_path) if annotation_path.exists() else {}
    im,process=sample_material(Image.open(source).convert('RGBA'),spec,annotation)
    process.update(native_cleanup(im))
    if draft:
        folder=BASE/'pixel-review'/'drafts';folder.mkdir(exist_ok=True)
        im.save(folder/f'{spec["id"]}_draft.png');review_one(im,spec['id']+'_DRAFT')
        print(json.dumps({'draft':spec['id'],'bbox':im.getbbox(),'process':process},ensure_ascii=False));return
    if not annotation.get('observations') or not annotation.get('adjustments') or not annotation.get('patches'):
        raise ValueError('原生定稿缺少实际视觉观察/具体修正标注，不能以草案冒充')
    # 共门框/九宫格原生重构在标注中显式登记，由单独部件工程执行后加载。
    if annotation.get('native_reconstruction_file'):
        im=Image.open(BASE/annotation['native_reconstruction_file']).convert('RGBA')
        process['native_reconstruction_file']=annotation['native_reconstruction_file']
        process['native_reconstruction_sha256']=sha(BASE/annotation['native_reconstruction_file'])
        record=BASE/annotation['native_reconstruction_record']
        process['native_reconstruction_record']=rel(record)
        process['native_reconstruction_record_sha256']=sha(record)
        process['source_pixel_use']='sampled draft material/design parts plus explicit structural native redraw; no final whole image resize'
    patches(im,annotation['patches'])
    metrics=measurement(im,spec)
    path=BASE/'finished'/f'{spec["id"]}_v001.png';im.save(path)
    layers=layer_export(im,spec,annotation);review_one(im,spec['id'])
    generation=next(a for a in load(BASE/'generation-record.json')['assets'] if a['id']==spec['id'])
    if generation['sha256']!=sha(source):raise ValueError('实际工具归档母稿与当前源图哈希不一致')
    source_use={'method':'AI_MATERIAL_DESIGN_REFERENCE_AND_NATIVE_PIXEL_FINISH',
        'master':rel(source),'master_sha256':sha(source),'prompt':generation['prompt'],
        'prompt_sha256':generation['prompt_sha256'],'reference_images':generation['references'],
        'generation_record':rel(BASE/'generation-record.json'),'tool_output':generation['tool_output'],
        'generation_record_sha256':sha(BASE/'generation-record.json'),
        'generation_date_utc':generation['archived_at_utc'][:10],
        'sampled':process,'native_adjustments':annotation['adjustments'],
        'generation_tool':'built-in image_gen.imagegen','full_image_resize_is_final':False}
    entry={'id':spec['id'],'manifest_id':spec['manifest_id'],'file':rel(path),
      'production_file':spec['production_file'],'sha256':sha(path),'size':spec['canvas'],
      'finishing_record':rel(path.with_suffix('.finish.json')),
      **metrics,'runtime_windows':annotation.get('runtime_windows',[]),
      'emitter_points':annotation.get('emitter_points',[]),'layers':layers,
      'tiling':annotation.get('tiling',{'axes':[],'repeat':False}),
      'interaction_center':annotation.get('interaction_center'),'source_use':source_use,
      'calibration_features':annotation.get('calibration_features'),
      'non_runtime_glass':annotation.get('non_runtime_glass',[]),
      'observations':annotation['observations'],'emission_baked':False,'review_status':'PENDING_ROOT_ART_REVIEW'}
    save_json(path.with_suffix('.finish.json'),entry)
    print(json.dumps({'finished':spec['id'],'bbox':metrics['bbox'],'rgb_count':metrics['rgb_count']},ensure_ascii=False))

def catalog_and_contact(specs):
    entries=[]
    for spec in specs:
        file=BASE/'finished'/f'{spec["id"]}_v001.finish.json'
        if file.exists():entries.append(load(file))
    save_json(BASE/'native-catalog-v001.json',{'assets':entries,'required_assets':18,
        'actual_finished_assets':len(entries),'production_review':'PENDING_ROOT_ART_REVIEW'})
    ledger=[]
    for entry in entries:
        annotation=BASE/'annotations'/f'{entry["id"]}.json'
        ledger.append({'id':entry['id'],'manifest_id':entry['manifest_id'],
          'file':entry['file'],'sha256':entry['sha256'],
          'finishing_record':entry['finishing_record'],'finishing_record_sha256':sha(ROOT/entry['finishing_record']),
          'annotation':rel(annotation),'annotation_sha256':sha(annotation),
          'source_use':entry['source_use'],'review_status':'PENDING_ROOT_ART_REVIEW'})
    save_json(BASE/'native-source-ledger-v001.json',{'assets':ledger,
        'generation_record':rel(BASE/'generation-record.json'),
        'generation_record_sha256':sha(BASE/'generation-record.json'),
        'script_versions':{rel(p):sha(p) for p in (BASE/'tools').glob('*.py')},
        'actual_builtin_imagegen_outputs':load(BASE/'generation-record.json')['successful_outputs'],
        'permission_basis':'用户继续已明确提出的原生脚本整理方案；根分派本轮18对象',
        'user_final_style_approval_claimed':False})
    # 同一像素尺度排布，空白只是审阅留白；不存在的资产不显示成假图。
    board=Image.new('RGBA',(800,1440),'#4D6470');draw=ImageDraw.Draw(board)
    for index,entry in enumerate(entries):
        x=(index%4)*200;y=(index//4)*288
        im=Image.open(ROOT/entry['file']).convert('RGBA')
        board.alpha_composite(im,(x+(200-im.width)//2,y))
        draw.text((x+4,y+264),entry['id'],fill='#ECE9D8')
    for scale in (1,2):board.resize((800*scale,1440*scale),Image.Resampling.NEAREST).save(BASE/'pixel-review'/f'objects_contact_{scale}x.png')

def main():
    cli=argparse.ArgumentParser();cli.add_argument('--id');cli.add_argument('--draft',action='store_true');cli.add_argument('--catalog',action='store_true')
    args=cli.parse_args();specs=load(BASE/'planned-catalog-v001.json')['assets']
    if args.catalog:catalog_and_contact(specs);return
    if not args.id:raise ValueError('需要显式资产ID；不对缺失母稿默认通过')
    spec=next(s for s in specs if s['id']==args.id);finish(spec,args.draft)
if __name__=='__main__':main()
