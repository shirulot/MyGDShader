# 地板像素生产 v001 源记录

2026-10-06。用户认可[场景效果图](../previews/scene_preview_v001.png)，要求据此生产可铺刷、可自动补全、实际衔接的地板素材。

- [要素分析](scene-factor-analysis.md)：逐项区分钢板、平台边、格栅、板缝、桥和装饰的职责。
- [首版材质母稿](floor_material_master_v001.png)与[完整提示词](floor_material_master_v001.prompt.txt)：首轮风格参考，未直接进入像素包。
- [修正材质母稿](floor_material_master_v002.png)与[完整提示词](floor_material_master_v002.prompt.txt)：用户指出当前材质不贴近认可场景后，用内置 `image_gen` 再次以认可图为图像参考生成。保留细颗粒钢板语汇，移除宽色块、竖条和大斑。母稿本身不是生产 atlas，正式整理与色阶记载在像素报告。
- 正式图集入口：[可自动铺刷地板包](../../../../assets/ember/environment/pixel_floor_v001/README.md)。
- 原生图集构建：[build_pixel_floor_art_v001.gd](../../../../tools/build_pixel_floor_art_v001.gd)；独立装饰构建：[build_pixel_floor_details_v001.gd](../../../../tools/build_pixel_floor_details_v001.gd)；TileSet／引擎验收构建：[build_pixel_floor_v001.gd](../../../../tools/build_pixel_floor_v001.gd)。
- 平台外立面：[build_pixel_floor_facade_v001.gd](../../../../tools/build_pixel_floor_facade_v001.gd)，独立派生层提供南向16px投影，不改变基础地板和桥的几何。

原生构建脚本现在**默认使用 v002 修正材质**。直接运行 `godot --headless --path . -s res://tools/build_pixel_floor_art_v001.gd` 会产生当前材质；只有显式附加 `-- --material=v001` 才重建历史视觉基线。附加 `-- --sample-only` 可仅导出材质小样。资源目录与文件名的 `v001` 表示结构版本，当前材质版本由 `catalog.material_revision=v002` 登记。

[实际材质整理记录](material_processing_v002.json)列出源图 SHA256、四个实际采样原点、192×192 采样范围、6px 步长、18px 局部低频扣除和5阶原生配色。正式暂用0号[32px原生材质](floor_albedo_native_v002.png)，其4px共享连续带保留细颗粒；[其他候选](floor_albedo_candidates_native_v002.png)仅供审阅，未作为 Terrain 随机变体注册。

平台厚度由[独立南立面构建脚本](../../../../tools/build_pixel_floor_facade_v001.gd)生成正式 atlas，参考[真实图块小样](facade_sample_4x_v001.png)。`facade` 有47块，`facade_landing` 有89块，复用原地板／落桥图块坐标；加上原351块，9套核心图集共487块。立面图块仍为32×32，上16px透明、下16px绘制；派生层偏移 `(0,16)`，可见范围相对地板格原点为 `x=[0,32)、y=[32,48)`。只有南面，没有东面或桥投影；南侧已有地板时全透明，南桥口 `[4,28)` 在整个16px高度透明。像素证据为正式包中的 `facade_validation.json`，原351块的 SHA256 保持不变。

全套重新构建时，先运行地板原生脚本，再运行南立面脚本，最后运行 TileSet／引擎验收脚本。南立面会把自身两套派生图集追加到 `catalog.json`，不修改地板占用、核心素材或原生 Terrain 随机候选。

来源登记为 `AI_MATERIAL_STYLE_REFERENCE_WITH_GODOT_NATIVE_PIXEL_CONSTRUCTION`。几何由新脚本可复现地构建；后续修正材质采用母稿实际像素取样、低频校正与原生量化。不能称为从效果图直接裁切或从母稿无损提取。没有从第三方资源库取材，不登记为 CC0。

`structural-baseline-v001/` 保留视觉被用户指出偏离时的结构基线图片、资源、报告和原生构建脚本。其结构检查通过不代表视觉认可，后续修正不覆盖这个快照。

原始材质工具输出保留于 `C:/Users/shiru/.codex/generated_images/01a10cd5-c2d4-7a01-8740-0c3b355f7465/exec-2963cfe7-b214-4558-aefb-6d5739248a52.png`；本目录副本未缩放或改像素。实际功能和失败项以正式包中的报告为准。概念图认可、结构验收和最终成品的用户视觉认可分别记录。
