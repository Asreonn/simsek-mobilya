# Siteyi güncelleme

Bu site bir katalogdur. Ziyaretçi fotoğraflara bakar, sizi arar veya WhatsApp'tan yazar.
Fiyat veya sepet yoktur.

## Yeni fotoğraf eklemek

1. Fotoğrafın orijinalini saklayın. Mümkünse WhatsApp'tan küçültülmüş kopya yerine
   telefonun asıl fotoğrafını kullanın. Fotoğrafta tarih, telefon damgası veya başka
   bir firmanın yazısı olmasın.
2. Yardımcınıza fotoğrafla birlikte şunları verin: **ne olduğu** (örneğin beyaz
   mutfak), **hangi bölümde gösterileceği** ve **kendi işiniz mi, örnek model mi**
   olduğu. Başka bir yerden alınan model, “Uygulamalarımız” bölümüne konmaz.
3. Yardımcınız fotoğrafı aşağıda anlatıldığı gibi kataloğa kaydetsin. Yalnızca
   `public/media/` klasörüne fotoğraf atmak sitede görünmesi için yeterli değildir.
4. Proje klasöründe terminal açıp çalıştırın:

   ```bash
   make photos
   make site
   make serve
   ```

5. Tarayıcıda **http://localhost:8080** adresini açın. Yeni fotoğrafı bulun,
   büyütün ve WhatsApp düğmesine basınca doğru model numarasının yazdığını kontrol
   edin. Telefonda Ara ve WhatsApp düğmelerini de deneyin.
6. İnternetteki siteyi güncellemek için **public klasörünün tamamını** mevcut
   barındırma alanına yükleyin. Terminaldeki önizlemeyi kapatmak için `Ctrl+C` basın.

## Fotoğrafı kaydeden yardımcı için

- Orijinali koruyun; seçilen temiz kopyayı `assets/catalog/` altında uygun bölümde
  saklayın. Mevcut dosyaların üzerine yazmayın.
- `data/media/catalog.json` içindeki `assets` listesine benzer bir kaydı kopyalayıp
  **yeni, benzersiz bir ID** verin. Örneğin sıradaki kullanılmayan `P-MUT-07`.
- `provided` kendi çekimleriniz, `reference` ilham modelleri içindir. Kategoriler:
  `kitchen` (mutfak), `tv`, `coffee` (kahve köşesi), `hall` (antre), `workshop` (atölye).
- `title` kısa ad, `description` fotoğrafın açıklaması, `alt_tr` ise fotoğrafı
  göremeyen ziyaretçi için açık bir Türkçe betimleme olsun. `master`, `width`,
  `height`, `sha256`, `provenance` ve `suggested_usage` alanlarını yeni dosyanın
  gerçek bilgileriyle güncelleyin; önceki kaydın özetini veya kaynak bilgisini bırakmayın.
- `web` listesine `assets/web/` altındaki WebP kopyalarını gerçek `path`, `width`,
  `height`, `sha256` bilgileriyle ekleyin. En fazla 600 / 1000 / 1400 px genişlik;
  kaynak küçükse büyütmeyin. Bu kopyalar işlenmiş manifest olmadığında yedektir.
- `make photos` daha iyi web boyutlarını ve `data/media/web_manifest.json`
  dosyasını üretir. `preview/enhance.html` ile kadrajları inceleyin.
- Ardından `make media-check`, `make media-docs`, `make media-preview` ve
  `make site` çalıştırın. Hata varsa yayınlamadan önce düzeltin.
- Mutfak, TV, kahve ve antre fotoğrafları uygun galeriye kendiliğinden eklenir.
  İlk ekranda bazı fotoğraflar gösterilir; devamı “Diğer uygulamaları gör” veya
  “Daha fazla model gör” düğmesiyle açılır. Atölye bölümü seçilmiş `P-ATL-01/02`
  fotoğraflarını kullanır; seçimi değiştirmek için siteyi hazırlayan kişiye danışın.

## Yazı veya telefon değişirse

Metinler `content/site.json` dosyasındadır. Yardımcınız değişikliği yaptıktan sonra
yalnızca `make site` yeterlidir; fotoğrafların yeniden işlenmesine gerek yoktur.
Dosya yoksa `content/site.example.json` içindeki örnek metinler kullanılır.

Adres, çalışma saatleri ve hizmet bölgesi alanları boşsa gösterilmez. Bilmediğiniz
bilgiyi tahmin ederek doldurmayın. Telefon değişirse `phone_display`, `phone_e164`
ve `whatsapp` alanlarını birlikte güncelleyin.

Alan adınız belli olduğunda `site_url` alanına `https://` ile başlayan gerçek
adresi yazdırın ve `make site` çalıştırın. Site haritası ve paylaşım bağlantıları
bu adrese göre hazırlanır. Alan boşsa site haritası oluşturulmaz.

`src/` kaynak şablonlardır. `public/` içindeki HTML, CSS ve JS dosyalarını elle
düzenlemeyin; bir sonraki derlemede yeniden yazılırlar. Derleme fotoğraf klasörünü
temizlemez; fotoğraf silmek ayrı bir işlemdir.
