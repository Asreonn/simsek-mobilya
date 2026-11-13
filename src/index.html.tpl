<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  $base_tag
  <meta name="theme-color" content="#FFFAF4">
  <title>$seo_title</title>
  <meta name="description" content="$seo_description">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="tr_TR">
  <meta property="og:site_name" content="$brand_name">
  <meta property="og:title" content="$seo_title">
  <meta property="og:description" content="$seo_description">
  <script>(function(d){d.documentElement.classList.add('js');var f=function(e){var t=e.target;if(t&&t.tagName==='IMG')t.classList.add('is-loaded');};d.addEventListener('load',f,true);d.addEventListener('error',f,true);})(document);</script>
  $font_preload$hero_preload
  $seo_extra
  $favicon
  <link rel="stylesheet" href="assets/site.css?v=$asset_version">
  <script type="application/ld+json">$structured_data</script>
  $faq_ld
  <script id="gallery-data" type="application/json">$gallery_data</script>
  $analytics
  <script src="assets/site.js?v=$asset_version" defer></script>
</head>
<body data-site-url="$site_url_attr" data-wa-number="$wa_number" data-page-size="$page_size" data-category="$default_category">
  <a class="skip-link" href="#icerik">İçeriğe geç</a>
  <p class="visually-hidden" id="live" role="status" aria-live="polite"></p>
  <header class="site-header">
    <div class="container header-inner">
      <a href="#" class="brand" aria-label="$brand_name — Ana sayfa">$brand_mark<span class="brand-type"><strong>$brand_name</strong><span>$brand_tagline</span></span></a>
      <nav class="main-nav" aria-label="Ana menü">$nav_links</nav>
      <div class="header-actions">
        <button class="icon-button picks-trigger" type="button" data-open-picks aria-label="Seçtiklerim" hidden>$heart_icon<span class="picks-count" aria-hidden="true">0</span></button>
        <a class="button button-call header-call" href="$tel">$phone_icon <span class="call-short">Ara</span><span class="call-number">$phone_display</span></a>
      </div>
    </div>
  </header>
  <main id="icerik">
    <section class="hero" aria-labelledby="hero-title">
      <div class="hero-photo">$hero_picture$hero_caption$hero_controls</div>
      <div class="container hero-inner">
        <div class="hero-content">
          <p class="eyebrow">$hero_eyebrow</p>
          <h1 id="hero-title">$hero_title</h1>
          <div class="button-row">
            <a class="button button-primary" href="#katalog">$hero_cta_browse $down_icon</a>
            <a class="button button-light" href="$tel">$phone_icon $phone_display</a>
            <a class="button button-wa" href="$whatsapp">$wa_icon $hero_cta_whatsapp</a>
          </div>
        </div>
      </div>
    </section>
    <section class="picks container" aria-label="Kategoriler">
      <div class="pick-list">$picks</div>
    </section>
    <section class="why" aria-label="$why_title">
      <ul class="container why-list">$why_items</ul>
    </section>
    <section id="katalog" class="section catalog-section" aria-labelledby="models-title">
      <div class="container section-heading" data-reveal>
        <h2 id="models-title" tabindex="-1">$catalog_title</h2>
      </div>
      <div class="filter-bar"><div class="filter-wrap"><nav class="container filter-list" aria-label="Katalog kategorileri">$filters<span class="filter-indicator" aria-hidden="true"></span></nav></div></div>
      <div class="container">
        <div class="catalog-tools">
          <div class="seg" role="group" aria-label="Fotoğraf türü">
            <button type="button" data-role="all" aria-pressed="true">Hepsi</button>
            <button type="button" data-role="provided" aria-pressed="false">Bizim işlerimiz</button>
            <button type="button" data-role="reference" aria-pressed="false">Örnek modeller</button>
          </div>
        </div>
        <div class="model-grid" id="model-grid">$models</div>
        <div class="model-empty" id="model-empty" hidden><p>Bu kategoride uygulama fotoğrafı bulunmuyor.</p><button class="button button-outline" type="button" id="reset-role">Tüm fotoğrafları göster</button></div>
        <div class="more-row"><button class="button button-outline" id="more-models" type="button" hidden><span>Daha fazla göster</span> $plus_icon</button></div>
      </div>
    </section>
    <section id="surec" class="steps-section" aria-labelledby="steps-title">
      <div class="container">
        <div class="section-heading" data-reveal><div><h2 id="steps-title">$steps_title</h2></div></div>
        <ol class="steps">$steps_items</ol>
      </div>
    </section>
    <section id="atolye" class="section container workshop-section" aria-labelledby="workshop-title">
      <div class="workshop-copy" data-reveal><h2 id="workshop-title">$workshop_title</h2><p>$workshop_text</p><p class="owner">$owner <span>· $brand_name</span></p><a class="text-link" href="#iletisim">İletişim $arrow_icon</a></div>
      <div class="workshop-media"><div class="workshop-photos" data-reveal>$workshop_pictures</div>$workshop_video</div>
    </section>
    $testimonials
    <section id="sss" class="faq-section" aria-labelledby="faq-title">
      <div class="container faq-layout">
        <div class="section-heading" data-reveal><div><h2 id="faq-title">$faq_title</h2></div></div>
        <div class="faq-list">$faq_items</div>
      </div>
    </section>
    <section id="iletisim" class="section contact-section" aria-labelledby="contact-title">
      <div class="container contact-layout">
        <div class="contact-copy" data-reveal>
          <h2 id="contact-title">$contact_title</h2>
          <a class="contact-phone" href="$tel">$phone_display</a>
          <div class="button-row"><a class="button button-call" href="$tel">$phone_icon Hemen Ara</a><a class="button button-wa" href="$whatsapp">$wa_icon WhatsApp</a>$directions</div>
          <form class="wa-form" action="https://wa.me/$wa_number" method="get" target="_blank" rel="noopener">
            <label for="wa-text">$contact_form_label</label>
            <textarea id="wa-text" name="text" rows="3" required placeholder="$contact_form_placeholder"></textarea>
            <button class="button button-wa" type="submit">$wa_icon WhatsApp'ta gönder</button>
          </form>
          $address_html
          $hours_html
          <p class="social-links">$social_html</p>
        </div>
        $contact_map
      </div>
    </section>
  </main>
  <footer class="site-footer"><div class="container footer-main"><a class="brand" href="#">$brand_mark<span class="brand-type"><strong>$brand_name</strong><span>$brand_tagline</span></span></a><nav class="footer-nav" aria-label="Alt menü">$nav_links</nav><div class="footer-meta"><p>$footer_text</p><a href="$tel">$phone_display</a><span>© $year $brand_name</span></div></div><nav class="container category-pages" aria-label="Model kategorileri">$category_pages</nav></footer>
  <div class="mobile-contact" data-cols="$mobile_cols" aria-label="Hızlı iletişim">$mobile_bar</div>
  <div class="fav-bar" id="fav-bar" hidden>
    <button class="fav-open" type="button" data-open-picks>$heart_icon <span><b id="fav-bar-count">0</b> seçim</span></button>
    <a class="button button-wa" id="fav-send" href="$whatsapp" target="_blank" rel="noopener">$wa_icon Gönder</a>
  </div>
  <dialog class="lightbox" id="lightbox" aria-labelledby="lightbox-title" aria-describedby="lightbox-description">
    <div class="lightbox-top"><span id="lightbox-count" aria-live="polite"></span><div class="lightbox-tools"><button class="icon-button" type="button" id="lightbox-zoom" aria-label="Fotoğrafı yakınlaştır" aria-pressed="false">$zoom_icon</button><button class="icon-button" type="button" id="lightbox-share" aria-label="Bu modeli arkadaşınıza gönderin">$share_icon</button><button class="icon-button" type="button" id="lightbox-close" aria-label="Fotoğrafı kapat">$close_icon</button></div></div>
    <div class="lightbox-stage"><button class="icon-button lightbox-prev" type="button" aria-label="Önceki fotoğraf">$left_icon</button><div class="zoom-frame"><img id="lightbox-image" alt="" width="1600" height="1200"></div><button class="icon-button lightbox-next" type="button" aria-label="Sonraki fotoğraf">$arrow_icon</button></div>
    <div class="lightbox-caption">
      <div class="lightbox-info"><p class="lightbox-kind" id="lightbox-kind"></p><h2 id="lightbox-title"></h2><p id="lightbox-description"></p><p class="price-note">$price_note</p></div>
      <div class="lightbox-actions"><button class="button button-outline" type="button" id="lightbox-share-photo" hidden>$share_icon Fotoğrafı paylaş</button><button class="button button-outline" type="button" id="lightbox-fav" aria-pressed="false">$heart_icon <span>Seçtiklerime ekle</span></button><a class="button button-wa" id="lightbox-ask" href="$whatsapp" target="_blank" rel="noopener">$wa_icon $ask_label</a></div>
    </div>
    <div class="lightbox-similar" id="lightbox-similar" hidden><h3>Benzer modeller</h3><div class="similar-list" id="similar-list"></div></div>
  </dialog>
  <dialog class="picks-dialog" id="picks-dialog" aria-labelledby="picks-dialog-title">
    <div class="picks-head"><h2 id="picks-dialog-title">Seçtiklerim</h2><button class="icon-button" type="button" id="picks-close" aria-label="Kapat">$close_icon</button></div>
    <p class="picks-empty" id="picks-empty">Seçtikleriniz burada görünecek.</p>
    <ul class="picks-items" id="picks-items"></ul>
    <div class="picks-actions"><a class="button button-wa" id="picks-send" href="$whatsapp" target="_blank" rel="noopener">$wa_icon WhatsApp'ta gönder</a><button class="button button-outline" type="button" id="picks-clear">Listeyi temizle</button></div>
  </dialog>
</body>
</html>
