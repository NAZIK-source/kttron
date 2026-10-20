// Связь страниц сайта с личным кабинетом:
// показывает баланс в шапке и сохраняет отправленные в WhatsApp заявки в кабинет.
(function () {
  var logged = false;

  function updateLinks(data) {
    if (!data.logged) return;
    var links = document.querySelectorAll('.account-link');
    for (var i = 0; i < links.length; i++) {
      links[i].textContent = 'Кабинет · ' + data.balance.toLocaleString('ru-RU') + ' б.';
    }
  }

  fetch('/account/api.php', { credentials: 'same-origin', cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : { logged: false }; })
    .then(function (data) { logged = !!data.logged; updateLinks(data); })
    .catch(function () {});

  function save(text, source) {
    if (!logged || !text) return;
    var body = new FormData();
    body.append('text', text);
    body.append('source', source);
    if (navigator.sendBeacon) navigator.sendBeacon('/account/api.php', body);
    else fetch('/account/api.php', { method: 'POST', body: body, credentials: 'same-origin', keepalive: true });
  }

  function messageFrom(href) {
    var i = href.indexOf('text=');
    if (i < 0) return '';
    try { return decodeURIComponent(href.slice(i + 5).split('&')[0]); } catch (e) { return ''; }
  }

  // Корзина заявки, калькулятор и калькуляторы на страницах материалов
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('#requestSend, #send, .calc-wa');
    if (!a) return;
    save(messageFrom(a.getAttribute('href') || ''), a.id === 'requestSend' ? 'request' : 'calc');
  }, true);

  // Форма «Написать специалисту» на главной
  document.addEventListener('submit', function (e) {
    var f = e.target;
    if (!f || f.id !== 'leadForm') return;
    var get = function (n) { return f.elements[n] ? String(f.elements[n].value).trim() : ''; };
    var text = ['Имя: ' + get('name'), 'Телефон: ' + get('phone'), get('message') ? 'Задача: ' + get('message') : '']
      .filter(Boolean).join('\n');
    save(text, 'lead');
  }, true);
})();
