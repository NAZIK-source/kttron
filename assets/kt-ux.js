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

  // Ссылка «Перейти к содержимому» первой в странице
  var main = document.querySelector('main');
  if (main) {
    if (!main.id) main.id = 'top';
    var skip = document.createElement('a');
    skip.className = 'kt-skip';
    skip.href = '#' + main.id;
    skip.textContent = { ru: 'Перейти к содержимому', kk: 'Мазмұнға өту', tg: 'Ба мундариҷа гузаштан', uz: 'Asosiy qismga o‘tish' }[lang] || 'Перейти к содержимому';
    document.body.insertBefore(skip, document.body.firstChild);
  }

  // Кнопка звонка в шапке на телефоне (номер на узких экранах спрятан в меню)
  var tel = document.querySelector('.header-contacts a[href^="tel:"]');
  var langBox = document.querySelector('.header-aside .lang');
  var aside = document.querySelector('.header-top-in .header-aside');
  if (tel && aside && !document.querySelector('.kt-call')) {
    var call = document.createElement('a');
    call.className = 'kt-call';
    call.href = tel.getAttribute('href');
    call.setAttribute('aria-label', tel.textContent.trim());
    call.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z"/></svg>';
    // Перед языками, а где их нет — в правую часть шапки
    if (langBox) langBox.parentNode.insertBefore(call, langBox);
    else aside.insertBefore(call, aside.firstChild);
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

  // 4. Каталог: у каждого материала — ссылка на его страницу на нашем сайте вместо ТО на kttron.ru
  if (grid) {
    var pageLabel = { ru: 'Страница материала', kk: 'Материал беті', tg: 'Саҳифаи мавод', uz: 'Material sahifasi' }[lang] || 'Страница материала';
    var pagesMap = null;
    var fixLinks = function () {
      if (!pagesMap) return;
      grid.querySelectorAll('.product').forEach(function (card) {
        var ext = card.querySelector('.product-actions a[href*="kttron.ru"]');
        if (!ext) return;
        var h = card.querySelector('h3');
        var url = h && pagesMap[h.textContent.trim()];
        if (card.querySelector('.product-actions a[href^="/materials/"]')) ext.remove();
        else if (url) {
          ext.href = url;
          ext.removeAttribute('target');
          ext.removeAttribute('rel');
          ext.textContent = pageLabel;
        }
      });
    };
    fetch('/pages.json').then(function (r) { return r.ok ? r.json() : {}; }).then(function (all) { pagesMap = all; fixLinks(); }).catch(function () {});
    new MutationObserver(fixLinks).observe(grid, { childList: true });
  }

  // 5. Заявка: необязательные «Компания / БИН» и «Город доставки» — попадают в сообщение WhatsApp,
  //    запоминаются в браузере. Ссылка /?zayavka=1 (из калькулятора) сразу открывает заявку.
  var note = document.querySelector('#requestDrawer .request-note');
  var sendBtn = document.getElementById('requestSend');
  if (note && sendBtn) {
    var L = {
      company: { ru: 'Компания / БИН (если нужен счёт на компанию)', kk: 'Компания / БСН (шот компанияға керек болса)', tg: 'Ширкат / БИН (агар ҳисоб ба ширкат лозим бошад)', uz: 'Kompaniya / BIN (hisob kompaniyaga kerak bo‘lsa)' },
      city: { ru: 'Город доставки', kk: 'Жеткізу қаласы', tg: 'Шаҳри расонидан', uz: 'Yetkazib berish shahri' },
      cityPh: { ru: 'Алматы', kk: 'Алматы', tg: 'Алматы', uz: 'Almati' }
    };
    var tr = function (k) { return L[k][lang] || L[k].ru; };
    var box = document.createElement('div');
    box.className = 'kt-req-extra';
    var field = function (key, label, ph) {
      var lab = document.createElement('label');
      var input = document.createElement('input');
      input.type = 'text';
      input.autocomplete = key === 'city' ? 'address-level2' : 'organization';
      if (ph) input.placeholder = ph;
      try { input.value = localStorage.getItem('kttron-req-' + key) || ''; } catch (e) {}
      input.addEventListener('input', function () {
        try { localStorage.setItem('kttron-req-' + key, input.value); } catch (e) {}
      });
      lab.append(label, input);
      box.appendChild(lab);
      return input;
    };
    var company = field('company', tr('company'));
    var city = field('city', tr('city'), tr('cityPh'));
    note.parentNode.insertBefore(box, note);
    // Скрипт сайта собирает ссылку WhatsApp раньше нас (его обработчик зарегистрирован первым) — дописываем строки в её текст
    sendBtn.addEventListener('click', function () {
      var extra = [];
      if (company.value.trim()) extra.push('Компания / БИН: ' + company.value.trim());
      if (city.value.trim()) extra.push('Город доставки: ' + city.value.trim());
      if (!extra.length || sendBtn.getAttribute('href') === '#') return;
      try {
        var url = new URL(sendBtn.href);
        var text = url.searchParams.get('text') || '';
        if (text.indexOf('Компания / БИН:') !== -1 || text.indexOf('Город доставки:') !== -1) return;
        // Пробелы — как %20, а не «+»: так WhatsApp точно покажет текст без плюсов
        sendBtn.href = url.origin + url.pathname + '?text=' + encodeURIComponent(text + '\n' + extra.join('\n'));
      } catch (e) {}
    });
    if (/[?&]zayavka=1/.test(location.search)) {
      var fab = document.getElementById('requestFab');
      if (fab) setTimeout(function () { fab.click(); }, 300);
      try { history.replaceState(null, '', location.pathname + location.hash); } catch (e) {}
    }
  }
})();
