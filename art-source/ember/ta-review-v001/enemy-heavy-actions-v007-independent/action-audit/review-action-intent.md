# Heavy v007 独立动作意图审查

结论：**PASS，仅限本包 `idle_down`、`move_down`、`hit_down` 三动作 16 帧。未确认 P1/P2。** 旧包攻击与死亡不在这次送审范围；本结论不替代全包技术审计或游戏行为实现验收。

固定 ZIP：`art-source/ember/deliveries/enemy_heavy_actions_v007_2026-10-06.zip`，SHA256 `05350a58ef0a0e44ee19c3c6af69a2f38048f4e1c5d4ce24afae5076ece14494`，974073 bytes，82 文件。独立解包位于本目录 `package/`。16 个实际 PNG 已逐一绑定 catalog SHA 和 atlas 格；详见 [binding-and-pose-evidence.json](binding-and-pose-evidence.json) 与 [actual-motion-evidence.json](actual-motion-evidence.json)。

## 动作与实际可见结果

- **移动 8 帧 / 8 FPS / 循环**：逐帧查看浅底、深底整机图，以及左右履带窗口放大图。正面履带的同一纹样沿画面 +Y 方向推进；固定外壳、橡胶边和接地轮廓保持，纹样在上下端进入或离开外壳时没有出现可定位的断条、突然变宽或独立贴片。另直接比较实际 PNG 的两个 12×16 窗口，8 帧及 f07→f00 共 16 次过渡均满足 2px 同向循环，差异点为 0。这项像素测量用于确认实际纹样位移，视觉结论仍来自整机与局部逐帧观察，未以八个不同 hash 作为滚动成立的依据。
- **待机 4 帧 / 4 FPS / 循环**：塔体轻微上下起伏，双履带与宽接地支撑稳定。f00 与 f02 回到同一中性姿态符合四拍起伏，不构成角色重新生成或坏循环。位移较小仍能读成有重量的悬挂起伏，没有要求为了重量感增加无依据的大幅跳动。
- **受击 4 帧 / 12 FPS / 非循环**：中性→塔体左移 2px、下移 1px→右移 1px 的回弹→中性，短促反应与回收可读；单炮及双履带身份始终清楚。实际 `hit f00`、`hit f03`、`idle f00/f02`、`move f00` 全 RGBA 相同；全部 16 帧底部 y102–103 与中性逐像素相同，旧版受击跨动作接地多 1px 的问题在本范围关闭。

## 安装界面与旧问题

塔体与左右履带源区在 x44–46、x81–83 各有 3px 安装重叠，其中可见源像素分别为 99、98，y63–98。数字仅描述源区关系。对待机上下偏移和受击横移的实际成品逐帧观察，接头读成塔体后方的连续座体，没有第二个座体、悬空黑条或重复碎边；双履带主体未跟随塔体平移。局部依据见 [idle_down_mounts_dark_6x.png](idle_down_mounts_dark_6x.png)、[hit_down_mounts_light_6x.png](hit_down_mounts_light_6x.png)。

对照正式敌人动画规范、已接受 heavy 比例参考与旧失败回执，本次移动通过复用固定源纹样并在真实 PNG 中匀速循环，关闭旧版纹样厚度、间距、色阶逐帧变化且没有稳定履带流动的动作问题。蓝灰结构、浅色轻装甲、短炮和双履带比例保持已接受方向；未见新增部件或体积身份突变。

## 复核入口与范围

- [移动全部帧浅底 4×](move_down_all_frames_light_4x.png)、[移动履带相位深底 8×](move_tread_phase_dark_8x.png)、[受击全部帧浅底 4×](hit_down_all_frames_light_4x.png)。包内原生及 4× 深浅底图同样保留。
- 正式依据：`docs/shader-learning/ember-enemy-animation-standard-v001.md`；参考：`art-source/ember/enemy-examples-v001/enemy_tracked_heavy_scale_example_v001.png`、`art-source/ember/enemy-design-sheets-v001/three_views/enemy_tracked_heavy_three_views_v001.png`。
- 旧问题依据：`art-source/ember/ta-review-v001/enemy-v001-independent/review-cutter-heavy.md`。源重建与便携包另见兄弟审计 [technical/report.md](../technical/report.md)，不作为美术通过的替代证据。

本独立审查使用实际静态帧、相邻帧和循环边界对照，未启动浏览器或 GPU，未声称验证游戏移动速度与履带流速匹配、导航、受击逻辑或完整物理系统。根审查另有正常播放观察；本报告只给当前三动作的动作意图与接头闭合结论。
