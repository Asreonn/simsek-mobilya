# Şimşek Mobilya — Site Tasarım Planı (orkestratör sözleşmesi)

Tek kaynak bu dosyadır. Tüm işçiler (Codex, opencode, agy) buna uyar.

## Marka ve hedef

- Firma: **Şimşek Mobilya — Tasarım · Dekorasyon** · Usta: **Bayram Şimşek** · Tel: **0532 652 7813**
  - `tel:+905326527813` · WhatsApp: `https://wa.me/905326527813?text=Merhaba%2C%20web%20sitenizden%20ula%C5%9F%C4%B1yorum.`
- Amaç: **katalog sitesi**. Satış/sepet/fiyat YOK. Ziyaretçi bakar → beğenir → arar / WhatsApp'tan yazar.
- Kitle: sıradan aile/esnaf; teknolojiyle arası iyi olmayan biri bile ilk 5 saniyede
  "ne yapıyorlar, nasıl ararım" sorusunun cevabını görmeli. Büyük yazı, büyük butonlar,
  sade Türkçe, en fazla 2 tık.
- Uydurma bilgi YASAK: adres, kuruluş yılı, "X yıllık tecrübe", müşteri sayısı, malzeme
  (masif vb.), fiyat, teslim süresi, garanti süresi yazılmaz. Adres alanı boş bırakılır ve boşsa gizlenir.
- `role: reference` görseller firmanın bitmiş işi DEĞİL → "Örnek Modeller / Size özel
  uyarlanır" başlığı altında gösterilir. `role: provided` → "Uygulamalarımız".

## Görsel dil

Sıcak, temiz, turuncu-beyaz; ahşap atölye sıcaklığı. Bol beyaz alan, foto ön planda.

| Token | Değer | Kullanım |
|---|---|---|
| `--orange` | `#E8731C` | Ana vurgu, butonlar |
| `--orange-deep` | `#C25A0B` | Hover, başlık vurgusu |
| `--orange-soft` | `#FFF1E4` | Bölüm zeminleri, rozetler |
| `--cream` | `#FFFAF4` | Sayfa zemini |
| `--white` | `#FFFFFF` | Kartlar |
| `--ink` | `#2A1D14` | Ana metin (koyu ceviz) |
| `--muted` | `#6E5D50` | İkincil metin |
| `--line` | `#EFE3D6` | Kenarlıklar |
| `--wa` | `#1FA855` | Yalnız WhatsApp butonu |

- Yazı: başlık **Fraunces** (600/700, logodaki serif hissi), gövde **Manrope** (400/600/700).
  Google Fonts, `latin-ext` (Türkçe karakterler), `display=swap`.
- Gövde 17–18px (mobil 17px), satır yüksekliği 1.6. Buton yüksekliği ≥ 52px, dokunma alanı ≥ 48px.
- Köşe: kart 18px, buton 999px (hap). Gölge: yumuşak, sıcak (`0 10px 30px rgba(74,40,10,.10)`).
- Hareket: hafif fade/slide-up on scroll (IntersectionObserver), `prefers-reduced-motion` desteklenir.
- Kontrast WCAG AA. Turuncu üstüne beyaz yazı yalnız ≥ 18px kalın butonlarda.

## Sayfa yapısı (tek sayfa, `public/index.html`)

1. **Üst bar (sticky)**: logo amblemi + "Şimşek Mobilya" yazısı · menü (Uygulamalar,
   Modeller, Nasıl Çalışırız, Atölye, İletişim) · sağda turuncu **"Hemen Ara"**.
   Mobilde menü hamburger; "Ara" ikonu her zaman görünür.
2. **Hero**: tam genişlik `P-MUT-01` (koyu degrade üstüne beyaz başlık), kısa alt başlık,
   iki büyük buton: **📞 Hemen Ara** (turuncu) · **WhatsApp'tan Yaz** (yeşil).
   Altında 3 güven rozeti (ör. "Ücretsiz keşif ve ölçü", "Size özel tasarım", "Montaj dahil") —
   metinleri `content/site.json` verir.
3. **Neler Yapıyoruz**: 4 kategori kartı (Mutfak, TV Ünitesi, Kahve Köşesi, Antre & Ayna) —
   foto + başlık + 1 cümle + "Modelleri gör →" (galeriyi o kategoriyle filtreler).
4. **Uygulamalarımız** (`provided`, atölye hariç): büyük, ferah grid; tıklayınca lightbox.
5. **Örnek Modeller** (`reference`): filtre sekmeleri (Tümü / Mutfak / Kahve Köşesi /
   TV Ünitesi / Antre); masonry hissi veren grid; "Bu modelin benzerini istiyorum" →
   WhatsApp mesajı model ID'siyle ön dolu (`...?text=Merhaba, R-KAH-03 modeline benzer...`).
