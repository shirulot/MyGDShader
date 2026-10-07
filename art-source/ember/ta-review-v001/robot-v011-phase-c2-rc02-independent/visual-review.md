# 机器人 C2 rc02 独立视觉增量复审

2026-10-07。**SE collect F01/F02 外肘轮廓 P2 关闭，本轮局部视觉修复通过。** 新版恢复了原有外肘暗轮廓，在浅底不会再读成上方暗点和下方短线之间被背景截断；未确认新增的轮廓、身份或相邻帧问题。

绑定 ZIP SHA256：`64a3a18625dccc2fc1bde35ae44388a7acfb92ddb9aa4c83db811d2e5c10aa1b`。精确技术范围见 [integrity.md](integrity.md)。

## 实际观察

本次独立看完六张从固定包制作的诊断：SE collect 全四帧修前／修后的浅深底原生 1×、完整 4×，以及 raw rig／rc01／rc02 三行的外肘局部浅深底 12×。所有帧保持 64×96 原画布注册；局部 ROI 固定为 `(11,45)—(24,62)`，没有对单帧重新缩放或居中。浅底特意使用导致原问题最明显的 `#ece9d8`。

- [浅底原生1×](visual-se-collect-before-after-light-1x.png)、[深底原生1×](visual-se-collect-before-after-dark-1x.png)
- [浅底全身4×](visual-se-collect-before-after-light-4x.png)、[深底全身4×](visual-se-collect-before-after-dark-4x.png)
- [原rig／修前／修后浅底12×](visual-se-elbow-source-before-after-light-12x.png)、[原rig／修前／修后深底12×](visual-se-elbow-source-before-after-dark-12x.png)

旧版 `(14,51)` 的暗点和 `(14,55..56)` 的短暗段之间，三格不透明亮甲色曾与浅底融合。rc02 的 `(14,52..54)` 恢复原 rig 暗色后，外边重新连续；它仍是原有肘部轮廓，未扩大上／下臂体量，没有在两块甲片之间另外画一根细杆，也没有删除暗点或换背景来隐藏问题。

F01/F02 使用相同的外边修复，保持段不产生新的闪变；工具近臂的动作保持原样。F00/F03 的原有外肘、腕与工具关系逐帧对照无变化，F03 返回站姿没有额外线段。浅深底全身检查中，头胸、髋膝、踝靴与工具均延续 rc01；没有把局部修复扩成新的角色造型。

## 范围与结论

本分项继承 [rc01 的全部42新帧视觉审查](../robot-v011-phase-c2-rc01-independent/visual-review.md)；技术对比确认其余 110 张正式帧及母版／来源／姿态不变。此次只重看 SE collect 四帧与具体肘边，没有重复宣称重新审完全部 112 帧。

TA 的独立 headless 探针已确认 SE collect 完整顺序、一次完成及回 idle F00，但它属于行为验证。此分项没有控制浏览器或连续观察动画，主 TA 的实际网页正常／慢速复查由根单独记录；没有将静态联系图称为连续录像。

原 P2 的关闭依据是浅深底实际轮廓读感已恢复，同时六像素来源和相邻帧范围闭合。正式 C2 放行由主 TA 合并此前覆盖、S 中性专项和本次实际网页复查后签发。
