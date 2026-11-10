// 답도 메인: 화면 폭에 맞춰 그림을 줄이고, 지난 호 목록을 읽어 온다.
(function () {
  var hero = document.getElementById('hero'), box = document.getElementById('stagebox');
  function fit() {
    var w = hero.clientWidth, narrow = w < 820;
    hero.classList.toggle('narrow', narrow);
    var k = narrow ? w / 1146 : w / 1280;
    hero.style.setProperty('--k', k);
    box.style.height = (800 * k) + 'px';
  }
  fit();
  window.addEventListener('resize', fit);
  document.getElementById('replay').addEventListener('click', function () {
    hero.classList.toggle('run-b');
  });
  function esc(s) { var d = document.createElement('div'); d.textContent = s == null ? '' : String(s); return d.innerHTML; }
  fetch('issues.json', { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : []; }).then(function (list) {
    if (!list || !list.length) return;
    list.sort(function (a, b) { return a.id < b.id ? 1 : -1; });
    var ol = document.getElementById('issues');
    ol.innerHTML = list.map(function (it) {
      return '<li><a href="issues/' + encodeURIComponent(it.id) + '.html"><span class="no">제' + esc(it.no) + '호</span>' +
        '<span class="tt">' + esc(it.title) + '</span><span class="ct">' + esc(it.count) + '건 · ' + esc(it.date) + '</span></a></li>';
    }).join('');
    document.getElementById('noissue').hidden = true;
    document.getElementById('latest').href = 'issues/' + encodeURIComponent(list[0].id) + '.html';
  }).catch(function () {});
})();
