> Tarihsel araştırma/önceki çalışma notu. Eski çıktı yolları güncel değildir. Güncel envanter: [FOTO_ENVANTERI.md](../FOTO_ENVANTERI.md); kullanım: [README](../../README.md).

# Katalog görselleri — 13 Kasım 2026 son seçimi

Bu aşama web kataloğu için görsel hazırlığıdır. Müşteri sitesi yapılmadı.

## Sonuç

- **79 kaynak görselin tamamı için seçim/alternatif eşleştirmesi var.**
- Temiz havuz: **43 farklı fotoğraf + logo**.
- Fotoğrafların **12'si müşteriden gelen gerçek çekim**, **31'i model referansı**.
- Fotoğraf master'larının tamamında kısa kenar en az **1000 px**, uzun kenar en az
  **1500 px**. Boş dış çerçeveler bu ölçülere dahil edilmedi.
- Yapay büyütme, AI yeniden çizimi veya toplu renk/efekt uygulanmadı.
- 11 damgalı gerçek çekimin alt kenarı ayrı kopyalarda kırpıldı. Bunların 7'si
  son katalog havuzuna alındı; kurulum/ürün kadrajı uygun olmayan diğerleri zorlanmadı.
- Bir referansın alttaki yazılı dergi alanı da ürünü kesmeden kırpıldı.
- Kırpma sonrası kalan pikseller kaynak fotoğrafla birebir aynı; bu kontrol otomatik geçti.

**Temiz havuz:** `artifacts/catalog/catalog-ready/gallery.html`  
**Her orijinalin karşılığı:** `artifacts/catalog/catalog-ready/review.html`  
**Kaynaklar ve tüm kararlar:** `artifacts/catalog/catalog-ready/manifest.json`  
**Doğrulama:** `artifacts/catalog/catalog-ready/validation.json`

`masters/provided/` gerçek çekimleri, `masters/reference/` model referanslarını,
`masters/brand/` logoyu içerir. `web/` altında 600/1000/1400 px WebP kopyaları var;
kaynak genişliğini aşan varyant üretilmez. Yüksek çözünürlüklü kaynaklar master klasöründedir.

## Önceki “35” sayısının düzeltilmesi

İlk ZIP'teki 60 fotoğrafın hepsi Pinterest ekran görüntüsü değildi. Tek tek incelemede
12 doğrudan uygulama/üretim çekimi ayrıldı. Doğru toplam: **48 referans, 30 doğrudan
çekim, 1 logo**; ayrıca 2 video arşivde korunuyor.

Önceki 35 başarısız birebir aramanın **12'si bu doğrudan çekimler**, **23'ü referans**.
Bu çalışma, kullanıcı talebiyle benzer model alternatiflerini de kabul ediyor.
Birebir kaynak aramasının `needs_review` kayıtları geçmişte korunuyor; son katalog
seçiminde açık eşleştirme kalmadı. Bu, bütün görsellerin orijinallerinin bulunduğu
iddiası değildir: karşılaştırma sayfası aynı kare / başka çekim / benzer referans
ayrımını açıkça gösterir.

79 kaynak için ana seçimlerin dağılımı:

| İlişki | Kaynak sayısı |
|---|---:|
| Aynı gerçek çekim, alt damga kırpıldı | 7 |
| Aynı gerçek çekim, değiştirilmedi | 5 |
| Aynı fotoğrafın yeterli çözünürlükte çevrimiçi kopyası | 5 |
| Başka verilmiş gerçek çekim / farklı açı veya model | 10 |
| Benzer model referansı | 51 |
| Logo | 1 |

Aynı kaliteli fotoğraf birden fazla benzer giriş için kullanılabildiği için 79 giriş
43 farklı fotoğrafa indirgenir. Galeride tekrarlar gösterilmez; karşılaştırmada her
girdinin karşılığı ayrı kayıtlıdır.

## Yazı ve kalite kontrolü

Tüm kaynaklar ve bulunan adaylar çözünürlük/yazı açısından tarandı. 120 farklı büyük
aday dosya OCR ve teknik kontrolden geçirildi. Otomatik filtreyi geçenler görsel
olarak elendi; kabul edilenler daha büyük ayrıntı sayfalarında da incelendi.
Yazısız kabulü yalnızca OCR sonucuna dayanmaz.

Sosyal medya arayüzü, telefon/tarih damgası, üretici filigranı, görüntü üstüne yazılmış
ölçü/caption ve büyük yazılı dekor içeren adaylar temiz havuza alınmadı. Örneğin:

- Dolap üzerinde büyük kullanıcı adı bulunan referans elendi.
- OCR'nin kaçırdığı çapraz emlak filigranı görsel kontrolde elendi.
- “Coffee” yazılı sırt paneli ve kitaplarda büyük marka başlıkları olan modeller yerine
  daha temiz alternatifler seçildi.
- Düşük çözünürlüklü sosyal medya kopyaları büyütülmedi; yerlerine başka kaynak seçildi.
- Tamamlanmamış ürün, kurulum artıkları veya yayın açık TV ekranı bulunan bazı kareler
  katalog seçiminden çıkarıldı; arşivde korundu.

“Yazısız” kontrolü fotoğraf üstündeki arayüz/damga/filigran ve belirgin dekoratif yazıları
kapsar. Cihazların doğal düğme/ekran işaretleri ayrı bir grafik katman olarak silinmedi.
Logo marka görselidir; kendi yazısı bilinçli olarak korunur.

Doğrudan çekimlerin firma aidiyeti bağımsız olarak doğrulanmış değildir. Model
referansları bitmiş firma işi gibi etiketlenmez; web sitesinde model/ilham grubunda
kullanılacak şekilde ayrılmıştır.

## Yeniden çalıştırma

```bash
# Yeni aday toplama; mevcut dosyaları/sonuçları korur:
.venv/bin/python scripts/catalog_curation.py collect --candidates 8 --workers 3

# Yerel kırpım kopyaları ve analiz:
.venv/bin/python scripts/catalog_curation.py local
.venv/bin/python scripts/catalog_curation.py reaudit
.venv/bin/python scripts/catalog_curation.py board

# Yalnızca catalog_review.json içinde görsel onay verilmiş seçimler dışa çıkar:
.venv/bin/python scripts/catalog_curation.py export
.venv/bin/python scripts/catalog_curation.py validate
.venv/bin/python scripts/catalog_assets.py verify
.venv/bin/python -m unittest discover -s tests -v
```

`asset_overrides.json` kaynak sınıflandırmasını, `local_crops.json` gerçek çekimlerdeki
kırpma kutularını, `catalog_review.json` görsel eleme kararlarını,
`catalog_choices.json` giriş → seçim/alternatif eşleştirmelerini tutar. Otomatik tarama
tek başına yeni bir görseli onaylamaz. Yeni adaylarda görsel inceleme kararı gerekir.
Aynı çıktı klasöründe birden fazla yazan işlem çalıştırılmamalı.

Son doğrulama: **8 test geçti**, orijinal kaynak özetleri değişmedi, **44 master için
piksel koruma kontrolü geçti**, 79 girişte eksik seçim yok. 44 kartlık galeri ve
79 kartlık karşılaştırma; kırık görsel, JavaScript hatası ve mobil taşma olmadan
kontrol edildi.
