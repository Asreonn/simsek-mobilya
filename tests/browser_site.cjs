// Run against `make serve`: PLAYWRIGHT_MODULE=/path/to/playwright node tests/browser_site.cjs
// Browser tooling is optional and is not a runtime dependency of the catalog.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const url = process.env.SITE_TEST_URL || 'http://127.0.0.1:8080';
const output = path.resolve(__dirname, '../work/screens');
const storageKey = 'simsek-mobilya-picks-v1';
(async () => {
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const report = { widths: [], flows: [], errors: [], failedRequests: [] };
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce', hasTouch: true });
    await context.route('https://maps.google.com/**', route => route.fulfill({ contentType: 'text/html', body: '<p>Map test fixture</p>' }));
    const page = await context.newPage();
    page.on('pageerror', error => report.errors.push(error.message));
    page.on('response', response => { if (response.status() >= 400 && response.url().startsWith(url)) report.failedRequests.push(response.url()); });
    const layout = async () => page.evaluate(() => ({
      width: innerWidth, scroll: document.documentElement.scrollWidth,
      smallText: [...document.querySelectorAll('body *')].filter(el => !el.classList.contains('hero-caption') && !el.children.length && el.textContent.trim() && el.getBoundingClientRect().width && parseFloat(getComputedStyle(el).fontSize) < 14).map(el => el.className),
    }));
    for (const width of [320, 360, 390, 820, 900, 1024, 1200, 1440]) {
      await page.setViewportSize({ width, height: 900 }); await page.goto(url); await page.evaluate(() => document.fonts.ready);
      const metrics = await layout();
      assert(metrics.scroll <= width, `Horizontal overflow: ${JSON.stringify(metrics)}`);
      assert.deepEqual(metrics.smallText, []); report.widths.push(metrics);
      assert.equal(await page.locator('.model-card:visible').count(), 12);
    }
    const gallery = await page.locator('#gallery-data').evaluate(el => JSON.parse(el.textContent));
    const entries = Object.values(gallery);
    const allCount = entries.length;
    assert.equal(allCount, await page.locator('.model-card').count());
    for (const category of ['kitchen', 'coffee', 'wardrobe', 'tv', 'armchair', 'hall', 'all']) {
      await page.locator(`[data-filter="${category}"]`).click();
      const shown = await page.locator('.model-card:visible').evaluateAll(cards => cards.map(card => card.dataset.category));
      assert(shown.length > 0 && shown.length <= 12);
      if (category !== 'all') assert(shown.every(value => value === category));
    }
    await page.locator('button[data-role="provided"]').click();
    assert(await page.locator('.model-card:visible').evaluateAll(cards => cards.every(card => card.dataset.role === 'provided')));
    await page.locator('[data-filter="armchair"]').click();
    assert(await page.locator('#model-empty').isVisible());
    await page.locator('#reset-role').click();
    assert(await page.locator('.model-card:visible').count() > 0);
    await page.locator('[data-filter="all"]').click();
    await page.locator('#more-models').click();
    assert.equal(await page.locator('.model-card:visible').count(), 24);
    report.flows.push('6 categories, role filter, empty state, pagination');

    for (const [slug, category] of [['mutfak-dolabi', 'kitchen'], ['tv-unitesi', 'tv'], ['kahve-kosesi', 'coffee'], ['gomme-dolap', 'wardrobe'], ['berjer', 'armchair'], ['antre-ayna', 'hall']]) {
      await page.goto(`${url}/${slug}/`);
      assert(await page.locator('.model-card:visible').evaluateAll((cards, key) => cards.every(card => card.dataset.category === key), category));
      await page.locator('.model-card:visible .product-link').first().click();
      assert(await page.locator('#lightbox-image').evaluate(async image => { await image.decode(); return image.naturalWidth > 0; }));
      await page.keyboard.press('Escape');
      await page.locator('[data-filter="all"]').click();
      assert.equal(await page.locator('.model-card:visible').count(), 12);
    }
    await page.goto(url);
    report.flows.push('6 static category pages, relative assets, lightbox and filters');

    const first = await page.locator('.model-card:visible [data-lightbox]').first().getAttribute('data-lightbox');
    const second = await page.locator('.model-card:visible [data-lightbox]').nth(1).getAttribute('data-lightbox');
    await page.locator(`[data-fav="${first}"]`).click();
    await page.locator(`[data-fav="${second}"]`).click();
    assert.equal(await page.locator('#fav-bar-count').textContent(), '2');
    const message = new URL(await page.locator('#fav-send').getAttribute('href')).searchParams.get('text');
    assert(message.includes(gallery[first].title) && message.includes(gallery[second].title));
    assert(!message.includes("ŞM-"));
    await page.reload();
    assert.equal(await page.locator('#fav-bar-count').textContent(), '2');
    await page.locator('.header-actions [data-open-picks]').click();
    assert.equal(await page.locator('.picks-item').count(), 2);
    await page.locator('[data-remove-pick]').first().click();
    assert.equal(await page.locator('.picks-item').count(), 1);
    await page.locator('#picks-clear').click();
    assert(await page.locator('#picks-empty').isVisible());
    assert.equal(await page.locator('#picks-send').isVisible(), false);
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#fav-bar').isVisible(), false);
    report.flows.push('selection, correct WhatsApp message, persistence, removal, clear');

    await page.locator('.model-card:visible .product-link').first().click();
    assert(await page.locator('#lightbox').evaluate(el => el.open));
    assert.equal(await page.locator('#lightbox-close').evaluate(el => el === document.activeElement), true);
    const model = await page.locator('#lightbox-image').getAttribute('src');
    const deepURL = page.url();
    assert(decodeURIComponent(new URL(deepURL).hash).includes(gallery[first].model_no));
    await page.locator('#lightbox-fav').click();
    assert.equal(await page.locator('#lightbox-fav').getAttribute('aria-pressed'), 'true');
    await page.keyboard.press('ArrowRight');
    assert.notEqual(await page.locator('#lightbox-image').getAttribute('src'), model);
    await page.keyboard.press('ArrowLeft');
    assert.equal(await page.locator('#lightbox-image').getAttribute('src'), model);
    await page.locator('#lightbox-zoom').click();
    assert(await page.locator('.zoom-frame').evaluate(el => el.classList.contains('is-zoomed')));
    await page.locator('#lightbox-zoom').click();
    await page.locator('.zoom-frame').dispatchEvent('touchstart', { touches: [{ identifier: 1, clientX: 300, clientY: 200 }] });
    await page.locator('.zoom-frame').dispatchEvent('touchend', { touches: [], changedTouches: [{ identifier: 1, clientX: 100, clientY: 210 }] });
    assert.notEqual(await page.locator('#lightbox-image').getAttribute('src'), model);
    await page.locator('.zoom-frame').dispatchEvent('touchstart', { touches: [{ identifier: 1, clientX: 100, clientY: 200 }, { identifier: 2, clientX: 200, clientY: 200 }] });
    await page.locator('.zoom-frame').dispatchEvent('touchmove', { touches: [{ identifier: 1, clientX: 70, clientY: 200 }, { identifier: 2, clientX: 230, clientY: 200 }] });
    assert(await page.locator('.zoom-frame').evaluate(el => el.classList.contains('is-zoomed')));
    await page.locator('.zoom-frame').dispatchEvent('touchend', { touches: [], changedTouches: [] });
    await page.evaluate(() => { navigator.share = async data => { window.lastShare = data; }; });
    await page.locator('#lightbox-share').click();
    assert((await page.evaluate(() => window.lastShare.url)).includes('#model/'));
    for (let i = 0; i < 15; i++) await page.keyboard.press('Tab');
    assert(await page.locator('#lightbox').evaluate(el => el.contains(document.activeElement)));
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#lightbox').evaluate(el => el.open), false);
    assert(await page.locator('.model-card:visible .product-link').first().evaluate(el => el === document.activeElement));
    await page.goto(deepURL);
    assert(await page.locator('#lightbox').evaluate(el => el.open));
    assert.equal(await page.locator('#lightbox-image').getAttribute('src'), model);
    const ask = new URL(await page.locator('#lightbox-ask').getAttribute('href')).searchParams.get('text');
    assert(ask.includes(gallery[first].title));
    assert(!ask.includes("ŞM-"));
    await page.keyboard.press('Escape');
    await page.locator('.model-card:visible .product-link').first().click();
    await page.goBack(); assert.equal(await page.locator('#lightbox').evaluate(el => el.open), false);
    await page.goForward(); assert(await page.locator('#lightbox').evaluate(el => el.open));
    await page.keyboard.press('Escape');
    report.flows.push('lightbox, model URL, reload, browser back/forward, keyboard focus, swipe, pinch, sharing');

    assert.equal(await page.locator('.map-card iframe').count(), 1);
    assert((await page.locator('.map-card iframe').getAttribute('src')).includes('output=embed'));
    assert.equal(await page.locator('.map-load, #callback-form').count(), 0);
    assert(entries.every(item => item.category !== 'prefab'));
    assert.equal(await page.locator('[data-filter="prefab"], [data-category-link="prefab"]').count(), 0);
    assert(await page.locator('.button-call, .button-primary, .step-no').evaluateAll(elements => elements.every(element => getComputedStyle(element).color === 'rgb(255, 255, 255)')));
    await page.evaluate(key => localStorage.removeItem(key), storageKey);
    await page.setViewportSize({ width: 390, height: 844 }); await page.goto(url);
    assert.equal(await page.locator('.mobile-contact').evaluate(el => el.getBoundingClientRect().top >= innerHeight), true);
    await page.locator('#atolye').scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    assert(await page.locator('.mobile-contact').evaluate(el => el.getBoundingClientRect().top < innerHeight));
    assert((await layout()).scroll <= 390);
    report.flows.push('automatic map, no callback form, white button text, mobile contact bar after hero');

    // Malformed or unavailable storage must not break browsing or in-page selection.
    await page.evaluate(key => localStorage.setItem(key, '{bad json'), storageKey); await page.reload();
    assert.equal(await page.locator('#fav-bar-count').textContent(), '0');
    await page.evaluate(key => localStorage.setItem(key, JSON.stringify(['__proto__', 'no-such-id'])), storageKey); await page.reload();
    assert.equal(await page.locator('#fav-bar-count').textContent(), '0');
    const blocked = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 390, height: 844 } });
    await blocked.addInitScript(() => Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('Denied', 'SecurityError'); } }));
    const blockedPage = await blocked.newPage(); await blockedPage.goto(url);
    await blockedPage.locator('.model-card:visible [data-fav]').first().click();
    assert.equal(await blockedPage.locator('#fav-bar-count').textContent(), '1'); await blocked.close();
    report.flows.push('corrupt, stale and blocked localStorage');

    for (const [width, height, name] of [[390, 844, 'mobile'], [1440, 900, 'desktop']]) {
      await page.setViewportSize({ width, height }); await page.goto(url);
      await page.evaluate(async () => {
        document.querySelectorAll('img').forEach(img => img.loading = 'eager');
        await document.fonts.ready;
        await Promise.all([...document.images].filter(img => img.getAttribute('src')).map(img => img.decode().catch(() => {})));
      });
      assert.equal(await page.locator('img[src]').evaluateAll(images => images.filter(img => !img.naturalWidth).length), 0);
      await page.screenshot({ path: path.join(output, `${name}.png`) });
      await page.screenshot({ path: path.join(output, `${name}-full.png`), fullPage: true });
      await page.locator('.model-card:visible .product-link').first().click();
      assert((await layout()).scroll <= width);
      await page.screenshot({ path: path.join(output, `${name}-lightbox.png`) });
    }
    const noJs = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 360, height: 844 } });
    const fallback = await noJs.newPage(); await fallback.goto(url);
    assert.equal(await fallback.locator('.model-card:visible').count(), allCount);
    assert.equal(await fallback.locator('.fav-button:visible').count(), 0);
    assert(await fallback.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    assert(await fallback.locator('.footer-nav').isVisible()); await noJs.close();
    report.flows.push('decoded images, desktop/mobile screenshots, JavaScript disabled');
    assert.deepEqual(report.errors, []); assert.deepEqual(report.failedRequests, []);
    await fs.writeFile(path.join(output, 'checks.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
