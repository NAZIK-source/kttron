#!/usr/bin/env python3
"""Собирает страницы /materials/<slug>/ для товаров каталога, у которых нет своей страницы.

Источники (всё уже лежит в репозитории):
  index.html           — карточки каталога: название, описание, фасовка, фото, ссылка на kttron.ru
  assets/main-B89Pv38-2410.js — раздел каталога для каждого товара
  specs.json           — таблицы характеристик завода
  prices.json          — цены «от … ₸ за 1 кг» (на странице их потом обновляет kt-prices.js)
  calculator/index.html — какие товары есть в калькуляторе
Шапка, подвал и счётчики берутся со страницы-образца materials/kt-tron-3/.

Запуск из корня репозитория:  python3 tools/build_product_pages.py
Пересоздаёт страницы, materials/index.html, sitemap.xml и pages.json.
После него запустите tools/build_info_pages.py (кнопки «Техническое описание (PDF)») и tools/build_own_texts.py (текст «О материале»).
"""
import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://kttron.kz'
WA = '77751810595'

CATEGORIES = {
    'hydro': 'Гидроизоляция',
    'repair': 'Ремонт бетона',
    'grout': 'Подливочные составы',
    'inject': 'Инъектирование',
    'seals': 'Швы и герметизация',
    'protect': 'Защита бетона и металла',
    'additives': 'Добавки в бетон',
    'leaks': 'Остановка протечек',
    'adhesives': 'Клей для плитки',
}

# В данных каталога эти товары записаны в «Гидроизоляцию», но это не она
CATEGORY_FIX = {'КТ ТРОН-8': 'leaks', 'КТ ТРОН-101': 'adhesives'}

TRANSLIT = dict(zip('абвгдеёжзийклмнопрстуфхцчшщъыьэюя',
                    ['a', 'b', 'v', 'g', 'd', 'e', 'e', 'zh', 'z', 'i', 'y', 'k', 'l', 'm', 'n', 'o', 'p', 'r',
                     's', 't', 'u', 'f', 'h', 'ts', 'ch', 'sh', 'sch', '', 'y', '', 'e', 'yu', 'ya']))


def translit(text):
    return ''.join(TRANSLIT.get(c, c) for c in text.lower())


def slug_of(name):
    return re.sub(r'-{2,}', '-', re.sub(r'[^a-z0-9]+', '-', translit(name))).strip('-')


def factory_name(name):
    # Завод пишет «КТтрон-3», люди ищут «кттрон 3» и «kttron 3»
    return name.replace('КТ ТРОН', 'КТтрон')


def latin_name(name):
    return re.sub(r'[\s-]+', ' ', translit(factory_name(name))).strip()


# Подряд идущие блоки JSON-LD в <head> (нежадно: дальше идёт счётчик Метрики)
LD_BLOCKS = r'<script type="application/ld\+json">.*?</script>(?:\s*<script type="application/ld\+json">.*?</script>)*'


def e(text):
    return html.escape(text, quote=True)


def round_half_up(value):
    # Как Math.round в браузере: 2722,5 → 2723 (round() в Python дал бы 2722)
    return int(value + 0.5)


def fmt_price(value):
    return f'{round_half_up(value):,}'.replace(',', ' ')


def price_info(prices, name):
    v = prices.get(name)
    if isinstance(v, (int, float)) and v > 0:
        return v, 'кг'
    if isinstance(v, dict) and v.get('price'):
        return v['price'], v.get('unit', 'шт')
    return None, None