6. **Nasıl Çalışırız**: 4 adım (Görüşme → Ölçü & Tasarım → Atölyede Üretim → Montaj).
7. **Atölyemiz**: `P-ATL-01/02` + kısa metin (usta elinden çıkan iş vurgusu).
8. **İletişim**: büyük telefon numarası, Ara + WhatsApp butonları, logo görseli,
   çalışma saatleri/adres yalnız `site.json`'da doluysa.
9. **Footer**: logo, kısa slogan, telefon, © yıl.
- **Mobil**: altta sabit 2 butonlu çubuk (Ara | WhatsApp), üstte sticky bar ince.
- **Lightbox**: tam ekran, kaydırma (swipe) + ok tuşları + ESC, başlık + açıklama, alt
  köşede WhatsApp ile sor butonu, `<dialog>` tabanlı, odak yönetimi.

## Teknik

- Framework yok. Statik HTML + tek CSS + tek küçük vanilla JS. Build: Python (`.venv`).
- `scripts/build_site.py`: `content/site.json` + `data/media/catalog.json` +
  `data/media/web_manifest.json` → `public/` (index.html, `assets/site.css`, `assets/site.js`,
  `media/`). Kaynak şablonlar `src/` altında (`src/index.html.tpl`, `src/site.css`, `src/site.js`);
  basit `string.Template`/str.replace — ek bağımlılık yok.
- Manifest yoksa fallback: `catalog.json` içindeki `web[]` WebP yolları `public/media/` altına kopyalanır.
- Görsel: `<picture>` (AVIF varsa + WebP), `srcset`/`sizes`, `loading="lazy"` (hero hariç,
  hero `fetchpriority="high"`), `width/height` her zaman (CLS 0), LQIP arka planı.
- SEO: `<title>`, meta description, Open Graph (hero görseli), `LocalBusiness`/`FurnitureStore`
  JSON-LD (yalnız bilinen alanlar: ad, telefon, görsel), `lang="tr"`, `robots.txt`, `sitemap.xml`
  (alan adı `site.json` → `site_url`; boşsa sitemap atlanır).
- Erişilebilirlik: semantik bölümler, alt metin = `alt_tr`, odak halkası turuncu, skip-link.
- Performans hedefi: Lighthouse mobil ≥ 90; JS < 15 KB; CSS < 30 KB.
- `Makefile`: `make photos` (foto işleme), `make site` (build), `make serve` (python -m http.server 8080 -d public).

## Fotoğraf işleme (`scripts/enhance_photos.py`)

Masterlar (`assets/catalog/`) DEĞİŞTİRİLMEZ; çıktılar `public/media/` ve manifest.
Deterministik, muhafazakâr "profesyonel katalog" görünümü; yapay/HDR görüntü yasak.

1. EXIF düzelt, sRGB'ye çevir.
2. Beyaz dengesi: gri-dünya + parlak-beyaz karışımı, güç 0.6, kanal kazancı ±%12 ile sınırlı.
   `config/media/enhance_overrides.json` ile kapatılabilir (P-TV-02/03/04 mor LED bilinçli → `wb:false`).
3. Ton: %0.3/%99.7 persentil seviye germe (sınırlı), LAB-L üzerinde CLAHE (clip 1.6, tile 8) %45 karışım,
   hafif gölge kaldırma / ışık koruma S-eğrisi.
4. Renk: vibrance +%12 (düşük doygunluklu piksellere ağırlık), çok hafif sıcak ton (ahşap hissi).
5. `provided` (telefon çekimi) için hafif gürültü azaltma (fastNlMeans h≈3).
6. Yeniden boyutlandırmadan SONRA çıktı keskinleştirme (unsharp; boyuta göre).
7. Standart çıktılar (asla büyütme yok):
   - `full`: genişlik 640 / 1024 / 1600 / 2048 (kaynak izin verdiği kadar), oran korunur.
   - `card`: 4:3 akıllı kırpma (kenar/entropi + saliency tabanlı odak) 480 / 800.
   - `tall`: 3:4 akıllı kırpma 480 / 800 (dikey kaynaklar için masonry kartı).
   - Formatlar: WebP q82 (+ Pillow AVIF destekliyorsa AVIF q60). Metadata temizlenir.
   - `lqip`: 24px genişlik bulanık WebP base64 data URI; `color`: baskın ton hex.
8. Logo: `logo-full` (600/1000 WebP) + `logo-mark` (yazının üstündeki ev/S amblemi, kare kırpma
   192/384 PNG+WebP) + `favicon` (32/180/512 PNG). Kırpma kutusu config'te ayarlanabilir.
9. `data/media/web_manifest.json`:
   `{ "generated": ..., "assets": { "<ID>": { "role", "category", "title", "alt_tr", "width", "height",
   "lqip", "color", "full":[{"path","w","h","format"}], "card":[...], "tall":[...] } }, "logo": {...} }`
   (yollar `public/` köküne göre, ör. `media/p-mut-01-1600.webp`).
10. `preview/enhance.html`: önce/sonra yan yana karşılaştırma (QA için).
11. Testler `tests/test_enhance_photos.py` (boyut, büyütmeme, manifest şeması, master değişmemesi).

