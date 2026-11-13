"""Offline checks for the matching and archive-preservation boundaries."""
import argparse
import html
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import catalog_assets as assets


def textured_scene(seed):
    rng = np.random.default_rng(seed)
    im = Image.new('RGB', (800, 650), '#d9c6a5')
    draw = ImageDraw.Draw(im)
    for _ in range(160):
        x, y = rng.integers(0, 740), rng.integers(0, 590)
        color = tuple(int(n) for n in rng.integers(20, 230, 3))
        draw.rectangle((x, y, x + 40, y + 40), fill=color, outline='black')
    return im


class CatalogTests(unittest.TestCase):
    def test_cropped_recompressed_match(self):
        scene = textured_scene(123)
        query = scene.crop((70, 50, 710, 600)).resize((510, 440))
        buffer = io.BytesIO()
        query.save(buffer, format='JPEG', quality=55)
        buffer.seek(0)
        with Image.open(buffer) as compressed:
            result = assets.image_match(compressed, scene)
        self.assertTrue(result['verified'], result)

    def test_similar_layout_different_photo_rejected(self):
        result = assets.image_match(textured_scene(123), textured_scene(124))
        self.assertFalse(result['verified'], result)

    def test_plain_image_does_not_match(self):
        self.assertFalse(assets.image_match(Image.new('RGB', (500, 500), 'white'),
                                           Image.new('RGB', (500, 500), 'white'))['verified'])

    def test_screenshot_crop_selects_photo_band(self):
        screenshot = Image.new('RGB', (720, 1600), 'white')
        screenshot.paste(textured_scene(123).resize((720, 900)), (0, 65))
        box = assets.photo_box(screenshot)
        self.assertLess(box[1], 110)
        self.assertGreater(box[3], 900)
        self.assertLess(box[3], 1000)

    def test_search_parser_merges_source_pages(self):
        url = 'https://i.pinimg.com/736x/aa/bb/cc/aabbcc01234567890123456789012345.jpg'
        sites = [dict(url=f'https://example.com/{n}', title='Kitchen',
                      originalImage={'url': url}) for n in range(2)]
        state = {'initialState': {'cbirSites': {'sites': sites}}}
        document = '<div data-state="' + html.escape(json.dumps(state), quote=True) + '"></div>'
        found = assets.parse_search(document)
        self.assertEqual(len(found), 1)
        self.assertEqual(len(found[0]['referring_pages']), 2)
        duplicate_sizes = [dict(image_url=url, page_url='https://example.com/a'),
            dict(image_url=url.replace('/736x/', '/originals/'), page_url='https://example.com/b')]
        merged = assets.dedupe_candidates(duplicate_sizes)
        self.assertEqual(len(merged), 1)
        self.assertIn('/originals/', merged[0]['image_url'])
        self.assertEqual(len(merged[0]['referring_pages']), 2)
        self.assertEqual(assets.original_variants(url)[0],
                         'https://i.pinimg.com/originals/aa/bb/cc/aabbcc01234567890123456789012345.jpg')
        other = 'https://example.com/736x/test.jpg'
        self.assertEqual(assets.original_variants(other), [other])

    def test_archive_paths_never_control_extraction_and_hashes_survive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, work = root/'pics', root/'work'
            source.mkdir()
            buffer = io.BytesIO()
            textured_scene(123).save(buffer, format='JPEG')
            raw = buffer.getvalue()
            archive = source/'test.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('../../escaped.jpg', raw)
            before = assets.digest(archive.read_bytes())
            args = argparse.Namespace(input=source, work=work, groups=root/'none.json', seed=42)
            self.assertEqual(assets.audit(args), 0)
            self.assertFalse((root/'escaped.jpg').exists())
            self.assertEqual(assets.digest(archive.read_bytes()), before)
            self.assertEqual(assets.verify(args), 0)
            self.assertEqual(assets.audit(args), 0)
            self.assertEqual(assets.verify(args), 0)

    def test_blocked_upgrade_keeps_previous_verified_download(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, work = root/'pics', root/'work'
            source.mkdir()
            textured_scene(123).save(source/'reference.jpg')
            groups = root/'groups.json'
            groups.write_text(json.dumps({'reference.jpg': 'reference'}))
            args = argparse.Namespace(input=source, work=work, groups=groups, seed=42,
                upload_references=True, ids=None, retry=False, upgrade=True,
                limit=0, candidates=6, delay=3)
            assets.audit(args)
            row = assets.read_json(work/'inventory.json')['assets'][0]
            selected = dict(path=row['path'], width=800, height=650, bytes=row['bytes'],
                downloaded_url='https://example.com/photo.jpg', page_url='https://example.com/',
                quality_label='matching_online_copy', sha256=row['sha256'])
            assets.write_json(work/'matches.json', {row['id']: dict(status='matched', selected=selected)})
            with patch.object(assets, 'discover', side_effect=assets.ServiceBlocked('Search challenge')):
                self.assertEqual(assets.find(args), 3)
            result = assets.read_json(work/'matches.json')[row['id']]
            self.assertEqual(result['status'], 'matched')
            self.assertEqual(result['selected'], selected)
            self.assertEqual(result['last_upgrade']['status'], 'blocked')


if __name__ == '__main__':
    unittest.main()
