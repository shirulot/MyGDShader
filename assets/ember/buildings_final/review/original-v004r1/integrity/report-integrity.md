# 建筑 v004r1 来源、覆盖与注册增量审查

结论：**本轮来源 / 二值 Alpha / 可见 RGB / 同源功能合层 / 注册 / 固定包范围 PASS，原实体 Alpha P2 可关闭，未确认新的技术 P1 / P2。** 三个 fixed_architecture 层有 Alpha0 白色隐藏 RGB，不能声称全部15层的透空 RGBA 都为0；这不改变 Nearest 下可见复合，不升级为新的视觉阻塞。作者已在包外说明撤回泛化，固定 ZIP 未改。独立 UI P2 的关闭另见 `../ui-technical/review-ui-incremental.md`；造型与深浅底边缘由根 TA 汇总。

本轮从固定 ZIP 独立解到 `package/`，未编辑生产、未运行生产生成脚本、未重新启动 Godot / 捕获 GPU。独立脚本 `verify.py`、逐条数据 `evidence.json`，便携项目 / README 差异在 `portable-text-diff.json`；包外说明的绑定副本为 `bound-review-clarifications.md`。作者94项行为证据与另一代理的独立UI12项均不冒称本代理重跑。

## 固定包与原始来源

`building_assets_v004r1_2026-10-06.zip` SHA `22dc4017aef594f33350e71b0af723909fbd1c4fde1a88208c9a66e34c9e2a32`，28,875,505 B、79 entries / 78 manifest payload。CRC 无错误、无重名路径；78项字节数 / ZIP SHA / 解包 SHA 均匹配，只有 manifest 自身不自列入清单。78载荷还逐一与作者 portable stage 同 SHA。

旧 v004 ZIP 保留，当前 SHA `7d0b44613858a073ecb2696f88e4c4188dc7a58b38aa3d7a6f20279ae6d70ff5`。两包共同条目仅 README、便携 project.godot 和 manifest 改动，其余25条目同字节；三原母稿、用户三参考图 / 选图记录、提示词、旧 catalog、既有 runtime / shader、旧地板与角色图片均保持原字节。本批没有重生建筑或从旧碎件反推造型。

三母稿 SHA：控制塔 `3989ea530ae9200b3b95763826c3b0113139f3274fa168a0db1b84308f82b7fa`；维修间 `c61f2ad82b4e99f096321289a737b23fd7af25af7b4838cb3e1f0b600a20317c`；物流仓库 `9f9f74df29d9d62259be77fa0da0cb362368e2b0640ca977aac5b9ba5b9ecc50`，均与新 catalog、旧固定包及 coverage 登记一致。当前5个受保护工程文件与历史 `ui-v003-integrity/integrity-v003.json` 快照同 SHA（主 project.godot、energy_station、旧港地图、m0 UI、ember_harvest）。这是该快照到当前的比较边界，不宣称覆盖全部历史过程。

## 三整栋、共享覆盖和15功能层

按未改母稿独立重算一次 `Alpha >= 128`：实体保留原 RGB、Alpha255；完整PNG透空 RGBA0；mask 实体全255、透空全0。三完整PNG与三mask对独立结果**全 RGBA 0差**，覆盖内源 RGB 通道变化0，无腐蚀 / 膨胀 / 改色 / 重采样。三栋覆盖点为635100 / 725420 / 630463，丢弃低Alpha点17128 / 19514 / 19357，与作者覆盖统计一致。

从同一生产PNG按原门 / 设备 / 灯 / 玻璃区域及倒角独立分配15功能层。每层实际Alpha只有0/255、canvas均1254×1254；所有层的**可见RGBA**对独立分配0差，合法覆盖无重复所有权、漏点0；在规范透明背景上逐覆盖点组合回完整生产图，全RGBA0差。共同canvas / pivot / scale登记与母稿一致，没有拼接拉伸或各层独立阈值。

必须保留的例外：3个 fixed_architecture 在被移交给功能层的透明区使用 Godot `Color.TRANSPARENT`，实际RGB为白色。独立核得：

| 固定层 | Alpha0、RGB非0像素 |
|---|---:|
| control_tower | 109852 |
| repair_workshop | 27098 |
| logistics_warehouse | 49035 |

其余12功能PNG、3完整PNG和3mask透明RGB均0。三个固定层对“清空RGBA0”的独立文件模型有185985个原始RGBA差，全部是上述隐藏白RGB；可见Alpha / RGB和实际合层0差。通过组合不抹掉这项文件事实，也不把隐藏RGB差包装成新造型问题。原正式门槛是实体二值Alpha，因此原P2关闭；纠正说明或后续将清空值改为 `Color(0,0,0,0)` 可对齐泛化声明，无需因此重跑GPU。包外 `review_clarifications_v004r1.md` 已明确例外并绑定固定SHA，其内容没有改变包内载荷。

## 数值注册与变更范围

使用十进制精确解析比较旧 / 新 catalog 132个数值叶；整数写法 `635`→`635.0` 作为同一数值处理，没有误计为几何变更。source坐标、canvas、pivot、footprint、uniform_scale、门源矩形、倒角、净口与设备区域均完全同值。唯一数值差为塔的派生 `center_world_x`：`1.9555555555555557`→`1.9555555555555555`，约2.2e−16，不虚写成全部JSON数值逐字精确相同。

未改的 building_asset_v004.gd 第50–53行仍从 source_rect / source_pivot / native_scale 重算实际门中心，不使用该派生值，所以这不是运行几何变化。3个单Sprite静态prefab的offset与源pivot、两轴等比scale与完整精度catalog、Nearest和centered=false一致；3交互prefab只换新覆盖catalog路由。新adapter仅覆盖catalog路径和snapshot版本，状态机 / 门碰撞 / 修理 / 占用恢复及既有整壳淡出逻辑继承字节未改的runtime。

独立UI代理已在冷包真实E与F5输入、完整1408×800截图中验证12/12，关闭原说明 / toast / 名称越界P2；本代理只核其所依赖的冻结源码与载荷范围，不重复GPU或旧全行为测试。UI改变限demo布局与新生产路由；母稿和生产合成没有因UI改动漂移。

## 作者94项证据与限制

固定包 validation_v004r1.json 实含94条检查、94条pass=true，与声明94/94相符；10个源码 / catalog / 功能表绑定、11张实际GPU / 边缘对照图的SHA全部匹配包内文件，报告与作者portable stage同SHA。作者外置回执的ZIP SHA、bytes、79 / 78数量也匹配。这里核实的是**作者已发生的94项验证记录、截图与固定载荷的静态绑定**；本代理没有独立重跑94项或任何GPU，不能把作者passed总数称为本轮独立行为数。

通过范围是本批完整主体及声明的门 / 设备功能、二值出口与现有整壳0.14淡出 / 深暗门洞。未验证或新增楼层 / 房间高度分区、完整室内、实际地面灯光。哈希与同源合成不证明造型受用户接受；深浅边缘、柱檐连续性和整栋比例仍以根TA实际图像审核为准。
