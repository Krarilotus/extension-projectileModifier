# Custom Projectiles 1.8.15

远程替换弹药：projectile_physics: {firethrower_pot: {mode: fixed_angle, angle: 30}} 让原游戏计算发射速度。需要启用 Rebalancer 1.1.3+ 并配置平衡文件。按类型全局生效，包括自定义贴图变体；native 保留原值。目标射程和碰撞规则仍有效。

修改玩法设置后仍可读取存档；模块旧的射击队列和计时器会重置。自定义图形定义必须保持一致。allow_config_changes_on_load: false 要求使用原设置。strict_range: false 也会关闭新的手动射击射程检查。

自动弹药：在 unit_groups 中定义目标列表，再为射手设置 ammo_by_target.groups: {siege: regular} 或 ammo_by_target.units: {Monk: cow}。单个兵种优先，其他目标保持原有行为。需要射击间隔；native 清除规则。附带 Reconquista 示例。

通过 YAML 配置全部 77 种单位。普通弹药和牛弹可分别设置。射击间隔遵循受支持的射击动画；inaccuracy 使用游戏原生单位：1 = 1/8 格，8 = 1 格，0 = 精确瞄准。

集群数量限制仅用于 AI；玩家仍可手动指定攻击目标。自动选择单位目标时，target_bias_tiles: {Monk: 3} 会在原生评分中将僧侣视为最多近三格；射程及其他游戏规则仍然生效。

从 ZIP 中复制完整的 vanilla-projectiles.yml，编辑后选择副本。native 保留游戏原有规则；路径留空则不作更改。auto_targeting: false 表示仅接受手动攻击命令。strict_range: false 恢复取整后的射程检查；turn_before_shot: false 关闭转向修正。必需/建议规则适用于整个文件的选择。编辑后请重启游戏。

自定义图像：在 projectiles 下添加名称，并设置 inherits 和 sprites（完整且匹配的 GM1 文件）。定义 decorations 及单位的 near_decorations 规则，再通过火盆按钮放置。格式参见 README.md 和 examples/custom-sprites-and-decorations.yml。 只能放在符合条件的城墙或塔楼上；庄园不能放置火盆。

需要 UCP 3.0.7+、Crusader/Extreme 1.41 及模块依赖项。测试版本；参见 VALIDATION.md。
