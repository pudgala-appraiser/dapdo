// 답도 호 쪽 머리 그림: 경주 장항리 서오층석탑 1층 탑신 북면 부조 소묘(위원 제공)를 연필로 그려 나간다.
// 그리는 차례는 획 순서표(assets/janghangri_north_score.png)에 들어 있다. 프레임마다 어느 픽셀에 흑연을 얼마나
// 얹는지가 적혀 있고, 끝까지 얹으면 완성 그림(assets/janghangri_north.png)과 같아진다.
// 순서표와 프레임 경계(assets/mast_score.js)는 위원이 준 모션 드로잉에서 tools/mast_import.py로 꺼낸다.
(function () {
  var box = document.getElementById('mast-art'); if (!box) return;
  var cv = box.querySelector('canvas'), btn = document.getElementById('replay'), S = window.DAPDO_MAST;
  if (!cv || !cv.getContext || !S) return;
  var SPEED = 1; // 1이면 순서표에 적힌 속도(약 4.8초), 2면 두 배 빠르게
  var W = S.w, H = S.h, off = S.offsets, NF = off.length - 1;
  var still = window.matchMedia('(prefers-reduced-motion: reduce)');
  var ctx = cv.getContext('2d'); if (!ctx) return;
  var out = ctx.createImageData(W, H), o = out.data;
  var dep = null, wait = null, done = -1, raf = 0, run = 0, playing = false, elapsed = 0, last = null;

  function pixels(src, ok, fail) { // 그림 파일을 읽어 픽셀 값을 돌려준다
    var img = new Image();
    img.onerror = fail;
    img.onload = function () {
      try {
        var c = document.createElement('canvas'); c.width = img.naturalWidth; c.height = img.naturalHeight;
        var g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(img, 0, 0);
        ok(g.getImageData(0, 0, c.width, c.height).data);
      } catch (e) { fail(); }
    };
    img.src = src;
  }
  function score(ok, fail) { // 순서표는 한 번만 읽는다
    if (dep) return ok();
    if (wait) return wait.push([ok, fail]);
    wait = [[ok, fail]];
    pixels(cv.getAttribute('data-score'), function (d) {
      var w = wait, good = d.length >= off[NF] * 4; wait = null; if (good) dep = d;
      w.forEach(function (f) { f[good ? 0 : 1](); });
    }, function () { var w = wait; wait = null; w.forEach(function (f) { f[1](); }); });
  }
  function blank() {
    for (var i = 0; i < o.length; i += 4) { o[i] = o[i + 1] = o[i + 2] = 50; o[i + 3] = 0; }
    ctx.clearRect(0, 0, W, H); done = -1;
  }
  function lay(until) { // until 프레임까지의 획을 얹는다
    var lo = W * H, hi = -1, n, end, p, a;
    while (done < until) {
      done++; end = off[done + 1] * 4; p = 0;
      for (n = off[done] * 4; n < end; n += 4) {
        p += (dep[n] << 8) + dep[n + 1]; a = dep[n + 2];
        if (a) { o[p * 4 + 3] += a; if (p < lo) lo = p; if (p > hi) hi = p; }
      }
    }
    if (hi >= lo) { var top = Math.floor(lo / W); ctx.putImageData(out, 0, 0, 0, top, W, Math.floor(hi / W) - top + 1); }
  }
  function whole() { // 완성 그림을 바로 보인다(동작 줄이기 설정, 순서표를 읽지 못했을 때)
    var mine = run;
    pixels(cv.getAttribute('data-still'), function (d) {
      if (mine !== run) return;
      blank(); for (var i = 0; i < W * H; i++) o[i * 4 + 3] = d[i * 4];
      ctx.putImageData(out, 0, 0);
    }, function () {});
  }
  function stop() { playing = false; cancelAnimationFrame(raf); }
  function tick(now) {
    if (!playing || document.hidden) return;
    if (last !== null) elapsed += now - last;
    last = now;
    var f = Math.min(NF - 1, Math.floor(elapsed * SPEED / S.ms * NF));
    lay(f);
    if (f === NF - 1) stop(); else raf = requestAnimationFrame(tick);
  }
  function draw() {
    var mine = ++run; stop();
    if (btn) btn.disabled = still.matches;
    if (still.matches) return whole();
    blank();
    score(function () {
      if (mine !== run) return;
      elapsed = 0; last = null; playing = true;
      if (!document.hidden) raf = requestAnimationFrame(tick);
    }, function () { if (mine === run) whole(); });
  }

  // 다른 탭에 갔다 오면 멈춘 획부터 잇는다
  document.addEventListener('visibilitychange', function () {
    cancelAnimationFrame(raf); last = null;
    if (!document.hidden && playing) raf = requestAnimationFrame(tick);
  });
  if (btn) btn.addEventListener('click', draw);
  if (still.addEventListener) still.addEventListener('change', draw);
  draw();
})();
