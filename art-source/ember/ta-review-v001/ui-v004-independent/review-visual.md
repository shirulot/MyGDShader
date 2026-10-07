# UI v004 独立静态视觉审查

快照：2026-10-06 17:47（UTC+08:00）。审查者：TA 子审查代理 `style_specs`。仅查看固定GPU截图和相关源码；未修改生产资源，未运行交互验收。

**结论：静态窗口外观有条件通过。** 已展示的HUD、详情和各窗口没有需要重新生成皮肤的美术阻塞项；生命已正确横排。条件是合并技术代理对窄屏滚动可达性的复核，并补证滑条的键盘／手柄焦点是否可辨。后者当前只有单态截图，本报告不据此断言失效，也不声称所有焦点状态已经视觉通过。

## 固定版本与直接证据

ZIP：`art-source/ember/deliveries/ui_edge_interactions_v004_2026-10-06.zip`，实测 SHA256 `cb61690d89244a2f8dc71d1905a0102399aa6ce063ff1c439d18a9727df8c194`。

直接查看 `art-source/ember/ui-interactions-v004/previews/` 全部14张GPU图：overview、hud、details、pause、settings、help、confirm_restart、confirm_title、title、success、failure、terminal、toast和compact_settings_320x480。各截图均直接读取ZIP成员计算SHA，与工作区一致，见末表。`validation-summary.json` 的PASS只用于定位范围，639项／153项等制作方测试没有替代本次看图。

风格对照为 `art-source/ember/ui-edge-v001/selected_reference.png` 的A稿，以及 `art-source/ember/ui-approved-showcase-v003/approved_hud.png`／approved_terminal.png的已批准实际Godot画面。另读取 `usability-audit-v002.md`、本轮README、`modal_window.gd`、`bracket_button.gd`及滑条样式部分，区分允许滚动与真实溢出。

应用本地 `game-ui-design` 的可读性、焦点、遮罩及小视口审查方法，并查看其validations／sharp_edges参考；项目已选风格和当前PC/Godot范围优先，不据技能的主机／触屏通用默认值扩增产品需求。

## 分项判断

| 项目／截图 | 独立静态判断 | 处理 |
| --- | --- | --- |
| 横排生命：hud／overview | 两枚青色实体和一枚空槽从左向右排布，失去生命后的空槽保留；与标题、入口按钮没有相撞。时间在另一侧，底部目标与百分比可读。 | 通过本例2/3生命；大上限折叠另属技术边界 |
| 设备详情：details | 标题、关闭、设备肖像、名称、状态、目标与百分比层级清楚；说明两行正常换行，两个行动按钮有充足间距。窗口暗底隔离地图细节，肖像没有烘焙进面板。 | 静态通过 |
| 暂停／起始页 | 页面标题、说明和行动列表分组清楚；米白角标与大留白延续A稿，按钮没有采用另一套明亮圆角界面。 | 静态通过 |
| 设置：settings | 标签、36px数值、滑条、显示开关、保存说明与保存／取消按钮排列清楚。青色填充和米白控制点可辨；未见文本压在轨道上。 | 外观通过；焦点差异见下节 |
| 操作说明：help | 三段编号与青／黄铜小标题形成明确分组；米白正文在暗底可读，正常换行，没有页面尾部文字覆在返回按钮上。 | 静态通过，不验证按键实际行为 |
| 两种确认 | “重新开始／返回起始页”对象明确，黄铜清空提示与当前进度可读；保留当前巡检和确认行动分开。 | 静态通过；默认取消与返回恢复由技术代理验证 |
| 成功／失败 | 标题和青色／红色结果文字同时表达结果；能量、生命、剩余时间与重试／返回清楚，结果没有只靠颜色传达。 | 静态通过；失败例能量已满但生命0/3是宿主传入组合，不据单图判逻辑错误 |
| 侧终端：terminal | 肖像、145/380、进度、四种形状＋文字状态、停下采集说明及返回保持v003布局语言；选中安全行的青色和侧竖条可辨。 | 静态通过 |
| 非阻断提示：toast | 暗背板与米白提示字可读；本截图没有盖住生命、时间、目标读数和底条。 | 外观通过；不抢焦点／不拦鼠标／超时另验 |
| 遮罩层级 | 各模态页中地图、现场HUD和设备入口明显变暗，前景标题、正文及行动按钮保持亮度；不会把背景HUD误读成同层主操作区。 | 静态通过；输入穿透另验 |

## A稿／v003皮肤保持

