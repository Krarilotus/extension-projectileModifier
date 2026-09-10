# Custom Projectiles 1.6.0

77 birim türünün tamamı için mermi türünü, salvo boyutunu ve otomatik atış aralığını seçin. Mancınıklar mangonel taşları atabilir; kuşatma kuleleri ve yakın dövüş birimleri otomatik menzilli saldırı kazanabilir.

Modül ZIP dosyasındaki vanilla-projectiles.yml dosyasını ucp/resources/custom-projectiles/ klasörüne kopyalayın, kopyayı düzenleyip burada seçin. Atlanan ayarlar değişmez; boş yol hiçbir değişiklik yapmaz. UCP zorunlu ve önerilen değer kuralları seçilen dosyanın tamamına uygulanır. Değişikliklerden sonra oyunu yeniden başlatın.

UCP 3.0.7+, map-extensions 1.x ve Crusader/Extreme 1.41 gerektirir. 33 ayarın ve 77 birim adının tamamı vanilla-projectiles.yml ve README.md dosyalarında açıklanır. Yerel test sürümüdür; oyun içi kabul testleri henüz tamamlanmamıştır.

İsabet: inaccuracy oyunun tam sayı koordinat birimlerini kullanır: 1 = 1/8 kare, 8 = 1 kare. 0 rastgele nişan hatasını kaldırır; belirtilmezse özgün isabet korunur. spread bağımsızdır.

Mancınık, trebuşe, mangonel ve balistalarda interval atış animasyonunu izler; animasyonu kısaltmaz. sync_to_animation: false bağımsız zamanlayıcıyı geri getirir. Güncellemeden sonra yeni oyun başlatın.
