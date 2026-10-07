# Robot v011 Phase B1 rc02 — 技术增量独立审计

结论：**TECHNICAL_INCREMENTAL_PASS；本项未发现 P2。** rc01 的 NE/SE 同侧手脚投影同向问题已在实际骨点中改为反相，N 已落实纵向腕目标和定长双骨肘。本报告只通过固定包完整性、来源与修订边界、数值修订和最小资源加载；新增四向32帧的外观、步态、循环和转向最终验收由独立视觉/播放回执决定，不能从本报告推成整体动画通过。

审查日期：2026-10-07。固定 ZIP 独立解至本目录 `package/`，全过程未修改冻结 ZIP、活动生产目录或解包载荷。冷加载使用额外的 `cold-load/` 副本。

## 固定对象

|对象|实际 SHA-256 / 数量|
|---|---|
|`art-source/ember/deliveries/robot_eight_way_v011_phase_b1_rc02_2026-10-07.zip`|`b301fdea0e3f634d02a0da4eac437e1ce890515b582216daadc82c82211b4aaf`；14,354,117 B；696 文件条目|
|`sha256-manifest.json`|`b5b7c17e7a8574927dc7bfcab871a6a55e1a41da6a3e52c3fa230b955864f9c0`；695 唯一载荷；缺失、额外载荷及哈希/字节数错误均0|
|`walk-batch-metadata.json`|`5adc21d2224c9289b8659a376e4e8a4f22b973be9468eb81995eeb496c332990`|
|`robot_walk_batch_atlas_v011.png`|`137196518cba1eabfcb8b58579a33fe493ad6865ed8304426f98414ff6a42f01`；512×672|

清单和 metadata 是两个不同文件，没有沿用 rc01 的 catalog 命名歧义。根目录 atlas/metadata 与 `godot-walk-review/` 副本逐字节相同。56 个64×96格的 metadata SHA 与文件相符，atlas逐格解码与PNG RGBA零差，二值Alpha/原11色板无违规像素。

## 增量与固定来源

独立比较 rc01 固定解包副本：实际仅 `up` / `up_right` / `down_right` 的24张最终 walk PNG变化。`down` / `down_left` / `up_left` 的24张 walk 与八向母版8张，共32张逐字节保持。旧 S/SW 仍承接阶段A既有批准；NW的保留只说明字节未变，不替代其本批视觉审查。W/E walk、双帧 idle 和 collect 不在本批成品范围。

三向各11固定源片：N/SE无RGBA改动；NE只发生下述源归属转移。包内 `source/reference-phase-b1-rc01/` 的60份旧 rig ledger、11源片、8最终帧与TA留存rc01对应文件逐字节相同，不能通过替换比较基线掩盖修订。三向中性源片按既定顺序实拼均与原方向母版RGBA零差；三个母版PNG字节均未变。

NE源坐标 **(22,59)** 原值 **(130,155,163,255)，#829BA3**：`body`变为透明0，`arm_left_lower`从透明0取得完全相同RGBA。唯一rig配置变化是左臂分区多边形补到这一源像素；所有其他源片像素相同。没有重画颜色、扩大源甲片或更换母版。参见冻结代码 `build_remaining_walk_v011.cjs` 的 NE polygon、`composite_remaining_joints_v011.cjs:38–46`，以及独立 `incremental-integrity.json` / `author-evidence-binding.json`。

旧body位置和新前臂位置都进入修订掩码。独立按像素中心逆映射得到的该源点投影如下；这记录源点的采样位置，并不保证所有位置都处于最终顶层可见表面。

|NE帧|旧body位置|新前臂位置|
|---|---|---|
|F00|(22,60)|(19,60)|
|F01|(22,60)|(20,60)|
|F02|(22,60)|(22,60)|
|F03|(22,59)|(24,59)|
|F04|(22,60)|(24,59)、(25,59)|
|F05|(22,60)|(24,60)|
|F06|(22,60)|(22,60)|
|F07|(22,59)|(20,60)|

F04的两个输出采样仍逆映射到同一个固定源像素，是最近邻旋转的投影，不是增加两枚新源像素。8帧这些旧/新位置均被修订mask覆盖。

## 反相与骨长的独立数值

`build_remaining_walk_v011.cjs:38–57` 的 `poseForDirection` 对 `forward.x>0` 反号上/下臂旋转角，再依同一源骨段重建肘/腕；实际NE/SE全部8帧角度与rc01反号的最大误差低于9×10⁻¹⁶。北向取原腕端点纵向±0.60px目标，左右错半周期，用原骨长解双骨肘。