## Metinler (`content/site.json`)

Şema (anahtarlar sabit, değerler Türkçe):

```json
{
  "site_url": "",
  "brand": {"name": "Şimşek Mobilya", "tagline": "...", "owner": "Bayram Şimşek",
            "phone_display": "0532 652 7813", "phone_e164": "+905326527813",
            "whatsapp": "905326527813", "address": "", "hours": "", "service_area": ""},
  "seo": {"title": "...", "description": "... (≤155 karakter)"},
  "nav": [{"id": "uygulamalar", "label": "Uygulamalar"}, ...],
  "hero": {"eyebrow": "...", "title": "...", "subtitle": "...", "cta_call": "Hemen Ara", "cta_whatsapp": "WhatsApp'tan Yaz",
           "badges": ["...", "...", "..."]},
  "categories": [{"key": "kitchen", "title": "Mutfak Dolabı", "text": "...", "cover": "P-MUT-02"},
                 {"key": "tv", ...}, {"key": "coffee", ...}, {"key": "hall", ...}],
  "projects": {"title": "Uygulamalarımız", "intro": "..."},
  "models": {"title": "Örnek Modeller", "intro": "... size özel ölçü ve renkte uyarlanır ...",
             "note": "Bu görseller ilham amaçlı örnek modellerdir.", "ask_label": "Benzerini İstiyorum",
             "filters": {"all": "Tümü", "kitchen": "Mutfak", "coffee": "Kahve Köşesi", "tv": "TV Ünitesi", "hall": "Antre & Ayna"}},
  "process": {"title": "Nasıl Çalışırız?", "steps": [{"title": "...", "text": "..."} x4]},
  "workshop": {"title": "Atölyemiz", "text": "..."},
  "contact": {"title": "...", "text": "...", "whatsapp_message": "Merhaba, web sitenizden ulaşıyorum. ..."},
  "footer": {"text": "..."}
}
```

Ton: samimi, net, esnaf ağzına yakın ama düzgün Türkçe; kısa cümleler; abartı ve
uydurma rakam yok. Kategori `cover` ID'leri: kitchen→`P-MUT-02`, tv→`P-TV-01`,
coffee→`R-KAH-03`, hall→`R-ANT-03`.

## İş dağılımı

| İş | İşçi | Çıktı |
|---|---|---|
| Plan, sözleşme, entegrasyon, son kontrol | Claude (orkestratör) | bu dosya |
| Fotoğraf işleme hattı | Codex **c2** | `scripts/enhance_photos.py`, manifest, preview, test |
| Site iskeleti + build | Codex **c1** | `src/*`, `scripts/build_site.py`, `public/`, Makefile |
| Türkçe metinler | opencode free model | `content/site.json` |
| Görsel/UX inceleme | agy Sonnet | inceleme raporu |

---

## v2 revizyonu (2026-11-13) — "gerçek katalog" yönü

Kullanıcı geri bildirimi: yazı tipleri/animasyonlar/yumuşaklık kötü; açıklamalar görselle
uyuşmuyor; katalog havası yok; foto ve çeşit az. Müşteri isteği: katalog (sipariş yok),
kategoriler, her kategoride fotoğraflar, iletişim bilgileri. v1'in çakışan kuralları geçersizdir.

- **Kategoriler:** Mutfak Dolabı (kitchen), Kahve Köşesi (coffee), Gömme Dolap (wardrobe),
  TV Ünitesi (tv), Berjer (armchair), Prefabrik Ev (prefab), Antre & Ayna (hall); Atölye ayrı bölüm.
- **Konum:** İstiklal Mahallesi, Müge Sokak No:3, 31900 Payas / Hatay · 0532 652 78 13.
- **Tipografi:** Başlık **Outfit** (600/700), gövde **Inter** (400/500/600). Fraunces/Manrope kaldırılır.
- **Biçim:** Köşe kart 6px, buton 8px (hap yok). Gölge çok hafif ya da yok; ince kenarlık.
- **Hareket:** Yalnız 200ms opacity fade; blur, shimmer, scale, translate yok. Görsel yüklenirken
  düz baskın renk zemin, yüklenince 200ms fade.
- **Metin:** Kartlarda yalnız kısa ürün adı + Model No (ŞM-MUT-07) + gerçek iş ise "Uygulamamız" rozeti.
  Uzun açıklama kartta yok; lightbox'ta tek cümle.
- **Katalog düzeni:** Hero kısa → kategori döşemeleri (foto + ad + "N model") → Katalog bölümü:
  yapışkan kategori sekmeleri (mobilde yatay kaydırma, sayılarla) + düzenli eşit oranlı ürün ızgarası
  (4:3, masaüstü 4 sütun, tablet 3, mobil 2) → Atölye → İletişim (adres, harita, yol tarifi).
  URL hash ile kategori paylaşılabilir (#katalog/mutfak).
