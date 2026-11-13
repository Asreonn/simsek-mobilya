# Siteyi kullanma ve güncelleme

Katalogda kategori seçin, beğendiğiniz fotoğrafların kalbine dokunun. **Seçtiklerim**
listesini açıp modelleri çıkarabilir veya tek WhatsApp mesajında ustaya gönderebilirsiniz.
Seçimler aynı tarayıcıda saklanır. Tarayıcı saklamaya izin vermiyorsa sayfa açıkken
seçim yapılabilir; bu durum ekranda bildirilir.

Fotoğrafa dokununca büyük görünüm açılır. Oklar, klavye veya kaydırma ile aynı
kategoride ilerleyin. Yakınlaştır düğmesi, fotoğrafa dokunma veya iki parmak hareketi
ile ayrıntıyı görün. Paylaş düğmesi modele özel bağlantı üretir. Adres çubuğundaki
`#model/…` bağlantısını da kopyalayabilirsiniz.

**Bizim işlerimiz** firma uygulamalarını, **Örnek modeller** fikir veren modelleri
filtreler. “Uygulamamız” rozeti yalnızca firma fotoğraflarında görünür.

İletişim bölümünde arama, WhatsApp ve yol tarifi bulunur. Harita doğrudan görünür;
bir düğmeye basılması gerekmez. Mesaj formu WhatsApp'ı açar; mesajı kullanıcı gönderir.

## Yeni fotoğraf ekleme

Fotoğraf ekleme **mevcut yardımcı süreciyle** sürer. Yönetim paneli eklenmedi.

1. Telefonun asıl fotoğrafını koruyun. Yardımcınıza fotoğrafın ne olduğunu,
   kategorisini ve kendi işiniz mi, örnek model mi olduğunu söyleyin.
2. Yardımcı orijinali, temiz masterı ve kaynak/eşleme bilgilerini mevcut medya
   kayıtlarına eklesin. Sadece `public/media/` içine fotoğraf bırakmak yeterli değildir.
3. `data/media/catalog.json` kaydına benzersiz ID/model numarası, `title`,
   `description`, `alt_tr`, kategori, `role`, `master`, boyut, SHA-256, `web` ve kaynak
   bilgilerini gerçek dosyaya göre yazsın. Başka modelin numarasını veya özetini taşımayın.
4. Orijinal kayıtlarını `data/media/originals.json`, kaynak eşlemelerini
   `data/media/mapping.json` ve gerekiyorsa `config/media/` altında tamamlasın.
5. Proje klasöründe çalıştırsın:

   ```bash
   make photos
   make check
   make media-docs
   make media-preview
   make site
   make serve
   ```

6. `http://localhost:8080` adresinde yeni fotoğrafı, büyük görünümü, kategori
   filtrelerini ve WhatsApp mesajındaki model numarasını kontrol edin.

Kategoriler: `kitchen`, `coffee`, `wardrobe`, `tv`, `armchair`, `hall`.
Atölye fotoğrafları `workshop` kategorisindedir. `provided` kendi işiniz,
`reference` örnek model, `brand` logo anlamına gelir.

Masterlar `assets/catalog/` altında; orijinaller `assets/originals/` altında korunur.
Mevcut kaynakların üzerine yazmayın. Yedek WebP'ler `assets/web/` ve katalogdaki
`web` listesinde kayıtlıdır. `make photos` işlenmiş boyutları ve
`data/media/web_manifest.json` dosyasını üretir; kadrajlar `preview/enhance.html`
ile incelenebilir. Yeni kayıtlar, SHA-256 ve ilişkiler `make check` ile doğrulanır.

## Yazı, telefon veya adres değişikliği

`content/site.json` dosyasını düzenleyip `make site` çalıştırın. Telefon değişirse
`phone_display`, `phone_e164`, `whatsapp` birlikte değişmelidir. Çalışma saatlerini,
sosyal hesapları, müşteri yorumlarını ve hizmet iddialarını yalnızca doğrulanmış bilgiyle
doldurun; boş alanlar gösterilmez. `src/` kaynak, `public/` üretim çıktısıdır.

`site_url` mevcut GitHub Pages adresidir. Alan adı değişirse `make site` ve
`make qr` çalıştırın. Ana sayfa, 6 kategori sayfası, canonical, sosyal paylaşım
etiketleri ve site haritası birlikte güncellenir.

## Yayın ve QR

GitHub Pages iş akışı, `main` dalına gönderilen `public/` değişikliklerini yayınlar.
Yerelde dosya üretmek yayındaki siteyi değiştirmez. Başka barındırma kullanılacaksa
`public/` klasörünün tamamını, kategori alt klasörleri dahil yükleyin.

`make qr`, kayıtlı site adresini içeren şu dosyaları üretir ve PNG'yi tekrar okuyarak
doğrular:

- [Baskıya uygun SVG](../public/media/katalog-qr.svg)
- [592 px PNG](../public/media/katalog-qr.png)
- [Doğrulama kaydı](../data/reports/qr-validation.json)

Kartvizit/tabela baskısından önce QR'yi telefonla okuyup yayındaki kataloğun açıldığını
kontrol edin. Kodun çevresindeki beyaz boşluğu koruyun.

## Kontroller

`make check` medya ve Python kontrollerini çalıştırır. Tarayıcı kabul testi isteğe
bağlı Playwright kurulumuyla çalışır; site bu pakete bağımlı değildir:

```bash
make serve
# Ayrı terminalde:
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node tests/browser_site.cjs
```

Testler gerçek WhatsApp mesajı göndermez. Harita testinde dış servis yerine yerel
bir yanıt kullanılır. Ekran görüntüleri `work/screens/` altında oluşur.
