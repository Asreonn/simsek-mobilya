#!/usr/bin/env python3
"""Rebuild compact Turkish/Latin web fonts without modifying the downloaded sources.

Optional asset maintenance: uv run --no-project --with 'fonttools[woff]' python scripts/subset_fonts.py
The regular standard-library site build only copies the committed output fonts.
"""
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / 'src/fonts'
for family in ('inter', 'fraunces'):
    for source, target, unicodes in (
        ('latin', 'latin-compact', set(range(0x100)) | {0x131, 0x152, 0x153, 0x2BB, 0x2BC, 0x2C6, 0x2DA, 0x2DC, 0x304, 0x308, 0x329, 0x20AC, 0x2122, 0x2212, 0xFEFF, 0xFFFD} | set(range(0x2000, 0x2070))),
        ('latin-ext', 'tr', {0x11E, 0x11F, 0x130, 0x15E, 0x15F}),
    ):
        font = TTFont(FONTS / f'{family}-{source}.woff2')
        limits = {}
        if 'fvar' in font:
            for axis in font['fvar'].axes:
                limits[axis.axisTag] = (400, 700) if axis.axisTag == 'wght' else axis.defaultValue
        if limits:
            font = instantiateVariableFont(font, limits, inplace=True)
        if 'gvar' in font:
            # Instancing can omit empty/non-varying entries. The subsetter expects
            # a mapping for every glyph, including spaces and .notdef.
            for glyph in font.getGlyphOrder():
                font['gvar'].variations.setdefault(glyph, [])
        options = subset.Options()
        options.flavor = 'woff2'
        options.layout_features = ['*']
        sub = subset.Subsetter(options=options)
        sub.populate(unicodes=unicodes)
        sub.subset(font)
        font.flavor = 'woff2'
        destination = FONTS / f'{family}-{target}.woff2'
        font.save(destination)
        print(destination.name, destination.stat().st_size)
