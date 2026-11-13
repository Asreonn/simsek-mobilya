# Site geliştirmesi için başlangıç notu

Bu çalışma yalnızca dosya, medya ve içerik hazırlığıdır. Müşteri sitesinin arayüzü,
sayfaları, sunucusu ve yayını henüz uygulanmadı. `preview/` yalnızca yerel medya
inceleme aracıdır. `src/` ve `public/` ilerideki uygulama için boş bırakıldı.

## Nereden başlanır?

1. [FOTO_ENVANTERI.md](FOTO_ENVANTERI.md): her orijinalin ve yeni setteki her fotoğrafın
   içeriği, boyutu, kullanım yeri, dosya bağlantısı ve karşılığı burada. Görselleri
   yeniden tek tek sınıflandırmak gerekmiyor.
2. `data/media/catalog.json`: uygulamanın okuyacağı 44 kayıt; 43 fotoğraf ve logo.
3. `data/media/mapping.json`: 79 orijinal görsel → seçilen / alternatif ID bağlantıları.
4. `data/media/originals.json`: gelen dosyalar, 81 orijinal medya, ZIP üye adları ve özetler.
5. `make check`: var olan medya yapısının bütünlüğünü ve araç testlerini doğrular.

## İçerik yapısı önerisi

| Bölüm | Hazır medya | Uygulama notu |
|---|---|---|
| Ana sayfa | `P-MUT-01`, `P-TV-01`, `LOGO-01` | Gerçek çekim adayı ve marka görseli; kesin aidiyet müşteriyle teyit edilir |
| Mutfak modelleri | `category: kitchen` | Gerçek çekimler ve model referansları ayrı gösterilebilir |
| Kahve köşeleri | `category: coffee` | Çoğu `R-KAH-*`; model/ilham içeriği olarak ele alınır |
| TV üniteleri | `P-TV-*`, `R-TV-01` | Benzer alternatif aynı uygulamanın devamı gibi sunulmaz |
| Antre / aynalar | `R-ANT-*` | Hazır temiz set referans görsellerden oluşuyor |
| Atölye / hakkında | `P-ATL-01`, `P-ATL-02` | Verilen üretim çekimleri; özgün pikseller korundu |
| İletişim | `LOGO-01` | Marka/iletişim satırı kaynak logoda; adres ve çalışma saatleri verilmedi |

Bu bir katalog hazırlığıdır; fiyat, stok, sepet, ödeme veya sipariş sistemi için
gereksinim verilmedi. Uygulama teknolojisi de henüz seçilmedi.

## Medya veri sözleşmesi

Her katalog kaydında `id`, `title`, `description`, `alt_tr`, `category`, `role`,
`suggested_usage`, `master`, `web`, `width`, `height`, `sha256` ve `provenance` var.
Yollar **proje köküne göredir**. Kodda dosya adlarını tahmin etmek yerine bu kayıtlar
kullanılmalı. WebP varyantları genişlik bilgisiyle birlikte hazırdır.

`role` değerleri:

- `provided`: müşteriden gelen gerçek çekim. Firmanın tamamlanan işi olduğu bağımsız
  olarak doğrulanmış değildir.
- `reference`: model / ilham görseli. Firma işi olarak sunulmamalı.
- `brand`: logo. Diğer fotoğraflardan farklı olarak marka yazısı bilinçli korunur.

Bir eşleştirmede `do_not_claim_same_installation: true` varsa alternatif, aynı işin
son hâli veya aynı ürünün diğer açısı olarak etiketlenmez. Görselden malzemenin masif
olduğu, ölçüler, fiyatlar, teslim süresi veya proje konumu çıkarılmamalı.

## Dosyaları siteye bağlarken

- Asıl seçilmiş dosyalar `assets/catalog/`, teslim kopyaları `assets/web/` içinde.
- `assets/originals/` gelen arşiv ve fotoğraflardır; siteye topluca yayınlanacak klasör değildir.
- `public/` şu anda boş. Teknoloji belirlendiğinde sadece kullanılacak WebP dosyaları
  veya üretim adımının çıktıları buraya alınmalı; bugünden ikinci bir medya kopyası yok.
- Galeri büyük fotoğrafta doğal oranı korumalı. Kart kadrajı ürünün önemli bölümünü
  kesmemeli; yatay/dikey kaynaklar envanterdeki boyutlardan anlaşılır.
- Mevcut görseller yeterli olduğu için başlangıçta yeniden tarama / indirme gerekmez.
- Yeni dosya eklenirse açıklaması ve alt metni JSON kaydına yazılır; `make media-docs`
  ve `make media-preview` ile envanter ve inceleme aracı güncellenir.

## Hazır olmayan bilgiler

Adres, hizmet bölgesi, çalışma saatleri, kesin hizmet metinleri, hangi doğrudan
çekimlerin firmanın işi olduğu ve referansların yayın tercihi henüz kullanıcıdan
kesinleştirilmedi. Bu alanlara tahmini içerik yazılmadı. İki video arşivde korunur;
web için kurgu, sıkıştırma veya otomatik oynatma seçimi yapılmadı.
