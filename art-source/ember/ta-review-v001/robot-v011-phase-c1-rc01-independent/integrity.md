# Robot v011 C1 rc01 独立技术审查

审查日期：2026-10-07，Asia/Irkutsk。结论：**技术范围 PASS**，未确认来源、补丁保护、导出或必要播放行为方面的 P1/P2。范围仅为 SW 新增 idle 2 帧、collect 4 帧及其保留资源、独立冷资源与单次结束行为；动作外观由独立视觉审查及根 TA 裁决。本报告不扩大到其余方向的 idle/collect、最终 24 条动作或主工程接入。

## 固定包与旧资产

正式 ZIP：`art-source/ember/deliveries/robot_eight_way_v011_phase_c1_rc01_2026-10-07.zip`；SHA256 `0c62177198973b24bb3fbfcc306ba4617af3ad754eb5a0696bdfddb4f19f51df`，19,576,548 bytes，859 条目（858 载荷与 1 manifest）。独立读取 ZIP，CRC、清单集合、每项字节数及 SHA 全部相符；固定活动目录的 859 项与 ZIP 同字节，未用活动目录替代正式包。

以已审 B2 rc01 固定 ZIP `538d7bb49eb2e4480046eee50306a232b7a3f130219564e1618dbfbfff19164c` 为基线，8 张身份母版、64 张 walk 帧及旧 walk atlas 均逐字节保持；本轮没有重开旧走路造型审查。

## 固定来源、排姿与支撑

独立从 B2 的 11 固定片重建 C1 的 12 片：10 个肢体片原 RGBA 保持；body 使用原 body 至 y55，pelvis 使用同一原 body 从 y54 开始。y54–55 共 8 个实体重叠像素来自原源，没有新增连接色。中性组合与已通过 SW 母稿全 RGBA 差为 0，母稿 SHA `1ce8c81e3b4e1758b4478e78bb5aa1499f3e1cd95687283541a4c4e9b09d16b3`。

独立按源片、层序和像素中心最近邻采样重算六张原始 rig 帧，均全 RGBA 差为 0。idle F01 仅上身移 y−1，骨盆与双靴固定。collect F01/F02 上身、骨盆移 (−0.8,+2)，双靴源到屏幕的矩阵保持恒等；腿由原骨长、原弯曲分支及固定踝点求解。24 条肢链、48 个骨段端点检查：排姿重算误差 0，端点最大误差 7.11e−15 px，骨长最大误差 7.99e−15 px，无逐帧缩放或长度钳制。idle y≥64、collect y≥77 的实际输出分别与母稿同 RGBA；这是可见下部/靴底的定点证据，不把合法遮挡误写成整个靴片都在最终 PNG 可见。

## 局部 imagegen 采纳范围

重新对采用的生成源做同规格 nearest 采样、11 色调色板量化，独立重建保护区、接缝 mask 和合成规则；六张最终帧与重算结果全 RGBA 差为 0。以下数值为相对原始 rig 帧的实际修改像素，保护区内及 mask 外修改均为 0。

| 动作 | 各帧修改像素 | 新增暗芯实体像素 |
| --- | --- | --- |
| idle F00–F01 | 0 / 10 | 0 / 9 |
| collect F00–F03 | 5 / 80 / 71 / 0 | 0 / 11 / 11 / 0 |

body/pelvis 实体、肢体甲片、靴及其登记的透明轮廓保护均未改变。透明背景伪影不能通过 mask 和新增实体暗芯限制。collect F02 除近侧左臂外的固定排姿与 F01 相同，独立复算其共享接缝区域：5,930 个画布位置复用 F01 并与正式 F02 相符；该数量不是实体像素数。collect F03 与 idle F00、原母稿全 RGBA 相同。

三次 imagegen 源、实际输入及 prompt 哈希均绑定。第一版 collect 源 `0de7747a717c4aba7332fa39c083af4ef175d18ea612a2c437bef533bd012c30` 标为 `REJECTED_NOT_USED`，不参与正式六帧的独立重建；采用第二版的局部合法采样即可精确解释正式帧，未把整幅生成背景或重绘肢体带入正式层。

## 导出与播放器绑定

画布 64×96、root (32,80)。action metadata 内 15 张 PNG 与 atlas 对应区域全 RGBA 相同，源帧哈希、两份 atlas 字节一致；所有帧实体 Alpha=255、透空 RGBA=0，实体色属于固定 11 色。action atlas SHA `9262c6eac7fb6885d529ba6a39d3ecab01305aa1d9d7f2101ba84906e5211be7`。

冷加载的 SpriteFrames 具有 idle 2@2FPS loop、collect 4@6FPS nonloop、保留 walk 8@8FPS loop 与 pose 1 条身份参考；15 个 AtlasTexture 区域、单位 duration、外部 atlas 依赖均正确。八个 collect 动图也单次播放：GIF 实际不含 NETSCAPE 循环扩展，WebP 实际 total plays=1；没有仅凭导出账本的 `loop_encoded=1` 推断 GIF 会重复。`action-review.html` 读取包内 metadata/PNG，其资源及审阅链接在包内可解析；本轮未操作浏览器。

## 作者证据与独立冷验证

作者 30 张保存的 GPU 图（15 张资源×1/4×）独立与正式 PNG 的 nearest 放大逐像素比较，均全 RGBA 差为 0；作者 collect 结束 idle0 图也与正式 idle F00 相同。作者两循环、完整播放矩阵及 GPU 捕获属于已绑定作者证据，本轮没有宣称重跑。

本轮从固定 ZIP 新解压隔离副本，实际执行 Godot 4.7.2 headless 冷导入及原场景必要行为检查：**27/27 PASS**；导入 3.296s、探针 0.932s，均 exit 0/stderr 0。包括 4 条资源参数、15 个导入 atlas 区域的全 RGBA、root/Nearest，以及实际观察 collect [0,1,2,3]、恰一次 finished，由原处理函数使两处显示节点均回到 idle F00。858 个原载荷导入后哈希均保持。首次自有探针有类型推断错误，初始日志保留；只修正 TA 探针类型声明，重新从 ZIP 建立无缓存副本后完成上述结果，生产素材未修改。

上述独立 roundtrip 为导入资源的 `get_image()` 数据核验和实际 headless 播放行为，**不是新 GPU 帧缓冲捕获**。不重复作者 30 GPU 与两循环矩阵，不用技术一致性替代动作观感裁决。

独立证据：[technical-binding.json](technical-binding.json)、[technical-verify.py](technical-verify.py)、[technical-cold-receipt.json](technical-cold-receipt.json)、[technical-cold-probe.json](technical-cold-probe.json)、[technical-probe.gd](technical-probe.gd)。回执内 probe/log SHA 已独立复核；状态为 `FIXED_SOURCE_PATCH_EXPORT_AND_MINIMAL_COLD_PASS`。
