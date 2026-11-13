# Medya seti ve doğrulama

Güncel set: **43 fotoğraf + logo**. 12 fotoğraf müşteriden gelen doğrudan çekimlerden,
31 fotoğraf model referanslarından seçildi. 79 kaynak görselin tamamı bir seçim veya
alternatifle eşleştirildi. Tekrar sahneler ayrı ürün gibi çoğaltılmadı.

- Fotoğraf master'ları kısa kenarda en az 1000, uzun kenarda en az 1500 px.
- Yazı/arayüz/tarih damgası/filigran ve belirgin büyük yazılı dekor görsel incelemede elendi.
- Fotoğraflar yapay olarak büyütülmedi veya yeniden çizilmedi.
- Kullanıcının onayıyla alttan hafif damga kırpması yapıldı; kalan pikseller birebir korundu.
- WebP dosyaları 600 / 1000 / 1400 px. Kaynağı aşan genişlik üretilmedi.
- Logo JPEG ve opak zeminli; marka yazısı korunuyor. Şeffaf PNG/SVG türetilmedi.

“Yazısız” kontrolü görüntü üstündeki damga, filigran, sosyal medya arayüzü ve belirgin
dekoratif yazıları kapsar. Cihazların doğal düğme/ekran işaretleri ayrıca silinmedi.
Görsel kabul yalnızca OCR sonucuna dayanmaz; seçilenler görsel olarak da incelendi.

`make media-check` şu kontrolleri yapar:

1. Gelen 7 dosyanın ve 81 orijinal medya dosyasının SHA-256 özeti.
2. 44 master ve 109 WebP dosyasının varlığı, özeti ve ölçüleri.
3. Kırpılan master'ın kaynak bölgeyle piksel piksel eşitliği.
4. 79 görselin eksiksiz seçim/alternatif bağlantısı.
5. Katalog master klasörlerinde manifest dışı kopya bulunmaması.

Son rapor: `data/reports/media-validation.json`. Sekiz araç testi için `make test`.
Yerel önizlemeler masaüstünde ve 390 px genişlikte; kırık görsel, JS hatası ve taşma
olmadan kontrol edildi: `data/reports/preview-validation.json`.

Orijinal/final ayrımı korunur. Aynı baytları içeren bazı gerçek çekimlerin iki dizinde
bulunması bilinçlidir: orijinal arşiv ve düzenlenebilir katalog kopyası ayrı rollerdir.
WebP boyutları da farklı ekranlar için amaçlı teslim varyantlarıdır. Silinenler tarama
havuzu, tekrar indirmeler, ara kırpımlar, OCR/örnek sayfaları ve eski deneme çıktılarıdır.

Önceki ayrıntılı araştırma ve kaynak bağlantıları [araştırma notunda](research/GORSEL_ARASTIRMA.md).
Eski sonuçlar tarihsel kayıttır; güncel dosya yolları ve içerik için
[FOTO_ENVANTERI.md](FOTO_ENVANTERI.md) esas alınır.
