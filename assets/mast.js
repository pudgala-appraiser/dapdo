// 답도 호 쪽 머리 그림: 경주 장항리 서오층석탑 1층 탑신 북면 부조 소묘(위원 제공).
// 그림과 움직임은 쪽의 SVG와 dapdo.css에 있고(약 3초), 여기서는 '다시 그리기'만 맡는다.
(function () {
  var el = document.getElementById('mast-art'), b = document.getElementById('replay');
  if (!el) return;
  var still = window.matchMedia('(prefers-reduced-motion: reduce)');
  function draw() {
    el.classList.remove('running');
    if (!still.matches) { el.getBoundingClientRect(); el.classList.add('running'); }
  }
  function apply() { if (b) b.disabled = still.matches; }
  if (b) b.addEventListener('click', draw);
  if (still.addEventListener) still.addEventListener('change', function () { apply(); draw(); });
  apply();
})();
