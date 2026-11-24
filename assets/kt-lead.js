/* Окно «Заявка на техническое решение»: открывается кнопками с data-lead, отправляет форму на /zayavka.php
   (письмо на info@kttron.kz с файлами). Язык подписей — по <html lang>. */
(function () {
  var T = {
    ru: {
      title: 'Заявка на техническое решение',
      lead: 'Опишите объект и приложите фото или проект — технический отдел подберёт систему материалов. Для наших клиентов — без оплаты.',
      name: 'Ваше имя*', phone: 'Телефон*', city: 'Город', message: 'Что случилось: объект, дефект, площадь, сроки',
      files: 'Фото, проект, ведомость', filesHint: 'До 5 файлов, всего до 15 МБ: JPG, PNG, PDF, Word, Excel',
      consent: 'Согласен с <a href="/politika-konfidencialnosti/" target="_blank">политикой конфиденциальности</a>',
      send: 'Отправить', sending: 'Отправляем…', close: 'Закрыть',
      ok: 'Спасибо! Заявка отправлена. Менеджер свяжется с вами в рабочее время (пн–пт, 09:00–17:00).',
      err: {
        name: 'Укажите имя.', phone: 'Укажите телефон полностью, например +7 777 123-45-67.', consent: 'Нужно согласие с политикой конфиденциальности.',
        too_big: 'Файлы слишком большие: всего до 15 МБ. Остальное пришлите в WhatsApp.', file_count: 'Можно приложить до 5 файлов.',
        file_type: 'Такой тип файла не принимаем. Подойдут JPG, PNG, PDF, Word, Excel.', rate: 'Слишком много заявок подряд. Напишите нам в WhatsApp.',
        any: 'Не получилось отправить. Напишите нам в WhatsApp или на info@kttron.kz.'
      }
    },
    kk: {
      title: 'Техникалық шешімге өтінім',
      lead: 'Нысанды сипаттап, фото немесе жобаны тіркеңіз — техникалық бөлім материалдар жүйесін іріктейді. Біздің клиенттер үшін тегін.',
      name: 'Атыңыз*', phone: 'Телефон*', city: 'Қала', message: 'Не болды: нысан, ақау, аудан, мерзім',
      files: 'Фото, жоба, тізім', filesHint: '5 файлға дейін, барлығы 15 МБ-қа дейін: JPG, PNG, PDF, Word, Excel',
      consent: '<a href="/politika-konfidencialnosti/" target="_blank">Құпиялылық саясатымен</a> келісемін',
      send: 'Жіберу', sending: 'Жіберілуде…', close: 'Жабу',
      ok: 'Рахмет! Өтінім жіберілді. Менеджер жұмыс уақытында хабарласады (дс–жм, 09:00–17:00).',
      err: {
        name: 'Атыңызды жазыңыз.', phone: 'Телефонды толық жазыңыз, мысалы +7 777 123-45-67.', consent: 'Құпиялылық саясатымен келісу қажет.',
        too_big: 'Файлдар тым үлкен: барлығы 15 МБ-қа дейін. Қалғанын WhatsApp-қа жіберіңіз.', file_count: '5 файлға дейін тіркеуге болады.',
        file_type: 'Бұл файл түрі қабылданбайды. JPG, PNG, PDF, Word, Excel жарайды.', rate: 'Өтінім тым көп. WhatsApp-қа жазыңыз.',
        any: 'Жіберу мүмкін болмады. WhatsApp-қа немесе info@kttron.kz поштасына жазыңыз.'
      }
    },
    tg: {
      title: 'Дархост барои ҳалли техникӣ',
      lead: 'Объектро тавсиф кунед ва акс ё лоиҳаро замима намоед — шӯъбаи техникӣ системаи маводро интихоб мекунад. Барои мизоҷони мо ройгон.',
      name: 'Номи шумо*', phone: 'Телефон*', city: 'Шаҳр', message: 'Чӣ шуд: объект, нуқсон, масоҳат, мӯҳлат',
      files: 'Акс, лоиҳа, рӯйхат', filesHint: 'То 5 файл, ҳамагӣ то 15 МБ: JPG, PNG, PDF, Word, Excel',
      consent: 'Бо <a href="/politika-konfidencialnosti/" target="_blank">сиёсати махфият</a> розӣ ҳастам',
      send: 'Фиристодан', sending: 'Фиристода мешавад…', close: 'Пӯшидан',
      ok: 'Ташаккур! Дархост фиристода шуд. Менеджер дар вақти корӣ бо шумо тамос мегирад (дш–ҷм, 09:00–17:00).',
      err: {
        name: 'Номро нависед.', phone: 'Телефонро пурра нависед, масалан +7 777 123-45-67.', consent: 'Розигӣ бо сиёсати махфият лозим аст.',
        too_big: 'Файлҳо хеле калонанд: ҳамагӣ то 15 МБ. Боқимондаро ба WhatsApp фиристед.', file_count: 'То 5 файл замима кардан мумкин аст.',
        file_type: 'Ин навъи файл қабул намешавад. JPG, PNG, PDF, Word, Excel мувофиқанд.', rate: 'Дархостҳо зиёданд. Ба WhatsApp нависед.',
        any: 'Фиристодан нашуд. Ба WhatsApp ё ба info@kttron.kz нависед.'
      }
    },
    uz: {
      title: 'Texnik yechim uchun ariza',
      lead: "Obyektni tasvirlab, surat yoki loyihani biriktiring — texnik bo'lim materiallar tizimini tanlaydi. Mijozlarimiz uchun bepul.",
      name: 'Ismingiz*', phone: 'Telefon*', city: 'Shahar', message: "Nima bo'ldi: obyekt, nuqson, maydon, muddat",
      files: "Surat, loyiha, ro'yxat", filesHint: '5 tagacha fayl, jami 15 MB gacha: JPG, PNG, PDF, Word, Excel',
      consent: '<a href="/politika-konfidencialnosti/" target="_blank">Maxfiylik siyosati</a> bilan roziman',
      send: 'Yuborish', sending: 'Yuborilmoqda…', close: 'Yopish',
      ok: "Rahmat! Ariza yuborildi. Menejer ish vaqtida siz bilan bog'lanadi (du–ju, 09:00–17:00).",
      err: {
        name: 'Ismingizni yozing.', phone: "Telefonni to'liq yozing, masalan +7 777 123-45-67.", consent: 'Maxfiylik siyosatiga rozilik kerak.',
        too_big: 'Fayllar juda katta: jami 15 MB gacha. Qolganini WhatsApp orqali yuboring.', file_count: '5 tagacha fayl biriktirish mumkin.',
        file_type: 'Bunday fayl turi qabul qilinmaydi. JPG, PNG, PDF, Word, Excel mos keladi.', rate: "Arizalar juda ko'p. WhatsApp'ga yozing.",
        any: "Yuborib bo'lmadi. WhatsApp yoki info@kttron.kz manziliga yozing."
      }
    }
  };
  var lang = (document.documentElement.lang || 'ru').slice(0, 2);
  var t = T[lang] || T.ru;
  var MAX_TOTAL = 15 * 1024 * 1024, MAX_FILES = 5;

  var css = '.kl-back{position:fixed;inset:0;z-index:300;background:#10161acc;display:grid;place-items:center;padding:16px;overflow:auto}' +
    '.kl-back[hidden]{display:none}.kl-box{position:relative;background:#fff;border-radius:16px;width:min(520px,100%);padding:24px 24px 22px;box-shadow:0 24px 60px #0006}' +
    '.kl-box h2{margin:0 36px 6px 0;font-size:1.3rem;line-height:1.25}.kl-box p.kl-lead{margin:0 0 14px;color:#6e6e6e;font-size:.92rem}' +
    '.kl-x{position:absolute;top:12px;right:12px;width:36px;height:36px;border:0;border-radius:50%;background:#f1f3f5;font-size:1.4rem;line-height:1;cursor:pointer}' +
    '.kl-f{display:grid;gap:10px}.kl-f input[type=text],.kl-f input[type=tel],.kl-f textarea{width:100%;border:1px solid #dcdcdc;border-radius:10px;padding:.7rem .85rem;font:inherit;background:#f8f9fa}' +
    '.kl-f input:focus,.kl-f textarea:focus{outline:2px solid #0093dd;outline-offset:0;background:#fff}.kl-f textarea{min-height:84px;resize:vertical}' +
    '.kl-file{border:1px dashed #9fc7de;border-radius:10px;padding:.7rem .85rem;background:#f5f9fc;font-size:.9rem}.kl-file b{display:block;margin-bottom:4px}' +
    '.kl-file small{display:block;color:#6e6e6e;margin-top:4px}.kl-file input{max-width:100%}.kl-list{margin:6px 0 0;padding:0;list-style:none;font-size:.85rem;color:#2c2c2c}' +
    '.kl-c{display:flex;gap:8px;align-items:flex-start;font-size:.85rem;color:#4a4a4a}.kl-c input{margin-top:3px}.kl-hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}' +
    '.kl-err{color:#c0392b;font-size:.9rem;font-weight:600;margin:0}.kl-ok{font-size:1rem;font-weight:600;color:#1e7e34;margin:8px 0 4px}' +
    '.kl-f .btn{justify-self:start}.kl-f .btn[disabled]{opacity:.6;cursor:wait}';

  var back, form, errEl, list, opener;

  function build() {
    var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    back = document.createElement('div');
    back.className = 'kl-back'; back.hidden = true;
    back.innerHTML =
      '<div class="kl-box" role="dialog" aria-modal="true" aria-labelledby="klTitle">' +
      '<button type="button" class="kl-x" aria-label="' + t.close + '">×</button>' +
      '<h2 id="klTitle">' + t.title + '</h2><p class="kl-lead">' + t.lead + '</p>' +
      '<form class="kl-f" novalidate enctype="multipart/form-data">' +
      '<input type="text" name="name" autocomplete="name" maxlength="100" required placeholder="' + t.name + '" aria-label="' + t.name + '">' +
      '<input type="tel" name="phone" autocomplete="tel" maxlength="30" required placeholder="' + t.phone + '" aria-label="' + t.phone + '">' +
      '<input type="text" name="city" autocomplete="address-level2" maxlength="100" placeholder="' + t.city + '" aria-label="' + t.city + '">' +
      '<textarea name="message" maxlength="3000" placeholder="' + t.message + '" aria-label="' + t.message + '"></textarea>' +
      '<label class="kl-file"><b>' + t.files + '</b><input type="file" name="files[]" multiple accept=".jpg,.jpeg,.png,.webp,.heic,.pdf,.doc,.docx,.xls,.xlsx,.dwg,.zip,image/*">' +
      '<small>' + t.filesHint + '</small><ul class="kl-list"></ul></label>' +
      '<div class="kl-hp" aria-hidden="true"><input type="text" name="website" tabindex="-1" autocomplete="off"></div>' +
      '<label class="kl-c"><input type="checkbox" name="consent" value="1" checked><span>' + t.consent + '</span></label>' +
      '<p class="kl-err" hidden></p>' +
      '<button type="submit" class="btn btn-solid btn-lg">' + t.send + '</button>' +
      '</form></div>';
    document.body.appendChild(back);
    form = back.querySelector('form'); errEl = back.querySelector('.kl-err'); list = back.querySelector('.kl-list');
    back.querySelector('.kl-x').addEventListener('click', close);
    back.addEventListener('click', function (e) { if (e.target === back) close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !back.hidden) close(); });
    form.querySelector('input[type=file]').addEventListener('change', function () {
      list.innerHTML = '';
      Array.prototype.forEach.call(this.files, function (f) {
        var li = document.createElement('li'); li.textContent = '📎 ' + f.name + ' — ' + (f.size < 102400 ? Math.max(1, Math.round(f.size / 1024)) + ' KB' : (f.size / 1048576).toFixed(1).replace('.', ',') + ' MB'); list.appendChild(li);
      });
    });
    form.addEventListener('input', function () { errEl.hidden = true; });
    form.addEventListener('submit', submit);
  }

  function showErr(code) { errEl.textContent = t.err[code] || t.err.any; errEl.hidden = false; }

  function submit(e) {
    e.preventDefault();
    errEl.hidden = true;
    var fd = new FormData(form);
    if (String(fd.get('name') || '').trim().length < 2) return showErr('name');
    var digits = String(fd.get('phone') || '').replace(/\D/g, '');
    if (digits.length < 10 || digits.length > 15) return showErr('phone');
    if (!form.consent.checked) return showErr('consent');
    var files = form.querySelector('input[type=file]').files, total = 0;
    if (files.length > MAX_FILES) return showErr('file_count');
    for (var i = 0; i < files.length; i++) total += files[i].size;
    if (total > MAX_TOTAL) return showErr('too_big');
    fd.append('t', String(form.dataset.opened || ''));
    fd.append('page', location.pathname);
    fd.append('lang', lang);
    var btn = form.querySelector('button[type=submit]');
    btn.disabled = true; btn.textContent = t.sending;
    fetch('/zayavka.php', { method: 'POST', body: fd, headers: { Accept: 'application/json' } })
      .then(function (r) { return r.json().catch(function () { return { ok: false, error: r.status === 413 ? 'too_big' : 'any' }; }); })
      .then(function (res) {
        if (!res.ok) { showErr(res.error); return; }
        try { ym(113689719, 'reachGoal', 'tech_request'); } catch (x) {}
        form.hidden = true;
        var ok = document.createElement('p'); ok.className = 'kl-ok'; ok.textContent = t.ok;
        back.querySelector('.kl-box').appendChild(ok);
      })
      .catch(function () { showErr('any'); })
      .then(function () { btn.disabled = false; btn.textContent = t.send; });
  }

  function open(e) {
    if (e) e.preventDefault();
    if (!back) build();
    opener = document.activeElement;
    var done = back.querySelector('.kl-ok');
    if (done) { done.remove(); form.reset(); list.innerHTML = ''; form.hidden = false; }
    errEl.hidden = true;
    form.dataset.opened = String(Date.now());
    back.hidden = false;
    document.body.style.overflow = 'hidden';
    form.querySelector('[name=name]').focus();
  }

  function close() {
    back.hidden = true;
    document.body.style.overflow = '';
    if (opener && opener.focus) opener.focus();
  }

  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('[data-lead]');
    if (b) open(e);
  });
})();
