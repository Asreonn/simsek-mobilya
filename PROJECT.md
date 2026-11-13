# Şimşek Mobilya kataloğu

Yol: `/home/asreonn/uwu/Scripts/web/marangoz`.
Git: `https://github.com/Asreonn/simsek-mobilya.git`; GitHub Pages yayın iş akışı mevcut.
Durum: **73 model, 7 kategori içeren statik katalog; v3 revizyonu hazır. Yayın: GitHub Pages.**

Önce [README](README.md), ardından [revizyon durumu](docs/SITE_REVIZYON_DURUMU.md)
ve [kullanım notu](docs/SITE_KULLANIM.md) okunmalı.

```bash
make site
make serve
make check
make qr
```

`src/` ve `content/site.json` kaynaklardır; `public/` derlenir. Framework veya sunucu
uygulaması yoktur. `data/media/catalog.json`, `originals.json`, `mapping.json` medya
kayıtlarını; `web_manifest.json` işlenmiş görselleri tanımlar. Kütüphanede 75 fotoğraf
ve logo vardır; 2 atölye fotoğrafı katalog model sayısına dahil değildir.

Seçimler tarayıcıda saklanır. Model bağlantıları `#model/ŞM-MUT-01` biçimindedir.
Kategori adresleri `mutfak-dolabi/`, `kahve-kosesi/`, `gomme-dolap/`, `tv-unitesi/`,
`berjer/`, `prefabrik-ev/`, `antre-ayna/` altında üretilir.

Fotoğraf ekleme mevcut yardımcı süreciyle sürer; yönetim paneli istenmiyor.
`assets/originals/` ve master görseller korunur. Referans fotoğraflar firmanın
uygulaması olarak sunulmaz. Yeni görseller ve kaynakları için
[envanteri](docs/FOTO_ENVANTERI.md) kullanın.

`make check` orijinal özetlerini, katalog ilişkilerini, kaynak piksel korumasını ve
Python testlerini kontrol eder. Tarayıcı testi `tests/browser_site.cjs`; son yerel
kanıtları `work/screens/` ve `work/final-python-check.log` altında bulunur.

Depoda mevcut kullanıcı değişiklikleri vardır. Özellikle `.claude/` altındaki
oturum öncesi değişiklikler görev dışıdır; reset, stash veya toplu temizlik yapmayın.
Geçici medya araştırma çıktıları `work/catalog/` içine gider.
