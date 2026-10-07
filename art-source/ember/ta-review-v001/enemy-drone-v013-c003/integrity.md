# 无人机 c003：轻量静态绑定

结论：**STATIC_BINDING_PASS**，本轮封包、保留图和注册证据未发现缺口。仅核静态来源与数据，不代替根级造型裁决，不计为方向动画通过。

ZIP SHA256 `10ba6bfa175c1327869292252345b36410a36741b75b59d280781a4e8a9e3e3c`，898,781 bytes，20 文件＝19 payload＋manifest。独立重算安全路径、无重复/链接、CRC、19 项哈希/大小及当前冻结目录逐字节一致；固定副本位于 `package/`。

四格顺序为原 down、c002 front、SW、SE。前两张与旧独立固定 c002 包逐字节相同；down 又与 v012 实际 ZIP 的无人机 idle f00 PNG 逐字节相同：

| 原图 | SHA256 |
| --- | --- |
| neutral_down | `8996f4f7dc0a96fc3f81910d7fb4a91717ee30c36d83702c1a05bed48e645a33` |
| generated_front_c002 | `b24e4be8519218d63cef0432d93c1d25c6503a05fd25724cede033f4ea092d95` |

四张清洁图均为 128²、Alpha 0/255。catalog 路径、SHA、实际 output 与 native QA 一致；四格深浅 1×图及最近邻 4×图与实际 PNG 合成全 RGBA 零差，不重排 bbox。

两斜向共同使用源 `c003r1` SHA `6998ebcde01124af54234c989f4ea0fe830785ca62dbb459da5c265fa5ee32d2`，两个 887² source_rect 均在原图内。登记 scale 独立重算等于 `26/244 × 724/887 = 0.08697580719685068`；只有统一比例和单次 anchor 平移，target 小探头点为 (64,80)，地面根合同为 (64,104)。轴心与 catalog 重算误差低于 0.0001 px，轴差约 SW (30.680,11.069)、SE (30.577,10.993)；这些数字仅核算登记，不作为机械造型阈值。

`axis_guides_8x.png` SHA 和 2048×1024 尺寸已绑定，8×最近邻块一致；未重跑 GPU 绘制参考线。原 c003、内部 r1 源图和各自提示词共 4 项均与 source_provenance 指向的实际原文件哈希一致，未把初稿当最终源。

本轮没有启动 Godot、导出器、浏览器或修改生产。逐项 SHA、Alpha、bbox 诊断和数学登记见 [integrity.json](integrity.json)，独立脚本见 [verify_integrity.py](verify_integrity.py)。
