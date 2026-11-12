// 답도 호 쪽 머리 그림: 경주 장항리 서오층석탑 1층 탑신 북면 부조 소묘(위원 제공)를 연필로 빗금을 긋듯 그린다.
// 그림은 assets/janghangri_north.png 하나다(밝기 = 연필 농도). 픽셀마다 나타나는 때를 여기서 정한다:
// 진한 선 → 중간 톤 → 옅은 결, 세 번에 걸쳐 방향이 다른 빗금으로, 구역마다 획을 나란히 그어 간다.
(function () {
  var box = document.getElementById('mast-art'); if (!box) return;
  var cv = box.querySelector('canvas'), btn = document.getElementById('replay');
  if (!cv || !cv.getContext) return;
  var W = 664, H = 560, N = W * H;
  var DUR = 3000, DELAY = 250, SOFT = 0.015; // 그리는 시간(ms), 바닥선 뒤 기다림(ms), 획 끝이 번지는 정도
  var LAYERS = [ // 빗금 방향(도), 획 너비, 획 길이 최소·최대, 구역의 획 수, 구역 길이, 시작·끝(0~1), 대상 순서의 비중
    [35, 13, 110, 170, 8, 170, 0.00, 0.60, 0.62],  // 진한 선: 문 → 왼쪽 역사 → 오른쪽 역사
    [-50, 11, 90, 150, 8, 150, 0.26, 0.86, 0.50],  // 중간 톤
    [80, 9, 80, 130, 9, 140, 0.50, 1.00, 0.00]];   // 옅은 결: 여기저기
  var PDUR = 0.11, still = window.matchMedia('(prefers-reduced-motion: reduce)');
  var ctx = cv.getContext('2d'), out = ctx.createImageData(W, H), o = out.data, M = null, T = null, raf = 0, t0 = 0;

  function rnd(a) { return function () { a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function hash(i) { i = Math.imul(i ^ i >>> 16, 0x45d9f3b); i = Math.imul(i ^ i >>> 16, 0x45d9f3b); return ((i ^ i >>> 16) >>> 0) / 4294967296; }
  function maxf(src, r) { // 둘레 r픽셀 안의 가장 진한 값
    var a = new Uint8Array(N), b = new Uint8Array(N), x, y, k, m, v;
    for (y = 0; y < H; y++) for (x = 0; x < W; x++) { m = 0; for (k = x - r < 0 ? 0 : x - r; k <= x + r && k < W; k++) { v = src[y * W + k]; if (v > m) m = v; } a[y * W + x] = m; }
    for (y = 0; y < H; y++) for (x = 0; x < W; x++) { m = 0; for (k = y - r < 0 ? 0 : y - r; k <= y + r && k < H; k++) { v = a[k * W + x]; if (v > m) m = v; } b[y * W + x] = m; }
    return b;
  }
  function plan() { // 픽셀마다 나타나는 때(0~1)를 정한다
    var m5 = maxf(M, 2), m3 = maxf(M, 1), pid = new Int32Array(N), loc = new Float32Array(N), lay = new Uint8Array(N), R = rnd(23), l, i;
    for (i = 0; i < N; i++) lay[i] = m5[i] >= 96 ? 0 : m3[i] >= 40 ? 1 : 2;
    T = new Float32Array(N);
    for (l = 0; l < 3; l++) {
      var L = LAYERS[l], th = L[0] * Math.PI / 180, c = Math.cos(th), s = Math.sin(th), w = L[1], nb = L[4], pu = L[5], ph = R() * 6.28;
      var us = [0, W * c, H * s, W * c + H * s], vs = [0, -W * s, H * c, -W * s + H * c];
      var umin = Math.min.apply(0, us), vmin = Math.min.apply(0, vs) - 3, nband = Math.ceil((Math.max.apply(0, vs) + 3 - vmin) / w) + 1;
      var ln = [], off = [], rev = [], b;
      for (b = 0; b < nband; b++) { ln.push(L[2] + R() * (L[3] - L[2])); off.push(R() * L[3]); rev.push(R() < 0.3); }
      var keys = {}, score = [], x, y;
      for (y = 0; y < H; y++) for (x = 0; x < W; x++) {
        i = y * W + x; if (lay[i] !== l || !M[i]) continue;
        var u = x * c + y * s, v = -x * s + y * c + 2.2 * Math.sin(u / 41 + ph);
        b = Math.floor((v - vmin) / w); if (b < 0) b = 0; else if (b >= nband) b = nband - 1;
        var q = (u - umin + off[b]) / ln[b], sg = Math.floor(q), p = q - sg, pb = Math.floor(b / nb), ps = Math.floor(((sg + 0.5) * ln[b] - off[b]) / pu) + 8, key = pb * 4096 + ps, k = keys[key];
        if (k === undefined) { // 새 구역: 가운데의 x로 문·왼쪽 역사·오른쪽 역사를 가린다
          var cx = ((ps - 8 + 0.5) * pu + umin) * c - ((pb + 0.5) * nb * w + vmin) * s;
          k = keys[key] = score.length; score.push(L[8] * (cx >= 200 && cx < 445 ? 0 : cx < 200 ? 0.42 : 0.8) + (1 - L[8]) * R());
        }
        pid[i] = k;
        var ud = ln[b] / 2600; if (ud < 0.03) ud = 0.03; else if (ud > 0.065) ud = 0.065;
        loc[i] = ((b % nb) / nb) * (PDUR - 0.065) + hash(b * 100003 + sg + l * 7919) * 0.012 + (rev[b] ? 1 - p : p) * ud + (hash(i) - 0.5) * 0.008;
      }
      var n = score.length, ord = [], st = new Float32Array(n);
      for (i = 0; i < n; i++) ord.push(i);
      ord.sort(function (a, z) { return score[a] - score[z]; });
      for (i = 0; i < n; i++) st[ord[i]] = L[6] + (n > 1 ? i / (n - 1) : 0) * (L[7] - L[6] - PDUR);
      for (i = 0; i < N; i++) if (lay[i] === l && M[i]) T[i] = st[pid[i]] + loc[i];
    }
  }
  function paint(t) {
    for (var i = 0, j = 3; i < N; i++, j += 4) { var m = M[i]; if (!m) continue; var v = (t - T[i]) / SOFT; o[j] = v <= 0 ? 0 : v >= 1 ? m : m * v; }
    ctx.putImageData(out, 0, 0);
  }
  function frame(now) {
    var t = (now - t0 - DELAY) / DUR;
    if (t > 1 + SOFT) { paint(9); raf = 0; return; }
    paint(t); raf = requestAnimationFrame(frame);
  }
  function draw() {
    if (!T) return;
    if (raf) cancelAnimationFrame(raf); raf = 0;
    box.classList.remove('running');
    if (still.matches) { paint(9); return; }
    box.getBoundingClientRect(); box.classList.add('running');
    t0 = performance.now(); raf = requestAnimationFrame(frame);
  }
  var img = new Image();
  img.onload = function () {
    var c = document.createElement('canvas'); c.width = W; c.height = H;
    var x = c.getContext('2d'), d, i, j;
    x.drawImage(img, 0, 0, W, H);
    try { d = x.getImageData(0, 0, W, H).data; } catch (e) { return; }
    M = new Uint8Array(N);
    for (i = 0, j = 0; i < N; i++, j += 4) { M[i] = d[j]; o[j] = o[j + 1] = o[j + 2] = 50; }
    plan(); draw();
  };
  img.src = cv.getAttribute('data-src');
  if (btn) { btn.disabled = still.matches; btn.addEventListener('click', draw); }
  if (still.addEventListener) still.addEventListener('change', function () { if (btn) btn.disabled = still.matches; draw(); });
})();
