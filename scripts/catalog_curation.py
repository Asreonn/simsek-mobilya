#!/usr/bin/env python3
"""Find high-resolution, text-free catalog alternatives without changing sources.

OCR is a screening tool. Human visual approval is recorded separately; an empty
OCR result alone never certifies a photograph as free of text or artifacts.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import hashlib
import html
import io
import json
import os
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import urlsplit

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps
import requests

from catalog_assets import (ROOT, CONFIG, dedupe_candidates, digest, immutable_write,
                            original_variants, read_json, write_json, now, image_match)

WORK = ROOT/'work/catalog'
CUR = WORK/'curation'
MIN_SHORT, MIN_LONG = 1000, 1500


def category(row):
    if row['kind'] == 'workshop_candidate':
        return 'workshop' if row['container'].endswith('1.11.58 AM.zip') else 'coffee'
    if row['kind'] == 'logo':
        return 'logo'
    n = row['index']
    if row['container'].endswith('1.11.50 AM.zip'):
        if n in [21, 55, 56, 57]:
            return 'tv'
        if n in [22, 23, 50]:
            return 'hall'
        if n <= 12 or n in [20, 24, 25, 26, 27, 28, 29, 48, 49, 52, 53, 54]:
            return 'kitchen'
        return 'coffee'
    if row['container'].endswith('1.12.04 AM.zip'):
        return 'kitchen'
    if row['container'].endswith('1.11.52 AM.zip'):
        return 'hall' if n == 1 else 'tv'
    if row['container'].endswith('1.12.06 AM.zip'):
        return 'hall' if n == 2 else 'tv'
    return 'tv'


def text_words(tsv):
    words = []
    for item in csv.DictReader(io.StringIO(tsv), delimiter='\t', quoting=csv.QUOTE_NONE):
        text = (item.get('text') or '').strip()
        if not text or int(item.get('level', 0)) != 5:
            continue
        conf = float(item.get('conf', -1))
        meaningful = ''.join(c for c in text if c.isalnum())
        if (conf >= 55 and len(meaningful) >= 3) or (
            conf >= 35 and any(t in text.lower() for t in ['redmi','pinterest','kaydet','instagram','@','www.'])):
            words.append(dict(text=text, confidence=conf,
                box=[int(item[k]) for k in ['left','top','width','height']]))
    return words


def inspect(path):
    raw = path.read_bytes()
    sha = digest(raw)
    cache = CUR/'qa'/f'{sha}.json'
    cached=read_json(cache,{})
    if cached.get('qa_version') == 3:
        return cached
    with Image.open(io.BytesIO(raw)) as im:
        im.load()
        image = ImageOps.exif_transpose(im).convert('RGB')
        w, h = image.size
        pixels=np.asarray(image)
        uniform=((pixels.min(axis=2)>248)|(pixels.max(axis=2)<6))
        ys=np.where(uniform.mean(axis=1)<.995)[0]
        if len(ys):
            xs=np.where(uniform[ys[0]:ys[-1]+1].mean(axis=0)<.995)[0]
        else:
            xs=[]
        box=[int(xs[0]),int(ys[0]),int(xs[-1]+1),int(ys[-1]+1)] if len(xs) and len(ys) else [0,0,w,h]
        usable_w,usable_h=box[2]-box[0],box[3]-box[1]
        small = image.copy()
        small.thumbnail((1200, 1200))
        gray = cv2.cvtColor(np.asarray(small), cv2.COLOR_RGB2GRAY)
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        # A compact spatial/color signature only ranks already related results;
        # it is not an assertion of semantic or exact-image equivalence.
        layout = np.asarray(image.resize((12, 12))).astype(float)/255
        lab = cv2.cvtColor(np.asarray(small), cv2.COLOR_RGB2LAB)
        hist = cv2.calcHist([lab], [1, 2], None, [12, 12], [0, 256, 0, 256])
        hist = cv2.normalize(hist, None).ravel()
    if cached.get('qa_version')==2:
        words=cached['words']
    else:
        ocr = subprocess.run(['tesseract', str(path), 'stdout', '--psm', '11', 'tsv'],
            capture_output=True, text=True, timeout=45,
            env={**os.environ, 'OMP_THREAD_LIMIT':'1'})
        if ocr.returncode:
            raise RuntimeError(f'OCR failed: {ocr.stderr[:200]}')
        words = text_words(ocr.stdout)
    result = dict(qa_version=3, sha256=sha, width=w, height=h, bytes=len(raw),
        effective_box=box,usable_width=usable_w,usable_height=usable_h,
        sharpness=round(sharpness, 2), words=words,
        resolution_ok=min(usable_w,usable_h) >= MIN_SHORT and max(usable_w,usable_h) >= MIN_LONG,
        sharpness_ok=sharpness >= 45,
        auto_text_clear=not words, visual_approved=False,
        layout=layout.ravel().tolist(), histogram=hist.tolist())
    result['auto_eligible'] = result['resolution_ok'] and result['sharpness_ok'] and not words
    write_json(cache, result)
    return result


def local(args):
    inventory=read_json(WORK/'inventory.json')
    crops=read_json(CONFIG/'local_crops.json',{})
    records={}
    for row in inventory['assets']:
        if row['type']!='image' or row['kind']=='reference':
            continue
        key=row['id'];source=WORK/row['path']; target=source
        with Image.open(source) as im:
            image=ImageOps.exif_transpose(im)
            box=crops.get(key,[0,0,image.width,image.height])
            if key in crops:
                cropped=image.crop(box)
                target=CUR/'local'/f'{key}_bottom-crop.png'
                target.parent.mkdir(parents=True,exist_ok=True)
                cropped.save(target,format='PNG',icc_profile=im.info.get('icc_profile'))
                with Image.open(target) as saved:
                    assert np.array_equal(np.asarray(saved),np.asarray(cropped)), key
        qa=inspect(target)
        records[key]=dict(source=row['path'],path=str(target.relative_to(WORK)),
            kind=row['kind'],category=category(row),box=box,
            processing='lossless_bottom_crop' if key in crops else 'unchanged',
            source_pixels_preserved=True,qa=qa)
        write_json(CUR/'local.json',records)
        print(key,qa['width'],qa['height'],'OCR',[(t['text'],t['box']) for t in qa['words']],flush=True)


def reaudit(args):
    pool=read_json(CUR/'pool.json',{})
    paths={r['path'] for r in pool.values() if r.get('path')}
    with ThreadPoolExecutor(max_workers=3) as executor:
        qa=dict(executor.map(lambda path:(path,inspect(WORK/path)),paths))
    for record in pool.values():
        if record.get('path') in qa:
            record['qa']=qa[record['path']]
    write_json(CUR/'pool.json',pool)
    print('Re-audited',len(paths))


def collect(args):
    CUR.mkdir(parents=True, exist_ok=True)
    inventory = read_json(WORK/'inventory.json')
    matches = read_json(WORK/'matches.json', {})
    jobs = {}
    for row in inventory['assets']:
        if row['kind'] != 'reference' or row['type'] != 'image':
            continue
        if args.ids and row['id'] not in args.ids:
            continue
        candidates = read_json(WORK/'search'/f'{row["id"]}.json', {}).get('candidates', [])
        candidates = dedupe_candidates(candidates)[:args.candidates]
        selected = matches.get(row['id'], {}).get('selected')
        if selected:
            candidates.insert(0, dict(image_url=selected['downloaded_url'],
                page_url=selected.get('page_url',''), title='Previous exact match'))
        for rank, c in enumerate(candidates):
            key = digest(c['image_url'].encode())[:20]
            if key not in jobs:
                jobs[key] = dict(**c, memberships=[])
            jobs[key]['memberships'].append(dict(id=row['id'], index=row['index'],
                category=category(row), rank=rank))
    for c in read_json(CONFIG/'external_candidates.json',[]):
        memberships=[dict(id=r['id'],index=r['index'],category=c['category'],rank=0)
                     for r in inventory['assets'] if r['kind']=='reference'
                     and category(r)==c['category'] and (not args.ids or r['id'] in args.ids)]
        if memberships:
            jobs[digest(c['image_url'].encode())[:20]]=dict(**c,memberships=memberships)
    pool = read_json(CUR/'pool.json', {})
    for key, record in pool.items():
        if key in jobs:
            record['memberships'] = jobs[key]['memberships']
    tasks = [(key, job) for key, job in jobs.items() if key not in pool or (
        args.retry and pool[key]['status']=='error')]
    if args.limit:
        tasks = tasks[:args.limit]
    print(f'Candidates {len(jobs)}, pending {len(tasks)}', flush=True)

    def worker(key, c):
        record = dict(**c, at=now(), status='error', attempts=[])
        session = requests.Session()
        session.headers['User-Agent'] = 'MarangozCatalogResearch/1.1'
        try:
            for url in original_variants(c['image_url']):
                try:
                    with session.get(url, timeout=(8,18), stream=True) as response:
                        response.raise_for_status()
                        raw = bytearray()
                        for chunk in response.iter_content(65536):
                            raw.extend(chunk)
                            if len(raw) > 20*1024*1024:
                                raise ValueError('Image exceeds 20 MiB')
                        raw = bytes(raw)
                        final_url = response.url
                    with Image.open(io.BytesIO(raw)) as im:
                        im.load()
                        w,h = im.size
                        fmt = im.format.lower()
                    record['attempts'].append(dict(url=url, width=w, height=h))
                    if min(w,h) < MIN_SHORT or max(w,h) < MIN_LONG:
                        record.update(status='low_resolution', width=w, height=h)
                        continue
                    ext = {'jpeg':'jpg'}.get(fmt,fmt)
                    target = CUR/'pool'/f'{digest(raw)}.{ext}'
                    # The same bytes may be returned by concurrent source URLs.
                    try:
                        immutable_write(target, raw)
                    except FileExistsError:
                        if digest(target.read_bytes()) != digest(raw):
                            raise ValueError('Concurrent output mismatch')
                    qa = inspect(target)
                    record.update(status='downloaded', path=str(target.relative_to(WORK)),
                                  downloaded_url=final_url, qa=qa)
                    return key, record
                except (requests.RequestException, OSError, ValueError, RuntimeError,
                        subprocess.TimeoutExpired) as e:
                    record['attempts'].append(dict(url=url,error=f'{type(e).__name__}: {str(e)[:180]}'))
            return key, record
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(worker,key,c) for key,c in tasks]
        for n,future in enumerate(as_completed(futures),1):
            key,record = future.result()
            pool[key] = record
            write_json(CUR/'pool.json',pool)
            print(f'[{n}/{len(tasks)}] {record["status"]} '
                  f'{record.get("qa",{}).get("width","")}x{record.get("qa",{}).get("height","")} '
                  f'text={len(record.get("qa",{}).get("words",[]))}',flush=True)
    write_json(CUR/'pool.json',pool)
    print('downloaded',sum(r['status']=='downloaded' for r in pool.values()),
          'eligible',sum(r.get('qa',{}).get('auto_eligible',False) for r in pool.values()))


def board(args):
    pool = read_json(CUR/'pool.json',{})
    unique = {}
    for key,record in pool.items():
        if record.get('qa',{}).get('auto_eligible'):
            sha = record['qa']['sha256']
            if sha not in unique:
                unique[sha] = dict(key=key,**record)
    entries = list(unique.values())
    entries.sort(key=lambda e:(e['memberships'][0]['category'], -e['qa']['width']*e['qa']['height']))
    boards = CUR/'boards';boards.mkdir(parents=True,exist_ok=True)
    numbered = []
    for start in range(0,len(entries),16):
        sheet = Image.new('RGB',(1600,1600),'#ece7df');draw=ImageDraw.Draw(sheet)
        for slot,e in enumerate(entries[start:start+16]):
            number = start+slot+1
            x=(slot%4)*400;y=(slot//4)*400
            with Image.open(WORK/e['path']) as im:
                im=ImageOps.exif_transpose(im).convert('RGB');im.thumbnail((390,345))
                sheet.paste(im,(x+(400-im.width)//2,y))
            qa=e['qa'];cats=','.join(sorted({m['category'] for m in e['memberships']}))
            draw.text((x+6,y+350),f'{number:03d} | {qa["width"]}x{qa["height"]} | {cats}',fill='black')
            draw.text((x+6,y+372),e['key'],fill='black')
            numbered.append(dict(number=number,**e))
        target=boards/f'pool_{start+1:03d}.jpg';sheet.save(target,quality=92);print(target)
    write_json(CUR/'numbered_pool.json',numbered)


def export(args):
    """Export only reviewed masters and map every input to an honest choice."""
    inventory=read_json(WORK/'inventory.json')
    review=read_json(CONFIG/'catalog_review.json')
    mapping=read_json(CONFIG/'catalog_choices.json')
    pool=read_json(CUR/'pool.json',{})
    local_records=read_json(CUR/'local.json',{})
    variant=read_json(CUR/'ref38_variant.json')
    out=WORK/'catalog-ready'
    approved=review['approved']
    assets={}
    for choice,approval in approved.items():
        family,key=choice.split(':',1)
        if family=='pool':
            origin=pool[key]
            source=WORK/origin['path']
            role='reference'
            provenance=dict(url=origin.get('downloaded_url',origin['image_url']),
                            page_url=origin.get('page_url',''),authorship='unverified')
        elif family=='variant':
            source=WORK/variant['path'];role='reference'
            old=read_json(WORK/'matches.json')['a4ec981ad2b21071']['selected']
            provenance=dict(url=old['downloaded_url'],page_url=old.get('page_url',''),
                original_path=variant['source'],crop_box=variant['box'],authorship='unverified')
        else:
            origin=local_records[key];source=WORK/origin['path']
            role='brand' if family=='logo' else 'provided'
            provenance=dict(original_path=origin['source'],crop_box=origin['box'],
                processing=origin['processing'],authorship='user_provided_not_independently_verified')
        qa=inspect(source)
        if role!='brand':
            if not approval.get('visual_text_clear') or not qa['resolution_ok']:
                raise ValueError(f'Unapproved or low-resolution export: {choice}')
        with Image.open(source) as original:
            image=ImageOps.exif_transpose(original)
            box=qa['effective_box'] if role!='brand' else [0,0,image.width,image.height]
            if box!=[0,0,image.width,image.height]:
                cropped=image.crop(box)
                buffer=io.BytesIO();cropped.save(buffer,format='PNG')
                raw=buffer.getvalue();ext='png'
            else:
                raw=source.read_bytes();ext=source.suffix.lstrip('.')
            width,height=box[2]-box[0],box[3]-box[1]
        sha=digest(raw)
        master=out/'masters'/role/f'{approval["category"]}_{sha[:16]}.{ext}'
        immutable_write(master,raw)
        # A PNG trim must contain exactly the original pixels of the approved region.
        with Image.open(source) as original,Image.open(master) as final:
            assert np.array_equal(np.asarray(ImageOps.exif_transpose(original).crop(box)),
                                  np.asarray(final)),choice
            preview=ImageOps.exif_transpose(final).convert('RGB')
            web=[]
            for target_w in [600,1000,1400]:
                if target_w>preview.width:
                    continue
                resized=preview.resize((target_w,round(preview.height*target_w/preview.width)),Image.Resampling.LANCZOS)
                web_path=out/'web'/role/f'{approval["category"]}_{sha[:16]}_{target_w}.webp'
                web_path.parent.mkdir(parents=True,exist_ok=True)
                resized.save(web_path,format='WEBP',quality=90,method=6)
                web.append(dict(path=str(web_path.relative_to(out)),width=resized.width,height=resized.height))
        assets[choice]=dict(master=str(master.relative_to(out)),source=str(source.relative_to(WORK)),
            role=role,category=approval['category'],width=width,height=height,sha256=sha,
            text_clear=approval.get('visual_text_clear',False),visual_review=approval['inspection'],
            source_pixels_preserved=True,export_box=box,provenance=provenance,web=web,
            ocr_words=qa['words'])
        print('MASTER',choice,width,height,flush=True)
    assignments=[]
    for row in inventory['assets']:
        if row['type']!='image':
            continue
        if row['kind']=='logo':
            choices=['logo:'+row['id']]
        elif row['kind']=='reference':
            choices=mapping['references_by_index'][str(row['index'])]
        else:
            choices=mapping['local_by_id'][row['id']]
        if not all(c in assets for c in choices):
            raise ValueError(f'Mapping contains an unapproved choice: {row["id"]}')
        primary=choices[0]
        if primary=='logo:'+row['id']:
            relation='brand_asset'
        elif primary=='local:'+row['id']:
            relation='same_photo_bottom_crop' if row['id'] in read_json(CONFIG/'local_crops.json',{}) else 'same_photo'
        elif assets[primary]['role']=='provided':
            relation='different_provided_photo'
        else:
            relation='similar_reference'
            if row.get('query'):
                with Image.open(WORK/row['query']) as q,Image.open(out/assets[primary]['master']) as p:
                    if image_match(q,p)['verified']:
                        relation='exact_online_photo'
        assignments.append(dict(id=row['id'],index=row['index'],container=row['container'],
            member=row['member'],original=row['path'],thumbnail=row['thumbnail'],
            original_kind=row['kind'],category=category(row),choices=choices,relation=relation))
    assert len(assignments)==sum(r['type']=='image' for r in inventory['assets'])
    manifest=dict(created_at=now(),quality=dict(minimum_short_edge=MIN_SHORT,minimum_long_edge=MIN_LONG,
        no_upscaling=True,generative_edits=False,visual_review=True,
        text_scope='No overlaid text, social UI, phone/date stamps or watermarks; logo lettering intentionally retained'),
        assets=assets,assignments=assignments)
    write_json(out/'manifest.json',manifest)
    create_review(out,manifest)
    print(json.dumps(dict(inputs=len(assignments),unique_photos=sum(a['role']!='brand' for a in assets.values()),
        provided=sum(a['role']=='provided' for a in assets.values()),references=sum(a['role']=='reference' for a in assets.values()),
        uncovered=0),ensure_ascii=False))


def create_review(out,manifest):
    esc=lambda text:html.escape(str(text),quote=True)
    names=dict(kitchen='Mutfak',coffee='Kahve köşesi',hall='Antre / ayna',tv='TV ünitesi',workshop='Atölye',logo='Logo')
    relations=dict(brand_asset='Logo — marka yazısı korundu',same_photo='Aynı gerçek çekim',
        same_photo_bottom_crop='Aynı çekim — alt damga kırpıldı',different_provided_photo='Başka gerçek çekim / farklı açı veya model',
        similar_reference='Benzer model referansı',exact_online_photo='Aynı fotoğrafın çevrimiçi kaynağı')
    cards=[]
    for row in manifest['assignments']:
        panels=[]
        for n,choice in enumerate(row['choices']):
            a=manifest['assets'][choice]
            preview=a['web'][0]['path'] if a['web'] else a['master']
            role=dict(provided='Kullanıcının verdiği gerçek çekim',reference='Model referansı',brand='Marka görseli')[a['role']]
            link=a['provenance'].get('page_url') or a['provenance'].get('url')
            source=f'<a href="{esc(link)}">Kaynak</a>' if link else ''
            panels.append(f'<section><p>{"Seçilen" if n==0 else "Alternatif"} · {role}</p>'
                f'<a href="{esc(a["master"])}"><img loading="lazy" src="{esc(preview)}" alt="{esc(names[a["category"]])}"></a>'
                f'<p>{a["width"]} × {a["height"]} px · {source}</p></section>')
        cards.append(f'<article data-category="{row["category"]}" data-relation="{row["relation"]}">'
            f'<h2>{esc(names[row["category"]])} · #{row["index"]:02d}</h2>'
            f'<p>{esc(relations[row["relation"]])}</p><div class="pair">{"".join(panels)}</div>'
            f'<details><summary>Orijinal kare</summary><p>{esc(row["container"])}<br>{esc(row["member"])}</p>'
            f'<a href="../{esc(row["original"])}"><img loading="lazy" src="../{esc(row["thumbnail"])}" alt="Orijinal"></a></details></article>')
    buttons=''.join(f'<button data-filter="{k}">{v}</button>' for k,v in [('all','Tümü'),*names.items()])
    photo_count=sum(a['role']!='brand' for a in manifest['assets'].values())
    input_count=len(manifest['assignments'])
    content=f'''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Şimşek Mobilya — katalog için seçilen görseller</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f2eee7;color:#2c241d;font:15px system-ui}}header{{padding:28px;max-width:1500px;margin:auto}}h1{{font-size:28px}}h2{{font-size:18px}}nav{{display:flex;flex-wrap:wrap;gap:8px}}button{{padding:9px 16px;border:1px solid #c3b29a;background:#fff;border-radius:6px;cursor:pointer}}main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,440px),1fr));gap:20px;padding:0 24px 28px;max-width:1540px;margin:auto}}article{{padding:18px;background:#fff;border:1px solid #d8cab6;border-radius:12px;min-width:0}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}section{{min-width:0}}img{{width:100%;height:300px;object-fit:contain;background:#f6f3ef}}a{{color:#79552e}}details{{font-size:12px;overflow-wrap:anywhere}}details img{{height:200px;width:auto;max-width:100%}}[hidden]{{display:none!important}}@media(max-width:500px){{header{{padding:18px}}main{{padding:0 12px 20px}}article{{padding:12px}}.pair img{{height:240px}}}}
</style><header><h1>Katalog için seçilen görseller</h1>
<p>{input_count} kaynak görselin tamamı için seçim hazır. {photo_count} ayrı fotoğraf + logo. Fotoğraf master'larında en az 1000 px kısa kenar ve 1500 px uzun kenar; yapay büyütme yok.</p>
<p>Gerçek çekimler ile benzer model referansları açıkça ayrıldı. Referans görseller tamamlanan firma işleri olarak sunulmamalı. Logo yazısı korundu.</p>
<nav>{buttons}</nav><p><a href="gallery.html">Yalnızca temiz seçimi göster</a> · <a href="manifest.json">Tüm kaynaklar, kırpımlar ve eşleştirmeler</a></p></header>
<main>{''.join(cards)}</main><script>document.querySelectorAll('button').forEach(b=>b.onclick=()=>document.querySelectorAll('article').forEach(a=>a.hidden=b.dataset.filter!=='all'&&a.dataset.category!==b.dataset.filter))</script></html>'''
    (out/'review.html').write_text(content)
    gallery=[]
    for choice,a in manifest['assets'].items():
        preview=a['web'][0]['path'] if a['web'] else a['master']
        label={'provided':'Müşteriden gelen gerçek çekim','reference':'Model referansı','brand':'Logo'}[a['role']]
        gallery.append(f'<article data-category="{a["category"]}" data-role="{a["role"]}">'
            f'<a href="{esc(a["master"])}"><img loading="lazy" src="{esc(preview)}" alt="{esc(names[a["category"]])}"></a>'
            f'<h2>{esc(names[a["category"]])}</h2><p>{label} · {a["width"]} × {a["height"]} px</p></article>')
    gallery_content=content[:content.index('<main>')]+f'<main>{"".join(gallery)}</main>'+content[content.index('<script>'):]
    gallery_content=gallery_content.replace('Yalnızca temiz seçimi göster','Orijinal / seçim karşılaştırması').replace('href="gallery.html"','href="review.html"')
    (out/'gallery.html').write_text(gallery_content)


def gallery(args):
    out=WORK/'catalog-ready'
    create_review(out,read_json(out/'manifest.json'))


def validate(args):
    out=WORK/'catalog-ready';m=read_json(out/'manifest.json')
    inventory=read_json(WORK/'inventory.json')
    expected={r['id'] for r in inventory['assets'] if r['type']=='image'}
    assert {r['id'] for r in m['assignments']}==expected
    checked=0
    for choice,a in m['assets'].items():
        path=out/a['master']
        assert digest(path.read_bytes())==a['sha256'],choice
        if a['role']!='brand':
            assert min(a['width'],a['height'])>=MIN_SHORT and max(a['width'],a['height'])>=MIN_LONG,choice
            assert a['text_clear'] and a['visual_review'],choice
        with Image.open(WORK/a['source']) as source,Image.open(path) as master:
            source=ImageOps.exif_transpose(source)
            assert master.size==(a['width'],a['height'])
            assert np.array_equal(np.asarray(source.crop(a['export_box'])),np.asarray(master)),choice
            p=a['provenance']
            if p.get('crop_box'):
                with Image.open(WORK/p['original_path']) as original:
                    assert np.array_equal(np.asarray(ImageOps.exif_transpose(original).crop(p['crop_box'])),np.asarray(source)),choice
        for web in a['web']:
            assert web['width']<=a['width'] and web['height']<=a['height'],choice
            with Image.open(out/web['path']) as im:
                assert im.size==(web['width'],web['height']),choice
        checked+=1
    for row in m['assignments']:
        assert row['choices'] and all(c in m['assets'] for c in row['choices'])
    from collections import Counter
    result=dict(ok=True,source_images=len(expected),masters=checked,
        photo_masters=sum(a['role']!='brand' for a in m['assets'].values()),
        minimum_photo_size=f'{MIN_SHORT} short edge / {MIN_LONG} long edge',
        pixel_preservation_checks=checked,uncovered=0,
        relations=dict(Counter(r['relation'] for r in m['assignments'])))
    write_json(out/'validation.json',result)
    print(json.dumps(result,ensure_ascii=False))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    c=sub.add_parser('collect')
    c.add_argument('--candidates',type=int,default=8)
    c.add_argument('--workers',type=int,default=3)
    c.add_argument('--limit',type=int,default=0)
    c.add_argument('--retry',action='store_true')
    c.add_argument('--ids',nargs='+')
    sub.add_parser('board')
    sub.add_parser('local')
    sub.add_parser('reaudit')
    sub.add_parser('export')
    sub.add_parser('gallery')
    sub.add_parser('validate')
    args=p.parse_args()
    if args.command=='collect' and not 1<=args.workers<=4:
        p.error('Use 1 to 4 workers')
    globals()[args.command](args)


if __name__=='__main__':
    main()
