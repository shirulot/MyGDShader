# 建筑 v002 整栋主交付独立视觉增量审查

> 最新状态覆盖：用户随后明确退回屋顶/墙体衔接不齐及屋顶大一圈的观感；根已核实用户原消息，当前v002为NEEDS_REVISION。以下初审不能作为当前外观通过，参见[最新根回执](../review-building-v002.md)。

快照：2026-10-06 19:01 UTC+08:00。审查者：TA 子审查代理 `style_specs`。固定ZIP独立解压，只读看图与分层／预制体登记；没有改生产文件或重复生成旧稿。

**历史初审：整栋主交付齐备；原静态通过已因最新用户反馈撤回。** 三栋均已提供干净透明 `complete_closed.png`、整体 `fixed_shell.png`、共同canvas／pivot的必要功能层，以及可直接放置的静态和交互预制体。来源与组装相对v001无新增偏差的判断不证明原屋顶/墙体比例本身正确，当前外观需按用户反馈返修。以下保留原定位证据。

本结论限定控制塔、维修工坊、物流仓库三栋南向资源的交付形式及静态画面。读档、碰撞、机械连续性与冷包执行由其它独立审查合并，不凭静态截图授予行为通过。

## 固定包与范围

ZIP：`art-source/ember/deliveries/building_assets_v002_2026-10-06.zip`，独立实测 SHA256 `18fe88a25dc19aaaf7cdae43505ff3eb04c060b5358daf8171fcc300c4832f35`，279条目。安全解压在本报告所在 `visual/` 目录；以下路径均相对此目录。

依据用户「完整组合为主交付，必要功能才拆层」要求、`docs/shader-learning/building-assets-production-v002.md`、`ta-art-review-standard-v001.md` §4.1及[已完成v001静态报告](../../building-v001-independent/review-visual.md)。入口：`assets/ember/building_assets_v002/README.md`、catalog及`scenes/ember/building_assets_v002/README.md`。提交说明位于ZIP外的 `art-source/ember/building-assets-v002/ta_submission_v002.md`，仅作版本索引。

## 完整主成品与逐栋视觉

已直接查看三张完整透明PNG和三张fixed_shell，读取实际PNG尺寸；完整图四角Alpha均为0。图中没有地板、角色、标签或演示UI。主资产可由同名 `*_static.tscn` 单Sprite直接放置，三份场景均 `centered=false`、Nearest、offset为负pivot、默认scale=1。

| 建筑 | 实测完整canvas／登记pivot | 合层后实际看到的结构 | 静态结论 |
| --- | --- | --- | --- |
| 控制塔 | 192×352／(96,328) | 上层连续三格观察窗、下层双窄窗、人门门框、层间横带、屋顶盖与天线齐全；上下柱与屋顶四周檐边保留完整收边。 | 通过，未见新裁柱／裁檐或窗框错位。 |
| 维修工坊 | 256×256／(128,232) | 两扇独立三格天窗、左前窗、中人门、右检修箱、屋顶风机与短管弯保留；左右角柱、屋顶侧檐和门框接合完整。 | 通过，双天窗没有合成一扇，旧侧檐修复未回退。 |
| 物流仓库 | 320×288／(160,264) | 左人门与中央货门、两条内部屋顶竖肋、左右外梁、屋顶格栅与服务机、右墙检修口完整；门框与导轨仍属同一壳体。 | 通过，屋顶肋／外梁数量与位置保持，无合层漏件。 |

三张fixed_shell保留整栋固定造型，门片、盖板与状态面按功能去除，门洞在固定框内透空。README明确fixed_shell与已包含同一固定像素的功能层是各自使用入口，开发不需将两者重叠显示。实际交互预制体使用功能合层自动组装，静态入口直接使用整张完整图。

## 41层的实际职责核查

逐项读取catalog的 `group`、`kind`、`source_members`及v002组装脚本。合层均用整栋canvas／pivot，预制体在零偏移注册中加载；旧47件保留在v001辅助目录，运行时引用的是v002功能合层。catalog保留细件来源与安装坐标作来源账本，不要求使用者逐柱梁重新拼装。

| 保留层次 | 实际功能／合并证据 | 判断 |
| --- | --- | --- |
| RearShell／Roof／FrontWall | 后墙、屋顶、前墙分别承担前后覆盖与进入室内时的显隐。控制塔屋顶同层已合并center、trim、盖内件／框、天线和格栅；仓库屋顶合并center、trim、格栅、服务机。 | 有必要职责，不要求合成一个无法遮挡的交互Sprite。 |
| 静态背景／前景框层 | 控制塔三组玻璃合并为一个状态层，全部观察窗／窄窗框合为前景静态层；工坊两块天窗玻璃合并，天窗框／风机罩／管弯合为前景层，叶轮在罩内；检修框位于内件之前。 | 固定像素分前后顺序用于覆盖活动／状态面，未见无理由碎件。 |
| DoorLeaves／DoorFrames | 四门片分别响应三个人门及一卷帘；每栋门框已合并且位于门片之前；室内门框／门片淡显与前墙隐藏规则不同。 | 独立门控制和遮挡必要；仓库两门框已为同一静态层。 |
| FrontAccessories及状态Mask | 同栋控制面板与灯壳已合并；灯面按对应门／设备的锁定、活动、故障、供电状态独立。 | 保留各控制对象Mask合理，不要求把独立状态全并为一张同色层。 |
| 盖板／内件／叶轮 | 两侧检修盖及内件、塔屋顶盖、工坊内叶轮有独立机械显隐或运动职责，原固定壳／框已合并。 | 必要活动层。 |

