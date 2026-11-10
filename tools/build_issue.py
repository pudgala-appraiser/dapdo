#!/usr/bin/env python3
"""월호 자료(JSON)를 검사해 issues/<id>.html을 만들고 issues.json을 고친다.
사용: python3 tools/build_issue.py data/issues/2026-11.json [--no-index] [--allow-dup]
- 필수 항목이 비었거나 링크가 http(s)로 시작하지 않으면 멈춘다.
- 앞선 호에 이미 실은 문헌(같은 링크 또는 같은 제목)이 있으면 멈춘다(--allow-dup으로 넘길 수 있다).
- id가 test로 시작하거나 --no-index를 주면 issues.json(지난 호 목록)은 건드리지 않는다.
- 자료에 "label"이 있으면 "제N호" 대신 그 이름을 쓴다(예: 창간 준비호, "no": 0). 다음 호 번호는 가장 큰 no에 1을 더한다."""
import json, sys, os, re, html, glob

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECTIONS = [("art", "一", "불교미술·미술사"), ("heritage", "二", "문화유산학·법제"), ("science", "三", "AI·과학과 문화유산"), ("books", "四", "신간")]
FLAGS = {"초록만 확인", "목차만 확인", "서지 검증 필요", "본문 미확인"}
DEEP = [("material", "자료"), ("method", "방법"), ("significance", "의의"), ("limits", "한계")]
e = lambda s: html.escape(str(s if s is not None else ""), quote=True)
norm = lambda s: re.sub(r"[\W_]+", "", str(s or "")).lower()

def fail(msg):
    print("오류: " + msg); sys.exit(1)

def check_item(it, where, need_summary):
    for k in ("title", "venue", "url"):
        if not str(it.get(k, "")).strip(): fail("%s: '%s' 비어 있음 — %s" % (where, k, it.get("title", "")[:40]))
    if not re.match(r"https?://", it["url"]): fail("%s: 링크가 http(s)로 시작하지 않음 — %s" % (where, it["url"]))
    if need_summary and not str(it.get("summary", "")).strip() and not it.get("deep"): fail("%s: 요지 없음 — %s" % (where, it["title"][:40]))
    for f in it.get("flags", []):
        if f not in FLAGS: fail("%s: 허용되지 않은 표시 '%s' (허용: %s)" % (where, f, ", ".join(sorted(FLAGS))))
    d = it.get("deep")
    if d:
        if not str(d.get("thesis", "")).strip(): fail("%s: 정밀 요약에 핵심 논지(thesis) 없음 — %s" % (where, it["title"][:40]))

def title_html(it):
    t = '<a href="%s" rel="noopener">%s</a>' % (e(it["url"]), e(it["title"]))
    if it.get("title_ko"): t += ' <span class="ko">(%s)</span>' % e(it["title_ko"])
    t += "".join('<span class="flag">%s</span>' % e(f) for f in it.get("flags", []))
    return t

