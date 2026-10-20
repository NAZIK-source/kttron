// Цены «от … ₸ за 1 кг» из /prices.json.
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

  function patchCards(root) {
    var cards = (root || document).querySelectorAll('.product');
    for (var i = 0; i < cards.length; i++) {
      var h = cards[i].querySelector('h3'), box = cards[i].querySelector('.price');
      var e = h && box && entry(h.textContent);
      if (!e || box.getAttribute('data-kt-price') === String(e.price)) continue;
      var hint = box.querySelector('small');
      box.textContent = label(e);
      if (hint) box.appendChild(hint);
      box.setAttribute('data-kt-price', String(e.price));
    }
  }

  // Страница материала: плашка «Цена — по запросу»
  function patchFacts() {
    var h1 = document.querySelector('.material-page h1');
    var e = h1 && entry(h1.textContent);
    if (!e) return;
    var facts = document.querySelectorAll('.fact');
    for (var i = 0; i < facts.length; i++) {
      var s = facts[i].querySelector('span'), b = facts[i].querySelector('b');
      if (s && b && /Цена/.test(s.textContent)) b.textContent = label(e);
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
