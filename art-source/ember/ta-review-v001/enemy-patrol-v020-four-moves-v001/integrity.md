# P20 v001 巡逻四新向 move：独立技术审查

**结论：NEEDS_REVISION。NE 的浅甲伸缩与左右腿源区串入两项 P2 已由根 TA 结合实际图像确认。包完整性、母稿及旧稿保持、PNG/atlas/TRES 和最小冷加载分别通过；不能据这些通过项放行本批源归属。**

2026-10-07。仅本固定候选：SW/NW/N/NE 四条 move、32 新帧；旧 S/SE 两条 16 帧保持。W/E 只有静态母稿及审阅器回退，未制作移动，不算完成。未改生产文件或固定包，未操作浏览器。技术证据均在本 TA 目录，固定包解至 `technical-package/`。

## 固定绑定

| 对象 | 独立核实结果 |
|---|---|
| ZIP | `art-source/ember/deliveries/enemy_patrol_four_moves_v020_v001_2026-10-07.zip`；3,226,684 B；SHA256 `6a22203fde428f0820e3019ad5ae859159b4b39c35bcfe111190fc96c75c1e52` |
| 清单 | 143 文件：142 载荷 + manifest；无缺项、额外文件、字节数或 SHA 错配 |
| manifest | SHA256 `77740c0298d4ed54afa432c45bd06650bcaa178d54ebfe2c675945917c204f75` |
| `output/catalog.json` | SHA256 `1d0d766586e28be490713ccb397d8057e11f6782e2d27b60022094479fcd1c69` |
| `rig.json` | SHA256 `bab3596de72741ae36aef96161139eb9b426492c56654055b83fde24ff123c04`，与 catalog 绑定一致 |
| `output/enemy_patrol_move_v020.tres` | SHA256 `e658affe36eb526a3d490a1ba64d1c5656936a030283daa5db619941b3765020`，与 catalog 绑定一致 |

审查后再次核 ZIP 与全部解包载荷，未发生变化。详见 `technical-zip-file-binding.json`、`technical-post-freeze-binding.json`。

## 两项具体返修

1. **NE 浅色甲片进入可伸缩的 `left_thigh`。** 源段 `(57,80)→(57,85)` 长 5 px，却包含 15 个浅甲实体像素。F03/F04 映射段长 7.28011 px，轴向比 1.45602；不是只伸展深色关节连接条。F03 输出 `(61,83)/(61,84)`、F04 `(61,84)/(61,85)` 均取同一浅甲源 `(62,82)` RGBA `[192,182,169,255]`，形成实际拉长的浅色条。根 TA 已看 8×与网页 F03 读形，确认局部 P2。最小修订：把可见浅甲与可伸缩接缝分开，按原甲片职责保持形体；保留既有母稿与动作相位。
2. **NE 20 个原实体源像素同时归左右独立运动片。** thigh 6、cap 9、foot 5；其余 SW/NW/N 无实体重复或遗漏。已独立证明正式 PNG 实际双现，不能用中性 RGBA0 差排除：F02 原膝侧 `(62,89)` `[113,61,2,255]` 经 left_cap/right_cap 分别到 `(62,89)/(64,86)`；F04 到 `(60,91)/(63,88)`。原靴边 `(62,96)` `[109,127,143,255]` F02 到 `(62,96)/(62,92)`，F04 到 `(59,97)/(65,95)`。两条路径各自顶层可见。最小修订：按真实左右肢体边界明确唯一 ownership，移除邻腿实体串入；不能逐帧抹点掩盖源区问题。

来源、变换、实际颜色及顶层归属详见 `technical-rigidity-crosscheck.md/json` 与独立 `technical-ne-cap-shared-route.json`。根 TA 的最终视觉裁决覆盖早期未发现问题的抽样记录；本报告不把初看记录当最终通过。

## 已闭合的独立检查

