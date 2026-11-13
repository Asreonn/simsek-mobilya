"""Photo pipeline contracts, source preservation, and real derivative checks."""
import base64
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageCms, features

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import enhance_photos as photos

ROOT = Path(__file__).resolve().parents[1]


def snapshot(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob('*') if p.is_file()}


class PhotoMathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        photos.initialize_worker()

    def test_wb_limits_and_intentional_color_override(self):
        rgb = np.full((40, 60, 3), (160, 100, 55), dtype=np.float32)
        balanced, gains = photos.white_balance(rgb)
        self.assertTrue(all(.88 <= value <= 1.12 for value in gains))
        self.assertLess(balanced[:, :, 0].mean(), rgb[:, :, 0].mean())
        disabled, gains = photos.white_balance(rgb, False)
        np.testing.assert_array_equal(disabled, rgb)
        self.assertEqual(gains, [1, 1, 1])
        overrides = json.loads((ROOT / 'config/media/enhance_overrides.json').read_text())
        for asset_id in ('P-TV-02', 'P-TV-03', 'P-TV-03'):
            self.assertIs(overrides['assets'][asset_id]['wb'], False)

    def test_moderate_change_and_repeatable_pixels(self):
        ramp = np.linspace(35, 225, 256, dtype=np.uint8)
        rgb = np.repeat(np.tile(ramp, (128, 1))[:, :, None], 3, axis=2)
        image = Image.fromarray(rgb)
        first, _, _ = photos.enhance(image, 'reference', {})
        second, _, _ = photos.enhance(image, 'reference', {})
        np.testing.assert_array_equal(first, second)
        self.assertLess(np.mean(np.abs(np.array(first).astype(float) - rgb)), 18)
        self.assertLess(np.max(np.ptp(np.array(first).astype(int), axis=2)), 9)

    def test_denoise_only_provided(self):
        image = Image.new('RGB', (32, 32), '#a7a29c')
        with patch.object(photos.cv2, 'fastNlMeansDenoisingColored', side_effect=lambda rgb, *args: rgb) as denoise:
            photos.enhance(image, 'reference', {})
            denoise.assert_not_called()
            photos.enhance(image, 'provided', {})
            self.assertEqual(denoise.call_args.args[2:4], (3, 3))

    def test_smart_crop_finds_off_center_detail_and_override(self):
        array = np.full((800, 1600, 3), 128, np.uint8)
        rng = np.random.default_rng(10)
        array[200:600, 1200:1500] = rng.integers(0, 255, (400, 300, 3), dtype=np.uint8)
        image = Image.fromarray(array)
        box = photos.smart_crop_box(image, (4, 3))
        self.assertGreater(box[0], 250)
        self.assertEqual((box[2] - box[0]) * 3, (box[3] - box[1]) * 4)
        self.assertEqual(box, photos.smart_crop_box(image, (4, 3)))
        self.assertEqual(photos.smart_crop_box(image, (4, 3), [0, .5])[0], 0)
        with self.assertRaises(ValueError):
            photos.smart_crop_box(image, (4, 3), [2, .5])

    def test_exif_srgb_and_metadata_removal(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'oriented.jpg'
            exif = Image.Exif()
            exif[274] = 6
            exif[270] = 'Private source metadata'
            icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
            Image.new('RGB', (80, 40), '#aa9077').save(path, exif=exif, icc_profile=icc)
            image = photos.read_srgb(path)
            self.assertEqual(image.size, (40, 80))
            self.assertEqual(image.info, {})
            self.assertEqual(len(image.getexif()), 0)

    def test_no_upscale(self):
        image = Image.new('RGB', (479, 360))
        with self.assertRaises(ValueError):
            photos.resized(image, 480)
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(photos.variants(Path(temp), image, 'test', (480, 800), ('webp',)), [])


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        catalog = json.loads((ROOT / 'data/media/catalog.json').read_text())
        logo = next(row for row in catalog['assets'] if row['role'] == 'brand')
        destination = cls.root / logo['master']
        destination.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / logo['master'], destination)
        rows = []
        for index, size in enumerate(((1100, 850), (850, 1200))):
            path = cls.root / f'assets/catalog/test/photo-{index}.png'
            path.parent.mkdir(parents=True, exist_ok=True)
            y, x = np.indices((size[1], size[0]))
            pixels = np.stack((70 + x % 130, 65 + y % 130, 60 + (x + y) % 130), axis=2).astype(np.uint8)
            Image.fromarray(pixels).save(path)
            rows.append({'id': f'TEST-{index}', 'master': path.relative_to(cls.root).as_posix(),
                         'width': size[0], 'height': size[1], 'sha256': photos.digest(path),
                         'role': 'provided' if index else 'reference', 'category': 'kitchen',
                         'title': 'Deneme <başlık>', 'alt_tr': 'Örnek & fotoğraf'})
        rows.append(logo)
        (cls.root / 'data/media').mkdir(parents=True)
        (cls.root / 'data/media/catalog.json').write_text(json.dumps({'assets': rows}))
        (cls.root / 'config/media').mkdir(parents=True)
        overrides = json.loads((ROOT / 'config/media/enhance_overrides.json').read_text())
        overrides['assets'] = {'TEST-1': {'wb': False}}
        (cls.root / 'config/media/enhance_overrides.json').write_text(json.dumps(overrides))
        (cls.root / 'assets/originals').mkdir()
        (cls.root / 'assets/originals/untouched.bin').write_bytes(b'original immutable pixels')
        cls.before = snapshot(cls.root / 'assets')
        cls.manifest = photos.run(cls.root, workers=2)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_manifest_schema_dimensions_formats_and_placeholders(self):
        self.assertEqual(set(self.manifest['assets']), {'TEST-0', 'TEST-1'})
        self.assertIn('generated', self.manifest)
        formats = {'webp', 'avif'} if features.check('avif') else {'webp'}
        for entry in self.manifest['assets'].values():
            self.assertTrue({'role', 'category', 'title', 'alt_tr', 'width', 'height',
                             'lqip', 'color', 'full', 'card', 'tall'} <= entry.keys())
            self.assertRegex(entry['color'], r'^#[0-9a-f]{6}$')
            prefix, data = entry['lqip'].split(',', 1)
            self.assertEqual(prefix, 'data:image/webp;base64')
            with Image.open(io.BytesIO(base64.b64decode(data))) as tiny:
                self.assertEqual(tiny.width, 24)
            for kind in ('full', 'card', 'tall'):
                if not entry[kind]:
                    continue
                self.assertEqual({v['format'] for v in entry[kind]}, formats)
                crop = entry.get('crops', {}).get(kind, [0, 0, entry['width'], entry['height']])
                for variant in entry[kind]:
                    self.assertLessEqual(variant['w'], crop[2] - crop[0])
                    self.assertLessEqual(variant['h'], crop[3] - crop[1])
                    if kind == 'full':
                        self.assertIn(variant['w'], photos.FULL_WIDTHS)
                    else:
                        self.assertIn(variant['w'], photos.CROP_WIDTHS)
                        ratio = 4 / 3 if kind == 'card' else 3 / 4
                        self.assertAlmostEqual(variant['h'], variant['w'] / ratio, delta=.5)
                    path = self.root / 'public' / variant['path']
                    self.assertTrue(path.is_relative_to(self.root / 'public/media'))
                    with Image.open(path) as output:
                        self.assertEqual(output.size, (variant['w'], variant['h']))
                        self.assertNotIn('icc_profile', output.info)
                        self.assertNotIn('exif', output.info)
        self.assertEqual(self.manifest['assets']['TEST-0']['tall'], [])
        self.assertEqual(len(self.manifest['assets']['TEST-1']['tall']), 2 * len(formats))
        self.assertEqual(self.manifest['assets']['TEST-1']['processing']['wb_gains'], [1, 1, 1])

    def test_serial_parallel_byte_identical_and_sources_unchanged(self):
        before_outputs = snapshot(self.root / 'public/media')
        serial = photos.run(self.root, workers=1)
        self.assertEqual(self.manifest, serial)
        self.assertEqual(before_outputs, snapshot(self.root / 'public/media'))
        self.assertEqual(self.before, snapshot(self.root / 'assets'))

    def test_logo_roof_s_and_lettering_boundary(self):
        logo = self.manifest['logo']
        verification = logo['crop_verification']
        self.assertTrue(verification['verified'])
        self.assertGreaterEqual(min(verification['emblem_margins_ltrb']), 2)
        self.assertGreaterEqual(verification['lettering_gap'], 2)
        self.assertEqual({v['w'] for v in logo['full']}, {600, 1000})
        self.assertEqual({v['w'] for v in logo['mark']}, {192, 384})
        self.assertEqual({v['w'] for v in logo['favicon']}, {32, 180, 512})
        for variant in logo['mark'] + logo['favicon']:
            with Image.open(self.root / 'public' / variant['path']) as image:
                self.assertEqual(image.size, (variant['w'], variant['w']))
        config = json.loads((self.root / 'config/media/enhance_overrides.json').read_text())['logo']
        row = json.loads((self.root / 'data/media/catalog.json').read_text())['assets'][-1]
        image = photos.read_srgb(self.root / row['master'])
        for box in ([140, 60, 1200, 936], [140, 20, 1200, 980], [140, 20, 1150, 936]):
            with self.assertRaisesRegex(ValueError, 'cuts emblem'):
                photos.logo_mark(image, dict(config, crop_box=box))

    def test_preview_is_escaped_and_links_exist(self):
        page = (self.root / 'preview/enhance.html').read_text()
        self.assertIn('Önce', page)
        self.assertIn('Sonra', page)
        self.assertIn('&lt;başlık&gt;', page)
        self.assertNotIn('Deneme <başlık>', page)
        self.assertIn('../public/media/logo-mark-192.png', page)

    def test_invalid_record_cannot_escape_catalog(self):
        with self.assertRaises(ValueError):
            photos.master_path(self.root, {'id': 'BAD', 'master': 'assets/originals/untouched.bin'})


