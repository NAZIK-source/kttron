#!/usr/bin/env python3
"""Собирает app-data.json — данные для мобильного приложения.

Приложение скачивает этот файл с kttron.kz при запуске, поэтому каталог, цены,
калькулятор и подбор материала в нём всегда такие же, как на сайте.

Источники (те же, что у генераторов страниц):
  index.html, assets/main-B89Pv38-.js — карточки каталога (через build_product_pages)
  prices.json, specs.json             — цены и характеристики
  calculator/index.html               — нормы расхода калькулятора
  tools/build_landing_pages.py        — подбор материалов под задачу (PAGES)

Запуск из корня репозитория:  python3 tools/build_app_data.py
Пишет app-data.json в корень сайта и копию в mobile/assets/ (вшивается в приложение).
Перезапускайте после смены цен, товаров или калькулятора.
"""
import json
import re
from datetime import datetime

import build_landing_pages as landing
import build_product_pages as products_src

ROOT = products_src.ROOT
SITE = products_src.SITE


def absolute(url):
    return url if url.startswith('http') else SITE + url


def load_calc():
    page = (ROOT / 'calculator/index.html').read_text(encoding='utf-8')
    literal = re.search(r'const materials = (\[.*?\]);', page, re.S).group(1)
    # Объекты JS → JSON: ключи латиницей без кавычек
    as_json = re.sub(r'([{,]\s*)([a-zA-Z]+):', r'\1"\2":', literal)
    return json.loads(as_json)


def load_tasks(prices):
    tasks = []
    for p in landing.PAGES:
        tasks.append({
            'id': p['url'].strip('/').split('/')[-1],
            'url': absolute(p['url']),
            'title': p['h1'].replace(' в Алматы', ''),
            'group': p['eyebrow'],
            'image': absolute(p['image']),
            'lead': p['lead'],
            'materials': [{'name': n, 'why': why} for n, why in p['materials']],
            'steps': p['steps'],
            'faq': [{'q': q, 'a': a} for q, a in p['faq']],
        })
    return tasks


def main():
    prices = json.loads((ROOT / 'prices.json').read_text(encoding='utf-8'))
    specs = json.loads((ROOT / 'specs.json').read_text(encoding='utf-8'))
    calc = load_calc()
    calc_by_name = {m['name']: m['id'] for m in calc}

    items = []
    for p in products_src.load_products():
        price, unit = products_src.price_info(prices, p['name'])
        items.append({
            'id': p['id'],
            'name': p['name'],
            'category': p['category'],
            'desc': p['desc'],
            'pack': p['pack'],
            'image': absolute(p['image']),
            'url': absolute(p['url']),
            'source': p['source'],
            'price': price,
            'unit': unit,
            'specs': specs.get(p['name'], []),
            'calc': calc_by_name.get(p['name']),
        })

    data = {
        'version': datetime.now().strftime('%Y%m%d%H%M'),
        'site': SITE,
        'whatsapp': products_src.WA,
        'prices_note': prices.get('_источник', ''),
        # Цены по названию — калькулятору, как kt-prices.js на сайте
        'prices': {name: {'price': pr, 'unit': un} for name in prices if not name.startswith('_')
                   for pr, un in [products_src.price_info(prices, name)] if pr},
        'categories': [{'id': k, 'name': v} for k, v in products_src.CATEGORIES.items()],
        'products': items,
        'calc': calc,
        'tasks': load_tasks(prices),
    }
    out = ROOT / 'app-data.json'
    text = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    out.write_text(text, encoding='utf-8')
    # Копия внутри приложения — на случай первого запуска без интернета
    (ROOT / 'mobile/assets').mkdir(parents=True, exist_ok=True)
    (ROOT / 'mobile/assets/app-data.json').write_text(text, encoding='utf-8')
    print(f'{out.name}: {len(items)} товаров, {len(calc)} в калькуляторе, {len(data["tasks"])} задач')


if __name__ == '__main__':
    main()