- 八向 `source/*.png` 均与已通过 S002 固定 ZIP 的 `neutral_*.png` 逐字节一致，八张输出中性图亦同字节。S002 SHA256 `28951089e1403c65f6a8446aed5f049fdba704809175da36a391c6c5fa1e99a1`；来源 receipt 匹配。本批动画以登记原片及几何变换组成，未发现逐帧重生源 RGB 的管线；这不豁免上述 NE 分区缺陷。
- 旧 S 的 8 PNG + atlas 与 v012 固定 ZIP `42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe` 同字节；旧 SE 的 8 PNG + atlas 与已过 pilot ZIP `c7cf9683604740953a48d43b6fd2fbf7cd5d11767ee3af1fbc65171d4493dd21` 同字节。旧 16 帧的批准范围保持，不继承给四新向。
- 48 PNG 与六 atlas 的各格 RGBA 差 0，所有登记帧 SHA、atlas SHA 一致；实体 Alpha 均为 0/255。画布 128×128，root `(64,104)`；六 move 均 8 帧、8 FPS、loop=true；W/E move 不在 TRES。
- 四新向原生中性绑定图与母稿 RGBA 差 0。独立解析实际源区、保护区及层次；工具保护实体 SW/NW/N/NE 为 145/162/150/140 点，均只归 body，32 帧保护区实际输出与母稿对应颜色差 0。body 纯平移，膝甲/靴 32 组基底恒等；这里不泛称 `left_thigh` 的浅甲也刚性。
- 独立姿态公式、catalog 的 32 组部件变换及 hip/knee/ankle/support 登记一致；连接端点算术闭合。**N F02 right_thigh、F06 left_thigh 的 3 px 原连接段投影两端重合，basis=0/det=0。** 根 TA 已专项看实际承接，未见缺缝或悬挂甲片，不以此判退；也不能声明所有连杆始终非退化、厚度始终 1。

完整逐项证据：`technical-pixel-integrity.json`、`technical-summary.json`，独立脚本 `technical-audit.py`。

## CPU 取样残差与最小冷加载

独立双精度逆映射 CPU 合成与正式 PNG **不是全零差**：32 新帧共 64 个 RGBA 差异点，含 37 个 Alpha 覆盖差异；其余 27 点双方均 opaque，最大 RGB 单通道差 199（计入 Alpha 改变点时最大为 255）。坐标、预期/实际 RGBA、源 UV/归属已完整保留，不能改写为“32 帧 CPU0差”。本次未把 nearest 边缘/浮点取样模型差异进一步冒称为已精确归因，也未凭这些统计替代实际外观裁决。

| 方向 | F00–F07 独立 CPU RGBA 残差 |
|---|---|
| SW | 4, 6, 2, 5, 5, 6, 3, 3（34） |
| NW | 0, 1, 0, 1, 3, 3, 0, 1（9） |
| N | 0, 0, 0, 0, 0, 0, 0, 0（0） |
| NE | 3, 1, 0, 0, 8, 4, 5, 0（21） |

**独立最小 cold：PASS。** 将固定包所需 30 个文件按原字节复制到全新 TA 项目 `technical-cold-load/`，Godot 4.7.2 headless 导入并运行独立探针。六条 TRES 共 48 格全部加载，嵌入图像与 atlas 原 PNG RGBA 一致；128×128 region、duration=1、8 FPS/loop 与登记一致。加载八张中性依赖并实例化 preview 两个 nearest/centered=false 的角色。审阅器缓存的 14 项是 **八张中性 + 六条移动**，不构成八向移动已完成。

另从真实 CPU rig 读取 36 张 ownership mask，与独立解析逐像素差 0；32 组实时 CPU pose 与独立公式/登记误差 <2e−5。该读回确认 NE 重叠确属实际管线，不代表该源归属合理。探针没有 GPU 画面或连续播放验收。

证据：`technical-minimal-cold-load.json`、`technical-runtime-cpu-readback.json`、`technical-cold-probe.gd`、`technical-cold-probe.log`。

## 作者记录及范围限制

包内作者 GPU 80 项＝64 个新帧深浅底 +16 个旧帧，所报 live/TRES差值均 0；runtime 有 12 条 8/1 FPS 播放器记录、每条见全 8 帧且最少一轮，八条切向记录均报通过。两份 QA 的 catalog SHA 已独立绑定，详见 `technical-author-qa-binding.json`。**这些作者运行记录仅核绑定，未由本技术线复跑。**

本次独立运行只含最小资源 cold 和 CPU 归属/姿态读取；未重跑完整 GPU、自然播放、切向矩阵，未新增其他动作/方向验收。最终本包因 NE 两项 P2 返修；源保持及资源加载通过不能升级为整批生产通过。
