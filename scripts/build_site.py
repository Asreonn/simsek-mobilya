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
    "prefab": ("prefabrik-ev", "Prefabrik Ev"),
    "hall": ("antre-ayna", "Antre & Ayna"),
}


def build(root=ROOT):
    public = root / "public"
    public.mkdir(parents=True, exist_ok=True)
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
    categories, tabs, gallery = [], [], {}
    card_groups = []
    total = sum(map(len, buckets.values()))
    tabs.append(f'<a class="filter-button" href="#katalog" data-filter="all" aria-controls="model-grid">Tümü <span>{total}</span></a>')
    for key, assets in buckets.items():
        cards = []
        card_groups.append(cards)
        slug, fallback_title = CATEGORY_META[key]
        category = definitions.get(key, {})
        title = category.get("title", fallback_title)
        cover = category.get("cover")
        if cover not in {a["id"] for a in assets}:
            cover = assets[0]["id"]
        categories.append(f'<a class="category-card" href="#katalog/{slug}" data-category-link="{key}"><div class="category-photo">{media.picture(cover, "card", "(max-width: 639px) 46vw, (max-width: 1023px) 30vw, 280px")}</div><div class="category-body"><h3>{e(title)}</h3><span>{len(assets)} model {icon("arrow")}</span></div></a>')
        tabs.append(f'<a class="filter-button" href="#katalog/{slug}" data-filter="{key}" data-slug="{slug}" aria-controls="model-grid">{e(title)} <span>{len(assets)}</span></a>')
        for asset in assets:
            full = [v for v in asset["full"] if v["format"] == "webp"]
            largest = full[-1]
            description = re.split(r"(?<=[.!?])\s+", asset["description"])[0]
            gallery[asset["id"]] = {"id": asset["id"], "model_no": asset["model_no"], "title": asset["title"], "description": description,
                "alt": asset["alt_tr"], "role": asset["role"], "category": key, "src": quote(largest["path"]), "srcset": media.srcset(full),
                "width": largest["w"], "height": largest["h"], "whatsapp": whatsapp(f'Merhaba, {asset["model_no"]} modeli hakkında bilgi almak istiyorum.')}
            badge = '<span class="work-badge">Uygulamamız</span>' if asset["role"] == "provided" else ''
            cards.append(f'<article class="model-card" data-category="{key}"><a class="product-link" href="{e(quote(largest["path"]))}" data-lightbox="{e(asset["id"])}" aria-label="{e(asset["title"])} — Model No: {e(asset["model_no"])}"><div class="product-photo">{media.picture(asset["id"], "card", "(max-width: 639px) 46vw, (max-width: 1023px) 30vw, 23vw")}{badge}</div><div class="model-body"><h3>{e(asset["title"])}</h3><p>Model No: {e(asset["model_no"])}</p></div></a></article>')

    # Tümü offers a cross-section; category views retain provided-first order.
    cards = [group[index] for index in range(max(map(len, card_groups), default=0)) for group in card_groups if index < len(group)]
    hero = media.assets.get("P-MUT-01") or next(a for assets in buckets.values() for a in assets)
    hero_image = [a for a in hero["full"] if a["format"] == "webp"][-1]
    seo_extra = f'<meta property="og:image" content="{e(absolute(hero_image["path"]))}"><meta property="og:image:alt" content="{e(hero["alt_tr"])}"><meta property="og:image:width" content="{hero_image["w"]}"><meta property="og:image:height" content="{hero_image["h"]}">'
    if base:
        seo_extra += f'<link rel="canonical" href="{e(base)}/"><meta property="og:url" content="{e(base)}/">'
    structured = {"@context": "https://schema.org", "@type": "FurnitureStore", "name": brand["name"], "telephone": phone, "image": absolute(hero_image["path"])}
    if base:
        structured["url"] = base + "/"
    address = brand["address"].strip()
    if address:
        structured["address"] = {"@type": "PostalAddress", "streetAddress": ", ".join(part.strip() for part in address.split(",")[:2]), "addressLocality": "Payas", "addressRegion": "Hatay", "postalCode": "31900", "addressCountry": "TR"}
    if brand["service_area"].strip():
        structured["areaServed"] = brand["service_area"]
    maps = "https://www.google.com/maps/dir/?api=1&destination=" + quote(address, safe="")
    map_embed = "https://maps.google.com/maps?q=" + quote(address, safe="") + "&z=16&output=embed"
    contact_map = f'<iframe class="contact-map" src="{e(map_embed)}" loading="lazy" title="Şimşek Mobilya — Payas atölye konumu" referrerpolicy="no-referrer-when-downgrade"></iframe>' if address else ""
    workshop = [a for a in media.assets.values() if a["category"] == "workshop" and a["role"] == "provided"]
    values = {
        "seo_title": e(site["seo"]["title"]), "seo_description": e(site["seo"]["description"]), "seo_extra": seo_extra,
        "favicon": favicon, "structured_data": json_script(structured), "gallery_data": json_script(gallery),
        "brand_name": e(brand["name"]), "brand_tagline": e(brand["tagline"]), "brand_mark": brand_mark,
        "owner": e(brand["owner"]), "tel": "tel:" + phone, "phone_display": e(brand["phone_display"]),
        "whatsapp": e(whatsapp(site["contact"]["whatsapp_message"])),
        "hero_picture": media.picture(hero["id"], hero=True, sizes="(max-width: 767px) 100vw, 50vw"),
        "hero_preload": media.preload(hero["id"], sizes="(max-width: 767px) 100vw, 50vw"),
        "badges": "".join(f'<li>{icon("check")}{e(badge)}</li>' for badge in site["hero"]["badges"]),
        "categories": "".join(categories), "models": "".join(cards), "filters": "".join(tabs), "model_count": total,
        "workshop_pictures": "".join(media.picture(a["id"], "card", "(max-width: 767px) 46vw, 25vw") for a in workshop[:2]),
        "address": e(address), "map_url": e(maps), "contact_map": contact_map,
        "directions": f'<a class="button button-outline" href="{e(maps)}">{icon("arrow")} Yol Tarifi</a>' if address else "",
        "footer_text": e(site["footer"]["text"]), "year": date.today().year,
    }
    for key in ("eyebrow", "title", "subtitle", "cta_call", "cta_whatsapp"):
        values[key if key.startswith("cta_") else f"hero_{key}"] = e(site["hero"][key])
    for section in ("workshop", "contact"):
        for key in ("title", "text"):
            values[f"{section}_{key}"] = e(site[section].get(key, ""))
    values["catalog_intro"] = e(site.get("catalog", {}).get("intro", "Beğendiğiniz modeli seçin, ölçü ve renk seçeneklerini konuşalım."))
    values.update({f"{name}_icon": icon(name) for name in ICONS})
    document = Template((root / "src/index.html.tpl").read_text(encoding="utf-8")).substitute(values)
    (public / "index.html").write_text(document, encoding="utf-8")
    (public / "assets").mkdir(exist_ok=True)
    for filename in ("site.css", "site.js"):
        shutil.copyfile(root / "src" / filename, public / "assets" / filename)
    robots = "User-agent: *\nAllow: /\n"
    sitemap = public / "sitemap.xml"
    if base:
        sitemap.write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{e(base)}/</loc></url></urlset>\n', encoding="utf-8")
        robots += f"Sitemap: {base}/sitemap.xml\n"
    elif sitemap.is_file():
        sitemap.unlink()
    (public / "robots.txt").write_text(robots, encoding="utf-8")
    print(f"Site hazır: {public / 'index.html'} · {total} model · {len(buckets)} kategori")
    print(f"CSS: {(public / 'assets/site.css').stat().st_size:,} bayt · JS: {(public / 'assets/site.js').stat().st_size:,} bayt")


if __name__ == "__main__":
    build()