以下由当前 ledger 骨点独立算 **F04−F00**，点乘该方向保存的 `forward`；它不是归一化向量，因此数值是加权像素投影，不能当实际脚底行程。F00/F04 bob相同，比较不受身体起伏混入。

|方向/同侧|腕 Δ·forward|踝 Δ·forward|结论|
|---|---:|---:|---|
|N 左|+0.4800|−0.4800|反相；真实纵向腕/踝各1.2px相反|
|N 右|−0.4800|+0.4800|反相|
|NE 左|+3.5389|−4.3468|反相，rc01同号已修|
|NE 右|−4.2571|+4.3468|反相，rc01同号已修|
|SE 左|+3.7524|−4.3468|反相，rc01同号已修|
|SE 右|−4.6419|+4.3468|反相，rc01同号已修|

三向全部24帧 body/所有腿靴变换、腿骨点、bob与rc01完全相同；肩根与rc01相同。48组上/下臂长度记录（96个长度误差）都低于8×10⁻¹⁵，北向全部腕目标y误差0、无IK越界记录。此数值证明修订落地，不单独证明关节读形、承重或自然步态。

## 修补范围与刚性保护

本轮独立重算只覆盖修订三向24帧，没有重跑上一轮已核固定来源全流水。使用TA自己的像素中心逆映射及源片保护规则，重新核对当前刚体输出；三张新 imagegen 连接编辑源图也独立经声明的Sharp/Vips nearest/Alpha160/11色量化，与包内量化图零差。原始源图、提示词及输入保存于固定包，未独立审计生成服务调用历史。

24帧结果均为：刚体PNG重算零差；连接补丁最终合成零差；普通joint mask和old/new arm revision mask重算零差；当前刚性甲片/靴/前臂壳/工具保护区被补丁改动0；普通joint mask外相对新刚体改动0；old/new臂域和肩肘/归属点修订mask外相对rc01最终帧改动0。腿关节虽出现在普通连接mask中，其最终像素仍受更窄的臂修订范围保留规则控制。本次没有把“当前补丁范围”与“相对rc01修订范围”混为同一测试。

## 最小独立冷加载与作者证据边界

**独立实测 PASS**：固定包的Godot入口12载荷复制到独占 `cold-load/`，Godot4.7.2 headless冷导入，加载 `robot_walk_batch_v011.tres`、实例化 `preview_walk_batch.tscn`。14 clips/56格逐项核region、帧duration=1、解码RGBA；6条walk各8帧8FPS loop，8条pose各1帧1FPS非loop。两显示sprite为1×/4×、nearest、`centered=false`、`offset=(-32,-80)`；错误0。未执行GPU截图/循环观测/转向输入矩阵。TA探针以 `Image.load_from_file` 读本地源PNG产生的导出适用性warning属于测试探针，生产TRES使用已导入texture；本项没有测试最终平台导出。

**作者记录仅绑定，NOT_RUN_BY_TA**：`qa/godot_walk_batch_v011.json` 的112张GPU文件全部存在且SHA与固定manifest相符，报告atlas绑定当前 `137196…`；6条walk各两圈的记录，以及 `qa/godot_walk_transitions_v011.json` 的32条切向记录绑定同一atlas。没有将这些作者运行记录表述为本代理重放/连续观察。包内 `qa/cold_delivery_validation_rc02.json` 明确绑定阶段A rc02旧ZIP `df9884…`，属于历史证据，不能充作当前B1 rc02独立冷验。

`walk-review.html` 实际入口和静态链接完整，动态八向母版链接均存在；`review.html` 是旧阶段模板，不是本轮walk入口。

保留作者 motion skill 警告供视觉审查：SW near-duplicate `[0.0111,0.0104,0.0084,0.0094]`、N `[0.0085,0.0072,0.0091,0.0072]`、SE `[0.0089,0.0099,0.0109,0.0107]`。这些指标不能单独决定通过或返修，尤其N腕纵投影已修并不等于观感步幅充分。

## TA证据

- `zip-file-binding.json`：固定ZIP每成员绑定。
- `incremental-integrity.json` / `audit_increment.py`：24帧来源、范围、保护、骨点独立重算及32帧旧稿保持。
- `raw-quantized-source-binding.json` / `check_quantized_increment.cjs`：三张新连接源的量化重算。
- `author-evidence-binding.json` / `bind_author_evidence.py`：112图、六条循环、32转向仅绑定，源配置增量和入口链接。
- `minimal-cold-load.json` / `cold-load/ta_minimal_load.gd`：本代理最小资源冷加载实测。
- 三份 `*.cjs.diff.txt`：制作代码相对rc01的只读差异。

冷加载结束后再次核冻结解包695载荷全部SHA未变。范围内可提交综合TA回执；没有批准W/E、最终idle/collect或整套112帧完成。
