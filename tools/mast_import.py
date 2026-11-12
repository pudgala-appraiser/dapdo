#!/usr/bin/env python3
"""위원이 준 모션 드로잉 HTML에서 호 쪽 머리 그림의 자료를 꺼낸다.
사용: python3 tools/mast_import.py <드로잉.html>

꺼내는 것은 셋이다.
- assets/janghangri_north.png        완성 그림(회색조, 밝기 = 연필 농도)
- assets/janghangri_north_score.png  획 순서표. 점 하나가 기록 하나다: 빨강·초록 = 앞 픽셀과의 간격(16비트), 파랑 = 얹는 흑연의 양
- assets/mast_score.js               프레임 경계(offsets)와 그리는 시간(ms)

순서표를 끝까지 재생한 결과가 완성 그림과 한 픽셀도 다르지 않은지 확인한 뒤에 쓴다.
그림의 크기·기울기가 쪽의 양식(assets/dapdo.css)과 다르면 멈춘다. 꺼낸 뒤에는 tools/version.py로 판 번호를 올린다."""
import sys, os, re, base64, json, io

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) < 2: sys.exit(__doc__)
s = open(sys.argv[1], encoding="utf-8").read()

def need(pat, what, flags=0):
    m = re.search(pat, s, flags)
    if not m: sys.exit("오류: 파일에서 %s을(를) 찾지 못했다" % what)
    return m

mask = base64.b64decode(need(r'<mask[^>]*>\s*<image[^>]*href="data:image/png;base64,([A-Za-z0-9+/=]+)"', "완성 그림").group(1))
score = base64.b64decode(need(r'id="stroke-score"[^>]*>\s*([A-Za-z0-9+/=]+)\s*</script>', "획 순서표").group(1))
offs = [int(x) for x in need(r'const offsets = \[([0-9,\s]+)\]', "프레임 경계").group(1).split(",")]
fps = float(need(r'scoreFramesPerSecond = ([0-9.]+)', "프레임 속도").group(1))
rate = float(need(r'playbackRate = ([0-9.]+)', "재생 배속").group(1))
m = need(r'<canvas[^>]*width="(\d+)"[^>]*height="(\d+)"', "캔버스 크기")
W, H = int(m.group(1)), int(m.group(2))
view = need(r'viewBox="([^"]+)"', "viewBox").group(1)
rot = need(r'transform:\s*rotate\(([-0-9.]+)deg\)', "기울기").group(1)

# 쪽의 양식이 전제하는 값(dapdo.css의 .jh-cv, build_issue.py의 정지 그림)
if (W, H, view, rot) != (664, 560, "-20 -10 704 582", "-1.1"):
    sys.exit("오류: 그림 틀이 다르다(캔버스 %dx%d, viewBox %s, 기울기 %s도). dapdo.css의 .jh-cv와 build_issue.py의 머리 그림을 함께 고쳐야 한다" % (W, H, view, rot))
if any(b < a for a, b in zip(offs, offs[1:])) or offs[0] != 0: sys.exit("오류: 프레임 경계가 차례대로가 아니다")

try:
    import numpy as np
    from PIL import Image
except ImportError:
    print("알림: numpy·Pillow가 없어 순서표와 완성 그림의 대조를 건너뛴다")
else:
    mk = Image.open(io.BytesIO(mask)); sc = Image.open(io.BytesIO(score))
    if mk.size != (W, H): sys.exit("오류: 완성 그림 크기가 %s다" % (mk.size,))
    if sc.mode != "RGB" or sc.info: sys.exit("오류: 순서표는 색 정보가 붙지 않은 RGB PNG여야 한다(%s, %s)" % (sc.mode, list(sc.info)))
    rec = np.asarray(sc).reshape(-1, 3).astype(np.int64)
    if len(rec) < offs[-1]: sys.exit("오류: 순서표가 프레임 경계보다 짧다")
    acc = np.zeros(W * H, np.int64)
    for a, b in zip(offs, offs[1:]):
        if b > a:
            r = rec[a:b]; pix = np.cumsum((r[:, 0] << 8) + r[:, 1])
            if pix[-1] >= W * H: sys.exit("오류: 순서표가 그림 밖을 가리킨다")
            np.add.at(acc, pix, r[:, 2])
    want = np.asarray(mk.convert("L")).astype(np.int64).ravel()
    if acc.max() > 255 or (acc != want).any():
        sys.exit("오류: 순서표를 끝까지 재생한 결과가 완성 그림과 다르다(%d픽셀)" % int((acc != want).sum()))
    print("대조: 순서표를 끝까지 재생하면 완성 그림과 같다(기록 %d개)" % offs[-1])

nf = len(offs) - 1
ms = round(nf / (fps * rate) * 1000)
A = os.path.join(root, "assets")
open(os.path.join(A, "janghangri_north.png"), "wb").write(mask)
open(os.path.join(A, "janghangri_north_score.png"), "wb").write(score)
with open(os.path.join(A, "mast_score.js"), "w", encoding="utf-8") as f:
    f.write("// tools/mast_import.py가 만든 파일이다. 손으로 고치지 않는다.\n")
    f.write("window.DAPDO_MAST=" + json.dumps({"w": W, "h": H, "ms": ms, "offsets": offs}, separators=(",", ":")) + ";\n")
print("꺼냄: 완성 그림 %d바이트, 순서표 %d바이트, %d프레임, 그리는 시간 %.1f초" % (len(mask), len(score), nf, ms / 1000))