def load_products():
    index = (ROOT / 'index.html').read_text(encoding='utf-8')
    bundle = (ROOT / 'assets/main-B89Pv38-2410.js').read_text(encoding='utf-8')
    # Страницы, сделанные вручную, — те, что прописаны в коде каталога (в index.html ссылка теперь у всех)
    home_bundle = (ROOT / 'assets/main-kt20261024.js').read_text(encoding='utf-8')
    handmade = set(re.findall(r'page:`(/materials/[^`]+)`', home_bundle))
    cats = dict(re.findall(r'\{id:`(p\d+)`,name:`[^`]*`[\s\S]*?category:`([^`]*)`', bundle))
    products = []
    for card in re.findall(r'<article class="product">(.*?)</article>', index, re.S):
        def pick(pattern):
            m = re.search(pattern, card, re.S)
            return html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else ''
        pid = re.search(r'data-add="(p\d+)"', card).group(1)
        page = re.search(r'href="(/materials/[^"]+)"', card)
        detail = re.search(r'<div class="detail-body">(.*?)</div>\s*</details>', card, re.S)
        products.append({
            'id': pid,
            'name': pick(r'<h3[^>]*>(.*?)</h3>'),
            'desc': pick(r'<p class="desc">(.*?)</p>'),
            'pack': pick(r'<div class="pack">[^:]*:\s*([^<]+)</div>'),
            'image': re.search(r'<img src="([^"?]+)', card).group(1),
            'source': re.search(r'href="(https://www\.kttron\.ru/[^"]+)"', card).group(1),
            'own_page': page.group(1) if page and page.group(1) in handmade else None,
            'category': CATEGORY_FIX.get(pick(r'<h3[^>]*>(.*?)</h3>'), cats.get(pid, 'repair')),
            'detail': re.sub(r'\s*<p class="detail-source">.*?</p>', '', detail.group(1)).strip() if detail else '',
        })
    for p in products:
        p['url'] = p['own_page'] or f'/materials/{slug_of(p["name"])}/'
    return products


def consumption_fact(rows):
    for r in rows:
        if len(r) != 2 or not r[0].startswith('Расход') or 'вод' in r[0].lower():
            continue
        label, value = r
        if 'толщиной 1 мм' in label:
            return f'{value} кг/м² на 1 мм'
        if 'м³' in label:
            return f'{value} кг/м³'
        if 'м²' in label:
            return f'{value} кг/м²'
    return None


def temperature_fact(rows):
    for r in rows:
        if len(r) == 2 and r[0].startswith('Температура применения'):
            return r[1]
    return None


def specs_table(rows):
    out = []
    for r in rows:
        if len(r) == 1:
            out.append(f'<tr><th colspan="2">{e(r[0])}</th></tr>')
        else:
            out.append(f'<tr><td>{e(r[0])}</td><td>{e(r[1])}</td></tr>')
    return '<div class="spec-wrap"><table class="spec">' + ''.join(out) + '</table></div>'


def json_ld(p, price, unit):
    crumbs = {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Главная', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Материалы', 'item': SITE + '/materials/'},
            {'@type': 'ListItem', 'position': 3, 'name': p['name'], 'item': SITE + p['url']},
        ],
    }
    product = {
        '@context': 'https://schema.org',
        '@type': 'Product',
        'name': p['name'],
        'alternateName': [factory_name(p['name']), latin_name(p['name'])],
        'description': p['desc'],
        'image': SITE + p['image'],
        'sku': p['id'],
        'brand': {'@type': 'Brand', 'name': 'КТ ТРОН'},
        # Путь категории через «>»: так его принимает Google в отчёте «Данные о товарах»
        'category': 'Строительные материалы > ' + CATEGORIES.get(p['category'], 'Ремонт бетона'),
        'url': SITE + p['url'],
    }
    if price:
        product['offers'] = {
            '@type': 'Offer',
            'url': SITE + p['url'],
            'priceCurrency': 'KZT',
            'price': str(round_half_up(price)),
            'priceSpecification': {
                '@type': 'UnitPriceSpecification',
                'price': str(round_half_up(price)),
                'priceCurrency': 'KZT',
                'unitCode': 'KGM' if unit == 'кг' else ('MTR' if unit == 'м' else 'H87'),
            },
            # Все материалы — под заказ
            'availability': 'https://schema.org/BackOrder',
            'itemCondition': 'https://schema.org/NewCondition',
            'seller': {'@type': 'Organization', 'name': 'ТОО DARHAN (КТ ТРОН Казахстан)'},
            'areaServed': 'KZ',
        }
    dump = lambda d: json.dumps(d, ensure_ascii=False, indent=2).replace('</', '<\\/')
    return (f'<script type="application/ld+json">\n{dump(crumbs)}\n</script>\n'
            f'<script type="application/ld+json">\n{dump(product)}\n</script>')


