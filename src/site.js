(() => {
  'use strict';
  const $ = selector => document.querySelector(selector);
  const $$ = selector => [...document.querySelectorAll(selector)];
  const gallery = JSON.parse($('#gallery-data').textContent);
  const entries = Object.values(gallery);
  const cards = $$('.model-card');
  const filters = $$('[data-filter]');
  const dialog = $('#lightbox');
  const picksDialog = $('#picks-dialog');
  const image = $('#lightbox-image');
  const zoom = $('.zoom-frame');
  const pageSize = Number(document.body.dataset.pageSize) || 12;
  const storageKey = 'simsek-mobilya-picks-v1';
  const announce = message => { $('#live').textContent = message; };
  const track = (name, props = {}) => window.plausible?.(name, { props });
  const waLink = message => `https://wa.me/${document.body.dataset.waNumber}?text=${encodeURIComponent(message)}`;
  const modelHash = item => '#model/' + encodeURIComponent(item.model_no);
  const modelURL = item => new URL(modelHash(item), location.href).href;
  const categoryHash = item => '#katalog/' + filters.find(f => f.dataset.filter === item.category)?.dataset.slug;
  let category = 'all', role = 'all', limit = pageSize;
  let current = null, group = [], opener = null, picksOpener = null, returnHash = '#katalog';
  let selected = new Set();
  let storageAvailable = true;
  try {
    const stored = JSON.parse(localStorage.getItem(storageKey) || '[]');
    if (Array.isArray(stored)) selected = new Set(stored.filter(id => Object.hasOwn(gallery, id)));
  } catch { storageAvailable = false; }

  $$('.pic img').forEach(img => {
    if (img.complete) img.classList.add('is-loaded');
  });
  const matchingCards = () => cards.filter(card => (category === 'all' || card.dataset.category === category) && (role === 'all' || card.dataset.role === role));
  const filterList = $('.filter-list');
  const updateIndicator = () => {
    const active = filters.find(link => link.dataset.filter === category);
    if (active) {
      $('.filter-indicator').style.width = `${active.offsetWidth}px`;
      $('.filter-indicator').style.transform = `translateX(${active.offsetLeft}px)`;
    }
    $('.filter-wrap').classList.toggle('can-left', filterList.scrollLeft > 4);
    $('.filter-wrap').classList.toggle('can-right', filterList.scrollLeft + filterList.clientWidth < filterList.scrollWidth - 4);
  };
  const updateModels = () => {
    const matching = matchingCards();
    const visible = new Set(matching.slice(0, limit));
    cards.forEach(card => { card.hidden = !visible.has(card); });
    filters.forEach(link => {
      if (link.dataset.filter === category) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });
    $$('button[data-role]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.role === role)));
    $('#model-status').textContent = `${matching.length} modelden ${Math.min(limit, matching.length)} tanesi gösteriliyor`;
    $('#more-models').hidden = matching.length <= limit;
    $('#model-empty').hidden = matching.length > 0;
    updateIndicator();
  };
  $$('button[data-role]').forEach(button => button.addEventListener('click', () => {
    role = button.dataset.role; limit = pageSize; updateModels();
  }));
  $('#reset-role').addEventListener('click', () => {
    role = 'all'; limit = pageSize; updateModels();
    $('button[data-role="all"]').focus({ preventScroll: true });
  });
  $('#more-models').addEventListener('click', () => {
    const next = matchingCards()[limit];
    limit += pageSize; updateModels();
    next?.querySelector('a').focus({ preventScroll: true });
  });
  filterList.addEventListener('scroll', updateIndicator, { passive: true });
  window.addEventListener('resize', updateIndicator);
  document.fonts?.ready.then(updateIndicator);

  const syncModal = () => document.body.classList.toggle('modal-open', dialog.open || picksDialog.open);
  const resetZoom = () => {
    zoom.classList.remove('is-zoomed'); image.style.transformOrigin = '';
    $('#lightbox-zoom').setAttribute('aria-pressed', 'false');
  };
  const setZoom = (on, x = .5, y = .5) => {
    zoom.classList.toggle('is-zoomed', on);
    image.style.transformOrigin = `${x * 100}% ${y * 100}%`;
    $('#lightbox-zoom').setAttribute('aria-pressed', String(on));
  };
  const syncFavoriteButtons = () => {
    $$('[data-fav]').forEach(button => {
      const item = gallery[button.dataset.fav], on = selected.has(item.id);
      button.classList.toggle('is-on', on);
      button.setAttribute('aria-pressed', String(on));
      button.setAttribute('aria-label', `${item.model_no} modelini seçtiklerim${on ? 'den çıkar' : 'e ekle'}`);
    });
    if (current) {
      const on = selected.has(current.id);
      $('#lightbox-fav').classList.toggle('is-on', on);
      $('#lightbox-fav').setAttribute('aria-pressed', String(on));
      $('#lightbox-fav span').textContent = on ? 'Seçtiklerimden çıkar' : 'Seçtiklerime ekle';
    }
  };
  const make = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  };
  const thumbnail = item => {
    const img = make('img'); img.src = item.thumb; img.alt = ''; img.width = 120; img.height = 90; img.loading = 'lazy'; return img;
  };
  const renderPicks = () => {
    const list = $('#picks-items'); list.replaceChildren();
    selected.forEach(id => {
      const item = gallery[id], li = make('li', 'picks-item');
      const copy = make('div'), link = make('a', '', item.title);
      link.href = modelHash(item); link.dataset.openModel = item.id;
      copy.append(link, make('small', '', item.model_no));
      const remove = make('button', 'icon-button', '×');
      remove.type = 'button'; remove.dataset.removePick = id;
      remove.setAttribute('aria-label', `${item.model_no} modelini çıkar`);
      li.append(thumbnail(item), copy, remove); list.append(li);
    });
    $('#picks-empty').hidden = selected.size > 0;
    $('.picks-actions').hidden = !selected.size;
  };
  const updatePicks = (save = false) => {
    if (save) {
      try { localStorage.setItem(storageKey, JSON.stringify([...selected])); }
      catch { storageAvailable = false; }
    }
    const count = selected.size;
    document.body.classList.toggle('has-picks', count > 0);
    $('#fav-bar').hidden = count === 0;
    $$('[data-open-picks]').forEach(button => {
      button.hidden = false;
      button.setAttribute('aria-label', `Seçtiklerim: ${count} model`);
    });
    $('.picks-count').textContent = count;
    $('#fav-bar-count').textContent = count;
    const numbers = [...selected].map(id => gallery[id].model_no).join(', ');
    const message = `Merhaba, şu modelleri beğendim: ${numbers}. Ölçü ve fiyat hakkında bilgi alabilir miyim?`;
    const href = waLink(message);
    $('#fav-send').href = href; $('#picks-send').href = href;
    syncFavoriteButtons();
    if (picksDialog.open) renderPicks();
  };
  const togglePick = id => {
    if (!Object.hasOwn(gallery, id)) return;
    const adding = !selected.has(id);
    if (adding) selected.add(id); else selected.delete(id);
    updatePicks(true);
    announce(`${gallery[id].model_no} ${adding ? 'seçtiklerinize eklendi' : 'seçtiklerinizden çıkarıldı'}.${storageAvailable ? '' : ' Bu tarayıcıda seçimler yalnızca sayfa açıkken saklanıyor.'}`);
    track(adding ? 'Model seçildi' : 'Model çıkarıldı', { model: gallery[id].model_no });
    const button = $$('[data-fav]').find(b => b.dataset.fav === id);
    button?.classList.remove('is-pop');
    requestAnimationFrame(() => button?.classList.add('is-pop'));
  };
  window.addEventListener('storage', event => {
    if (event.key !== storageKey && event.key !== null) return;
    try {
      const value = JSON.parse(event.newValue || '[]');
      selected = new Set(Array.isArray(value) ? value.filter(id => Object.hasOwn(gallery, id)) : []);
      updatePicks();
    } catch { /* Leave current selections intact if another tab writes bad data. */ }
  });
  const showModel = (item, push = false) => {
    if (!item) return;
    if (!dialog.open) {
      returnHash = location.hash.startsWith('#model/') ? categoryHash(item) : (location.hash || '#katalog');
      group = matchingCards().map(card => gallery[card.querySelector('[data-lightbox]').dataset.lightbox]).filter(other => other.category === item.category);
      if (!group.some(other => other.id === item.id)) group = entries.filter(other => other.category === item.category);
    }
    current = item; resetZoom();
    image.alt = item.alt; image.width = item.width; image.height = item.height;
    image.sizes = '(max-width: 639px) 100vw, min(1120px, 96vw)';
    image.srcset = item.srcset; image.src = item.src;
    $('#lightbox-title').textContent = item.title;
    $('#lightbox-description').textContent = item.description;
    $('#lightbox-model').textContent = 'Model No: ' + item.model_no;
    $('#lightbox-kind').textContent = item.role === 'provided' ? 'Uygulamamız' : 'Örnek model · Size özel uyarlanır';
    $('#lightbox-count').textContent = `${group.findIndex(other => other.id === item.id) + 1} / ${group.length}`;
    $('#lightbox-ask').href = item.whatsapp;
    $$('.lightbox-prev, .lightbox-next').forEach(button => { button.hidden = group.length < 2; });
    const similar = $('#similar-list'); similar.replaceChildren();
    entries.filter(other => other.category === item.category && other.id !== item.id).slice(0, 4).forEach(other => {
      const button = make('button', 'similar-item'); button.type = 'button'; button.dataset.openModel = other.id;
      button.append(thumbnail(other), make('span', '', other.model_no)); similar.append(button);
    });
    $('#lightbox-similar').hidden = !similar.children.length;
    syncFavoriteButtons();
    if (picksDialog.open) picksDialog.close();
    if (push || !location.hash.startsWith('#model/')) history[push ? 'pushState' : 'replaceState'](null, '', modelHash(item));
    if (!dialog.open) { dialog.showModal(); $('#lightbox-close').focus(); }
    syncModal();
    track('Model görüntülendi', { model: item.model_no });
  };
  const move = direction => {
    if (!group.length) return;
    const index = group.findIndex(item => item.id === current.id);
    const item = group[(index + direction + group.length) % group.length];
    history.replaceState(null, '', modelHash(item)); showModel(item);
  };
  const route = (scroll = false) => {
    if (location.hash.startsWith('#model/')) {
      let value;
      try { value = decodeURIComponent(location.hash.slice(7)); } catch { value = ''; }
      const item = entries.find(item => item.model_no === value || item.id === value);
      if (item) {
        if (!dialog.open && !opener) { category = item.category; updateModels(); }
        showModel(item); return;
      }
      announce('Bu model bulunamadı. Katalogdaki modelleri inceleyebilirsiniz.');
    }
    if (dialog.open) dialog.close();
    const slug = location.hash.startsWith('#katalog/') ? location.hash.slice(9) : '';
    category = filters.find(link => link.dataset.slug === slug)?.dataset.filter || (!location.hash ? document.body.dataset.category : '') || 'all';
    limit = pageSize; updateModels();
    if (scroll && location.hash.startsWith('#katalog')) {
      document.body.classList.remove('header-hidden');
      $('#katalog').scrollIntoView();
      filters.find(link => link.dataset.filter === category)?.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    }
  };
  window.addEventListener('hashchange', () => route(true));
  window.addEventListener('popstate', () => route(true));
  $$('[data-category-link], [data-filter]').forEach(link => link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (link.hash !== location.hash) history.pushState(null, '', link.hash);
    route(true);
  }));
  document.addEventListener('click', event => {
    const fav = event.target.closest('[data-fav]');
    if (fav) { togglePick(fav.dataset.fav); return; }
    const remove = event.target.closest('[data-remove-pick]');
    if (remove) {
      const index = [...selected].indexOf(remove.dataset.removePick);
      togglePick(remove.dataset.removePick);
      const buttons = $$('[data-remove-pick]');
      (buttons[Math.min(index, buttons.length - 1)] || $('#picks-close')).focus();
      return;
    }
    const link = event.target.closest('[data-lightbox], [data-open-model]');
    if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (!dialog.open) opener = link.closest('#picks-dialog') ? picksOpener : link;
    showModel(gallery[link.dataset.lightbox || link.dataset.openModel], !dialog.open);
  });
  $('#lightbox-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => {
    if (dialog.open) return;
    if (location.hash.startsWith('#model/')) history.replaceState(null, '', returnHash);
    resetZoom(); image.removeAttribute('src'); image.removeAttribute('srcset');
    syncModal(); opener?.focus({ preventScroll: true });
  });
  const dismissBackdrop = modal => modal.addEventListener('click', event => {
    if (event.target !== modal) return;
    const r = modal.getBoundingClientRect();
    if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) modal.close();
  });
  dismissBackdrop(dialog); dismissBackdrop(picksDialog);
  $('.lightbox-prev').addEventListener('click', () => move(-1));
  $('.lightbox-next').addEventListener('click', () => move(1));
  dialog.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault(); move(event.key === 'ArrowRight' ? 1 : -1);
    }
  });
  $('#lightbox-fav').addEventListener('click', () => current && togglePick(current.id));
  $('#lightbox-zoom').addEventListener('click', () => setZoom(!zoom.classList.contains('is-zoomed')));
  let touch = null, pinching = false, pinched = false, startDistance = 0;
  zoom.addEventListener('click', event => {
    if (pinched) { pinched = false; return; }
    const r = image.getBoundingClientRect();
    setZoom(!zoom.classList.contains('is-zoomed'), (event.clientX - r.left) / r.width, (event.clientY - r.top) / r.height);
  });
  zoom.addEventListener('pointermove', event => {
    if (!zoom.classList.contains('is-zoomed') || event.pointerType === 'touch') return;
    const r = zoom.getBoundingClientRect();
    image.style.transformOrigin = `${(event.clientX - r.left) / r.width * 100}% ${(event.clientY - r.top) / r.height * 100}%`;
  });
  const distance = touches => Math.hypot(touches[0].clientX - touches[1].clientX, touches[0].clientY - touches[1].clientY);
  zoom.addEventListener('touchstart', event => {
    pinching = event.touches.length === 2;
    if (pinching) { startDistance = distance(event.touches); touch = null; pinched = true; }
    else touch = event.touches.length === 1 ? { x: event.touches[0].clientX, y: event.touches[0].clientY } : null;
  }, { passive: true });
  zoom.addEventListener('touchmove', event => {
    const r = zoom.getBoundingClientRect();
    if (pinching && event.touches.length === 2) {
      event.preventDefault();
      setZoom(distance(event.touches) > startDistance, ((event.touches[0].clientX + event.touches[1].clientX) / 2 - r.left) / r.width, ((event.touches[0].clientY + event.touches[1].clientY) / 2 - r.top) / r.height);
    } else if (zoom.classList.contains('is-zoomed') && event.touches.length === 1) {
      event.preventDefault();
      image.style.transformOrigin = `${(event.touches[0].clientX - r.left) / r.width * 100}% ${(event.touches[0].clientY - r.top) / r.height * 100}%`;
    }
  }, { passive: false });
  zoom.addEventListener('touchend', event => {
    if (touch && !pinching && !zoom.classList.contains('is-zoomed') && event.changedTouches.length) {
      const dx = event.changedTouches[0].clientX - touch.x, dy = event.changedTouches[0].clientY - touch.y;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.4) { pinched = true; move(dx < 0 ? 1 : -1); }
    }
    touch = null; if (!event.touches.length) pinching = false;
  }, { passive: true });
  zoom.addEventListener('touchcancel', () => { touch = null; pinching = false; }, { passive: true });
  $('#lightbox-share').addEventListener('click', async () => {
    if (!current) return;
    const item = current, url = modelURL(item);
    try {
      if (navigator.share) await navigator.share({ title: `${item.title} · ${item.model_no}`, url });
      else if (navigator.clipboard?.writeText) { await navigator.clipboard.writeText(url); announce('Model bağlantısı kopyalandı.'); }
      else window.open(`https://wa.me/?text=${encodeURIComponent(`${item.model_no} ${url}`)}`, '_blank', 'noopener');
    } catch (error) { if (error.name !== 'AbortError') announce('Bağlantıyı adres çubuğundan kopyalayabilirsiniz.'); }
  });
  $$('[data-open-picks]').forEach(button => button.addEventListener('click', () => {
    picksOpener = button; renderPicks(); picksDialog.showModal(); syncModal(); $('#picks-close').focus();
  }));
  $('#picks-close').addEventListener('click', () => picksDialog.close());
  picksDialog.addEventListener('close', () => { syncModal(); if (!dialog.open) picksOpener?.focus({ preventScroll: true }); });
  $('#picks-clear').addEventListener('click', () => {
    selected.clear(); updatePicks(true); $('#picks-close').focus(); announce('Seçtikleriniz temizlendi.');
  });
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href^="https://wa.me/"]');
    if (link) track('WhatsApp', { models: link.id === 'lightbox-ask' ? current?.model_no : [...selected].map(id => gallery[id].model_no).join(', ') });
  });
  $('.wa-form').addEventListener('submit', () => track('WhatsApp mesajı'));
  $$('#callback-form input:not([type="hidden"])').forEach(input => input.addEventListener('input', () => {
    $('#callback-phone').setCustomValidity(''); $('#callback-name').setCustomValidity('');
  }));
  $('#callback-form').addEventListener('submit', event => {
    const phone = $('#callback-phone'), name = $('#callback-name'), digits = phone.value.replace(/\D/g, '').length;
    if (!name.value.trim() || digits < 10 || digits > 15) {
      event.preventDefault();
      const invalid = name.value.trim() ? phone : name;
      invalid.setCustomValidity('Lütfen adınızı ve geçerli bir telefon numarası yazın.'); invalid.reportValidity(); return;
    }
    $('#callback-text').value = `Merhaba, ben ${name.value.trim()}. Mobilya hakkında görüşmek için beni ${phone.value.trim()} numarasından arayabilir misiniz?`;
    track('Arama talebi');
  });
  $$('.map-load').forEach(button => button.addEventListener('click', () => {
    const frame = make('iframe'); frame.title = button.dataset.mapTitle; frame.src = button.dataset.mapSrc;
    frame.loading = 'lazy'; frame.referrerPolicy = 'no-referrer-when-downgrade'; frame.allowFullscreen = true;
    button.closest('.map-card').append(frame);
    frame.tabIndex = 0; frame.focus(); button.hidden = true;
  }));
  const video = $('#work-video');
  if (video) {
    $('.video-play').addEventListener('click', () => video.play().catch(() => announce('Videoyu oynatmak için video denetimlerini kullanın.')));
    video.addEventListener('play', () => video.closest('.video-tile').classList.add('is-playing'));
    video.addEventListener('ended', () => video.closest('.video-tile').classList.remove('is-playing'));
  }
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(records => records.forEach(record => {
      if (record.isIntersecting) { record.target.classList.add('is-in'); observer.unobserve(record.target); }
    }), { threshold: .08 });
    document.documentElement.classList.add('anim');
    $$('[data-reveal]').forEach(element => observer.observe(element));
    const heroObserver = new IntersectionObserver(([record]) => $('.mobile-contact').classList.toggle('is-visible', !record.isIntersecting && record.boundingClientRect.bottom < 0));
    heroObserver.observe($('.hero'));
  } else $('.mobile-contact').classList.add('is-visible');
  let previousY = scrollY, scheduled = false;
  window.addEventListener('scroll', () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      if (Math.abs(scrollY - previousY) > 6) {
        const hide = innerWidth < 900 && scrollY > 180 && scrollY > previousY && !$('.site-header').contains(document.activeElement);
        document.body.classList.toggle('header-hidden', hide); previousY = scrollY;
      }
      scheduled = false;
    });
  }, { passive: true });
  $('.site-header').addEventListener('focusin', () => document.body.classList.remove('header-hidden'));
  window.addEventListener('resize', () => { if (innerWidth >= 900) document.body.classList.remove('header-hidden'); });
  updatePicks(); route();
  if (location.hash.startsWith('#katalog')) requestAnimationFrame(() => route(true));
})();
