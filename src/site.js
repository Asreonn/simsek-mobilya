(() => {
  'use strict';
  document.documentElement.classList.add('js');
  const markLoaded = img => { if (img.complete) img.classList.add('is-loaded'); };
  document.querySelectorAll('.lazy-pic img').forEach(markLoaded);
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const menuButton = document.querySelector('.menu-toggle');
  const menu = document.querySelector('.main-nav');
  const setMenu = (open, restoreFocus = false) => {
    menu.classList.toggle('is-open', open);
    menuButton.setAttribute('aria-expanded', String(open));
    menuButton.setAttribute('aria-label', open ? 'Menüyü kapat' : 'Menüyü aç');
    if (restoreFocus) menuButton.focus();
  };
  menuButton.addEventListener('click', () => setMenu(menuButton.getAttribute('aria-expanded') !== 'true'));
  menu.addEventListener('click', event => { if (event.target.closest('a')) setMenu(false); });
  document.addEventListener('click', event => {
    if (!event.target.closest('.site-header')) setMenu(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') setMenu(false, true);
  });
  window.matchMedia('(min-width: 1024px)').addEventListener('change', () => setMenu(false));

  const modelCards = [...document.querySelectorAll('.model-card')];
  const filters = [...document.querySelectorAll('[data-filter]')];
  const modelStatus = document.querySelector('#model-status');
  const moreModels = document.querySelector('#more-models');
  let activeCategory = 'all';
  let modelLimit = 6;
  const updateModels = () => {
    const matching = modelCards.filter(card => activeCategory === 'all' || card.dataset.category === activeCategory);
    modelCards.forEach(card => { card.hidden = true; });
    matching.slice(0, modelLimit).forEach(card => { card.hidden = false; });
    filters.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.filter === activeCategory)));
    const label = filters.find(button => button.dataset.filter === activeCategory)?.textContent.trim() || 'Tümü';
    modelStatus.textContent = matching.length
      ? `${label} · ${matching.length} modelden ${Math.min(modelLimit, matching.length)} tanesi gösteriliyor`
      : 'Bu kategoride henüz örnek model yok. Fikrinizi bize WhatsApp ile anlatabilirsiniz.';
    moreModels.hidden = matching.length <= modelLimit;
  };
  const filterModels = category => {
    activeCategory = filters.some(button => button.dataset.filter === category) ? category : 'all';
    modelLimit = 6;
    updateModels();
  };
  document.querySelector('.filter-list').hidden = false;
  filters.forEach(button => button.addEventListener('click', () => filterModels(button.dataset.filter)));
  document.querySelectorAll('[data-category-link]').forEach(link => {
    link.addEventListener('click', () => {
      filterModels(link.dataset.categoryLink);
      // Move keyboard focus past the category cards into the newly filtered gallery.
      const heading = document.querySelector('#models-title');
      heading.setAttribute('tabindex', '-1');
      heading.focus({ preventScroll: true });
    });
  });
  moreModels.addEventListener('click', () => {
    const matching = modelCards.filter(card => activeCategory === 'all' || card.dataset.category === activeCategory);
    const nextCard = matching[modelLimit];
    modelLimit += 6;
    updateModels();
    nextCard?.querySelector('a').focus({ preventScroll: true });
  });
  updateModels();

  const projects = [...document.querySelectorAll('.project-card')];
  const moreProjects = document.querySelector('#more-projects');
  projects.forEach((card, index) => { card.hidden = index >= 4; });
  moreProjects.hidden = projects.length <= 4;
  moreProjects.addEventListener('click', () => {
    projects.forEach(card => { card.hidden = false; });
    moreProjects.hidden = true;
    projects[4]?.querySelector('a').focus({ preventScroll: true });
  });

  const dialog = document.querySelector('#lightbox');
  const gallery = JSON.parse(document.querySelector('#gallery-data').textContent);
  const image = document.querySelector('#lightbox-image');
  const close = document.querySelector('#lightbox-close');
  let currentGroup = [];
  let currentIndex = 0;
  let opener = null;
  const showImage = index => {
    currentIndex = (index + currentGroup.length) % currentGroup.length;
    const item = gallery[currentGroup[currentIndex]];
    image.alt = item.alt;
    image.width = item.width;
    image.height = item.height;
    image.sizes = '(max-width: 639px) 100vw, min(1180px, 95vw)';
    image.srcset = item.srcset;
    image.src = item.src;
    document.querySelector('#lightbox-title').textContent = item.title;
    document.querySelector('#lightbox-description').textContent = item.description;
    document.querySelector('#lightbox-kind').textContent = `${item.role === 'reference' ? 'Örnek model · Size özel uyarlanır' : item.category === 'workshop' ? 'Atölyemiz' : 'Uygulamalarımız'}${item.role === 'reference' ? ' · Model No: ' + item.id : ''}`;
    document.querySelector('#lightbox-count').textContent = `${currentIndex + 1} / ${currentGroup.length}`;
    document.querySelector('#lightbox-ask').href = item.whatsapp;
    document.querySelectorAll('.lightbox-prev, .lightbox-next').forEach(button => { button.hidden = currentGroup.length < 2; });
  };
  document.addEventListener('click', event => {
    const link = event.target.closest('[data-lightbox]');
    if (!link || !dialog.showModal || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    opener = link;
    currentGroup = [...document.querySelectorAll(`[data-gallery="${link.dataset.gallery}"]`)]
      .filter(candidate => !candidate.closest('[hidden]'))
      .map(candidate => candidate.dataset.lightbox);
    showImage(currentGroup.indexOf(link.dataset.lightbox));
    dialog.showModal();
    document.body.classList.add('modal-open');
    close.focus();
  });
  close.addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => {
    document.body.classList.remove('modal-open');
    image.removeAttribute('src');
    image.removeAttribute('srcset');
    opener?.focus({ preventScroll: true });
  });
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  });
  document.querySelector('.lightbox-prev').addEventListener('click', () => showImage(currentIndex - 1));
  document.querySelector('.lightbox-next').addEventListener('click', () => showImage(currentIndex + 1));
  dialog.addEventListener('keydown', event => {
    if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
      event.preventDefault();
      showImage(currentIndex + (event.key === 'ArrowRight' ? 1 : -1));
    }
  });
  let touchStart = null;
  image.addEventListener('touchstart', event => {
    touchStart = event.touches.length === 1 ? { x: event.touches[0].clientX, y: event.touches[0].clientY } : null;
  }, { passive: true });
  image.addEventListener('touchend', event => {
    if (!touchStart || !event.changedTouches.length) return;
    const dx = event.changedTouches[0].clientX - touchStart.x;
    const dy = event.changedTouches[0].clientY - touchStart.y;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.4) showImage(currentIndex + (dx < 0 ? 1 : -1));
    touchStart = null;
  }, { passive: true });
  image.addEventListener('touchcancel', () => { touchStart = null; }, { passive: true });

  if ('IntersectionObserver' in window && !reducedMotion.matches) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    }), { threshold: 0.08 });
    document.querySelectorAll('[data-reveal]').forEach(element => {
      element.classList.add('reveal-ready');
      observer.observe(element);
    });
    reducedMotion.addEventListener('change', () => {
      if (reducedMotion.matches) {
        observer.disconnect();
        document.querySelectorAll('.reveal-ready').forEach(element => element.classList.add('is-visible'));
      }
    });
  }
})();
