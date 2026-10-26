#!/usr/bin/env python3
"""Вставляет на страницы товаров собственный текст «О материале» из tools/own_texts.json:
для чего материал, типичные задачи, как выбрать среди соседних и пример расчёта расхода.
Описание завода остаётся ниже под заголовком «Описание производителя».

Текст стоит между метками <!--kt:own--> и <!--/kt:own-->, повторный запуск заменяет его, а не дублирует.
Запускайте после tools/build_product_pages.py (он пересоздаёт страницы):
  python3 tools/build_own_texts.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def e(s):
    return html.escape(s, quote=False)


def block(name, t):
    tasks = ''.join(f'<li>{e(x)}</li>' for x in t['tasks'])
    out = (f'<!--kt:own--><section class="own-text">\n'
           f'          <h2>О материале {e(name)}</h2>\n'
           f'          <p>{e(t["lead"])}</p>\n'
           f'          <h3>Для каких задач</h3>\n'
           f'          <ul>{tasks}</ul>\n'
           f'          <h3>Как выбрать</h3>\n'
           f'          <p>{e(t["choose"])}</p>\n')
    if t.get('calc'):
        out += (f'          <h3>Сколько нужно материала</h3>\n'
                f'          <p>{e(t["calc"])} Посчитать свой объект — в <a href="/calculator/">калькуляторе</a> '
                f'или пришлите размеры в WhatsApp.</p>\n')
    return out + '          </section><!--/kt:own-->\n          '


def main():
    texts = json.loads((ROOT / 'tools/own_texts.json').read_text(encoding='utf-8'))
    pages = json.loads((ROOT / 'pages.json').read_text(encoding='utf-8'))
    done, missing = 0, []
    for name, url in pages.items():
        slug = url.strip('/').split('/')[-1]
        path = ROOT / url.strip('/') / 'index.html'
        if slug not in texts or not path.exists():
            missing.append(name)
            continue
        s = path.read_text(encoding='utf-8')
        new = block(name, texts[slug])
        if '<!--kt:own-->' in s:
            s2 = re.sub(r'<!--kt:own-->.*?<!--/kt:own-->\n\s*', lambda m: new, s, count=1, flags=re.S)
        else:
            # Перед первым заголовком раздела после шапки товара
            start = s.index('class="material-layout"')
            pos = s.index('<h2', start)
            s2 = s[:pos] + new + s[pos:]
        # Текст завода — с пометкой, что это описание производителя
        s2 = s2.replace('<h2>Описание</h2>', '<h2>Описание производителя</h2>', 1)
        if s2 != s:
            path.write_text(s2, encoding='utf-8')
        done += 1
    print('страниц с текстом «О материале»:', done, '; без текста:', missing or 'нет')


if __name__ == '__main__':
    main()
