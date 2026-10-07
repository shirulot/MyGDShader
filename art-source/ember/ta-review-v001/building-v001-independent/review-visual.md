# 建筑 v001 独立静态视觉审查

审查快照：2026-10-06 17:25（UTC+08:00）。审查者：TA 子审查代理 `style_specs`。只读审查生产文件，本文件为独占输出。

**结论：三栋南向实拼的静态造型通过；按用户本轮补充的“完整组合为主交付”要求，当前固定包仍需补交组合资源。** 缺项与造型评价分开。未发现需要重新生成这三栋已实拼造型的静态视觉阻塞问题；此结论不替代根代理的动作连续性、碰撞与完整引擎状态审核，也不代替用户最终验收。

## 固定版本及审查依据

固定包：`art-source/ember/deliveries/building_assets_v001_2026-10-06.zip`，实测 SHA256 `5870774d53e2010158523021661cf30a560386fe2826c39a66845d8e7e45dbc1`。

实测登记文件：

- `source_specs_v001.json`：`1e58c5e406040f59c760db41c814856356db8fae2396329ae060fcce91926fd8`。
- `assets/ember/building_assets_v001/catalog_v001.json`：`f41c1673a06aa662bc2f7c6df2dfe47f5a4d5cb48e9f21ad6e161c462d212060`。
- 下列原生图、状态图、联系图及四件关键墙／屋顶PNG共11项，直接读取ZIP成员计算SHA，均与审查时工作区文件一致；没有用历史prototype代替最终实拼。

依据：`docs/shader-learning/art-style-standard-v002.md`、`ember-building-standard-v001.md`、`selected-buildings-breakdown-v001.md`、`building-assets-production-v001.md`，以及用户最新授权对应的 `ta-art-review-standard-v001.md` §4.1。制作方的 `visual_review_v001.json` 仅作索引，以下判断来自直接看图和登记核对。

直接查看三份用户选图：`art-source/ember/selected-buildings-v001/references/{control_tower,repair_workshop,logistics_warehouse}_user_selected.png`；最终GPU图位于 `assets/ember/building_assets_v001/previews/`，已看 `gpu_buildings_native_1x_v001.png`、整数2x、closed、open、interior、maintenance、power_off、fault、`gpu_parts_library_v001.png`（47件）及动作07室内／08开盖的静态画面。另直接查看工坊／仓库的 `front_wall.png` 与 `roof.png`。

## 逐栋静态结论

| 建筑 | 实际看到的关键结构 | 比例、拼接与最小处理 | 结论 |
| --- | --- | --- | --- |
| 控制塔 | 两层立面，上层三格连续观察窗；下层门两侧各一窄窗；屋顶检修盖、右后天线、格栅齐全。轻装甲与蓝灰结构关系清楚。 | 窗格上／下边框及两条内分隔杆完整；上层柱、层间横带、下层角柱与门框接合未见背景漏缝。屋顶角帽的黄铜比选图减弱、门洞按40×56净口整理，属于已登记差异，无需逐像素复刻。 | 静态通过 |
| 维修工坊 | 宽单层房间；独立的两扇三格天窗；右后风机和短黄铜管弯；前立面左窗、中央人门、右低检修箱。 | 最终左右角柱均保留完整倒角和底部收边；屋顶左右侧檐没有旧cover裸断边。天窗玻璃与框的边界贴合，未越过分隔杆。门／窗／检修箱与墙壳有正常的边框遮盖，未见明显拼贴错位。 | 静态通过 |
| 物流仓库 | 左人门与中央宽货门；屋顶恰好两条内部竖肋，另有左右外梁；右上格栅及右下服务机可辨。 | 最终左右立面角柱、左右屋顶外收边均完整；两内部肋与北／南檐交接没有裸截口；货门框、导轨、卷帘和墙面连接连续。右立面检修口是功能补设计，不是遗漏选图部件。 | 静态通过 |

旧“裁柱／裁侧檐”问题在本固定包中已实际修复。catalog中三栋前墙登记为 `border_preserve`、3段；屋顶为 `border_preserve`、9段；三格观察窗、天窗与工坊窗框各27段。判断依据同时包含最终部件和完整GPU实拼，不仅是这些模式字段或制作方PASS。保护边界注册不能等同于对选图的完整等比例缩放，但当前柱檐保留和组装结果可接受。

## 尺度、材料与状态画面

三栋登记分别为128×128、192×128、256×160 world脚印；建筑1原生纹理像素=1 world、scale=1；已有地板128纹理／32 world、scale=0.25继续独立使用。最终屋顶纵深比用户选图大，来自完整覆盖正式脚印的登记约定。它改变顶面可见占比，但没有把工坊变成设备架、仓库变成箱子或塔变成筒体；不按选图像素尺寸拒收。

