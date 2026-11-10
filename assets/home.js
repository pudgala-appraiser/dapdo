// 답도 메인: 화면 폭에 맞춰 그림(경주 남산리 서삼층석탑 동면 야차·용)을 줄이고, 지난 호 목록을 읽어 온다.
(function () {
  var hero = document.getElementById('hero'), box = document.getElementById('stagebox');
  function fit() {
    var w = hero.clientWidth, narrow = w < 820;
    hero.classList.toggle('narrow', narrow);
    var k = narrow ? w / 1120 : w / 1280;
    hero.style.setProperty('--k', k);
    box.style.height = ((narrow ? 480 : 600) * k) + 'px';
  }
  fit();
  window.addEventListener('resize', fit);
  // 첫 화면 그림은 한 번만 재생되는 GIF다. 다시 그릴 때는 받아 둔 파일로 새 주소를 만들어 처음부터 돌린다.
  var cover = document.getElementById('cover'), gif = cover.getAttribute('src'), blob = null, obj = null;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) cover.src = cover.getAttribute('data-still');
  fetch(gif).then(function (r) { return r.ok ? r.blob() : null; }).then(function (b) { blob = b; }).catch(function () {});
  document.getElementById('replay').addEventListener('click', function () {
    if (!blob) { cover.src = gif + '?r=' + Date.now(); return; }
    if (obj) URL.revokeObjectURL(obj);
    obj = URL.createObjectURL(blob); cover.src = obj;
  });
  function esc(s) { var d = document.createElement('div'); d.textContent = s == null ? '' : String(s); return d.innerHTML; }
  fetch('issues.json', { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : []; }).then(function (list) {
    if (!list || !list.length) return;
    list.sort(function (a, b) { return a.id < b.id ? 1 : -1; });
    var ol = document.getElementById('issues');
    ol.innerHTML = list.map(function (it) {
      return '<li><a href="issues/' + encodeURIComponent(it.id) + '.html"><span class="no">' + esc(it.label || ('제' + it.no + '호')) + '</span>' +
        '<span class="tt">' + esc(it.title) + '</span><span class="ct">' + esc(it.count) + '건 · ' + esc(it.date) + '</span></a></li>';
    }).join('');
    document.getElementById('noissue').hidden = true;
    document.getElementById('latest').href = 'issues/' + encodeURIComponent(list[0].id) + '.html';
  }).catch(function () {});
})();
