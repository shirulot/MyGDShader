# 履带重装机三动作 v007 独立技术审查

结论：**TECHNICAL_EXPORT_PASS，未发现来源、区域覆盖、履带循环或资源绑定异常。** 此结论不代替安装界面、动作力度与原生像素观感的独立视觉验收；攻击/死亡不在本包。

固定 ZIP 为 `enemy_heavy_actions_v007_2026-10-06.zip`，独立 SHA256 `05350a58ef0a0e44ee19c3c6af69a2f38048f4e1c5d4ce24afae5076ece14494`，974073 bytes，82 项 / 81 清单载荷。独立解至本目录 `package/`，CRC、全部长度/SHA、解包 SHA 和当前同名载荷 SHA 均吻合，无重复路径；清单外只有 `file_hashes.json` 自身。生产文件只读，本轮没有启动 Godot。

## 源区与身份

canonical SHA `f970aec0962bb8fe8ad7d515e5a11f1c6bbafec23410a665c08a61baed2f20de`，与已固定 v001 ZIP 内 `enemy_tracked_heavy_canonical_down_v001.png` 字节相同。没有逐帧再生成角色或改写源 PNG。中立输出与原 canonical 在明确的 0.5 覆盖规则内，覆盖/可见 RGB 差 0；源文件有连续 Alpha，硬覆盖依旧不能代表原生像素精修。

独立计算三块源区域：左右履带/安装座、中央塔体分别覆盖 814、813、1695 个有效源像素，联合完整覆盖 3125 个有效像素，无漏；左右履带源区无交集。重复归属仅限声明的两条安装界面：

| 界面 | 有效重复源像素 | 原生源范围 |
|---|---:|---|
| left_track_mount / tower | 99 | x44–46，bbox `[44,63,47,99]` |
| right_track_mount / tower | 98 | x81–83，bbox `[81,63,84,99]` |

没有声明外的邻区重复覆盖，重复源点全部记录在 `evidence.json`，不是只凭“3px”说明放行。塔体 z=1、履带 z=0，三块始终采样同 canonical；两履带矩阵保持 identity，塔体只接受登记的整数位移。不存在按帧缩放、重心或包围盒对齐。安装界面显露时是否仍读为一个合理接头，交由独立视觉审查；本报告不把区域数量/连通性当成此项视觉结论。

## 实际履带采样与 16 帧

独立实现两窗口 `(30,86,12,16)`、`(86,86,12,16)` 的 RGB 采样：

`source_y = 86 + ((output_y - 86 - phase) mod 16)`。

相位 `0,2,4,6,8,10,12,14`，纹理读形向屏幕 +Y 递进；f07→f00 同样模 16 前进 2，phase16 与 phase0 完全相同，窗口有 8 个不同纹理相。**3072 个窗口点 RGB 与原 Alpha 全部吻合**。Alpha 使用输出原坐标源值，没有借循环纹理的 Alpha 改外形。

每个移动帧另与“相同塔体位移、phase=0”的独立输出比较：窗口外可见 RGBA 差 0，排除了把塔体悬架变化误算为窗外纹理变化。全部 16 帧以固定三块源区、登记整数矩阵和窗口采样重建，**完整 RGBA 差 0**。这覆盖了安装座、窗边、胶边、罩壳和炮体，而非只比较窗口中心。

- 16 个登记姿态的实际矩阵与独立预期完全相同，root `(64,104)`、两支撑 `(36,104)/(92,104)` 始终一致。
- 左右外履带 ROI（x24–41 / x86–103，y64–103）所有帧 Alpha 零差；待机/受击该 ROI 的完整 RGBA 零差。所有帧 y102–103 接地带全 RGBA 零差。
- 正式帧均 128×128、二值 Alpha、无画布边截断；单帧与图集裁格全 RGBA 零差，catalog 帧 SHA 对应。16 帧均单一 8 连通区域，仅作为碎片诊断。
- idle f00/f02 完全相同，各动作中立首帧完全相同，hit f03 精确恢复中立。塔体移动定义为 idle `0/-1/0/+1 y`，move f02/f06 下沉 1px，hit `[0,0]→[-2,1]→[1,0]→[0,0]`；两履带固定。

## 资源、GPU 与冷证据

实际 `.tres` 含 idle 4 帧@4 FPS/loop、move 8 帧@8 FPS/loop、hit 4 帧@12 FPS/nonloop，duration 全 1.0。16 个嵌入图片/AtlasTexture 裁区与图集全 RGBA 零差，裁区按完整 `(128*i,0,128,128)` 注册，没有沿 bbox 取图。catalog 的源/rig/atlas/逐帧 SHA 绑定有效。

**32 张保存的黑白底 rig/PNG 对照** 独立解码：左右 RGBA 零差，且分别与正式帧直接合成、统一 ROI `(16,32,96,80)`、4× nearest 放大 RGBA 零差。这是独立核对包内 GPU 证据，没有冒称本轮重新渲染。

冷回执 SHA `6402d000d3e653eb25751a5e9226fd513c487d4e6c3ef5ab9c25588021d3f1d2`，冷报告 SHA `fefed3270132e3a605cd62fb200de2bcfd76761dd19bbf2a8516bdb5a90247d9`。独立核对冷目录 `enemy-heavy-actions-v007-coldcheck` 的 **33 项核心源/资源（包括16帧）**，均与回执 SHA、固定 ZIP 相同；回执内嵌报告与实际报告相同，catalog SHA 绑定同固定包。import/capture exit=0，4 日志的长度/SHA 吻合，两个 stderr 均 0 bytes。

作者冷运行约 9.2014 秒，正常速度/1 FPS 共 6 个播放器遍历全部帧；idle/move 出现循环且没有 finished，hit 出现 finished 且没有 loop。单次 hit 在审阅播放器停留 0.5 秒后重播，资源本身 nonloop。该冷运行属于制作方证据，本轮仅核实其绑定和记录，未重复启动 GPU。

6106 本地 `heavy-actions-v007/index.html` 与包内 `preview.html` 同 SHA；catalog 与三个 atlas 的本地服务文件同固定包。独立工程及嵌入帧资源随包交付；页面是辅助入口，正式依据仍为固定包原帧。

证据在本目录 `verify.py`、`evidence.json`、`bound-cold-receipt.json`、`bound-cold-playback.json` 及 `package/`。本包的原地履带纹理循环没有绑定实际世界位移/速度，因此不声称已验证游戏移动匹配或无滑步；也不扩大到攻击、死亡及其他朝向。
