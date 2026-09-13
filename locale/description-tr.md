# Custom Projectiles 1.8.6

77 birim türünün tamamını YAML ile ayarlayın. Normal mühimmat ve inekler ayrı ayarlanır. Aralıklar desteklenen atış animasyonlarına uyar; inaccuracy yerel oyun birimlerini kullanır: 1 = 1/8 karo, 8 = 1 karo, 0 = tam isabetli nişan.

Hedef grubu eşiği yalnızca yapay zekâ için geçerlidir; oyuncular saldırı hedefini elle seçebilir.

ZIP içindeki eksiksiz vanilla-projectiles.yml dosyasını kopyalayın, düzenleyin ve kopyayı seçin. native oyunun kurallarını korur; boş yol hiçbir şeyi değiştirmez. auto_targeting: false yalnızca elle verilen saldırı emirlerine izin verir. strict_range: false yuvarlanmış menzil denetimlerini geri getirir; turn_before_shot: false dönüş düzeltmesini kapatır. Zorunlu/önerilen, dosya seçiminin tamamına uygulanır. Düzenledikten sonra oyunu yeniden başlatın.

Özel görseller: projectiles altında inherits ve sprites içeren bir ad ekleyin (tam ve uyumlu GM1 dosyası). decorations ve birimlerin near_decorations kurallarını tanımlayın; mangal düğmesiyle yerleştirin. Biçimler: README.md ve examples/custom-sprites-and-decorations.yml. Uygun surlara veya kulelere yerleştirin; malikânelere yerleştirilemez.

UCP 3.0.7+, Crusader/Extreme 1.41 ve modül bağımlılıkları gerekir. Test sürümü; bkz. VALIDATION.md.
