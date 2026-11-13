# Şimşek Mobilya kataloğu

Payas / Hatay’daki Şimşek Mobilya için statik katalog sitesi. **73 model, 7 kategori**;
favorilere ekleme, toplu WhatsApp mesajı, paylaşılabilir model bağlantısı ve fotoğraf
büyütme içerir. Kütüphanede ayrıca iki atölye fotoğrafı bulunur. Orijinal medya korunur.

```bash
make site          # Kaynaklardan public/ ve kategori sayfalarını oluştur
make serve         # http://localhost:8080
make check         # Medya bütünlüğü ve Python testleri
make qr            # site_url için doğrulanmış PNG/SVG katalog QR kodu
```

- [Site kullanımı ve fotoğraf ekleme](docs/SITE_KULLANIM.md)
- [Revizyon durumu ve doğrulama kanıtları](docs/SITE_REVIZYON_DURUMU.md)
- [Gemini UX/UI analiz raporu](docs/SITE_ANALIZ_RAPORU_GEMINI.md)
- [Tasarım sözleşmesi](docs/SITE_TASARIM_PLANI.md)
- [Fotoğraf envanteri](docs/FOTO_ENVANTERI.md)
- [Medya kalitesi](docs/MEDYA_KALITESI.md)
- [Medya inceleme galerisi](preview/index.html) · [Karşılaştırma](preview/comparison.html)

## Kaynaklar

| Yol | İçerik |
|---|---|
| `content/site.json` | Firma bilgileri, metinler, kategori tanımları, site adresi |
| `src/` | HTML şablonu, CSS, JavaScript, yerel fontlar ve paylaşım görseli |
| `public/` | Derlenmiş ana sayfa, 7 kategori sayfası ve yayın varlıkları |
| `assets/originals/` | Teslim arşivleri, orijinal fotoğraf ve videolar |
| `assets/catalog/`, `assets/web/` | Seçilmiş masterlar ve WebP varyantları |
| `data/media/` | Katalog, orijinal/eşleme kayıtları ve işlenmiş görsel manifesti |
| `config/media/` | Seçim ve işleme ayarları |
| `scripts/` | Site derlemesi, medya işleme/doğrulama ve QR üretimi |
| `tests/` | Python kontrolleri ve isteğe bağlı tarayıcı kabul testi |
| `work/` | Yerel test raporları ve ekran görüntüleri; Git dışında |

Site çalışma sırasında framework veya sunucu uygulaması gerektirmez. Derleme Python
standart kütüphanesini kullanır. Fotoğraf işleme ve QR araçları mevcut Pillow/OpenCV
ortamında çalışır. Ortam yoksa:

```bash
uv venv --python 3.14
uv pip install --python .venv/bin/python -r requirements.txt
```

Fotoğraflar değiştiğinde `make photos`, ardından `make site` çalıştırılır.
`make media-docs` envanteri, `make media-preview` medya inceleme galerisini günceller.
Fotoğraf ekleme mevcut yardımcı süreciyle sürdürülür; yönetim paneli kapsam dışıdır.

Tarayıcı testi için ayrı bir Playwright kurulumu ve Chromium gerekir; bunlar sitenin
çalışma veya Python derleme bağımlılığı değildir:

```bash
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node tests/browser_site.cjs
```

Mevcut yayın düzeni GitHub Pages'tir: `.github/workflows/pages.yml`, `main` dalına
`public/` değişikliği gönderildiğinde yayın dosyalarını dağıtır. Yerel derleme yayını
güncellemez. `public/` içindeki HTML/CSS/JS elle düzenlenmez.

Medya kaynakları ve orijinal koruma kuralları [hazırlık notunda](docs/SITE_HAZIRLIK.md)
ve [temizlik kaydında](docs/TEMIZLIK_RAPORU.md) tarihsel olarak belgelenmiştir.
`reference` fotoğraflar örnek modellerdir; `provided` fotoğraflar firmanın uygulamalarıdır.
