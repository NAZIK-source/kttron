#!/usr/bin/env python3
"""Собирает страницы «Реквизиты и условия» (/rekvizity/) и «Политика конфиденциальности»
(/politika-konfidencialnosti/) и ставит ссылки на них в подвал всех страниц сайта.

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
    ('Документы', 'Сертификаты и технические описания материалов — по запросу в WhatsApp или на e-mail.'),
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

PAGES = [
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

FOOT_LINKS = ('        <p class="foot-links"><a href="/rekvizity/">Реквизиты и условия</a> · '
              '<a href="/politika-konfidencialnosti/">Политика конфиденциальности</a></p>\n')


def body(page):
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
                  '.info-table tr{display:block;padding:.5rem 0;border-bottom:1px solid var(--line)}}</style>\n  </head>', 1)
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
    # Ссылки ставим последней строкой подвала; повторный запуск ничего не дублирует
    if 'class="foot-links"' in s or 'class="site-footer"' not in s:
        return s
    return re.sub(r'(<footer class="site-footer">.*?)(\n\s*</div>\s*\n\s*</footer>)',
                  lambda m: m.group(1) + '\n' + FOOT_LINKS.rstrip('\n') + m.group(2), s, count=1, flags=re.S)


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
    print('страницы реквизитов и политики собраны, ссылки в подвале проставлены')


if __name__ == '__main__':
    main()
