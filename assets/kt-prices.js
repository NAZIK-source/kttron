// Цены «от … ₸ за 1 кг» и «≈ … ₸ / 25 кг» за упаковку из /prices.json.
// Подставляет цену в карточки каталога, на страницы материалов и в калькулятор.
// Нет цены в файле — остаётся «Цена по запросу».
(function () {
  var lang = (document.documentElement.lang || 'ru').slice(0, 2);
  var words = {
    ru: { from: 'от {p} ₸ за 1 {u}', kg: 'кг', pcs: 'шт' },
    kk: { from: '1 {u} үшін {p} ₸ бастап', kg: 'кг', pcs: 'дана' },
    tg: { from: 'аз {p} ₸ барои 1 {u}', kg: 'кг', pcs: 'дона' },
    uz: { from: '1 {u} uchun {p} ₸ dan', kg: 'kg', pcs: 'dona' }
  };
  var t = words[lang] || words.ru;
  var prices = {};

  function fmt(n) { return Math.round(n).toLocaleString('ru-RU'); }

  // Значение в prices.json: число (₸ за 1 кг) или { "price": 5000, "unit": "шт" }
  function entry(name) {
    var v = prices[String(name || '').trim()];
    if (typeof v === 'number' && v > 0) return { price: v, unit: 'кг' };
    if (v && typeof v.price === 'number' && v.price > 0) return { price: v.price, unit: v.unit || 'шт' };
    return null;
  }

  function label(e) {
    var unit = e.unit === 'кг' ? t.kg : e.unit === 'шт' ? t.pcs : e.unit;
    return t.from.replace('{p}', fmt(e.price)).replace('{u}', unit);
  }

  // Цена за упаковку: прораб считает мешками. Двухкомпонентные продаются комплектом 33,5 кг
  function packKg(name, text) {
    if (/10 2К|122 флекс/.test(name)) return 33.5;
    var m = String(text || '').match(/(\d+(?:[.,]\d+)?)\s*(кг|kg)/i);
    return m ? parseFloat(m[1].replace(',', '.')) : 0;
  }

  function packLine(e, kg) {
    if (!e || e.unit !== 'кг' || !kg) return null;
    var el = document.createElement('small');
    el.className = 'kt-pack-price';
    el.textContent = '≈ ' + fmt(e.price * kg) + ' ₸ / ' + String(kg).replace('.', ',') + ' ' + t.kg;
    return el;
  }

  function patchCards(root) {
    var cards = (root || document).querySelectorAll('.product');
    for (var i = 0; i < cards.length; i++) {
      var h = cards[i].querySelector('h3'), box = cards[i].querySelector('.price');
      var e = h && box && entry(h.textContent);
      if (!e || box.getAttribute('data-kt-price') === String(e.price)) continue;
      var hint = box.querySelector('small:not(.kt-pack-price)');
      var pack = cards[i].querySelector('.pack');
      box.textContent = label(e);
      var line = packLine(e, packKg(h.textContent, pack && pack.textContent));
      if (line) box.appendChild(line);
      if (hint) box.appendChild(hint);
      box.setAttribute('data-kt-price', String(e.price));
    }
  }

  // Страница материала: плашка «Цена — по запросу»
  function patchFacts() {
    var h1 = document.querySelector('.material-page h1');
    var e = h1 && entry(h1.textContent);
    if (!e) return;
    var facts = document.querySelectorAll('.fact'), packText = '';
    for (var j = 0; j < facts.length; j++) {
      var ps = facts[j].querySelector('span'), pb = facts[j].querySelector('b');
      if (ps && pb && /Фасовка/.test(ps.textContent)) packText = pb.textContent;
    }
    for (var i = 0; i < facts.length; i++) {
      var s = facts[i].querySelector('span'), b = facts[i].querySelector('b');
      if (s && b && /Цена/.test(s.textContent)) {
        b.textContent = label(e);
        var line = packLine(e, packKg(h1.textContent, packText));
        if (line) b.appendChild(line);
      }
    }
  }

  // Для калькулятора: window.ktPrice('КТ ТРОН-3') → { price, unit } или null
  window.ktPrice = entry;

  function apply() {
    patchCards();
    patchFacts();
    document.dispatchEvent(new CustomEvent('kt-prices'));
  }

  // Каталог перерисовывается при фильтрации — следим за ним
  function watch() {
    var grid = document.getElementById('productGrid');
    if (grid && window.MutationObserver) {
      new MutationObserver(function () { patchCards(grid); }).observe(grid, { childList: true });
    }
  }

  // no-cache: браузер каждый раз сверяет файл с сервером, новые цены видны сразу
  fetch('/prices.json', { cache: 'no-cache' })
    .then(function (r) { return r.ok ? r.json() : {}; })
    .then(function (data) {
      prices = data || {};
      if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { apply(); watch(); });
      else { apply(); watch(); }
    })
    .catch(function () {});
})();
