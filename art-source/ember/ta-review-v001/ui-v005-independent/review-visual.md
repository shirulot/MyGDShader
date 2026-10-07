# UI v005 独立增量静态审查

初审快照：2026-10-06 17:53；新增GPU复核：18:45（均UTC+08:00）。审查者：TA 子审查代理 `style_specs`。本报告仅审v004→v005差异，保留[原v004报告](../ui-v004-independent/review-visual.md)，没有修改生产文件。

**结论：`NEEDS_REVISION`，具体P2为滑条有真实焦点却没有可见焦点提示。** 新GPU图已确认入口与生命左沿对齐，入口修改与旧静态成果通过。滑条聚焦／未聚焦的轨道、填充、thumb和外框完全相同，键盘／手柄玩家无法从该控件判断焦点位置。手柄行为由技术代理独立复核；本结论不要求重做已批准窗口或皮肤。

固定ZIP：`art-source/ember/deliveries/ui_edge_interactions_v005_2026-10-06.zip`，实测 SHA256 `7792955f87603d5efbfda61dcf999b9b761370552463dc69d8cc8167f7d31a7e`。包内仍沿用 `art-source/ember/ui-interactions-v004/`、`scripts/ember/ui_edge_v004/` 与原scene路径，不存在单独ui-interactions-v005来源目录。

## 直接比较结果

逐件读取v004、v005固定ZIP成员计算SHA：

- 14张提交GPU截图全部字节相同，含320×480设置、overview、HUD与全部窗口；截图SHA继承v004报告末表。
- 18张 `assets/ember/ui_edge_v001/` 皮肤PNG全部字节相同；v003→v004已核对同样18件一致，A稿皮肤没有回退。
- `edge_hud.gd`、`life_indicator.gd`、`bracket_button.gd`、`edge_ui_style.gd`、`modal_window.gd`、`toast.gd`未改。因此生命横排是v004既有成果，v005没有再改生命纹理／排布、窗口外观、按钮焦点皮肤或滑条样式。
- 相关变更在 `scripts/ember/ui_edge_v004/interaction_ui.gd`，v004 SHA `4f6d2a9393bf9fe6d86185bfc04a06ef1abffcec103df32cb70980862fac63fc`；v005 SHA `6ef311309c5ae7559179174dbb3cfea933e75f6f83b44bf1557e7051a6bc68a8`。

## 变化内容及静态影响

| 变化 | 独立评价 | 当前证据边界 |
| --- | --- | --- |
| 设备详情／菜单入口左沿 | `_layout()`由 `min(preferences.safe_margin,size.x*0.08)` 改为读取 `life.position.x`；生命本身按HUD实际可用宽高10%上限取整。入口与生命使用同一落点，消除窄宽／大留边时两个不同上限产生的横向错位。 | 新GPU图确认320×480时生命／详情／菜单均x32，720×720、60px留边时均x60；三个左沿实际对齐，文字及生命槽未被边界裁掉。入口修订通过。 |
| 手柄确认／返回／Start及滑条方向 | 新增组件局部按钮映射和可配置confirm/back。没有更换按钮皮肤或改变文字层级；现有帮助页A确认／B返回的静态提示仍一致。 | 行为是否只触发一次、焦点／关闭／宿主是否正确由技术代理复跑，不凭源码授予行为通过。 |
| 横排生命／窗口／遮罩 | 相关源与截图都未变，可继承v004静态判断。 | 不重复提出重新生成皮肤或缩字。 |

## v004条件的继承与关闭范围

根代理已转达技术代理对v004真实滚轮及焦点自动滚到320×480帮助Back／设置Cancel的PASS。该行为证据关闭v004首屏取消被滚动裁切的可达性疑问；本报告未亲自执行这些输入。v005模态滚动／样式代码未变，可结合v005技术复验继承，不把允许滚动当布局失败。

已直接查看技术代理生成的五张新图：滑条focused／unfocused、320×480 HUD、720×720大留边HUD、60px设置聚焦图。来源清单 `technical/gpu-focus-layout/focus-layout-gpu.json` 记录Interaction UI SHA `6ef311309c5ae7559179174dbb3cfea933e75f6f83b44bf1557e7051a6bc68a8`，与本固定v005包一致；这些是固定包冷项目的追加审查证据，不是包内旧截图。

### P2：滑条焦点不可见，需局部修订

focused图里滑条虽已获得真实焦点，视觉仍只有常态米白thumb角件与青色填充；unfocused图的关闭按钮出现焦点角层，但滑条自身没有任何区别。大留边60px的设置图同样没有滑条独立焦点标识。真实focus=true／false由技术记录确认，本子审查另读PNG独立逐像素比较ROI `[84,232,552,44]`，差异确为0；同时直接目视确认轨道／thumb／外框没有聚焦强调。这已从“证据不足”收束为明确的焦点显示缺陷。

最小修订：在滑条持有焦点时给整个44px控件区或thumb增加独立可见的青色线／角件／有厚度外框，失焦清除；保留既有轨道、填充、值与输入行为。不能只保留焦点状态变量或零视觉差异的StyleBox。复审提交同值同位置focus／unfocus GPU对照并验证键盘／手柄导航可辨，不要求重新生成18件皮肤。本次v005据此退回该局部项，不等待v006才能形成结论。

## 追加GPU图SHA256

下表文件均位于本报告目录的 `technical/gpu-focus-layout/`，文件哈希已独立核对清单。

| 文件 | SHA256 |
| --- | --- |
| settings_slider_focused_720.png | `fee73c3d1d36dc2836cbb6bf3b27c4cab21fb6fb23b1c26395f682c7c0116f92` |
| settings_slider_unfocused_720.png | `0a7a5e510dc6532f3e4b7178daaf5572770ee8ffcce74157c19331a857b6226d` |
| hud_320x480_margin36.png | `557120fe5449640478930898baa1a61bbd8f4c582ecbb7b31a65d38635531426` |
| hud_720x720_margin60.png | `0ce8c906ea7f896df13c9480af7d82d66fc00416136b0f8d75a4cb1fb9db72e9` |
| settings_margin60_focused_720.png | `f98a17496f2e138d6e3f5635cc532b9778f239f68da88da9214f530a1c18c091` |
