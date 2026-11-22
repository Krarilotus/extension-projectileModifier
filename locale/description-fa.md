# Custom Projectiles

تغییر دهید که واحدها چه چیزی شلیک کنند، با چه فاصله و تا چه بردی تیر بیندازند و کدام هدف‌ها را در اولویت قرار دهند.

## نحوهٔ استفاده

1. برای بازی عادی، **فایل تنظیمات پرتابه (YAML)** را خالی بگذارید.
2. فایل `vanilla-projectiles.yml` را از پوشهٔ افزونه یا فایل ZIP کپی کنید، نسخهٔ کپی را ویرایش کنید و آن را در **شخصی‌سازی‌ها > Balance Changes** انتخاب کنید.
3. بازی را دوباره اجرا کنید.

## کارهایی که می‌توانید انجام دهید

این تنظیمات را به واحد متناظر در نسخهٔ کپی خود اضافه کنید.

### کند کردن زمان بارگذاری کمانداران

به کمانداران اروپایی بین هر شلیک زمان بیشتری بدهید.

```yaml
units:
  European archer:
    interval: 600
```

![مقایسهٔ زمان بارگذاری کمانداران اروپایی](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/archer-reload.jpg)

### افزایش برد منجنیق‌ها

به منجنیق‌ها اجازه دهید هدف‌هایی تا فاصلهٔ ۴۰ خانه را نشانه بگیرند.

```yaml
units:
  Catapult:
    interval: 700
    range: 40
```

![شلیک منجنیق به یک هدف دوردست](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/catapult-range.jpg)

### پرتاب سنگ‌های بیشتر در هر نوبت

کاری کنید هر رگبار منجنیق برجی ده سنگ پرتاب کند.

```yaml
units:
  Mangonel:
    count: 10
    spread: 48
```

![رگبار منجنیق برجی در حال پرواز](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/mangonel-volley.jpg)

### انتخاب مهمات بر اساس هدف

کاری کنید منجنیق‌ها به‌طور خودکار به سمت منجنیق‌های دشمن گاو پرتاب کنند.

```yaml
units:
  Catapult:
    interval: 700
    ammo_by_target: {units: {Catapult: cow}}
```

![گاوی که به سمت یک منجنیق دشمن پرتاب شده است](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/catapult-ammunition.jpg)

*توجه: این یک ترجمهٔ ماشینی است و در انتظار بازبینی انسانی قرار دارد.*
