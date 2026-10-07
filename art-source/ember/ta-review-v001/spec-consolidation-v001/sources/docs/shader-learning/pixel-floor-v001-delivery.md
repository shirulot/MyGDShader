# 可铺刷地板交付：结构 v001／材质 v002

**历史交付：用户随后明确否定本包的视觉。** 下文保留当时的结构检查与文件记录，不代表当前美术认可。新版入口为[参考效果地板 v002](reference-floor-v002-production.md)。

2026-10-06。依据用户认可的[参考场景](../../art-source/ember/pixel-standard-v002/previews/scene_preview_v001.png)，优先保证实际铺刷补全。用户指出首版视觉偏离后，已改用实际 AI 材质取样、细颗粒钢板、暖灰压顶、暗桥孔，并补充平台南向外立面。参考场景认可与本包用户视觉认可分开记录；当前成品仍为视觉候选。

## 可直接使用的文件

- [完整独立工程 ZIP](../../art-source/ember/deliveries/pixel_floor_v001_material_v002_2026-10-06.zip)：123个文件，约6.2MB；无旧导入缓存启动通过，逐文件压缩包SHA256校验失败0。解压后导入 `project.godot` 即可运行。
- [资源与接入说明](../../assets/ember/environment/pixel_floor_v001/README.md)：PNG、TileSet、图层顺序、跨层同步和快捷键。
- [可运行试铺场景](../../scenes/ember/pixel_floor_sandbox_v001.tscn)：五种笔刷、绘制／擦除、撤销重做、保存重载、整数倍观察。
- [真实素材展示场景](../../scenes/ember/pixel_floor_showcase_v001.tscn)：地板、孔洞、桥、装饰及现有原生机器人／采能站。
- [实际 GPU 展示图](../../assets/ember/environment/pixel_floor_v001/gpu_scene_showcase_1x_v001.png)、[2倍图](../../assets/ember/environment/pixel_floor_v001/gpu_scene_showcase_2x_v001.png)。背景水色仅用于展示，不是本轮交付的水域素材。
- [完整提示词与生产来源](../../art-source/ember/pixel-standard-v002/floor-production-v001/README.md)。

原生纹理／世界格32px，Nearest，图层缩放1。独立试铺工程位于 `art-source/ember/pixel-floor-v001/godot-review/`，不依赖原工程的 Game autoload。

## 交付数量与分工

| 家族 | 配置数 | 图集 |
| --- | ---: | --- |
| 连续钢板、透明周界、格栅 | 各47 | 各256×192 |
| 板缝路径、24px步道 | 各16 | 各256×64 |
| 地板／周界桥端接头 | 各89 | 各256×384 |
| 南向外立面／立面桥口 | 47＋89 | 256×192／256×384 |
| 油渍、磨损、锈、细裂、两态检修口 | 8 | 256×32 |

共10张生产 atlas、7份 `.tres`，487核心结构配置＋8装饰配置。此为配置数，包含透明内部块、上下文组合，不与旧123艺术预算重复累计。

Floor 保持原生 Terrain 的47基础块；FloorLanding／Rim／FloorFacade 根据同一份地板与桥语义同步，不把无 Terrain 身份的接头写回用户编辑的 Floor。桥24px端口与两侧4px肩口固定，入口4px短格栅踏板接续材质。南向外立面投影16px，南桥口中央24px全高透明，不改变可走区域。

## 已完成验证与边界

[核心像素报告](../../assets/ember/environment/pixel_floor_v001/pixel_validation.json)：351块、359,424块内像素、1,638,400邻接带像素、340,032桥口像素、4,096端口，零失败。验证的是格边及两侧4px带、Alpha、端口、内部连通和相位，不只比较最外一排。

[立面报告](../../assets/ember/environment/pixel_floor_v001/facade_validation.json)：136块，139,264 Alpha像素、17,408南桥口像素与704邻接／周期检查，零失败；原核心PNG哈希保持。

[Godot 4.7.2报告](../../assets/ember/environment/pixel_floor_v001/engine_validation.json)：117,851格检查，三个面积家族各256邻域、两个网络各16组合，各家族24随机区域及3种绘制顺序；89桥口及擦除收口、128次五笔刷编辑、平行板缝、8装饰槽、覆盖层裁剪、原生邻刷／擦格、撤销重做、保存重载、场景重载及派生立面同步均通过。隔离验证四阶段退出0、stderr为空，并保存8张真实GPU技术截图和2张展示截图。

原生 Terrain API、工具运行时和编辑器 GUI 分开验收。编辑器 GUI UndoRedo未实测；推荐先运行随包试铺工具。独立使用 API 擦除需显式通知 empty Terrain，再重选存活邻格，不能只调用 `erase_cell()`。跨层自动联动依赖工具脚本；本包没有设置碰撞、导航或游戏逻辑。

## 重新生成

在包含源母稿与规范JSON的工程根目录，依次运行 Godot headless 脚本：

```text
godot --headless --path . --script res://tools/build_pixel_floor_art_v001.gd
godot --headless --path . --script res://tools/build_pixel_floor_details_v001.gd
godot --headless --path . --script res://tools/build_pixel_floor_facade_v001.gd
godot --headless --path . --script res://tools/build_pixel_floor_v001.gd
```

第一步默认材质v002；只有显式追加 `-- --material=v001` 才重造历史首版。必须在基础catalog之后重建facade，再构建嵌入图片的TileSet。PNG改了但 `.tres` 未重新构建时，场景会继续显示旧嵌入图片。项目内隔离工程的 `run_validation.ps1` 完成重嵌与GPU复验，`run_showcase.ps1` 重拍展示。
