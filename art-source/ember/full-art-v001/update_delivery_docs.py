"""原生、来源、视觉、Godot和R01全部通过后，才同步123艺术单元的当前文档。"""
import csv
import hashlib
import io
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
DOCS = ROOT/'docs/shader-learning'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def main():
    for name,status in [
        ('validation-candidates-v001.json','NATIVE_40_NUMERIC_PASS'),
        ('validation-provenance-v001.json','FULL_40_PROVENANCE_PASS'),
        ('art-review-v001.json','FULL_40_ART_REVIEW_PASS'),
        ('godot-delivery-summary-v001.json','GODOT_FULL_ART_AND_FRESH_REUSE_PASS')]:
        if read(BASE/name).get('status')!=status:
            raise SystemExit('未通过验收：'+name)
    if read(ROOT/'art-source/ember/references/full_native_scale_v003.json').get('status')!='R01_COMPLETE_NATIVE_SCALE_REVIEW_PASS':
        raise SystemExit('R01统一比例未完成视觉验收')
    catalog = read(ROOT/'assets/ember/ember_additional_catalog_v001.json')
    numeric = read(BASE/'validation-candidates-v001.json')
    godot = read(BASE/'godot-delivery-summary-v001.json')
    # 当前说明替换顶部结论；保留已经冻结的旧批次记录和旧交付ZIP。
    readme = ROOT/'assets/ember/README.md'
    text = readme.read_text(encoding='utf-8')
    old = '当前已正式交付 **83/123 个艺术单元，剩余 40 未完成**：三套瓦片集共 62 单元、机器人四向 20 帧与采能站 1。共 **25 张生产 PNG**（3 张瓦片 atlas＋20 张角色单帧＋1 张角色 atlas＋1 张采能站）；图集打包、重复刷块与审阅图不增加艺术计数。TileMapLayer 和机器人 SpriteFrames 已通过 Godot 4.7.2 实际导入、保存重载与渲染验证。'
    new = '当前已正式交付 **123/123 个艺术单元，剩余艺术项 0**：瓦片 62、机器人 20 帧、建筑道具 19、UI 15、2D 特效纹理 4、3D 底色／草片 3。共 **65 张生产 PNG、11 份可复用 .tres、3 个独立示例场景**。图集、组件源层和审阅图不增加艺术计数。全部新资源已通过 Godot 4.7.2 导入、保存重载、实际渲染以及无原缓存新工程复用验证。'
    if old in text: text = text.replace(old,new,1)
    elif new not in text: raise ValueError('README顶部未匹配')
    text = text.replace('R01 只完成机器人／站点／地板的部分原生比例验证，未含门与控制台。',
                        'R01 已包含机器人、站点、开关门、控制台和四地板的统一 2×[比例验收板](../../art-source/ember/references/full_native_scale_v003.png)。')
    old = '当前合并包：[ember_assets_v002_2026-10-04.zip](../../art-source/ember/deliveries/ember_assets_v002_2026-10-04.zip)，含 83 个已完成艺术单元和来源／验证记录；剩余 40 项仍在清单中登记为计划。'
    new = '''打开[新素材库场景](../../scenes/ember/asset_library_sandbox.tscn)查看建筑道具、UI 九宫格、特效纹理和 3D 材质。门的两态 SpriteFrames、面板／屏幕 StyleBoxTexture，以及三种 StandardMaterial3D 可直接复用；每项尺寸、锚点、灯窗、发射点和可拆源层见[40项目录](ember_additional_catalog_v001.json)及[完整艺术交付说明](../../docs/shader-learning/asset-production-full-art.md)。

当前合并包：[ember_assets_v003_2026-10-04.zip](../../art-source/ember/deliveries/ember_assets_v003_2026-10-04.zip)，含 123 个已完成艺术单元和来源／验证记录。v001/v002 历史包保持原样。

艺术素材已完成；D01～D13 技术输入、可选 collect 动画、实际关卡布局及课程 Shader 仍按清单另行实施。素材库中的材质常量和灯窗坐标不代表技术 Mask、Normal 或整套课程效果已完成。'''
    if old in text: text = text.replace(old,new,1)
    elif new not in text: raise ValueError('README交付链接未匹配')
    readme.write_text(text,encoding='utf-8')
    for name in ['tilemap-reusable-tilesets.md','asset-production-batch-01.md']:
        path = DOCS/name
        text = path.read_text(encoding='utf-8')
        text = text.replace('83/123，剩余 40 未完成','123/123，剩余艺术项 0').replace('83/123，剩余 40','123/123，剩余艺术项 0')
        if '[完整艺术交付说明](asset-production-full-art.md)' not in text:
            text = text.replace('\n\n','\n\n最新全套进度与新素材复用方法见[完整艺术交付说明](asset-production-full-art.md)。下文保留本批次范围。\n\n',1)
        path.write_text(text,encoding='utf-8')
    path = DOCS/'asset-production-batch-02-robot.md'
    text = path.read_text(encoding='utf-8')
    marker = '全套最新艺术进度 **123/123**，见[完整艺术交付说明](asset-production-full-art.md)。本文保存机器人批次交付时的 83/123 快照，角色 PNG 和本批来源记录保持原样。'
    if marker not in text: text=text.replace('\n\n','\n\n'+marker+'\n\n',1)
    path.write_text(text,encoding='utf-8')
    path = DOCS/'art-generation-standard.md'
    text = path.read_text(encoding='utf-8')
    text = text.replace('本文是新生产标准及预算；图片尚未生成。','本文是新生产标准及预算。2026-10-04 的 123/123 艺术项已完成，见[完整艺术交付说明](asset-production-full-art.md)；技术输入和实际场景迁移另行实施。')
    path.write_text(text,encoding='utf-8')
    path = DOCS/'resources.md'
    text = path.read_text(encoding='utf-8').replace('下方 64/123 是瓦片批次完成时的历史快照。','上方 64/123 是瓦片批次完成时的历史快照。')
    addition = '''2026-10-04 完整艺术批次：新增建筑道具 18、UI 15、特效／3D 纹理 7，合计全套 **123/123 艺术项完成**；此前 6、64 和 83 的数量是分批历史快照。40 份实际 imagegen 母稿逐项保留提示词、原始输出路径和 SHA256，并经原生整理、交叉视审与 Godot 新工程复用检查。来源使用方式包含材料／结构参考和明确登记的原生重建，不登记为 CC0。目录与来源证明见[完整艺术交付说明](asset-production-full-art.md)。D01～D13 技术输入、可选动作与课程 Shader 仍按实验需要准备。

'''
    if addition not in text: text=text.replace('## 资源原则',addition+'## 资源原则',1)
    path.write_text(text,encoding='utf-8')
    rows = list(csv.DictReader(io.StringIO((DOCS/'asset-generation-manifest.csv').read_text(encoding='utf-8'))))
    completed = {asset['manifest_id'] for asset in catalog['assets']}
    for row in rows:
        if row['id'] in completed: row['status']='NATIVE_PNG_RESOURCES_GODOT_VERIFIED'
        if row['id']=='R01':
            row['status']='COMPLETE_NATIVE_SCALE_REVIEW'
            row['proposed_path']='art-source/ember/references/full_native_scale_v003.png'
    output=io.StringIO(newline='')
    writer=csv.DictWriter(output,fieldnames=list(rows[0]),lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    (DOCS/'asset-generation-manifest.csv').write_text(output.getvalue(),encoding='utf-8')
    for folder,count in [('batch-03-objects',18),('batch-04-ui',15),('batch-05-textures',7)]:
        path=ROOT/'art-source/ember'/folder/'generation-record.json'
        # 生成台账已被整理记录绑定SHA，保持历史原样；接受结果另存，避免破坏来源链。
        record={'status':'NATIVE_ART_AND_GODOT_VERIFIED','formal_approved_production_units':count,
                'generation_record':path.relative_to(ROOT).as_posix(),
                'generation_record_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'acceptance':'art-source/ember/full-art-v001/art-review-v001.json',
                'godot_acceptance':'art-source/ember/full-art-v001/godot-delivery-summary-v001.json'}
        path.with_name('acceptance-record-v001.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    detail = '''# 《余烬采能站》完整艺术素材交付

日期：2026-10-04。**123/123 艺术单元已完成，剩余艺术项 0**。其中 120 项 2D、3 项 3D；按逻辑单元计数，组件层、图集打包、参考图和重复刷块不增加数量。共有 65 张正式 PNG、11 份 .tres 和 3 个独立示例场景。

| 范围 | 艺术单元 | 正式文件 |
| --- | ---: | --- |
| 三套通用瓦片 | 62 | 3 atlas、4 TileSet；[TileMapLayer 布局方法](tilemap-reusable-tilesets.md) |
| 四向机器人 | 20 | 20 单帧、1 atlas、1 SpriteFrames；[动画报告](asset-production-batch-02-robot.md) |
| 采能站与建筑道具 | 19 | 19 PNG；门两态 SpriteFrames、屏幕 StyleBoxTexture |
| HUD／任务／九宫格 UI | 15 | 14 图标、1 面板；面板 StyleBoxTexture |
| 水纹／泡沫／烟团 | 4 | 4 PNG |
| 草片／金属／混凝土 | 3 | 3 PNG、3 StandardMaterial3D |

## 直接复用

打开[瓦片布局场景](../../scenes/ember/tileset_layout_sandbox.tscn)，选择 `LayoutWorkspace` 中的 TileMapLayer 手工布置，或把[合并 TileSet](../../assets/ember/environment/tilesets/ember_common_tileset_v001.tres)指定给自己的 TileMapLayer。当前为手工刷块；接口、覆盖层和方向约束见瓦片文档。

打开[机器人场景](../../scenes/ember/robot_animation_sandbox.tscn)查看四向动画；将 [SpriteFrames](../../assets/ember/characters/robot/robot_sprite_frames_v001.tres)指定给 AnimatedSprite2D，设置 `centered=false`、`offset=(-32,-80)`、Nearest。walk 使用 8 FPS。

打开[新素材库场景](../../scenes/ember/asset_library_sandbox.tscn)，四个页签分别展示建筑道具、UI／九宫格、特效纹理、3D 材质。此场景独立调整自己的预览窗口，不改项目主场景。PNG 不包含文字、运行灯色、烟火或课程 Shader 效果。

在自己的 Sprite2D 使用对象时，建议 `centered=false`、`offset=-anchor`，并启用 Nearest。锚点是像素边界坐标。所有新对象的画布、主体 bbox、灯窗区域、发射点、来源和可拆层见[40项生产目录](../../assets/ember/ember_additional_catalog_v001.json)。源层仍在 `art-source/ember/batch-03-objects/layers/`，与对应 PNG 共用完整画布／锚点；可动叶片、门前景和中继顶部的组合已核对。`art-source` 由 `.gdignore` 排除导入；需要运行时拆层时，将所需组件复制到自己的 `assets` 子目录，逐层绑定 Sprite2D，并使用同一 `offset=-anchor` 和目录中的 z_index。

| 可直接指定的资源 | 用法 |
| --- | --- |
| [door_states_v001.tres](../../assets/ember/buildings/door/door_states_v001.tres) | AnimatedSprite2D 的 `closed`／`open`；96×128、锚点48/112、共用精确门框 |
| [panel_style_v001.tres](../../assets/ember/ui/panels/panel_style_v001.tres) | Panel 的 `panel` StyleBox；四边8px；已实际渲染192×96、400×180、600×300 |
| [screen_style_v001.tres](../../assets/ember/buildings/terminal/screen_style_v001.tres) | 屏幕边框；原图region `(16,16,64,64)`、四边8px、中心透明；已拉伸640×96 |
| [grass_leaf_v001.tres](../../assets/ember/three_d/materials/grass_leaf_v001.tres) | QuadMesh 材质；Alpha Scissor 0.5、双面；根部32/120 |
| [metal_v001.tres](../../assets/ember/three_d/materials/metal_v001.tres) | 金属底色材质，metallic 0.55、roughness 0.65 为复用起点 |
| [concrete_v001.tres](../../assets/ember/three_d/materials/concrete_v001.tres) | 混凝土底色材质，metallic 0、roughness 1 |

九宫格原理与属性对应 Godot 的 [StyleBoxTexture](https://docs.godotengine.org/en/stable/classes/class_styleboxtexture.html)；材质属性对应 [BaseMaterial3D](https://docs.godotengine.org/en/stable/classes/class_basematerial3d.html)。3D 纹理使用 Lossless、实际 Mipmaps、Nearest with Mipmaps；近／远距离渲染分别保留在验证目录。2D PNG 使用 Lossless、无 Mipmaps、Nearest。水纹与两种材质 XY 重复，泡沫只 X 重复；烟团／草片不重复。请在使用节点或材质上按这个轴向配置重复采样。

## 新增40项逐项信息

以下 sha256 与[数值报告](../../art-source/ember/full-art-v001/validation-candidates-v001.json)、[美术审查](../../art-source/ember/full-art-v001/art-review-v001.json)绑定；完整值与源层路径见生产目录。

| ID | 名称 | 画布 | anchor | 正式PNG |
| --- | --- | --- | --- | --- |
'''
    for asset in catalog['assets']:
        canvas='×'.join(map(str,asset['canvas']))
        anchor='/'.join(map(str,asset.get('anchor',[])))
        file=asset['file'].removeprefix('res://')
        detail+=f"| `{asset['id']}` | {asset['label']} | {canvas} | {anchor} | [{Path(file).name}](../../{file}) |\n"
    detail+=f'''
## 验收与来源

本轮新增40项各有独立的实际 imagegen 母稿。母稿包含较大画布、抗锯齿和过量细节，实际生产图经过原生网格重构、固定16色整理、二值Alpha和结构校正。设备、图标或平铺模式的原生重建均在来源语义中明确登记。母稿和透明修正图不直接当作原生验收资产，不登记为 CC0。

各批生成台账和候选目录保留当时状态与字节，接受结果另存该批 `acceptance-record-v001.json`；最终状态以本次40项生产目录和验收报告为准。提示词、标注、原生源层、脚本和依赖均被来源报告绑定SHA；验收后改动会阻止推广和封包。

- [建筑道具生成记录](../../art-source/ember/batch-03-objects/generation-record.json)、[UI生成记录](../../art-source/ember/batch-04-ui/generation-record.json)、[纹理生成记录](../../art-source/ember/batch-05-textures/generation-record.json)：实际输出路径、归档母稿、完整提示词及参考依赖。
- [独立来源复核](../../art-source/ember/full-art-v001/validation-provenance-v001.json)：40份母稿逐份对照原始工具输出，提示词与源层组合核对。
- [原生数值检查](../../art-source/ember/full-art-v001/validation-candidates-v001.json)：{numeric['automatic_checks']}条检查通过；尺寸、固定16色、二值Alpha、留白、锚点、平铺边界与当前输出SHA一致。数值通过不代替视觉检查。
- [美术检查](../../art-source/ember/full-art-v001/art-review-v001.json)：实际原生／2倍、设备与图标语义、门框和透明门洞、九宫格多尺寸、五种3×3平铺及代理交叉意见。
- [对象／UI独立交叉审查](../../art-source/ember/full-art-v001/independent-objects-ui-review-v001.json)：覆盖18对象与15UI；纹理制作方未将自己的7纹理列为独立审查，纹理由根另行实际查看。
- [Godot与新工程摘要](../../art-source/ember/full-art-v001/godot-delivery-summary-v001.json)：{len(godot['stages'])}个实际执行阶段，退出码0、stderr为空。全套复制到无原缓存、无旧游戏autoload的新工程，资源保存重载、62瓦片、20机器人帧、40新PNG和实际渲染通过。
- [R01统一比例板](../../art-source/ember/references/full_native_scale_v003.png)：机器人、站点、开关门、控制台和四地板统一2倍，没有按对象分别缩放。

![新增素材库](../../art-source/ember/full-art-v001/render/library_page_00.png)

![统一原生比例](../../art-source/ember/references/full_native_scale_v003.png)

## 验证和再生成

在项目根目录 PowerShell 运行，Godot 路径按本机安装修改：

```powershell
$godotExe = 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe'
& $godotExe --headless --editor --path . --import
& $godotExe --headless --path . --script res://tools/build_ember_asset_library.gd -- --verify-only
& $godotExe --headless --path . --script res://tools/build_ember_tilesets.gd -- --verify-only
& $godotExe --headless --path . --script res://tools/build_ember_robot_animation.gd -- --verify-only
```

`--verify-only` 只检查已存在的资源与场景。新素材库构建器默认保留已有示例；只有明确传 `--rebuild-sandbox` 才重建示例场景。重新整理原生源时，先产生新版本候选、数值与视觉验收记录，避免覆盖既有版本。纹理源、工具、验证器和全部生成提示词随包保留。

## 交付包与范围

[ember_assets_v003_2026-10-04.zip](../../art-source/ember/deliveries/ember_assets_v003_2026-10-04.zip)含65正式PNG、11资源、3示例、完整母稿／原生源层／脚本／验证记录。包内 `DELIVERY-MANIFEST.json` 对每个载荷文件给出 SHA256；包外 `.package.json` 和 `.audit.json` 记录ZIP校验，不做自引用。此前 v001/v002 包保留原样。

艺术素材完成不等于整个游戏／课程完成。D01～D12的40个技术输入预算、D13布局相关0～30个Mask、可选collect8帧、实际关卡、课程Shader、3D模型／UV及音频没有在本次艺术交付中登记完成。材质常量不代替D11法线等派生图；对象灯窗与发射点不代替D08通道Mask。现有主游戏和学习者Shader仍按各自进度使用原资源，迁移另行实施。
'''
    (DOCS/'asset-production-full-art.md').write_text(detail,encoding='utf-8')
    print('当前文档已登记123/123艺术单元；技术输入与课程状态保持独立')

if __name__=='__main__':
    main()
