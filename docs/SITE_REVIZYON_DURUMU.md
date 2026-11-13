# Şimşek Mobilya — 14 Kasım 2026 revizyonu

Gemini oturumunda yarım kalan görsel yenileme tamamlandı. Yeni şablon ve stiller,
model seçme/paylaşma JavaScript'i ve Python derlemesi birleştirildi. **73 model ve
7 kategori** sitede yer alır. Kütüphanedeki iki atölye fotoğrafı ayrıca gösterilir.

Kaynak analiz: [Gemini raporunun korunmuş kopyası](SITE_ANALIZ_RAPORU_GEMINI.md).
Kullanım ve fotoğraf ekleme: [SITE_KULLANIM.md](SITE_KULLANIM.md).

## Uygulananlar

| Rapordaki konu | Son durum |
|---|---|
| Okunabilirlik ve dokunma alanları | Görünür metin en az 14px; ana eylemler 48–52px, filtreler 48px. Üstte telefon rakamla görünür. |
| Seçtiklerim | Kart ve büyük görünümde kalp; tarayıcıda saklama; listeleme, çıkarma, temizleme ve tek WhatsApp mesajı. Bozuk/eski/engellenen depolamada katalog çalışır. |
| Model bağlantısı ve paylaşım | `#model/<model_no>`, doğrudan açılış, yenileme, geri/ileri; sistem paylaşımı veya bağlantı kopyalama, uygun olmayan tarayıcıda WhatsApp paylaşımı. |
| Görsel kimlik | Krem/ceviz paleti, Fraunces başlık ve Inter gövde, yerel WOFF2 fontları, sıcak gölgeler. Orijinal fontlar ve lisansları korunur; sayfa küçük Türkçe/Latin kopyaları yükler. |
| Sayfa akışı | Hero, tek kategori düğme satırı, neden biz, katalog, dört adım, atölye/video, SSS ve iletişim. |
| Katalog | 7 kategori, kendi işlerimiz/örnek model filtresi, sayfalama, boş sonuçtan dönüş ve kaydırılabilir filtre göstergesi. |
| Büyük fotoğraf | Aynı kategoride ok/klavye/kaydırma; düğme/dokunma/iki parmak yakınlaştırma; 4 benzer model; favori ve WhatsApp eylemleri. |
| Mobil sabit alanlar | Aşağı kaydırmada gizlenen üst bar; hero sonrası Ara/WhatsApp/Konum; seçim varken Seçtiklerim çubuğu. |
| İletişim | WhatsApp mesaj formu ve WhatsApp'ta hazırlanan arama talebi; isteğe bağlı yüklenen harita. Mesajı kullanıcı gönderir. |
| Güven ve fiyat açıklığı | Mevcut atölye fotoğrafları/video, usta adı, üretim adımları ve fiyatın ölçü/malzemeye bağlı olduğuna dair SSS. |
| SEO | Mutlak sosyal paylaşım görseli, canonical, Twitter kartı, 7 kategori sayfası, 8 URL'li sitemap, FurnitureStore ve FAQ verileri. |
| QR | PNG/SVG üretimi; PNG tekrar çözülerek kayıtlı katalog adresi doğrulanır. |
| Animasyon | Azaltılmış hareket desteği, kısa belirmeler, kalp geri bildirimi ve filtre göstergesi. |
| Fotoğraf yönetimi | **Kullanıcının seçimiyle mevcut yardımcıyla ekleme süreci belgeli olarak sürer. Yönetim paneli eklenmedi.** |

Kategori sayfaları: `mutfak-dolabi/`, `kahve-kosesi/`, `gomme-dolap/`, `tv-unitesi/`,
`berjer/`, `prefabrik-ev/`, `antre-ayna/`. Her birinin başlığı, canonical adresi,
kategori fotoğrafı ve başlangıç filtresi kendine aittir. JavaScript kapalıyken de
ana sayfanın tüm modelleri veya ilgili kategori sayfasının modelleri incelenebilir.

Logo, mevcut doğrulanmış amblem kırpımı ve yuvarlatılmış çerçeveyle kullanılır.
Kaynak olmayan bir vektör logo veya önce/sonra hikâyesi üretilmedi. Görsellerin
mevcut işleme hattı korunur; büyük görünüm tam fotoğrafı gösterir.

## Doğrulama

- `make check`: **29 test geçti**. 81 orijinal medya ve 76 katalog varlığı için
  bütünlük, kaynak pikseli ve ilişkiler doğrulandı. Orijinal/master dosyalar değiştirilmedi.
