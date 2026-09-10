# Projectile Modifier

77 birim türünün tamamı için mermi türünü, salvo boyutunu ve otomatik atış aralığını seçin. Mancınıklar mangonel taşları atabilir; kuşatma kuleleri ve yakın dövüş birimleri otomatik menzilli saldırı kazanabilir.

**Balance Changes → Mermiler**

Bir grubu, ardından bir birimi açın. Sayısal bir değeri değiştirmek için kılıç kutusunu işaretleyin; yardımı görmek için ayarı genişletin. Devre dışı ayarlar dosyadaki değerleri veya özgün davranışı korur. Değişiklikleri uygulamak için oyunu yeniden başlatın.

Yakın dövüş birimleri ve kuşatma kuleleri dahil otomatik atışı etkinleştirir. Varsayılan olarak özgün atışların yerini alır. Özgün mermiyi, mermisi olmayan birimlerde ise okları kullanır. Oyun adımı milisaniye değil, bir simülasyon adımıdır.

Otomatik atış hedefleri. Müttefik birimler ve binalar hariç tutulur. Surlar kendi surlarınızı da kapsar. YAML dosyasında özel öncelik listeleri tanımlanabilir.

Hareket, gecikmeli salvolar, isabet, yükseklik ve animasyon gibi gelişmiş ayarlar için YAML dosyası yükleyin. Aşağıda etkinleştirilen ayarlar dosyadaki değerleri geçersiz kılar. Dosya olmadan temel ayarları kullanabilirsiniz. Örnekler ve tam tablo README.md dosyasında; düzenleme şeması projectile-config.schema.json dosyasındadır.

UCP 3.0.7+, map-extensions 1.x ve Crusader/Extreme 1.41 gerektirir. Zamanlayıcılar ve bekleyen salvolar kaydedilir; yüklemek için ayarların eşleşmesi gerekir. Bu imzasız 1.3.2 test sürümü, Monsterfish’in 1.2.0 sürümüne dayanır. Oyun içi, çok oyunculu ve kayıt modülü kabul testleri henüz tamamlanmamıştır; VALIDATION.md dosyasına bakın. Geliştirici başvuru belgesi İngilizcedir.
