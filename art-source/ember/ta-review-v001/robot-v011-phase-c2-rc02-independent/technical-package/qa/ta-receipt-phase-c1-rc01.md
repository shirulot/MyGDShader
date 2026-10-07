# 机器人 v011 C1 rc01 TA 正式回执

2026-10-07。结论：**PASS，仅SW/down_left新增idle2、collect4，共两条六帧。** 已过八向walk64帧及8张身份母版逐字节保持。当前最终动作目标中的10条70帧通过，余下七向idle/collect共14条42帧仍待生产和独立验收，单张pose不计idle。

固定 ZIP `robot_eight_way_v011_phase_c1_rc01_2026-10-07.zip`，19,576,548 B，858载荷+manifest，SHA256 `0c62177198973b24bb3fbfcc306ba4617af3ad754eb5a0696bdfddb4f19f51df`。action metadata SHA256 `44083663252fcf5447ba63d2bf0bdb453ba80d2da24f36d8f8663f0d96433214`，action atlas SHA256 `9262c6eac7fb6885d529ba6a39d3ecab01305aa1d9d7f2101ba84906e5211be7`。

六帧完整深浅原生/4×及肩肘、腰髋、膝踝共同ROI深浅8×已实际审查。待机上身微动由原腰部暗芯承接；采集下探屈膝、双靴支撑和近侧左腕工具动作可读，F01/F02固定身体/腿部未出现贴片跳变、亮缝、关节断开或鞋重画。F02→F03回位完整，F03与idle F00全RGBA相同。动作幅度克制，本小样不声称验证了具体场景采集目标或判定。

根在固定网页查看正常/四分之一速度、深浅底、1×/4×并列，单步核F01/F02/F03与idle末首，并确认采集正常结束回idle。独立技术核验858载荷、原12片、中性组合、定长腿与固定踝点、六帧排姿及接缝合成全RGBA零差。idle修改0/10、collect5/80/71/0点，保护区及mask外零差；拒绝的采集首稿和第二稿背景伪影没有进入最终层。F01/F02共同排姿区域共享补丁，不让AI逐帧另画刚性部件。

15张资源PNG/atlas/TRES与动作参数通过；独立Godot冷验证27/27，实际collect依次0→1→2→3且恰一次finished后回idle F00，858原载荷保持。作者保存的30张GPU图已独立逐像素比对为零差，本轮未重跑GPU/两圈完整矩阵，也未把离散浏览器截图称为连续录像。

证据：[独立全帧视觉](visual-review.md)、[来源/补丁与独立冷验](integrity.md)、[根浏览器](root-preview.md)、[冷验27/27](technical-cold-receipt.json)。允许按已验证方法继续补其余七向idle/collect并分批送审，S需先建立双脚中性支撑，不能沿用walk F02冒充idle。既有通过文件保持，新增动作不得自动继承通过。