- `tests/browser_site.cjs`: **320, 360, 390, 820, 900, 1024, 1200 ve 1440px**;
  yatay taşma veya görünür 14px altı metin yok. JS hatası ve yerel HTTP hatası yok.
- Kategori/tür filtreleri, sayfalama, boş sonuç, seçimlerin yenileme sonrası kalıcılığı,
  doğru model numaralı toplu mesaj, listeyi temizleme ve depolama hata durumları geçti.
- Model bağlantısı, yenileme, geri/ileri, modal odak sınırı/geri dönüş, klavye,
  sentetik kaydırma/iki parmak hareketi, paylaşım ve yedi kategori sayfası geçti.
- Mesaj formu, arama talebi metni, haritayı tıklayınca oluşturma, mobil sabit çubuk
  ve JavaScript kapalı görünüm kontrol edildi. Otomatik test mesaj göndermedi.
- Hareket azaltma kapalıyken hero ve kaydırılan iletişim bölümünün görünürlüğü ayrıca
  kontrol edildi; görünür bağlantı/düğmelerde 44px altı yükseklik bulunmadı.
- Mobil Lighthouse: **performans 92, erişilebilirlik 100, iyi uygulamalar 100, SEO 100**.
  Yerel Python HTTP sunucusu, sıkıştırma olmadan, simüle mobil yavaşlatma ölçümüdür.
  LCP 3.1s, toplam engelleme 110ms, hız indeksi 1.7s. Canlı site ölçümü değildir.
- CSS 29,184 bayt; JS 21,223 bayt. JS'in gzip karşılığı yaklaşık 6 KB; yerel önizleme
  sunucusu sıkıştırma uygulamaz. İlk kartlar HTML'de sayfalı gelir; JavaScript
  kapalıysa tüm modeller erişilebilir kalır.
- QR: kayıtlı `https://asreonn.github.io/simsek-mobilya/#katalog` adresi tekrar
  okunarak doğrulandı. Bu kontrol yayındaki sitenin içeriğini doğrulamaz.

Kalıcı ölçüm özeti: [data/reports/site-qa.json](../data/reports/site-qa.json).
Yerel ham kanıtlar:

- [Tarayıcı raporu](../work/screens/checks.json)
- [Python kontrol çıktısı](../work/final-python-check.log)
- [Lighthouse JSON](../work/lighthouse-mobile.json)
- [Masaüstü görünümü](../work/screens/desktop-full.png)
- [Mobil görünüm](../work/screens/mobile-full.png)
- [Mobil büyük fotoğraf](../work/screens/mobile-lightbox.png)

## Dış bilgi veya canlı ortam gerektirenler

Çalışma saatleri, sosyal hesaplar ve izinli müşteri yorumları boş bırakıldı. Ücretsiz
keşif veya teslim süresi gibi teyitsiz vaat eklenmedi. Kesin coğrafi koordinat
bilinmediği için `geo` üretilmedi; adres ve yol tarifi mevcut kayıtlı bilgiyi kullanır.

Analitik hizmeti bağlı değildir; `plausible_domain` boştur. Olay çağrıları ancak
bir analitik kurulumuyla ölçüme dönüşür; bugün model ilgi verisi toplandığı iddia
edilmez. Kısa özel alan adı ve işletme profili dış hesap/alan adı işlemleridir.

Fiziksel telefonda dokunma hareketleri, gerçek WhatsApp mesaj teslimi, canlı harita
ve video ses içeriği için insan kontrolü hâlâ gerekir. Tarayıcı harita testinde
üçüncü taraf istek yanıtı taklit edildi; harita dış servisi doğrulanmadı.
Bu rapordaki ölçümler yerel kabul kanıtıdır. Canlı yayın durumu ayrıca deponun
GitHub Actions ekranındaki GitHub Pages çalıştırmasından kontrol edilir.

## Tekrar çalıştırma

```bash
make site
make check
make qr
make serve
# Ayrı terminal:
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node tests/browser_site.cjs
```

Font kaynakları değiştirilirse, yalnızca varlık bakımı için:

```bash
uv run --no-project --with 'fonttools[woff]' python scripts/subset_fonts.py
make site
```

Normal site derlemesi bu ek font aracına bağımlı değildir; üretilmiş WOFF2'ler
`src/fonts/` içinde bulunur. Yönetim, yayın ve fotoğraf ekleme yönergeleri
[SITE_KULLANIM.md](SITE_KULLANIM.md) içindedir.
