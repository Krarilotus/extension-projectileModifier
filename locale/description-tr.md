# Custom Projectiles

Birimlerin ne ateşlediğini, ne sıklıkla ve ne kadar uzağa atış yaptığını ve hangi hedefleri tercih ettiğini değiştirin.

## Nasıl kullanılır

1. Normal oyun için **Mermi yapılandırma dosyası (YAML)** alanını boş bırakın.
2. `vanilla-projectiles.yml` dosyasını eklenti klasöründen veya ZIP dosyasından oyunun `ucp/resources/custom-projectiles/` klasörüne kopyalayın. Gerekirse klasörü oluşturun, kopyayı düzenleyin ve **Özelleştirmeler > Balance Changes** altında seçin.
3. Oyunu yeniden başlatın.

## Neler yapabilirsiniz

Kopyanızda ilgili birimi bulun ve `native` değerlerini gösterilen değerlerle değiştirin.

### Okçuların yeniden doldurmasını yavaşlatma

Avrupalı okçuların atışları arasındaki süreyi artırın.

```yaml
units:
  European archer:
    interval: 600
```

### Mancınıklara daha fazla menzil verme

Mancınıkların 40 kareye kadar uzaklıktaki hedeflere nişan almasını sağlayın.

```yaml
units:
  Catapult:
    interval: 700
    range: 40
```

### Aynı anda daha fazla taş fırlatma

Her mangonel yaylım atışının on taş fırlatmasını sağlayın.

```yaml
units:
  Mangonel:
    count: 10
    spread: 48
```

![Havadaki bir Mangonel salvosu](https://raw.githubusercontent.com/Krarilotus/extension-projectileModifier/534bfdd4d0c01dfdefece636841d2fc336bc0ddb/docs/screenshots/mangonel-volley.jpg)

### Hedefe göre mühimmat seçme

Mancınıkların düşman mancınıklarına otomatik olarak inek fırlatmasını sağlayın.

```yaml
units:
  Catapult:
    interval: 700
    ammo_by_target: {units: {Catapult: cow}}
```

## Diğer eklentiler

Smarter Walls, Improved Siegeengines veya Improved Tunnelers kullanıyorsanız, yükleme sırasında bunları Custom Projectiles'tan önceye koyun.

*Not: Bu metin makine çevirisidir ve insan incelemesi beklemektedir.*
