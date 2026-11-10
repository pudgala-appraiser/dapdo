// 답도 월호: 따라다니는 목차에서 지금 읽는 부문을 표시한다.
(function () {
  var pin = document.getElementById('pin'); if (!pin) return;
  var links = [].slice.call(pin.querySelectorAll('a[href^="#"]')).filter(function (a) { return a.getAttribute('href') !== '#top'; });
  var heads = links.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
  var cur = -1, tick = false;
  function mark() {
    tick = false;
    var line = pin.getBoundingClientRect().bottom + 24, now = -1;
    for (var i = 0; i < heads.length; i++) if (heads[i] && heads[i].getBoundingClientRect().top <= line) now = i;
    if (now === cur) return;
    if (cur >= 0) { links[cur].classList.remove('on'); links[cur].removeAttribute('aria-current'); }
    cur = now;
    if (cur >= 0) {
      links[cur].classList.add('on'); links[cur].setAttribute('aria-current', 'true');
      var box = pin.firstElementChild, a = links[cur];   // 좁은 화면: 표시된 항목이 보이도록 목차를 옆으로 민다
      var keep = pin.querySelector('.up').offsetWidth + 8;   // 왼쪽에 고정된 '답도 ↑' 너비
      if (a.offsetLeft - keep < box.scrollLeft || a.offsetLeft + a.offsetWidth > box.scrollLeft + box.clientWidth) box.scrollLeft = a.offsetLeft - keep;
    }
  }
  window.addEventListener('scroll', function () { if (!tick) { tick = true; requestAnimationFrame(mark); } }, { passive: true });
  window.addEventListener('resize', mark);
  mark();
})();
