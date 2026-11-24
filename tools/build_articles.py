#!/usr/bin/env python3
"""Собирает раздел «Полезные статьи»: /stati/ (список) и /stati/<slug>/ (статьи), блок «Полезные статьи»
на главной (после «Официальные поставки и техподдержка в РК») и записи в sitemap.xml.

Тексты — tools/articles.py. Шапка и подвал — со страницы-образца materials/kt-tron-3/, как у остальных генераторов.
Запускать после build_info_pages.py:  python3 tools/build_articles.py
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_product_pages import LD_BLOCKS, ROOT, SITE, e  # noqa: E402
from spec_block import spec_block  # noqa: E402
from articles import ARTICLES  # noqa: E402

INDEX = {
    'url': '/stati/',
    'h1': 'Полезные статьи',
    'title': 'Статьи о гидроизоляции и ремонте бетона | КТ ТРОН Казахстан',
    'description': 'Полезные статьи о гидроизоляции и ремонте бетона: как выбрать материал, остановить протечку, '
                   'заделать швы и рассчитать расход. Материалы КТ ТРОН в Алматы и по Казахстану.',
}
MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября',
          'ноября', 'декабря']

STYLE = ('<style>.art-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px;margin:1.2rem 0 0}'
         '.art-card{display:flex;flex-direction:column;gap:.55rem;padding:1.2rem 1.25rem;background:#fff;'
         'border:1px solid var(--line,#dcdcdc);border-radius:14px;color:inherit;text-decoration:none;'
         'transition:border-color .2s,transform .2s}.art-card:hover{border-color:#0093dd;transform:translateY(-2px)}'
         '.art-card b{font-size:1.05rem;line-height:1.3;color:#0077b3}.art-card span{color:var(--muted,#6e6e6e);font-size:.9rem;flex:1}'
         '.art-card i{font-style:normal;font-weight:700;color:#0077b3;font-size:.9rem}'
         '.art-all{text-align:center;margin:1.4rem 0 0}.art-all a{font-weight:700;color:#0077b3}'
         '.article{max-width:820px}.article .art-date{color:var(--muted,#6e6e6e);font-size:.9rem;margin:-.4rem 0 1.2rem}'
         '.article h2{margin:1.8rem 0 .6rem}.article .note{background:#e5f5fc;border-radius:10px;padding:.85rem 1rem}'
         '.article .info-table{width:100%;border-collapse:collapse;margin:.6rem 0 1.2rem;background:#fff;font-size:.95rem}'
         '.article .info-table th,.article .info-table td{border:1px solid var(--line,#dcdcdc);padding:.55rem .7rem;'
         'text-align:left;vertical-align:top}.article .info-table th{background:#f5f5f5}'
         '.article .table-wrap{overflow-x:auto}.art-more{margin-top:2rem}</style>')


def ru_date(iso):
    y, m, d = iso.split('-')
    return f'{int(d)} {MONTHS[int(m) - 1]} {y}'


def card(art):
    return (f'<a class="art-card" href="/stati/{art["slug"]}/"><b>{e(art["title"])}</b>'
            f'<span>{e(art["card"])}</span><i>Читать →</i></a>')


def head_for(head, url, title, description, ld, og_type='website'):
    h = head
    h = re.sub(r'<title>.*?</title>', f'<title>{e(title)}</title>', h, flags=re.S)
    h = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{e(description)}"', h)
    h = re.sub(r'<meta property="og:type" content="[^"]*"', f'<meta property="og:type" content="{og_type}"', h)
    h = re.sub(r'<meta property="og:url" content="[^"]*"', f'<meta property="og:url" content="{SITE}{url}"', h)
    h = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{e(title)}"', h)
    h = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{e(description)}"', h)
    h = re.sub(r'<link rel="canonical" href="[^"]*"', f'<link rel="canonical" href="{SITE}{url}"', h)
    blocks = ''.join('<script type="application/ld+json">\n' + json.dumps(x, ensure_ascii=False, indent=2) + '\n</script>'
                     for x in ld)
    h = re.sub(LD_BLOCKS, lambda m: blocks, h, count=1, flags=re.S)
    return h.replace('  </head>', f'    {STYLE}\n  </head>', 1)


def crumbs_ld(items):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u} for i, (n, u) in enumerate(items)]}


def page(head, tail, crumbs_html, inner):
    return (head + '    <main id="top">\n      <section class="section material-page">\n'
            f'        <div class="shell info-page article">\n          <nav class="crumbs" aria-label="Хлебные крошки">{crumbs_html}</nav>\n'
            f'{inner}        </div>\n      </section>\n    </main>\n' + tail)


def build_index(head, tail):
    ld = [crumbs_ld([('Главная', '/'), (INDEX['h1'], INDEX['url'])]),
          {'@context': 'https://schema.org', '@type': 'ItemList', 'itemListElement': [
              {'@type': 'ListItem', 'position': i + 1, 'url': f'{SITE}/stati/{a["slug"]}/', 'name': a['title']}
              for i, a in enumerate(ARTICLES)]}]
    h = head_for(head, INDEX['url'], INDEX['title'], INDEX['description'], ld)
    inner = (f'          <h1>{INDEX["h1"]}</h1>\n'
             '          <p class="lead">Разбираем частые вопросы о гидроизоляции и ремонте бетона: какой материал выбрать, '
             'в каком порядке работать и сколько брать. Факты — из технических описаний завода КТ ТРОН.</p>\n'
             '          <div class="art-grid">' + ''.join(card(a) for a in ARTICLES) + '</div>\n' + spec_block())
    return page(h, tail, '<a href="/">Главная</a> / Полезные статьи', inner)


def build_article(art, head, tail):
    url = f'/stati/{art["slug"]}/'
    title = f'{art["title"]} | КТ ТРОН Казахстан'
    ld = [crumbs_ld([('Главная', '/'), ('Полезные статьи', '/stati/'), (art['title'], url)]),
          {'@context': 'https://schema.org', '@type': 'Article', 'headline': art['title'],
           'description': art['description'], 'datePublished': art['date'], 'dateModified': art.get('modified', art['date']),
           'mainEntityOfPage': SITE + url, 'inLanguage': 'ru',
           'image': SITE + '/images/hero-dam.jpg',
           'author': {'@type': 'Organization', 'name': 'КТ ТРОН Казахстан', 'url': SITE + '/'},
           'publisher': {'@type': 'Organization', 'name': 'КТ ТРОН Казахстан (ТОО «DARHAN»)',
                         'logo': {'@type': 'ImageObject', 'url': SITE + '/images/kt-icon-512.png'}}}]
    h = head_for(head, url, title, art['description'], ld, og_type='article')
    body = re.sub(r'(<table class="info-table">.*?</table>)', r'<div class="table-wrap">\1</div>', art['body'], flags=re.S)
    body = '\n'.join(('          ' + ln) if ln.strip() else '' for ln in body.strip('\n').split('\n'))
    others = [a for a in ARTICLES if a['slug'] != art['slug']][:3]
    inner = (f'          <h1>{e(art["title"])}</h1>\n'
             f'          <p class="art-date">{ru_date(art.get("modified", art["date"]))}</p>\n'
             f'{body}\n' + spec_block() +
             '          <h2 class="art-more">Ещё статьи</h2>\n'
             '          <div class="art-grid">' + ''.join(card(a) for a in others) + '</div>\n'
             '          <p class="art-all"><a href="/stati/">Все статьи →</a></p>\n')
    return page(h, tail, f'<a href="/">Главная</a> / <a href="/stati/">Полезные статьи</a> / {e(art["title"])}', inner)


HOME_START, HOME_END = '<!--kt:stati-->', '<!--/kt:stati-->'


def home_block():
    return (f'      {HOME_START}\n      <section class="section stati" id="stati">\n        {STYLE}\n'
            '        <div class="shell">\n          <div class="section-head">\n'
            '            <p class="eyebrow">Статьи</p>\n            <h2>Полезные статьи</h2>\n          </div>\n'
            '          <div class="art-grid">' + ''.join(card(a) for a in ARTICLES[:4]) + '</div>\n'
            '          <p class="art-all"><a href="/stati/">Все статьи →</a></p>\n'
            f'        </div>\n      </section>\n      {HOME_END}\n')


def update_home():
    p = ROOT / 'index.html'
    s = p.read_text(encoding='utf-8')
    if HOME_START in s:
        s = re.sub(r'[ \t]*' + re.escape(HOME_START) + r'.*?' + re.escape(HOME_END) + r'\n', lambda m: home_block(), s,
                   count=1, flags=re.S)
    else:
        m = re.search(r'<section class="section why" id="why">.*?</section>\n', s, re.S)
        s = s[:m.end()] + '\n' + home_block() + s[m.end():]
    p.write_text(s, encoding='utf-8')


def main():
    template = (ROOT / 'materials/kt-tron-3/index.html').read_text(encoding='utf-8')
    head = template[:template.index('    <main id="top">')]
    tail = template[template.rindex('</main>') + len('</main>\n'):]
    out = ROOT / 'stati/index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_index(head, tail), encoding='utf-8')
    for art in ARTICLES:
        p = ROOT / 'stati' / art['slug'] / 'index.html'
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(build_article(art, head, tail), encoding='utf-8')
    update_home()
    sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    today = date.today().isoformat()
    for url, mod in [('/stati/', today)] + [(f'/stati/{a["slug"]}/', a.get('modified', a['date'])) for a in ARTICLES]:
        loc = SITE + url
        if f'<loc>{loc}</loc>' not in sitemap:
            sitemap = sitemap.replace('</urlset>', f'  <url><loc>{loc}</loc><lastmod>{mod}</lastmod>'
                                                   f'<changefreq>monthly</changefreq><priority>0.6</priority></url>\n</urlset>')
    (ROOT / 'sitemap.xml').write_text(sitemap, encoding='utf-8')
    print('статей собрано:', len(ARTICLES))


if __name__ == '__main__':
    main()