独立统计为19静态层、22活动／状态层，共41层（三栋11／15／15）。数量仅描述实现；判断依据是来源归并、实际显示顺序、显隐和控制职责。当前分层满足完整成品为主、开发必要层为辅的要求。

## 实际状态画面增量

直接查看包内 `assets/ember/building_assets_v002/previews/` 的 native1×／2×、open、interior、maintenance、power_off、fault GPU图，以及塔half_open、工坊locked_glass_lit、仓库maintenance透明状态图。

开门画面中，固定门框与柱梁保持原安装位置，净口透出同一地面，卷帘未残留在门外。检修画面中，塔盖下开口和工坊／仓库内件均在原框内，固定屋顶和墙体不随盖状态变形。室内画面按职责隐藏屋顶和前墙，后墙保留、门框淡显；状态截图没有把固定浅甲整体染色，供电／故障变化集中在玻璃和灯面。当前没有视觉增量返修项。

两张native1×／2×截图的实际SHA与v001此前绑定完全一致，支持既有造型／尺度静态结论延续；v002新预制体实际冷运行及逐像素组装由技术代理另行复验。此次看图没有把制作方118／148／41等PASS数字作为独立视觉通过证据。

## 放行边界

v001「缺三张整栋透明图和必要合层」缺项已关闭，当前无需新增绘图或缩减层数。可保留47细件、母稿和来源登记辅助后续编辑；实际开发使用整栋PNG／静态预制体或已经注册的交互预制体。

当前不扩展到其它朝向、完整室内家具、屋顶通行、自动建筑笔刷或主工程整体替换。建筑与已有角色／地板的造型和尺度评价沿用v001已审范围；用户最终选择及技术行为验收分别记录。

## SHA256证据

下表路径除注明外，相对 `assets/ember/building_assets_v002/`。

| 文件 | SHA256 |
| --- | --- |
| catalog_v002.json | `9a89de864acdcccaf98e3ed6cefab71a89d1edbb9145ae3ebc1cb32b587ed8c1` |
| buildings/control_tower/complete_closed.png | `9ae1c3aebd51a1277d22c7512d7dee93ea17104682b37f2f9a7fad39d6a99f0e` |
| buildings/control_tower/fixed_shell.png | `3534766b7343285cbb1fd7916ffea68c9404e3645e9f9573c0a3e5df5e4345fb` |
| buildings/repair_workshop/complete_closed.png | `9f4ad8df7d2aec56a2f0fdd652a13f96eca846ef36d8adaf0198e1aa67899dbf` |
| buildings/repair_workshop/fixed_shell.png | `27645450f832a6d1a236ad454df23a4820ae6804212be6eef19c3fa51b591d0b` |
| buildings/logistics_warehouse/complete_closed.png | `6b6e0849a07b6acfd38aff249478f79aa3c37561d53d9366ebdc597427df6643` |
| buildings/logistics_warehouse/fixed_shell.png | `3d0394e8be5898a331d186055cbc85215486e856708a3bed3f21514fbd74736b` |
| previews/gpu_buildings_native_1x_v002.png | `5a49ac25213b8abe686d9bc3a96fc36ccfcd80634e98622aeb96638ca51174dd` |
| previews/gpu_buildings_native_2x_v002.png | `8a2b7a5c9a556d553df2f8e1760e2b9ca948dfb8dc10987eb4a063d5e7aeeb61` |
| previews/gpu_buildings_open_v002.png | `920900a7274529e8ca9db1f1aa4e5825443dbae7af7cd8fd587b00b8e25ea04a` |
| previews/gpu_buildings_interior_v002.png | `192d90cbc104bfae79f1879e5b40139006168fb9ae69e324d28fd234129a1e92` |
| previews/gpu_buildings_maintenance_v002.png | `30f867ea1aa6c160204976ab1d5544cc3693da451d85375f931a43574183ae3f` |
| previews/gpu_buildings_power_off_v002.png | `f138a34cfebf855727883ed43e956dca8c77f2f8c3c6975981542be60fd0e797` |
| previews/gpu_buildings_fault_v002.png | `a9a4a0cf0c39236089d0b8373de36e7d3672e6ff70547fa1de55e75301574911` |
