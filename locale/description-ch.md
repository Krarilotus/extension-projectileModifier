# Custom Projectiles 1.7.0

为全部 77 种单位设置弹射物类型、齐射数量及自动射击间隔。投石车可以发射散射投石器的石弹；攻城塔和近战单位也能获得自动远程攻击能力。

将模块 ZIP 中的 vanilla-projectiles.yml 复制到 ucp/resources/custom-projectiles/，编辑副本后在此选择。省略的设置保持不变；路径为空时不做任何更改。UCP 的必需值和建议值规则适用于整个文件选择项。修改后请重新启动游戏。

需要 UCP 3.0.7+、map-extensions 1.x 和 Crusader/Extreme 1.41。全部 33 项设置和 77 个单位名称均在 vanilla-projectiles.yml 和 README.md 中说明。本版本为本地测试候选版，实际游戏验收仍待完成。

精度：inaccuracy 使用游戏原生整数坐标单位：1 = 1/8 格，8 = 1 格。0 消除随机瞄准误差；省略则保留原版精度。spread 独立生效。

支持原生射击计时的单位（参见 README.md）：interval 按射击动画计时，不会缩短动画。sync_to_animation: false 恢复独立计时器。更新后请开始新游戏。
