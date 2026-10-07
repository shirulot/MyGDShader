# 巡逻兵五动作 v008 共享 mask 增量独立复审

**结论：PASS。v006 两种悬空黑条/碎点表现已关闭；移动、受击和待机的共享修补影响符合范围，未发现新增可见缺陷。**

只从固定 ZIP 独立解包到本目录 `package/`：SHA256 `4a3ab26e04abb5816c505fb0c0f851b8042886d8ea3d2b8516b1923360af74b4`，1,098,713 bytes，147 文件。包内 `references/` 的五张旧 atlas 原字节分别与冻结 v004_r1 move、v005 idle/hit、v006 attack/death ZIP 完全一致。实际 30 张 PNG 的 SHA 与 catalog 逐项相同，当前 atlas 各格与单帧一致。

## 修补与旧 P2 关闭

独立比较旧/新膝甲 polygon 的全部源纹素中心：唯一被排除的三个中心为 canonical `(76,87)`、`(76,88)`、`(76,89)`，没有新增源纹素。逐点按每个实际 `left_knee_cap` 的 position/basis 逆映射，全部 32 个删除显示像素均落回这三处，旧点 RGB 与源 RGB 一致。不是逐帧擦掉不同位置，也不是删除合法膝壳、夹爪或鞋。

在实际深浅底、固定注册的原生/4× 图及局部图中：

- attack f02 的 `(76,88–90)`、f03 的 `(76,87–89)` 黑条已消失。真实夹爪仍完整，膝甲壳面/轮廓未缩掉；没有改成连接线或重画工具动作。
- death f04 的 `(72,97)/(71,98)`、f05 的 `(66–68,102)`、f06/f07 的 `(63–65,102)` 点/条已消失。膝、腿鞋及残骸外形保持，原侧倒和末帧肩侧接地没有被重新对齐或改变；没有留下悬空底条。

因此 v006 的两种可见表现由同一 UV 源区修正闭合。判断依据是实际显示和精确来源，不是“现在只有一个连通区域”。

## 共享五动作的实际差异

| 动作 | 逐帧可见差异像素 f00 起 | 结果 |
|---|---|---|
| idle | 0 / 0 / 0 / 0 | 四帧全 RGBA 未变 |
| move | 1 / 1 / 1 / 0 / 0 / 1 / 0 / 1 | 指定五帧仅移除误带点；腿/爪无新增裂缝 |
| hit | 0 / 0 / 1 / 0 | 仅 f02 移除误带点；真实夹爪和恢复不变 |
| attack | 0 / 3 / 3 / 3 / 3 / 0 | 原黑条清除，真实工具/后坐保持 |
| death | 0 / 0 / 1 / 2 / 2 / 3 / 3 / 3 | 原碎点清除，稳定残骸保持 |

合计 32 像素全部由 Alpha255 变为 Alpha0，0 新增、0 可见重着色，其他全 RGBA 像素未变，双方 Alpha0 位置亦无隐藏 RGB 差异。

move 的具体显示删除点为 f00 `(76,90)`、f01 `(76,91)`、f02 `(76,90)`、f05 `(76,91)`、f07 `(76,89)`，全都逆映射源 `(76,89)`。hit f02 的 `(77,87)` 逆映射源 `(76,87)`。实际图中这些点清除后工具内缘更干净，没有挖掉膝盖有效装甲或引入裂口；其余步相/受击外形沿用旧固定图。

此次只审共享 mask 修补及其显示影响，未重复未变的主动作设计，也没有重开物理、AI 或伤害集成范围。未运行浏览器/Godot，未操作用户编辑器，未改生产文件。其它敌人不继承本结论。

## 证据

- [30 帧差异、全部删除点及逆映射/旧包绑定](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v008-independent/visual/shared-mask-delta.json)
- [攻击 f02/f03 深底 4×](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v008-independent/visual/attack_down_targeted_dark_4x.png) · [浅底原生](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v008-independent/visual/attack_down_targeted_light_1x.png)
- [死亡 f04–f07 深底 4×](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v008-independent/visual/death_down_targeted_dark_4x.png) · [浅底局部](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v008-independent/visual/death_down_old_v008_light_local_8x.png)
- [移动指定五帧浅底 4×](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v008-independent/visual/move_down_targeted_light_4x.png) · [深底原生](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v008-independent/visual/move_down_targeted_dark_1x.png)
- [受击 f02 浅底 4×](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v008-independent/visual/hit_down_targeted_light_4x.png) · [深底原生](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v008-independent/visual/hit_down_targeted_dark_1x.png)
- [独立复核脚本](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v008-independent/visual/inspect_shared_mask.py)

目录同时保留五动作旧/新完整画布的原生及4×深浅对照、修补相关局部图和固定包原图，便于复核。
