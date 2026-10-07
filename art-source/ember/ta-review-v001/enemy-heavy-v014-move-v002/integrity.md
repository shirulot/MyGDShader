# 重装机 v014-v002 独立技术增量复审

日期：2026-10-07。结论：**P2_CLOSED_FIXED_SOURCE_AND_COLD_RESOURCE_PASS**。v001 的 N 左履带白块 P2 已关闭；本轮未确认新增技术阻塞。通过限于本次采样修复、来源/保护/导出及最小冷加载，六个新方向的动作视觉仍由根 TA 与独立视觉回执裁决，不扩大到其他动作。

固定 ZIP SHA256 `74ce3153d2389e9d170fbc5ccf0ea92dcf0a14dd671822d3479a5feaa1d00db9`，3,901,897 bytes，162条目=161载荷+manifest；独立 CRC、清单集合、SHA、字节数全部通过。活动162文件与固定包同字节。旧基线始终读取保留的 v001 ZIP（`dbad34a8845cce2a648d904790f5abd34fd64abbb5762f50d458f595e648c9ae`），没有用可变工作目录代替旧包。

rig 的运行差异严格为 N 左窗 origin.x 28→31、cross_width 16→11，即 x28..43 收到 x31..41；y85..100、period16、sign=-1、2px/帧，以及 ownership、源、悬挂和支点全保持。新增 revision 字段只是说明文字。8张 source、全部 provenance/母稿/登记/prompt、SOURCE_RECEIPT 同字节；rig/shader/preview/项目等10项已审运行代码同字节。export.gd 仅增加可选方向参数，未请求再生的动作使用包内上一 catalog poses和现存PNG；无参数入口仍完整导出，冷打开不依赖外部历史工作目录。网页只改版本标题。增量加入独立审计脚本/QA，不误当美术载荷变化。

其余7动作的56帧+7atlas，**63文件逐字节保持**，含旧 S(v012)/SE(HCv001) 两条；N F00亦与 v001/原母稿同字节。N F01–F07每帧恰好75个RGB点改变，共525点，全部位于排除的边缘列 x28/29/30/42/43、旧窗 y85..100内，且逐点回到原固定source的RGBA。新窗内部、旧窗外全RGBA差0；全部Alpha差0。没有重绘框、轮盖、侧甲、壳体或支点，也没有透明度删边。

对旧报告33项实际白污染坐标逐一复算，**33/33恢复原源实体颜色**，不再输出不透明纯白。新左/右窗8相位实际采样分别1408/1792，共3200次，透明源采样0，窗口内正式输出RGB与按 sign=-1/2f/mod16得到的原源RGB差0。F07→F00仍为向上2px、16周期闭环。自有同位置 `N_left_old_new_8x.png` 上行v001、下行v002，已看修复的原生像素8×图；白点和短白边已消失。这里只关闭确认的 P2，不用技术指标替代全部动作美术判断。

64PNG与8atlas逐帧全RGBA差0；TRES内8张Image均对应正确atlas原RGBA，catalog/rig/TRES/atlas/64帧SHA全部绑定。更新N的4张深浅底1×/4×联系图独立复合RGBA差0。catalog SHA `c5baac058883aef7c9f25d3b3369f8eb653c71bbcd89bb15f2ab706394baa5bf`。v001的SW/NE/E升降帧26个边界覆盖差，随这些7条未变PNG原样继承其已记录来源和限制，本轮未重开无关GPU调查。

作者96组新帧live rig/PNG与16个旧帧TRES对照、16播放器组、8切向记录，以及新增tread_source_audit，均与本 catalog/manifest绑定；**没有冒充TA重跑**。外置cold_receipt_v002 SHA/包SHA/161载荷对上，当前制作方冷目录161项全部同字节；其“111核心”未提供成员集合，本报告以独立161项比较为证据。当前6106服务的 index/catalog/N atlas同固定包，未发网络请求。

TA实际最小冷验证：从本ZIP新解无缓存工程，Godot4.7.2-stable Steam/headless，导入5.763s、探针1.315s，均exit0/stderr0，**24/24 PASS**。检查8实际内嵌atlas关联/动作元数据、N八帧region/duration、外部依赖为空、场景打开/Nearest以及N↔down保留F03+0.375相位。导入后161原载荷SHA全保持。**没有GPU framebuffer、自然循环或作者96GPU/16播放器/8转向全套复跑**；不重复v001的95项宽检查。

证据：本目录 `binding.json`、`verify_incremental.py`、旧/新诊断图、`cold-probe.json`、`cold-receipt.json`、自有探针/运行脚本及导入/探针stdout/stderr。生产只读，旧ZIP保留。
