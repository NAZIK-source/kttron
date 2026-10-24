// Переводы kz/tg/uz прямо в HTML (для поисковиков, которые не выполняют скрипты, — в первую очередь Яндекс).
//
// Скрипт сайта переводит страницы на лету: подставляет тексты в элементы с data-i18n и рисует
// каталог. Здесь мы открываем каждую языковую страницу в браузере (Playwright), забираем готовые
// переводы и каталог и записываем их в сам файл. Разметку файла не переформатируем — меняем только
// тексты, атрибуты и пустые контейнеры каталога. Скрипт сайта потом всё равно перерисует их сам.
//
// Запуск: сайт должен открываться локально (например, Apache на :8080 с корнем в репозитории), затем
//   node tools/prerender_langs.js http://localhost:8080
// Перезапускайте после смены переводов, каталога или цен в скриптах сайта.
const fs = require('fs');
const path = require('path');
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }

const ROOT = path.resolve(__dirname, '..');
const BASE = (process.argv[2] || 'http://localhost:8080').replace(/\/$/, '');
const PAGES = ['kz/', 'tg/', 'uz/', 'kz/objects/', 'tg/objects/', 'uz/objects/'];
// Каталог на главных вставляем готовым, как на русской главной; сетку объектов (136 фото) оставляем скрипту
const CONTAINERS = ['solGrid', 'catChips', 'productGrid'];

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const re = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  // Только скрипт сайта: без наших дополнений (цены, свёрнутый каталог) и без Метрики
  await page.route(/kt-(ux|prices|card)\.js|mc\.yandex\.ru/, (r) => r.abort());
  for (const rel of PAGES) {
    await page.goto(`${BASE}/${rel}`, { waitUntil: 'load' });
    await page.waitForTimeout(1500);
    const data = await page.evaluate((ids) => {
      const pick = (attr, prop) => {
        const out = {};
        document.querySelectorAll(`[${attr}]`).forEach((el) => { out[el.getAttribute(attr)] = prop(el); });
        return out;
      };
      const meta = document.querySelector('meta[name="description"]');
      const containers = {};
      ids.forEach((id) => { const el = document.getElementById(id); if (el) containers[id] = el.innerHTML; });
      const metaBox = document.getElementById('catalogMeta');
      return {
        title: document.title,
        description: meta ? meta.getAttribute('content') : null,
        text: pick('data-i18n', (el) => el.textContent),
        aria: pick('data-i18n-aria', (el) => el.getAttribute('aria-label') || ''),
        placeholder: pick('data-i18n-placeholder', (el) => el.getAttribute('placeholder') || ''),
        title_attr: pick('data-i18n-title', (el) => el.getAttribute('title') || ''),
        containers,
        catalogMeta: metaBox ? metaBox.textContent : null,
      };
    }, CONTAINERS);

    const file = path.join(ROOT, rel, 'index.html');
    let s = fs.readFileSync(file, 'utf8');
    const before = s;
    // Тексты: содержимое элемента с data-i18n="ключ" (там только текст, без вложенной разметки)
    for (const [key, text] of Object.entries(data.text)) {
      const rx = new RegExp(`(<([a-z0-9]+)\\b[^>]*\\sdata-i18n="${re(key)}"[^>]*>)([^<]*)(</\\2>)`, 'g');
      s = s.replace(rx, (m, open, tag, inner, close) => {
        // Сохраняем отступы вокруг текста, как в исходном файле
        const lead = inner.match(/^\s*/)[0], trail = inner.match(/\s*$/)[0];
        return open + (inner.trim() ? lead + esc(text.trim()) + trail : esc(text)) + close;
      });
    }
    const setAttr = (map, dataAttr, attr) => {
      for (const [key, val] of Object.entries(map)) {
        const rx = new RegExp(`<[a-z0-9]+\\b[^>]*\\s${dataAttr}="${re(key)}"[^>]*>`, 'g');
        s = s.replace(rx, (tag) => (new RegExp(`\\s${attr}="[^"]*"`).test(tag)
          ? tag.replace(new RegExp(`(\\s${attr}=")[^"]*(")`), `$1${escAttr(val)}$2`)
          : tag.replace(/\s*\/?>$/, (end) => ` ${attr}="${escAttr(val)}"${end}`)));
      }
    };
    setAttr(data.aria, 'data-i18n-aria', 'aria-label');
    setAttr(data.placeholder, 'data-i18n-placeholder', 'placeholder');
    setAttr(data.title_attr, 'data-i18n-title', 'title');
    if (data.description) s = s.replace(/(<meta\s+name="description"\s+content=")[^"]*(")/, `$1${escAttr(data.description)}$2`);
    // Пустые контейнеры каталога — готовой разметкой
    // Вставка — между метками <!--kt:id--> и <!--/kt:id-->, чтобы повторный запуск заменял, а не дублировал
    for (const [id, html] of Object.entries(data.containers)) {
      const marked = new RegExp(`(<!--kt:${id}-->)[\\s\\S]*?(<!--/kt:${id}-->)`);
      if (marked.test(s)) s = s.replace(marked, (m, a, b) => a + html + b);
      else s = s.replace(new RegExp(`(<([a-z]+)\\b[^>]*\\sid="${id}"[^>]*>)(</\\2>)`),
        (m, open, tag, close) => `${open}<!--kt:${id}-->${html}<!--/kt:${id}-->${close}`);
    }
    if (data.catalogMeta) s = s.replace(/(<p\b[^>]*\sid="catalogMeta"[^>]*>)[^<]*(<\/p>)/, `$1${esc(data.catalogMeta)}$2`);
    if (s !== before) fs.writeFileSync(file, s);
    console.log(rel, s === before ? 'без изменений' : 'обновлён', '—', data.title);
  }
  await browser.close();
})();
