# Klasör düzeni ve temizlik — 13 Kasım 2026

Site uygulanmadı. Orijinaller ve onaylı yeni set korunarak medya altyapısı düzenlendi.

## Korunanlar

- Gelen **6 ZIP + JPEG logo**, teslim baytları ve SHA-256 özetleri değişmedi.
- **79 orijinal görsel + 2 video**; her birinin içeriği ve arşiv/üye adı kayıtlı.
- Onaylı **43 fotoğraf + logo**; açıklayıcı ID ve dosya adlarıyla `assets/catalog/` içinde.
- **109 WebP varyantı**; farklı ekranlar için amaçlı boyutlar.
- Kırpılmış iki referansın gerekli ham kaynakları; piksel kontrolü için saklandı.
- Kaynak URL'leri, önceki seçim kararları, araştırma notları ve sekiz araç testi.

## Silinenler

Önce eski dosyaların listesi, boyutu ve özeti `data/reports/cleanup-plan.json` içine
yazıldı. Yeni konumlardaki asıllar ve seçimler doğrulandıktan sonra **677 geçici /
yinelenen dosya, yaklaşık 107 MiB** kaldırıldı:

- Elenen arama adaylarının indirilmiş dosyaları.
- Son sette zaten bulunan eski indirme ve ara kırpım kopyaları.
- Rastgele örnek sayfaları, büyük inceleme panoları, eski önizleme ekran görüntüleri.
- OCR girdileri/çıktıları, geçici arama denemeleri ve Python bytecode önbelleği.
- Geçici taşıma aracı ve video kontrol kareleri; özgün videolar korunur.

Yalnızca bu amaçla kullanılan eski `artifacts/`, `work/` ve yerel `__pycache__/`
klasörleri kaldırıldı. İşlem kaydı: `data/reports/cleanup-files.json`.

Mevcut araçların kullanmadığı `playwright`, `gallery-dl`, `greenlet` paketleri proje
Python ortamından kaldırıldı. `requirements.txt` içindeki medya araçları için gereken
ortam korunuyor. Başka projelerin veya ortak tarayıcı önbelleğinin dosyalarına dokunulmadı.

`du` ile görülen proje klasörü yaklaşık **594 MiB → 317 MiB** oldu. Bunun yaklaşık
235 MiB'ı çalışan Python/OpenCV ortamıdır. Bu sayı proje klasörünün ölçüsüdür;
ortak paket önbelleklerinden ayrıca dosya silinmedi.

Orijinal arşiv ile kullanılabilir orijinal fotoğraf, ayrıca final master ve WebP
boyutları farklı işlevler için bilinçli olarak tutulur. Dosya içeriği aynı olsa da
orijinal ve düzenlenebilir final kopyasının ayrı olması, gelecekteki düzenlemelerde
orijinalin korunmasını sağlar.

## Güncel giriş noktaları

- [Fotoğraf envanteri](FOTO_ENVANTERI.md): 81 orijinal medya ve 44 yeni set öğesi.
- [Site hazırlığı](SITE_HAZIRLIK.md): veri sözleşmesi ve sonraki geliştirme adımları.
- [Kalite/doğrulama](MEDYA_KALITESI.md).
- [Yerel galeri](../preview/index.html) ve [karşılaştırma](../preview/comparison.html).

`data/media/` güncel ve etkin kaynaktır. `data/research/` ile `docs/research/`
tarihsel kayıt içerir; oralardaki eski çıktı yolları tekrar kullanılacak yollar değildir.

## Doğrulama

Yeni konumlarda tüm orijinal/master/WebP özetleri ve 44 kırpım piksel kontrolü geçti.
79 görselde eksik eşleştirme yok. Paket temizliğinden sonra sekiz test yeniden geçti.
Galeri 44, karşılaştırma 79 kayıtla masaüstü/mobil kontrolünden geçti. Sonraki dosya
adı düzenlemeleri sonrası yerel bağlantılar ve medya varlığı ayrıca kontrol edildi.

Komutlar: `make check`, `make media-docs`, `make media-preview`.
