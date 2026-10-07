# v007：旧 tile 全项风格统一

2026-10-05。完成资源整理和引擎验证，视觉状态仍为候选，不能把技术通过写成用户认可。

## 直接使用

- **完整笔刷页**：`scenes/ember/manual_brush_preview_v007.tscn`，打开后 F6。左侧选择 67 个笔刷，右侧左键画、右键擦。透明附件与底板分层。
- **自动铺刷页**：`scenes/ember/autotile_sandbox_v007.tscn`，F6 后左键画、右键擦，滚轮缩放，中键拖动。
- **完整手工 TileSet**：`assets/ember/environment/tilesets_v007/ember_common_tileset_v007.tres`。保持旧 67 个 ID 及 atlas 坐标；使用 128px 纹理，TileMapLayer 缩放 0.25，对应 32 世界单位。
- **Terrain TileSet**：`assets/ember/environment/autotiles_v007/*_terrain_v007.tres`，7 个图集共 236 种连接配置。
- **全部笔刷大图**：[all_brushes_review.png](../../assets/ember/environment/tilesets_v007/all_brushes_review.png)。
- **引擎实际渲染**：[手工笔刷页](../../assets/ember/environment/tilesets_v007/godot_brush_preview.png)、[自动铺刷页](../../assets/ember/environment/autotiles_v007/godot_render.png)。

## 旧清单覆盖

| 类别 | 新版处理 |
| --- | --- |
| T01 地板 | 新生成清洁内区及磨损、格栅、湿润填充；四种填充统一实际边缘。自动地板保留 v006 画好的边角，替换误含缺口的全内区 |
| T02 墙体 | 使用 v006 重绘及切片注册修复结果，13 个旧笔刷映射到对应完整 Terrain 图块 |
| T03 栏杆 | 完整重绘 16 种连接；保留双梁和柱帽布局，修正邻格残留导致的转角压偏 |
| T04 管线 | 完整重绘 16 种连接；保留原弯管走向和管径，更新圆润金属明暗及黄铜接头；阀门单独生成后安装到水平管线，保留两侧端口 |
| T05 水渠 | 修复此前被拒岸沿稿的切片串边，保留原画凹角并统一接口；水面沿用无缝静态蓝色底层 |
| T06 栈桥 | 使用 v006 新桥面；补齐旧清单中的独立边梁和四方向收尾，边梁从画好的构件提取，不旋转光照 |
| T07 检修口 | 新生成开／关两态，同尺寸、同安装位置 |
| T08 贴花 | 新生成裂纹、锈迹、螺栓、油渍、电缆环、碎屑六类，保留透明背景 |

旧 v001 基础 62 项，加 v002 补充的 5 个桥边／收尾，共 67 个旧 ID 全部登记于 `tilesets_v007/migration.json`。这 67 项与 236 个自动连接配置有重叠，不相加为新的艺术预算。四种地板填充可手工混刷；自动 Terrain 页面展示的是清洁地板，不宣称另有三套 47 型地板。

## 采用的美术规范

蓝灰工业钢材、克制黄铜、左上光照、细腻明暗和自然转角。纹理统一 128px，保留完整构件；不强制 16 色、二值 Alpha 或原生 32px 像素阶梯角。官方连接模板只决定语义与槽位。

生图排版不是精确网格：管线／栏杆按完整构件注册，排除闭合端附近串入的邻格像素；岸沿的开放边排除跨行阴影，再保留同格原画凹角。所有原稿、归一图、提示词、提取坐标及生成记录在 `art-source/ember/autotiles-v007/`。

## 已验证和边界

- Godot 4.7.2：25,541 个 Terrain 格子检查，0 失败；包括邻域组合、随机铺刷和擦除后重建。
- 2,960 对兼容接口 RGBA 检查：0 不匹配；48 个路径图块的端口到主体检查：0 失败。
- 四种地板 32 对横／纵邻接：0 RGBA 不匹配。
- 67 个手工笔刷：保存、重载、坐标和 ID 核验通过；预览运行、透明附件叠加和擦除已实际执行，并保存 GPU 截图。
- 已查看完整笔刷图及实际铺刷。仍存在可继续打磨的视觉问题：部分地板转角接点重复，池岸局部压顶阴影宽度有变化，墙面有轻微块间明暗差。因此保留候选状态，不能据接口测试宣称整套美术无瑕疵。
- 本轮完成新版资源与预览；主游戏场景尚未迁移，历史 v001～v006 保留。使用新版时更换 TileSet 并设置相应层缩放，不能仅把 128px 图覆盖进旧 32px atlas 配置。

## 可复现构建

1. `python tools/build_ember_autotiles_v007.py`
2. `python tools/build_ember_manual_tiles_v007.py`
3. `python tools/check_ember_v006_ports.py --revision v007`
4. Godot 执行 `--headless --path . --editor --import`。
5. Godot 执行 `--headless --path . --script res://tools/build_ember_autotiles.gd -- --revision=v007`。
6. Godot 执行 `--headless --path . --script res://tools/build_ember_manual_tiles_v007.gd`。
7. GPU 截图分别运行 `tools/capture_ember_seams.gd -- --revision=v007` 和 `tools/capture_ember_manual_v007.gd`，不传 `--headless`。

Windows GUI 版 Godot 用 `Start-Process -WindowStyle Hidden -Wait` 等待构建结束并检查日志。
