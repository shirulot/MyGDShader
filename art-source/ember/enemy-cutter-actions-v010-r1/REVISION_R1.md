# v010-r1：只修审阅观察区域

TA指出原浏览器/联系图Rect(32,32,88,80)在死亡后段漏掉x30–31圆锯边缘。正式128×128 PNG、五张图集和SpriteFrames完整。

本修订统一辅助观察区为Rect(24,32,80,80)，与verify.gd相同。浏览器原生宽80、4×宽320；export.gd的联系图路径同步改正以确保今后可重建。本次实际仅执行rebuild_contacts.gd读取冻结图集重建深浅底1×/4×联系图，没有重跑rig或改动画像素。

qa/preview_crop_audit_r1.json记录30帧新观察区外有效像素全部为0；qa/unchanged_art_r1.json逐项绑定旧/新30帧、五图集及资源/rig/源文件SHA。验证与GPU播放证据沿用完全相同的原始动作catalog，旧冷导入凭据由qa/inherited_validation_r1.json明确指向，不冒称本修订重新跑了GPU。

原v010包保留。此修订仍需TA关闭预览P2后才能通过。
