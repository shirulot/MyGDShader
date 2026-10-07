# 《余烬采能站》技术输入交付

日期：2026-10-04。D01～D12 的 **40/40 个技术输入已完成**，本批实际交付 40 PNG、3 CanvasTexture、2 StandardMaterial3D 和 1 独立检查场景。与已有美术合计 105 生产 PNG、16 份 `.tres`、4 个示例；艺术数量仍为 123/123。

打开[技术输入场景](../../scenes/ember/technical_inputs_sandbox.tscn)查看校准／程序输入、设备通道、2D 检修灯和 3D 材质。移动鼠标观察 2D 法线；现有游戏主场景及学习者 Shader 保留。完整逐项参数、来源、SHA 和重复轴见[技术目录](../../assets/ember/data/technical_inputs_catalog_v001.json)。

| 范围 | 数量 | 正式目录 |
| --- | ---: | --- |
| D01 校准图 | 5 | `assets/ember/data/calibration/` |
| D02 灰阶／颜色 Ramp | 2 | `assets/ember/data/ramps/` |
| D03 圆／星 Mask | 2 | `assets/ember/data/masks/` |
| D04 低／高频 Noise | 2 | `assets/ember/data/noise/` |
| D05 Alpha 细边／孔洞测试 | 1 | `assets/ember/data/calibration/` |
| D06 径向／能量条纹 | 2 | `assets/ember/data/energy/` |
| D07 已知高度／匹配法线 | 2 | `assets/ember/data/calibration/` |
| D08 十设备区域 Mask | 10 | `assets/ember/data/object_masks/` |
| D09 三张 2D 法线 | 3 | `assets/ember/data/normals/` |
| D10 小粒子 | 4 | `assets/ember/vfx/particles/` |
| D11 两材质法线／粗糙度／金属度 | 6 | `assets/ember/three_d/textures/metal/`、`concrete/` |
| D12 草叶高度权重 | 1 | `assets/ember/three_d/textures/grass/` |

## 数据采样与配对

单通道 PNG 是 L 灰阶，数据从 `.r` 读取。Mask、Noise、高度、法线、粗糙度、金属度和权重按线性数据采样，不添加 `source_color`。校准色块／颜色 Ramp 用作颜色时，按当前渲染上下文标记颜色采样。不要把数据通道的黄紫预览当作底色美术。

本批导入设置为 Lossless（`compress/mode=0`），明确禁用法线压缩（`compress/normal_map=2`）、粗糙度自动处理（`roughness/mode=1`）和 3D 自动压缩（`detect_3d/compress_to=0`），并关闭 Alpha 边缘填色／预乘和法线绿色翻转。注意法线选项的 `0` 是自动检测，不能用来表示禁用；合并目录中的最终导入策略覆盖制作方保留的历史建议。D11／D12 保留 Mipmaps，其余关闭；过滤和重复由节点、材质或采样器决定，逐图重复轴见目录。8 位 PNG 的参数量化不可避免，例如金属度 .55／粗糙度 .65 对应约 .549／.651。

设备 Mask 使用 **R=局部换色、G=发光、B=允许扰动、A=底图 Alpha**。十张 A 与登记底图一致，R/G 由已确认内窗或实际组件选择生成；风机仅 R 选中叶片，G=0。所有 B=0，表示本批没有启用扰动区。`terminal_window_mask_v001.png` 配对 `terminal_body_v001.png` 的 96×96 画布。底图换版后必须重新派生，不能只改路径。

将 [station_canvas_texture_v001.tres](../../assets/ember/data/normals/station_canvas_texture_v001.tres) 或 [console_canvas_texture_v001.tres](../../assets/ember/data/normals/console_canvas_texture_v001.tres) 指定给自己的 Sprite2D.texture；采用 `centered=false`、`offset=-anchor` 时仍遵循底图锚点。[floor_clean_canvas_texture_v001.tres](../../assets/ember/data/normals/floor_clean_canvas_texture_v001.tres) 配对 ground_details 左上 `(0,0,32,32)` 的实际地板单元，法线是原生 32×32，支持自行重复。

采能站／控制台／地板使用登记的浅浮雕高度代理，不声称是物体的真实三维模型。中性窗保持平面；底图原有像素材质明暗未重新烘焙。金属法线表达原有涂层边界的很浅起伏；混凝土法线明确为平面，避免从颜色噪点猜造凹凸。

新 [metal_technical_v001.tres](../../assets/ember/three_d/materials/metal_technical_v001.tres) 和 [concrete_technical_v001.tres](../../assets/ember/three_d/materials/concrete_technical_v001.tres) 已接入法线及 `.r` 参数图。粗糙度／金属度乘数为 1，参数不被重复相乘；旧底色材质继续保留。草权重按可见区域生成，最高可见像素 y10=1、根部像素 y119=0、透明域=0，基座边界仍是 y120；尚未编写风摆 Shader。

Godot 的 [CanvasTexture](https://docs.godotengine.org/en/stable/classes/class_canvastexture.html) 使用 X+／Y+／Z+ 法线并需要 Light2D 才显示法线效果。PNG 坐标 y 向下，本批高度导数使用 `(-dh/dx,+dh/dy,1)` 后归一化，不在导入时再次翻绿。[官方导入说明](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_images.html)说明过滤／重复由使用节点或材质控制。

## 验证与来源

全部输入由项目程序或已确认几何派生，没有新增生图调用或外部资源。三份制作目录及源脚本保存在 `art-source/ember/technical-inputs-v001/{basic,object-masks,surfaces}/`；数据图不受艺术调色板限制。

40 张源 PNG 与 Godot 导入纹理全部原生像素比较，差异为 0；设备轮廓、固定种子／接缝、法线符号及草根权重有数值验证。真实 GPU 对测试／采能站／控制台／地板共四张法线做 8 次轴向等距移动灯检查，并查看真实底图配对灯光、3D 同视角移动灯及近／远 Mipmaps。新工程没有原缓存或 Autoload，26 张 GPU 截图与原工程字节一致。

[最终验收](../../art-source/ember/technical-inputs-v001/final-acceptance.json)汇总制作来源、跨组独立审阅、8 个实际 Godot 进程阶段和旧资源保护。原 426 项受保护文件，包括美术、游戏、课程练习和历史 ZIP，字节保持一致。

需要重做本批资源时，先阅读三组脚本的参数与覆盖保护；重做派生图要同步版本和验收。检查已有资源可运行：

```powershell
& 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe' --headless --path . --script res://tools/build_ember_technical_inputs.gd -- --verify-only
```

## 完成范围

D13 是最多 30 张布局区域 Mask 的预算，**实际交付 0 张**：现有布局尚未登记水面／露天降雨／热区。先由你用 TileMapLayer 布置和确认具体区域，再按布局生成；岸线可由水面 Mask 派生。可选 collect 动画、参考气氛图和课程 Shader 未因资源准备自动完成，课程进度不变。

完整合并包：[ember_assets_v004_2026-10-04.zip](../../art-source/ember/deliveries/ember_assets_v004_2026-10-04.zip)。v001～v003 历史 ZIP 保持原样；旧版本验收只代表当时发布快照，当前技术资源以本页及最终验收为准。
