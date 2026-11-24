/* Переключатель карт 2ГИС / Google / Яндекс в блоке .map-tabs */
(function () {
  function init(box) {
    var frame = box.querySelector('iframe');
    var open = box.querySelector('.map-open');
    var btns = box.querySelectorAll('.map-tabbar button');
    for (var i = 0; i < btns.length; i++) {
      btns[i].addEventListener('click', function () {
        for (var j = 0; j < btns.length; j++) {
          var on = btns[j] === this;
          btns[j].classList.toggle('is-active', on);
          btns[j].setAttribute('aria-pressed', on ? 'true' : 'false');
        }
        if (frame.getAttribute('src') !== this.dataset.src) frame.setAttribute('src', this.dataset.src);
        if (open) open.setAttribute('href', this.dataset.href);
      });
    }
  }
  function run() {
    var boxes = document.querySelectorAll('.map-tabs');
    for (var i = 0; i < boxes.length; i++) init(boxes[i]);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run); else run();
})();
