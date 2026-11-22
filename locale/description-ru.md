# Custom Projectiles

Настраивайте, чем стреляют юниты, как часто и далеко они бьют и каким целям отдают предпочтение.

## Как использовать

1. Оставьте поле **Файл настроек снарядов (YAML)** пустым для обычной игры.
2. Скопируйте `vanilla-projectiles.yml` из папки расширения или ZIP-архива, отредактируйте копию и выберите её в разделе **Настройки > Balance Changes**.
3. Перезапустите игру.

## Что можно сделать

Добавьте эти параметры к нужному юниту в вашей копии.

### Замедлить перезарядку лучников

Увеличьте паузу между выстрелами европейских лучников.

```yaml
units:
  European archer:
    interval: 600
```

![Сравнение перезарядки европейских лучников](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/archer-reload.jpg)

### Увеличить дальность катапульт

Позвольте катапультам наводиться на цели на расстоянии до 40 клеток.

```yaml
units:
  Catapult:
    interval: 700
    range: 40
```

![Катапульта стреляет по дальней цели](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/catapult-range.jpg)

### Выпускать больше камней за раз

Сделайте так, чтобы каждый залп мангонели выпускал десять камней.

```yaml
units:
  Mangonel:
    count: 10
    spread: 48
```

![Залп мангонели в полёте](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/mangonel-volley.jpg)

### Выбирать боеприпасы в зависимости от цели

Настройте катапульты так, чтобы они автоматически метали коров во вражеские катапульты.

```yaml
units:
  Catapult:
    interval: 700
    ammo_by_target: {units: {Catapult: cow}}
```

![Корова летит во вражескую катапульту](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/catapult-ammunition.jpg)

*Примечание: это машинный перевод, ожидающий проверки человеком.*
