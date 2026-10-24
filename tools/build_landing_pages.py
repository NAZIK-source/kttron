#!/usr/bin/env python3
"""Собирает страницы под частые запросы: гидроизоляция фундамента, подвала, бассейна, ремонт бетона.

Какие материалы для какой задачи — по разделу «Область применения» в описаниях завода
(index.html). Примеры расчёта — по нормам расхода завода и ценам из prices.json,
теми же, что в калькуляторе. Шапка и подвал — со страницы-образца materials/kt-tron-3/.

Запуск из корня репозитория:  python3 tools/build_landing_pages.py
"""
import json
import math
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_product_pages import (LD_BLOCKS, ROOT, SITE, WA, e, fmt_price,  # noqa: E402
                                 load_products, price_info, round_half_up)

# Пример расчёта: материал, норма и площадь. kg_per = кг на 1 м² (или на 1 м² × 1 мм, если thick)
Example = dict


def example_text(ex, prices, pack_of):
    name = ex['name']
    price, unit = price_info(prices, name)
    lo, hi = ex['norm']
    factor = ex['area'] * ex.get('thick', 1) * ex.get('scale', 1)
    kg_lo, kg_hi = factor * lo, factor * hi
    pack = pack_of[name]
    bags_lo, bags_hi = math.ceil(kg_lo / pack), math.ceil(kg_hi / pack)
    unit_kg = ex.get('kit', pack)
    kg = f'{fmt_num(kg_lo)}–{fmt_num(kg_hi)}' if kg_lo != kg_hi else fmt_num(kg_lo)
    bags = f'{bags_lo}–{bags_hi}' if bags_lo != bags_hi else str(bags_lo)
    text = f'{ex["what"]}: {kg} кг {e(name)} — {bags} {ex.get("pack_word", "меш.")} по {fmt_num(unit_kg)} кг'
    if price and unit == 'кг':
        s_lo, s_hi = round_half_up(bags_lo * unit_kg * price), round_half_up(bags_hi * unit_kg * price)
        text += f', ориентировочно от {fmt_price(s_lo)}{"–" + fmt_price(s_hi) if s_hi > s_lo else ""} ₸'
    return text + '.'


def fmt_num(x):
    return (f'{x:.1f}'.rstrip('0').rstrip('.')).replace('.', ',')


