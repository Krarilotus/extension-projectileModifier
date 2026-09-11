# Custom Projectiles 1.8.4

通过 YAML 配置全部 77 种单位。普通弹药和牛弹可分别设置。射击间隔遵循受支持的射击动画；inaccuracy 使用游戏原生单位：1 = 1/8 格，8 = 1 格，0 = 精确瞄准。

集群数量限制仅用于 AI；玩家仍可手动指定攻击目标。

将模块 ZIP 中的 vanilla-projectiles.yml 复制到 ucp/resources/custom-projectiles/，编辑副本后在此选择。省略的设置保持不变；路径为空时不做任何更改。UCP 的必需值和建议值规则适用于整个文件选择项。修改后请重新启动游戏。

自定义图像：在 projectiles 下添加名称，并设置 inherits 和 sprites（完整且匹配的 GM1 文件）。定义 decorations 及单位的 near_decorations 规则，再通过火盆按钮放置。格式参见 README.md 和 examples/custom-sprites-and-decorations.yml。 只能放在符合条件的城墙或塔楼上；庄园不能放置火盆。

需要 UCP 3.0.7+、Crusader/Extreme 1.41 及模块依赖项。测试版本；参见 VALIDATION.md。
