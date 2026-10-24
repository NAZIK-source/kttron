// Карточка товара в каталоге: открывается по нажатию на любое место товара,
// показывает фасовку, цену, ссылку на страницу материала и таблицу характеристик
// из /specs.json; на телефоне — поверх шапки. Пока окно открыто, в адресной строке — адрес страницы товара.
(function () {
  var grid = document.getElementById('productGrid');
  var box = document.getElementById('lightbox');
  if (!grid || !box) return;

  var css = document.createElement('style');
  css.textContent =
    '#productGrid .product{cursor:pointer}' +
    '#productGrid .product .product-actions,#productGrid .product details{cursor:auto}' +
    '.lightbox{z-index:300}' +
    '.lightbox-meta{display:grid;gap:4px;margin:2px 0 4px}' +
    '.lightbox-meta .lb-pack{color:var(--brand-deep);font-weight:700;font-size:.9rem}' +
    '.lightbox-meta .lb-price{color:var(--brand-deep);font-weight:800;font-size:1.15rem}' +
    '.lb-specs{margin-bottom:1rem}' +
    '.lb-specs h3{color:var(--ink);font-size:1rem;margin:0 0 .4rem}' +
    '.lightbox-detail{max-height:min(58vh,520px)}' +
    '.lb-specs table{width:100%;border-collapse:collapse;font-size:.86rem;color:var(--ink)}' +
    '.lb-specs td{padding:.45rem .5rem;border-bottom:1px solid var(--line);vertical-align:top}' +
    '.lb-specs td:last-child{width:38%;font-weight:600}' +
    '.lb-specs th{text-align:left;background:var(--paper);padding:.5rem;font-size:.88rem}' +
    '@media (width<=800px){' +
    '.lightbox{padding:12px;place-items:start center}' +
    '.lightbox-panel{padding:12px;gap:12px}' +
    '.lightbox img{height:min(34vh,260px)}' +
    '.lightbox-detail{max-height:none;overflow:visible}' +
    '.lightbox-close{position:fixed;top:14px;right:14px;box-shadow:0 4px 14px #0000003d}}';
  document.head.appendChild(css);

  var lastCard = null;
  var lang = (document.documentElement.lang || 'ru').slice(0, 2);
  var pageLabel = { ru: 'Страница материала', kk: 'Материал беті', tg: 'Саҳифаи мавод', uz: 'Material sahifasi' }[lang] || 'Страница материала';
  var specsTitle = { ru: 'Характеристики', kk: 'Сипаттамалары', tg: 'Хусусиятҳо', uz: 'Xususiyatlar' }[lang] || 'Характеристики';

  // Таблицы характеристик грузим один раз, при первом открытии карточки
  var specs = null;
  function loadSpecs() {
    if (!specs) {
      specs = fetch('/specs.json', { cache: 'no-cache' })
        .then(function (r) { return r.ok ? r.json() : {}; })
        .catch(function () { return {}; });
    }
    return specs;
  }

  // Адреса страниц товаров: у каждого из 50 теперь своя страница
  var pages = null;
  function loadPages() {
    if (!pages) {
      pages = fetch('/pages.json', { cache: 'no-cache' })
        .then(function (r) { return r.ok ? r.json() : {}; })
        .catch(function () { return {}; });
    }
    return pages;
  }

  function renderSpecs(name) {
    loadSpecs().then(function (all) {
      var rows = all[name];
      var detail = document.getElementById('lightboxDetail');
      var title = document.getElementById('lightboxTitle');
      // Пока грузили, могли открыть другой товар
      if (!rows || !detail || !title || title.textContent.trim() !== name) return;
      var old = detail.querySelector('.lb-specs');
      if (old) old.remove();
      var wrap = document.createElement('div');
      wrap.className = 'lb-specs';
      wrap.appendChild(Object.assign(document.createElement('h3'), { textContent: specsTitle }));
      var table = document.createElement('table');
      rows.forEach(function (r) {
        var tr = document.createElement('tr');
        if (r.length === 1) {
          tr.appendChild(Object.assign(document.createElement('th'), { colSpan: 2, textContent: r[0] }));
        } else {
          tr.appendChild(Object.assign(document.createElement('td'), { textContent: r[0] }));
          tr.appendChild(Object.assign(document.createElement('td'), { textContent: r[1] }));
        }
        table.appendChild(tr);
      });
      wrap.appendChild(table);
      // Цифры — первым делом, описание ниже
      detail.insertBefore(wrap, detail.firstChild);
    });
  }

  // Нажатие на карточку (кроме кнопок, ссылок и «Полного описания») открывает окно товара
  grid.addEventListener('click', function (e) {
    var card = e.target.closest('.product');
    if (!card) return;
    lastCard = card;
    if (e.target.closest('button, a, details, input, select, textarea')) return;
    var zoom = card.querySelector('[data-zoom]');
    if (zoom) zoom.click();
  }, true);

  // Фасовка, цена и ссылка на страницу — берём из самой карточки, там они уже на нужном языке
  function fillMeta() {
    var title = document.getElementById('lightboxTitle');
    var card = lastCard;
    if (!card || !title || card.querySelector('h3').textContent.trim() !== title.textContent.trim()) return;
    var meta = document.getElementById('lightboxMeta');
    if (!meta) {
      meta = document.createElement('div');
      meta.id = 'lightboxMeta';
      meta.className = 'lightbox-meta';
      title.insertAdjacentElement('afterend', meta);
    }
    meta.textContent = '';
    var pack = card.querySelector('.pack'), price = card.querySelector('.price');
    if (pack) meta.appendChild(Object.assign(document.createElement('div'), { className: 'lb-pack', textContent: pack.textContent.trim() }));
    if (price) meta.appendChild(Object.assign(document.createElement('div'), { className: 'lb-price', textContent: price.firstChild ? price.firstChild.textContent.trim() : '' }));

    var actions = box.querySelector('.lightbox-actions');
    var old = document.getElementById('lightboxPage');
    if (old) old.remove();
    var page = card.querySelector('.product-actions a[href^="/"]');
    if (actions && page) {
      var a = page.cloneNode(true);
      a.id = 'lightboxPage';
      actions.insertBefore(a, document.getElementById('lightboxLink'));
    } else if (actions) {
      var name = title.textContent.trim();
      loadPages().then(function (all) {
        if (!all[name] || document.getElementById('lightboxPage') || title.textContent.trim() !== name) return;
        var link = Object.assign(document.createElement('a'), { id: 'lightboxPage', className: 'btn btn-ghost-dark', href: all[name], textContent: pageLabel });
        actions.insertBefore(link, document.getElementById('lightboxLink'));
      });
    }
    renderSpecs(title.textContent.trim());
  }

  // Адрес окна: пока открыта карточка товара, в адресной строке — адрес его страницы
  // (ссылку можно переслать, у получателя откроется полная страница). «Назад» закрывает окно.
  var pushed = false, savedTitle = document.title;
  function pushUrl() {
    var title = document.getElementById('lightboxTitle');
    var card = lastCard;
    if (!title || !card || !card.querySelector('h3') || card.querySelector('h3').textContent.trim() !== title.textContent.trim()) return;
    var name = title.textContent.trim();
    loadPages().then(function (all) {
      var url = all[name];
      if (!url || box.hidden || title.textContent.trim() !== name || pushed) return;
      history.pushState({ ktCard: url }, '', url);
      pushed = true;
      savedTitle = document.title;
      document.title = name + ' — КТ ТРОН Казахстан';
    });
  }
  function dropUrl() {
    if (!pushed) return;
    pushed = false;
    document.title = savedTitle;
    if (history.state && history.state.ktCard) history.back();
  }
  window.addEventListener('popstate', function () {
    if (!pushed) return;
    pushed = false;
    document.title = savedTitle;
    var close = document.getElementById('lightboxClose');
    if (!box.hidden && close) close.click();
  });

  new MutationObserver(function () {
    if (!box.hidden) { fillMeta(); pushUrl(); } else dropUrl();
  }).observe(box, { attributes: true, attributeFilter: ['hidden'] });
})();
