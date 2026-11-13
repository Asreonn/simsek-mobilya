PYTHON ?= .venv/bin/python

.PHONY: check media-check media-docs media-preview test photos
check: media-check test

media-check:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/media_library.py validate

media-docs:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/media_library.py docs

media-preview:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/media_library.py preview

photos:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/enhance_photos.py

test:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest discover -s tests -v

.PHONY: site serve qr
site:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/build_site.py

serve:
	$(PYTHON) -m http.server 8080 -d public

qr:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/make_qr.py