蓝灰暗面、米白角件、青色主信息和克制黄铜保持。窗体扩展采用同一皮肤和布局职责，没有重新做一整套材质，也没有把文字、数值或动态填充烘焙进PNG。

独立读取v003与v004两份固定ZIP中的 `assets/ember/ui_edge_v001/`，18张皮肤PNG逐件SHA完全一致，包含panel、text_backplate、button_focus、bracket_corner、life_fill／outline、进度及四状态图。图像一致性与实际窗口看图共同支持“保留已批准皮肤”；不要求横排生命位置继续照旧垂直布局。

## 条件与边界

### 320×480设置：允许滚动，不判为整页溢出

`compact_settings_320x480.png` 中窗体约从(24,24)到(296,456)，标题／关闭独立保留，滑条、标签和保存说明在窄宽度下换行正常；右侧可见滚动条。保存按钮首屏可见，取消按钮在滚动正文下方被裁切，说明也明确关闭／返回将放弃本次调整。

这是本轮允许的长内容滚动，不等于按钮永久画出视口。源码确认正文为ScrollContainer且 `follow_focus=true`，但源码不能证明实际键盘／手柄聚焦后已把取消完整滚入视口。请技术复核保留“320×480聚焦取消后实际可见”的证据；若无法滚入，再修正文高度／跟随焦点。当前不要求为一张首屏截图强制缩小字体或重排全部页面。

此截图没有充分展示窄屏HUD、其它小屏窗口或所有任意尺寸；制作方70样本的布局零错误不能外推为本子审查已逐图看过全部尺寸。

### 焦点可见性：按钮可辨，滑条需补对照

pause、两种confirm、title及结果页的首个行动按钮可见比普通角件更厚的focus角层；状态行也有独立青色选中条。常规按钮焦点与页面层级在当前静态图中可辨。

设置滑条当前只展示一张状态图；`_style_slider()` 将grabber／grabber_highlight设置为同一角件，轨道填充highlight也同色，截图没有提供聚焦与未聚焦并排。这里记录**证据不足，不直接断言不存在焦点**。最小补证是同一值、同一注册位置的滑条focused／unfocused GPU对照；如聚焦确实没有视觉差异，使用现有青色线／角件增加独立焦点指示即可，无需新皮肤生成。

技术代理负责冷导入、真实输入、焦点切换／恢复、遮罩输入层、宿主暂停与结果数据。本报告只对所列静态外观负责，不能授予这些行为通过。

## 截图SHA256

下表相对 `art-source/ember/ui-interactions-v004/previews/`。

| 文件 | SHA256 |
| --- | --- |
| overview.png | `e9d702a604394707d3aacf20cae328a5129815e122a6d563ce6c5b87dae90d24` |
| hud.png | `4de81241b6acd0c2983206ee589ac9ef4500f464b6af6781028b92093598b8c6` |
| details.png | `7f30b880e5790d5d109418733668f3023bbe68d1025a530f0589be922124af24` |
| pause.png | `a66629495f9c47c42bdc2b0535ff5554124e9025dde5d797b5d4beb50579b26b` |
| settings.png | `fee73c3d1d36dc2836cbb6bf3b27c4cab21fb6fb23b1c26395f682c7c0116f92` |
| help.png | `d8ad2ac2d3d23a4116ae431b338cfaef264f6e2fb1c647dfebcd71f2bc4edf9c` |
| confirm_restart.png | `6edb688462717506b2b9b70ba7bae5a0ebd56bba685fc7cb2d0d23762c820286` |
| confirm_title.png | `8f06c73c170d8af9e082929ce8ef01b93a5acf4d32fdb18f27fd2a4fae0778b0` |
| title.png | `b3b86512bca136a5cf2d5d8c642a5144afaeabfedcf6ab32bd96ca59606d2758` |
| success.png | `cd42f558b9fdce1c5e399670c827b688051e1bbf66e60ee8ea42ec95b33f68d8` |
| failure.png | `f6b04923b657a902c0d0702be08dbc58135b7bae3801f30e0cff217b2b564c2e` |
| terminal.png | `7e63b548f2a8d9219ddb278559dccedfe806cc0cb3eaf0ec6e5f5739a29a4fb2` |
| toast.png | `6820bd69df3b40d6e4205325f0a02667e7892c3e97c6dc602fae02df093fe03c` |
| compact_settings_320x480.png | `9a7fce187ccff907456f3d6910a6a08b8792835d6d37756e60f15b4c0561a315` |
