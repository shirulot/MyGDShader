# 边缘标记 · 最终窗口与交互 v006

当前正式结论为 **TA PASS**，见 [v006 回执](../ta-review-v001/ui-v006-independent/review-ui-v006.md) 和 [ta-acceptance-v006.json](ta-acceptance-v006.json)。统一资源入口在 [assets/ember/ui_final](../../../assets/ember/ui_final/README.md)，继续设计请遵循 [UI 风格与制作规范](../../../docs/shader-learning/ember-ui-style-guide.md)。

## 运行示例

Godot 打开 `res://assets/ember/ui_final/demo.tscn`，按 F6。该入口复用既有组件实现，已包含 v006 返修；资源现统一在 assets/ember/ui_final。

- 生命在左上横向排列，失去生命保留空槽；更多生命以准确数字补充。
- 点击「设备详情」或世界中的「查看设备」打开详情，详情可固定到右侧终端。
- 菜单包含继续、设置、帮助、重开和返回起始页；设置的保存／取消实际生效。
- 重开与返回有默认取消的确认页；起始页及成功／失败结算可操作；Toast 不抢焦点。
- 鼠标、Tab／Shift+Tab、方向键、Enter、Esc 与手柄 A／B／Start 均有验证。按钮及滑条有独立焦点层，小屏焦点自动滚入正文。

示例进入时停在 145/380、2/3 生命、01:18，便于视觉比对。菜单重开或起始页开始后运行演示计时／采集。验证快捷键：1–4 切站点状态，H 切生命，G 切能量，T 触发时间结束，Space 切演示采集，只在无模态窗口时响应。

## 接入

可复用总入口：`res://assets/ember/ui_final/ui.tscn`，建议放入 CanvasLayer，使用屏幕尺寸。

| 接口 | 用途 |
| --- | --- |
| `set_game_state(Dictionary)` | 传入 life、max_life、energy、energy_goal、seconds、station_state、collecting、station_name；支持入树前缓存 |
| `set_station_portrait(Texture2D)` | 设置真实设备肖像，断开时清空 |
| `set_station_screen_rect(Rect2)` | 设置当前设备投影位置；完成 ready 后调用 |
| `show_result(bool)` | 由宿主给出成功／失败结果 |
| `blocking_changed` / `is_blocking()` | 宿主管理移动、计时和采集阻断 |
| `restart_requested` / `session_requested` / `title_requested` | 宿主执行重开、开始和返回逻辑 |
| `preferences_changed` | 接收已保存并应用的偏好 |

UI 不直接改写 Game 或整个 SceneTree 的暂停状态。侧终端是非模态信息显示，模态窗口才请求玩法阻断。采集遵循站定自动采集，移动中断，只有安全／预警状态可采；145/380 表示全局累计与目标。

设置默认保存到 `user://ember_edge_ui_v004.cfg`；保存失败保留窗口并提示，关闭或取消放弃草稿。当前字体工厂依赖 Windows 系统中文字体，其他平台需要配置并验证 CJK 字体。

## 交付与证据

[previews/](../../../assets/ember/ui_final/previews/) 保留 16 张最终引擎图，包含 [总览](../../../assets/ember/ui_final/previews/overview.png)、所有声明的页面和小屏／焦点对照。[v006 完整包](../deliveries/ui_edge_interactions_v006_2026-10-06.zip) 可解压为独立工程运行。

有效工具为 `tools/validate_ui_interactions_v004.gd`、`tools/probe_ui_interaction_navigation_v004.gd`、`tools/capture_ui_interactions_v004.gd`；基础组件验证与皮肤生成工具继续保留。

通过范围是本套 UI 及潮汐港专项交互宿主，M0 主游戏接入尚不在本次验收范围。背包、商店和未定义的音频／画质设置仍是后续扩展。旧冷工程和过期展示已按用户要求整理；最终 ZIP 与正式审查记录仍保留，清理详情见 [整理记录](../ui-final/cleanup-report.json)。
