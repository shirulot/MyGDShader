# v013 弯膝动作参考

用户明确要求使用机器人已有膝关节。v012 的站立支撑不符合动作需求，不能以此前技术/视觉回执替代这次用户验收。

- Jonasz O., Character Sprites Prototype Template Animation：https://jonasz-o.itch.io/character-sprites-prototype-template-animation 。查看公开的七帧下蹲预览 `jonasz-crouch-public.gif`，拆帧仅供观察。观察：髋部下沉，膝向角色前方走，大腿与小腿有明确折角；身体前倾配合重心。角色像素不复制到本项目。
- VanillaLoop, Item Pickup Set：https://www.fab.com/listings/38420cbf-0776-4a95-aab7-685564215b28 。查看公开 Crouch 宣传图，观察低位拾取的支撑与不同朝向。仅动作分析，没有购买、导入、复用其模型或动画；该图片不作为 imagegen 输入，也不随生产包分发。
- Meshy, Collect Object：https://www.meshy.ai/animation-library/daily-actions/picking-up-item/collect-object 。发现了可旋转的动作预览，但本轮浏览器控制超时；未把未实际观看的动态预览算作验证。

## 本项目采用的设计推论

1. 膝盖在角色自身前后平面弯曲。八方向改变这个平面的投影，不能把屏幕左右当作关节弯曲轴。
2. 保留浅蹲：髋后移 0.7、下沉 2.4 个原生像素；脚掌固定。侧面显出折角，正背面用腿段缩短和遮挡表达深度。
3. 原生 64×96、原锚点 (32,80)、原四帧/6FPS 单次采集暂不变；F1/F2 共用腿姿，仅工具臂保留不同的动作阶段。
4. imagegen 只参与本项目源部件排姿后的关节修形；待机、行走、采集首尾保留。新候选不能自动标记为用户已认可。
