#!/usr/bin/env python3
"""Maintain the canonical media library without implementing the client site."""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
import hashlib
import html
import json
from pathlib import Path
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/media'
RELATIONS={
    'brand_asset':'Marka görseli',
    'same_photo':'Aynı çekim',
    'same_photo_bottom_crop':'Aynı çekim; alt damga kırpıldı',
    'exact_online_photo':'Birebir çevrimiçi kaynak',
    'similar_reference':'Benzer model referansı',
    'different_provided_photo':'Başka verilmiş çekim / farklı açı veya model',
}

def read(name):return json.loads((DATA/name).read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def path(relative):
    p=(ROOT/relative).resolve()
    if ROOT not in p.parents:raise ValueError(f'Path outside project: {relative}')
    return p
def link(label,relative):return f'[{label}](<{quote("../"+relative,safe="/._-~")}>)'


def validate(args):
    import numpy as np
    from PIL import Image,ImageOps
    catalog=read('catalog.json');originals=read('originals.json');mapping=read('mapping.json')
    assets={a['id']:a for a in catalog['assets']};source_rows={r['id']:r for r in originals['media']}
    assert len(assets)==len(catalog['assets']) and len(source_rows)==len(originals['media'])
    referenced=set();web_count=0
    for f in originals['delivery_files']:
        assert sha(path(f['path']))==f['sha256'],f['path']
    for r in originals['media']:
        assert r['title'] and r['description']
        assert sha(path(r['path']))==r['sha256'],r['id']
        assert path(r['archive']).is_file(),r['id']
    for a in assets.values():
        assert a['title'] and a['description'] and a['alt_tr'] and a['suggested_usage'],a['id']
        assert sha(path(a['master']))==a['sha256'],a['id']
        p=a['provenance'];assert sha(path(p['source_path']))==p['source_sha256']
        with Image.open(path(a['master'])) as master,Image.open(path(p['source_path'])) as original:
            assert master.size==(a['width'],a['height'])
            cropped=ImageOps.exif_transpose(original).crop(p['source_crop_box'])
            assert np.array_equal(np.asarray(master),np.asarray(cropped)),a['id']
        if a['role']!='brand':
            assert min(a['width'],a['height'])>=1000 and max(a['width'],a['height'])>=1500,a['id']
            assert a['text_clear'] and a['visual_review'],a['id']
        for w in a['web']:
            assert sha(path(w['path']))==w['sha256']
            with Image.open(path(w['path'])) as im:
                assert im.size==(w['width'],w['height'])
            assert w['width']<=a['width'] and w['height']<=a['height']
            web_count+=1
    expected={r['id'] for r in source_rows.values() if r['type']=='image'}
    assert {r['original_id'] for r in mapping['assignments']}==expected
    for r in mapping['assignments']:
        assert r['selected'] and all(i in assets for i in r['selected']),r['original_id']
        referenced.update(r['selected'])
    actual={p.resolve() for p in (ROOT/'assets/catalog').rglob('*') if p.is_file()}
    assert actual=={path(a['master']) for a in assets.values()},'Unexpected master copy or missing master'
    summary=dict(ok=True,original_media=len(source_rows),original_images=len(expected),
        videos=sum(r['type']=='video' for r in source_rows.values()),
        delivery_files=len(originals['delivery_files']),catalog_assets=len(assets),
        catalog_photos=sum(a['role']!='brand' for a in assets.values()),web_variants=web_count,
        mapped_images=len(mapping['assignments']),uncovered=0,
        pixel_preservation_checks=len(assets),roles=dict(Counter(a['role'] for a in assets.values())),
        referenced_catalog_assets=len(referenced))
    target=ROOT/'data/reports/media-validation.json';target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False))


