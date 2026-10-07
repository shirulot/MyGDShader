# UI v004 独立技术审查

固定 v004 结论：**鼠标/键盘及生命周期验证通过；真实手柄 A/B 需 P2 修订，生产方已提交 v005 待增量复审。** 不把 v005 工作区源码变更混入这份 v004 固定包证据。

ZIP SHA256 `cb61690d89244a2f8dc71d1905a0102399aa6ce063ff1c439d18a9727df8c194`，16705277 bytes；226 manifest 文件。只在本 technical 目录冷解包与生成证据，未改生产源码/主工程/M0，未操作用户编辑器。冷副本 `project.godot` 只添加独立用户存储目录，以免测试写入玩家设置。

## 已通过

- `package-integrity.json`：348 项全部 PASS，逐一核验 ZIP manifest、工作区提交源码与源哈希、旧 5 个保护文件；完成后旧保护仍相同。收到 v005 后工作区 `interaction_ui.gd` 变化已明确另记，冷副本仍绑定 v004。
- 独立冷导入 exit 0、stderr 空。
- 选择复跑原交互 153、生命周期 112、复用 53 项，共 318 项 PASS；70 个布局样本、0 几何错误。旧组件的 26 项安全省略/最小宽度记录属已声明的非阻塞边界。
- 新独立探针 44 项全部 PASS：实际 Enter/Tab/Shift+Tab 与鼠标输入、全焦点环、遮罩/提示鼠标穿透、两种确认默认取消/焦点恢复/单次提交、设置取消/真实保存失败/成功落盘/新实例读取、320×480 帮助滚轮与设置底部取消焦点滚动、快速离树重挂与跨 960×540 重挂、真实宿主冻结恢复及结束局保护。
- 14 张真实 GPU 图独立重截，与固定交付截图 SHA 全部相同。已目视 `overview.png` 与 `compact_settings_320x480.png`，未见技术布局阻塞。

## P2：真实手柄确认/返回未接入

在固定 v004 冷副本发送 `InputEventJoypadButton` 按下及释放：聚焦 HUD 设备入口后 A 不打开详情；先打开暂停后 B 不关闭；Start 也不打开暂停。当前 `InputMap.ui_accept` 仅 Enter/Kp Enter/Space，`ui_cancel` 仅 Escape；方向动作包含手柄事件，因此键盘和方向验证不能证明 A/B 已可用。

代码位置为固定 v004 `scripts/ember/ui_edge_v004/interaction_ui.gd` 的 `_input` 和 `_unhandled_key_input`：仅依赖内置键盘 ui_accept/ui_cancel，没有局部 A/B 路由。影响 README 声明的“手柄 A 确认、B 返回”；鼠标、键盘与已经通过的事务逻辑不受影响。修法是局部处理手柄事件并按事件消费，保持全局 InputMap 不变，确保按下/释放只提交一次。生产方已在 v005 添加此路由，将按固定 v005 复核。

最小失败证据：`cold-project/ta-ui-probe/gamepad-v004-repro.json`，复現代码 `cold-project/tools/ta_v004_gamepad_repro.gd`；日志 `gamepad-repro.stdout.log`，stderr 空。原 44 项 probe 与报告仍独立保留。

## 文件与范围

结果汇总 `technical-summary.json`；独立行为报告 `cold-project/ta-ui-probe/independent-results.json`，探针 `cold-project/tools/ta_ui_v004_probe.gd`；原测试与 GPU 结果位于 cold-project 对应 art-source 路径，运行日志在 technical 根目录。

只验声明 UI 与专项宿主，包括横向生命、详情/终端、暂停/设置/帮助、重开/返回确认、起始/结果/提示；不扩大为完整游戏或 M0 验收。Windows CJK 系统字体与旧安全省略是已声明限制；没有以未定义背包/商店等系统作为缺陷。美术整体结论交主审。
