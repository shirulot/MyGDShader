# 参考效果图对应的地板生产标准与交付 v002

本轮依据用户的新要求：**完成的素材必须实际拼出接近已认可效果图的场景，并以铺刷自动补全为最高优先级。** 旧 `pixel_floor_v001` 的结构验证仍保留，但其视觉已被用户否定，不能作为新包的艺术完成依据。

## 参考与比例

唯一场景艺术目标为 [认可效果图](../../art-source/ember/pixel-standard-v002/previews/scene_preview_v001.png)。本轮新地板位于 `assets/ember/environment/reference_floor_v002/`，旧角色和主游戏入口继续保留；演示组合使用已有角色／设备作为比例参照。

| 项目 | 生产值 | 用途 |
| --- | --- | --- |
| 逻辑世界格 | 32×32 world | 保持工程坐标约定 |
| 纹理格、TileSet.tile_size、atlas region | 128×128 texture px | 保留原始生图的材质与细节容量 |
| TileMapLayer.scale | `(0.25,0.25)` | 128纹理格映射32世界格，不能漏设 |
| 展示倍率 | 1 world px = 2 display px | 参考图1536×1024同幅对照 |
| 暖灰压顶 | 8 world / 32 texture px | 可见厚度与磨损、接头、螺栓 |
| 南向立面 | 32 world / 128 texture px | 投影在平台顶面外，深色大板与立柱 |
| 桥默认笔刷 | 2格宽 | 允许真正的格栅桥梁和桥台 |
| 桥外侧退让 | 每侧12 world px | 二格64world范围内保留40world桥体，接岸保留肩口 |

这里的128纹理格取代旧美术 v2 的32原生格建议及旧包24px单格桥宽要求，原因是用户将参考效果的实际复现置于此前尺寸建议之上。不能只替换旧 PNG 后继续使用旧 atlas 坐标与缩放。

## 材料与图层

底面为安静的蓝灰涂装钢，保留成片涂装变化和稀疏磨损，不把母稿压成五色颗粒。暖灰压顶有连续倒角、磨损边和接头；深钢板立面采用较大的面板、支撑与固定上左光。外凸角斜切、内凹角包住缺口；不能旋转含固定光照的完整立面假装另一个方向。

格栅桥的网格、承重梁、桥头盖板、小黄铜固定件均来自实际 artist 母稿。地板和桥组合时根据像素足迹处理周界：桥接入平台的40world通道打开，通道两侧12world肩口仍有压顶和立面。普通地板47型本身不足以表达这类跨层上下文，需要派生层自动补齐。

板缝、检修格栅、水平栏杆和转角栏杆作为独立装饰，避免每格自动添加装饰抢占画面。它们不参与可行走地形的邻接判断。装饰位置不能用来掩盖地板或桥的连接错误。

## 铺刷约定与验证

面积地形使用八邻接47型：N、NE、E、SE、S、SW、W、NW；对角只有在相邻的两个正交格均存在时成立。原生 Terrain 负责输入层拓扑，补全器负责共享大面纹理相位、桥口、压顶和投影立面。只复制47张图片、跳过补全脚本不能获得展示图的全部跨层效果。

验收必须同时查看实际 TileMapLayer 组合画面和自动铺刷测试。至少覆盖256邻域、不同刷序、四方向接桥、L/T交汇、洞、孤岛、擦除后重连、保存重载和纹理格缩放。工具的撤销重做与编辑器GUI撤销重做分开记录；没有实际测试的项目标明未测。

独立检查脚本：[validate_reference_floor_v002.gd](../../tools/validate_reference_floor_v002.gd)。真实细节切片脚本：[build_reference_details_v002.gd](../../tools/build_reference_details_v002.gd)。细节坐标与来源：[details_catalog_v002.json](../../assets/ember/environment/reference_floor_v002/details_catalog_v002.json)。

## 生图与来源

采用内置 `imagegen` 工具，五份平台／桥／方向角／细节／水纹母稿和完整提示词保留于 [源文件目录](../../art-source/ember/reference-floor-v002/)。母稿是 AI 生成图，不登记为 CC0。生产整理仅裁取实际像素、nearest缩放、按足迹去掉背景和整理 atlas，不减去局部均值，不量化材质色阶，不程序重画艺术面。

生图请求设置了透明背景，但实际模块母稿中部分区域仍为不透明背景；生产稿使用明确几何足迹 Alpha。水纹另有独立的实际生图母稿，取代早期样图中的参考水域裁片；可选展示装饰分别登记。

最终艺术状态仍为候选，用户对概念效果图的认可不能转写为用户已接受新瓦片。结构验证的具体结果和可运行文件入口以同目录 README 和验收 JSON 为准。

交付入口：[完整独立工程 ZIP](../../art-source/ember/deliveries/reference_floor_v002_2026-10-06.zip)、[铺刷使用说明](../../assets/ember/environment/reference_floor_v002/README.md)、[实际GPU实拼图](../../assets/ember/environment/reference_floor_v002/gpu_reference_scene_v002.png)。独立复验27,909格通过；GPU连续擦除两个2×2区域后，露出的水面与CPU图层结果一致。原生编辑器GUI撤销重做仍标为未测。
