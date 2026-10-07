# UI v002 独立 TA 审查

结论：**有条件通过**。A「边缘标记」的皮肤、分层和当前现场 HUD / 采能站终端的视觉方向通过；发现一处 P2 生命周期缺陷，正式冻结组件与后续接入前必须修订并复验。未发现 P1 问题。本结论不代表主玩法已接入新 HUD，也不代表通用设置 / 暂停 / 列表控件已完成。

## P2：离树 HUD 外部关闭中断，显示与开闭状态不一致

- 文件：`scripts/ember/ui_edge_v001/edge_hud.gd:115`，涉及 `set_drawer_open()` 的 107–120 行。
- 触发条件：HUD 已完成 `_ready()`，打开抽屉；外部调用 `remove_child(hud)` 暂存组件；离树期间同步调用 `hud.set_drawer_open(false)`；再把 HUD 加回原 CanvasLayer。
- 实测错误：`Cannot call method 'gui_get_focus_owner' on a null value.`，定位 `edge_hud.gd:115`。离树后 `get_viewport()` 返回 null，方法在执行 `_drawer.hide()` 前中断。
- 结果：`is_drawer_open()` 为 false，但 `get_drawer().visible` 仍为 true；重新挂回树后仍保持该不一致。HUD 尚按打开的旧布局摆放，终端继续显示，调用方已认为关闭。
- 影响：缓存 UI、切换容器 / 场景或离树期间同步外部状态时出现脚本报错和残留终端。直接调用独立 Drawer 的 `close()` 已有树状态保护，但 HUD 的公开状态同步接口遗漏同类处理。
- 建议修法：只在 `is_inside_tree()` 时获取 viewport 并释放内部焦点；无论是否入树，都继续 hide、设 `MOUSE_FILTER_IGNORE` 和更新布局。保持 `set_drawer_open(false)` 不发出 `drawer_closed` 的既有直接同步契约。
- 修后复验：重复本探针离树 / 再入树两项；补测离树期间连续关闭、打开再关闭，确认 stderr 为空，返回状态、真实可见性及重新入树后的布局一致。

## 独立证据

所有审查代码和运行记录均位于本目录。运行发生在 ZIP 展开的 `cold-project/` 副本，生产源码、主工程配置、M0 和用户现有编辑器没有被修改或操作。

1. `integrity-report.json`：ZIP SHA256 为 `f2c47d6b377df9fbb3f64f29a9bf3a97e0ddff27197ee4ea36ff666b7bd2c586`，与报送值一致。105 项 manifest 分别核验当前工程和 ZIP 内容；另核验 11 份脚本、5 份受保护文件、12 张 GPU 截图及原始 A 稿，共 239 项，失败 0。
2. `cold-import.stdout.log` / `cold-import.stderr.log`：独立最小工程冷导入退出 0，stderr 为空。
3. `reuse-rerun.stdout.log` / `reuse-rerun.stderr.log`：交付包中原有复用审计在独立目录重新执行，53 项通过，退出 0，stderr 为空。没有机械重复全部 366 项。
4. `cold-project/tools/ta_independent_probe.gd`：通过 `SubViewport.push_input()` 投递真实鼠标按下 / 释放与 Enter 按下 / 释放，验证真实事件分发，未直接模拟 `pressed.emit()`。生命 / 能量 HUD 穿透、抽屉拦截、返回点击关闭一次、收起后世界点击恢复、键盘确认关闭，共 6 项全部通过。
5. 同一探针追加离树 HUD 测试，2 项失败，均由上述唯一 P2 根因导致。JSON 见 `cold-project/ta-independent-probe.json`；Godot 退出 1，错误见 `ta-probe.stderr.log`。

原有报告本身也核对了真实计数：245 项常规、53 项复用、68 项控件合计 366；70 组布局报告的 `geometry_error_count=0`，26 条 findings 均为已明确记载的省略 / 最小尺寸限制。保留的 before 区与 before 报告没有被误当当前结果。

## 视觉结论和非阻塞边界

人工查看原始 A 稿及 8 张实际引擎预览：组件总览、标准 HUD、安全抽屉、爆发抽屉、960×540 抽屉、480×480、360×640 和 960×540 边界画面。方向保持米白正文、蓝灰面板、克制铜色及状态色，角件和读数层分离，生命空格的轮廓保留。当前版本可作为 A 稿工程实现继续保留。

填充层裁切与端夹处于兄弟节点，未发现将铜夹裁掉的结构问题；组件总览的 0 / 38 / 100% 也符合该结构。数据和状态以同一映射驱动，未知状态没有被伪装为安全。设备不可投影、释放及动态 portrait 的原有复验通过。

以下边界已在 README / usability-audit-v002.md 明示，不作为此次拒收理由：360px 窄画布开抽屉暂藏现场 HUD；480px 高隐藏肖像，540px 高肖像很小；长标题和巨大数值安全省略；系统中文字体回退；四种采能状态固定；通用 Theme 配置、滚动列表、Tooltip 和模态对话框尚缺；抽屉非模态，需要玩法层决定暂停和锁移动。后续主 HUD 迁移必须先处理旧 UI 的 GameTimer / countdown_tick 责任。

P2 修正后应生成新的不可覆盖交付版本、更新报告和 manifest，并由 TA 核对新的脚本哈希、该探针无错误及真实截图后再确认最终通过。
