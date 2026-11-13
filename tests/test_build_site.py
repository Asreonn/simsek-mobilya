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
        self.assertIn("Evinize yakışan, size özel mobilyalar.", source)
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

    def test_enhanced_manifest_lqip_avif_and_logo_are_used(self):
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
        self.assertIn("data:image/webp;base64,AAAA", source)
        self.assertIn('sizes="32x32"', source)
        self.assertIn("background-color:#123456", source)

    def test_canonical_sitemap_and_optional_fields_follow_content(self):
        content = {"site_url": "https://example.test/katalog", "brand": {"address": "Bilinen adres", "hours": "09.00–17.00"}, "nav": [{"id": "surec", "label": "Nasıl Çalışırız"}]}
        self.write_json("content/site.json", content)
        original = (self.root / "content/site.json").read_bytes()
        source = self.build()
        self.assertIn('href="https://example.test/katalog/"', source)
        self.assertIn('href="#nasil-calisiriz"', source)
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
        page = Page(source)
        for tag, attrs in page.tags:
            if tag == "a" and attrs.get("class") == "model-ask":
                message = parse_qs(urlsplit(attrs["href"]).query)["text"][0]
                self.assertIn(attrs["aria-label"].split(" — ")[0], message)
        model_tags = [attrs for tag, attrs in page.tags if tag == "article" and attrs.get("class") == "model-card"]
        project_tags = [attrs for tag, attrs in page.tags if tag == "article" and attrs.get("class") == "project-card"]
        self.assertEqual(len(model_tags), sum(a["role"] == "reference" for a in self.catalog["assets"]))
        self.assertEqual(len(project_tags), sum(a["role"] == "provided" and a["category"] != "workshop" for a in self.catalog["assets"]))

    def test_external_manifest_path_is_rejected(self):
        self.write_json("data/media/web_manifest.json", {"assets": {"P-MUT-01": {"full": [{"path": "../outside.webp", "w": 100, "h": 100}]}}})
        with self.assertRaisesRegex(ValueError, "Geçersiz manifest yolu"):
            self.build()


if __name__ == "__main__":
    unittest.main()
