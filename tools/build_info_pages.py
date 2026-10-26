#!/usr/bin/env python3
"""Собирает страницы «О компании» (/o-kompanii/), «Контакты» (/kontakty/), «Документы» (/dokumenty/),
«Реквизиты и условия» (/rekvizity/) и «Политика конфиденциальности» (/politika-konfidencialnosti/)
и ставит ссылки на них в подвал всех страниц сайта.

Документы (сертификаты и технические описания завода) лежат в /dokumenty/, их список — tools/dokumenty.json.
На страницы товаров, для которых есть техописание, ставится кнопка «Техническое описание (PDF)».

Шапка и подвал — со страницы-образца materials/kt-tron-3/, как у остальных генераторов.
Реквизиты и условия — в списках ниже; после правки перезапустите.

Запуск из корня репозитория:  python3 tools/build_info_pages.py
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_product_pages import LD_BLOCKS, ROOT, SITE, e  # noqa: E402

REQUISITES = [
    ('Полное наименование', 'Товарищество с ограниченной ответственностью «DARHAN» (ТОО «DARHAN»)'),
    ('БИН', '990240010117'),
    ('Юридический адрес', 'Республика Казахстан, 050000, г. Алматы, Алмалинский район, пр. Сейфуллина, 534/92, офис 101'),
    ('Офис', 'г. Алматы, ул. Шевченко 118, офис 221, БЦ «Алтын Гасыр»'),
    ('Телефон, WhatsApp', '<a href="tel:+77751810595">+7 775 181-05-95</a>'),
    ('E-mail', '<a href="mailto:info@kttron.kz">info@kttron.kz</a>'),
    ('Режим работы', 'понедельник — пятница, 10:00–17:00'),
    ('Статус', 'официальный дистрибьютор завода КТ ТРОН (КТтрон) в Казахстане — '
               '<a href="/images/sertifikat-distributor.jpg" target="_blank" rel="noopener">сертификат дистрибьютора</a>'),
]

TERMS = [
    ('Как заказать', 'Соберите заявку на сайте (кнопка «В заявку») или напишите в WhatsApp. Менеджер уточнит объект, '
                     'подберёт материалы, подтвердит цену и срок поставки.'),
    ('Поставка под заказ', 'Материалы поставляются под заказ. Срок поставки менеджер сообщает при подтверждении заказа.'),
    ('Цены', 'На сайте — цены «от» за 1 кг по прайсу завода для Казахстана, без учёта доставки. '
             'Окончательная цена — в счёте.'),
    ('Оплата', 'По счёту, который менеджер присылает после подтверждения заказа. Оплата на сайте не принимается.'),
    ('Доставка', 'Стоимость и сроки доставки по Алматы и в другие города Казахстана рассчитываются под объём заказа.'),
    ('Кэшбэк', 'Баллы за заказы начисляются в личном кабинете по <a href="/account/rules.php">правилам программы</a>.'),
    ('Документы', 'Сертификаты и технические описания материалов — на странице <a href="/dokumenty/">«Документы»</a>, '
                  'протоколы испытаний — по запросу в WhatsApp или на e-mail.'),
    ('Возврат и обмен', 'По согласованию с менеджером в соответствии с законодательством Республики Казахстан.'),
]

POLICY_DATE = '24 октября 2026'
POLICY = [
    ('1. Кто обрабатывает данные',
     '<p>Персональные данные обрабатывает ТОО «DARHAN» (БИН 990240010117), г. Алматы, ул. Шевченко 118, офис 221 — '
     'официальный дистрибьютор завода КТ ТРОН в Казахстане (далее — «мы»). Политика действует для сайта kttron.kz, '
     'личного кабинета и мобильного приложения КТ ТРОН. Мы руководствуемся Законом Республики Казахстан '
     '«О персональных данных и их защите».</p>'),
    ('2. Какие данные мы получаем',
     '<ul><li><b>Заявка и сообщение в WhatsApp</b> — имя, номер телефона, список материалов, комментарий '
     '(объект, объём, сроки).</li>'
     '<li><b>Личный кабинет и приложение</b> — имя, номер телефона, пароль (хранится только в зашифрованном виде, '
     'мы его не видим), история заявок и оплат, баллы кэшбэка, дата согласия с этой политикой.</li>'
     '<li><b>Безопасность входа</b> — IP-адрес и время попыток входа, чтобы защищать кабинет от подбора пароля.</li>'
     '<li><b>Статистика сайта</b> — данные Яндекс.Метрики: файлы cookie, IP-адрес, сведения о браузере и устройстве, '
     'просмотренные страницы и действия на них (включая запись сеансов — Вебвизор).</li></ul>'),
    ('3. Зачем',
     '<ul><li>ответить на заявку, подобрать материалы и рассчитать расход;</li>'
     '<li>оформить и исполнить заказ, выставить счёт, организовать доставку;</li>'
     '<li>вести личный кабинет и программу кэшбэка;</li>'
     '<li>улучшать сайт и понимать, какие страницы полезны.</li></ul>'),
    ('4. Основания',
     '<p>Ваше согласие — вы даёте его, отправляя заявку, сообщение или регистрируясь в кабинете, — '
     'а также заключение и исполнение договора поставки.</p>'),
    ('5. Кому передаём',
     '<p>Мы не продаём и не передаём данные третьим лицам, кроме случаев, когда это нужно для работы сервиса или '
     'требует закон:</p><ul><li>WhatsApp — когда вы сами отправляете нам сообщение;</li>'
     '<li>Яндекс.Метрика — обезличенная статистика посещений;</li>'
     '<li>перевозчик — адрес и телефон получателя, если вы заказали доставку;</li>'
     '<li>государственные органы — по законному запросу.</li></ul>'),
    ('6. Где и сколько храним',
     '<p>Данные кабинета хранятся на сервере хостинг-провайдера. Храним их, пока действует ваш аккаунт или '
     'пока они нужны для целей из раздела 3, а также в сроки, установленные законодательством '
     '(например, для бухгалтерских документов).</p>'),
    ('7. Как защищаем',
     '<p>Сайт работает только по защищённому протоколу HTTPS, пароли хранятся в зашифрованном виде, доступ к '
     'данным есть только у сотрудников, которые обрабатывают заказы.</p>'),
    ('8. Cookie и данные в браузере',
     '<p>Сайт использует cookie Яндекс.Метрики, а список заявки хранит в памяти вашего браузера, чтобы он не пропадал '
     'при переходе между страницами. Cookie можно отключить в настройках браузера — сайт продолжит работать.</p>'),
    ('9. Ваши права',
     '<p>Вы можете узнать, какие данные о вас хранятся, исправить их, отозвать согласие или попросить удалить аккаунт. '
     'Напишите на <a href="mailto:info@kttron.kz">info@kttron.kz</a> или в WhatsApp '
     '<a href="https://wa.me/77751810595">+7 775 181-05-95</a> — ответим в течение 10 рабочих дней.</p>'),
    ('10. Изменения',
     f'<p>Мы можем обновлять эту политику; новая редакция действует с момента публикации на этой странице. '
     f'Редакция от {POLICY_DATE}.</p>'),
]

CERT_CARD = (
    '          <div class="cert-card">\n'
    '            <a class="cert-img" href="/images/sertifikat-distributor.jpg" target="_blank" rel="noopener">'
    '<img src="/images/sertifikat-distributor-640.jpg" width="640" height="453" loading="lazy" '
    'alt="Сертификат официального дистрибьютора завода КТ ТРОН, выданный ТОО DARHAN, действует до 31 декабря 2026 года" /></a>\n'
    '            <div><h3>Сертификат официального дистрибьютора</h3>'
    '<p>ТОО DARHAN является официальным дистрибьютором завода КТ ТРОН и имеет право реализации продукции марки КТ ТРОН в Казахстане.</p>'
    '<p class="cert-valid">Срок действия: до 31 декабря 2026 года</p>'
    '<p><a class="cert-open" href="/images/sertifikat-distributor.jpg" target="_blank" rel="noopener">Открыть сертификат полностью</a></p></div>\n'
    '          </div>\n')

ABOUT = f'''          <p class="lead">ТОО «DARHAN» — официальный дистрибьютор завода КТ ТРОН (КТтрон) в Казахстане. Поставляем материалы
          для ремонта, гидроизоляции и защиты бетонных и железобетонных конструкций и помогаем подобрать их под конкретный объект.</p>
{CERT_CARD}          <h2>Что мы поставляем</h2>
          <ul>
            <li><a href="/gidroizolyaciya/">Гидроизоляция</a> — проникающая, обмазочная жёсткая и эластичная, остановка активных протечек;</li>
            <li><a href="/remont-betona/">Ремонт бетона</a> — тиксотропные и литьевые ремонтные составы, торкрет-смеси;</li>
            <li>подливочные составы для фундаментов под оборудование и анкеровки;</li>
            <li>материалы для инъектирования трещин и герметизации швов: гидрошнуры, гидроленты, герметики.</li>
          </ul>
          <p>Весь ассортимент — в <a href="/materials/">каталоге материалов</a>: более 50 позиций с ценами и характеристиками.</p>
          <h2>Как мы работаем</h2>
          <ol>
            <li><b>Консультация.</b> Пришлите фото дефекта или описание объекта в WhatsApp — подскажем, какая система материалов нужна.</li>
            <li><b>Расчёт.</b> Посчитаем расход под площадь и толщину слоя — можно и самостоятельно в <a href="/calculator/">калькуляторе</a>.</li>
            <li><b>Поставка под заказ.</b> Менеджер подтверждает цену и срок и присылает счёт; доставка по Алматы и Казахстану рассчитывается под объём.</li>
            <li><b>Документы.</b> Сертификаты и технические описания завода — на странице <a href="/dokumenty/">«Документы»</a>.</li>
          </ol>
          <h2>Объекты</h2>
          <p>Примеры объектов, где применялись материалы КТ ТРОН, — в разделе <a href="/objects/">«Объекты»</a>.</p>
          <h2>Реквизиты</h2>
          <p>ТОО «DARHAN», БИН 990240010117. Офис: г. Алматы, ул. Шевченко 118, офис 221, БЦ «Алтын Гасыр».
          Полные реквизиты и условия — на странице <a href="/rekvizity/">«Реквизиты и условия»</a>, телефоны и карта — в <a href="/kontakty/">«Контактах»</a>.</p>
'''

CONTACTS = [
    ('Адрес', 'г. Алматы, ул. Шевченко 118, офис 221, БЦ «Алтын Гасыр» — '
              '<a href="https://2gis.kz/almaty/firm/70000001037895624" target="_blank" rel="noopener">открыть в 2ГИС</a>'),
    ('Телефон', '<a href="tel:+77751810595">+7 775 181-05-95</a>'),
    ('WhatsApp', '<a href="https://wa.me/77751810595" target="_blank" rel="noopener">написать в WhatsApp</a> — обычно отвечаем в течение часа'),
    ('E-mail', '<a href="mailto:info@kttron.kz">info@kttron.kz</a>'),
    ('Режим работы', 'понедельник — пятница, 10:00–17:00'),
    ('Компания', 'ТОО «DARHAN», БИН 990240010117 — <a href="/rekvizity/">реквизиты и условия</a>'),
]
MAP = ('          <div class="map-wrap"><iframe title="КТ ТРОН Казахстан на карте" loading="lazy" '
       'referrerpolicy="no-referrer-when-downgrade" '
       'src="https://www.google.com/maps?q=%D0%90%D0%BB%D0%BC%D0%B0%D1%82%D1%8B,%20%D1%83%D0%BB.%20%D0%A8%D0%B5%D0%B2%D1%87%D0%B5%D0%BD%D0%BA%D0%BE%20118&output=embed">'
       '</iframe></div>\n')

DOCS = json.loads((ROOT / 'tools/dokumenty.json').read_text(encoding='utf-8'))
DOC_ANCHORS = {'Сертификаты и свидетельства': 'sertifikaty', 'Технические описания': 'tekhnicheskie-opisaniya',
               'Протоколы испытаний': 'protokoly'}


def file_label(path):
    p = ROOT / path.lstrip('/')
    kind = 'PDF' if path.endswith('.pdf') else 'JPG'
    return f'{kind}, {p.stat().st_size / 1048576:.1f} МБ'.replace('.', ',') if p.exists() else kind


def docs_body():
    out = ['          <p class="lead">Документы завода КТ ТРОН на материалы, которые мы поставляем: сертификаты соответствия, '
           'свидетельства о государственной регистрации и технические описания. Файлы открываются прямо на сайте.</p>\n',
           '          <p class="doc-toc">' + ' · '.join(f'<a href="#{a}">{e(t)}</a>' for t, a in DOC_ANCHORS.items()) + '</p>\n',
           '          <h2>Сертификат дистрибьютора</h2>\n', CERT_CARD]
    section = None
    for g in DOCS:
        if g['section'] != section:
            section = g['section']
            out.append(f'          <h2 id="{DOC_ANCHORS[section]}">{e(section)}</h2>\n')
            if section == 'Протоколы испытаний':
                out.append('          <p class="muted">Протоколы испытаний предоставляем по запросу — напишите в '
                           '<a href="https://wa.me/77751810595" target="_blank" rel="noopener">WhatsApp</a> или на '
                           '<a href="mailto:info@kttron.kz">info@kttron.kz</a>.</p>\n')
        items = ''.join(
            f'<li><a href="{it["file"]}" target="_blank">{e(it["title"])}</a> <span>{file_label(it["file"])}</span></li>'
            if it.get('file') else f'<li>{e(it["title"])}</li>' for it in g['items'])
        out.append(f'          <h3>{e(g["group"])}</h3>\n          <ul class="doc-list">{items}</ul>\n')
    return ''.join(out)


PAGES = [
    {
        'url': '/o-kompanii/',
        'h1': 'О компании КТ ТРОН Казахстан',
        'title': 'О компании — КТ ТРОН Казахстан, официальный дистрибьютор КТтрон (ТОО «DARHAN»)',
        'description': 'ТОО «DARHAN» — официальный дистрибьютор завода КТ ТРОН (КТтрон) в Казахстане: гидроизоляция, ремонт '
                       'и защита бетона, подбор материалов под объект, поставка под заказ в Алматы и по Казахстану.',
    },
    {
        'url': '/kontakty/',
        'h1': 'Контакты КТ ТРОН Казахстан',
        'title': 'Контакты КТ ТРОН (КТтрон) в Алматы — адрес, телефон, WhatsApp',
        'description': 'КТ ТРОН Казахстан в Алматы: ул. Шевченко 118, офис 221, БЦ «Алтын Гасыр». Телефон и WhatsApp '
                       '+7 775 181-05-95, info@kttron.kz. Консультации и поставка материалов КТтрон под заказ.',
    },
    {
        'url': '/dokumenty/',
        'h1': 'Документы: сертификаты и технические описания',
        'title': 'Сертификаты и технические описания КТ ТРОН (КТтрон) — скачать PDF',
        'description': 'Сертификаты соответствия, свидетельства о госрегистрации и технические описания материалов КТ ТРОН '
                       '(КТтрон) в PDF. Сертификат официального дистрибьютора в Казахстане.',
    },
    {
        'url': '/rekvizity/',
        'h1': 'Реквизиты и условия работы',
        'title': 'Реквизиты и условия работы — КТ ТРОН Казахстан (ТОО «DARHAN»)',
        'description': 'Реквизиты ТОО «DARHAN» — официального дистрибьютора КТ ТРОН в Казахстане: БИН, адреса, телефон. '
                       'Условия заказа, поставки под заказ, оплаты и доставки.',
    },
    {
        'url': '/politika-konfidencialnosti/',
        'h1': 'Политика конфиденциальности',
        'title': 'Политика конфиденциальности — КТ ТРОН Казахстан',
        'description': 'Как ТОО «DARHAN» (КТ ТРОН Казахстан) обрабатывает персональные данные посетителей сайта kttron.kz, '
                       'личного кабинета и приложения.',
    },
]

FOOT_LINKS = ('        <p class="foot-links"><a href="/o-kompanii/">О компании</a> · <a href="/kontakty/">Контакты</a> · '
              '<a href="/dokumenty/">Документы</a> · <a href="/rekvizity/">Реквизиты и условия</a> · '
              '<a href="/politika-konfidencialnosti/">Политика конфиденциальности</a></p>\n')


def body(page):
    if page['url'] == '/o-kompanii/':
        return ABOUT
    if page['url'] == '/kontakty/':
        rows = ''.join(f'<tr><th scope="row">{e(k)}</th><td>{v}</td></tr>' for k, v in CONTACTS)
        return (f'          <table class="info-table">{rows}</table>\n{MAP}'
                '          <p>Пришлите в WhatsApp фото дефекта или список материалов — подберём систему и рассчитаем расход. '
                'Работаем по всему Казахстану, поставка под заказ.</p>\n')
    if page['url'] == '/dokumenty/':
        return docs_body()
    if page['url'] == '/rekvizity/':
        rows = ''.join(f'<tr><th scope="row">{e(k)}</th><td>{v}</td></tr>' for k, v in REQUISITES)
        terms = ''.join(f'<tr><th scope="row">{e(k)}</th><td>{v}</td></tr>' for k, v in TERMS)
        return (f'          <h2>Реквизиты</h2>\n          <table class="info-table">{rows}</table>\n'
                f'          <h2>Условия работы</h2>\n          <table class="info-table">{terms}</table>\n'
                '          <p class="muted">Персональные данные обрабатываем по '
                '<a href="/politika-konfidencialnosti/">политике конфиденциальности</a>.</p>\n')
    parts = ''.join(f'          <h2>{e(h)}</h2>\n          {html}\n' for h, html in POLICY)
    return parts


def build(page, head, tail):
    url = page['url']
    h = head
    h = re.sub(r'<title>.*?</title>', f'<title>{e(page["title"])}</title>', h, flags=re.S)
    h = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{e(page["description"])}"', h)
    h = re.sub(r'<meta property="og:url" content="[^"]*"', f'<meta property="og:url" content="{SITE}{url}"', h)
    h = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{e(page["title"])}"', h)
    h = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{e(page["description"])}"', h)
    h = re.sub(r'<link rel="canonical" href="[^"]*"', f'<link rel="canonical" href="{SITE}{url}"', h)
    crumbs = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Главная', 'item': SITE + '/'},
        {'@type': 'ListItem', 'position': 2, 'name': page['h1'], 'item': SITE + url}]}
    ld = '<script type="application/ld+json">\n' + json.dumps(crumbs, ensure_ascii=False, indent=2) + '\n</script>'
    h = re.sub(LD_BLOCKS, lambda m: ld, h, count=1, flags=re.S)
    h = h.replace('  </head>', '    <style>.info-page{max-width:860px}.info-table{width:100%;border-collapse:collapse;margin:0 0 1.6rem;background:#fff}'
                  '.info-table th,.info-table td{padding:.6rem .7rem;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}'
                  '.info-table th{width:32%;color:var(--muted);font-weight:600}.info-page h2{margin:1.6rem 0 .6rem}'
                  '@media (max-width:640px){.info-table th,.info-table td{display:block;width:auto;border:0;padding:.15rem 0}'
                  '.info-table tr{display:block;padding:.5rem 0;border-bottom:1px solid var(--line)}}'
                  '.info-page .lead{font-size:1.08rem}.info-page h3{margin:1.2rem 0 .4rem;font-size:1.05rem}'
                  '.info-page li{margin:.25rem 0}.doc-toc{font-weight:600}'
                  '.doc-list{list-style:none;padding:0;margin:0 0 .8rem}.doc-list li{padding:.45rem 0;border-bottom:1px solid var(--line)}'
                  '.doc-list span{color:var(--muted);font-size:.85rem;white-space:nowrap}'
                  '.cert-card{display:grid;grid-template-columns:minmax(0,300px) 1fr;gap:24px;align-items:center;margin:1rem 0 1.6rem}'
                  '.cert-card a.cert-img{display:block;line-height:0;border-radius:6px;overflow:hidden;box-shadow:0 2px 14px rgba(0,60,110,.15)}'
                  '.cert-card img{width:100%;height:auto;display:block}.cert-card h3{margin:0 0 .5rem}.cert-card p{margin:0 0 .5rem}'
                  '.cert-card .cert-valid{font-weight:600}.cert-card a.cert-open{font-weight:600}'
                  '.info-page .map-wrap{margin:1rem 0 1.4rem}'
                  '@media (max-width:640px){.cert-card{grid-template-columns:1fr}}</style>\n  </head>', 1)
    main = f'''    <main id="top">
      <section class="section material-page">
        <div class="shell info-page">
          <nav class="crumbs" aria-label="Хлебные крошки"><a href="/">Главная</a> / {e(page['h1'])}</nav>
          <h1>{e(page['h1'])}</h1>
{body(page)}        </div>
      </section>
    </main>
'''
    return h + main + tail


def add_footer_links(s):
    # Ссылки ставим последней строкой подвала; повторный запуск заменяет строку, а не дублирует
    if 'class="foot-links"' in s:
        return re.sub(r'[ \t]*<p class="foot-links">.*?</p>\n', FOOT_LINKS, s, count=1)
    if 'class="site-footer"' not in s:
        return s
    return re.sub(r'(<footer class="site-footer">.*?)(\n\s*</div>\s*\n\s*</footer>)',
                  lambda m: m.group(1) + '\n' + FOOT_LINKS.rstrip('\n') + m.group(2), s, count=1, flags=re.S)


TDS_ALIASES = {'Гидрошнур НП': 'КТтрон-гидрошнур НП', 'КТ ТРОН-ТЭД-2': 'Клей эпоксидный КТтрон-ТЭД-2',
               'Ленты и фланцы для швов': 'КТтрон-гидролента PWP, DSL, DSL-PERFOR'}


def norm(name):
    return re.sub(r'[\s\-–]+', '', re.sub(r'\(ТО[^)]*\)', '', name).lower().replace('кт трон', 'кттрон'))


def add_tds_buttons():
    """Кнопка «Техническое описание (PDF)» на страницах товаров, для которых у завода есть ТО."""
    tds = {norm(it['title']): it['file'] for g in DOCS if g['section'] == 'Технические описания' for it in g['items']}
    pages = json.loads((ROOT / 'pages.json').read_text(encoding='utf-8'))
    done = 0
    for name, url in pages.items():
        pdf = tds.get(norm(TDS_ALIASES.get(name, name)))
        path = ROOT / url.strip('/') / 'index.html'
        if not pdf or not path.exists():
            continue
        s = path.read_text(encoding='utf-8')
        btn = (f'<!--kt:tds--><a class="btn btn-ghost-dark btn-lg" href="{pdf}" target="_blank">'
               f'Техническое описание (PDF)</a><!--/kt:tds-->')
        s2 = re.sub(r'<!--kt:tds-->.*?<!--/kt:tds-->', btn, s, count=1)
        if s2 == s and '<!--kt:tds-->' not in s:
            s2 = re.sub(r'(<div class="hero-cta">.*?)(\n\s*</div>)', lambda m: m.group(1) + '\n                ' + btn + m.group(2),
                        s, count=1, flags=re.S)
        if s2 != s:
            path.write_text(s2, encoding='utf-8')
        done += 1
    return done


def main():
    # Сначала ссылки в подвал всех страниц — тогда и образец уже с ними
    for path in ROOT.rglob('*.html'):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(('account/', 'admin/', 'test/', '.git/')):
            continue
        s = path.read_text(encoding='utf-8')
        new = add_footer_links(s)
        if new != s:
            path.write_text(new, encoding='utf-8')
    template = (ROOT / 'materials/kt-tron-3/index.html').read_text(encoding='utf-8')
    head = template[:template.index('    <main id="top">')]
    tail = template[template.rindex('</main>') + len('</main>\n'):]
    today = date.today().isoformat()
    sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    for page in PAGES:
        out = ROOT / page['url'].strip('/') / 'index.html'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build(page, head, tail), encoding='utf-8')
        loc = SITE + page['url']
        if f'<loc>{loc}</loc>' not in sitemap:
            sitemap = sitemap.replace('</urlset>', f'  <url><loc>{loc}</loc><lastmod>{today}</lastmod><changefreq>yearly</changefreq><priority>0.3</priority></url>\n</urlset>')
    (ROOT / 'sitemap.xml').write_text(sitemap, encoding='utf-8')
    print('информационные страницы собраны, ссылки в подвале проставлены; кнопок ТО на товарах:', add_tds_buttons())


if __name__ == '__main__':
    main()
