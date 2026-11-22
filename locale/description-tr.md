# Custom Projectiles

Birimlerin ne ateşlediğini, ne sıklıkla ve ne kadar uzağa atış yaptığını ve hangi hedefleri tercih ettiğini değiştirin.

## Nasıl kullanılır

1. Normal oyun için **Mermi yapılandırma dosyası (YAML)** alanını boş bırakın.
2. Eklenti klasöründen veya ZIP dosyasından `vanilla-projectiles.yml` dosyasını kopyalayın, kopyayı düzenleyin ve **Özelleştirmeler > Balance Changes** altından seçin.
3. Oyunu yeniden başlatın.

## Neler yapabilirsiniz

Bu ayarları kopyanızdaki ilgili birimin altına ekleyin.

### Okçuların yeniden doldurmasını yavaşlatma

Avrupalı okçuların atışları arasındaki süreyi artırın.

```yaml
units:
  European archer:
    interval: 600
```

![Avrupalı okçuların yeniden doldurma karşılaştırması](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/archer-reload.jpg)

### Mancınıklara daha fazla menzil verme

Mancınıkların 40 kareye kadar uzaklıktaki hedeflere nişan almasını sağlayın.

```yaml
units:
  Catapult:
    interval: 700
    range: 40
```

![Uzaktaki bir hedefe ateş eden mancınık](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/catapult-range.jpg)

### Aynı anda daha fazla taş fırlatma

Her mangonel yaylım atışının on taş fırlatmasını sağlayın.

```yaml
units:
  Mangonel:
    count: 10
    spread: 48
```

![Havada uçan mangonel yaylım atışı](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/mangonel-volley.jpg)

### Hedefe göre mühimmat seçme

Mancınıkların düşman mancınıklarına otomatik olarak inek fırlatmasını sağlayın.

```yaml
units:
  Catapult:
    interval: 700
    ammo_by_target: {units: {Catapult: cow}}
```

![Düşman mancınığına doğru fırlatılan bir inek](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/feature/target-ammunition/docs/screenshots/catapult-ammunition.jpg)

*Not: Bu metin makine çevirisidir ve insan incelemesi beklemektedir.*
