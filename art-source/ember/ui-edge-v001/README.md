# 边缘标记 · 当前共用基础组件

此目录保存 v006 仍在使用的皮肤来源、组件拆分合同和基础验证。目录名 v001 是资源路径，不表示废弃。

最终入口：[UI 资源索引](../ui-final/README.md)。设计标准：[UI 风格与制作规范](../../../docs/shader-learning/ember-ui-style-guide.md)。完整交互示例：`res://scenes/ember/ui_edge_interactive_v004.tscn`，Godot 中 F6 运行。

## 当前组件

| 组件 | 保留的拆分方式 |
| --- | --- |
| 横向生命 | 24×32 空槽与填充分离；横向步进 32；空间不足或超过格数时用准确数字补充 |
| 时间牌 | 暗底、角件、动态 mm:ss 分离 |
| 能量条 | 轨道、填充裁切、铜端夹、数值分别控制；端夹始终在裁切外 |
| 设备标记 | 独立形状、文字、投影和显示判断，不能越出可见世界区域 |
| 四状态行 | 同源状态定义；图形与文字一起表达安全／预警／爆发／冷却 |
| 侧终端 | 不透明背板、独立肖像、框、数据、只读状态行和返回按钮 |
| 按钮 | 底层状态、文字、角括号和焦点覆盖层分离；装饰忽略输入 |

组件场景：`scenes/ember/ui_edge_v001/components/`。脚本：`scripts/ember/ui_edge_v001/`。18 张无文字 PNG 与尺寸合同：[inventory.json](../../../assets/ember/ui_final/skins/inventory.json)。皮肤制作源：`tools/build_ui_edge_skin_v001.gd`。

`edge_hud.tscn` 可以独立放入 CanvasLayer 使用，不需要示例地图。它只接收数据，UI 与世界瓦片缩放分别处理。可选只读适配器为 `scripts/ember/ui_edge_binding_v001.gd`；需要宿主显式绑定数据源与选中设备。

## 保留依据

- [用户选择的 A 稿](selected_reference.png)：确认视觉风格；竖排生命已经被后续用户要求替换。
- [原子皮肤总览](previews/component_sheet.png)：静态组件素材索引，不代表当前完整页面排版。
- [基础复用审计 v002](usability-audit-v002.md)、[生命周期修复 v003](lifecycle-repair-v003.md)：历史问题与修复依据；完整窗口能力以 v006 入口和最新规范为准。
- `protected-source-baseline.json`：交付工具检查主工程与玩法文件的原始基线。

旧整屏预览和旧交付 ZIP 已由最终 v006 替代；删除明细保存在 `art-source/ember/ui-final/cleanup-report.json`。历史审计按原版本阅读，不视为当前能力清单。
