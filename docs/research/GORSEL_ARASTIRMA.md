> Tarihsel araştırma/önceki çalışma notu. Eski çıktı yolları güncel değildir. Güncel envanter: [FOTO_ENVANTERI.md](../FOTO_ENVANTERI.md); kullanım: [README](../../README.md).

# Şimşek Mobilya görsel araştırması

**Güncelleme:** Tek tek inceleme sonrası sınıflandırma 48 referans / 30 doğrudan çekim /
1 logo olarak düzeltildi. Benzer alternatifler ve yalnızca alttan kırpma kullanılarak
43 fotoğraf + logo içeren temiz havuz hazırlandı. Güncel sonuç ve doğrulama:
[KATALOG_SECIMI.md](KATALOG_SECIMI.md). Aşağıdaki ilk arama sayıları önceki aşamanın
geçmişidir; güncel katalog seçiminde 79 girdinin tamamının karşılığı var.

İnceleme: 13 Kasım 2026, Europe/Istanbul. Her ZIP'in tüm görselleri teknik olarak
okundu; görsel içerik değerlendirmesi için sabit seed=42 ile paket başına 2–3 örnek
seçildi. Dosya dosya sanat yönetimi yapılmadı. Site tasarımı bu aşamanın kapsamı değil.

## Eldeki malzeme

| ZIP son eki | Fotoğraf | Video | Örneklerde görülen içerik | Fotoğraf boyutları |
|---|---:|---:|---|---|
| `1.11.50 AM` | 60 | 0 | 48 referans ekran görüntüsü ve 12 doğrudan uygulama/üretim çekimi | Genişlik 720–2048, yükseklik 1200–2048 px |
| `1.11.52 AM` | 3 | 1 | Işıklı TV ünitesi ve aynalı antre uygulamaları | 1200×1600 veya 1600×1200 |
| `1.11.56 AM` | 3 | 0 | Mor LED'li TV duvarı, aynı uygulamanın farklı açıları | 2040×1536 |
| `1.11.58 AM` | 6 | 0 | Atölyede üretim, benzer ardışık çekimler | 1536×2048 |
| `1.12.04 AM` | 2 | 1 | Beyaz mutfak uygulaması; telefon/tarih damgası | 1600×1204 |
| `1.12.06 AM` | 4 | 0 | TV ünitesi ve ayna/antre uygulamaları | 1200×1600 veya 1600×1200 |

ZIP'lerde 78 fotoğraf ve 2 video var. Ayrı logo görseliyle toplam 79 fotoğraf,
2 video, yani 81 medya dosyası. ZIP içindeki 78 fotoğrafta birebir SHA-256 tekrarı yok;
görsel olarak çok benzer çekimler var. Videolar sayıldı ve korunarak çıkarıldı;
içerik/kurgu incelemesi yapılmadı.

Logo dosyası `WhatsApp Image 2026-11-12 at 10.47.33 PM.jpeg`: **1290×1539 JPEG**.
Şeffaf PNG yok. Görselde “ŞİMŞEK MOBİLYA TASARIM DEKORASYON” kimliği var.
PNG'ye çevirmek kayıp ayrıntıyı geri getirmez veya arka planı şeffaf yapmaz.
Başlıkta kullanılacak küçük, okunaklı sürüm için yazı ve işaretin temiz bir vektör
uyarlaması ayrı çalışma olmalı; mevcut tasarım korunmalı. Telefonu müşteri teyidinden
sonra HTML metni olarak yazmak, görseldeki küçük rakamları büyütmekten daha okunaklı olur.

## Pinterest orijinallerini bulma

