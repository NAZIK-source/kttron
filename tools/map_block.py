"""Блок карты с переключателем 2ГИС / Google / Яндекс (главная ru/kz/tg/uz и /kontakty/)."""
import json
import urllib.parse

LAT, LON = 43.244629, 76.926374
FIRM_2GIS = '70000001119747145'

_opt = {"pos": {"lat": LAT, "lon": LON, "zoom": 16}, "opt": {"city": "almaty"}, "org": FIRM_2GIS}
# Запрос по названию: Google показывает метку профиля компании «КТ ТРОН Казахстан»
_GQ = urllib.parse.quote('КТ ТРОН Казахстан, Шевченко 118, Алматы')
MAPS = [
    ('2gis', '2ГИС',
     'https://widgets.2gis.com/widget?type=firmsonmap&amp;options='
     + urllib.parse.quote(json.dumps(_opt, separators=(',', ':'))),
     f'https://2gis.kz/almaty/geo/{FIRM_2GIS}'),
    ('google', 'Google',
     'https://www.google.com/maps?q=' + _GQ + '&amp;z=17&amp;output=embed',
     'https://www.google.com/maps/search/?api=1&amp;query=' + _GQ),
    ('yandex', 'Яндекс',
     f'https://yandex.kz/map-widget/v1/?ll={LON}%2C{LAT}&amp;z=17&amp;pt={LON}%2C{LAT}%2Cpm2rdm',
     f'https://yandex.kz/maps/?pt={LON}%2C{LAT}&amp;z=17&amp;l=map'),
]
OPEN = {'ru': 'Открыть карту', 'kk': 'Картаны ашу', 'tg': 'Харитаро кушодан', 'uz': 'Xaritani ochish'}
NAMES = {'uz': {'Яндекс': 'Yandex', '2ГИС': '2GIS'}}

STYLE = ('<style>.map-tabs{display:flex;flex-direction:column}.map-tabbar{display:flex;gap:6px;padding:8px;'
         'background:#fff;border-bottom:1px solid var(--line,#dcdcdc)}.map-tabbar button{flex:1;border:1px solid '
         'var(--line,#dcdcdc);background:#fff;border-radius:999px;padding:.45rem .6rem;font:inherit;font-size:.86rem;'
         'font-weight:800;color:var(--gray,#6e6e6e);cursor:pointer}.map-tabbar button:hover{border-color:#0093dd;'
         'color:#0093dd}.map-tabbar button.is-active{background:#0093dd;border-color:#0093dd;color:#fff}'
         '.map-tabs iframe{border:0;width:100%;height:360px;display:block}.map-open{display:block;padding:8px 12px;'
         'background:#fff;border-top:1px solid var(--line,#dcdcdc);font-size:.86rem;font-weight:700;color:#0077b3;'
         'text-align:right}.map-open:hover{text-decoration:underline}</style>')


def map_block(title, lang='ru', indent='          ', title_attr=''):
    names = NAMES.get(lang, {})
    btns = ''.join(
        f'<button type="button" data-src="{src}" data-href="{href}" aria-pressed="{"true" if i == 0 else "false"}"'
        f'{" class=\"is-active\"" if i == 0 else ""}>{names.get(label, label)}</button>'
        for i, (_, label, src, href) in enumerate(MAPS))
    first = MAPS[0]
    return (f'{indent}<div class="map-wrap map-tabs">{STYLE}<div class="map-tabbar">{btns}</div>'
            f'<iframe title="{title}"{title_attr} loading="lazy" referrerpolicy="no-referrer-when-downgrade" '
            f'src="{first[2]}"></iframe>'
            f'<a class="map-open" href="{first[3]}" target="_blank" rel="noopener">{OPEN[lang]} ↗</a></div>\n'
            f'{indent}<script src="/assets/kt-map.js?v=1" defer></script>\n')