def build_page(template_head, template_tail, p, products, specs, prices, calc_ids):
    name, fname = p['name'], factory_name(p['name'])
    price, unit = price_info(prices, name)
    rows = specs.get(name, [])
    alt = fname if fname != name else ''
    title = f'{fname} ({name}) — купить в Алматы, цена, характеристики' if alt else f'{name} — купить в Алматы, цена, характеристики'
    description = (f'{name}{" (" + fname + ")" if alt else ""} в Алматы: {p["desc"].rstrip(".")}. '
                   f'Фасовка {p["pack"]}. Официальный дистрибьютор КТ ТРОН, поставка под заказ по Алматы и Казахстану.')

    head = template_head
    head = re.sub(r'<title>.*?</title>', f'<title>{e(title)}</title>', head, flags=re.S)
    head = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{e(description)}"', head)
    head = re.sub(r'<meta property="og:url" content="[^"]*"', f'<meta property="og:url" content="{SITE}{p["url"]}"', head)
    head = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{e(title)}"', head)
    head = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{e(description)}"', head)
    head = re.sub(r'<meta property="og:image" content="[^"]*"', f'<meta property="og:image" content="{SITE}{p["image"]}"', head)
    head = re.sub(r'<link rel="canonical" href="[^"]*"', f'<link rel="canonical" href="{SITE}{p["url"]}"', head)
    head = re.sub(LD_BLOCKS, lambda m: json_ld(p, price, unit), head, count=1, flags=re.S)

    facts = [('Фасовка', p['pack']),
             ('Цена', f'от {fmt_price(price)} ₸ за 1 {unit}' if price else 'по запросу')]
    if rows:
        cons, temp = consumption_fact(rows), temperature_fact(rows)
        if cons:
            facts.append(('Расход', cons))
        if temp:
            facts.append(('Температура', temp))
    facts_html = ''.join(f'<div class="fact"><span>{e(k)}</span><b>{e(v)}</b></div>' for k, v in facts)

    wa_text = f'Здравствуйте! Нужен {name}. Подскажите цену и наличие в Алматы.'
    buttons = [f'<a class="btn btn-solid btn-lg" href="https://wa.me/{WA}?text={quote(wa_text)}" target="_blank" rel="noopener">Узнать цену и наличие</a>']
    if name in calc_ids:
        buttons.append(f'<a class="btn btn-ghost-dark btn-lg" href="/calculator/?material={calc_ids[name]}">Рассчитать расход</a>')
    buttons.append('<a class="btn btn-ghost-dark btn-lg" href="/#catalog">Весь каталог</a>')

    related = [q for q in products if q['category'] == p['category'] and q['id'] != p['id']]
    related_html = ''.join(f'<a href="{q["url"]}">{e(q["name"])}</a>' for q in related)
    aka = ', '.join(x for x in [alt, latin_name(name)] if x)

    main = f'''    <main id="top">
      <section class="section material-page">
        <div class="shell">
          <nav class="crumbs" aria-label="Хлебные крошки"><a href="/">Главная</a> / <a href="/materials/">Материалы</a> / {e(name)}</nav>
          <div class="material-layout">
            <img src="{p['image']}" alt="{e(name)} — {e(CATEGORIES.get(p['category'], '').lower())}" width="640" height="480" />
            <div>
              <p class="eyebrow">{e(CATEGORIES.get(p['category'], ''))} · консультации и поставка под заказ в Алматы</p>
              <h1>{e(name)}</h1>
              <p class="aka">Также пишут: {e(aka)}</p>
              <p class="muted">{e(p['desc'])}</p>
              <div class="facts">{facts_html}</div>
              <div class="hero-cta">
                {chr(10).join('                ' + b if i else b for i, b in enumerate(buttons))}
              </div>
            </div>
          </div>
          <h2>Описание производителя</h2>
          <div class="material-detail">{p['detail']}</div>
'''
    if rows:
        main += f'''          <h2>Характеристики {e(name)}</h2>
          <p class="muted">По техническому описанию завода.</p>
          {specs_table(rows)}
'''
    main += f'''          <p class="muted">Источник: описание и характеристики завода КТ ТРОН (kttron.ru).</p>
          <h2>{e(name)} в Алматы</h2>
          <p>{e(name)}{" (" + e(fname) + ")" if alt else ""} — материал завода КТ ТРОН. ТОО DARHAN — официальный дистрибьютор завода в Казахстане: консультации и поставка под заказ в Алматы, ул. Шевченко 118, офис 221, доставка по Казахстану. Цену с учётом объёма, наличие и подбор материала под ваш объект подскажем в WhatsApp или по телефону <a href="tel:+77751810595">+7 775 181-05-95</a>.</p>
'''
    if related:
        main += f'''          <h2>Другие материалы раздела «{e(CATEGORIES.get(p['category'], ''))}»</h2>
          <div class="related">{related_html}</div>
'''
    main += '''        </div>
      </section>
    </main>
'''
    return head + main + template_tail


