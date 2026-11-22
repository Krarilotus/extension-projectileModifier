# Custom Projectiles

自定义单位发射的弹药、射击频率与射程，以及它们优先攻击的目标。

## 使用方法

1. 如需正常游玩，请将 **弹射物配置文件（YAML）** 留空。
2. 将扩展文件夹或 ZIP 压缩包中的 `vanilla-projectiles.yml` 复制到游戏目录下的 `ucp/resources/custom-projectiles/`。如果该文件夹不存在，请先创建它，然后编辑副本并在 **自定义 > Balance Changes** 中选择该文件。
3. 重启游戏。

## 可实现的效果

将以下设置添加到你副本中对应的单位下。

### 减慢弓箭手装填速度

增加欧洲弓箭手两次射击之间的间隔。

```yaml
units:
  European archer:
    interval: 600
```

![欧洲弓箭手装填速度对比](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/archer-reload.jpg)

### 增加投石车射程

让投石车能够瞄准最远 40 格外的目标。

```yaml
units:
  Catapult:
    interval: 700
    range: 40
```

![投石车向远处目标开火](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/catapult-range.jpg)

### 一次发射更多石块

让塔楼投石机每次齐射发射十块石头。

```yaml
units:
  Mangonel:
    count: 10
    spread: 48
```

![飞行中的塔楼投石机齐射](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/mangonel-volley.jpg)

### 按目标选择弹药

让投石车在攻击敌方投石车时自动发射奶牛。

```yaml
units:
  Catapult:
    interval: 700
    ammo_by_target: {units: {Catapult: cow}}
```

![飞向敌方投石车的奶牛](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/catapult-ammunition.jpg)

*注：此为机器翻译，尚待人工审校。*