PAGES = [
    {
        'url': '/gidroizolyaciya/fundamenta/',
        'h1': 'Гидроизоляция фундамента в Алматы',
        'title': 'Гидроизоляция фундамента в Алматы — материалы КТ ТРОН (КТтрон), цены, расход',
        'description': 'Материалы для гидроизоляции фундамента в Алматы: проникающая КТ ТРОН-1 и 11, эластичная КТ ТРОН-10, герметизация швов. Цены от, расчёт расхода, поставка под заказ в Алматы.',
        'eyebrow': 'Гидроизоляция',
        'image': '/images/objects/o007.jpg',
        'lead': ('Фундамент постоянно контактирует с грунтовой водой и влагой. Для защиты бетона завод КТ ТРОН выпускает '
                 'проникающие, обмазочные и эластичные составы, а также материалы для швов и вводов коммуникаций. '
                 'Подберём систему под ваш фундамент по фото в WhatsApp и рассчитаем количество.'),
        'materials': [
            ('КТ ТРОН-1', 'Проникающая гидроизоляция. По описанию завода — для подземных частей зданий, подвалов и фундаментов: вода не проходит через бетон снаружи.'),
            ('КТ ТРОН-11', 'Проникающая гидроизоляция для бетонов, прослуживших длительный срок: подземные части зданий, фундаменты, подвалы.'),
            ('КТ ТРОН-10 1К', 'Эластичная гидроизоляция: внешняя и внутренняя гидроизоляция подземных частей зданий, перекрывает трещины до 1 мм.'),
            ('КТ ТРОН-10 2К', 'Двухкомпонентная эластичная гидроизоляция для подземных частей зданий и конструкций с возможными микротрещинами.'),
            ('КТ ТРОН-2', 'Герметизация швов, примыканий, трещин и вводов коммуникаций.'),
            ('Гидрошнур НП', 'Набухающий профиль для рабочих швов бетонирования и фундаментных плит.'),
        ],
        'examples': [
            Example(what='Проникающая гидроизоляция 100 м² стен фундамента', name='КТ ТРОН-1', norm=(0.8, 1.2), area=100, pack_word='вед.'),
            Example(what='Эластичная гидроизоляция 100 м² слоем 2 мм', name='КТ ТРОН-10 1К', norm=(1.5, 1.5), area=100, thick=2),
        ],
        'steps': [
            'Пришлите фото фундамента и опишите ситуацию (есть ли вода, трещины, швы) — подберём систему материалов.',
            'Подготовьте основание: удалите разрушенный бетон, грязь и старые покрытия, расшейте трещины и швы.',
            'Загерметизируйте швы, примыкания и вводы коммуникаций (КТ ТРОН-2, гидрошнур), при активной протечке — КТ ТРОН-8.',
            'Нанесите гидроизоляцию по техническому описанию завода: проникающие составы КТ ТРОН-1/11 наносятся на влажную поверхность.',
        ],
        'faq': [
            ('Какую гидроизоляцию выбрать для фундамента?',
             'Для бетонного фундамента обычно применяют проникающую гидроизоляцию (КТ ТРОН-1, для старого бетона — КТ ТРОН-11). Если возможны подвижки и микротрещины — эластичную КТ ТРОН-10 1К или 2К. Швы и вводы коммуникаций герметизируют отдельно. Точный состав системы подскажем по фото.'),
            ('Сколько стоит гидроизоляция фундамента?',
             'Зависит от площади, состояния бетона и выбранной системы. Ориентир по материалам — в расчёте выше и в калькуляторе расхода. Точную цену с учётом объёма назовёт менеджер.'),
            ('Можно ли сделать гидроизоляцию изнутри, если снаружи доступа нет?',
             'Да: по описанию завода КТ ТРОН-10 1К и 2К применяются для внешней и внутренней гидроизоляции подземных частей зданий, а проникающие составы уплотняют сам бетон.'),
        ],
        'related': ['/gidroizolyaciya/podvala/', '/gidroizolyaciya/basseyna/', '/remont-betona/'],
    },
    {
        'url': '/gidroizolyaciya/podvala/',
        'h1': 'Гидроизоляция подвала в Алматы',
        'title': 'Гидроизоляция подвала в Алматы — остановка протечек, материалы КТ ТРОН, цены',
        'description': 'Гидроизоляция подвала и цокольного этажа в Алматы: остановка протечек КТ ТРОН-8, проникающая КТ ТРОН-1, эластичная КТ ТРОН-10, герметизация вводов. Цены от, расход.',
        'eyebrow': 'Гидроизоляция',
        'image': '/images/objects/o020.jpg',
        'lead': ('Вода в подвале обычно идёт через трещины, рабочие швы и вводы коммуникаций. Сначала останавливают активные '
                 'протечки и герметизируют швы, затем защищают стены и пол гидроизоляцией. Все материалы для этого '
                 'поставляем под заказ.'),
        'materials': [
            ('КТ ТРОН-8', 'Быстрая остановка активных протечек, первичная обработка швов перед гидроизоляцией подвальных помещений и цокольных этажей.'),
            ('КТ ТРОН-1', 'Проникающая гидроизоляция подвалов и подземных частей зданий.'),
            ('КТ ТРОН-11', 'Проникающая гидроизоляция для старого бетона: подземные части зданий, подвалы.'),
            ('КТ ТРОН-10 1К', 'Эластичная гидроизоляция, внешняя и внутренняя, для подземных частей зданий; перекрывает трещины до 1 мм.'),
            ('КТ ТРОН-2', 'Герметизация швов, трещин и вводов коммуникаций.'),
            ('Гидрошнур НП', 'Набухающий профиль: герметизация вводов подземных коммуникаций и рабочих швов.'),
        ],
        'examples': [
            Example(what='Остановка протечек: 10 м швов и трещин сечением 30×30 мм', name='КТ ТРОН-8', norm=(1850, 1850), area=10, thick=1, scale=0.03 * 0.03, pack_word='вед.'),
            Example(what='Проникающая гидроизоляция 60 м² стен и пола', name='КТ ТРОН-1', norm=(0.8, 1.2), area=60, pack_word='вед.'),
        ],
        'steps': [
            'Найдите, откуда идёт вода: трещины, швы, вводы труб, стык стены и пола. Пришлите фото — подскажем материалы.',
            'Остановите активные протечки быстротвердеющим составом КТ ТРОН-8.',
            'Загерметизируйте швы, примыкания и вводы коммуникаций (КТ ТРОН-2, гидрошнур НП).',
            'Нанесите гидроизоляцию на стены и пол — проникающую (КТ ТРОН-1/11) или эластичную (КТ ТРОН-10) — по техническому описанию завода.',
        ],
        'faq': [
            ('Как остановить воду в подвале, если она течёт прямо сейчас?',
             'Для активных протечек завод выпускает быстротвердеющий состав КТ ТРОН-8 — он останавливает воду через трещины и швы. После этого делают основную гидроизоляцию.'),
            ('Можно ли сделать гидроизоляцию подвала изнутри?',
             'Да. Проникающие составы КТ ТРОН-1/11 и эластичная КТ ТРОН-10 по описанию завода применяются для гидроизоляции подземных частей зданий, в том числе изнутри.'),
            ('Сколько материала нужно на подвал?',
             'Посчитайте в калькуляторе расхода или пришлите размеры помещения в WhatsApp — посчитаем с учётом швов и состояния стен.'),
        ],
        'related': ['/gidroizolyaciya/fundamenta/', '/gidroizolyaciya/basseyna/', '/remont-betona/'],
    },
    {
        'url': '/gidroizolyaciya/basseyna/',
        'h1': 'Гидроизоляция бассейна и резервуара в Алматы',
        'title': 'Гидроизоляция бассейна и резервуара в Алматы — материалы КТ ТРОН, цены, расход',
        'description': 'Гидроизоляция бассейнов, резервуаров и ёмкостей, в том числе с питьевой водой: КТ ТРОН-1, КТ ТРОН-7, КТ ТРОН-10, герметизация швов КТ ТРОН-8, клей КТ ТРОН-101. Алматы.',
        'eyebrow': 'Гидроизоляция',
        'image': '/images/objects/o093.jpg',
        'lead': ('Бассейны, резервуары и ёмкости постоянно под давлением воды. У завода КТ ТРОН есть материалы для '
                 'таких конструкций, в том числе с питьевой водой: проникающая, жёсткая обмазочная и эластичная гидроизоляция, '
                 'составы для швов и клей для облицовки бассейна плиткой.'),
        'materials': [
            ('КТ ТРОН-1', 'Проникающая гидроизоляция бетона: резервуары, в том числе с питьевой водой, бассейны, очистные сооружения.'),
            ('КТ ТРОН-7', 'Жёсткая обмазочная гидроизоляция бассейнов, резервуаров и ёмкостей, в том числе с питьевой водой.'),
            ('КТ ТРОН-10 1К', 'Эластичная гидроизоляция бассейнов, резервуаров и ёмкостей, в том числе с питьевой водой.'),
            ('КТ ТРОН-10 2К', 'Двухкомпонентная эластичная гидроизоляция бассейнов, резервуаров и ёмкостей.'),
            ('КТ ТРОН-8', 'Герметизация конструктивных швов и трещин в резервуарах, в том числе для питьевой воды.'),
            ('КТ ТРОН-101', 'Эластичный клей для плитки, в том числе для облицовки бассейнов.'),
        ],
        'examples': [
            Example(what='Обмазочная гидроизоляция чаши 50 м² слоем 2 мм', name='КТ ТРОН-7', norm=(1.55, 1.55), area=50, thick=2),
            Example(what='Эластичная гидроизоляция 50 м² слоем 2 мм', name='КТ ТРОН-10 2К', norm=(1.5, 1.5), area=50, thick=2, kit=33.5, pack_word='компл.'),
        ],
        'steps': [
            'Пришлите фото чаши или резервуара и расскажите, новый он или после эксплуатации — подберём систему.',
            'Подготовьте бетон: удалите слабый слой и старые покрытия, расшейте трещины и швы.',
            'Загерметизируйте швы и трещины (КТ ТРОН-8), при необходимости отремонтируйте бетон составами КТ ТРОН-3.',
            'Нанесите гидроизоляцию по техническому описанию завода, затем облицуйте плиткой на клей КТ ТРОН-101.',
        ],
        'faq': [
            ('Подходят ли материалы для резервуаров с питьевой водой?',
             'По описанию завода КТ ТРОН-1, КТ ТРОН-7 и КТ ТРОН-10 применяются для резервуаров и ёмкостей, в том числе с питьевой водой. Документы по запросу.'),
            ('Что лучше для бассейна — жёсткая или эластичная гидроизоляция?',
             'Жёсткая обмазочная КТ ТРОН-7 — для стабильных конструкций. Если возможны подвижки и микротрещины, выбирают эластичную КТ ТРОН-10 1К или 2К. Подскажем по фото.'),
            ('Чем клеить плитку в бассейне?',
             'Эластичным клеем КТ ТРОН-101 — по описанию завода он применяется в том числе для облицовки бассейнов.'),
        ],
        'related': ['/gidroizolyaciya/fundamenta/', '/gidroizolyaciya/podvala/', '/remont-betona/'],
    },
    {
        'url': '/remont-betona/',
        'h1': 'Ремонт бетона в Алматы',
        'title': 'Ремонт бетона в Алматы — ремонтные составы КТ ТРОН-3, КТ ТРОН-4, цены, расход',
        'description': 'Составы для ремонта бетона и железобетона в Алматы: тиксотропные и литьевые КТ ТРОН-3, быстротвердеющие КТ ТРОН-4, КТ ТРОН-6, праймер для арматуры. Цены от, расчёт расхода.',
        'eyebrow': 'Ремонт бетона',
        'image': '/images/objects/o016.jpg',
        'lead': ('Сколы, разрушенный защитный слой, оголённая арматура, раковины и трещины — для каждой задачи у завода '
                 'КТ ТРОН свой состав. Тиксотропные наносят на стены и потолки, литьевые заливают в опалубку, '
                 'быстротвердеющие — когда конструкцию нужно быстро вернуть в работу.'),
        'materials': [
            ('КТ ТРОН-3', 'Тиксотропный состав для конструкционного ремонта балок, колонн, плит, стеновых панелей.'),
            ('КТ ТРОН-3 Т400', 'Безусадочный быстротвердеющий тиксотропный состав, ремонт локальных дефектов, слой 3–30 мм.'),
            ('КТ ТРОН-3 Л400', 'Литьевой безусадочный состав для ремонта заливкой в опалубку.'),
            ('КТ ТРОН-4 Т600', 'Быстротвердеющий тиксотропный состав для ускоренного ремонта.'),
            ('КТ ТРОН-6', 'Штукатурная смесь для неконструкционного ремонта: восстановление защитного слоя, выравнивание.'),
            ('КТ ТРОН-праймер', 'Защита стальной арматуры перед ремонтом и грунтование оснований.'),
        ],
        'examples': [
            Example(what='Ремонт 10 м² поверхности слоем 20 мм', name='КТ ТРОН-3 Т400', norm=(1850, 1850), area=10, thick=20, scale=0.001),
            Example(what='Восстановление защитного слоя 30 м² толщиной 10 мм', name='КТ ТРОН-6', norm=(1750, 1750), area=30, thick=10, scale=0.001),
        ],
        'steps': [
            'Пришлите фото дефекта: какая конструкция, глубина разрушения, видна ли арматура — подберём состав.',
            'Удалите слабый и разрушенный бетон до прочного основания, очистите арматуру от ржавчины.',
            'Обработайте арматуру КТ ТРОН-праймером.',
            'Восстановите бетон ремонтным составом — тиксотропным на вертикали и потолке или литьевым в опалубку — по техническому описанию завода.',
        ],
        'faq': [
            ('Чем тиксотропный состав отличается от литьевого?',
             'Тиксотропный не стекает — его наносят на стены и потолки шпателем или механизированно. Литьевой текучий — его заливают в опалубку и полости.'),
            ('Что выбрать, если конструкцию нужно быстро вернуть в работу?',
             'Быстротвердеющие составы серии КТ ТРОН-4 (Т600 — тиксотропный, Л600 — литьевой) и КТ ТРОН-3 Т400.'),
            ('Сколько нужно состава на ремонт?',
             'Расход ремонтных составов указан на 1 м³ раствора: умножьте площадь на толщину слоя. Удобнее посчитать в калькуляторе расхода.'),
        ],
        'related': ['/gidroizolyaciya/fundamenta/', '/gidroizolyaciya/podvala/', '/gidroizolyaciya/basseyna/'],
    },
]

