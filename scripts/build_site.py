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
            asset["description"] = public_text(entry["description"])
            asset["alt_tr"] = public_text(entry["alt_tr"])
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
            lqip = generated.get("lqip", "")
            asset["lqip"] = lqip if re.fullmatch(r"data:image/(?:webp|png|avif|jpeg);base64,[A-Za-z0-9+/=]+", lqip) else ""
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
        if asset["lqip"]:
            style += f'background-image:url({asset["lqip"]});background-size:cover;'
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

    def ask(asset):
        message = f'Merhaba, {asset["id"]} modeline benzer bir mobilya istiyorum. Bilgi alabilir miyim?' if asset["role"] == "reference" else f'Merhaba, web sitenizdeki {asset["id"]} fotoğrafı hakkında bilgi almak istiyorum.'
        return whatsapp(message)

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
    logos = media.logo_variants("full")
    if logos:
        logo = next((a for a in logos if a["format"] == "webp"), logos[0])
        contact_logo = f'<div class="contact-logo"><img src="{e(quote(logo["path"]))}" width="{logo["w"]}" height="{logo["h"]}" alt="{e(brand["name"])} logosu" loading="lazy" decoding="async"></div>'
    else:
        contact_logo = f'<div class="contact-logo">{media.picture("LOGO-01", sizes="90px")}</div>' if "LOGO-01" in media.assets else ""
    favicon = ""
    for v in media.logo_variants("favicon"):
        if v["format"] == "png":
            rel = "apple-touch-icon" if v["w"] == 180 else "icon"
            favicon += f'<link rel="{rel}" type="image/png" sizes="{v["w"]}x{v["h"]}" href="{e(quote(v["path"]))}">\n'

    categories = []
    labels = site["models"]["filters"]
    for index, category in enumerate(site["categories"], 1):
        picture = media.picture(category["cover"], "card", "(max-width: 639px) calc(100vw - 40px), (max-width: 1023px) 45vw, (max-width: 1392px) 22vw, 304px")
        categories.append(f'<a class="category-card" href="#modeller" data-category-link="{e(category["key"])}"><div class="category-photo">{picture}<span class="category-index">0{index}</span></div>'
                          f'<div class="category-body"><h3>{e(category["title"])}</h3><p>{e(category["text"])}</p><span class="text-link">Modelleri gör {icon("arrow")}</span></div></a>')
    gallery_data = {}

    def photo_link(asset, group, kind, sizes):
        full = [a for a in asset["full"] if a["format"] == "webp"]
        largest = full[-1]
        gallery_data[asset["id"]] = {
            "id": asset["id"], "title": asset["title"], "description": asset["description"], "alt": asset["alt_tr"],
            "role": asset["role"], "category": asset["category"], "src": quote(largest["path"]), "srcset": media.srcset(full),
            "width": largest["w"], "height": largest["h"], "whatsapp": ask(asset),
        }
        return (f'<a class="photo-link" href="{e(quote(largest["path"]))}" data-lightbox="{e(asset["id"])}" data-gallery="{group}" aria-label="{e(asset["title"])} — Fotoğrafı büyüt">'
                f'{media.picture(asset["id"], kind, sizes)}<span class="zoom-hint">{icon("zoom")}</span></a>')

    projects, models, workshop_pictures = [], [], []
    # Mix categories on the initial "Tümü" view instead of showing only the
    # catalog's first category. Preserve every record and its original metadata.
    buckets = {key: [] for key in labels if key != "all"}
    for asset in media.assets.values():
        if asset["role"] == "reference":
            buckets.setdefault(asset["category"], []).append(asset)
    for category in site["categories"]:
        bucket = buckets.get(category["key"], [])
        bucket.sort(key=lambda asset: asset["id"] != category["cover"])
    ordered_assets = [asset for asset in media.assets.values() if asset["role"] != "reference"]
    while any(buckets.values()):
        for bucket in buckets.values():
            if bucket:
                ordered_assets.append(bucket.pop(0))
    for asset in ordered_assets:
        if asset["role"] == "provided" and asset["category"] != "workshop":
            picture = photo_link(asset, "projects", "full", "(max-width: 639px) calc(100vw - 40px), (max-width: 1392px) 46vw, 626px")
            projects.append(f'<article class="project-card">{picture}<div class="project-caption"><h3>{e(asset["title"])}</h3></div></article>')
        elif asset["role"] == "reference":
            kind = "tall" if asset["height"] > asset["width"] else "full"
            picture = photo_link(asset, "models", kind, "(max-width: 639px) calc(100vw - 40px), (max-width: 1023px) 45vw, (max-width: 1392px) 29vw, 410px")
            models.append(f'<article class="model-card" data-category="{e(asset["category"])}">{picture}<div class="model-body"><div class="model-meta"><span class="model-category">{e(labels.get(asset["category"], asset["category"]))}</span><span class="asset-id">Model No: {e(asset["id"])}</span></div>'
                          f'<h3>{e(asset["title"])}</h3><a class="model-ask" href="{e(ask(asset))}" aria-label="{e(asset["id"])} — {e(site["models"]["ask_label"])}">{icon("wa")} {e(site["models"]["ask_label"])}</a></div></article>')
    for asset_id in ("P-ATL-01", "P-ATL-02"):
        if asset_id in media.assets:
            workshop_pictures.append(media.picture(asset_id, sizes="(max-width: 639px) 44vw, 23vw"))
    hero = media.assets["P-MUT-01"]
    hero_image = [a for a in hero["full"] if a["format"] == "webp"][-1]
    seo_extra = f'<meta property="og:image" content="{e(absolute(hero_image["path"]))}">\n<meta property="og:image:alt" content="{e(hero["alt_tr"])}">\n<meta property="og:image:width" content="{hero_image["w"]}">\n<meta property="og:image:height" content="{hero_image["h"]}">'
    if base:
        seo_extra += f'\n<link rel="canonical" href="{e(base)}/">\n<meta property="og:url" content="{e(base)}/">'
    structured = {"@context": "https://schema.org", "@type": "FurnitureStore", "name": brand["name"], "telephone": phone, "image": absolute(hero_image["path"])}
    if base:
        structured["url"] = base + "/"
    if brand["address"].strip():
        structured["address"] = brand["address"]
    if brand["service_area"].strip():
        structured["areaServed"] = brand["service_area"]
    details = []
    for key, title in (("address", "Adres"), ("hours", "Çalışma saatleri"), ("service_area", "Hizmet bölgesi")):
        if brand[key].strip():
            tag = "address" if key == "address" else "p"
            details.append(f'<{tag}><strong>{title}:</strong> {e(brand[key])}</{tag}>')
    aliases = {"surec": "nasil-calisiriz"}
    values = {
        "seo_title": e(site["seo"]["title"]), "seo_description": e(site["seo"]["description"]),
        "seo_extra": seo_extra, "favicon": favicon, "structured_data": json_script(structured), "gallery_data": json_script(gallery_data),
        "brand_name": e(brand["name"]), "brand_tagline": e(brand["tagline"]), "brand_mark": brand_mark,
        "owner": e(brand["owner"]), "tel": "tel:" + phone, "phone_display": e(brand["phone_display"]),
        "whatsapp": e(whatsapp(site["contact"]["whatsapp_message"])),
        "nav": "".join(f'<a href="#{e(aliases.get(item["id"], item["id"]))}">{e(item["label"])}</a>' for item in site["nav"]),
        "hero_picture": media.picture("P-MUT-01", hero=True),
        "hero_preload": media.preload("P-MUT-01"),
        "badges": "".join(f'<li>{icon("check")}{e(badge)}</li>' for badge in site["hero"]["badges"]),
        "categories": "\n".join(categories), "projects": "\n".join(projects), "models": "\n".join(models),
        "filters": "".join(f'<button class="filter-button" type="button" data-filter="{e(key)}" aria-pressed="{str(key == "all").lower()}" aria-controls="model-grid">{e(label)}</button>' for key, label in labels.items()),
        "steps": "".join(f'<li data-reveal><span class="step-number">0{index}</span><h3>{e(step["title"])}</h3><p>{e(step["text"])}</p></li>' for index, step in enumerate(site["process"]["steps"], 1)),
        "workshop_pictures": "".join(workshop_pictures), "contact_logo": contact_logo,
        "contact_details": f'<div class="contact-details">{"".join(details)}</div>' if details else "",
        "footer_text": e(site["footer"]["text"]), "year": date.today().year,
    }
    for key in ("eyebrow", "title", "subtitle", "cta_call", "cta_whatsapp"):
        values[key if key.startswith("cta_") else f"hero_{key}"] = e(site["hero"][key])
    for section in ("projects", "models", "process", "workshop", "contact"):
        for key in ("title", "intro", "note", "text"):
            values[f"{section}_{key}"] = e(site[section].get(key, ""))
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
    print(f"Site hazır: {public / 'index.html'}")
    print(f"Metin: {'content/site.json' if content_path.is_file() else 'content/site.example.json (yedek)'}")
    print(f"Medya: {len(media.assets)} kayıt; {media.fallback_count} katalog yedeği; {len(projects)} uygulama, {len(models)} örnek model")
    print(f"CSS: {(public / 'assets/site.css').stat().st_size:,} bayt · JS: {(public / 'assets/site.js').stat().st_size:,} bayt")
    print("Sitemap: " + (base + "/sitemap.xml" if base else "site_url boş; üretilmedi"))


if __name__ == "__main__":
    build()
