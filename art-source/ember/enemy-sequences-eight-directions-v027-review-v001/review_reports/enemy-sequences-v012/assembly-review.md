# 四款敌人 v012 总装准备检查

**最终结论：PASS_FINAL_PACKAGE_STATIC_BINDING。** 冻结包 `enemy_sequences_v012_2026-10-06.zip`，SHA256 `42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe`，306 entries / 305 manifest payload，独立清单与既审载荷绑定通过。120个逐帧PNG、20张atlas及4个组合SpriteFrames保持固定审阅包的载荷、帧顺序和时间参数，没有发现缺条、漏帧、错接动作或重复动作键。包内20/20正式回执绑定各自版本；本报告执行总装核验，不重新替代这些逐动作美术回执。

审查对象：`art-source/ember/enemy-sequences-v012/` 当前静态快照。独立证据 [assembly-binding.json](assembly-binding.json)，可复查脚本 [verify-assembly-static.py](verify-assembly-static.py)。仅从文件读取/解码，输出只写TA目录；未重跑引擎/GPU，也未重新审已通过的像素画面。

## 独立核对结果

| 项目 | 实际核对 |
|---|---|
| 5个来源ZIP | 逐一读取实际ZIP SHA，匹配已审固定包及recipe；未由作者的PASS字段推导来源正确。|
| 20张atlas | v012图集字节与对应来源ZIP中的正式atlas完全相同，同时匹配来源catalog及recipe SHA。|
| 120个PNG | 每个`unit/action/fNN`字节等于对应固定ZIP的同动作/同帧，匹配两份登记SHA；128×128。输出目录恰有140张PNG（120帧+20atlas），无额外或缺失PNG。|
| 4个SpriteFrames | 独立解析实际保存的`.tres`，解出20个嵌入RGBA8 Image、20个ImageTexture及120个AtlasTexture。逐帧按保存的矩形解码，120格原始RGBA字节与固定ZIP的对应PNG解码完全相同，包括透明区RGB；帧region依次为`(128*i,0,128,128)`，duration全为1。|
| 20条时间参数 | 每单位idle4@4/move8@8循环、attack6@10/hit4@12/death8@10单次；来源catalog、recipe及实际SpriteFrames三方一致。20个`unit/action`键唯一，每单位5条完整；相同中性像素被不同动作有意复用不算重复动作。|
| canvas/root | 来源包和recipe均128×128、root(64,104)。root是注册约定，不是SpriteFrames内部属性；实际preview使用`centered=false`、`offset=(-64,-104)`及Nearest，侦察机仍采用地面投影根。|
| 既有40播放器记录 | 独立读取`assembly_runtime.json`的全部20动作×normal/slow。每条seen集合恰覆盖预期所有帧、无重复索引；idle/move至少一圈且无finished，单次动作至少一次finished且无loop。未将记录当成连续视频视觉观察。|

## 来源绑定

| 来源 | 组装范围 | ZIP SHA256 |
|---|---|---|
| patrol v008 | 五动作30帧 | `4a3ab26e04abb5816c505fb0c0f851b8042886d8ea3d2b8516b1923360af74b4` |
| heavy v007 | idle/move/hit 16帧 | `05350a58ef0a0e44ee19c3c6af69a2f38048f4e1c5d4ce24afae5076ece14494` |
| heavy v009 | attack/death 14帧 | `329e2fb60b0e7930a5178e92b4fe014e526bc5aa771f1a8b53e69eee8b15bf18` |
| cutter v010-r1 | 五动作30帧 | `c154a145e56aa10cd6394507350a47dc21ead655915c73e7f74131e146f9f948` |
| drone v011 | 五动作30帧 | `13a4942d34d0ceabac7473c1689aa4784bc0c6f1555ff68817ed9d93159dab3e` |

初审 recipe SHA256 为 `fd6a2137458d87525fc785ff87e461b9097263addf8fb340a3d5cbb8d0e7a140`；当时integrity/runtime两份记录自带recipe hash均匹配。独立JSON绑定四份TRES、20atlas、工程入口、脚本、recipe、接受登记及runtime截图/记录的实际SHA。原runtime记录只内置recipe hash，没有内置四TRES hash；因此本次的文件绑定和已有运行记录不能宣称为新冷跑或最终封包运行。最终状态与引用hash更新详见下节。

## 静态依赖及接受状态

`project.godot`入口为`preview.tscn`，场景依赖`preview.gd`。该脚本按四个明确unit名称加载`output/<unit>.tres`；四资源纹理为内部RGBA Image→ImageTexture→AtlasTexture，不依赖活动母稿、原rig或绝对机器路径。示例正常2×及slow原生1×只是显示尺度；slow用`1/FPS` speed_scale。`capture.gd`加载同一preview，记录40个播放器及recipe hash。这些必要文件当前存在，路径关系可解析。

初审 snapshot 中`TA_ACCEPTANCE.json`为`PENDING_TA`、15/20；根代理随后完成侦察机正式回执，制作方同步登记并冻结下述最终ZIP。本子代理未修改生产接受登记。

## 最终固定包增量闭环

独立证据 [final-package-binding.json](final-package-binding.json)：ZIP内306个名称无重，`file_hashes.json`列305个payload恰好覆盖其余所有成员；逐成员字节数与SHA全匹配，未只复述package_receipt。已审120个PNG、20个atlas、4个TRES、5份原ZIP与其余运行依赖均保持同hash；接受状态、回执和最终capture记录/截图的更新单列绑定。

最终 recipe SHA 为 `a37186d19814d6bb967f703a83324d4791d489b78f2793d839498891056a8d23`。独立将新状态`TA_APPROVED_SOURCES_ASSEMBLY`单处恢复成旧`ASSEMBLY_PENDING_FINAL_TA`后，恰好还原初审fd6a…hash，证明recipe只更新接受状态，动作/来源参数完全未变。integrity记录恢复旧recipe引用后也还原旧SHA。

最终runtime JSON及截图与初审不同，已重新绑定。制作方说明更新状态后执行了最终build/capture；TA不凭静态哈希推断执行次数。独立核包内最终40播放器seen/loops/finished完整、其内置recipe hash匹配最终登记。这里只说TA核了最终已有运行记录与固定包绑定，**未独立重跑引擎、未执行最终ZIP解压冷跑**，也不把该记录当作连续视频美术观察。

最终`TA_ACCEPTANCE.json`为PASS、20/20，20个unit/action键与总装完全对应；每条来源ZIP SHA和所附正式报告SHA均从冻结包独立匹配。新增侦察机正式报告，其余15条回执仍保留各自批准版本。范围仍是四款五动作down/front像素资源；其它朝向、AI/伤害/碰撞、世界速度和玩法事件接口不在本总装验收内。
