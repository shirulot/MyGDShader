# UI v006 独立增量技术复审

结论：**本次技术增量通过。v005 滑条无可见 focus 的 P2 已关闭；720→960 重挂→320 的 Cancel 聚焦后未滚入问题已关闭。** 最终视觉结论由主审另给。

## 固定包及增量范围

独立从 `art-source/ember/deliveries/ui_edge_interactions_v006_2026-10-06.zip` 解压到本目录 `cold-project/`，没有使用活动生产目录替代固定包。SHA256 `af61549eef1605a98301f822c2018d68bed4687118a2ed8c499073e71e758504`，17022123 bytes，224 ZIP 文件条目、223 manifest 载荷（清单自身除外）；CRC、所有载荷 SHA/大小及独立解压文件 SHA 全通过，无重复路径。

与固定 v005 ZIP 做精确字节差异：只有 `interaction_ui.gd`、`modal_window.gd` 两个既有组件脚本变化，另有捕获/导航两工具变化。45 张 `assets/` 实际资源 PNG 全部不变；变化的两张 PNG 是 settings/compact_settings 预览截图，另新增两张 focus 对照。精确差异保存在 `v005-to-v006.diff`，完整包证据为 `integrity.json`。无变化组件继承前版独立验收，本次不复跑无关美术、布局或全部 153 项历史检查。

UI 源 SHA `bb3b3e2a240137fe3995464089c3ebf6966f2a2caafec76d0f4735b498949016`；modal 源 SHA `0b2788cc6504c1c2d96998ca7e57e75baa3afd8c21d7dca2204716ef459c21bb`。所有修改和运行均只发生于本审查目录的冷副本，没有修改宿主项目、M0 或生产文件，也未操作用户已有编辑器。

## 两项修复的实际独立证据

| 验证 | 结果 |
|---|---|
| 滑条实际焦点开/关 | 相同值36、相同720×720布局；实际 has_focus true/false 已登记；ROI `[84,232,552,44]` 改变112像素。前版同ROI为0像素。青色四角提示实际出现在 GPU 图中 |
| FocusOverlay 生命周期 | 焦点进入可见、离开隐藏、再次进入恢复；mouse_filter=IGNORE、focus_mode=NONE，避免角层接管输入；小屏 Tab 离开也隐藏 |
| 重挂后当前焦点 | 同一组件720→960新Viewport，当前视口拥有窗口焦点，旧Viewport焦点为空 |
| 小屏真实 Shift+Tab | 重挂后320×480，关闭按钮焦点，一次实际 `InputEventKey` Shift+Tab 按下/释放：Cancel 获焦，scroll从0变47；Cancel `[48,380,216,52]` 完整位于Scroll `[48,112,224,320]` 内 |
| 反向导航连续性 | 继续真实Shift+Tab依次Save→Markers→SafeMargin，各目标均滚入；滑条恢复焦点角层 |
| 输入和事务 | 实际KEY_RIGHT只改一档；Tab离开隐藏角层；小屏Cancel实际Enter取消后回到pause且偏好仍36；延迟滚动排队后立即close_all安全 |

自动滚入验证没有手动调用 `ensure_control_visible` 或 `cycle_focus`，也没有先把 Cancel 坐标校正后截图。新 `_reveal_focus` 从当前Viewport读取当前焦点，检查壳在树内/可见且焦点属于scroll，再延迟滚入；因此不依赖旧Viewport的焦点信号连接。不是逐帧重设滚动位置。

## 冷副本运行与输入回归

冷导入 exit0。Godot `4.7.2-stable (steam)`，Compatibility，NVIDIA GeForce RTX 4070 Laptop GPU。独立新增 `ta_ui_v006_focus_scroll_probe.gd` **16项全部PASS**，保存4张实际GPU截图；原样复制 v005 独立真实 Joypad 探针（字节相同）**25项全部PASS**。A/B/Start、D-pad单步、不双提交、设置取消、确认默认取消、结果不穿回旧局、跨Viewport及X/Y局部改键均未回退；ready/完整输入/释放后的全局InputMap快照仍相同。

本次独立运行总计41项。生产声明的15+153项保留为生产方报告，不计入独立重跑数量。最终 cold-import、gamepad、focus-scroll stderr 均为0 bytes。

## 证据与复验

- 汇总：`technical-summary.json`。
- 新增探针/16项结果：`cold-project/tools/ta_ui_v006_focus_scroll_probe.gd`、`gpu-focus-scroll/focus-scroll-results.json`。
- 原25项手柄探针/本版本结果：`cold-project/tools/ta_ui_v005_gamepad_probe.gd`、`cold-project/ta-ui-probe/gamepad-v005-results.json`。
- 原生GPU截图：`gpu-focus-scroll/settings_slider_focused_720.png`、`settings_slider_unfocused_720.png`、`compact_cancel_after_real_shift_tab_320.png`、`compact_slider_after_real_shift_tab_320.png`。结果JSON含实图SHA、真实焦点状态、ROI和滚动位置。

复验使用实际 Godot 可执行文件对本目录冷副本运行上述两个 `--script res://tools/...`；焦点/滚动探针需GPU并传 `-- --output=<绝对输出目录>`，手柄探针可headless。不要在生产目录运行审查探针。

范围仍是声明UI与专项宿主，没有扩大到完整游戏、M0或未定义系统；焦点提示的视觉力度等最终美术判断由主审完成。此次没有发现新增技术阻断。
