#!/usr/bin/env python3
"""Create print-ready catalog QR files and verify the encoded URL by decoding PNG.

Uses the existing OpenCV/Pillow media environment. No network service is involved.
Run again whenever content/site.json's site_url changes.
"""
import json
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def build(root=ROOT):
    site = json.loads((root / 'content/site.json').read_text())
    base = site.get('site_url', '').strip().rstrip('/')
    parsed = urlsplit(base)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError('QR için site_url gerçek bir https:// adresi olmalı.')
    url = base + '/#katalog'
    matrix = cv2.QRCodeEncoder_create().encode(url)
    # Normalize the quiet zone to four white modules for print/scanner reliability.
    y, x = np.where(matrix == 0)
    matrix = np.pad(matrix[y.min():y.max()+1, x.min():x.max()+1], 4, constant_values=255)
    destination = root / 'public/media'
    destination.mkdir(parents=True, exist_ok=True)
    png = Image.fromarray(matrix).resize((matrix.shape[1]*16, matrix.shape[0]*16), Image.Resampling.NEAREST)
    decoded, points, _ = cv2.QRCodeDetector().detectAndDecode(np.array(png))
    if decoded != url or points is None:
        raise ValueError('QR tekrar okunamadı; doğrulanmamış çıktı yazılmadı.')
    png.save(destination / 'katalog-qr.png')
    blocks = ''.join(f'<path d="M{x} {y}h1v1h-1z"/>' for y, x in zip(*np.where(matrix == 0)))
    size = matrix.shape[0]
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" shape-rendering="crispEdges" role="img" aria-labelledby="title"><title id="title">{escape(site["brand"]["name"])} katalog QR kodu</title><rect width="{size}" height="{size}" fill="white"/><g fill="black">{blocks}</g></svg>\n'
    (destination / 'katalog-qr.svg').write_text(svg)
    report = {'url': url, 'decoded': decoded, 'verified': True, 'modules': size, 'png_size': png.size[0], 'quiet_zone_modules': 4}
    report_path = root / 'data/reports/qr-validation.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    build()
