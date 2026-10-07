# Heavy / Cutter v013 首阶段：独立技术绑定

结论：**TECHNICAL_BINDING_PASS**。仅对应 heavy、cutter 的 `move_down_right`，各 8 帧、8 FPS、loop、128×128，登记根点 (64,104)。本报告不替代另行逐帧视觉裁决，也不批准暂停制作的巡逻/无人机方向稿。

固定 ZIP SHA256 `5db52757c74fc537b3f45d87abdbab8c58e5d8fcd3cf6366153f7b32ef98b9ef`，5,518,904 bytes，121 文件＝120 payload＋manifest。独立验证安全路径、无重复/链接、CRC、清单大小与 SHA；120 项与冻结目录逐字节一致。解包仅写本审查目录 `package/`。

## 独立像素与来源核验

- 16 张逐帧 PNG 均为 128²、二值 Alpha，未触画布边缘；两张 1024×128 atlas 的每格与对应 PNG 全 RGBA 零差。两款深浅底 1×/4×联系图均与实际 atlas 最近邻合成逐字节一致，未按 bbox 重新对齐。
- 实际 `pilot_catalog`、rig enabled 列表和交付 TRES 都只有 heavy/cutter；暂停单位仅在冻结静态上下文中。导出遍历 enabled 列表，审阅器 picker 依据实际 TRES 只显示两款；不会把巡逻/无人机误列为通过动画。
- v012 ZIP 重新计算 SHA 一致。两款 reference `move_down.png` 与 v012 实际 atlas 逐字节相同；`source/approved_down` 和 `neutral_down` 与 v012 idle f00 实际 PNG 逐字节相同。未以作者 baseline 数字代替旧包对照，也未宣称本轮重审全部 120 个旧帧。
- 固定 registered 源与对应 SE neutral 全 RGBA 相同；两款源图 SHA、rig 脚本/登记 SHA、16 张方向中性图及 turnaround 源哈希闭合。每款维持一套 `common_scale`；这里只核登记和来源，不重算生成模型或推导造型通过。
- 独立逐点比较 cutter bind 与 registered 原图，实际 **83** 个变化：新增 13、删除 44、可见重着色 26，全部落于两块声明前腿区域 `[43,80,59,97)` / `[71,77,86,96)`；区域外全 RGBA 零差，壳体、工具和后腿原装甲未改。heavy bind 全 RGBA 零差。每个变化坐标及前后 RGBA 保存在 [integrity.json](integrity.json)。

固定部件来源另用独立 CPU 中心点多边形登记和最近邻逆取样复算。heavy 三区有效源点为 body 1423、近履带 1089、远履带 727，无漏/重复；bind＋8 帧全 RGBA 零差。cutter 原源点为 body 1000、后右腿 147、后左腿 128；70 个原前腿点按声明排除，40 个重复源点均位于声明安装重叠区；新增两腿来自同一固定生成母件和两个 source_rect，未逐帧换源。

cutter bind 和 6 个动画帧 CPU 重组全 RGBA 零差；f04 `(48,90)` / f06 `(47,89)` 各有 1 点 CPU/GPU 边界差：固定新前腿 crop 最左取样线的 CPU 结果有覆盖，正式帧透明。该算法尚未做到 GPU 浮点边界的精确等价，作为重组精度边界如实保留，不单凭两点差异新造动作/美术 P2。证据：[fixed-parts-reconstruction.json](fixed-parts-reconstruction.json)。空格遵守实际导出的白 RGB／Alpha 0 契约，未把透明 RGB 差异当形变。

## 独立冷加载

Godot 4.7.2 独立冷 import：exit 0、stderr 0。最小资源合同 **40/40**：两套 TRES 各只有一条 `move_down_right`，8 帧、8 FPS、loop；16 个 AtlasTexture region 依次为 `(128*i,0,128,128)`、duration 1；内嵌 ImageTexture 与实际 atlas 全 RGBA 零差，各格与实际 PNG 零差；实际审阅器只列两款、两款资源路由及 Nearest/全画布显示均通过。

证据：[冷结果](package/ta-cold-contract.json)、[独立探针](package/ta_cold_contract.gd)、[冷导入日志](cold-import.log)、[冷加载日志](cold-contract.log)。初次探针误用 JSON 浮点数组与整数数组直接等式，并对 `res://` 原图读取产生工具警告，修正探针的类型比较和绝对文件读取后 40/40；诊断日志另保留，未修改生产合同。

## 作者证据绑定

`pilot_gpu_roundtrip.json` 32 个深浅 live-rig/PNG 和保存资源/PNG 对照均记录 0 差；`pilot_runtime.json` 8 个正常/慢速实例均遍历八帧且完成循环，16 个方向选择记录保持已制作动画相位、未制作方向退回 neutral。这三份作者 QA 均与本包 pilot catalog SHA `b428b2dbc931f6789cd11d3b3f163b900bca33fbd0d6814be81fbcf1036df8c4` 闭合，**本轮仅绑定，未重跑作者 GPU 或自然循环**。

来源脚本、固定包、逐点数据及独立脚本均留在本目录。生产文件、原包、用户编辑器和主工程未改。
