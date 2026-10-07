# Ember 四款敌人八向五动作 · v027 汇总

四款敌人各40条动作，共160条、960帧。本目录仅复制逐批正式通过的固定PNG，再为每款角色生成一个SpriteFrames。20条原正向动作保持v012原文件；方向与动作不以镜像或静态占位补数。

`assembly_recipe.json`记录每条动作的来源、图集与单帧SHA、帧数、FPS和循环属性。`TA_ACCEPTANCE.json`记录逐批美术回执；`reviewed_packages/`保存这些回执对应的原始ZIP，`review_reports/`保存正式报告和勘误。逐批通过与本汇总包的独立导入验收分开记录。

使用 `output/enemy_patrol.tres`、`enemy_tracked_heavy.tres`、`enemy_cutter.tres`、`enemy_scout_drone.tres`。给AnimatedSprite2D赋对应SpriteFrames，设Nearest、`centered=false`、`offset=Vector2(-64,-104)`。每帧128×128，根点(64,104)。TRES以相对路径引用同目录各单位文件夹中的原PNG图集；移动资源时保留这一目录关系。单帧PNG同时提供。

动作名为 `idle/move/attack/hit/death` 加 `_down/_down_left/_left/_up_left/_up/_up_right/_right/_down_right`。待机4帧4FPS、移动8帧8FPS循环；攻击6帧10FPS、受击4帧12FPS、死亡8帧10FPS单次播放，结束停留末帧。攻击视觉释放在F03，死亡残骸停留在F07。

PNG按Lossless导入，关闭Mipmaps、Fix Alpha Border和Premult Alpha，并关闭自动转3D压缩。本独立项目已设置importer_defaults。安装脚本只给本资源目录写对应导入设置；这些设置保留透明区域原RGB，使加载后960个切片也能逐RGBA验证。手动复制时保留单位目录与TRES之间的相对路径，并设置这些导入项。

切换同类动作方向时，先保存frame及frame_progress，再play新方向并调用set_frame_and_progress恢复。原暂停/播放状态也应保留，示例见preview.gd。不要为死亡自动重播，也不要按每帧包围盒重新对齐角色。像素资源验收不代替项目的AI、伤害、碰撞或世界移动速度匹配。

独立打开project.godot运行preview.tscn，可按单位、动作、方向查看并与原正向同相位对照。`build.gd`验证保存后SpriteFrames的960个原生切片；`verify.gd`对全部帧进行深浅底实际GPU比对；`capture.gd`验证320个正常/1FPS播放器和160次保相位方向切换。只有正式总监回执才能将本汇总包标记为最终通过。
