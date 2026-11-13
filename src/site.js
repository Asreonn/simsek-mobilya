(() => {
  'use strict';
  document.querySelectorAll('.pic img').forEach(img => {
    if (img.complete) img.classList.add('is-loaded');
  });
  const modelCards = [...document.querySelectorAll('.model-card')];
  const filters = [...document.querySelectorAll('[data-filter]')];
  const modelStatus = document.querySelector('#model-status');
  const moreModels = document.querySelector('#more-models');
  let activeCategory = 'all';
  let modelLimit = 12;
  const matchingCards = () => modelCards.filter(card => activeCategory === 'all' || card.dataset.category === activeCategory);
  const updateModels = () => {
    const matching = matchingCards();
    modelCards.forEach(card => { card.hidden = true; });
    matching.slice(0, modelLimit).forEach(card => { card.hidden = false; });
    filters.forEach(link => {
      if (link.dataset.filter === activeCategory) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });
    modelStatus.textContent = `${matching.length} modelden ${Math.min(modelLimit, matching.length)} tanesi gösteriliyor`;
    moreModels.hidden = matching.length <= modelLimit;
  };
  const route = (scroll = false) => {
    const slug = location.hash.startsWith('#katalog/') ? location.hash.slice(9) : '';
    activeCategory = filters.find(link => link.dataset.slug === slug)?.dataset.filter || 'all';
    modelLimit = 12;
    updateModels();
    if (scroll && location.hash.startsWith('#katalog')) {
      document.querySelector('#katalog').scrollIntoView();
    }
  };
  window.addEventListener('hashchange', () => route(true));
  document.querySelectorAll('[data-category-link], [data-filter]').forEach(link => {
    link.addEventListener('click', () => {
      // Also reset pagination when the selected hash is already current.
      if (link.hash === location.hash) route(true);
      if (link.hasAttribute('data-category-link')) {
        document.querySelector('#models-title').focus({preventScroll: true});
      }
    });
  });
  moreModels.addEventListener('click', () => {
    const nextCard = matchingCards()[modelLimit];
    modelLimit += 12;
    updateModels();
    nextCard?.querySelector('a').focus({preventScroll: true});
  });
  route();
  if (location.hash.startsWith('#katalog/')) {
    requestAnimationFrame(() => document.querySelector('#katalog').scrollIntoView());
  }

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
    document.querySelector('#lightbox-kind').textContent = item.role === 'provided' ? 'Uygulamamız' : 'Örnek model · Size özel uyarlanır';
    document.querySelector('#lightbox-model').textContent = 'Model No: ' + item.model_no;
    document.querySelector('#lightbox-count').textContent = `${currentIndex + 1} / ${currentGroup.length}`;
    document.querySelector('#lightbox-ask').href = item.whatsapp;
    document.querySelectorAll('.lightbox-prev, .lightbox-next').forEach(button => { button.hidden = currentGroup.length < 2; });
  };
  document.addEventListener('click', event => {
    const link = event.target.closest('[data-lightbox]');
    if (!link || !dialog.showModal || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    opener = link;
    currentGroup = [...document.querySelectorAll('[data-lightbox]')]
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

})();
