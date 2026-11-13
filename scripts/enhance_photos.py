#!/usr/bin/env python3
"""Conservative, reproducible catalog derivatives. Masters are opened read-only.

Only catalog.json supplies image records. Overrides accept wb: false and an
optional normalized focus: [x, y] per ID. Logo boxes use EXIF-corrected pixels.
The emblem crop is padded with its corner color to square, never stretched.
Portraits get tall variants; every photo gets full and card variants when the
source permits the requested width. Encoding uses fixed settings and one codec
thread per process. `generated` uses SOURCE_DATE_EPOCH, otherwise input mtimes.
"""
from __future__ import annotations

import argparse
import base64
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import hashlib
import html
import io
import json
import multiprocessing
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import quote

import cv2
import numpy as np
from PIL import Image, ImageCms, ImageFilter, ImageOps, features

ROOT = Path(__file__).resolve().parents[1]
FULL_WIDTHS = (640, 1024, 1600, 2048)
CROP_WIDTHS = (480, 800)
VERSION = 1


def initialize_worker():
    cv2.setNumThreads(1)
    cv2.setRNGSeed(0)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_srgb(path):
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source)
        profile = image.info.get('icc_profile')
        if profile:
            image = ImageCms.profileToProfile(
                image, ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                ImageCms.createProfile('sRGB'), outputMode='RGB')
        else:
            image = image.convert('RGB')
        # New pixels carry no EXIF, ICC, XMP, or source metadata into encoders.
        return Image.fromarray(np.array(image))


def white_balance(rgb, enabled=True):
    if not enabled:
        return rgb.copy(), [1.0, 1.0, 1.0]
    sample = rgb[::max(1, rgb.shape[0] // 512), ::max(1, rgb.shape[1] // 512)]
    brightness = sample.mean(axis=2)
    valid = sample[(brightness > 12) & (brightness < 245)]
    if not valid.size:
        return rgb.copy(), [1.0, 1.0, 1.0]
    gray = valid.mean(axis=0)
    bright = valid[valid.mean(axis=1) >= np.percentile(valid.mean(axis=1), 90)].mean(axis=0)
    estimate = (.65 * gray + .35 * bright).astype(np.float64)
    gain = np.clip(1 + .6 * (estimate.mean() / np.maximum(estimate, 1) - 1), .88, 1.12)
    return np.clip(rgb * gain, 0, 255).astype(np.float32), gain.tolist()


def enhance(image, role, override):
    source = np.asarray(image).astype(np.float32)
    rgb, gains = white_balance(source, override.get('wb', True))
    # Common luminance endpoints preserve channel relationships. Bounds limit
    # level stretch to 8%; flat scenes are deliberately left unstretched.
    luminance = cv2.cvtColor(np.uint8(np.clip(rgb, 0, 255)), cv2.COLOR_RGB2GRAY)
    low, high = np.percentile(luminance, (.3, 99.7))
    black, white = min(float(low), 8), max(float(high), 244)
    rgb = np.clip((rgb - black) * min(1.08, 255 / (white - black)), 0, 255).astype(np.uint8)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    light = lab[:, :, 0].astype(np.float32)
    local = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8)).apply(lab[:, :, 0])
    light = .55 * light + .45 * local
    t = light / 255
    # Gentle toe lift and shoulder roll-off, zero at black/white (max < 3 DN).
    light += 255 * (.035 * t * (1 - t) + .025 * t * (1 - t) * (1 - 2 * t))
    lab[:, :, 0] = np.uint8(np.clip(np.rint(light), 0, 255))
    rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB).astype(np.float32) / 255
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    hsv[:, :, 1] *= 1 + .12 * (1 - hsv[:, :, 1])
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 1)
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    # Sub-percent warmth, attenuated in saturated colors and highlights.
    warmth = (1 - hsv[:, :, 1]) * (1 - .7 * hsv[:, :, 2])
    rgb[:, :, 0] += .004 * warmth
    rgb[:, :, 2] -= .003 * warmth
    result = np.uint8(np.clip(np.rint(rgb * 255), 0, 255))
    if role == 'provided':
        result = cv2.fastNlMeansDenoisingColored(result, None, 3, 3, 7, 21)
    before = np.mean(np.max(source, axis=2) >= 254)
    after = np.mean(np.max(result, axis=2) >= 254)
    flags = []
    if after - before > .015:
        flags.append('highlight_clipping_increase')
    return Image.fromarray(result), {
        'wb_enabled': override.get('wb', True),
        'wb_gains': [round(g, 6) for g in gains],
        'levels': [round(black, 3), round(white, 3)],
        'highlight_fraction_before': round(float(before), 6),
        'highlight_fraction_after': round(float(after), 6),
    }, flags


