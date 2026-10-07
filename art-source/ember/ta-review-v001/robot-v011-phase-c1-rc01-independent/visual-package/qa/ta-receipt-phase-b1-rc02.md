# 机器人 v011 阶段 B1 rc02 TA 正式回执

日期：2026-10-07。结论：**PASS，仅本批 NW / N / NE / SE 四条 walk，共32帧。** NE/SE同侧手脚同向的旧P2关闭，N纵向腕目标与关节投影修订可接受；NW在本批正式通过。既有阶段A S/SW及八向身份参考保持原结论。

固定 ZIP：`robot_eight_way_v011_phase_b1_rc02_2026-10-07.zip`，14,354,117 B；SHA256 `b301fdea0e3f634d02a0da4eac437e1ce890515b582216daadc82c82211b4aaf`，696条目/695载荷。manifest SHA256 `b5b7c17e7a8574927dc7bfcab871a6a55e1a41da6a3e52c3fa230b955864f9c0`，atlas SHA256 `137196518cba1eabfcb8b58579a33fe493ad6865ed8304426f98414ff6a42f01`。

## 旧问题关闭与实际观感

NE/SE F00→F04 同侧腕/踝按行进方向投影已反相；根复看三修订方向全部八帧联系图，并在固定播放器核正常8FPS、慢放2FPS的原生/4×画面、接触帧与末首步进。手臂与腿交错关系落实，N不再沿用未明确的横向摆臂。肩肘腕、髋膝踝和固定甲片未确认新断接、跳形或逐帧设计变化。SE↔S固定F03切向保持索引，未见无因比例或根注册跳动。

NW本轮正常播放与rc01已完成的全帧视觉结果结合，并由字节保持核验证明仍是同一八帧。rc01仍保留整包退回历史；本次才给NW新的正式动画通过。

弱运动指标仍保留为观察，未仅凭骨长、连通性或分数放行。浏览器观察是离散画面，不称为根独立录像或两圈GPU全帧回放。详细操作与边界见[根视觉/浏览器记录](root-preview.md)。

## 独立技术与资源验证

695载荷完整。实际仅N/NE/SE24张最终walk修改，S/SW/NW24张walk加八张身份图共32张保持字节。NE源(22,59)的原RGBA从body归还arm_left_lower，中性源片实拼RGBA零差，其余源像素未重画。三向24帧的固定部件重建、补丁合成、修订mask及刚性保护独立核对均闭合；范围外相对rc01改动0。

56张PNG与atlas/TRES逐格RGBA一致。独立Godot4.7.2 headless冷导入、14 clips/56格解码及预览实例化通过，错误0；1×/4×nearest与root偏移正确。作者112张GPU、六向两轮和32次切向仅做文件/图集绑定，未宣称TA独立重跑。包内阶段A旧cold_delivery_validation_rc02.json不作为当前B1冷验。

详见[独立完整性报告](integrity.md)、[最小冷加载](minimal-cold-load.json)。

## 后续生产范围

允许继续剩余W/E walk和八向idle2/collect4，按认可母版、同一部件/关节路线分批提交。最终目标保持八向idle2/walk8/collect4，共24段112帧；当前仅六向walk48帧与身份参考已过，W/E walk和最终idle/collect未完成验收。不得把单张pose当双帧idle通过，亦不得让本批PASS覆盖未来帧。
