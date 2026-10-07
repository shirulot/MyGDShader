> 当前采集动作已由用户重新打开：v012锁腿不符合需求。最新为 [v013弯膝候选](revisions/collect-knee-v013/README.md) / [前后对照](http://127.0.0.1:8141/revisions/collect-knee-v013/compare.html)，等待视觉反馈。以下v012信息为历史记录。

# 机器人八向素材 · 当前使用 v012

采集膝盖修订已通过独立复审（PASS_NEW_COLLECT_POSES），八向32张采集帧通过，本轮膝盖扭曲问题关闭。结合保留的待机和行走，当前完整素材为24段112帧；16张采集前探／保持帧改变，其余96张PNG原字节保持。

- [当前素材包](../deliveries/robot_collect_knee_v012_rc01_2026-10-07.zip)
- [八向前后对照](http://127.0.0.1:8141/revisions/collect-knee-v012/compare.html)
- [当前完整动作预览](http://127.0.0.1:8141/revisions/collect-knee-v012/runtime/preview.html)
- [当前独立Godot工程](revisions/collect-knee-v012/runtime/project.godot)
- [正式复审回执与证据](../ta-review-v001/robot-collect-knee-v012-rc01-independent/review-collect-knee.md)
- [当前帧哈希与通过登记](source/current-robot-action-acceptance-v012.json)
- [当前动作规范](source/current-robot-action-contract.json)
- [修订来源、局部处理和验证说明](revisions/collect-knee-v012/README.md)

固定包保留送审时的“候选”标记，通过状态以包外正式回执和当前登记为准；不重写已审ZIP。SHA256：4dc7298a4b1f3782635bd461eca6dc2be1179e79b35dc4ecfa7ac04a6030f209。

旧v011采集仅作历史对照；其旧C2和迁移通过记录不能替代本次膝部复审。旧包及来源保留。主游戏的目标高度、交互距离与玩法接入尚未纳入本次交付。

历史来源见[README-full-actions.md](README-full-actions.md)、[WORKLOG.md](WORKLOG.md)与[JOINT-RULES.md](JOINT-RULES.md)。
