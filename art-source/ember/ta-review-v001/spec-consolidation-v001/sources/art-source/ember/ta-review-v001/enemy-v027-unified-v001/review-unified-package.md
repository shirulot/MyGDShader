# 四类敌人 V027 v001 统一运行包：PASS_ASSEMBLY_ONLY

日期：2026-10-07。本次批准固定汇总包的来源完整性、四个运行资源、独立冷加载及预览入口。160条960帧的逐批美术通过范围保持，没有以汇总替换返修后的版本。实际安装到 `assets/ember/characters/enemies_v003` 及主玩法集成尚不在本回执内。

固定ZIP `enemy_sequences_eight_directions_v027_v001_2026-10-07.zip`，69,253,900 bytes，SHA256 `aba87363a03247ab5069dc2d21dac9544a29e200932d86f0d7aa2a8a12e91826`。1254载荷加manifest，CRC、每项大小／SHA及冻结目录副本逐项一致。catalog SHA `0fdf47aebbce4c56aeed2c7baac9d13af77d3baaad71453a1abd9cf0bf8c1732`。

## 独立验证结果

|项目|结果|
|---|---|
|160条来源|四单位×八方向×五动作唯一完整；recipe/catalog一致，TA_ACCEPTANCE逐条映射一致|
|17个来源ZIP及17份正式回执|内含ZIP与交付库原件逐字节一致；内含回执与TA原件逐字节一致，各回执包含对应固定ZIP SHA|
|160图集、960单帧|每个文件与来源ZIP及来源catalog完全一致；单帧与图集对应格RGBA一致、二值Alpha|
|32方向缩略图|均与相应idle F0逐字节一致|
|旧正向20条120帧|保持v012原件；侦察机5条追溯到v011 SHA `13a4942d34d0ceabac7473c1689aa4784bc0c6f1555ff68817ed9d93159dab3e`，没有混入r1实验|
|四个新TRES|各40条，合计196,556 bytes；160个相对PNG引用有效，无PackedByteArray大块内嵌像素|
|完整ZIP隔离冷导入|初始无缓存；import11.497秒、probe10.004秒，均退出0、stderr0；1254原载荷不变|
|Godot实际保存资源|960个AtlasTexture格加载后的RGBA含透明区与源单帧一致；区域、尺寸、帧时长、FPS和loop符合规范|
|真实预览节点|4单位资源路由、5动作重启、nearest／centered=false通过|
|320次保相位切向|160种组合各在播放、暂停两状态验证frame2＋progress0.375、播放状态与原正向对照相位保持|
|320个自然计时播放器|全部160条各正常速度和1FPS验证；所有帧实际到达，循环动作触发循环，单次动作只结束一次并停末帧|
|本地网页发布文件|1154个文件与冻结来源一致，含index、catalog、1152个PNG|

登记为128×128、root(64,104)，idle4@4FPS／move8@8FPS循环，attack6@10FPS／hit4@12FPS／death8@10FPS单次。资源独立目录整体迁移时应保持TRES与单位PNG文件夹关系，并保留Lossless、无mipmaps、无fix_alpha_border、无premult_alpha及无自动3D压缩的导入设置。

## 实际网页复查及范围

访问 `http://127.0.0.1:6106/enemy-eight-directions-v027-v001/index.html`。四个单位均实际切换并看到对应图像：巡逻待机／移动／死亡、重装移动、切割攻击、侦察受击。检查4×浅底、1×深底、单次动作停末帧、前后步进和暂停切向保持当前帧。保存根级入口截图供复核。

本轮是已过像素的汇总增量验收，没有重复宣称重新逐帧美术审查960张图，也没有重跑作者1920条GPU深浅底矩阵。作者GPU结果仍是作者证据；本轮独立引擎证据为冷加载真实RGBA、运行节点及自然计时播放器。未启动主游戏或改写正式资源。

独立证据：`technical-integrity.json`、`technical-cold-receipt.json`、`technical-cold-result.json`、`technical-web-binding.json`，可复跑探针与脚本保存在本目录。

## 交付下一步

可以按已声明计划复制到新的 `assets/ember/characters/enemies_v003`，保持已通过PNG／TRES，保留旧enemies_v002、v012与全部冻结包。安装时仅对新目录登记导入设置，核对实际安装路径的四资源960格加载，以及review-current入口，再提交安装回执供TA增量核验。固定V027包不为更新通过状态而重写。
