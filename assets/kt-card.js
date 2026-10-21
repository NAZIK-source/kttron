// Карточка товара в каталоге: открывается по нажатию на любое место товара,
// показывает фасовку, цену и ссылку на страницу материала; на телефоне — поверх шапки.
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
    '@media (width<=800px){' +
    '.lightbox{padding:12px;place-items:start center}' +
    '.lightbox-panel{padding:12px;gap:12px}' +
    '.lightbox img{height:min(34vh,260px)}' +
    '.lightbox-detail{max-height:none;overflow:visible}' +
    '.lightbox-close{position:fixed;top:14px;right:14px;box-shadow:0 4px 14px #0000003d}}';
  document.head.appendChild(css);

  var lastCard = null;

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
    }
  }

  new MutationObserver(function () { if (!box.hidden) fillMeta(); })
    .observe(box, { attributes: true, attributeFilter: ['hidden'] });
})();