def patch_own_page(p, prices):
    # У 8 товаров страницы сделаны вручную: правим только заголовки, «Также пишут» и цену
    path = ROOT / p['url'].strip('/') / 'index.html'
    s = path.read_text(encoding='utf-8')
    name, fname = p['name'], factory_name(p['name'])
    title = f'{fname} ({name}) — купить в Алматы, цена, характеристики'
    description = (f'{name} ({fname}) в Алматы: {p["desc"].rstrip(".")}. '
                   f'Фасовка {p["pack"]}. Официальный дистрибьютор КТ ТРОН, поставка под заказ по Алматы и Казахстану.')
    s = re.sub(r'<title>.*?</title>', f'<title>{e(title)}</title>', s, flags=re.S)
    s = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{e(description)}"', s)
    s = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{e(title)}"', s)
    s = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{e(description)}"', s)
    if 'class="aka"' not in s:
        s = s.replace(f'<h1>{e(name)}</h1>', f'<h1>{e(name)}</h1>\n              <p class="aka">Также пишут: {e(fname)}, {e(latin_name(name))}</p>', 1)
        s = s.replace('  </head>', '    <style>.aka{color:var(--muted);font-size:.9rem;margin:-.2rem 0 .6rem}</style>\n  </head>', 1)
    price, unit = price_info(prices, name)
    # Разметку товара берём ту же, что у собранных страниц: с ценой, наличием и категорией
    s = re.sub(LD_BLOCKS, lambda m: json_ld(p, price, unit), s, count=1, flags=re.S)
    if price:
        s = re.sub(r'(<div class="fact"><span>Цена</span><b>)[^<]*(</b>)', lambda m: f'{m.group(1)}от {fmt_price(price)} ₸ за 1 {unit}{m.group(2)}', s)
    path.write_text(s, encoding='utf-8')


def materials_index(template_head, template_tail, products, prices):
    head = template_head
    title = 'Материалы КТ ТРОН (КТтрон) в Алматы — каталог, цены, характеристики'
    description = 'Все материалы завода КТ ТРОН у официального дистрибьютора в Алматы: гидроизоляция, ремонт бетона, подливка, швы, защита, добавки. Цены от, характеристики, расход.'
    head = re.sub(r'<title>.*?</title>', f'<title>{e(title)}</title>', head, flags=re.S)
    head = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{e(description)}"', head)
    head = re.sub(r'<meta property="og:url" content="[^"]*"', f'<meta property="og:url" content="{SITE}/materials/"', head)
    head = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{e(title)}"', head)
    head = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{e(description)}"', head)
    head = re.sub(r'<link rel="canonical" href="[^"]*"', f'<link rel="canonical" href="{SITE}/materials/"', head)
    crumbs = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Главная', 'item': SITE + '/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Материалы', 'item': SITE + '/materials/'}]}
    head = re.sub(LD_BLOCKS,
                  lambda m: '<script type="application/ld+json">\n' + json.dumps(crumbs, ensure_ascii=False, indent=2) + '\n</script>',
                  head, count=1, flags=re.S)
    blocks = []
    for cat, label in CATEGORIES.items():
        items = [p for p in products if p['category'] == cat]
        if not items:
            continue
        cards = []
        for p in items:
            price, unit = price_info(prices, p['name'])
            price_html = f'от {fmt_price(price)} ₸ за 1 {unit}' if price else 'Цена по запросу'
            cards.append(f'<a class="mat-card" href="{p["url"]}"><img src="{p["image"]}" alt="{e(p["name"])}" loading="lazy" width="160" height="140" />'
                         f'<b>{e(p["name"])}</b><span>{e(p["desc"])}</span><em>{e(price_html)}</em></a>')
        blocks.append(f'          <h2>{e(label)}</h2>\n          <div class="mat-grid">{"".join(cards)}</div>\n')
    main = f'''    <main id="top">
      <section class="section material-page">
        <div class="shell">
          <nav class="crumbs" aria-label="Хлебные крошки"><a href="/">Главная</a> / Материалы</nav>
          <p class="eyebrow">Официальный дистрибьютор в Казахстане</p>
          <h1>Материалы КТ ТРОН в Алматы</h1>
          <p class="muted">{len(products)} материалов завода КТ ТРОН (КТтрон): у каждого своя страница с ценой «от», характеристиками и расходом. Офис и консультации — Алматы, ул. Шевченко 118, офис 221.</p>
          <p class="related">Популярные задачи: <a href="/gidroizolyaciya/fundamenta/">Гидроизоляция фундамента</a><a href="/gidroizolyaciya/podvala/">Гидроизоляция подвала</a><a href="/gidroizolyaciya/basseyna/">Гидроизоляция бассейна</a><a href="/remont-betona/">Ремонт бетона</a></p>
{"".join(blocks)}        </div>
      </section>
    </main>
'''
    return head + main + template_tail


