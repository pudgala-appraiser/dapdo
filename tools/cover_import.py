#!/usr/bin/env python3
"""위원이 준 모션 드로잉 HTML(획을 좌표로 담은 형식)에서 첫 화면 그림의 획 자료를 꺼낸다.
사용: python3 tools/cover_import.py <드로잉.html>

꺼내는 것: assets/sangju_cover.bin
  획 하나마다 [점 개수(2바이트), 굵기×40(1), 농도×255(1), 시작 시각×10ms(2), 끝 시각×10ms(2), 좌표×8(점마다 x·y 2바이트씩)]가
  '확정 순서'대로 이어진다. 이 순서대로 다 그은 것이 완성 소묘이고, assets/home.js가 시각에 맞춰 긋는다.

캔버스 크기가 첫 화면의 틀(index.html의 캔버스, dapdo.css의 .stage, home.js의 SH)과 다르면 멈춘다.
스크립트를 끈 환경에서 보이는 정지 그림(assets/sangju_cover.png)은 완성 화면을 받아 따로 넣는다.
꺼낸 뒤에는 tools/version.py로 판 번호를 올린다."""
import sys, os, re, base64, struct

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) < 2: sys.exit(__doc__)
s = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r'var DATA = "([A-Za-z0-9+/=]+)"', s)
if not m: sys.exit("오류: 파일에서 획 자료(DATA)를 찾지 못했다")
b = base64.b64decode(m.group(1))
m = re.search(r'<canvas id="base" width="(\d+)" height="(\d+)"', s)
if not m: sys.exit("오류: 캔버스 크기를 찾지 못했다")
W, H = int(m.group(1)), int(m.group(2))
if (W, H) != (2431, 1256):
    sys.exit("오류: 캔버스가 %dx%d다. index.html의 캔버스 크기, dapdo.css의 .stage 높이, home.js의 SH를 함께 고쳐야 한다" % (W, H))
o = n = 0; end = 0.0
while o < len(b):
    if o + 8 > len(b): sys.exit("오류: 획 자료가 중간에 끊겼다")
    k, w, a, t0, t1 = struct.unpack_from("<HBBHH", b, o); o += 8 + 4 * k
    if k < 1 or t1 < t0 or o > len(b): sys.exit("오류: %d번째 획이 잘못됐다" % n)
    n += 1; end = max(end, t1 / 10)
open(os.path.join(root, "assets", "sangju_cover.bin"), "wb").write(b)
print("꺼냄: 획 %d개, %d바이트, 그리는 시간 %.1f초, 캔버스 %dx%d" % (n, len(b), end / 1000, W, H))
