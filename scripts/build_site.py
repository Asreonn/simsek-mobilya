#!/usr/bin/env python3
"""Render the furniture catalog using only the Python standard library.

Enhanced media is preferred. Catalog fallbacks live in media/catalog/; no media
is ever removed. Content sources are read only, and all text is HTML escaped.
"""
from __future__ import annotations
from datetime import date
from html import escape
import json
from pathlib import Path
import re
import shutil
from string import Template
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def merge(default, actual):
    if isinstance(default, dict) and isinstance(actual, dict):
        return {k: merge(v, actual.get(k, v)) for k, v in default.items()} | {k: v for k, v in actual.items() if k not in default}
    return actual


def e(value):
    return escape(str(value), quote=True)


def json_script(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


ICONS = {
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2A19.8 19.8 0 0 1 3.1 5.2 2 2 0 0 1 5.1 3h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.5 2.1L9 11a16 16 0 0 0 4 4l1.3-1.3a2 2 0 0 1 2.1-.5c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.7 2z"/>',
    "wa": '<path d="M20.5 11.6a8.5 8.5 0 0 1-12.7 7.3L3 20.5l1.5-4.8A8.5 8.5 0 1 1 20.5 11.6Z"/><path d="m8.2 7.5 1.3 2-1 1c.8 1.8 1.8 2.8 3.6 3.6l1-1 2 1.3c-.2 2.8-3.3 2.1-5.6.4C7.2 13 5.5 9.5 8.2 7.5Z"/>',
    "arrow": '<path d="M4 12h16m-6-6 6 6-6 6"/>',
    "left": '<path d="M20 12H4m6-6-6 6 6 6"/>',
    "down": '<path d="M12 4v16m-6-6 6 6 6-6"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "close": '<path d="m6 6 12 12M6 18 18 6"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    "zoom": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4M10.5 7.5v6m-3-3h6"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.1"/>',
    "craft": '<path d="m14 4 6 6-3 3-2-2-8 9-3-3 9-8-2-2zM5 4l3 3m9 10 3 3"/>',
    "heart": '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
    "share": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4m0-11-6.8 4"/>',
    "ruler": '<path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.4 2.4 0 0 1 0-3.4l2.6-2.6a2.4 2.4 0 0 1 3.4 0Z"/><path d="m14.5 12.5 2-2m-5-1 2-2m-5-1 2-2m9 9 2-2"/>',
    "home": '<path d="m3 10 9-7 9 7"/><path d="M5 9v11h14V9"/><path d="M10 20v-6h4v6"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "play": '<path d="M8 5v14l11-7z"/>',
    "quote": '<path d="M7 8H5a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h2v2a3 3 0 0 1-3 3m13-10h-2a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h2v2a3 3 0 0 1-3 3"/>',
}


def icon(name):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">{ICONS[name]}</svg>'



INTERNAL_SENTENCE = re.compile(r"(damga|kırp|filigran|jpeg|şeffaf|referansı?\.?$)", re.I)


def public_text(text):
    """Katalogdaki iç küratörlük notlarını (kırpma, damga, kaynak türü) müşteriye göstermez."""
    text = re.sub(r"^\s*Doğrudan çekim:\s*", "", text)
    text = re.sub(r";\s*[^;.]*referansı(?=\.)", "", text)
    sentences = re.split(r"(?<=\.)\s+", text.strip())
    kept = [s for s in sentences if s and not INTERNAL_SENTENCE.search(s)]
    out = " ".join(kept).strip()
    return (out[:1].upper() + out[1:]) if out else ""


class Media:
    def __init__(self, root, catalog, manifest):
        self.root = root
        self.public = root / "public"
        self.assets = {}
        enhanced = manifest.get("assets", {})
        self.logo = manifest.get("logo", {})
        self.fallback_count = 0
        for entry in catalog["assets"]:
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", entry["id"]) or entry["id"] in self.assets:
                raise ValueError(f'Geçersiz veya yinelenen medya ID: {entry["id"]}')
            asset = dict(entry)
            asset["description"] = public_text(entry.get("description", ""))
            asset["model_no"] = entry.get("model_no") or "ŞM-" + entry["id"]
            asset["alt_tr"] = public_text(entry.get("alt_tr", entry["title"]))
            generated = enhanced.get(entry["id"], self.logo if entry["role"] == "brand" else {})
            full = self.variants(generated.get("full", []))
            if not any(a["format"] == "webp" for a in full):
                full = self.copy_catalog(entry)
                self.fallback_count += 1
            if not full:
                raise ValueError(f'{entry["id"]}: yayınlanabilir WebP bulunamadı')
            asset["full"] = full
            for kind in ("card", "tall"):
                asset[kind] = self.variants(generated.get(kind, []))
            color = generated.get("color", "#EFE3D6")
            asset["color"] = color if re.fullmatch(r"#[a-fA-F0-9]{6}", color) else "#EFE3D6"
            self.assets[entry["id"]] = asset

    def variants(self, items):
        result = []
        for item in items:
            relative = Path(item["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"Geçersiz manifest yolu: {relative}")
            destination = (self.public / relative).resolve()
            if not destination.is_relative_to(self.public.resolve()):
                raise ValueError(f"public/ dışına çıkan medya yolu: {relative}")
            if not destination.is_file():
                continue
            w, h = int(item.get("w", item.get("width", 0))), int(item.get("h", item.get("height", 0)))
            if w > 0 and h > 0:
                result.append({"path": relative.as_posix(), "w": w, "h": h, "format": str(item.get("format", relative.suffix[1:])).lower()})
        return sorted(result, key=lambda a: a["w"])

    def copy_catalog(self, entry):
        variants = []
        for item in entry.get("web", []):
            source = (self.root / item["path"]).resolve()
            if not source.is_relative_to(self.root.resolve()) or source.suffix.lower() != ".webp":
                raise ValueError(f'Geçersiz katalog WebP yolu: {item["path"]}')
            if not source.is_file():
                raise FileNotFoundError(f'Katalog görseli bulunamadı: {item["path"]}')
            relative = Path("media/catalog") / entry["id"].lower() / source.name
            destination = self.public / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists() or source.stat().st_mtime_ns != destination.stat().st_mtime_ns or source.stat().st_size != destination.stat().st_size:
                shutil.copy2(source, destination)
            variants.append({"path": relative.as_posix(), "w": int(item["width"]), "h": int(item["height"]), "format": "webp"})
        return sorted(variants, key=lambda a: a["w"])

    @staticmethod
    def srcset(variants, fmt="webp"):
        return ", ".join(f'{quote(a["path"])} {a["w"]}w' for a in variants if a["format"] == fmt)

    def picture(self, asset_id, kind="full", sizes="100vw", hero=False):
        asset = self.assets[asset_id]
        variants = asset.get(kind) or asset["full"]
        webp = [a for a in variants if a["format"] == "webp"] or [a for a in asset["full"] if a["format"] == "webp"]
        candidate = next((a for a in webp if a["w"] >= (1600 if hero else 600)), webp[-1])
        avif = self.srcset(variants, "avif")
        source = f'<source type="image/avif" srcset="{e(avif)}" sizes="{e(sizes)}">' if avif else ""
        style = f'background-color:{asset["color"]};'
        priority = 'loading="eager" fetchpriority="high"' if hero else 'loading="lazy"'
        cls = "pic" if hero else "pic lazy-pic"
        return (f'<picture class="{cls}" style="{e(style)}">{source}<img src="{e(quote(candidate["path"]))}" '
                f'srcset="{e(self.srcset(webp))}" sizes="{e(sizes)}" width="{candidate["w"]}" height="{candidate["h"]}" '
                f'alt="{e(asset["alt_tr"])}" {priority} decoding="async"></picture>')

    def preload(self, asset_id, sizes="100vw"):
        """Hero görselini HTML ayrıştırılırken indirmeye başlatır (LCP hızlanır)."""
        variants = self.assets[asset_id]["full"]
        for fmt in ("avif", "webp"):
            srcset = self.srcset(variants, fmt)
            if srcset:
                return (f'<link rel="preload" as="image" type="image/{fmt}" imagesrcset="{e(srcset)}" '
                        f'imagesizes="{e(sizes)}" fetchpriority="high">')
        return ""

    def logo_variants(self, key):
        return self.variants(self.logo.get(key, []))


CATEGORY_META = {
    "kitchen": ("mutfak", "Mutfak Dolabı"),
    "coffee": ("kahve-kosesi", "Kahve Köşesi"),
    "wardrobe": ("gomme-dolap", "Gömme Dolap"),
    "tv": ("tv-unitesi", "TV Ünitesi"),
    "armchair": ("berjer", "Berjer"),
    "hall": ("antre-ayna", "Antre & Ayna"),
}

CATEGORY_PAGES = {key: slug for key, slug in (
    ("kitchen", "mutfak-dolabi"), ("coffee", "kahve-kosesi"),
    ("wardrobe", "gomme-dolap"), ("tv", "tv-unitesi"),
    ("armchair", "berjer"), ("hall", "antre-ayna"))}

SAFE_URL = re.compile(r"https://[^\s\"'<>]+")


def smallest_thumb(asset):
    variants = [v for v in asset.get("card", []) if v["format"] == "webp"] or [v for v in asset["full"] if v["format"] == "webp"]
    return variants[0]


def why_html(items):
    icons = ("ruler", "craft", "home")
    return "".join(
        f'<li class="why-item" data-reveal><span class="why-icon">{icon(icons[i % len(icons)])}</span>'
        f'<div><h3>{e(item["title"])}</h3><p>{e(item["text"])}</p></div></li>'
        for i, item in enumerate(items))


def steps_html(items):
    return "".join(
        f'<li class="step" data-reveal><span class="step-no" aria-hidden="true">{i}</span>'
        f'<div><h3>{e(item["title"])}</h3><p>{e(item["text"])}</p></div></li>'
        for i, item in enumerate(items, 1))


def faq_html(items):
    return "".join(f'<details class="faq-item" data-reveal><summary>{e(item["q"])}</summary><p>{e(item["a"])}</p></details>' for item in items)


def testimonials_html(section):
    items = [t for t in section.get("items", []) if str(t.get("text", "")).strip()]
    if not items:
        return ""
    cards = "".join(
        f'<figure class="quote-card" data-reveal>{icon("quote")}<blockquote><p>{e(t["text"])}</p></blockquote>'
        f'<figcaption>{e(t.get("name", ""))}</figcaption></figure>' for t in items)
    return (f'<section id="yorumlar" class="section container" aria-labelledby="quotes-title"><div class="section-heading"><div>'
            f'<p class="eyebrow">Müşterilerimiz</p><h2 id="quotes-title">{e(section.get("title", "Müşterilerimiz ne diyor?"))}</h2></div></div>'
            f'<div class="quote-grid">{cards}</div></section>')


def build(root=ROOT):
    public = root / "public"
    public.mkdir(parents=True, exist_ok=True)
    # Remove only the retired generated page; source photos remain in the library.
    retired_page = public / "prefabrik-ev/index.html"
    if retired_page.is_file():
        retired_page.unlink()
        if not any(retired_page.parent.iterdir()):
            retired_page.parent.rmdir()
    defaults = read_json(root / "content/site.example.json")
    content_path = root / "content/site.json"
    site = merge(defaults, read_json(content_path)) if content_path.is_file() else defaults
    manifest_path = root / "data/media/web_manifest.json"
    media = Media(root, read_json(root / "data/media/catalog.json"), read_json(manifest_path) if manifest_path.is_file() else {})
    brand = site["brand"]
    phone = re.sub(r"[^+0-9]", "", brand["phone_e164"])
    wa_number = re.sub(r"\D", "", brand["whatsapp"])
    if not re.fullmatch(r"\+[0-9]{8,15}", phone) or not re.fullmatch(r"[0-9]{8,15}", wa_number):
        raise ValueError("Telefon veya WhatsApp numarası geçersiz")

    def whatsapp(message):
        return f"https://wa.me/{wa_number}?text={quote(message, safe='')}"

    base = site["site_url"].strip().rstrip("/")
    if base:
        parsed = urlsplit(base)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise ValueError("site_url, https://ornek.com biçiminde olmalı")

    def absolute(path):
        return f"{base}/{quote(path)}" if base else quote(path)

    brand_mark = '<span class="brand-mark brand-monogram" aria-hidden="true">Ş</span>'
    marks = media.logo_variants("mark")
    if marks:
        mark = next((a for a in marks if a["format"] == "webp"), marks[0])
        brand_mark = f'<img class="brand-mark" src="{e(quote(mark["path"]))}" width="{mark["w"]}" height="{mark["h"]}" alt="" decoding="async">'
    favicon = ""
    for v in media.logo_variants("favicon"):
        if v["format"] == "png":
            rel = "apple-touch-icon" if v["w"] == 180 else "icon"
            favicon += f'<link rel="{rel}" type="image/png" sizes="{v["w"]}x{v["h"]}" href="{e(quote(v["path"]))}">\n'

    definitions = {c["key"]: c for c in site["categories"]}
    buckets = {key: sorted([a for a in media.assets.values() if a["category"] == key and a["role"] in ("provided", "reference")], key=lambda a: a["role"] != "provided") for key in CATEGORY_META}
    buckets = {key: assets for key, assets in buckets.items() if assets}
    picks, tabs, gallery = [], [], {}
    card_groups = []
    total = sum(map(len, buckets.values()))
    tabs.append(f'<a class="filter-button" href="#katalog" data-filter="all" aria-controls="model-grid">Tümü</a>')
    for key, assets in buckets.items():
        cards = []
        card_groups.append(cards)
        slug, fallback_title = CATEGORY_META[key]
        category = definitions.get(key, {})
        title = category.get("title", fallback_title)
        cover = category.get("cover")
        if cover not in {a["id"] for a in assets}:
            cover = assets[0]["id"]
        picks.append(f'<a class="pick" href="#katalog/{slug}" data-category-link="{key}"><span class="pick-photo">{media.picture(cover, "card", "56px")}</span><span class="pick-text"><strong>{e(title)}</strong></span></a>')
        tabs.append(f'<a class="filter-button" href="#katalog/{slug}" data-filter="{key}" data-slug="{slug}" aria-controls="model-grid">{e(title)}</a>')
        for asset in assets:
            full = [v for v in asset["full"] if v["format"] == "webp"]
            largest = full[-1]
            thumb = smallest_thumb(asset)
            description = re.split(r"(?<=[.!?])\s+", asset["description"])[0]
            gallery[asset["id"]] = {"id": asset["id"], "model_no": asset["model_no"], "title": asset["title"], "description": description,
                "alt": asset["alt_tr"], "role": asset["role"], "category": key, "src": quote(largest["path"]), "srcset": media.srcset(full),
                "thumb": quote(thumb["path"]), "width": largest["w"], "height": largest["h"],
                "whatsapp": whatsapp(f'Merhaba, {asset["model_no"]} modeli hakkında bilgi almak istiyorum.')}
            badge = '<span class="work-badge">Uygulamamız</span>' if asset["role"] == "provided" else ''
            fav = (f'<button class="fav-button" type="button" data-fav="{e(asset["id"])}" aria-pressed="false" '
                   f'aria-label="{e(asset["model_no"])} modelini seçtiklerime ekle">{icon("heart")}</button>')
            label = ("Uygulamamız " if asset["role"] == "provided" else "") + f'{asset["title"]} Model No: {asset["model_no"]}'
            cards.append(f'<article class="model-card" data-category="{key}" data-role="{asset["role"]}"><a class="product-link" href="{e(quote(largest["path"]))}" data-lightbox="{e(asset["id"])}" aria-label="{e(label)}"><div class="product-photo">{media.picture(asset["id"], "card", "(max-width: 639px) 46vw, (max-width: 1023px) 30vw, 23vw")}{badge}</div><div class="model-body"><h3>{e(asset["title"])}</h3><p>Model No: {e(asset["model_no"])}</p></div></a>{fav}</article>')

    # Tümü offers a cross-section; category views retain provided-first order.
    cards = [group[index] for index in range(max(map(len, card_groups), default=0)) for group in card_groups if index < len(group)]

    hero_config = site["hero"]
    pool = {a["id"]: a for assets in buckets.values() for a in assets}
    hero = pool.get(hero_config.get("image", "")) or pool.get("P-MUT-01") or next(iter(pool.values()))
    hero_full = [a for a in hero["full"] if a["format"] == "webp"]
    hero_image = hero_full[-1]
    hero_caption = '<span class="hero-caption">Kendi uygulamalarımızdan</span>' if hero["role"] == "provided" else ""

    og_source = root / "src/og-image.jpg"
    if og_source.is_file():
        (public / "media").mkdir(exist_ok=True)
        shutil.copyfile(og_source, public / "media/og-image.jpg")
        og_path, og_w, og_h = "media/og-image.jpg", 1200, 630
    else:
        og_path, og_w, og_h = hero_image["path"], hero_image["w"], hero_image["h"]

    seo_title, seo_description = e(site["seo"]["title"]), e(site["seo"]["description"])
    seo_extra = (f'<meta property="og:image" content="{e(absolute(og_path))}"><meta property="og:image:alt" content="{e(hero["alt_tr"])}">'
                 f'<meta property="og:image:width" content="{og_w}"><meta property="og:image:height" content="{og_h}">'
                 f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{seo_title}">'
                 f'<meta name="twitter:description" content="{seo_description}"><meta name="twitter:image" content="{e(absolute(og_path))}">')
    if base:
        seo_extra += f'<link rel="canonical" href="{e(base)}/"><meta property="og:url" content="{e(base)}/">'

    address = brand["address"].strip()
    hours = brand.get("hours", "").strip()
    socials = [(label, brand.get(key, "").strip()) for label, key in (("Instagram", "instagram"), ("Facebook", "facebook"))]
    socials = [(label, url) for label, url in socials if SAFE_URL.fullmatch(url)]

    structured = {"@context": "https://schema.org", "@type": "FurnitureStore", "name": brand["name"], "telephone": phone, "image": absolute(og_path), "description": site["seo"]["description"]}
    if base:
        structured["url"] = base + "/"
    if address:
        structured["address"] = {"@type": "PostalAddress", "streetAddress": ", ".join(part.strip() for part in address.split(",")[:2]), "addressLocality": "Payas", "addressRegion": "Hatay", "postalCode": "31900", "addressCountry": "TR"}
    if brand["service_area"].strip():
        structured["areaServed"] = brand["service_area"]
    if socials:
        structured["sameAs"] = [url for _, url in socials]
    maps = "https://www.google.com/maps/dir/?api=1&destination=" + quote(address, safe="")
    map_embed = "https://maps.google.com/maps?q=" + quote(address, safe="") + "&z=16&output=embed"
    map_title = f'{brand["name"]} — Payas atölye konumu'
    contact_map = (f'<div class="map-card"><iframe src="{e(map_embed)}" title="{e(map_title)}" '
                   'loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div>') if address else ""

    faq_items = site.get("faq", [])
    faq_ld = ""
    if faq_items:
        faq_ld = '<script type="application/ld+json">' + json_script({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": item["q"], "acceptedAnswer": {"@type": "Answer", "text": item["a"]}} for item in faq_items]}) + "</script>"

    workshop = [a for a in media.assets.values() if a["category"] == "workshop" and a["role"] == "provided"]
    video = ""
    video_path, poster_path = public / "media/video/montaj.mp4", public / "media/video/montaj-poster.webp"
    if video_path.is_file() and poster_path.is_file():
        video = (f'<div class="video-tile" data-reveal><video id="work-video" controls preload="none" playsinline poster="media/video/montaj-poster.webp" '
                 f'aria-label="Bir mutfağın montajından kısa kayıt"><source src="media/video/montaj.mp4" type="video/mp4"></video>'
                 f'<button class="video-play" type="button" aria-label="Montaj videosunu oynat">{icon("play")}</button>'
                 f'<span class="video-caption">Montajdan kısa kayıt</span></div>')

    directions = f'<a class="button button-outline" href="{e(maps)}">{icon("pin")} Yol Tarifi</a>' if address else ""
    mobile_bar = (f'<a class="button button-call" href="tel:{phone}">{icon("phone")} Ara</a>'
                  f'<a class="button button-wa" href="{e(whatsapp(site["contact"]["whatsapp_message"]))}">{icon("wa")} WhatsApp</a>')
    if address:
        mobile_bar += f'<a class="button button-outline" href="{e(maps)}">{icon("pin")} Konum</a>'

    nav = site["nav"]
    nav_links = "".join(f'<a href="#{e(n["id"])}">{e(n["label"])}</a>' for n in nav)
    domain = site.get("analytics", {}).get("plausible_domain", "").strip()
    analytics = f'<script defer data-domain="{e(domain)}" src="https://plausible.io/js/script.js"></script>' if re.fullmatch(r"[a-z0-9][a-z0-9.-]*", domain) else ""
    fonts_dir = root / "src/fonts"
    font_preload = "".join(f'<link rel="preload" href="assets/fonts/{name}.woff2" as="font" type="font/woff2" crossorigin>\n  '
                           for name in ("inter-latin-compact", "fraunces-latin-compact", "fraunces-tr") if (fonts_dir / f"{name}.woff2").is_file())
    catalog = site["catalog"]
    page_size = max(4, min(48, int(catalog.get("page_size", 12))))

    values = {
        "seo_title": seo_title, "seo_description": seo_description, "seo_extra": seo_extra, "analytics": analytics, "font_preload": font_preload,
        "favicon": favicon, "structured_data": json_script(structured), "faq_ld": faq_ld, "gallery_data": json_script(gallery),
        "brand_name": e(brand["name"]), "brand_tagline": e(brand["tagline"]), "brand_mark": brand_mark,
        "owner": e(brand["owner"]), "tel": "tel:" + phone, "phone_display": e(brand["phone_display"]),
        "site_url_attr": e(base), "wa_number": wa_number, "page_size": page_size,
        "whatsapp": e(whatsapp(site["contact"]["whatsapp_message"])),
        "nav_links": nav_links, "base_tag": "", "default_category": "",
        "category_pages": "".join(f'<a href="{CATEGORY_PAGES[key]}/">{e(definitions.get(key, {}).get("title", CATEGORY_META[key][1]))}</a>' for key in buckets),
        "hero_picture": media.picture(hero["id"], hero=True, sizes="100vw"), "hero_caption": hero_caption,
        "hero_preload": media.preload(hero["id"], sizes="100vw"),
        "picks": "".join(picks), "picks_title": e(hero_config.get("picks_title", "Ne arıyorsunuz?")),
        "why_title": e(site["why"].get("title", "")), "why_items": why_html(site["why"]["items"]),
        "models": "".join(card if i < page_size else card.replace('<article ', '<article hidden data-paged ', 1) for i, card in enumerate(cards)), "filters": "".join(tabs), "model_count": total,
        "catalog_title": e(catalog["title"]), "price_note": e(catalog["price_note"]), "ask_label": e(catalog["ask_label"]),
        "steps_title": e(site["steps"]["title"]), "steps_items": steps_html(site["steps"]["items"]),
        "workshop_pictures": "".join(media.picture(a["id"], "card", "(max-width: 767px) 46vw, 22vw") for a in workshop[:2]), "workshop_video": video,
        "testimonials": testimonials_html(site.get("testimonials", {})),
        "faq_title": e(site["faq_title"]), "faq_items": faq_html(faq_items),
        "address": e(address), "map_url": e(maps), "contact_map": contact_map, "directions": directions,
        "hours_html": f'<p class="contact-hours"><strong>Çalışma saatleri:</strong> {e(hours)}</p>' if hours else "",
        "social_html": "".join(f'<a href="{e(url)}" rel="noopener" target="_blank">{e(label)}</a>' for label, url in socials),
        "address_html": f'<address>{icon("pin")}<span>{e(address)}</span></address>' if address else "",
        "mobile_bar": mobile_bar, "mobile_cols": 3 if address else 2,
        "footer_text": e(site["footer"]["text"]), "year": date.today().year,
    }
    for key in ("eyebrow", "title", "subtitle", "cta_browse", "cta_whatsapp"):
        values[f"hero_{key}"] = e(hero_config[key])
    for section in ("workshop", "contact"):
        for key in ("title", "text"):
            values[f"{section}_{key}"] = e(site[section].get(key, ""))
    values["catalog_intro"] = e(catalog.get("intro", "Beğendiğiniz modeli seçin, ölçü ve renk seçeneklerini konuşalım."))
    values["contact_form_label"] = e(site["contact"]["form_label"])
    values["contact_form_placeholder"] = e(site["contact"]["form_placeholder"])
    values.update({f"{name}_icon": icon(name) for name in ICONS})
    template = Template((root / "src/index.html.tpl").read_text(encoding="utf-8"))

    def render(path, context):
        document = template.substitute(context)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(line.rstrip() for line in document.splitlines()) + "\n", encoding="utf-8")

    render(public / "index.html", values)
    page_urls = [base + "/"] if base else []
    for key, assets in buckets.items():
        slug = CATEGORY_PAGES[key]
        title = definitions.get(key, {}).get("title", CATEGORY_META[key][1])
        category_title = f'{title} Modelleri | {brand["name"]} · {brand["service_area"]}'
        description = definitions.get(key, {}).get("text", "")
        page = dict(values, base_tag='<base href="../">', default_category=key,
                    seo_title=e(category_title), seo_description=e(description),
                    hero_title=e(f'{title} modelleri.'), hero_subtitle=e(description),
                    catalog_title=e(title), catalog_intro=e(description), model_count=len(assets))
        cover = definitions.get(key, {}).get("cover")
        cover = cover if cover in {a["id"] for a in assets} else assets[0]["id"]
        page["hero_picture"] = media.picture(cover, hero=True)
        page["hero_preload"] = media.preload(cover)
        page["hero_caption"] = '<span class="hero-caption">Kendi uygulamalarımızdan</span>' if media.assets[cover]["role"] == "provided" else '<span class="hero-caption">Örnek model · Size özel uyarlanır</span>'
        # Retain all cards for filtering, but the HTML-only view starts in this category.
        page["models"] = "".join(card if f'data-category="{key}"' in card else card.replace('<article ', '<article hidden ', 1) for card in cards)
        page_url = f'{base}/{slug}/' if base else ""
        page["seo_extra"] = re.sub(r'<(?:link rel="canonical"|meta property="og:url")[^>]*>', '', seo_extra)
        if page_url:
            page["seo_extra"] += f'<link rel="canonical" href="{e(page_url)}"><meta property="og:url" content="{e(page_url)}">'
            page_urls.append(page_url)
        # Social metadata must describe the category rather than the home page.
        page["seo_extra"] = page["seo_extra"].replace(f'content="{seo_title}"', f'content="{e(category_title)}"').replace(f'content="{seo_description}"', f'content="{e(description)}"')
        page["structured_data"] = json_script(dict(structured, **({"url": page_url} if page_url else {})))
        render(public / slug / "index.html", page)
    (public / "assets").mkdir(exist_ok=True)
    for filename in ("site.css", "site.js"):
        shutil.copyfile(root / "src" / filename, public / "assets" / filename)
    if fonts_dir.is_dir():
        shutil.copytree(fonts_dir, public / "assets/fonts", dirs_exist_ok=True)
    robots = "User-agent: *\nAllow: /\n"
    sitemap = public / "sitemap.xml"
    if base:
        urls = "".join(f'<url><loc>{e(url)}</loc></url>' for url in page_urls)
        sitemap.write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
        robots += f"Sitemap: {base}/sitemap.xml\n"
    elif sitemap.is_file():
        sitemap.unlink()
    (public / "robots.txt").write_text(robots, encoding="utf-8")
    print(f"Site hazır: {public / 'index.html'} · {total} model · {len(buckets)} kategori")
    print(f"CSS: {(public / 'assets/site.css').stat().st_size:,} bayt · JS: {(public / 'assets/site.js').stat().st_size:,} bayt")


if __name__ == "__main__":
    build()
