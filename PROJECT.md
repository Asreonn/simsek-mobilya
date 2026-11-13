# Şimşek Mobilya katalog hazırlığı

Yol: `/home/asreonn/uwu/Scripts/web/marangoz`. Git deposu/remote yok.
Durum: **Katalog sitesi hazır (`make photos && make site`, önizleme `make serve`). Plan: docs/SITE_TASARIM_PLANI.md, kullanım: docs/SITE_KULLANIM.md.**

Önce [docs/FOTO_ENVANTERI.md](docs/FOTO_ENVANTERI.md), sonra
[docs/SITE_HAZIRLIK.md](docs/SITE_HAZIRLIK.md) okunmalı. Her orijinal ve yeni görselin
ne olduğu, kullanım yeri, dosya yolu ve alternatifi envanterde açıklanır.

Gelenler: 6 ZIP + JPEG logo; 79 görsel ve 2 video. Hepsi orijinal özetleriyle korundu.
Temiz seçim: 43 fotoğraf + logo; 12 müşteriden gelen çekim, 31 model referansı.
79 görselin tamamı seçime bağlı. Logo yazısı korunur; fotoğraflarda görünür damga,
filigran ve sosyal arayüz elendi. Kullanıcı benzer alternatifleri ve alttan hafif
kırpmayı onayladı. Kırpma dışındaki kaynak pikselleri değiştirilmedi.

Güncel veri kaynağı `data/media/catalog.json`, `originals.json`, `mapping.json`.
Görseller `assets/catalog/`, web boyutları `assets/web/`, orijinaller
`assets/originals/` altında. Dosyalar okunabilir ID ve içerik adları taşır.

```bash
make check
make media-docs
make media-preview
```

`preview/` müşteri sitesi değil, yerel medya inceleme aracıdır. `src/` ve `public/`
boş. Teknoloji seçilmedi, frontend paketi kurulmadı. Sonraki iş bu veri ve görsellerle
katalog sitesini tasarlamak/uygulamak. Referansları firmanın bitmiş işleri olarak
sunmayın; eşleştirmedeki alternatifler aynı uygulamanın sonrası anlamına gelmeyebilir.

Tarama adayları/ara kopyalar temizlendi; kaynak URL'leri ve tarihsel kararlar
`data/research/` altında. Araştırma araçlarının geçici çıktıları `work/catalog/`
içine gider. Eski `pics/` ve `artifacts/` düzeni kullanılmaz.

Doğrulama: `data/reports/media-validation.json`, `preview-validation.json`, temizlik
kaydı `docs/TEMIZLIK_RAPORU.md`. Python/Pillow/NumPy/OpenCV/Requests araçları ve
sekiz test mevcut. Kütüphanenin yeniden tek tek görsel incelemesi gerekmez.