def main():
    template = (ROOT / 'materials/kt-tron-3/index.html').read_text(encoding='utf-8')
    template_head = template[:template.index('    <main id="top">')]
    template_tail = template[template.rindex('</main>') + len('</main>\n'):]
    # Стили для строки «Также пишут» и списка материалов — одним блоком в <head>
    extra_css = ('    <style>.aka{color:var(--muted);font-size:.9rem;margin:-.2rem 0 .6rem}'
                 '.material-detail{max-width:860px}'
                 '.mat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;margin:0 0 1.6rem}'
                 '.mat-card{display:grid;gap:4px;padding:12px;border:1px solid var(--line);border-radius:var(--radius);background:#fff;text-decoration:none;color:var(--ink)}'
                 '.mat-card:hover{border-color:var(--brand)}.mat-card img{width:100%;height:140px;object-fit:contain;background:var(--paper);border-radius:10px}'
                 '.mat-card span{color:var(--muted);font-size:.85rem}.mat-card em{font-style:normal;font-weight:700;color:var(--brand-deep)}</style>\n')
    template_head = template_head.replace('  </head>', extra_css + '  </head>', 1)

    products = load_products()
    specs = json.loads((ROOT / 'specs.json').read_text(encoding='utf-8'))
    prices = json.loads((ROOT / 'prices.json').read_text(encoding='utf-8'))
    calc = (ROOT / 'calculator/index.html').read_text(encoding='utf-8')
    calc_ids = {n: i for i, n in re.findall(r'\{ id: "([^"]+)", name: "([^"]+)"', calc)}

    built = 0
    for p in products:
        if p['own_page']:
            continue
        out = ROOT / p['url'].strip('/') / 'index.html'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_page(template_head, template_tail, p, products, specs, prices, calc_ids), encoding='utf-8')
        built += 1

    (ROOT / 'materials/index.html').write_text(materials_index(template_head, template_tail, products, prices), encoding='utf-8')

    # Карточка товара в каталоге берёт отсюда ссылку «Страница материала»
    (ROOT / 'pages.json').write_text(json.dumps({p['name']: p['url'] for p in products}, ensure_ascii=False) + '\n', encoding='utf-8')

    for p in products:
        if p['own_page']:
            patch_own_page(p, prices)

    today = date.today().isoformat()
    sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    for p in products:
        loc = SITE + p['url']
        if f'<loc>{loc}</loc>' not in sitemap:
            sitemap = sitemap.replace('</urlset>', f'  <url><loc>{loc}</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>\n</urlset>')
    (ROOT / 'sitemap.xml').write_text(sitemap, encoding='utf-8')
    print(f'страниц товаров собрано: {built}, всего в каталоге: {len(products)}')


if __name__ == '__main__':
    main()
