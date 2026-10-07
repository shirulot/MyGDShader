# UI v005 独立增量技术审查

结论：**v004 真实手柄 P2 已关闭，v005 输入/事务/生命周期通过；滑条可见焦点提示新增 P2 需修订。** 不以输入功能通过替代焦点可读性验收。

固定 ZIP SHA256 `7792955f87603d5efbfda61dcf999b9b761370552463dc69d8cc8167f7d31a7e`，16709201 bytes，231 manifest。UI 源 SHA `6ef311309c5ae7559179174dbb3cfea933e75f6f83b44bf1557e7051a6bc68a8`。本次全部写入此 technical 与冷副本目录，主工程/M0/生产文件未改、用户已有编辑器未操作。

## 固定包增量与继承

`incremental-integrity.json`：357 项全部 PASS；对 v004 固定 ZIP 做精确字节差异，仅一个既有 `.gd` 改变：`interaction_ui.gd`。其增量是局部 A/B/Start/滑条 D-pad 路由及 HUD 入口留边跟随生命条；其余既有核心源码、场景与 60 个 PNG 全部相同。新增五文件为导航探针/uid/结果/日志。可继承已独立通过的 v004 318 项原运行、44 项 TA、70 布局与 14 GPU 证据的无变化范围；v004 的手柄失败证据保留。

## 实际增量验证

- 冷导入 exit 0、所有本次 stderr 空。
- 生产方导航补充 12 项独立复跑 PASS。
- 自建真实 `InputEventJoypadButton` 探针 25 项 PASS：A 打开聚焦入口，B 返回并恢复焦点，Start 打开暂停；D-pad 只移动一次、左右只改一档；设置 B 取消不应用；重开默认取消与实际提交；按下/释放不双提交；结果 B 不穿回旧局；外部夺焦时确认前恢复；跨 960×540 视口；局部 X/Y 自定义改键。
- 全部全局 InputMap 动作/事件快照在 ready、完整操作、释放后相同，确认未污染宿主映射。
- 原 44 项 TA 探针 **原样**复跑 PASS，哈希 `21f5e6b1459b9336eb7ec94dba3f628e80518246a0ce6ab495f381ac9c457205`；保留真实存储失败、紧凑窗口取消、轮滚、暂停/结果及重挂复验。
- 新增 5 张实际 GPU 图：滑条 focused/unfocused 对照、320×480 HUD、720×720 留边60 HUD与设置。320×480 生命/详情/菜单入口 x 均32，留边60的720画布均60，确认新增对齐修正生效。旧 5 个保护文件再次核验未变。

## P2：设置滑条没有可见焦点区别

位置：固定 `scripts/ember/ui_edge_v004/interaction_ui.gd:367` 的 `_style_slider`。376 行高亮填充共用常态 fill，378 行高亮 thumb 共用常态 `bracket_corner_16`；未建立明确焦点视觉层。

重现：在720×720专项宿主中打开设置，鼠标远离滑条，先 `SafeMargin.grab_focus()` 截图，再令关闭按钮获得焦点，保持相同值及布局截图。实际 `has_focus=true/false` 已登记；滑条全矩形 `[84,232,552,44]` 内 **0 像素变化**。焦点状态真实存在、方向编辑25项通过，因此不是输入失效，也不是截图忘记聚焦。目视 focused 图没有提示当前键盘/手柄选择在滑条上，无法从画面辨认输入目标。

修法：只给滑条补明确 focused 视觉（当前青色/角标体系的独立焦点层，或确定会随 focus 显示的样式/图标），保持现有布局、填充和输入路由。提交新的固定包及 focused/unfocused 实际 GPU 对照；最小复验是焦点显示、A/B/D-pad与320取消，无需重做既有资源。

直接证据 `gpu-focus-layout/settings_slider_focused_720.png`、`settings_slider_unfocused_720.png` 与 `focus-layout-gpu.json`（含真实焦点布尔、矩形、变化像素、源 SHA、截图 SHA、GPU）。捕获代码 `cold-project/tools/ta_ui_v005_focus_capture.gd`。

## 其它证据与范围

`technical-summary.json` 为汇总；`cold-project/ta-ui-probe/gamepad-v005-results.json` 与 `cold-project/tools/ta_ui_v005_gamepad_probe.gd` 为25项独立手柄结果/源；`cold-project/ta-ui-probe/independent-results.json` 为44项原探针本版本结果。`interaction-ui-v004-to-v005.diff` 保存精确核心增量。

范围沿用声明 UI 和专项宿主；没有扩大为完整游戏/M0，Windows字体与旧安全省略仍按原已声明限制记录。最终美术通过由主审/视觉审查给出；本次具体验证不因缺少未定义背包等系统而制造缺陷。