def docs(args):
    catalog=read('catalog.json');originals=read('originals.json');mapping=read('mapping.json')
    assets={a['id']:a for a in catalog['assets']};by_orig={r['original_id']:r for r in mapping['assignments']}
    used=defaultdict(list)
    for r in mapping['assignments']:
        for i in r['selected']:used[i].append(r['original_id'])
    lines=['# Fotoğraf envanteri — orijinaller ve katalog seçimi','',
        'Bu dosya, tekrar tek tek görsel açmadan siteyi hazırlamak içindir. Açıklamalar önceki görsel incelemelerden aktarılmıştır. Yeni site henüz yapılmadı.','',
        '**Özet:** 79 orijinal görsel + 2 video; katalogda 43 farklı fotoğraf + 1 logo. 79 görselin tamamı bir seçim/alternatife bağlıdır.','',
        '- `O...`: müşteriden gelen orijinal medya. ZIP adı ve üye adı aşağıdaki kaynak indeksinde tutulur.',
        '- `P-...`: müşteriden gelen çekimden seçilmiş katalog kopyası. Firma aidiyeti bağımsız olarak doğrulanmış değildir.',
        '- `R-...`: başka model/kaynak referansı. Tamamlanan firma işi olarak etiketlenmez.',
        '- `LOGO-01`: marka görseli; kendi yazısı korunur. JPEG ve opak zeminlidir.',
        '- Eşleştirme alternatifi, aynı işin bitmiş hâli veya aynı ürünün başka açısı anlamına gelmeyebilir; ilişki sütununa bakın.',
        '- Fotoğraf master ölçüleri: kısa kenar ≥1000 px, uzun kenar ≥1500 px. Yapay büyütme yok. WebP kopyaları 600/1000/1400 px; kaynağı aşan boyut üretilmez.','',
        '## Yeni sette hangi fotoğraf var?','',
        '| ID | Dosya / boyut | Fotoğrafta ne var? | Önerilen kullanım | Orijinal eşleşmeleri |',
        '|---|---|---|---|---|']
    for a in catalog['assets']:
        file=link(a['master'].split('/')[-1],a['master'])
        refs=', '.join(used[a['id']]) or 'Ek alternatif; ana eşleştirmede kullanılmadı'
        lines.append(f'| **{a["id"]}** · {a["role_label"]} | {file}<br>{a["width"]}×{a["height"]} | **{a["title"]}.** {a["description"]} | {a["suggested_usage"]} | {refs} |')
    lines+=['','## Her orijinalin içeriği ve yeni setteki karşılığı','',
        '| Orijinal | İçerik | Dosya / ölçü | Seçilen / alternatif | İlişki |','|---|---|---|---|---|']
    for r in originals['media']:
        size=f'{r.get("display_width",r.get("width","?"))}×{r.get("display_height",r.get("height","?"))}'
        if r['type']=='video':
            size+=f' · {r["duration"]:.1f} sn';selected='Video arşivde; web sürümü seçilmedi';relation='Ortadan bir kareyle içerik kontrol edildi; tam kurgu/kalite kabulü yok'
        else:
            m=by_orig[r['id']];selected=' / '.join(m['selected']);relation=RELATIONS[m['relation']]
        lines.append(f'| **{r["id"]}** | **{r["title"]}.** {r["description"]} | {link("orijinali aç",r["path"])}<br>{size} | {selected} | {relation} |')
    lines+=['','## Orijinal teslim / ZIP indeksi','',
        'Orijinal dosya adları kaybolmadı. Aşağıdaki üye adları ve SHA-256 özetleri `data/media/originals.json` içinde de bulunur.','',
        '| ID | Teslim dosyası | ZIP üyesi / gelen dosya adı | SHA-256 başlangıcı |','|---|---|---|---|']
    for r in originals['media']:
        lines.append(f'| {r["id"]} | {link(Path(r["archive"]).name,r["archive"])} | {r["member"]} | `{r["sha256"][:16]}` |')
    lines+=['','## Araçlar ve tek kaynak','',
        '- `data/media/catalog.json`: ID, içerik, alt metin, kategori, kullanım, master/WebP yolları ve kaynak izi.',
        '- `data/media/originals.json`: 81 orijinal medya ve teslim arşivleri.',
        '- `data/media/mapping.json`: 79 görselin ana seçim/alternatif bağlantıları.',
        '- `make media-check`: kaynak, master, WebP, eşleştirme ve kırpım piksel kontrolü.',
        '- `make media-docs`: bu Markdown dosyasını güncel JSON kayıtlarından yeniden üretir.',
        '- `preview/index.html`: temiz seçim; `preview/comparison.html`: orijinal/seçim karşılaştırması. Bunlar yalnızca yerel inceleme aracıdır.','']
    (ROOT/'docs/FOTO_ENVANTERI.md').write_text('\n'.join(lines))
    print('docs/FOTO_ENVANTERI.md generated:',len(catalog['assets']),'catalog assets,',len(originals['media']),'original media')


