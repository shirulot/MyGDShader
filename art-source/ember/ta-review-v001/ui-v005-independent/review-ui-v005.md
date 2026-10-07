# UI v005：TA 正式回执

结论：**NEEDS_REVISION，仅剩本轮确认的滑条可见焦点 P2。** 新手柄路由、入口对齐与已审窗口外观保留；不要求重新生成皮肤或重排全部页面。

固定ZIP `art-source/ember/deliveries/ui_edge_interactions_v005_2026-10-06.zip`，SHA256 `7792955f87603d5efbfda61dcf999b9b761370552463dc69d8cc8167f7d31a7e`，16,709,201字节，231项manifest。内部路径继续沿用`ui-interactions-v004`与`ui_edge_v004`，不混同未冻结的后续工作区。

## P2：已获得焦点的设置滑条没有可见提示

独立GPU在同一数值、同一位置分别抓取聚焦/未聚焦状态；实际`has_focus`状态已确认切换，滑条区域`[84,232,552,44]`内变化像素为0。根审直接对照两图，也看不到滑条自身焦点提示；未聚焦截图只有关闭按钮的焦点角层变厚。键盘/手柄用户移动到滑条时无法辨认当前操作目标，属于具体可用性缺陷，输入本身仍有效。

固定包`scripts/ember/ui_edge_v004/interaction_ui.gd:367`的`_style_slider`将常态/高亮的grabber和填充分别设为同图/同色。最小修订为用现有角件、青色线或明确focus StyleBox增加独立焦点层，退焦恢复常态；不需要新皮肤。修后交同值聚焦/未聚焦两图，验证Tab/方向焦点、手柄左右调整和320×480滚动后提示仍可见。

证据：[聚焦截图](technical/gpu-focus-layout/settings_slider_focused_720.png)、[未聚焦截图](technical/gpu-focus-layout/settings_slider_unfocused_720.png)、[实际焦点和几何登记](technical/gpu-focus-layout/focus-layout-gpu.json)。已将具体返修通知UI chat，要求保留v005、另冻v006。

## 已通过范围

- v004已独立复现真实手柄A/B缺口；v005的局部路由关闭该问题。制作方12项导航复跑、独立25项真实Joypad事件和原44项TA行为探针，共81项运行检查通过，stderr为空。
- A/B/Start、方向单步、自定义X/Y确认/返回、按下/释放单次提交、确认默认取消、结果页拦截、跨视口重挂均通过。全局InputMap在创建前/后/释放后动作事件快照一致。
- 357项包与来源检查通过；60张既有PNG逐字节一致。旧源码中只有`interaction_ui.gd`发生本轮变化，未改处采用固定v004已完成的318项原检查、44项独立探针、70组布局和14张独立GPU证据，不假称v005重跑全部旧检查。
- 原14张提交截图与v004完全一致，18张皮肤与既有批准A稿/v003链一致。横排生命、设备详情、终端、暂停、设置、帮助、两种确认、起始/结算与提示的现有静态外观保留。
- 新增独立GPU确认320×480入口和生命左沿同为x32、720×720留边60时同为x60。标题/关闭固定、窄屏正文滚动可达，设置取消与帮助返回能随焦点滚入可见区域。

此审查仅覆盖声明UI组件与专项宿主。主玩法/M0集成、完整移动碰撞以及未声明商店/背包不在结论内。Windows系统中文字体是当前验证环境，其他系统字体未据此推定。

详细报告：[v005增量视觉](review-visual.md)、[v005技术](technical/review-technical.md)、[v004固定技术基线](../ui-v004-independent/technical/review-technical.md)。
