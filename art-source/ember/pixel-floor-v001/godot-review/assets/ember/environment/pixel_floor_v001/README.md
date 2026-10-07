# 可自动铺刷地板 v001

依据用户认可的[场景效果图](../../../../art-source/ember/pixel-standard-v002/previews/scene_preview_v001.png)制作。原生纹理格和世界格均为 **32×32**。当前结构版本 v001，材质修正版 v002；首版视觉偏差的结构快照另行保留。正式材质采用 AI 母稿实际取样、局部低频校正和5阶原生量化，几何通过 Godot 构建脚本生成。

材质修正：取消周期大色块和纯色边带，钢板使用围绕 `#4B6876` 的细颗粒5阶；平台压顶改暖灰并加入稀疏分段；桥孔压暗，金属条去除过亮青色。局部磨损通过独立 Details 控制，基础中心不反复烘焙油斑。

## 图层与使用方式

| 图层 | 笔刷语义 | 图集结构 | 使用资源 |
| --- | --- | --- | --- |
| Floor | 连续钢板区域 | 47 型面积 | `floor_terrain_v001.tres` |
| FloorLanding | 桥端落地修正 | 89 型上下文覆盖 | 共用 Floor TileSet 的普通 source 1，由工具同步 |
| FloorFacade | 平台南向外立面投影 | 47 型＋89 型桥口 | `facade_terrain_v001.tres`，由工具同步 |
| Rim | 平台周界 | 47 型透明覆盖 | `rim_terrain_v001.tres`，由 Floor 同步 |
| Grate | 地板上的格栅区域 | 47 型面积覆盖 | `grate_terrain_v001.tres` |
| Seam | 稀疏板缝路径 | 16 型网络 | `seam_terrain_v001.tres` |
| Bridge | 24px 宽步道 | 16 型网络 | `bridge_terrain_v001.tres` |
| Details | 油渍、磨损、锈、细裂、两态检修口 | 8 个普通图块 | `details_tileset_v001.tres` |

最直接的试用入口是[试铺场景](../../../../scenes/ember/pixel_floor_sandbox_v001.tscn)。运行后用 `1～5` 切换地板、格栅、板缝、桥、装饰，装饰类型由下拉框选择；左键连续绘制，右键擦除，中键拖动画面。`Ctrl+Z/Y` 撤销／重做，`Ctrl+S/L` 保存／读取，支持整数 1／2／4 倍观察。

运行试铺工具时，Floor 与 Rim 共用地板占用；Grate、Seam 和 Details 限于 Floor；同格 Floor 优先于 Bridge。删除地板会同步移除失去承载的覆盖层。板缝按笔划登记端口，相邻的独立路径不会自动串接。桥端接地板时开放中央 24px，保留两侧各 4px 的肩口；桥增删都会重算接头。

## 接入自己的场景

1. 复制本目录、[试铺脚本](../../../../scripts/ember/pixel_floor_painter_v001.gd)和试铺场景，保持 `res://` 路径不变。
2. 以试铺场景为模板，保留根节点脚本以及 `Floor`、`FloorLanding`、`FloorFacade`、`Rim`、`Grate`、`Seam`、`Bridge`、`Details` 子层的名字。FloorFacade 位于 Floor 之前绘制，位置固定 `(0,16)`；FloorLanding 在 Floor 上方、Grate／Seam／Rim 下方。TileMapLayer 使用 `(1,1)` 缩放和 Nearest；不把 32px 纹理缩放成旧 128px 格。
3. 运行后绘制并保存布局。`user://pixel_floor_layout_v001.json` 保存占用及板缝连接语义，重新读取时重建所有图块。运行时保存不会改写 `.tscn`。
4. 需要在编辑器画地形时，Floor／Grate 用 Terrain Connect，Seam 用 Terrain Path，Bridge 用 Terrain Connect。脚本的 `@tool` 同步处理跨层收口。Rim 和额外落桥图块不要手选铺刷。

试铺工具的运行区域由脚本 `BOARD` 固定为 22×16 格；接入更大的运行地图时修改该矩形。编辑器手动绘制不受此矩形限制。验收区分原生 Terrain API、工具运行时操作和编辑器 GUI；目前编辑器 GUI 的 UndoRedo 未实测，不能用工具的撤销／重做结果代替。

基础五家族已经配置 Terrain，单独拿各 `.tres` 也可在当前图层进行原生地形补全。**Godot 原生 Terrain 不跨层同步**；平台周界和桥端联动依赖随包脚本。Floor 始终保留 source 0 的基础 Terrain 图块；额外落桥图块位于普通 atlas source 1，分别由 FloorLanding／Rim 按“地板邻域＋桥端口”选用，不混进随机 Terrain 候选。这样原生 Terrain 编辑的 Floor 不会把落桥格误读为空地。

自己通过 API 操作独立 TileMapLayer 时，擦除不能只调用 `erase_cell()`：本机验证需要显式用 `set_cells_terrain_connect(removed, 0, -1, false)` 通知空地，再对存活格重新 Connect。随包工具根据语义占用重建所有相关层，已处理擦除后的补全。

Details 使用普通 atlas source 0，槽位次序见[装饰目录](details_catalog.json)。贴花与检修口不会参与邻域。打开的检修口仅表示外观；本包不设置掉落、碰撞或导航。

## 结构约定与范围

- 面积掩码：`N NE E SE S SW W NW`，位权 `1 2 4 8 16 32 64 128`；对角须同时有两侧正交邻居。
- 网络掩码：`N E S W`，位权 `1 2 4 8`；桥的开放端口固定为像素区间 `[4,28)`。
- 落桥口内侧有 4px 短格栅踏板，衔接桥面与蓝灰钢板；Rim 在整个桥通道上保持透明，两侧保留肩口。
- FloorFacade 将南向外露边投影成 16px 深钢立面。纹理上半16px透明，图层偏移16px，实际从地板格下缘延伸到格外16px；南侧已有地板时全透明，接南桥时中央24px全高透空。它是视觉投影，不加入可走占用、碰撞或导航。
- Grate 覆盖层的孔为真实透明，可看到下方地板；Bridge 的孔底为不透明深色，表现完整桥面，不会透出下方水纹。
- 周界 Rim 按**地板**占用解释，不是水岸 `water_bank_47`。空白区由游戏定义；本包不包含水面纹理或水域 Shader。
- 本轮交付钢板、格栅、板缝、步道及地面装饰；门、机器人、管线、栏杆等仍用各自资源。

来源和要素拆解见[分析记录](../../../../art-source/ember/pixel-standard-v002/floor-production-v001/scene-factor-analysis.md)。像素检查与实际引擎检查分别记录在 `pixel_validation.json` 和 `engine_validation.json`；视觉方向来自已认可效果图，本包成品仍供用户实际审阅。