def preview(args):
    catalog=read('catalog.json');originals=read('originals.json');mapping=read('mapping.json')
    assets={a['id']:a for a in catalog['assets']};source={r['id']:r for r in originals['media']}
    esc=lambda v:html.escape(str(v),quote=True)
    def photo(a):
        p=a['web'][0]['path'] if a['web'] else a['master']
        return f'<a href="../{esc(a["master"])}"><img loading="lazy" src="../{esc(p)}" alt="{esc(a["alt_tr"])}"></a>'
    def shell(body,title,other):
        buttons=''.join(f'<button data-filter="{k}">{v}</button>' for k,v in [('all','Tümü'),('coffee','Kahve köşesi'),('kitchen','Mutfak'),('hall','Antre / ayna'),('tv','TV'),('workshop','Atölye'),('logo','Logo')])
        return f'''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#f3efe8;color:#29231d;font:15px system-ui}}header{{padding:26px;max-width:1500px;margin:auto}}h1{{font-size:27px}}h2{{font-size:17px}}main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,390px),1fr));gap:18px;padding:0 22px 28px;max-width:1520px;margin:auto}}article{{padding:16px;background:white;border:1px solid #d6c9b8;border-radius:10px;min-width:0}}img{{width:100%;height:310px;object-fit:contain;background:#f8f5f0}}button{{padding:8px 13px;margin:4px;border:1px solid #c7b69d;border-radius:5px;background:white;cursor:pointer}}a{{color:#74512b}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}details{{font-size:12px;overflow-wrap:anywhere}}details img{{height:200px}}[hidden]{{display:none!important}}@media(max-width:450px){{header{{padding:16px}}main{{padding:0 10px 20px}}.pair img{{height:240px}}}}</style>
<header><h1>{title}</h1><p>Yerel medya inceleme aracı · 43 fotoğraf + logo · Gerçek çekimler ve model referansları ayrı etiketlidir.</p><p><a href="{other[0]}">{other[1]}</a> · <a href="../docs/FOTO_ENVANTERI.md">Açıklamalı Markdown envanteri</a></p><nav>{buttons}</nav></header><main>{body}</main>
<script>document.querySelectorAll('button').forEach(b=>b.onclick=()=>document.querySelectorAll('article').forEach(a=>a.hidden=b.dataset.filter!=='all'&&a.dataset.category!==b.dataset.filter))</script></html>'''
    cards=[]
    for a in catalog['assets']:
        cards.append(f'<article data-category="{a["category"]}">{photo(a)}<h2>{a["id"]} · {esc(a["title"])}</h2><p>{esc(a["role_label"])} · {a["width"]}×{a["height"]} px</p><p>{esc(a["description"])}</p></article>')
    target=ROOT/'preview';target.mkdir(exist_ok=True)
    (target/'index.html').write_text(shell(''.join(cards),'Katalog için seçilen görseller',('comparison.html','Orijinal / seçim karşılaştırması')))
    cards=[]
    for r in mapping['assignments']:
        o=source[r['original_id']];panels=''.join(f'<section>{photo(assets[i])}<p>{i} · {esc(assets[i]["title"])}</p></section>' for i in r['selected'])
        cards.append(f'<article data-category="{r["category"]}"><h2>{o["id"]} · {esc(o["title"])}</h2><p>{RELATIONS[r["relation"]]}</p><div class="pair">{panels}</div><details><summary>Orijinal ve açıklama</summary><p>{esc(o["description"])}</p><a href="../{esc(o["path"])}"><img loading="lazy" src="../{esc(o["path"])}" alt="Orijinal"></a></details></article>')
    (target/'comparison.html').write_text(shell(''.join(cards),'Orijinaller ve katalog seçimi',('index.html','Yalnızca temiz seçimi göster')))
    print('preview/index.html and preview/comparison.html generated')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['validate','docs','preview'])
    args=p.parse_args();globals()[args.command](args)

if __name__=='__main__':main()
