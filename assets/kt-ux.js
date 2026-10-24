// Общие правки удобства (стили — в kt-ux.css):
// 1) главная: пока не выбран раздел и пустой поиск, показываем только ходовые материалы и кнопку «Показать все»;
// 2) объекты: по 12 карточек и кнопка «Показать ещё»;
// 3) окно заявки: фокус на крестике при открытии, Escape закрывает, фокус возвращается, закрытое окно недоступно с клавиатуры.
(function () {
  var lang = (document.documentElement.lang || 'ru').slice(0, 2);
  var T = {
    all: { ru: 'Показать все материалы', kk: 'Барлық материалдарды көрсету', tg: 'Ҳамаи маводҳоро нишон диҳед', uz: 'Barcha materiallarni ko‘rsatish' },
    more: { ru: 'Показать ещё', kk: 'Тағы көрсету', tg: 'Боз нишон диҳед', uz: 'Yana ko‘rsatish' }
  };
  function t(key) { return T[key][lang] || T[key].ru; }

  function moreButton(after, text, onClick) {
    var wrap = document.createElement('div');
    wrap.className = 'kt-more';
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-ghost-dark btn-lg';
    btn.textContent = text;
    btn.addEventListener('click', onClick);
    wrap.appendChild(btn);
    after.insertAdjacentElement('afterend', wrap);
    return wrap;
  }

  // 1. Главная (и kz/tg/uz): каталог из 50 материалов сворачиваем до ходовых
  var POPULAR = ['p030', 'p031', 'p032', 'p034', 'p035', 'p043', 'p039', 'p001', 'p002', 'p044', 'p045', 'p026'];
  var grid = document.getElementById('productGrid');
  var isHome = /^\/(kz\/|tg\/|uz\/)?$/.test(location.pathname);
  if (grid && isHome) {
    var expanded = false;
    var search = document.getElementById('searchInput');
    var more = moreButton(grid, '', function () {
      expanded = true;
      update();
      var first = grid.querySelector('.product:not(.kt-pop) button, .product:not(.kt-pop) a');
      if (first) first.focus({ preventScroll: true });
    });
    var update = function () {
      var chip = document.querySelector('#catChips .chip.is-active');
      var allChip = !chip || chip.getAttribute('data-cat') === 'all';
      var cards = grid.querySelectorAll('.product');
      var collapse = !expanded && allChip && !(search && search.value.trim()) && cards.length > POPULAR.length;
      cards.forEach(function (card) {
        var add = card.querySelector('[data-add]');
        var idx = add ? POPULAR.indexOf(add.getAttribute('data-add')) : -1;
        card.classList.toggle('kt-pop', idx !== -1);
        // В свёрнутом виде — в порядке списка POPULAR (сначала гидроизоляция)
        card.style.order = collapse && idx !== -1 ? String(idx - POPULAR.length) : '';
      });
      grid.classList.toggle('kt-collapsed', collapse);
      more.hidden = !collapse;
      more.firstChild.textContent = t('all') + ' (' + cards.length + ')';
    };
    new MutationObserver(update).observe(grid, { childList: true });
    document.addEventListener('click', function (e) {
      // Выбрали раздел или задачу — показываем всё, что подходит
      if (e.target.closest && e.target.closest('#catChips .chip, #solGrid [data-cat], #solGrid a, #solGrid button')) setTimeout(update, 0);
    });
    if (search) search.addEventListener('input', update);
    update();
  }

  // 2. Объекты: по 12 карточек
  var objects = document.getElementById('objectsGrid');
  if (objects) {
    var STEP = 12, shown = STEP;
    var moreObj = moreButton(objects, t('more'), function () { shown += STEP; apply(); });
    var apply = function () {
      var items = objects.children;
      for (var i = 0; i < items.length; i++) items[i].style.display = i < shown ? '' : 'none';
      moreObj.hidden = items.length <= shown;
    };
    // Смена фильтра перерисовывает список — начинаем снова с 12
    new MutationObserver(function () { shown = STEP; apply(); }).observe(objects, { childList: true });
    apply();
  }

  // 3. Окно заявки
  var drawer = document.getElementById('requestDrawer');
  if (drawer) {
    var closeBtn = document.getElementById('requestClose');
    var opener = null;
    document.addEventListener('focusin', function (e) {
      if (!drawer.contains(e.target)) opener = e.target;
    });
    var sync = function () {
      var open = drawer.classList.contains('is-open');
      if (open) {
        drawer.removeAttribute('inert');
        drawer.setAttribute('role', 'dialog');
        drawer.setAttribute('aria-modal', 'true');
        drawer.setAttribute('aria-labelledby', 'requestTitle');
        if (closeBtn && !drawer.contains(document.activeElement)) closeBtn.focus({ preventScroll: true });
      } else {
        drawer.setAttribute('inert', '');
        if (drawer.contains(document.activeElement) || document.activeElement === document.body) {
          if (opener && document.contains(opener)) opener.focus({ preventScroll: true });
        }
      }
    };
    new MutationObserver(sync).observe(drawer, { attributes: true, attributeFilter: ['class'] });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && drawer.classList.contains('is-open') && closeBtn) closeBtn.click();
    });
    sync();
  }
})();