def meta(it):
    return " · ".join(x for x in (e(it.get("authors", "")), e(it["venue"])) if x)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = set(a for a in sys.argv[1:] if a.startswith("--"))
    if not args: fail("자료 파일 경로가 필요함")
    D = json.load(open(args[0], encoding="utf-8"))
    for k in ("id", "title", "date", "lead", "sections"):
        if not D.get(k): fail("최상위 '%s' 없음" % k)
    iid = D["id"]
    if not re.match(r"^[0-9a-z-]+$", iid): fail("id는 영문 소문자·숫자·붙임표만: " + iid)
    test = iid.startswith("test") or "--no-index" in opts
    secs = {s["key"]: s for s in D["sections"]}
    for k in secs:
        if k not in [x[0] for x in SECTIONS]: fail("알 수 없는 부문 key: " + k)
    seen = {}
    for f in glob.glob(os.path.join(root, "data", "issues", "*.json")):
        if os.path.abspath(f) == os.path.abspath(args[0]): continue
        try: P = json.load(open(f, encoding="utf-8"))
        except Exception: continue
        if str(P.get("id", "")).startswith("test") or str(P.get("id", "")) == "sample": continue
        for s in P.get("sections", []):
            for it in s.get("items", []) + s.get("more", []):
                seen[norm(it.get("url"))] = P["id"]; seen[norm(it.get("title"))] = P["id"]
    dups, n_items, n_deep = [], 0, 0
    for key, num, name in SECTIONS:
        s = secs.get(key) or {}
        for it in s.get("items", []):
            check_item(it, name, True); n_items += 1; n_deep += 1 if it.get("deep") else 0
        for it in s.get("more", []):
            check_item(it, name + "(목록)", False); n_items += 1
        for it in s.get("items", []) + s.get("more", []):
            for k in (norm(it["url"]), norm(it["title"])):
                if k and k in seen: dups.append("%s ← %s호에 이미 실림" % (it["title"][:50], seen[k])); break
    if dups and "--allow-dup" not in opts and not test:
        fail("앞선 호와 겹치는 문헌 %d건:\n  " % len(dups) + "\n  ".join(dups))
    idx_path = os.path.join(root, "issues.json")
    idx = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else []
    prev = next((x for x in idx if x["id"] == iid), None)
    no = D["no"] if "no" in D else (prev["no"] if prev else (max([x["no"] for x in idx] or [0]) + 1))
    issue_label = D.get("label") or (prev or {}).get("label")
    label = "시험호" if test else (issue_label or "제%s호" % no)

    out = []
    w = out.append
    w('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">')
    w('<title>답도 踏道 %s — %s</title>' % (e(label), e(D["title"])))
    w('<meta name="description" content="%s">' % e(D["lead"][:150]))
    if test: w('<meta name="robots" content="noindex">')
    w('<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    w('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;700;800&amp;family=Noto+Sans+KR:wght@400;700&amp;display=swap">')
    w('<link rel="stylesheet" href="../assets/dapdo.css">\n</head>\n<body class="issue">')
    w('<header class="wrap">\n<div class="topbar"><a class="cap" href="../">踏道 · MONTHLY REVIEW OF SCHOLARSHIP</a><span>%s · %s</span></div>' % (e(label), e(D["title"])))
    w('<div class="mast">\n<div>\n<div class="mast-art" id="mast-art" role="img" aria-label="연필로 그린 경주 장항리 서오층석탑 1층 탑신 북면. 가운데 문비에 귀면 문고리 한 쌍이 있고, 좌우 연화좌 위에 금강역사가 한 구씩 서 있다."></div>')
    w('<p class="figcap">경주 장항리 서오층석탑 · 1층 탑신 북면</p>\n</div>')
    w('<div class="mast-ttl">\n<div class="h"><h1>답도</h1><span class="seal">月報</span></div>\n<p class="sub">불교미술·문화유산 연구 성과 월보</p>')
    w('<p class="no">%s · %s 발행</p>\n<ul class="toc">' % (e(label), e(D["date"])))
    for key, num, name in SECTIONS:
        s = secs.get(key) or {}
        c = len(s.get("items", [])) + len(s.get("more", []))
        w('<li><a href="#%s"><b>%s</b>%s<i>%s</i></a></li>' % (key, num, e(name), ("%d건" % c) if c else "신규 없음"))
    w('</ul>\n<div><button class="ghost" id="replay" type="button">다시 그리기</button></div>\n</div>\n</div>\n</header>')
    w('<main class="body">\n<p class="lead">%s</p>' % e(D["lead"]))
    deep = [(name, it) for key, num, name in SECTIONS for it in (secs.get(key) or {}).get("items", []) if it.get("deep")]
    if deep:
        w('<section aria-labelledby="h-deep">\n<h2 id="h-deep">눈여겨볼 연구</h2>')
        for name, it in deep:
            d = it["deep"]
            w('<article class="deep">\n<h3>%s</h3>\n<p class="meta">%s · %s</p>' % (title_html(it), meta(it), e(name)))
            w('<blockquote>%s</blockquote>\n<dl>' % e(d["thesis"]))
            for k, lab in DEEP:
                if str(d.get(k, "")).strip(): w('<dt>%s</dt><dd>%s</dd>' % (lab, e(d[k])))
            w('</dl>\n</article>')
        w('</section>')
    for key, num, name in SECTIONS:
        s = secs.get(key) or {}
        w('<section aria-labelledby="%s">\n<h2 id="%s"><b>%s</b>%s</h2>' % (key, key, num, e(name)))
        plain = [it for it in s.get("items", []) if not it.get("deep")]
        refd = [it for it in s.get("items", []) if it.get("deep")]
        if not s.get("items") and not s.get("more"):
            w('<p class="none">이번 달 신규 없음.</p>')
        for it in plain:
            w('<article class="item">\n<h3>%s</h3>\n<p class="meta">%s</p>\n<p class="sum">%s</p>\n</article>' % (title_html(it), meta(it), e(it.get("summary", ""))))
        if refd:
            w('<p class="none">위 ‘눈여겨볼 연구’에 실은 %d건: %s</p>' % (len(refd), " / ".join(e(it["title"]) for it in refd)))
        if s.get("more"):
            w('<details class="more"><summary>그 밖의 수록 문헌 %d건 (제목만)</summary>\n<ul>' % len(s["more"]))
            for it in s["more"]:
                w('<li>%s<br><span class="m">%s</span></li>' % (title_html(it), meta(it)))
            w('</ul>\n</details>')
        w('</section>')
    if D.get("checked"):
        w('<section aria-labelledby="h-chk">\n<h2 id="h-chk">이달 점검한 학술지</h2>\n<details><summary>%d종 펼쳐 보기</summary>\n<div class="tblbox"><table class="chk"><thead><tr><th>학술지</th><th>확인한 호</th><th>결과</th></tr></thead><tbody>' % len(D["checked"]))
        for c in D["checked"]:
            w('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (e(c.get("journal")), e(c.get("issue", "")), e(c.get("status", ""))))
        w('</tbody></table></div>\n</details>\n</section>')
    w('</main>\n<footer>\n<p>본문은 AI(Claude)가 공개된 서지와 초록을 바탕으로 엮었습니다. 요지는 원문을 대신하지 않으니, 인용하기 전에 원문을 확인해 주십시오.</p>')
    w('<p>‘초록만 확인’은 본문을 보지 못하고 초록으로 쓴 요지, ‘목차만 확인’은 목차에서 서지만 확인한 문헌, ‘서지 검증 필요’는 원문 DB에서 서지를 끝까지 대조하지 못한 문헌입니다.</p>')
    if D.get("model"): w('<p>엮은 모델: %s</p>' % e(D["model"]))
    w('<p><a href="../">답도 첫 화면</a></p>\n</footer>\n<script src="../assets/mast.js"></script>\n</body>\n</html>')
    os.makedirs(os.path.join(root, "issues"), exist_ok=True)
    open(os.path.join(root, "issues", iid + ".html"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    if not test:
        entry = {"id": iid, "no": no, "title": D["title"], "date": D["date"], "count": n_items}
        if issue_label: entry["label"] = issue_label
        idx = [x for x in idx if x["id"] != iid] + [entry]
        idx.sort(key=lambda x: x["id"])
        json.dump(idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("완료: issues/%s.html — %s, 문헌 %d건(정밀 요약 %d건)%s%s" % (iid, label, n_items, n_deep, ", 지난 호 목록 갱신" if not test else ", 지난 호 목록은 그대로", (", 중복 경고 %d건" % len(dups)) if dups else ""))

main()
