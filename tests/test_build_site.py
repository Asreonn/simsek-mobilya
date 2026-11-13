"""Integration checks for publishing boundaries and both optional input paths."""
from contextlib import redirect_stdout
from html.parser import HTMLParser
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from urllib.parse import parse_qs, unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_site", ROOT / "scripts/build_site.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tags = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class SiteBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for folder in ("src", "content"):
            (self.root / folder).mkdir()
        for name in ("index.html.tpl", "site.css", "site.js"):
            shutil.copyfile(ROOT / "src" / name, self.root / "src" / name)
        shutil.copyfile(ROOT / "content/site.example.json", self.root / "content/site.example.json")
        self.catalog = json.loads((ROOT / "data/media/catalog.json").read_text())
        # Real metadata and paths, tiny stand-in bytes: this suite checks the build,
        # while the browser QA checks image decoding and layout separately.
        for asset in self.catalog["assets"]:
            for variant in asset["web"]:
                path = self.root / variant["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"webp-test-fixture")
        self.write_json("data/media/catalog.json", self.catalog)
        self.sentinel = self.root / "public/media/other-worker.webp"
        self.sentinel.parent.mkdir(parents=True)
        self.sentinel.write_bytes(b"preserve this")

    def tearDown(self):
        self.temp.cleanup()

    def write_json(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False))

    def build(self):
        with redirect_stdout(io.StringIO()):
            MODULE.build(self.root)
        return (self.root / "public/index.html").read_text()

    def test_no_content_or_manifest_copies_webp_without_removing_media(self):
        source = self.build()
        page = Page(source)
        self.assertIn("Hayalinizdeki mobilyayı birlikte yapalım.", source)
        self.assertEqual(self.sentinel.read_bytes(), b"preserve this")
        self.assertFalse((self.root / "public/sitemap.xml").exists())
        for tag, attrs in page.tags:
            if tag == "img" and attrs.get("src"):
                self.assertTrue((self.root / "public" / unquote(attrs["src"])).is_file())
                self.assertGreater(int(attrs["width"]), 0)
                self.assertGreater(int(attrs["height"]), 0)
                if "srcset" in attrs:
                    self.assertTrue(attrs["sizes"])
        before = source
        self.assertEqual(self.build(), before)
        # Original sources and the other worker's media remain unchanged.
        self.assertEqual(self.sentinel.read_bytes(), b"preserve this")

    def test_enhanced_manifest_uses_solid_color_avif_and_logo(self):
        variants = []
        for fmt in ("webp", "avif"):
            path = f"media/enhanced-1024.{fmt}"
            (self.root / "public" / path).write_bytes(b"enhanced")
            variants.append({"path": path, "w": 1024, "h": 715, "format": fmt})
        (self.root / "public/media/favicon-32.png").write_bytes(b"png")
        self.write_json("data/media/web_manifest.json", {
            "assets": {"P-MUT-01": {"full": variants, "color": "#123456", "lqip": "data:image/webp;base64,AAAA"}},
            "logo": {"favicon": [{"path": "media/favicon-32.png", "w": 32, "h": 32, "format": "png"}]}
        })
        source = self.build()
        self.assertIn('type="image/avif"', source)
        self.assertIn("media/enhanced-1024.webp", source)
        self.assertNotIn("data:image/webp;base64,AAAA", source)
        self.assertIn('sizes="32x32"', source)
        self.assertIn("background-color:#123456", source)

    def test_canonical_sitemap_and_optional_fields_follow_content(self):
        content = {"site_url": "https://example.test/katalog", "brand": {"address": "Bilinen adres", "hours": "09.00–17.00"}, "nav": [{"id": "surec", "label": "Nasıl Çalışırız"}]}
        self.write_json("content/site.json", content)
        original = (self.root / "content/site.json").read_bytes()
        source = self.build()
        self.assertIn('href="https://example.test/katalog/"', source)
        self.assertIn('href="#katalog"', source)
        self.assertIn("Bilinen adres", source)
        sitemap = self.root / "public/sitemap.xml"
        self.assertEqual(ET.parse(sitemap).find(".//{*}loc").text, "https://example.test/katalog/")
        self.assertIn("Sitemap: https://example.test/katalog/sitemap.xml", (self.root / "public/robots.txt").read_text())
        self.assertEqual((self.root / "content/site.json").read_bytes(), original)
        self.write_json("content/site.json", {"site_url": ""})
        self.build()
        self.assertFalse(sitemap.exists())

    def test_reference_messages_and_html_script_escaping(self):
        content = {"hero": {"title": '<script>alert("x")</script>'}, "brand": {"name": "</script><script>alert(1)</script>"}}
        self.write_json("content/site.json", content)
        source = self.build()
        self.assertNotIn('<script>alert("x")</script>', source)
        self.assertIn("&lt;script&gt;", source)
        self.assertIn("\\u003c/script>", source)
        gallery = self.gallery(source)
        for item in gallery.values():
            message = parse_qs(urlsplit(item["whatsapp"]).query)["text"][0]
            self.assertIn(item["title"], message)
            self.assertNotIn(item["model_no"], message)
            self.assertIn(item["src"], message)
        cards = [attrs for tag, attrs in Page(source).tags if tag == "article" and attrs.get("class") == "model-card"]
        expected = [a for a in self.catalog["assets"] if a["role"] in ("reference", "provided") and a["category"] in MODULE.CATEGORY_META]
        self.assertEqual(len(cards), len(expected))

    @staticmethod
    def gallery(source):
        return json.loads(source.split('<script id="gallery-data" type="application/json">')[1].split('</script>')[0])

    def test_v2_category_counts_provided_order_and_automatic_covers(self):
        site = json.loads((ROOT / "content/site.json").read_text())
        self.write_json("content/site.json", site)
        source = self.build()
        page = Page(source)
        gallery = self.gallery(source)
        tiles = [attrs for tag, attrs in page.tags if attrs.get("class") == "pick"]
        active = {a["category"] for a in self.catalog["assets"] if a["category"] in MODULE.CATEGORY_META}
        self.assertEqual(len(tiles), len(active))
        for key in active:
            entries = [a for a in gallery.values() if a["category"] == key]
            roles = [a["role"] for a in entries]
            self.assertEqual(roles, sorted(roles, key=lambda r: r != "provided"))
            first = next(a for a in self.catalog["assets"] if a["id"] == entries[0]["id"])
            tile = source.split(f'data-category-link="{key}">')[1].split('</a>')[0]
            # Cover without explicit ID uses the first provided image, else first reference.
            self.assertIn(first["id"].lower(), tile.lower())
        self.assertNotIn('class="work-badge"', source)
        self.assertNotIn('fonts.googleapis.com', source)
        self.assertNotIn('family=Outfit', source)

    def test_new_categories_model_numbers_invalid_cover_and_internal_notes(self):
        site = json.loads((ROOT / "content/site.json").read_text())
        for c in site["categories"]:
            c["cover"] = "DOES-NOT-EXIST"
        self.write_json("content/site.json", site)
        prototype = next(a for a in self.catalog["assets"] if a["category"] == "kitchen")
        for index, key in enumerate(("wardrobe", "armchair")):
            self.catalog["assets"].append(dict(prototype, id=f"R-NEW-{index}", category=key, model_no=f"ŞM-NEW-{index}", description="Sade bir model. Filigran kırpılmalı. İkinci cümle."))
        self.write_json("data/media/catalog.json", self.catalog)
        source = self.build()
        gallery = self.gallery(source)
        for index, slug in enumerate(("gomme-dolap", "berjer")):
            self.assertIn(f'href="#katalog/{slug}"', source)
            item = gallery[f"R-NEW-{index}"]
            self.assertEqual(item["model_no"], f"ŞM-NEW-{index}")
            self.assertEqual(item["description"], "Sade bir model.")
        old = next(a for a in self.catalog["assets"] if a["category"] == "kitchen")
        old.pop("model_no", None)
        self.write_json("data/media/catalog.json", self.catalog)
        item = self.gallery(self.build())[old["id"]]
        self.assertEqual(item["model_no"], "ŞM-" + old["id"])
        self.assertNotIn("Filigran", source)
        self.assertEqual(MODULE.public_text("Doğrudan çekim: Beyaz dolap. JPEG damga kaldırılmalı."), "Beyaz dolap.")

    def test_contact_directions_embed_and_postal_address(self):
        site = json.loads((ROOT / "content/site.json").read_text())
        self.write_json("content/site.json", site)
        source = self.build()
        page = Page(source)
        iframe = next(attrs for tag, attrs in page.tags if tag == "iframe")
        self.assertEqual(iframe["loading"], "lazy")
        self.assertTrue(iframe["title"])
        self.assertEqual(parse_qs(urlsplit(iframe["src"]).query)["q"][0], site["brand"]["address"])
        self.assertNotIn('map-load', source)
        self.assertNotIn('callback-form', source)
        directions = next(attrs for tag, attrs in page.tags if tag == "a" and attrs.get("href", "").startswith("https://www.google.com/maps/dir/"))
        self.assertEqual(parse_qs(urlsplit(directions["href"]).query)["destination"][0], site["brand"]["address"])
        structured = json.loads(source.split('<script type="application/ld+json">')[1].split('</script>')[0])
        self.assertEqual(structured["@type"], "FurnitureStore")
        self.assertEqual(structured["address"], {"@type": "PostalAddress", "streetAddress": "İstiklal Mahallesi, Müge Sokak No:3", "addressLocality": "Payas", "addressRegion": "Hatay", "postalCode": "31900", "addressCountry": "TR"})
        self.assertIn("0532 652 78 13", source)
        self.assertNotIn("Ücretsiz keşif", source)
        self.assertNotIn("Montaj dahil", source)

    def test_external_manifest_path_is_rejected(self):
        self.write_json("data/media/web_manifest.json", {"assets": {"P-MUT-01": {"full": [{"path": "../outside.webp", "w": 100, "h": 100}]}}})
        with self.assertRaisesRegex(ValueError, "Geçersiz manifest yolu"):
            self.build()

    def test_category_documents_have_unique_metadata_and_complete_sitemap(self):
        self.write_json("content/site.json", {"site_url": "https://example.test/catalog"})
        retired = self.root / "public/prefabrik-ev/index.html"
        retired.parent.mkdir(parents=True)
        retired.write_text("outdated category")
        source = self.build()
        self.assertFalse(retired.exists())
        self.assertNotIn("prefab", source)
        self.assertNotIn("prefabrik", source)
        self.assertFalse(any(item["category"] == "prefab" for item in self.gallery(source).values()))
        urls = [el.text for el in ET.parse(self.root / "public/sitemap.xml").findall(".//{*}loc")]
        active = {a["category"] for a in self.catalog["assets"] if a["category"] in MODULE.CATEGORY_META}
        self.assertEqual(len(urls), len(active) + 1)
        for key in active:
            slug = MODULE.CATEGORY_PAGES[key]
            source = (self.root / "public" / slug / "index.html").read_text()
            page = Page(source)
            self.assertIn(f'https://example.test/catalog/{slug}/', urls)
            self.assertIn(f'data-category="{key}"', source)
            self.assertTrue(any(tag == "base" and attrs.get("href") == "../" for tag, attrs in page.tags))
            canonical = next(attrs["href"] for tag, attrs in page.tags if attrs.get("rel") == "canonical")
            self.assertEqual(canonical, f'https://example.test/catalog/{slug}/')
            visible = [attrs for tag, attrs in page.tags if tag == "article" and "hidden" not in attrs]
            self.assertTrue(visible)
            self.assertTrue(all(attrs["data-category"] == key for attrs in visible))

    def test_carousel_cache_versions_and_video_loading(self):
        (self.root / "public/media/video").mkdir(parents=True)
        for name in ("montaj.mp4", "montaj-poster.webp"):
            (self.root / "public/media/video" / name).write_bytes(b"fixture")
        source = self.build()
        tags = Page(source).tags
        slides = [attrs for _, attrs in tags if "data-slide-id" in attrs]
        self.assertEqual(len(slides), 4)
        for slide in slides:
            asset = next(a for a in self.catalog["assets"] if a["id"] == slide["data-slide-id"])
            self.assertEqual(asset["role"], "provided")
            self.assertNotEqual(asset["category"], "armchair")
        versioned = next(attrs["href"] for _, attrs in tags if attrs.get("rel") == "stylesheet")
        self.assertIn("?v=", versioned)
        self.assertNotIn("Model No:", source)
        self.assertNotIn("video-play", source)
        self.assertTrue(any(attrs.get("preload") == "none" and "controls" in attrs for tag, attrs in tags if tag == "video"))
        self.assertTrue(any("data-src" in attrs for tag, attrs in tags if tag == "source"))
        js = self.root / "src/site.js"
        js.write_text(js.read_text() + "\n// New release\n")
        updated = Page(self.build()).tags
        self.assertNotEqual(versioned, next(attrs["href"] for _, attrs in updated if attrs.get("rel") == "stylesheet"))


if __name__ == "__main__":
    unittest.main()
