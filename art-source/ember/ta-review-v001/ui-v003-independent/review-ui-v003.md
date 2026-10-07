# UI v003 独立 TA 复审

结论：**通过**。范围为 A「边缘标记」当前现场 HUD、单台采能站终端与已声明的组件复用边界。v002 的 P2 离树关闭缺陷关闭；本次未发现新的 P1 / P2 阻塞问题。完整游戏页面、全面 Theme、模态 / 暂停行为及跨 Viewport 设备映射仍按原声明处理。

## 固定版本

- 交付：`art-source/ember/deliveries/ui_edge_components_v003_2026-10-06.zip`。
- 独立计算 SHA256：`24def0986879b32e87c862561639140898b6fb21c6d4127f376fcb6cddd6dc49`，符合本次送审版本。
- 所有运行仅使用本目录 `cold-project/` 中的独立 ZIP 副本；未修改生产源码、主工程或 M0，也没有操作用户现有 Godot 编辑器。

## P2 关闭证据

原始 TA 探针 `ta_independent_probe.gd` 从 v002 独立审查目录原封不动复制，SHA256 为 `5eddd6cd8dad4ddfdcf6b66e36b28fa0cda52542f53cc42e2ead29ecca27b472`。没有使用生产方另写的 TA regression 复制版代替原始探针。

独立冷包运行 **8 项全通过**：6 项真实鼠标 / Enter 事件分发，以及原来失败的离树关闭、重新挂回两项。两个原失败节点均为 `drawer_visible=false`、`hud_open=false`。Godot 退出 0，stderr 为空。

证据：`cold-project/ta-independent-probe.json`、`ta-original8.stdout.log`、`ta-original8.stderr.log`。

## 新增修复范围的独立检查

先读取 HUD / Drawer / Progress / Button / Binding 的实际 v003 源码，再检查新增生命周期测试覆盖。生产新增的 112 项生命周期测试在本独立冷包重新运行，**112 项全通过**，退出 0，stderr 为空；运行时记录的代码哈希与固定包源码对应。

另外编写并运行独立的 `cold-project/tools/ta_v003_supplement.gd`，**34 项全通过**，退出 0，stderr 为空。重点验证：

- 已排队 `_enter_tree()` deferred 后同帧再次 remove，让回调真正执行时节点离树；关闭标志、真实可见性、最新数据及两个旧 / 新 Viewport 的焦点都正确。
- 720×720 转 960×540 后，用固定条件核对真实内部几何：288px 抽屉实际位置 `(672,0)`、尺寸 `(288,540)`；世界进度条 `(52,424,568,64)`；轨道 `(8,42,552,16)`；半满 FillClip `(10,46,274,8)`。填充纹理和固定铜夹的尺寸 / 层级一致。
- 抽屉 ContentClip `(288,540)`；返回按钮 `(28,476,232,52)`；Overlay `(232,52)`；四角位置 `(0,0)/(216,0)/(0,36)/(216,36)`，均与新画布匹配。终端内部进度也独立核对轨道与 FillClip。
- 连续四次同帧跨容器挂接 / 移除，制造多个待执行恢复回调；最终关闭和 25% 能量数据没有被旧回调覆盖，重新挂回后的轨道宽 840px、FillClip 宽 209px，未恢复旧焦点。
- 独立 Drawer / Progress / Button 脱离 HUD 再分别快速重挂、离树运行回调；实际内部布局、禁用焦点层和关闭状态均正确。
- 返回按钮 instance_id 保留，HUD 仍只有 5 个组件子节点，没有重复构建。

证据：`cold-project/ta-v003-supplement.json`、`ta-supplement.stdout.log`、`ta-supplement.stderr.log`；112 项证据为 `cold-project/art-source/ember/ui-edge-v001/lifecycle-validation-v003.json`、`lifecycle112.stdout.log`、`lifecycle112.stderr.log`。

独立冷导入、原始 8 项、生产 112 项重跑和 TA 34 项补验均成功；本次共 154 项运行检查，无失败。没有机械重跑其余 366 项。

## 完整性与视觉继承

根级 TA 的[完整性报告](../ui-v003-integrity/integrity-v003.json)已读取核对：305 项通过，124 项 manifest 在 ZIP / workspace 双侧核验，固定包哈希、11 份绑定源码、5 份受保护文件以及 39 项 v002 视觉内容比较均通过；变化精确限于申报的五份脚本。

18 张皮肤、8 个组件场景、12 张实际 GPU 截图和 A 稿参考均与 v002 哈希相同，因此继承 v002 已进行的视觉审查。此次通过绑定固定 v003 及上述用途；主玩法接入和此前声明的未完成组件不在本次验收范围。