TITLES = {p['url']: p['h1'] for p in PAGES}


def build(page, head, tail, products, prices):
    by_name = {p['name']: p for p in products}
    pack_of = {p['name']: float(re.search(r'[\d,]+', p['pack']).group(0).replace(',', '.')) if re.search(r'\d', p['pack']) else 25
               for p in products}
    url = page['url']

    h = head
    h = re.sub(r'<title>.*?</title>', f'<title>{e(page["title"])}</title>', h, flags=re.S)
    h = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{e(page["description"])}"', h)
    h = re.sub(r'<meta property="og:url" content="[^"]*"', f'<meta property="og:url" content="{SITE}{url}"', h)
    h = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{e(page["title"])}"', h)
    h = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{e(page["description"])}"', h)
    h = re.sub(r'<meta property="og:image" content="[^"]*"', f'<meta property="og:image" content="{SITE}{page["image"]}"', h)
    h = re.sub(r'<link rel="canonical" href="[^"]*"', f'<link rel="canonical" href="{SITE}{url}"', h)
    crumbs = [{'@type': 'ListItem', 'position': 1, 'name': 'Главная', 'item': SITE + '/'}]
    if url.startswith('/gidroizolyaciya/'):
        crumbs.append({'@type': 'ListItem', 'position': 2, 'name': 'Гидроизоляция', 'item': SITE + '/gidroizolyaciya/'})
    crumbs.append({'@type': 'ListItem', 'position': len(crumbs) + 1, 'name': page['h1'], 'item': SITE + url})
    ld = [
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': crumbs},
        {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in page['faq']]},
    ]
    blocks = '\n'.join('<script type="application/ld+json">\n' + json.dumps(d, ensure_ascii=False, indent=2).replace('</', '<\\/') + '\n</script>' for d in ld)
    h = re.sub(LD_BLOCKS, lambda m: blocks, h, count=1, flags=re.S)

    cards = []
    for name, why in page['materials']:
        p = by_name[name]
        price, unit = price_info(prices, name)
        price_html = f'от {fmt_price(price)} ₸ за 1 {unit}' if price else 'Цена по запросу'
        cards.append(f'<a class="mat-card" href="{p["url"]}"><img src="{p["image"]}" alt="{e(name)}" loading="lazy" width="160" height="140" />'
                     f'<b>{e(name)}</b><span>{e(why)}</span><em>{e(price_html)}</em></a>')
    examples = ''.join(f'<li>{example_text(ex, prices, pack_of)}</li>' for ex in page['examples'])
    steps = ''.join(f'<li>{e(s)}</li>' for s in page['steps'])
    faq = ''.join(f'<details class="faq"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in page['faq'])
    related = ''.join(f'<a href="{u}">{e(TITLES.get(u, ""))}</a>' for u in page['related'])
    wa = quote(f'Здравствуйте! Нужна консультация: {page["h1"].lower()}. Пришлю фото объекта.')
    crumbs_html = '<a href="/">Главная</a> / ' + ('<a href="/gidroizolyaciya/">Гидроизоляция</a> / ' if url.startswith('/gidroizolyaciya/') else '') + e(page['h1'])

    main = f'''    <main id="top">
      <section class="section material-page">
        <div class="shell">
          <nav class="crumbs" aria-label="Хлебные крошки">{crumbs_html}</nav>
          <div class="material-layout">
            <img src="{page['image']}" alt="{e(page['h1'])}" width="640" height="480" />
            <div>
              <p class="eyebrow">{e(page['eyebrow'])} · консультации и поставка под заказ в Алматы</p>
              <h1>{e(page['h1'])}</h1>
              <p>{e(page['lead'])}</p>
              <div class="hero-cta">
                <a class="btn btn-solid btn-lg" href="https://wa.me/{WA}?text={wa}" target="_blank" rel="noopener">Подобрать материал по фото</a>
                <a class="btn btn-ghost-dark btn-lg" href="/calculator/">Рассчитать расход</a>
              </div>
            </div>
          </div>
          <h2>Материалы КТ ТРОН для этой задачи</h2>
          <div class="mat-grid">{''.join(cards)}</div>
          <h2>Пример расчёта</h2>
          <ul class="calc-examples">{examples}</ul>
          <p class="muted">По нормам расхода завода и ценам «от» без учёта доставки. Точное количество и цену подскажем по вашему объекту.</p>
          <h2>Как сделать</h2>
          <ol class="steps">{steps}</ol>
          <p class="muted">Работы выполняйте по техническому описанию завода к каждому материалу — оно есть на странице материала.</p>
          <h2>Вопросы и ответы</h2>
          {faq}
          <h2>Консультации и поставка под заказ в Алматы</h2>
          <p>ТОО DARHAN — официальный дистрибьютор завода КТ ТРОН (КТтрон) в Казахстане. Офис и консультации: Алматы, ул. Шевченко 118, офис 221, доставка по Казахстану. Телефон и WhatsApp: <a href="tel:+77751810595">+7 775 181-05-95</a>.</p>
          <h2>Смотрите также</h2>
          <div class="related">{related}<a href="/materials/">Все материалы КТ ТРОН</a></div>
        </div>
      </section>
    </main>
'''
    return h + main + tail


# Таблица «Цены на гидроизоляцию за 1 м²» на /gidroizolyaciya/: материал, тип, кг на 1 м² (мин.–макс.),
# слой, мм (для составов, расход которых указан на 1 мм). Нормы — из технических описаний завода (specs.json).
GIDRO_TABLE = [
    ('КТ ТРОН-1', 'проникающая', (0.8, 1.2), None),
    ('КТ ТРОН-11', 'проникающая, для старого бетона', (0.8, 1.2), None),
    ('КТ ТРОН-7', 'жёсткая обмазочная', (1.55, 1.55), 2),
    ('КТ ТРОН-71', 'жёсткая обмазочная', (1.55, 1.55), 2),
    ('КТ ТРОН-10 1К', 'эластичная', (1.5, 1.5), 2),
    ('КТ ТРОН-10 2К', 'эластичная двухкомпонентная', (2.0, 2.0), 2),
    ('КТ ТРОН-122 флекс', 'эластичная двухкомпонентная', (2.0, 2.0), 2),
]
GIDRO_START, GIDRO_END = '      <!-- gidro-prices -->\n', '      <!-- /gidro-prices -->\n'
GIDRO_COST_Q = 'Сколько стоит гидроизоляция в Алматы?'


def gidro_section(prices):
    rows, costs = [], []
    pages = json.loads((ROOT / 'pages.json').read_text(encoding='utf-8'))
    for name, kind, (lo, hi), thick in GIDRO_TABLE:
        price, unit = price_info(prices, name)
        k = thick or 1
        kg = f'{fmt_num(lo * k)}–{fmt_num(hi * k)}' if lo != hi else fmt_num(lo * k)
        layer = f' (слой {thick} мм)' if thick else ''
        cost = round_half_up(lo * k * price) if price and unit == 'кг' else None
        if cost:
            costs.append(cost)
        rows.append(f'              <tr><td><a href="{pages[name]}">{e(name)}</a></td><td data-label="Вид">{kind}</td>'
                    f'<td data-label="Расход на 1 м²">{kg} кг{layer}</td><td data-label="Цена от, ₸/кг">{fmt_price(price) if price else "по запросу"}</td>'
                    f'<td data-label="Материал на 1 м²">{"от " + fmt_price(cost) + " ₸" if cost else "по запросу"}</td></tr>')
    html = f'''{GIDRO_START}      <section class="section" id="ceny">
        <div class="shell">
          <div class="section-head">
            <p class="eyebrow">Цены</p>
            <h2>Цены на гидроизоляцию в Алматы за 1 м²</h2>
          </div>
          <p class="muted gidro-text">Сколько стоит материал на 1 м²: расход по техническим описаниям завода КТ ТРОН, цены «от» по прайсу завода для Казахстана, без учёта доставки и работ. Точное количество зависит от состояния основания — посчитаем по вашему объекту.</p>
          <div class="gidro-table-wrap">
            <table class="gidro-table">
              <thead><tr><th>Материал</th><th>Вид гидроизоляции</th><th>Расход на 1 м²</th><th>Цена от, ₸/кг</th><th>Материал на 1 м²</th></tr></thead>
              <tbody>
{chr(10).join(rows)}
              </tbody>
            </table>
          </div>
          <p class="gidro-links"><a href="/calculator/">Рассчитать расход на вашу площадь</a> · <a href="https://wa.me/77751810595" target="_blank" rel="noopener">Узнать цену с доставкой в WhatsApp</a></p>

          <div class="gidro-types">
            <h3>Какая бывает гидроизоляция бетона</h3>
            <p><strong>Проникающая</strong> (<a href="{pages['КТ ТРОН-1']}">КТ ТРОН-1</a>, <a href="{pages['КТ ТРОН-11']}">КТ ТРОН-11</a>) наносится на влажный бетон и, по данным завода, повышает его марку по водонепроницаемости на 2–3 ступени и морозостойкость. Применяется для фундаментов, подвалов и подземных частей зданий, резервуаров (в том числе с питьевой водой), бассейнов и очистных сооружений. Паропроницаема. Расход — 0,8–1,2 кг на 1 м².</p>
            <p><strong>Жёсткая обмазочная</strong> (<a href="{pages['КТ ТРОН-7']}">КТ ТРОН-7</a>, <a href="{pages['КТ ТРОН-71']}">КТ ТРОН-71</a>) — слой 2–4 мм. Держит воду и на прижим (W10), и на отрыв (W8). Защищает конструкции от грунтовых вод, применяется для бассейнов, резервуаров и ёмкостей, в том числе с питьевой водой. Расход — 1,55 кг на 1 м² на каждый миллиметр.</p>
            <p><strong>Эластичная</strong> (<a href="{pages['КТ ТРОН-10 1К']}">КТ ТРОН-10 1К</a>, <a href="{pages['КТ ТРОН-10 2К']}">КТ ТРОН-10 2К</a>, <a href="{pages['КТ ТРОН-122 флекс']}">КТ ТРОН-122 флекс</a>) — для конструкций, где возможны микротрещины и небольшие деформации: бассейны, резервуары, внешняя и внутренняя гидроизоляция подземных частей зданий, надземные конструкции под атмосферным воздействием. КТ ТРОН-10 1К перекрывает трещины до 1 мм, двухкомпонентные составы дают водонепроницаемость до W16.</p>
            <p><strong>Швы и протечки.</strong> Активную воду останавливают быстротвердеющим <a href="{pages['КТ ТРОН-8']}">КТ ТРОН-8</a>, швы и вводы коммуникаций герметизируют <a href="{pages['КТ ТРОН-2']}">КТ ТРОН-2</a> и <a href="{pages['Гидрошнур НП']}">гидрошнуром НП</a> — до нанесения основной гидроизоляции.</p>
            <h3>Где купить гидроизоляцию в Алматы</h3>
            <p>Все материалы — под заказ у официального дистрибьютора завода КТ ТРОН в Алматы, ул. Шевченко, 118, офис 221. Пришлите фото объекта или размеры в WhatsApp <a href="https://wa.me/77751810595" target="_blank" rel="noopener">+7 775 181-05-95</a> — подберём систему материалов, посчитаем количество и назовём цену с доставкой по Алматы или в другой город Казахстана.</p>
          </div>
        </div>
      </section>
{GIDRO_END}'''
    answer = (f'Материал для гидроизоляции 1 м² стоит от {fmt_price(min(costs))} ₸ (проникающая КТ ТРОН-1) '
              f'до {fmt_price(max(costs))} ₸ (эластичная двухкомпонентная, слой 2 мм) — без учёта доставки и работ. '
              'Точная цена зависит от площади, состояния основания и выбранной системы. Пришлите фото объекта в WhatsApp — подберём материал и рассчитаем расход.')
    return html, answer


def patch_gidro(prices):
    path = ROOT / 'gidroizolyaciya/index.html'
    s = path.read_text(encoding='utf-8')
    html, answer = gidro_section(prices)
    if GIDRO_START in s:
        s = s[:s.index(GIDRO_START)] + html + s[s.index(GIDRO_END) + len(GIDRO_END):]
    else:
        anchor = '      <section class="section why">'
        s = s.replace(anchor, html + '\n' + anchor, 1)
    css = ('      .gidro-table-wrap{overflow-x:auto;margin:1rem 0}\n'
           '      .gidro-table{width:100%;min-width:640px;border-collapse:collapse;font-size:.92rem;background:#fff}\n'
           '      .gidro-table th,.gidro-table td{padding:.6rem .7rem;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}\n'
           '      .gidro-table th{background:var(--paper);font-size:.85rem}\n'
           '      .gidro-table td:last-child{font-weight:700;color:var(--brand-deep);white-space:nowrap}\n'
           '      .gidro-text,.gidro-types p{max-width:860px}.gidro-types{margin-top:2rem}.gidro-types h3{margin:1.4rem 0 .5rem}\n'
           '      #ceny a{color:var(--brand-deep);text-decoration:underline;text-underline-offset:2px}.gidro-table td:first-child a{font-weight:700}\n'
           '      @media (max-width:640px){.gidro-table{min-width:0}.gidro-table thead{display:none}.gidro-table tr{display:block;padding:.6rem 0;border-bottom:1px solid var(--line)}'
           '.gidro-table td{display:flex;justify-content:space-between;gap:12px;padding:.2rem .2rem;border:0}.gidro-table td[data-label]::before{content:attr(data-label);color:var(--muted);font-weight:400}'
           '.gidro-table td:last-child{white-space:normal}}\n')
    # Стили таблицы: убираем прежние и вставляем текущие
    s = re.sub(r'      \.gidro-table-wrap\{.*?(?=      /\* КТ ТРОН-8)', '', s, count=1, flags=re.S)
    s = s.replace('      a.sol{text-decoration:none;display:block}\n', '      a.sol{text-decoration:none;display:block}\n' + css, 1)
    # Ответ «Сколько стоит гидроизоляция в Алматы?» — с цифрами, и в разметке FAQPage, и на странице
    s = re.sub(r'("name": "' + re.escape(GIDRO_COST_Q) + r'",\s*"acceptedAnswer": \{\s*"@type": "Answer",\s*"text": ")[^"]*(")',
               lambda m: m.group(1) + answer + m.group(2), s, count=1)
    s = re.sub(r'(<h3[^>]*>' + re.escape(GIDRO_COST_Q) + r'</h3>\s*<p class="muted">)[^<]*(</p>)',
               lambda m: m.group(1) + answer + m.group(2), s, count=1)
    path.write_text(s, encoding='utf-8')


# Калькулятор: под формой — как считать, таблица норм (из списка materials в самой странице), примеры и вопросы
CALC_START, CALC_END = '      <!-- calc-guide -->\n', '      <!-- /calc-guide -->\n'
CALC_LD_START, CALC_LD_END = '    <!-- calc-ld -->\n', '    <!-- /calc-ld -->\n'
CALC_TITLE = 'Калькулятор расхода КТ ТРОН (КТтрон): гидроизоляция и ремонт бетона на 1 м² — Алматы'
CALC_DESC = ('Расход гидроизоляции и ремонтных составов КТ ТРОН на 1 м² по нормам завода: КТ ТРОН-1, 7, 10, '
             'КТ ТРОН-3, 4, подливочные, швы. Мешки и ориентировочная цена, поставка под заказ в Алматы.')
CALC_EXAMPLES = [
    Example(what='Проникающая гидроизоляция 100 м² подвала', name='КТ ТРОН-1', norm=(0.8, 1.2), area=100, pack_word='вед.'),
    Example(what='Обмазочная гидроизоляция 50 м² слоем 2 мм', name='КТ ТРОН-7', norm=(1.55, 1.55), area=50, thick=2),
    Example(what='Ремонт 10 м² бетона слоем 20 мм', name='КТ ТРОН-3 Т400', norm=(1850, 1850), area=10, thick=20, scale=0.001),
    Example(what='Зачеканка 20 м шва сечением 30×30 мм', name='КТ ТРОН-2', norm=(1750, 1750), area=20, thick=1, scale=0.03 * 0.03),
]
CALC_FAQ = [
    ('Как посчитать расход гидроизоляции на 1 м²?',
     'У проникающих составов норма дана на 1 м²: КТ ТРОН-1 и КТ ТРОН-11 — 0,8–1,2 кг/м². У обмазочных и эластичных — на 1 мм слоя: '
     'КТ ТРОН-7 — 1,55 кг/м², КТ ТРОН-10 1К — 1,5 кг/м² на каждый миллиметр. Умножьте площадь на норму, а для обмазочных ещё и на толщину слоя (обычно 2–4 мм).'),
    ('Сколько ремонтного состава нужно на 1 м²?',
     'Норма ремонтных составов указана на 1 м³ раствора, например 1850 кг для КТ ТРОН-3 Т400. На 1 м² при слое 1 мм это 1,85 кг, '
     'при слое 20 мм — 37 кг. Формула: площадь, м² × толщина, мм × норма ÷ 1000.'),
    ('Почему калькулятор считает с запасом?',
     'Материал продают целыми мешками, поэтому результат округляется вверх. Реальный расход зависит от ровности и впитываемости основания, '
     'поэтому для точного количества пришлите фото объекта в WhatsApp. Цена указана ориентировочно, без доставки.'),
]


def fmt_num2(x):
    return (f'{x:.2f}'.rstrip('0').rstrip('.')).replace('.', ',')


def calc_norm_text(m):
    lo, hi = m['min'], m['max']
    val = fmt_num2(lo) if lo == hi else f'{fmt_num2(lo)}–{fmt_num2(hi)}'
    if m['mode'] == 'area':
        return f'{val} кг/м²'
    if m['mode'] == 'mm':
        return f'{val} кг/м² на 1 мм' + (' сухой смеси' if m.get('kit') else '')
    t = m.get('thick')
    t_s = fmt_num2(t)
    if m['mode'] == 'seam':
        per_m = lo * (t / 1000) ** 2
        return f'{fmt_price(lo)} кг/м³; шов {t_s}×{t_s} мм — {fmt_num2(per_m)} кг на 1 м'
    per_m2 = lo * t / 1000
    return f'{fmt_price(lo)} кг/м³; слой {t_s} мм — {fmt_num2(per_m2)} кг/м²'


def calc_materials(s):
    js = s[s.index('const materials = ['):s.index('];', s.index('const materials = ['))]
    out = []
    for row in re.findall(r'\{[^{}]*\}', js):
        m = {k: v for k, v in re.findall(r'(\w+): "([^"]*)"', row)}
        m.update({k: float(v) for k, v in re.findall(r'(\w+): ([\d.]+)', row)})
        out.append(m)
    return out


def patch_calculator(prices, pack_of):
    path = ROOT / 'calculator/index.html'
    s = path.read_text(encoding='utf-8')
    pages = json.loads((ROOT / 'pages.json').read_text(encoding='utf-8'))
    rows, group = [], None
    for m in calc_materials(s):
        if m['group'] != group:
            group = m['group']
            rows.append(f'              <tr class="calc-group"><th colspan="3">{e(group)}</th></tr>')
        price, unit = price_info(prices, m['name'])
        p = f'{fmt_price(price)}' if price and unit == 'кг' else 'по запросу'
        rows.append(f'              <tr><td><a href="{pages[m["name"]]}">{e(m["name"])}</a></td>'
                    f'<td data-label="Норма">{calc_norm_text(m)}</td><td data-label="Цена от, ₸/кг">{p}</td></tr>')
    examples = '\n'.join(f'            <li>{example_text(ex, prices, pack_of)}</li>' for ex in CALC_EXAMPLES)
    faq = '\n'.join(f'          <details class="faq"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in CALC_FAQ)
    guide = f'''{CALC_START}      <section class="section" id="kak-schitat">
        <div class="shell calc-guide">
          <h2>Как рассчитать расход материалов КТ ТРОН</h2>
          <p>Нормы расхода взяты из технических описаний завода. Они указаны по-разному, и калькулятор выше учитывает это сам:</p>
          <ul>
            <li><strong>На 1 м²</strong> — проникающая гидроизоляция (КТ ТРОН-1, КТ ТРОН-11) и плиточный клей КТ ТРОН-101: килограммы = площадь × норма.</li>
            <li><strong>На 1 м² на каждый 1 мм слоя</strong> — обмазочная и эластичная гидроизоляция (КТ ТРОН-7, 71, 10, 122 флекс), праймер: килограммы = площадь × толщина × норма.</li>
            <li><strong>На 1 м³ раствора</strong> — ремонтные, торкрет- и подливочные составы: килограммы = площадь, м² × толщина, мм × норма ÷ 1000.</li>
            <li><strong>Швы</strong> (КТ ТРОН-2, WX-32T): килограммы = длина шва × ширина × глубина × норма на 1 м³.</li>
          </ul>
          <h3>Примеры расчёта</h3>
          <ul class="calc-examples">
{examples}
          </ul>
          <p class="muted">Цены «от» по прайсу завода для Казахстана, без доставки. Количество округлено до целых мешков.</p>
          <h3>Нормы расхода материалов КТ ТРОН</h3>
          <div class="calc-table-wrap">
            <table class="calc-table">
              <thead><tr><th>Материал</th><th>Норма расхода</th><th>Цена от, ₸/кг</th></tr></thead>
              <tbody>
{chr(10).join(rows)}
              </tbody>
            </table>
          </div>
          <h3>Частые вопросы</h3>
{faq}
          <p class="gidro-links">Подробнее о материалах: <a href="/gidroizolyaciya/">гидроизоляция в Алматы</a> · <a href="/remont-betona/">ремонт бетона</a> · <a href="/materials/">все материалы</a></p>
        </div>
      </section>
{CALC_END}'''
    if CALC_START in s:
        s = s[:s.index(CALC_START)] + guide + s[s.index(CALC_END) + len(CALC_END):]
    else:
        s = s.replace('    </main>', guide + '    </main>', 1)
    ld = [
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Главная', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Калькулятор расхода', 'item': SITE + '/calculator/'}]},
        {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in CALC_FAQ]},
    ]
    blocks = CALC_LD_START + '\n'.join(
        '    <script type="application/ld+json">\n' + json.dumps(d, ensure_ascii=False, indent=2).replace('</', '<\\/') + '\n    </script>'
        for d in ld) + '\n' + CALC_LD_END
    css = ('    <style>.calc-guide>p,.calc-guide li{max-width:860px}.calc-guide h3{margin:1.6rem 0 .6rem}'
           '.calc-table-wrap{overflow-x:auto}.calc-table{width:100%;border-collapse:collapse;font-size:.92rem;background:#fff}'
           '.calc-table th,.calc-table td{padding:.5rem .7rem;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}'
           '.calc-table thead th{background:var(--paper);font-size:.85rem}.calc-table .calc-group th{background:var(--brand-soft,#e5f5fc);color:var(--brand-deep)}'
           '.calc-table td:last-child{white-space:nowrap;font-weight:700;color:var(--brand-deep)}'
           '#kak-schitat a{color:var(--brand-deep);text-decoration:underline}'
           '.faq{border-bottom:1px solid var(--line);padding:.7rem 0;max-width:860px}.faq summary{font-weight:700;cursor:pointer}.faq p{margin:.5rem 0 0;color:var(--muted)}'
           '@media (max-width:640px){.calc-table thead{display:none}.calc-table tr{display:block;padding:.5rem 0;border-bottom:1px solid var(--line)}'
           '.calc-table td,.calc-table th{display:flex;justify-content:space-between;gap:12px;border:0;padding:.2rem}'
           '.calc-table td[data-label]::before{content:attr(data-label);color:var(--muted)}.calc-table td:last-child{white-space:normal}}</style>\n')
    blocks = blocks[:-len(CALC_LD_END)] + css + CALC_LD_END
    if CALC_LD_START in s:
        s = s[:s.index(CALC_LD_START)] + blocks + s[s.index(CALC_LD_END) + len(CALC_LD_END):]
    else:
        s = s.replace('  </head>', blocks + '  </head>', 1)
    s = re.sub(r'<title>.*?</title>', f'<title>{e(CALC_TITLE)}</title>', s, count=1, flags=re.S)
    s = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{e(CALC_DESC)}"', s, count=1)
    s = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{e(CALC_TITLE)}"', s, count=1)
    path.write_text(s, encoding='utf-8')


