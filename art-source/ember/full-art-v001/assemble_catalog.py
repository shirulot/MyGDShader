"""合并三个批次的40候选；--promote仅复制已绑定哈希且通过审查的图像。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
LABELS = dict(zip(
    ['console_base','pump_base','ventilator_base','cooler_base','relay_base','wall_lamp','floor_lamp',
     'door_closed','door_open','telepad_base','terminal_body','screen_frame','fuse','antenna_coil',
     'split_ring','log_cartridge','toolbox','helmet','hp','energy','time','interact','log','pause',
     'lighting','drainage','water_supply','ventilation','cooling','communication','teleport','protection',
     'panel_9slice','water_calm','water_directional','foam_strip','smoke_blob','grass_leaf','metal_albedo','concrete_albedo'],
    ['控制台','排水泵','排热风机','冷却装置','中继核心','壁灯','地灯','关闭门','开启门','传送底座',
     '维修终端','屏幕边框','保险丝','天线线圈','开口环','记录匣','工具箱','维修头盔','生命','能量','时间',
     '交互','记录','暂停','照明','排水','输水','排热','冷却','通信','传送','保护','九宫格面板',
     '平静水纹','定向水纹','泡沫条','烟团','草片','金属底色','混凝土底色']))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def resolve(value):
    path=(ROOT/value.removeprefix('res://')).resolve()
    if not path.is_relative_to(ROOT): raise ValueError('路径越出项目')
    return path

def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for group in ['objects','ui','textures']: parser.add_argument('--'+group,required=True,type=Path)
    parser.add_argument('--promote',action='store_true')
    args=parser.parse_args()
    assets=[]
    source_catalogs=[]
    for group,expected in [('objects',18),('ui',15),('textures',7)]:
        path=getattr(args,group).resolve()
        catalog=json.loads(path.read_text(encoding='utf-8'))
        entries=catalog.get('assets',[])
        if len(entries)!=expected: raise ValueError(group+'候选数量不完整')
        source_catalogs.append({'group':group,'file':path.relative_to(ROOT).as_posix(),'sha256':digest(path)})
        for original in entries:
            item=dict(original)
            source=resolve(item['file'])
            if not source.is_file() or digest(source)!=item['sha256']: raise ValueError('候选版本不符：'+item['id'])
            target=resolve(item['production_file'])
            if not target.is_relative_to(ROOT/'assets/ember') or target.suffix!='.png':
                raise ValueError('正式目标需在assets/ember中的新PNG')
            item['file']='res://'+source.relative_to(ROOT).as_posix()
            item['canvas']=item.get('canvas',item.get('size'))
            # 把对象源层的九宫格信息投射到生产目录统一字段，便于直接建立StyleBoxTexture。
            if item['id']=='screen_frame':
                slicing=item.get('tiling',{})
                item['slice_region']=slicing['slice_region']
                margins=slicing['slice_margins']
                item['slice_margins']=[margins[side] for side in ['left','top','right','bottom']]
                item['draw_center']=slicing['draw_center']
            item['label']=LABELS[item['id']]
            item['group']=group
            assets.append(item)
    if len({a['id'] for a in assets})!=40 or {a['id'] for a in assets}!=set(LABELS):
        raise ValueError('40项ID缺失或重复')
    result={'schema_version':1,'date':'2026-10-04','status':'NATIVE_40_CANDIDATES_VISUAL_REQUIRED',
            'new_art_units':40,'completed_art_units_after_acceptance':123,
            'source_catalogs':source_catalogs,'assets':assets}
    save(BASE/'candidate-catalog-v001.json',result)
    if args.promote:
        review=json.loads((BASE/'art-review-v001.json').read_text(encoding='utf-8'))
        numeric=json.loads((BASE/'validation-candidates-v001.json').read_text(encoding='utf-8'))
        provenance=json.loads((BASE/'validation-provenance-v001.json').read_text(encoding='utf-8'))
        hashes={item['id']:item['sha256'] for item in assets}
        if (review.get('status')!='FULL_40_ART_REVIEW_PASS' or review.get('asset_sha256')!=hashes
                or numeric.get('status')!='NATIVE_40_NUMERIC_PASS'
                or {i['id']:i['sha256'] for i in numeric['assets']}!=hashes):
            raise ValueError('缺少绑定当前40图的视觉与自动通过记录')
        dependencies=provenance.get('dependency_sha256',{})
        if provenance.get('status')!='FULL_40_PROVENANCE_PASS' or not dependencies:
            raise ValueError('缺少来源通过记录及冻结依赖')
        for name,expected_sha in dependencies.items():
            path=resolve(name)
            if not path.is_file() or digest(path)!=expected_sha:
                raise ValueError('来源审查后依赖已变：'+name)
        # 在写任何PNG前检查全部目标，防止半套复制后才发现版本冲突。
        for item in assets:
            target=resolve(item['production_file'])
            if target.exists() and digest(target)!=item['sha256']:
                raise ValueError('正式同版本PNG已有不同内容：'+item['id'])
        for item in assets:
            source=resolve(item['file'])
            target=resolve(item['production_file'])
            target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists(): shutil.copyfile(source,target)
            item['file']='res://'+target.relative_to(ROOT).as_posix()
            item['status']='NATIVE_ART_REVIEW_PASS'
        result['status']='NATIVE_40_ART_REVIEWED'
        result['art_review']='art-source/ember/full-art-v001/art-review-v001.json'
        save(ROOT/'assets/ember/ember_additional_catalog_v001.json',result)
    print(json.dumps({'candidate_count':40,'promoted':args.promote}))

if __name__=='__main__': main()
