#!/usr/bin/env python3
"""Inventory WhatsApp archives; recover visually matching online photographs.

No paid API, account cookies, browser profile, or image-generating service.
Only assets explicitly classified as 'reference' are sent to visual search.
Search results and downloaded files are evidence, not proof of authorship.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import random
import re
import sys
import time
from urllib.parse import parse_qs, urlsplit, urlunsplit
import zipfile

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps
import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT/'config/media'
IMAGES = {'.jpeg', '.jpg', '.png', '.webp', '.avif'}
VIDEOS = {'.mp4', '.mov', '.m4v'}
MAX_BYTES = 30 * 1024 * 1024
MAX_ARCHIVE = 512 * 1024 * 1024


class ServiceBlocked(RuntimeError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path, fallback=None):
    return json.loads(path.read_text()) if path.exists() else fallback


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def immutable_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if digest(path.read_bytes()) != digest(data):
            raise ValueError(f'Existing output differs: {path}')
    else:
        with path.open('xb') as f:
            f.write(data)


def photo_box(image):
    """Suggest the largest photographic band in a white phone screenshot.

    Used ONLY as a search query, never as an approved publication crop.
    Uncertain layouts fall back to a conservative central search region.
    """
    w, h = image.size
    if h / w < 1.6:
        return [0, 0, w, h]
    small = image.convert('RGB').resize((240, round(h * 240 / w)))
    arr = np.asarray(small)[:, 20:220].astype(np.float32)
    white = (arr.min(axis=2) > 235)
    dark = (arr.max(axis=2) < 25)
    detail = ((~white & ~dark).mean(axis=1) > .40)
    gap = max(3, round(len(detail) * .009))
    # Close small white breaks inside the photograph.
    detail = cv2.morphologyEx(detail.astype('uint8')[:, None], cv2.MORPH_CLOSE,
                              np.ones((gap, 1), np.uint8)).ravel()
    runs = []
    start = None
    for y, val in enumerate([*detail, 0]):
        if val and start is None:
            start = y
        elif not val and start is not None:
            if start < len(detail) * .4:
                runs.append((start, y))
            start = None
    if runs:
        a, b = max(runs, key=lambda pair: pair[1] - pair[0])
        if b - a > len(detail) * .25:
            scale = w / 240
            return [round(w * .04), round(a * scale + w * .035),
                    round(w * .96), min(h, round(b * scale - w * .035))]
    return [round(w * .04), round(h * .12), round(w * .96), round(h * .65)]


def audit(args):
    source = args.input.resolve()
    work = args.work.resolve()
    if source == work or source in work.parents:
        raise ValueError('Work directory must be outside the source directory')
    groups = read_json(args.groups, {})
    overrides = read_json(CONFIG/'asset_overrides.json', {})
    assets, inputs, errors = [], [], []

    def ingest(raw, name, container, index):
        suffix = Path(name).suffix.lower()
        if suffix not in IMAGES | VIDEOS:
            return
        sha = digest(raw)
        key = sha[:16]
        original = work / 'originals' / f'{key}{suffix}'
        row = dict(id=key, sha256=sha, container=container, member=name,
                   index=index, bytes=len(raw), path=str(original.relative_to(work)),
                   kind=groups.get(container, 'unclassified'),
                   type='image' if suffix in IMAGES else 'video')
        if key in overrides:
            row['kind'] = overrides[key]['kind']
            row['classification_reason'] = overrides[key]['reason']
        if suffix in IMAGES:
            with Image.open(io.BytesIO(raw)) as im:
                im.load()
                image = ImageOps.exif_transpose(im).convert('RGB')
                row.update(width=image.width, height=image.height, format=im.format,
                           exif_tags=len(im.getexif()))
                thumb = image.copy()
                thumb.thumbnail((360, 320))
                thumb_path = work / 'thumbs' / f'{key}.jpg'
                thumb_path.parent.mkdir(parents=True, exist_ok=True)
                thumb.save(thumb_path, quality=84)
                row['thumbnail'] = str(thumb_path.relative_to(work))
                if row['kind'] == 'reference':
                    row['search_box'] = photo_box(image)
                    query = image.crop(row['search_box'])
                    query.thumbnail((1000, 1200))
                    query_path = work / 'queries' / f'{key}.jpg'
                    query_path.parent.mkdir(parents=True, exist_ok=True)
                    query.save(query_path, quality=92)
                    row['query'] = str(query_path.relative_to(work))
                    row['search_crop_needs_review'] = True
        immutable_write(original, raw)
        assets.append(row)

    for p in sorted(source.iterdir()):
        if not p.is_file() or p.suffix.lower() not in IMAGES | VIDEOS | {'.zip'}:
            continue
        inputs.append(dict(name=p.name, bytes=p.stat().st_size,
                           sha256=digest(p.read_bytes())))
        if p.suffix.lower() == '.zip':
            with zipfile.ZipFile(p) as z:
                if sum(info.file_size for info in z.infolist()) > MAX_ARCHIVE:
                    raise ValueError(f'Archive too large: {p.name}')
                for index, info in enumerate(z.infolist(), 1):
                    if info.is_dir():
                        continue
                    if Path(info.filename).suffix.lower() not in IMAGES | VIDEOS:
                        continue
                    if info.file_size > MAX_BYTES:
                        errors.append(dict(container=p.name, member=info.filename,
                                           error='Member exceeds 30 MiB'))
                        continue
                    try:
                        ingest(z.read(info), info.filename, p.name, index)
                    except (OSError, ValueError, zipfile.BadZipFile) as e:
                        errors.append(dict(container=p.name, member=info.filename,
                                           error=str(e)))
        else:
            try:
                ingest(p.read_bytes(), p.name, p.name, 1)
            except (OSError, ValueError) as e:
                errors.append(dict(container=p.name, error=str(e)))

    samples = {}
    for container in sorted({r['container'] for r in assets}):
        rows = [r for r in assets if r['container'] == container and r['type'] == 'image']
        if not rows:
            continue
        selected = random.Random(args.seed).sample(rows, min(3, len(rows)))
        sheet = Image.new('RGB', (400 * len(selected), 440), '#eeeae4')
        draw = ImageDraw.Draw(sheet)
        for n, row in enumerate(selected):
            with Image.open(work / row['thumbnail']) as im:
                sheet.paste(im, (400*n+(400-im.width)//2, 10))
            draw.text((400*n+12, 342), f"#{row['index']:02d}  {row['id']}", fill='black')
            draw.text((400*n+12, 365), f"{row['width']}x{row['height']} | {row['bytes']//1024} KiB", fill='black')
        sheet_path = work / 'samples' / f'{digest(container.encode())[:12]}.jpg'
        sheet_path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(sheet_path, quality=90)
        samples[container] = dict(ids=[r['id'] for r in selected],
                                  sheet=str(sheet_path.relative_to(work)))
    manifest = dict(created_at=now(), input=str(source), inputs=inputs,
                    assets=assets, samples=samples, errors=errors)
    write_json(work / 'inventory.json', manifest)
    report(args)
    print(json.dumps(dict(assets=len(assets), kinds=dict(Counter(r['kind'] for r in assets)),
                          errors=len(errors), inventory=str(work/'inventory.json')), ensure_ascii=False))
    return 2 if errors else 0


class YandexHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.states = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        state = attrs.get('data-state')
        if state:
            try:
                self.states.append(json.loads(state))
            except ValueError:
                pass


def dedupe_candidates(candidates):
    """One Pinterest photograph can appear under many CDN thumbnail sizes."""
    unique = {}
    for c in candidates:
        p = urlsplit(c['image_url'])
        signature = Path(p.path).stem
        key = ('pinimg:' + signature if p.hostname == 'i.pinimg.com'
               and re.fullmatch(r'[a-f0-9]{32}', signature) else c['image_url'])
        if key not in unique:
            unique[key] = {**c, 'referring_pages': []}
        elif p.hostname == 'i.pinimg.com' and '/originals/' in p.path:
            unique[key]['image_url'] = c['image_url']
        pages = [c.get('page_url', ''), *c.get('referring_pages', [])]
        for page in pages:
            if page and page not in unique[key]['referring_pages']:
                unique[key]['referring_pages'].append(page)
    return list(unique.values())


def parse_search(document):
    parser = YandexHTML()
    parser.feed(document)
    candidates = []
    for state in parser.states:
        state = state.get('initialState', {})
        for item in state.get('cbirSites', {}).get('sites', []):
            media = item.get('originalImage', {})
            if media.get('url'):
                candidates.append(dict(image_url=media['url'], page_url=item.get('url', ''),
                                       title=item.get('title', ''), discovery='yandex_sites'))
        for item in state.get('cbirSimilar', {}).get('thumbs', []):
            url = parse_qs(urlsplit(item.get('linkUrl', '')).query).get('img_url', [''])[0]
            if url:
                candidates.append(dict(image_url=url, page_url='', title=item.get('title', ''),
                                       discovery='yandex_similar'))
    return dedupe_candidates(candidates)


def fetch_bytes(session, url, *, search=False, **kwargs):
    parts = urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname or parts.username:
        raise ValueError('Only public HTTPS URLs are supported')
    with session.request('POST' if 'files' in kwargs else 'GET', url, timeout=(12, 35),
                         stream=True, **kwargs) as response:
        if response.status_code in (403, 429) and search:
            raise ServiceBlocked(f'Search HTTP {response.status_code}; resume later. No automatic retry.')
        response.raise_for_status()
        chunks, length = [], 0
        for chunk in response.iter_content(65536):
            length += len(chunk)
            if length > MAX_BYTES:
                raise ValueError('Response exceeds 30 MiB')
            chunks.append(chunk)
        data = b''.join(chunks)
        if search and ('showcaptcha' in response.url or 'captcha' in response.url or
                       b'<title>Robot' in data or b'Confirm you are not a robot' in data):
            raise ServiceBlocked('Search challenge; no automatic retry or challenge bypass.')
        return data, response.url


def discover(session, query_path, cache_path):
    cached = read_json(cache_path)
    sha = digest(query_path.read_bytes())
    if cached and cached.get('query_sha256') == sha:
        cached['candidates'] = dedupe_candidates(cached['candidates'])
        return cached
    with query_path.open('rb') as f:
        data, _ = fetch_bytes(session, 'https://yandex.com/images/search', search=True,
            params=dict(rpt='imageview', format='json', request=json.dumps({
                'blocks': [{'block': 'b-page_type_search-by-image__link'}]})),
            files={'upfile': ('query.jpg', f, 'image/jpeg')})
    try:
        response = json.loads(data)
        cid = response['blocks'][0]['params']['cbirId']
    except (ValueError, KeyError, IndexError) as e:
        raise ServiceBlocked('Visual-search response changed or requires browser verification') from e
    data, result_url = fetch_bytes(session, 'https://yandex.com/images/search', search=True,
                                 params={'rpt': 'imageview', 'cbir_id': cid})
    candidates = parse_search(data.decode('utf-8'))
    if not candidates:
        # Distinguish a genuine no-result page from a parser/UI change.
        parser = YandexHTML()
        parser.feed(data.decode('utf-8'))
        if not any('initialState' in s for s in parser.states):
            raise ServiceBlocked('Search HTML changed or challenge encountered; inspect manually')
    result = dict(searched_at=now(), query_sha256=sha, search_url=result_url,
                  candidates=candidates)
    write_json(cache_path, result)
    return result


def original_variants(url):
    """Try known source URLs before their explicit thumbnail/proxy wrappers."""
    p = urlsplit(url)
    if p.hostname == 'i.pinimg.com':
        path = re.sub(r'^/[^/]+/', '/originals/', p.path, count=1)
        orig = urlunsplit(('https', p.netloc, path, '', ''))
        # Pinterest thumbnails can be JPEG even when the uploaded original is PNG.
        # These are alternate file formats, not attempts to bypass a challenge.
        stem = orig.rsplit('.', 1)[0]
        return list(dict.fromkeys([orig, stem+'.png', stem+'.webp', url]))
    if p.hostname == 'cdn.dsmcdn.com':
        path = re.sub(r'^/mnresize/\d+/(?:\d+|-)/', '/', p.path)
        return list(dict.fromkeys([urlunsplit(('https', p.netloc, path, p.query, '')), url]))
    if p.hostname in {'lalafo.kg', 'www.lalafo.kg'} and p.path == '/_next/image':
        inner = parse_qs(p.query).get('url', [''])[0]
        host = urlsplit(inner).hostname or ''
        if inner.startswith('https://') and re.fullmatch(r'img\d+\.lalafo\.com', host):
            return list(dict.fromkeys([inner, url]))
    return [url]


def image_match(query, candidate):
    """Geometric AND photometric check; similar furniture is insufficient."""
    def gray(image):
        image = image.convert('RGB').copy()
        image.thumbnail((1100, 1100))
        return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
    a, b = gray(query), gray(candidate)
    detector = cv2.SIFT_create(nfeatures=2500)
    ka, da = detector.detectAndCompute(a, None)
    kb, db = detector.detectAndCompute(b, None)
    result = dict(verified=False, inliers=0, correlation=0.0, coverage=0.0)
    if da is None or db is None or len(da) < 20 or len(db) < 20:
        return result
    pairs = cv2.BFMatcher().knnMatch(da, db, k=2)
    good = [pair[0] for pair in pairs if len(pair) == 2 and pair[0].distance < .70*pair[1].distance]
    if len(good) < 18:
        return result
    src = np.float32([ka[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([kb[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    cv2.setRNGSeed(42)
    matrix, mask = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
    if matrix is None or mask is None:
        return result
    inliers = mask.ravel().astype(bool)
    count = int(inliers.sum())
    ratio = count / len(good)
    hull = cv2.convexHull(src[inliers]) if count >= 3 else None
    coverage = cv2.contourArea(hull) / a.size if hull is not None else 0
    try:
        inverse = np.linalg.inv(matrix)
    except np.linalg.LinAlgError:
        return result
    warped = cv2.warpPerspective(b, inverse, (a.shape[1], a.shape[0]))
    valid = cv2.warpPerspective(np.full_like(b, 255), inverse, (a.shape[1], a.shape[0])) > 250
    # Ignore the outer border and any search UI icons in its corners.
    central = np.zeros_like(valid)
    h, w = a.shape
    central[int(h*.08):int(h*.92), int(w*.08):int(w*.92)] = True
    valid &= central
    fraction = float(valid.sum() / max(1, central.sum()))
    corr = 0.0
    if valid.sum() > 1000 and a[valid].std() > 3 and warped[valid].std() > 3:
        corr = float(np.corrcoef(a[valid], warped[valid])[0, 1])
    result.update(inliers=count, inlier_ratio=round(ratio, 4),
                  correlation=round(corr, 4), coverage=round(coverage, 4),
                  overlap=round(fraction, 4))
    result['verified'] = bool(count >= 18 and ratio >= .5 and coverage >= .15
                              and corr >= .80 and fraction >= .75)
    return result


def find(args):
    work = args.work.resolve()
    inventory = read_json(work/'inventory.json')
    if inventory is None:
        raise ValueError('Run audit first')
    if not args.upload_references:
        raise ValueError('find uploads reference crops to Yandex; pass --upload-references')
    results = read_json(work/'matches.json', {})
    rows = [r for r in inventory['assets'] if r['kind'] == 'reference' and r['type'] == 'image']
    rows = [r for r in rows if not args.ids or r['id'] in args.ids]
    if args.ids and set(args.ids) - {r['id'] for r in rows}:
        raise ValueError('Unknown/non-reference id in --ids')
    rows = [r for r in rows if r['id'] not in results or (
        args.retry and results[r['id']]['status'] != 'matched') or (
        args.upgrade and results[r['id']].get('selected', {}).get('quality_label')
        == 'matching_online_copy')]
    if args.limit:
        rows = rows[:args.limit]
    session = requests.Session()
    session.headers['User-Agent'] = 'MarangozCatalogResearch/1.0'
    blocked = False
    try:
        for n, row in enumerate(rows, 1):
            key = row['id']
            entry = dict(at=now(), status='searching', attempts=[],
                         usage_status='reference_only', authorship='unverified')
            previous = results.get(key)
            print(f'[{n}/{len(rows)}] {key} #{row["index"]}', flush=True)
            try:
                found = discover(session, work/row['query'], work/'search'/f'{key}.json')
                entry['search_url'] = found['search_url']
                entry['candidate_count'] = len(found['candidates'])
                with Image.open(work/row['query']) as q:
                    q.load()
                    best = None
                    seen = set()
                    for c in found['candidates'][:args.candidates]:
                        for url in original_variants(c['image_url']):
                            if url in seen:
                                continue
                            seen.add(url)
                            attempt = dict(image_url=url, page_url=c['page_url'])
                            try:
                                raw, final_url = fetch_bytes(session, url)
                                with Image.open(io.BytesIO(raw)) as im:
                                    im.load()
                                    im = ImageOps.exif_transpose(im)
                                    match = image_match(q, im)
                                    attempt.update(width=im.width, height=im.height, match=match)
                                    if match['verified']:
                                        fmt = (im.format or '').lower()
                                        if not fmt:
                                            with Image.open(io.BytesIO(raw)) as original:
                                                fmt = original.format.lower()
                                        ext = {'jpeg': 'jpg'}.get(fmt, fmt)
                                        target = work/'recovered'/f'{key}_{digest(raw)[:12]}.{ext}'
                                        immutable_write(target, raw)
                                        item = dict(**c, downloaded_url=final_url,
                                            path=str(target.relative_to(work)), sha256=digest(raw),
                                            width=im.width, height=im.height, bytes=len(raw), match=match,
                                            quality_label='pinterest_cdn_originals' if '/originals/' in final_url
                                            and urlsplit(final_url).hostname == 'i.pinimg.com' else 'matching_online_copy')
                                        area = im.width*im.height
                                        if best is None or area > best['width']*best['height']:
                                            best = item
                                        # An originals variant that matches needs no smaller fallback.
                                        break
                            except (requests.RequestException, OSError, ValueError, cv2.error) as e:
                                attempt['error'] = f'{type(e).__name__}: {str(e)[:240]}'
                            finally:
                                entry['attempts'].append(attempt)
                        if best:
                            area = best['width']*best['height']
                            old = previous.get('selected', {}) if previous else {}
                            old_area = old.get('width', 0)*old.get('height', 0)
                            if area >= q.width*q.height and (not args.upgrade or area > old_area):
                                break
                    if best:
                        entry.update(status='matched', selected=best)
                    else:
                        entry['status'] = 'needs_review' if found['candidates'] else 'no_results'
            except ServiceBlocked as e:
                entry.update(status='blocked', error=str(e))
                blocked = True
            except (requests.RequestException, OSError, ValueError) as e:
                entry.update(status='error', error=f'{type(e).__name__}: {str(e)[:240]}')
            # An upgrade attempt must never replace an existing good file with a
            # failed result or a smaller copy. Keep the attempt for review.
            if previous and previous.get('status') == 'matched':
                old = previous['selected']
                new = entry.get('selected')
                if not new or new['width']*new['height'] < old['width']*old['height']:
                    previous['last_upgrade'] = entry
                    entry = previous
            results[key] = entry
            write_json(work/'matches.json', results)
            report(args)
            selected = entry.get('selected', {})
            print(f'  {entry["status"]} {selected.get("width", "")}x{selected.get("height", "")}', flush=True)
            if blocked:
                print(entry.get('error') or entry.get('last_upgrade', {}).get('error'), file=sys.stderr)
                break
            if n < len(rows):
                time.sleep(args.delay)
    finally:
        session.close()
    print(json.dumps(dict(Counter(r['status'] for r in results.values()))))
    return 3 if blocked else 0


def report(args):
    work = args.work.resolve()
    inventory = read_json(work/'inventory.json')
    matches = read_json(work/'matches.json', {})
    notes = read_json(work/'editorial_notes.json', {})
    if inventory is None:
        raise ValueError('Run audit first')
    active_references={r['id'] for r in inventory['assets'] if r['kind']=='reference'}
    matches={key:value for key,value in matches.items() if key in active_references}
    esc = lambda s: html.escape(str(s), quote=True)
    cards = []
    kind_names = dict(reference='Referans', project_candidate='Uygulama adayı',
                      workshop_candidate='Atölye adayı', logo='Logo', unclassified='Sınıflandırılmadı')
    status_names = dict(matched='Eşleşti', needs_review='Elle inceleme gerekli',
                        no_results='Sonuç bulunamadı', blocked='Servis doğrulaması gerekli', error='Hata')
    for row in inventory['assets']:
        key = row['id']
        m = matches.get(key, {})
        image = f'<a href="{esc(row["path"])}"><img loading="lazy" src="{esc(row["thumbnail"])}" alt="{esc(row["member"])}"></a>' if row['type'] == 'image' else '<p>Video</p>'
        selected = m.get('selected')
        recovered = ''
        if selected:
            source_page = (f' · <a href="{esc(selected["page_url"])}">Kaynak sayfa</a>'
                           if selected.get('page_url') else '')
            resolution_note = ''
            if row.get('query'):
                with Image.open(work/row['query']) as query:
                    if selected['width']*selected['height'] < query.width*query.height:
                        resolution_note = '<p>Bulunan kopya arama kırpımından daha az piksel içeriyor; kaliteyi elle kontrol edin.</p>'
            recovered = (f'<a href="{esc(selected["path"])}"><img loading="lazy" src="{esc(selected["path"])}" alt="Eşleşen kaynak"></a>'
                         f'<p>{selected["width"]}×{selected["height"]} · {selected["bytes"]//1024} KiB</p>'
                         f'<p><a href="{esc(selected["downloaded_url"])}">Dosya kaynağı</a>{source_page}</p>{resolution_note}')
        query = f'<a href="{esc(row["query"])}">Arama kırpımı (taslak)</a>' if row.get('query') else ''
        status = status_names.get(m.get('status'), 'Arama bekliyor' if row['kind']=='reference' else 'Yerel dosya')
        editorial = f'<p>{esc(notes[key])}</p>' if key in notes else ''
        cards.append(f'<article data-kind="{esc(row["kind"])}"><h2>#{row["index"]:02d} · {esc(kind_names.get(row["kind"], row["kind"]))}</h2>'
                     f'<p class="small">{esc(row["container"])}<br>{esc(row["member"])}<br>{key}</p>'
                     f'<div class="pair">{image}<div>{recovered}</div></div><p>{query}</p>'
                     f'<p>{esc(status)}</p>{editorial}</article>')
    counts = dict(Counter(m['status'] for m in matches.values()))
    samples = ''.join(f'<p>{esc(name)}<br><a href="{esc(s["sheet"])}">Rastgele örnek sayfası</a></p>'
                      for name, s in inventory['samples'].items())
    document = f'''<!doctype html><html lang="tr"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Şimşek Mobilya — görsel inceleme</title>
<style>body{{font:16px system-ui;margin:32px;background:#f4f0e9;color:#24201d}}h1{{font-size:28px}}h2{{font-size:17px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:20px}}article{{background:white;border:1px solid #d5cabb;padding:16px;border-radius:12px}}img{{max-width:100%;height:260px;object-fit:contain}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}.small{{font-size:12px;overflow-wrap:anywhere}}button{{padding:8px 12px;margin:4px}}a{{color:#684017}}</style>
<h1>Şimşek Mobilya — görsel inceleme</h1><p>Orijinaller değişmedi. Referans eşleşmeleri: {esc(counts)}.</p>
<p>Eşleşme, görselin aynı olduğunu denetler; yazarlığı veya katalogda kullanım hakkını doğrulamaz. “project_candidate” grupları örnek incelemeye dayanır.</p>
<nav><button data-filter="all">Tümü</button><button data-filter="reference">Referans</button><button data-filter="project_candidate">Uygulama</button><button data-filter="workshop_candidate">Atölye</button><button data-filter="logo">Logo</button></nav>
<details><summary>Her paketten rastgele 2–3 örnek (seed=42)</summary>{samples}</details><main class="grid">{''.join(cards)}</main>
<script>document.querySelectorAll('button').forEach(b=>b.onclick=()=>document.querySelectorAll('article').forEach(a=>a.hidden=b.dataset.filter!=='all'&&a.dataset.kind!==b.dataset.filter))</script></html>'''
    (work/'review.html').write_text(document)
    write_json(work/'summary.json', dict(generated_at=now(), total=len(inventory['assets']),
        images=sum(r['type']=='image' for r in inventory['assets']),
        videos=sum(r['type']=='video' for r in inventory['assets']),
        kinds=dict(Counter(r['kind'] for r in inventory['assets'])),
        search_status=counts, errors=len(inventory['errors'])))


def verify(args):
    work = args.work.resolve()
    inventory = read_json(work/'inventory.json')
    if inventory is None:
        raise ValueError('Run audit first')
    failures = []
    for item in inventory['inputs']:
        p = Path(inventory['input'])/item['name']
        if not p.is_file() or digest(p.read_bytes()) != item['sha256']:
            failures.append(str(p))
    for row in inventory['assets']:
        p = work/row['path']
        if not p.is_file() or digest(p.read_bytes()) != row['sha256']:
            failures.append(str(p))
    for item in read_json(work/'matches.json', {}).values():
        selected = item.get('selected')
        if selected:
            p = work/selected['path']
            if not p.is_file() or digest(p.read_bytes()) != selected['sha256']:
                failures.append(str(p))
    print(json.dumps(dict(verified=not failures, failures=failures), ensure_ascii=False))
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=ROOT/'work/catalog')
    sub = parser.add_subparsers(dest='command', required=True)
    a = sub.add_parser('audit', help='Read every asset and sample 3 images per archive; offline')
    a.add_argument('--input', type=Path, default=ROOT/'assets/originals/incoming')
    a.add_argument('--groups', type=Path, default=CONFIG/'asset_sources.json')
    a.add_argument('--seed', type=int, default=42)
    f = sub.add_parser('find', help='Upload reference crops, find and download matching online files')
    f.add_argument('--upload-references', action='store_true')
    f.add_argument('--ids', nargs='+')
    f.add_argument('--limit', type=int, default=0, help='0 = all pending reference images')
    f.add_argument('--candidates', type=int, default=6)
    f.add_argument('--delay', type=float, default=3)
    f.add_argument('--retry', action='store_true', help='Retry non-matched entries, using cached search results')
    f.add_argument('--upgrade', action='store_true', help='Recheck matched copies without a Pinterest originals match')
    sub.add_parser('report', help='Rebuild local HTML review')
    sub.add_parser('verify', help='Check input, extracted and selected recovered file hashes')
    args = parser.parse_args()
    if args.command == 'find' and (args.limit < 0 or args.candidates < 1 or args.delay < 2):
        parser.error('limit >= 0, candidates >= 1, delay >= 2 seconds required')
    try:
        return globals()[args.command](args) or 0
    except (ValueError, OSError, zipfile.BadZipFile) as e:
        print(f'ERROR: {e}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