def attention(image):
    """Edge + local entropy + spectral residual saliency, no extra models/RNG."""
    sample = image.copy()
    sample.thumbnail((320, 320), Image.Resampling.LANCZOS)
    gray = cv2.cvtColor(np.asarray(sample), cv2.COLOR_RGB2GRAY)
    edges = np.abs(cv2.Laplacian(gray.astype(np.float32), cv2.CV_32F))
    entropy = np.zeros(gray.shape, np.float32)
    for band in range(16):
        probability = cv2.blur(((gray // 16) == band).astype(np.float32), (15, 15))
        entropy -= probability * np.log2(np.maximum(probability, 1e-7))
    spectrum = np.fft.fft2(gray.astype(np.float32))
    log_amplitude = np.log(np.maximum(np.abs(spectrum), 1e-7))
    residual = log_amplitude - cv2.blur(log_amplitude, (3, 3))
    saliency = np.abs(np.fft.ifft2(np.exp(residual + 1j * np.angle(spectrum)))) ** 2
    saliency = cv2.GaussianBlur(saliency.astype(np.float32), (9, 9), 2)
    def normal(array):
        return array / max(float(np.percentile(array, 99)), 1e-7)
    return .35 * normal(edges) + .25 * normal(entropy) + .40 * normal(saliency)


def smart_crop_box(image, ratio, focus=None):
    width, height = image.size
    a, b = ratio
    unit = min(width // a, height // b)
    if unit < 1:
        raise ValueError('Source too small for crop ratio')
    cw, ch = a * unit, b * unit
    if focus is not None:
        if len(focus) != 2 or not all(0 <= n <= 1 for n in focus):
            raise ValueError('focus must contain two numbers in [0, 1]')
        left = min(width - cw, max(0, round(focus[0] * width - cw / 2)))
        top = min(height - ch, max(0, round(focus[1] * height - ch / 2)))
        return (left, top, left + cw, top + ch)
    scores = attention(image)
    sh, sw = scores.shape
    integral = cv2.integral(scores)
    best = None
    # Maximal ratio crop leaves only one meaningful translation axis.
    xs = np.unique(np.rint(np.linspace(0, width - cw, 41)).astype(int))
    ys = np.unique(np.rint(np.linspace(0, height - ch, 41)).astype(int))
    for left in xs:
        for top in ys:
            x0, x1 = round(left * sw / width), round((left + cw) * sw / width)
            y0, y1 = round(top * sh / height), round((top + ch) * sh / height)
            mass = integral[y1, x1] - integral[y0, x1] - integral[y1, x0] + integral[y0, x0]
            center_distance = ((left + cw / 2) / width - .5) ** 2 + ((top + ch / 2) / height - .5) ** 2
            score = mass / max(float(scores.sum()), 1e-7) - .12 * center_distance
            candidate = (float(score), -float(center_distance), -int(top), -int(left))
            if best is None or candidate > best[0]:
                best = (candidate, (int(left), int(top), int(left + cw), int(top + ch)))
    return best[1]


def resized(image, width):
    if width > image.width:
        raise ValueError('Upscaling is forbidden')
    height = max(1, round(image.height * width / image.width))
    small = image.resize((width, height), Image.Resampling.LANCZOS)
    radius, percent = (.55, 48) if width <= 800 else (.8, 60)
    return small.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=3))


def atomic_bytes(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.' + path.name, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(content)
            stream.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def save_variant(root, image, name, fmt):
    path = Path('media') / (name + '.' + fmt)
    buffer = io.BytesIO()
    settings = {'quality': 82, 'method': 5} if fmt == 'webp' else (
        {'quality': 60, 'speed': 6, 'max_threads': 1} if fmt == 'avif' else {})
    image.save(buffer, format=fmt.upper(), **settings)
    atomic_bytes(root / 'public' / path, buffer.getvalue())
    return {'path': path.as_posix(), 'w': image.width, 'h': image.height, 'format': fmt}


def variants(root, image, stem, widths, formats):
    result = []
    for width in widths:
        if width <= image.width:
            output = resized(image, width)
            result.extend(save_variant(root, output, f'{stem}-{width}', fmt) for fmt in formats)
    return result


def placeholders(image):
    tiny = image.resize((24, max(1, round(image.height * 24 / image.width))), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    tiny.filter(ImageFilter.GaussianBlur(1.1)).save(buffer, 'WEBP', quality=35, method=5)
    sample = image.copy()
    sample.thumbnail((128, 128))
    # MEDIANCUT has no random initialization; use the most populous palette bin.
    palette = sample.quantize(colors=8, method=Image.Quantize.MEDIANCUT)
    index = max(palette.getcolors(), key=lambda item: (item[0], -item[1]))[1]
    color = palette.getpalette()[index * 3:index * 3 + 3]
    return 'data:image/webp;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii'), '#' + ''.join(f'{n:02x}' for n in color)


def process_photo(job):
    root, row, override, formats = job
    root = Path(root)
    path = master_path(root, row)
    before = digest(path)
    image = read_srgb(path)
    enhanced, processing, flags = enhance(image, row['role'], override)
    entry = {key: row[key] for key in ('role', 'category', 'title', 'alt_tr')}
    entry.update(width=image.width, height=image.height)
    entry['lqip'], entry['color'] = placeholders(enhanced)
    stem = row['id'].lower()
    entry['full'] = variants(root, enhanced, stem, FULL_WIDTHS, formats)
    crops = {}
    for kind, ratio in (('card', (4, 3)), ('tall', (3, 4))):
        entry[kind] = []
        if kind == 'tall' and image.width >= image.height:
            continue
        box = smart_crop_box(enhanced, ratio, override.get('focus'))
        crops[kind] = list(box)
        entry[kind] = variants(root, enhanced.crop(box), f'{stem}-{kind}', CROP_WIDTHS, formats)
        retained = (box[2] - box[0]) * (box[3] - box[1]) / (image.width * image.height)
        if retained < .5:
            flags.append(kind + '_crop_retains_less_than_half')
    entry.update(source_sha256=before, crops=crops, processing=processing, flags=flags)
    if digest(path) != before:
        raise RuntimeError(f'Master changed during processing: {row["id"]}')
    return row['id'], entry


def foreground_bounds(image, region, threshold):
    left, top, right, bottom = region
    if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
        raise ValueError('Logo verification region outside source')
    gray = np.array(image.convert('L'))[top:bottom, left:right]
    ys, xs = np.where(gray < threshold)
    if not len(xs):
        raise ValueError('No logo foreground in verification region')
    return [left + int(xs.min()), top + int(ys.min()), left + int(xs.max()) + 1, top + int(ys.max()) + 1]


def logo_mark(image, config):
    box = config['crop_box']
    left, top, right, bottom = box
    if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
        raise ValueError('Logo crop outside source')
    threshold = config.get('foreground_threshold', 85)
    emblem = foreground_bounds(image, config['emblem_region'], threshold)
    lettering = foreground_bounds(image, config['lettering_region'], threshold)
    margins = [emblem[0] - left, emblem[1] - top, right - emblem[2], bottom - emblem[3]]
    if min(margins) < 2 or bottom > lettering[1] - 2:
        raise ValueError('Logo crop cuts emblem/roof or includes ŞİMŞEK lettering')
    crop = image.crop(box)
    # A square cut directly from this source would cut the roof or admit text.
    # Add background canvas instead, preserving every pixel of the house/S.
    corners = [crop.getpixel(point) for point in ((0, 0), (crop.width - 1, 0), (0, crop.height - 1), (crop.width - 1, crop.height - 1))]
    color = tuple(int(v) for v in np.median(corners, axis=0))
    side = max(crop.size)
    mark = Image.new('RGB', (side, side), color)
    mark.paste(crop, ((side - crop.width) // 2, (side - crop.height) // 2))
    return mark, {'crop_box': box, 'emblem_bounds': emblem, 'lettering_bounds': lettering,
                  'emblem_margins_ltrb': margins, 'lettering_gap': lettering[1] - bottom,
                  'square_padding': [side - crop.width, side - crop.height], 'verified': True}


def process_logo(root, row, config):
    path = master_path(root, row)
    before = digest(path)
    image = read_srgb(path)
    mark, verification = logo_mark(image, config)
    result = {key: row[key] for key in ('id', 'role', 'category', 'title', 'alt_tr')}
    result.update(width=image.width, height=image.height, source_sha256=before)
    result['full'] = variants(root, image, 'logo-full', (600, 1000), ('webp',))
    result['mark'] = variants(root, mark, 'logo-mark', (192, 384), ('png', 'webp'))
    result['favicon'] = variants(root, mark, 'favicon', (32, 180, 512), ('png',))
    result['crop_verification'] = verification
    if digest(path) != before:
        raise RuntimeError('Logo master changed during processing')
    return result


def master_path(root, row):
    path = (root / row['master']).resolve()
    if not path.is_relative_to((root / 'assets/catalog').resolve()):
        raise ValueError('Master must be under assets/catalog')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*', row['id']):
        raise ValueError('Unsafe asset ID')
    if row.get('sha256') and digest(path) != row['sha256']:
        raise ValueError(f'Master hash differs from catalog: {row["id"]}')
    return path


def preview_html(catalog, manifest):
    esc = html.escape
    sections = []
    def figure(url, label, alt):
        return f'<figure><figcaption>{esc(label)}</figcaption><img loading="lazy" src="{esc(url, quote=True)}" alt="{esc(alt, quote=True)}"></figure>'
    for row in catalog['assets']:
        entry = manifest['logo'] if row['role'] == 'brand' else manifest['assets'][row['id']]
        full = [v for v in entry['full'] if v['format'] == 'webp']
        if not full:
            continue
        chosen = min(full, key=lambda v: abs(v['w'] - 1024))
        before = '../' + quote(row['master'], safe='/')
        after = '../public/' + chosen['path']
        pair = figure(before, 'Önce · kaynak', row['alt_tr']) + figure(after, 'Sonra · katalog', row['alt_tr'])
        details = []
        for kind in ('card', 'tall', 'mark', 'favicon'):
            choices = [v for v in entry.get(kind, []) if v['format'] in ('webp', 'png')]
            if choices:
                variant = choices[0]
                details.append(figure('../public/' + variant['path'], kind, row['alt_tr']))
        audit = entry.get('crop_verification') or {'processing': entry.get('processing'), 'crops': entry.get('crops'), 'flags': entry.get('flags')}
        sections.append(f'<section id="{esc(row["id"])}"><h2>{esc(row["id"])} · {esc(row["title"])}</h2>'
                        f'<p>{esc(row["role"])} · {entry["width"]} × {entry["height"]}</p><div class="pair">{pair}</div>'
                        f'<details><summary>Kadrajlar ve sayısal kontrol</summary><div class="crops">{"".join(details)}</div>'
                        f'<pre>{esc(json.dumps(audit, ensure_ascii=False, indent=2))}</pre></details></section>')
    return '''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fotoğraf işleme · Önce / Sonra</title><style>
body{font:16px/1.5 system-ui,sans-serif;color:#2a1d14;background:#fffaf4;margin:24px auto;max-width:1440px;padding:0 16px}
section{background:white;padding:18px;margin:24px 0;border:1px solid #efe3d6;border-radius:12px}
h2{font-size:20px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;min-width:0}
img{display:block;width:100%;height:auto}figcaption{padding:8px 0;font-weight:600}.crops{display:flex;gap:16px;flex-wrap:wrap;margin:16px 0}
.crops figure{max-width:240px}pre{white-space:pre-wrap;overflow-wrap:anywhere}summary{cursor:pointer;padding:12px 0}
@media(max-width:600px){body{padding:0 8px}.pair{gap:8px}section{padding:8px}h2{font-size:17px}}
</style><h1>Fotoğraf işleme · Önce / Sonra</h1>
<p>Kaynaklar korunur. Sağda WebP q82; kart kadrajları ve logo kontrolü her kaydın altında.
Dar kadraj ve ışık uyarıları flags alanında gösterilir. Dikey fotoğraflar tall varyantı içerir.</p>''' + '\n'.join(sections) + '</html>\n'


def run(root=ROOT, workers=None):
    root = Path(root).resolve()
    initialize_worker()
    catalog_path = root / 'data/media/catalog.json'
    overrides_path = root / 'config/media/enhance_overrides.json'
    catalog = json.loads(catalog_path.read_text())
    overrides = json.loads(overrides_path.read_text())
    rows = catalog['assets']
    ids = [row['id'] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate catalog ID')
    unknown = set(overrides.get('assets', {})) - set(ids)
    if unknown:
        raise ValueError(f'Unknown override IDs: {sorted(unknown)}')
    logos = [row for row in rows if row['role'] == 'brand']
    if len(logos) != 1:
        raise ValueError('Expected exactly one catalog brand record')
    sources = [master_path(root, row) for row in rows]
    # Validate the sensitive logo crop before starting any output writes.
    logo_mark(read_srgb(master_path(root, logos[0])), overrides['logo'])
    formats = ('webp', 'avif') if features.check('avif') else ('webp',)
    if workers is None:
        workers = min(4, os.cpu_count() or 1)
    if workers < 1:
        raise ValueError('workers must be positive')
    jobs = [(str(root), row, overrides.get('assets', {}).get(row['id'], {}), formats)
            for row in rows if row['role'] != 'brand']
    if workers == 1:
        assets = dict(map(process_photo, jobs))
    else:
        # spawn uses pipes, also works where the Python 3.14 forkserver's
        # AF_UNIX listener is unavailable (e.g. restricted build sandboxes).
        with ProcessPoolExecutor(max_workers=workers, initializer=initialize_worker,
                                 mp_context=multiprocessing.get_context('spawn')) as pool:
            assets = dict(pool.map(process_photo, jobs))
    input_paths = [catalog_path, overrides_path, *sources]
    epoch = int(os.environ.get('SOURCE_DATE_EPOCH', max(p.stat().st_mtime for p in input_paths)))
    manifest = {'generated': datetime.fromtimestamp(epoch, timezone.utc).isoformat(),
                'schema_version': VERSION, 'assets': assets,
                'logo': process_logo(root, logos[0], overrides['logo'])}
    atomic_bytes(root / 'data/media/web_manifest.json', (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode())
    atomic_bytes(root / 'preview/enhance.html', preview_html(catalog, manifest).encode())
    output_paths = {variant['path'] for entry in [*assets.values(), manifest['logo']]
                    for kind in ('full', 'card', 'tall', 'mark', 'favicon') for variant in entry.get(kind, [])}
    total = sum((root / 'public' / path).stat().st_size for path in output_paths)
    print(f'{len(assets)} photos + logo; {len(output_paths)} outputs; {total:,} bytes ({total / 1024**2:.2f} MiB); formats: {", ".join(formats)}')
    flagged = {key: entry['flags'] for key, entry in assets.items() if entry['flags']}
    print('Flags: ' + json.dumps(flagged, ensure_ascii=False))
    print('Logo: ' + json.dumps(manifest['logo']['crop_verification']))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, help='process count (default: at most 4)')
    args = parser.parse_args()
    run(workers=args.workers)


if __name__ == '__main__':
    main()
