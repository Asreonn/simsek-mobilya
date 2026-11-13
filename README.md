# Şimşek Mobilya — site hazırlık alanı

Site henüz yapılmadı. Orijinaller, seçilmiş katalog görselleri, kaynak kayıtları ve
sonraki geliştirme için içerik hazırlığı düzenlendi.

İlk okunacak dosya: **[Fotoğraf envanteri](docs/FOTO_ENVANTERI.md)**. Her fotoğrafın
ne gösterdiği, boyutu, kullanım yeri ve orijinal/alternatif bağlantısı tek dosyada.

- [Site geliştirmesi için başlangıç notu](docs/SITE_HAZIRLIK.md)
- [Medya kalitesi ve doğrulama](docs/MEDYA_KALITESI.md)
- [Temiz seçim galerisi](preview/index.html) · [Orijinal/seçim karşılaştırması](preview/comparison.html)
- [Temizlik kaydı](docs/TEMIZLIK_RAPORU.md)

```text
assets/
  originals/incoming/    Gelen 6 ZIP ve JPEG logo; teslim dosyaları korunur
  originals/photos/      ZIP'lerden çıkan 78 orijinal fotoğraf
  originals/videos/      2 orijinal video
  originals/downloaded/  Kırpılmış referansların gerekli 2 ham kaynağı
  catalog/               43 seçilmiş fotoğraf + logo; açıklayıcı dosya adları
  web/                   109 amaçlı WebP boyut varyantı
config/media/            Ön sınıflandırma, seçim kararları ve kırpma kutuları
data/media/              Güncel katalog, orijinaller ve eşleştirme JSON'ları
data/research/           Kaynak URL'leri ve önceki arama kararları; tarihsel kayıt
data/reports/            Bütünlük, önizleme ve temizlik kanıtları
docs/                    Envanter, hazırlık ve kalite notları
preview/                 Yalnızca yerel medya inceleme aracı
scripts/                 Medya doğrulama, envanter ve araştırma araçları
tests/                   Araç testleri
src/                     Gelecekteki site uygulaması için boş
public/                  Gelecekteki yayın dosyaları için boş
work/                    Gerekirse üretilen geçici araştırma çıktıları; temizlenebilir
```

Güncel set: **43 fotoğraf + logo**; 12 doğrudan çekim ve 31 model referansı.
79 kaynak görselin tamamı seçime/alternatife bağlıdır. İki video arşivde durur.
Model referansları tamamlanan firma işi olarak sunulmaz.

## Günlük araçlar

```bash
make check          # Medya, kaynak, piksel ve sekiz araç testi
make media-docs     # Açıklamalı Markdown envanterini JSON kayıtlarından üret
make media-preview  # Yerel galeri/karşılaştırmayı üret
```

Python ortamı korunur; gerekenler `requirements.txt` içindedir. Ortam yoksa:

```bash
uv venv --python 3.14
uv pip install --python .venv/bin/python -r requirements.txt
```

Siteyi hazırlarken `data/media/catalog.json` kayıtları kullanılmalı. Her kayıtta
Türkçe açıklama/alt metin, kategori, rol, master/WebP yolları ve kaynak izi var.
Dosya adlarını veya hangi fotoğrafın ne olduğunu yeniden tahmin etmek gerekmiyor.

## Yeniden araştırma gerektiğinde

Mevcut 43 fotoğrafı kullanmak için tekrar indirme gerekmez. `catalog_assets.py` ve
`catalog_curation.py` araştırma araçları korundu; çıktıları artık `work/catalog/`
altına gider. Örneğin yeni teslimler için çevrimdışı envanter:

```bash
.venv/bin/python scripts/catalog_assets.py audit
```

Tersine arama yalnızca `reference` olarak sınıflanan kırpımları, açık
`--upload-references` seçeneğiyle yükler. Kullanıcı hesapları/çerezleri veya ücretli
API kullanılmaz. Araştırma aşaması otomatik görsel onay vermez; yeni adaylar inceleme
sonrası güncel medya kayıtlarına alınır. Önceki aday dosyaları silindi, kaynak URL ve
karar kayıtları `data/research/` altında korunuyor. Tarihsel kayıtlardaki eski dosya
yolları etkin medya yolları değildir.