def main():
    template = (ROOT / 'materials/kt-tron-3/index.html').read_text(encoding='utf-8')
    head = template[:template.index('    <main id="top">')]
    tail = template[template.rindex('</main>') + len('</main>\n'):]
    head = head.replace('  </head>', (
        '    <style>.mat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;margin:0 0 1.6rem}'
        '.mat-card{display:grid;gap:4px;padding:12px;border:1px solid var(--line);border-radius:var(--radius);background:#fff;text-decoration:none;color:var(--ink)}'
        '.mat-card:hover{border-color:var(--brand)}.mat-card img{width:100%;height:140px;object-fit:contain;background:var(--paper);border-radius:10px}'
        '.mat-card span{color:var(--muted);font-size:.85rem}.mat-card em{font-style:normal;font-weight:700;color:var(--brand-deep)}'
        '.material-layout>img{object-fit:cover}.calc-examples li,.steps li{margin:.35rem 0;max-width:860px}'
        '.faq{border-bottom:1px solid var(--line);padding:.7rem 0;max-width:860px}.faq summary{font-weight:700;cursor:pointer}.faq p{margin:.5rem 0 0;color:var(--muted)}</style>\n'
        '  </head>'), 1)
    products = load_products()
    prices = json.loads((ROOT / 'prices.json').read_text(encoding='utf-8'))
    today = date.today().isoformat()
    sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    for page in PAGES:
        out = ROOT / page['url'].strip('/') / 'index.html'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build(page, head, tail, products, prices), encoding='utf-8')
        loc = SITE + page['url']
        if f'<loc>{loc}</loc>' not in sitemap:
            sitemap = sitemap.replace('</urlset>', f'  <url><loc>{loc}</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.9</priority></url>\n</urlset>')
    (ROOT / 'sitemap.xml').write_text(sitemap, encoding='utf-8')
    patch_gidro(prices)
    pack_of = {p['name']: float(re.search(r'[\d,]+', p['pack']).group(0).replace(',', '.')) if re.search(r'\d', p['pack']) else 25
               for p in products}
    patch_calculator(prices, pack_of)
    print(f'страниц собрано: {len(PAGES)}, таблица цен на /gidroizolyaciya/ и справка калькулятора обновлены')


if __name__ == '__main__':
    main()
