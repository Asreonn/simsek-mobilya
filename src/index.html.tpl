<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#FFFFFF">
  <title>$seo_title</title>
  <meta name="description" content="$seo_description">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="tr_TR">
  <meta property="og:site_name" content="$brand_name">
  <meta property="og:title" content="$seo_title">
  <meta property="og:description" content="$seo_description">
  <script>(function(d){d.documentElement.classList.add('js');var f=function(e){var t=e.target;if(t&&t.tagName==='IMG')t.classList.add('is-loaded');};d.addEventListener('load',f,true);d.addEventListener('error',f,true);})(document);</script>
  $hero_preload
  $seo_extra
  $favicon
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@600;700&amp;family=Inter:wght@400;500;600;700&amp;display=swap&amp;subset=latin-ext" rel="stylesheet">
  <link rel="stylesheet" href="assets/site.css">
  <script type="application/ld+json">$structured_data</script>
  <script id="gallery-data" type="application/json">$gallery_data</script>
  <script src="assets/site.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#icerik">İçeriğe geç</a>
  <header class="site-header">
    <div class="container header-inner">
      <a href="#" class="brand" aria-label="$brand_name — Ana sayfa">$brand_mark<span class="brand-type"><strong>$brand_name</strong><span>$brand_tagline</span></span></a>
      <nav class="main-nav" aria-label="Ana menü"><a href="#katalog">Katalog</a><a href="#atolye">Atölyemiz</a><a href="#iletisim">İletişim</a></nav>
      <a class="button button-call header-call" href="$tel">$phone_icon <span>Ara</span></a>
    </div>
  </header>
  <main id="icerik">
    <section class="hero container" aria-labelledby="hero-title">
      <div class="hero-content">
        <p class="eyebrow">$hero_eyebrow</p>
        <h1 id="hero-title">$hero_title</h1>
        <p class="hero-subtitle">$hero_subtitle</p>
        <div class="button-row"><a class="button button-call" href="$tel">$phone_icon $cta_call</a><a class="button button-wa" href="$whatsapp">$wa_icon $cta_whatsapp</a></div>
        <a class="text-link" href="#katalog">Modelleri inceleyin $arrow_icon</a>
      </div>
      <div class="hero-photo">$hero_picture<span class="hero-caption">Kendi uygulamalarımızdan</span></div>
    </section>
    <div class="trust-strip"><ul class="container trust-list">$badges</ul></div>
    <section id="kategoriler" class="section container" aria-labelledby="categories-title">
      <div class="section-heading"><div><p class="eyebrow">Eviniz için</p><h2 id="categories-title">Kategoriler</h2></div><a class="text-link" href="#katalog">Tüm modeller $arrow_icon</a></div>
      <div class="category-grid">$categories</div>
    </section>
    <section id="katalog" class="section catalog-section" aria-labelledby="models-title">
      <div class="container section-heading"><div><p class="eyebrow">Şimşek Mobilya koleksiyonu</p><h2 id="models-title" tabindex="-1">Katalog <span class="heading-count">$model_count model</span></h2></div><p>$catalog_intro</p></div>
      <div class="filter-bar"><nav class="container filter-list" aria-label="Katalog kategorileri">$filters</nav></div>
      <div class="container">
        <div class="catalog-meta"><p id="model-status" role="status" aria-live="polite"></p><p>Uygulamamız <span>rozetli fotoğraflar kendi işlerimizdir.</span></p></div>
        <div class="model-grid" id="model-grid">$models</div>
        <div class="more-row"><button class="button button-outline" id="more-models" type="button" hidden>Daha fazla göster $plus_icon</button></div>
        <noscript><p>Tüm modeller gösteriliyor. Büyütmek için fotoğrafa dokunun.</p></noscript>
      </div>
    </section>
    <section id="atolye" class="section container workshop-section" aria-labelledby="workshop-title">
      <div class="workshop-photos">$workshop_pictures</div>
      <div class="workshop-copy"><p class="eyebrow">Kendi atölyemizde</p><h2 id="workshop-title">$workshop_title</h2><p>$workshop_text</p><p class="owner">$owner <span>· $brand_name</span></p><a class="text-link" href="#iletisim">Birlikte konuşalım $arrow_icon</a></div>
    </section>
    <section id="iletisim" class="section contact-section" aria-labelledby="contact-title">
      <div class="container contact-layout">
        <div class="contact-copy"><p class="eyebrow">Payas / Hatay</p><h2 id="contact-title">$contact_title</h2><p>$contact_text</p><a class="contact-phone" href="$tel">$phone_display</a><div class="button-row"><a class="button button-call" href="$tel">$phone_icon Ara</a><a class="button button-wa" href="$whatsapp">$wa_icon WhatsApp</a>$directions</div><address>$address</address></div>
        $contact_map
      </div>
    </section>
  </main>
  <footer class="site-footer"><div class="container footer-main"><a class="brand" href="#">$brand_mark<span class="brand-type"><strong>$brand_name</strong><span>$brand_tagline</span></span></a><p>$footer_text</p><span>© $year $brand_name</span></div></footer>
  <div class="mobile-contact" aria-label="Hızlı iletişim"><a class="button button-call" href="$tel">$phone_icon Ara</a><a class="button button-wa" href="$whatsapp">$wa_icon WhatsApp</a></div>
  <dialog class="lightbox" id="lightbox" aria-labelledby="lightbox-title" aria-describedby="lightbox-description">
    <div class="lightbox-top"><span id="lightbox-count" aria-live="polite"></span><button class="icon-button" type="button" id="lightbox-close" aria-label="Fotoğrafı kapat">$close_icon</button></div>
    <div class="lightbox-stage"><button class="icon-button lightbox-prev" type="button" aria-label="Önceki fotoğraf">$left_icon</button><img id="lightbox-image" alt="" width="1600" height="1200"><button class="icon-button lightbox-next" type="button" aria-label="Sonraki fotoğraf">$arrow_icon</button></div>
    <div class="lightbox-caption"><div><p class="lightbox-kind" id="lightbox-kind"></p><h2 id="lightbox-title"></h2><p id="lightbox-model"></p><p id="lightbox-description"></p></div><a class="button button-wa" id="lightbox-ask" href="$whatsapp">$wa_icon Bu modeli sor</a></div>
  </dialog>
</body>
</html>
