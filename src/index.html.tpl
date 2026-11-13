<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#FFFAF4">
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
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&amp;family=Manrope:wght@400;600;700;800&amp;display=swap&amp;subset=latin-ext" rel="stylesheet">
  <link rel="stylesheet" href="assets/site.css">
  <script type="application/ld+json">$structured_data</script>
  <script id="gallery-data" type="application/json">$gallery_data</script>
  <script src="assets/site.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#icerik">İçeriğe geç</a>
  <header class="site-header">
    <div class="container header-inner">
      <a href="#" class="brand" aria-label="$brand_name — Ana sayfa">
        $brand_mark
        <span class="brand-type"><strong>$brand_name</strong><span>$brand_tagline</span></span>
      </a>
      <nav id="ana-menu" class="main-nav" aria-label="Ana menü">$nav</nav>
      <div class="header-actions">
        <a class="button button-call header-call" href="$tel" aria-label="Hemen Ara">$phone_icon<span>Hemen Ara</span></a>
        <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="ana-menu" aria-label="Menüyü aç">$menu_icon</button>
      </div>
    </div>
  </header>
  <main id="icerik">
    <section class="hero" aria-labelledby="hero-title">
      $hero_picture
      <div class="hero-shade"></div>
      <div class="container hero-content">
        <p class="eyebrow">$hero_eyebrow</p>
        <h1 id="hero-title">$hero_title</h1>
        <p class="hero-subtitle">$hero_subtitle</p>
        <div class="button-row">
          <a class="button button-call" href="$tel">$phone_icon $cta_call</a>
          <a class="button button-wa" href="$whatsapp">$wa_icon $cta_whatsapp</a>
        </div>
        <a class="hero-explore" href="#kategoriler">Kataloğu keşfedin $down_icon</a>
      </div>
      <span class="hero-caption">Uygulamalarımızdan</span>
    </section>
    <div class="trust-strip"><ul class="container trust-list">$badges</ul></div>

    <section id="kategoriler" class="section container" aria-labelledby="categories-title">
      <div class="section-heading" data-reveal>
        <div><p class="eyebrow">Evinizin her köşesine</p><h2 id="categories-title">Neler yapıyoruz?</h2></div>
        <p>İhtiyacınız olan yeri seçin, <br>birlikte fikir bulalım.</p>
      </div>
      <div class="category-grid">$categories</div>
    </section>

    <section id="uygulamalar" class="section projects-section" aria-labelledby="projects-title">
      <div class="container">
        <div class="section-heading" data-reveal>
          <div><p class="eyebrow">Fotoğraflarla yakından</p><h2 id="projects-title">$projects_title</h2></div>
          <p>$projects_intro</p>
        </div>
        <div class="project-grid" id="project-grid">$projects</div>
        <div class="more-row"><button class="button button-outline" id="more-projects" type="button" hidden>Diğer uygulamaları gör $plus_icon</button></div>
      </div>
    </section>

    <section id="modeller" class="section container" aria-labelledby="models-title">
      <div class="section-heading" data-reveal>
        <div><p class="eyebrow">Birlikte hayal edelim</p><h2 id="models-title">$models_title</h2></div>
        <p>$models_intro</p>
      </div>
      <p class="reference-note">$info_icon $models_note</p>
      <div class="filter-list" role="group" aria-label="Modelleri kategoriye göre filtrele" hidden>$filters</div>
      <p class="gallery-status" id="model-status" role="status" aria-live="polite"></p>
      <div class="model-grid" id="model-grid">$models</div>
      <div class="more-row"><button class="button button-outline" id="more-models" type="button" hidden>Daha fazla model gör $plus_icon</button></div>
      <noscript><p class="reference-note">Tüm modeller aşağıdadır. Fotoğraflara dokunarak büyütebilirsiniz.</p></noscript>
    </section>

    <section id="nasil-calisiriz" class="section process-section" aria-labelledby="process-title">
      <div class="container">
        <div class="section-heading centered" data-reveal><p class="eyebrow">İlk fikirden son dokunuşa</p><h2 id="process-title">$process_title</h2></div>
        <ol class="process-grid">$steps</ol>
      </div>
    </section>

    <section id="atolye" class="section container workshop-section" aria-labelledby="workshop-title">
      <div class="workshop-photos" data-reveal>$workshop_pictures<span class="workshop-stamp">Fikirden<br><strong>emeğe.</strong></span></div>
      <div class="workshop-copy" data-reveal>
        <p class="eyebrow">Atölyemiz</p>
        <h2 id="workshop-title">$workshop_title</h2>
        <p>$workshop_text</p>
        <div class="craftsperson"><span class="craft-icon">$craft_icon</span><div><strong>$owner</strong><span>$brand_name · $brand_tagline</span></div></div>
        <a class="text-link" href="#iletisim">Birlikte konuşalım $arrow_icon</a>
      </div>
    </section>

    <section id="iletisim" class="section contact-section" aria-labelledby="contact-title">
      <div class="container contact-inner" data-reveal>
        $contact_logo
        <p class="eyebrow">Bir telefon kadar yakınız</p>
        <h2 id="contact-title">$contact_title</h2>
        <p class="contact-text">$contact_text</p>
        <a class="contact-phone" href="$tel">$phone_display</a>
        <div class="button-row">
          <a class="button button-call" href="$tel">$phone_icon $cta_call</a>
          <a class="button button-wa" href="$whatsapp">$wa_icon $cta_whatsapp</a>
        </div>
        $contact_details
      </div>
    </section>
  </main>
  <footer class="site-footer">
    <div class="container footer-main">
      <a class="brand" href="#">$brand_mark<span class="brand-type"><strong>$brand_name</strong><span>$brand_tagline</span></span></a>
      <p>$footer_text</p><a href="$tel">$phone_display</a>
    </div>
    <div class="container footer-bottom"><span>© $year $brand_name</span><a href="#">Başa dön ↑</a></div>
  </footer>
  <div class="mobile-contact" aria-label="Hızlı iletişim">
    <a class="button button-call" href="$tel">$phone_icon Hemen Ara</a>
    <a class="button button-wa" href="$whatsapp">$wa_icon WhatsApp</a>
  </div>

  <dialog class="lightbox" id="lightbox" aria-labelledby="lightbox-title" aria-describedby="lightbox-description">
    <div class="lightbox-top"><span id="lightbox-count" aria-live="polite"></span><button class="icon-button" type="button" id="lightbox-close" aria-label="Fotoğrafı kapat">$close_icon</button></div>
    <div class="lightbox-stage">
      <button class="icon-button lightbox-prev" type="button" aria-label="Önceki fotoğraf">$left_icon</button>
      <img id="lightbox-image" alt="" width="1600" height="1200">
      <button class="icon-button lightbox-next" type="button" aria-label="Sonraki fotoğraf">$arrow_icon</button>
    </div>
    <div class="lightbox-caption"><div><p class="lightbox-kind" id="lightbox-kind"></p><h2 id="lightbox-title"></h2><p id="lightbox-description"></p></div><a class="button button-wa" id="lightbox-ask" href="$whatsapp">$wa_icon WhatsApp ile sor</a></div>
  </dialog>
</body>
</html>
