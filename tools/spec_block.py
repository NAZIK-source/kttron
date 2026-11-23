"""Блок «Пришлите спецификацию или проект» — для снабженцев и подрядчиков.
Файл на сайт не загружаем: клиент прикладывает его в WhatsApp или к письму.
Используют build_landing_pages.py и build_info_pages.py; в calculator/index.html блок вставлен вручную (такой же текст).
"""
from urllib.parse import quote

WA_TEXT = ('Здравствуйте! Отправляю спецификацию (проект, смету, фото) на расчёт материалов КТ ТРОН. '
           'Город доставки: ')
MAIL_SUBJECT = 'Спецификация на расчёт материалов КТ ТРОН'


def spec_block(indent='          '):
    wa = 'https://wa.me/77751810595?text=' + quote(WA_TEXT)
    mail = 'mailto:info@kttron.kz?subject=' + quote(MAIL_SUBJECT)
    return (
        f'{indent}<div class="spec-cta" id="specifikaciya" style="margin:32px 0;padding:20px 24px;border:1px solid rgba(23,80,160,.25);border-radius:12px;background:rgba(23,80,160,.05)">\n'
        f'{indent}  <h2 style="margin-top:0">Пришлите спецификацию или проект</h2>\n'
        f'{indent}  <p>Ведомость материалов, раздел проекта, смета или фото проблемного участка — подберём систему материалов КТ ТРОН, '
        'рассчитаем количество и подготовим коммерческое предложение.</p>\n'
        f'{indent}  <div class="hero-cta">'
        f'<a class="btn btn-solid btn-lg" href="{wa}" target="_blank" rel="noopener">Отправить в WhatsApp</a> '
        f'<a class="btn btn-ghost-dark btn-lg" href="{mail}">Отправить на почту</a></div>\n'
        f'{indent}  <p class="muted">Файл приложите к сообщению или письму: PDF, Excel, Word, фото. Укажите город доставки и сроки — '
        'остальное менеджер уточнит сам.</p>\n'
        f'{indent}</div>\n')