Ekran görüntülerinde pin URL'si yok. WhatsApp dosya adı veya fotoğraf özeti üzerinden
Pinterest adresi hesaplanamaz. Fotoğraftaki nesnelerle tersine görsel arama gerekir.
Google'ın [görselle arama yardımında](https://support.google.com/websearch/answer/1325808?hl=en)
da yerel dosya yükleme akışı anlatılır. Bu oturumdaki Google Lens denemesi olağandışı
trafik doğrulamasına takıldı. Kontrol aşılmaya çalışılmadı. Yandex görselle arama
yükleme ve sonuç akışı bu bağlantıda çalıştı.

Hazırlanan script referans ekran görüntüsünden bir arama kırpımı üretir; yalnızca
`reference` grubunu Yandex'e yükler. Dönen görsel URL'lerinde Pinterest varsa
`/originals/` varyantını dener. Bu davranış, gallery-dl'nin
[Pinterest çıkarıcısındaki](https://github.com/mikf/gallery-dl/blob/master/gallery_dl/extractor/pinterest.py)
`images.orig` ve `/originals/` kullanımına dayanır. Boyut ve gerçek görsel çözümlemesi
indirme sonrası yapılır; daha büyük dosya boyutu tek başına kalite ölçütü değildir.

Canlı doğrulama örneği: Pinterest ekran görüntüsü #2, **720×1600**; asıl fotoğraf
ekranda yaklaşık 706×940 px alan kaplıyor. Bulunan
[Pinterest dosyası](https://i.pinimg.com/originals/3f/28/eb/3f28eb57f5045e5ccbeb3116b313efdd.jpg)
**1086×1448** ve telefon arayüzü içermiyor.
[İndekste görünen pin](https://ru.pinterest.com/pin/1093882197025349961/) kaynak
adayı olarak kaydedildi. Görsel eşleşmesi yerel ayrıntılar, geometrik dönüşüm ve
hizalanmış piksel korelasyonuyla geçti. Bu, ilk üreticinin veya çekim dosyasının
bulunduğu anlamına gelmiyor. Toplu çalışmanın güncel sayıları `artifacts/catalog/summary.json`
dosyasında; her indirme ve başarısız aday `matches.json` içinde.

Bu oturumun son sonucu: **60 referansın tamamı arandı; 25'inde görsel eşleşmesi
geçen dosya indirildi, 35'i `needs_review` kaldı.** Seçilen 25 dosyanın 16'sı
Pinterest CDN `originals`, 9'u diğer eşleşen çevrimiçi kopyalardır. 12 seçili kayıtta
format/doğrudan dosya alternatifleri de denendi. Örneğin #6'nın 736×1097 kopyası
848×1264 PNG ile, #34'ün 401×601 önizlemesi 1200×1800 dosyayla iyileştirildi.

#54'te aynı fotoğraf bulundu fakat dosyanın altında sosyal medya yorum çubuğu var;
bu, temiz fotoğraf orijinalinin bulunduğu anlamına gelmiyor. Yerel inceleme sayfasında
bu not ve arama kırpımından daha az piksel içeren dosyalar ayrıca gösteriliyor.
Bulunanların tamamı insan tarafından yayına uygun olarak onaylanmış değildir.

Son doğrulama: 7 otomasyon testi geçti; kaynak ve çıkarılmış dosya özetleri aynı;
seçilen 25 dosyanın görsel eşleşmesi tekrar geçti. Yerel inceleme aracı 81 kartla,
kırık görsel/JavaScript hatası olmadan masaüstü ve 390 px genişlikte kontrol edildi.

Ekran görüntüsü #8'de “Tadilat Ehli” adı okunuyor; aramada bulunan
[firma sitesi](https://tadilatehli.com/) bir kaynak ipucu. Aynı görselin orijinalinin
orada bulunduğu doğrulanmadı. İsim benzerliğiyle otomatik yazarlık ataması yapılmadı.

## Bu fotoğraflar için önerilen iyileştirme

En büyük kazanç, efekt eklemekten önce doğru kaynak ve doğru kare seçiminden gelir.
Örneklerdeki uygulama çekimleri zaten 1200–2040 px genişlikte; küçük/orta katalog
kartlarında yapay büyütme gerektirmeyebilir. Pinterest ekran görüntülerinde ise
önce daha temiz kaynak dosyası tercih edilmeli.

Önerilen düzenleme sırası:

1. Aynı uygulamadan en net ve en düzgün açıyı seç; bir geniş plan ve bir detay yeterli.
   Atölye fotoğraflarında ardışık benzer kareleri tek güçlü üretim sahnesine indir.
2. TV ünitesi/dolap kenarlarını referans alarak ufku ve dikeyleri düzelt. Tüm çizgileri
   zorla dikleştirmek yerine doğal görünümü koru. darktable'ın
   [rotate and perspective](https://darktable-org.github.io/dtdocs/en/module-reference/processing-modules/rotate-perspective/)
   modülü bu iş için uygun; otomatik düzeltme sonrası gözle kontrol gerekir.
3. Beyaz dolap/duvarı referans alarak genel beyaz dengesini ayarla. Mor ve sarı LED'in
   gerçek atmosferini tamamen silme; mümkünse bölgesel maske kullan. Genel renk
   düzeltmesi ile yaratıcı renk düzenlemesi ayrılmalı; araçların işlevleri
   [color calibration](https://darktable-org.github.io/dtdocs/en/module-reference/processing-modules/color-calibration/)
   ve [color balance RGB](https://github.com/darktable-org/dtdocs/blob/master/content/module-reference/processing-modules/color-balance-rgb.md)
   belgelerinde açıklanıyor.
4. Karanlık dolap yüzeylerini hafifçe aç, LED çevresindeki aşırı parlaklığı yumuşat.
   Tamamen beyaza patlamış bir JPEG alanında gerçek ayrıntı geri getirilemez.
5. Düşük miktarda gürültü/JPEG temizliği ve çıkış boyutunda hafif keskinleştirme uygula.
   Ahşap damarları, kapak aralıkları ve kulplar %100 yakınlaştırmada korunmalı.
6. Son kadrajı seç. Telefon damgası bu örneklerde alt kenarda; ürün tabanı kesilmeden
   kırpılabiliyorsa bunu tercih et. Ürünü kesen damga veya başka üreticinin filigranı
   varsa temiz bir kaynak ara. Başka üreticinin yazısını silerek kendi işimiz gibi sunma.
7. Düzenlenmiş ana kopyayı sakla; WebP/AVIF gibi dağıtım kopyalarını en son üret.

Bu maddeler örneklere dayalı çalışma önerileridir. Her görsele aynı otomatik filtre
uygulanmadı; renk, perspektif ve yayın kadrajı henüz tek tek onaylanmış değil.

## Kadraj ve site üzerindeki efektler

| Kullanım | Önerilen başlangıç | Bu malzemede dikkat |
|---|---|---|
| Yatay uygulama kartı | 4:3 | TV ünitesi ve mutfak tezgâhının iki ucu görünmeli |
| Dikey antre/atölye | 3:4 veya doğal oran | Aynayı ve çalışan kişinin ellerini kesme |
| Açılan büyük fotoğraf | Doğal oran, `object-fit: contain` | Kart kadrajının dışındaki ürün ayrıntısı da görülsün |
| Ana karşılama görseli | Yeterli kaynak varsa 16:9; gerekirse iki sütunlu düzen | Dikey referansı zorla yataya kesme |

Her fotoğraf için ayrı odak noktası ve mobil kadraj tanımlanabilir. `object-fit: cover`
kartta kullanılabilir; ana dosyayı değiştirmez, fakat ürünün bir kısmını gizleyebilir.
İnce çerçeve, açık sıcak zemin, küçük hover yakınlaşması ve ölçülü gölge iyi başlangıç.
Başlık okunurluğu için gereken degradeyi CSS katmanında tut. Sabit koyu filtre,
ağır vignette, aşırı HDR/clarity, yoğun sarı LUT ve yapay alan derinliği mobilyanın
gerçek renk ve yüzey algısını bozar. Hareket efektleri azaltılmış hareket tercihine
uymalı.

Markanın mevcut krem/koyu ahşap tonları görselleri çevreleyen arayüzde kullanılabilir.
Ürünün rengini bu palete uydurmak için fotoğrafı boyamak önerilmez.

## Yapay zekâ ile büyütme

[Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) JPEG bozulmaları ve düşük
çözünürlüklü genel fotoğraflar için denenebilir. Genel sahne modelinin denoise ayarı,
aşırı yumuşatmayı azaltmak için kullanılabilir. Bu projede ilk tercih kaynak dosyasını
bulmak; büyütme yalnızca temiz kaynak bulunamayan seçili karelerde A/B denemesi olmalı.

Önerim: gerekiyorsa 2× çıktıyı orijinalle yan yana incele; ahşap damarı, mermer,
derz, kapak aralığı, kulp ve yazı şekillerini kontrol et. Bunlar başlangıç önerisi,
bu fotoğraflar için ölçülmüş en iyi model/ayar değildir. GAN tabanlı büyütmede gerçek
dışı ayrıntı ve yapı bozulması olabileceğini
[DeSRA araştırması](https://arxiv.org/abs/2307.02457) da inceliyor.

Üretken yeniden dekorasyon veya boş alan doldurma, yapılmış işin belgesini değiştirir;
böyle bir çıktı hazırlanırsa ayrı tasarım görselleştirmesi olarak ele alınmalı.
Bu çalışmada AI düzenleme, model indirme veya toplu upscale yapılmadı.

## Web'e çıkış ayarları

Fotoğraflarda WebP ve/veya AVIF, gerektiğinde JPEG yedeği kullanılabilir.
[web.dev format rehberi](https://web.dev/articles/choose-the-right-image-format)
bu formatları ve responsive teslimi öneriyor. Şeffaf logo için gerçek alfa içeren
PNG/WebP veya temiz SVG gerekir; JPEG'i PNG olarak kaydetmek şeffaflık oluşturmaz.

Başlangıç boyutları: **480 / 800 / 1200 / 1600 px** genişlik. Kaynağı aşan varyant
üretme. Dikey kaynakta kısa kenar daha küçükse 1600 genişlik bekleme. WebP kalite
78–85 ve AVIF 45–60 aralığı yalnızca encoder'a bağlı ilk deneme değeridir;
sayısal kalite değerleri formatlar arasında eşdeğer değildir. %100 karşılaştırma
ile ahşap dokusu ve keskin çizgiler üzerinden son karar verilmeli.

Kart başına kabaca 60–180 KB, büyük görsel için 150–350 KB tasarım bütçesiyle
başlanabilir; bunlar garanti veya ölçülmüş çıktı değildir. İnce detay ve kadraja
göre değişir. Aynı görüntüyü tekrar JPEG kaydedip sıkıştırmaktan kaçın.

`srcset`/`sizes`, açık `width`/`height` ve ekran dışındaki görsellerde `loading="lazy"`
kullanılmalı. Ana görsel lazy yüklenmemeli; gerekirse `fetchpriority="high"`
verilmeli. Bunlar [responsive images rehberindeki](https://web.dev/learn/design/responsive-images)
yükleme ve yerleşim önerileriyle uyumlu. Bu aşamada site veya performans ölçümü yok.

## Yayına geçmeden önce kalan işler

Otomatik indirme sonucu yerel inceleme aracında kontrol edilmeli; yanlış/eksik
kadrajlar ve bulunamayan referanslar gözden geçirilmeli. Eşleşen referanslar
`reference_only` olarak tutulur. Uygulama bölümünde hangi karelerin firmanın kendi
işleri olduğunun müşteri tarafından belirlenmesi gerekir. Ardından seçilen karelerde
perspektif/renk düzenleme ve cihaz boyutlarına göre ihracat yapılabilir.
