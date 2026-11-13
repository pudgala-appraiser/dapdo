// 답도 첫 화면: 화면 폭에 맞춰 그림 칸을 줄이고, 상주 석조천인상 연필 소묘(위원 제공)를 획 차례대로 긋는다.
// 지난 호 목록은 tools/build_issue.py가 index.html에 써 넣는다. 획 자료(assets/sangju_cover.bin)는 tools/cover_import.py가 꺼낸다.
(function () {
  var hero = document.getElementById('hero'), box = document.getElementById('stagebox');
  var SH = 579; // 그림 칸의 높이(너비 1120일 때). 그림 비율은 2431:1256
  function fit() {
    var w = hero.clientWidth, narrow = w < 820;
    hero.classList.toggle('narrow', narrow);
    var k = narrow ? w / 1120 : w / 1280;
    hero.style.setProperty('--k', k);
    box.style.height = ((narrow ? SH : 600) * k) + 'px';
  }
  fit();
  window.addEventListener('resize', fit);

  var base = document.getElementById('cover'), live = document.getElementById('cover-live'), btn = document.getElementById('replay');
  function fallback() { // 그리지 못하면 정지 그림을 보인다
    var img = new Image(); img.className = 'cover'; img.alt = ''; img.src = base.getAttribute('data-still');
    base.parentNode.insertBefore(img, base); base.style.display = live.style.display = 'none'; if (btn) btn.disabled = true;
  }
  var gb = base.getContext && base.getContext('2d'), gl = live.getContext && live.getContext('2d');
  if (!gb || !gl || !window.fetch || !window.DataView) return fallback();
  var INK = '52,52,57', W = base.width, H = base.height, S = [], N = 0, order = [];
  var still = window.matchMedia('(prefers-reduced-motion: reduce)');
  gb.lineCap = gl.lineCap = 'round'; gb.lineJoin = gl.lineJoin = 'round';

  function parse(buf) { // 획마다 [점 개수, 굵기, 농도, 시작 시각, 끝 시각, 좌표…]가 확정 순서대로 들어 있다
    var dv = new DataView(buf), o = 0, n, s, k, j;
    while (o < buf.byteLength) {
      n = dv.getUint16(o, true);
      s = { n: n, w: dv.getUint8(o + 2) / 40, c: 'rgba(' + INK + ',' + (dv.getUint8(o + 3) / 255).toFixed(3) + ')',
            t0: dv.getUint16(o + 4, true) / 10, t1: dv.getUint16(o + 6, true) / 10, p: new Float32Array(n * 2), L: new Float32Array(n), done: false };
      o += 8;
      for (k = 0; k < n * 2; k++) { s.p[k] = dv.getInt16(o, true) / 8; o += 2; }
      for (j = 1; j < n; j++) s.L[j] = s.L[j - 1] + Math.sqrt(Math.pow(s.p[2 * j] - s.p[2 * j - 2], 2) + Math.pow(s.p[2 * j + 1] - s.p[2 * j - 1], 2));
      S.push(s);
    }
    N = S.length;
    order = S.map(function (_, i) { return i; }).sort(function (a, b) { return S[a].t0 - S[b].t0 || a - b; });
  }
  function stroke(g, s, len) { // 획 하나를 처음부터 len 길이만큼 긋는다
    var p = s.p, L = s.L, n = s.n, i = 1, f;
    g.strokeStyle = s.c; g.lineWidth = s.w; g.beginPath(); g.moveTo(p[0], p[1]);
    if (len >= L[n - 1]) { for (; i < n; i++) g.lineTo(p[2 * i], p[2 * i + 1]); }
    else {
      for (; i < n && L[i] <= len; i++) g.lineTo(p[2 * i], p[2 * i + 1]);
      f = (len - L[i - 1]) / (L[i] - L[i - 1] || 1);
      g.lineTo(p[2 * i - 2] + (p[2 * i] - p[2 * i - 2]) * f, p[2 * i - 1] + (p[2 * i + 1] - p[2 * i - 1]) * f);
    }
    g.stroke();
  }
  function whole() { // 완성 소묘: 모든 획을 확정 순서대로 긋는다. 재생의 끝 화면도 같은 과정을 거친 결과다
    gb.clearRect(0, 0, W, H); gl.clearRect(0, 0, W, H);
    for (var i = 0; i < N; i++) { stroke(gb, S[i], Infinity); S[i].done = true; }
  }
  var raf = 0, playing = false, elapsed = 0, last = null, ci = 0, ai = 0, active = [];
  function frame(now) {
    if (!playing || document.hidden) return;
    if (last !== null) elapsed += now - last;
    last = now;
    var t = elapsed, i, s, keep = [];
    while (ai < N && S[order[ai]].t0 <= t) active.push(order[ai++]);
    while (ci < N && S[ci].t1 <= t) { stroke(gb, S[ci], Infinity); S[ci].done = true; ci++; } // 다 그은 획은 바탕 캔버스에 확정
    gl.clearRect(0, 0, W, H);
    for (i = 0; i < active.length; i++) {
      s = S[active[i]];
      if (s.done) continue;
      keep.push(active[i]);
      stroke(gl, s, s.L[s.n - 1] * (t - s.t0) / ((s.t1 - s.t0) || 1)); // 긋는 중인 획은 위 캔버스에
    }
    active = keep;
    if (ci < N) raf = requestAnimationFrame(frame); else playing = false;
  }
  function play() {
    cancelAnimationFrame(raf); playing = false;
    if (btn) btn.disabled = still.matches;
    if (still.matches) return whole(); // 동작 줄이기 설정이면 완성 화면을 바로 보인다
    for (var i = 0; i < N; i++) S[i].done = false;
    gb.clearRect(0, 0, W, H); gl.clearRect(0, 0, W, H);
    elapsed = 0; last = null; ci = 0; ai = 0; active = []; playing = true;
    if (!document.hidden) raf = requestAnimationFrame(frame);
  }
  // 다른 탭에 갔다 오면 멈춘 데서 잇는다
  document.addEventListener('visibilitychange', function () {
    cancelAnimationFrame(raf); last = null;
    if (!document.hidden && playing) raf = requestAnimationFrame(frame);
  });
  fetch(base.getAttribute('data-strokes')).then(function (r) { if (!r.ok) throw 0; return r.arrayBuffer(); }).then(function (buf) {
    parse(buf);
    if (btn) btn.addEventListener('click', play);
    if (still.addEventListener) still.addEventListener('change', play);
    play();
  }).catch(fallback);
})();
