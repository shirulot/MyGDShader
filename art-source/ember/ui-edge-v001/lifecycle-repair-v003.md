# UI v003 生命周期返修与复审提交

本修订处理TA对v002提出的P2离树关闭缺陷，并补同类焦点/设备投影保护。A稿皮肤、字号、数据语义、正常布局和主玩法不变。工程回归结果与TA独立验收分开记录，v003在收到复审结论前为待审。

## 根因与最小修复

原复现：已构建HUD打开抽屉 → `remove_child(hud)`暂存 → 离树期间 `set_drawer_open(false)` → 调用空viewport的焦点查询报错，在真正hide前中断，内部开闭标志与显示不一致。

生产修改均为生命周期守卫和重入后的局部同步，涉及五份脚本：

- `scripts/ember/ui_edge_v001/edge_hud.gd`：焦点查询仅入树时执行；隐藏、IGNORE和布局更新始终执行。重入树后deferred读取最新开闭状态恢复布局，不重复_ready或创建组件，不给旧回调缓存的状态覆盖新数据。
- `scripts/ember/ui_edge_v001/station_drawer.gd`：open只对已入树、可见且未禁用的按钮抓焦点；_ready保留预先关闭的IGNORE状态。close的幂等和信号契约不变。
- `scripts/ember/ui_edge_v001/energy_progress.gd`：重入树后按当前尺寸重排实际轨道与FillClip；修复外层矩形已更新而内部仍沿用旧宽度。
- `scripts/ember/ui_edge_v001/bracket_button.gd`：重入树后重排焦点Overlay与角件，避免返回按钮尺寸改变后仍显示旧宽角框。
- `scripts/ember/ui_edge_binding_v001.gd`：自动投影要求设备与HUD均在树内、同Viewport；离树或跨Viewport时隐藏标记，避免用旧画布/另一视口坐标产生假位置。跨视口映射仍由调用方负责。

抽屉、进度和按钮的内部布局更新不能只依赖resized：挂接过程中外层可能先更新到新尺寸，重入后重复写同值不再发信号。各组件的deferred重排只用于已构建实例，不改变初次构建与正常排布。离树期间可更新数据和显示状态；重新挂回树后恢复当前布局与可见性。`set_drawer_open(false)`是无信号直接同步，`close_drawer()`实际开到关只发一次通知。

## 回归证据

- TA原探针：保留六项真实鼠标/Enter输入验证和两项离树关闭验证，仅更换报告输出位置。生产方重跑8项全部通过，原两项失败均修复，stderr为空。见 [ta-regression-v003.json](ta-regression-v003.json)；这不代替TA本人复审。
- 新增 [lifecycle-validation-v003.json](lifecycle-validation-v003.json)：112项全部通过，实际移除、重新挂接、跨720×720与960×540视口、离树连续同步、焦点释放、节点复用、独立抽屉以及设备投影边界；内部轨道/FillClip/焦点角件也核对真实尺寸。报告记录当前源码与测试SHA，包工具拒绝哈希过期的通过结果。
- 原245项常规、53项复用和68项控件检查继续通过，70组布局0几何错误。原有安全省略和窄画布降级范围保持原文说明。
- 重新运行Compatibility GPU捕获：12张PNG与v002逐张SHA相同，证明已验收的常规视觉保持一致；两种进度条宽度的像素检查继续通过。见 [visual-comparison-v003.json](visual-comparison-v003.json)。

v002独立TA报告在 `art-source/ember/ta-review-v001/ui-independent/review-ui-v002.md`；其中before失败属于原版本。本修订的验证工具为 `tools/validate_ui_edge_lifecycle_v003.gd` 和 `tools/validate_ui_edge_ta_regression_v003.gd`，使用正常Godot headless参数执行即可。

## 固定交付与保护范围

交付包：`art-source/ember/deliveries/ui_edge_components_v003_2026-10-06.zip`，新哈希随提交消息登记。v001、v002包不覆盖。保留所有资源路径，18张PNG和A稿参考未修改；项目设置、M0和地图源由baseline哈希检查保护。

统一提交规范：`docs/shader-learning/ta-art-review-standard-v001.md`。当前通用Theme、列表、设置/暂停等未完成项继续按v002审计声明，本修订没有扩大承诺范围。后续收到复审意见再产生独立修订，不在同名ZIP中静默更改。