native1x／2x中现有机器人约26×42 world主体与40×56人门净口存在合理余量；货门104×60净口与大仓库用途相称。浅装甲、低饱和蓝灰、局部黄铜、左上照明及清楚像素面保持统一；旧化磨损没有压过门窗轮廓，也没有变成高光写实金属或密集明亮铆钉。实际地面延续已有低对比方向，建筑与角色没有明显材质语言冲突。

闭合／全开截图中门框安装位置保持，门片覆盖与净口边界合理，全开后露出同一连续地面，未见明显墙外穿洞。维修图中盖下内件在框内，屋顶检查口具有独立开口。断电／故障截图把暗或红变化限制在窗／指示面，固定装甲没有整体染色。室内图隐藏屋顶与前壳、保留后墙和地面；本批不包含完整室内家具关卡，空室内不能据此判成美术漏件。以上都是静态状态画面评价，不能据单帧宣称门动画、风机停转或Physics2D已通过。

## 新增交付缺项：完整组合主资源

固定ZIP中已存在三栋 `scenes/ember/building_assets_v001/{control_tower,repair_workshop,logistics_warehouse}.tscn`；各场景由 `scripts/ember/building_asset_v001.gd` 根据catalog恢复组合，GPU图确认可形成完整建筑。因此本批并非只有零件，也不是完全无法组装。

但对ZIP所有PNG成员核查后，本建筑载荷只有单件masters、47件parts与带地面／角色的GPU预览。**没有三张整栋透明PNG，也没有在整栋统一canvas／pivot下整理的必要静态功能合层。** 当前屋顶center／trim、柱、窗框、格栅、天线等仍按细件登记；细件库和效果截图不能独立满足用户最新的主交付形式。

最小补交：

1. 为三栋各提供一张默认闭合状态的整栋透明RGBA PNG，不带地面、角色或UI；使用现有整栋画布192×352／256×256／320×288及pivot(96,328)／(128,232)／(160,264)。现有实拼同源无损合成即可，无需重新生成造型。
2. 按实际高度、前后与进入遮挡需要合并静态主体，例如屋顶壳、前壳／后壳与确需独立的高度层；将同层固定柱、檐、窗框、格栅等并入相应壳体。门片／卷帘、盖板、风机叶轮、状态窗等继续独立。以功能为边界，不强制统一层数。
3. 把整栋与功能合层登记进catalog／README，保留单件来源、同一canvas／pivot／安装坐标；证明功能层与默认活动件重组可逐像素恢复整栋图，替换引用后状态和遮挡不回退。新增内容另封固定版本与哈希，不改写本审查绑定的ZIP。

这属于用户本轮明确的交付形式补充，不追溯为旧造型失败。补齐并复验组合图与功能层后，可以关闭该交付缺项。

## 快照证据SHA256

| 文件（相对 `assets/ember/building_assets_v001/`） | SHA256 |
| --- | --- |
| previews/gpu_buildings_native_1x_v001.png | `5a49ac25213b8abe686d9bc3a96fc36ccfcd80634e98622aeb96638ca51174dd` |
| previews/gpu_buildings_native_2x_v001.png | `8a2b7a5c9a556d553df2f8e1760e2b9ca948dfb8dc10987eb4a063d5e7aeeb61` |
| previews/gpu_buildings_closed_v001.png | `a977117b82b90e034850b423d93c7c72060977c1f9d6bacdd06b98874871dfcb` |
| previews/gpu_buildings_open_v001.png | `d91671fed79dd1de83894134e85d1a4bca73516dc5a1528e59f0b9e75da66fb1` |
| previews/gpu_buildings_interior_v001.png | `db4ffbebbec92d43150b6898170e7b2f0f6c338317502d092aea32a81a9713e5` |
| previews/gpu_buildings_maintenance_v001.png | `0d5914c2464eaec30212f7f4f866957a463bc79c8f008db0c134f64b5fd8693f` |
| previews/gpu_parts_library_v001.png | `204f4fec077518f1b331a6cd5c42569ca1ccdb0bccc1459442ed43bd2dcd42ab` |
| parts/repair_workshop_front_wall.png | `3aec86ff45aa3a21e7d118025d182c43ba70708ea4ead15296aa5de0bec4d2d8` |
| parts/logistics_warehouse_front_wall.png | `8df268eb31255fad3e41c985249a85d2c4bb2bf62d6027643e30936ddd6329f2` |
| parts/repair_workshop_roof.png | `ec4f8b53baa0c86fe22885d4b658237cc62b58a3fe589fbad31132898f19d32d` |
| parts/logistics_warehouse_roof.png | `fc725114ebb561375eba59fef11d91bdab820b8e3419bf947f5424b6b7bd47f7` |
