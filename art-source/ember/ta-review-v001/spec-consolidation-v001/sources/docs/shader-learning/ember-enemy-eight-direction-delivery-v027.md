# 四款敌人八向五动作交付 v027

当前状态：已完成交付。四款敌人×八方向×五动作，共160条、960帧，逐批美术、统一运行包和实际项目安装均已获技术美术总监通过。统一包结论为`PASS_ASSEMBLY_ONLY`，安装结论为`PASS_INSTALLATION_ONLY`，无待处理审核项。

当前预览：<http://127.0.0.1:6106/review-current/index.html>。支持四款单位、八方向、五动作、逐帧、正常/1FPS以及1×/4×查看。固定审核入口：<http://127.0.0.1:6106/enemy-eight-directions-v027-v001/index.html>。

固定包：`art-source/ember/deliveries/enemy_sequences_eight_directions_v027_v001_2026-10-07.zip`。

SHA256：`aba87363a03247ab5069dc2d21dac9544a29e200932d86f0d7aa2a8a12e91826`。每条动作的原固定包、源图集和单帧SHA、回执映射见包内`assembly_recipe.json`与`TA_ACCEPTANCE.json`。17份原固定ZIP和正式报告一并保留，回执中的扩展诊断仍可从原工作区`art-source/ember/ta-review-v001/`查询。

## 资源与目录

实际安装位置为`assets/ember/characters/enemies_v003/`，包含四个SpriteFrames：

|单位|资源文件|
|---|---|
|巡逻兵|`enemy_patrol.tres`|
|履带重装机|`enemy_tracked_heavy.tres`|
|切割者|`enemy_cutter.tres`|
|悬浮侦察机|`enemy_scout_drone.tres`|

每个TRES包含40条动作，以相对路径引用同目录下各单位文件夹中的PNG图集。TRES与单位文件夹必须一起保留目录关系。单帧位于`单位/动作_方向/f00.png`等路径，每个动作也提供横向PNG图集。四个TRES合计196,556字节，原PNG未经重新编码。

## 固定规范

每帧128×128透明画布，根点(64,104)。AnimatedSprite2D使用Nearest、`centered=false`、`offset=Vector2(-64,-104)`；按场景统一设置角色缩放，不逐帧裁切或按包围盒居中。

方向顺序为`down`、`down_left`、`left`、`up_left`、`up`、`up_right`、`right`、`down_right`。动作名称由下表中的动作名加下划线与方向构成，例如`attack_up_left`。

|动作|帧数|FPS|播放行为|
|---|---:|---:|---|
|idle|4|4|循环|
|move|8|8|循环|
|attack|6|10|单次，F03视觉释放|
|hit|4|12|单次，末帧恢复|
|death|8|10|单次，F07保持残骸|

F编号从0开始。切换同类动作方向时，保存`frame`和`frame_progress`，播放新方向后用`set_frame_and_progress`恢复，两者一起保留，暂停状态也应保持。示例见统一包`preview.gd`。死亡结束不自动重播。

## 像素与导入

PNG使用Lossless，关闭Mipmaps、Fix Alpha Border、Premult Alpha和自动转3D压缩。独立包已配置导入默认值；安装脚本只给新资源目录设置对应导入项。Nearest在AnimatedSprite2D节点指定。这样包括透明区原RGB在内的加载后切片也与源PNG一致。

美术保持低饱和旧工业方向：浅甲、蓝灰结构、克制黄铜和已认可的原生比例。不镜像交换不对称工具，不逐帧重新生成角色。装甲、护膝、靴和工具保持刚性；命名并登记的连接段可按端点变换。合法遮挡不会被强制补画成重复部件。

正向20条120帧保持v012原文件。悬浮侦察机正向继承已过原v011，不包含未审r1实验。其余七方向的来源与每轮正式回执逐条记录，不由正向通过结论外推。

## 验证范围

作者已验证最终候选：4个SpriteFrames的160条时间参数与960切片RGBA/源SHA，1920条深浅背景GPU比对，320个正常/1FPS播放器和160次保相位切向。完整固定ZIP在新目录冷导入后重跑GPU与播放器也通过，1254个载荷与1210个非QA核心文件保持。

技术美术总监独立验证了17份来源包与回执、160条映射、四个SpriteFrames的960格冷加载RGBA、320次播放/暂停保相位切向，以及320个正常/1FPS自然计时播放器。正式汇总回执：`art-source/ember/ta-review-v001/enemy-v027-unified-v001/review-unified-package.md`。该独立证据没有重跑或替代作者的1920条GPU矩阵。

安装作者检查：1157个载荷逐字节一致；仅给新目录1152个PNG生成导入元数据及缓存，主项目实际加载960格RGBA和源SHA全通过。472个旧版/固定包/项目保护文件的前后SHA一致，旧预览完整归档。安装送审证据：`art-source/ember/enemy-sequences-eight-directions-v027/qa/installation_submission_receipt_v001.json`。固定ZIP及固定审核目录保留提交时状态，当前通过与安装状态单独记录在`assets/ember/characters/enemies_v003/FINAL_ACCEPTANCE.json`。

技术美术总监随后独立复核实际安装路径：1157个载荷、1152份导入设置及2304个缓存、四资源160段960格RGBA/图集区域/帧时长/FPS/循环属性、472个保护文件、1154个当前预览文件与旧入口备份全部通过。正式安装回执：`art-source/ember/ta-review-v001/enemy-v027-installation-v001/review-installation.md`，SHA256为`1395554bf4588c2bf1a24cca1baefbb241d4a091a5e58285940b1882c7d47772`。ZIP旁的`enemy_sequences_eight_directions_v027_v001_acceptance.json`同时保留汇总与安装两份通过来源。

这些资源提供视觉序列和时间参数。伤害、投射物、碰撞、世界位移速度匹配等由主游戏逻辑接入；本轮验收不自动覆盖这些系统。