class PublishedOutputTests(unittest.TestCase):
    def test_real_manifest_and_immutable_catalog_sources(self):
        path = ROOT / 'data/media/web_manifest.json'
        if not path.exists():
            self.skipTest('Run make photos for published derivative checks')
        manifest = json.loads(path.read_text())
        catalog = json.loads((ROOT / 'data/media/catalog.json').read_text())
        rows = {row['id']: row for row in catalog['assets'] if row['role'] != 'brand'}
        self.assertEqual(set(manifest['assets']), set(rows))
        for row in catalog['assets']:
            self.assertEqual(photos.digest(ROOT / row['master']), row['sha256'], row['id'])
        for asset_id, entry in manifest['assets'].items():
            row = rows[asset_id]
            for key in ('role', 'category', 'title', 'alt_tr'):
                self.assertEqual(entry[key], row[key])
            self.assertEqual(entry['source_sha256'], row['sha256'])
            for kind in ('full', 'card', 'tall'):
                crop = entry['crops'].get(kind, [0, 0, entry['width'], entry['height']])
                expected_widths = {w for w in (photos.FULL_WIDTHS if kind == 'full' else photos.CROP_WIDTHS)
                                   if w <= crop[2] - crop[0]}
                if kind == 'tall' and entry['width'] >= entry['height']:
                    expected_widths = set()
                self.assertEqual({v['w'] for v in entry[kind]}, expected_widths, asset_id)
                for variant in entry[kind]:
                    self.assertLessEqual(variant['w'], crop[2] - crop[0])
                    self.assertLessEqual(variant['h'], crop[3] - crop[1])
                    with Image.open(ROOT / 'public' / variant['path']) as output:
                        self.assertEqual(output.size, (variant['w'], variant['h']))
        self.assertTrue(manifest['logo']['crop_verification']['verified'])


if __name__ == '__main__':
    unittest.main()
