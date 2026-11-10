#!/usr/bin/env python3
"""호 자료(JSON)를 검사해 issues/<id>.html을 만들고 issues.json을 고친다.
사용: python3 tools/build_issue.py data/issues/2026-11.json [--no-index] [--allow-dup] [--allow-drop]
- 필수 항목이 비었거나 링크가 http(s)로 시작하지 않으면 멈춘다.
- 앞선 호에 이미 실은 문헌이 있으면 멈춘다(--allow-dup으로 넘길 수 있다). 같은 호 안에서 겹쳐도 멈춘다.
  겹침은 제목이 같거나 주소 속 식별 번호(DOI·arXiv·JAKO·KCI ART 등)가 같을 때로 본다. 목차 주소는 여러 논문이 함께 쓰므로 주소만으로는 가리지 않는다.
- 저자를 확인하지 못한 문헌은 학술지명(『 』)이나 식별 번호가 든 주소(DOI·arXiv 등) 가운데 하나는 있어야 싣는다.
- 자료에 "updated"가 있으면 발행일 옆에 보탠 날을 함께 적는다. 첫 화면(index.html)의 지난 호 목록과 '이번 호' 링크도 함께 고친다.
- id가 test로 시작하거나 --no-index를 주면 issues.json(지난 호 목록)은 건드리지 않는다.
- 자료에 "label"이 있으면 "제N호" 대신 그 이름을 쓴다(예: 창간호, "no": 1). 다음 호 번호는 가장 큰 no에 1을 더한다.
- 답도는 홀수 달(1·3·5·7·9·11월) 15일에 내는 격월간이다. 호의 id는 발행한 달(YYYY-MM)이다.
- 꼬리말의 운영자 옆에 틀의 판 번호와 날짜(data/version.json)를 적는다. 첫 화면 꼬리말의 판 번호도 함께 고친다.
- 자료에 "special"(특집 묶음)이 있으면 네 부문 뒤에 학술지별 제목 목록으로 싣는다. 특집의 문헌도 겹침 검사와 건수에 들어간다.
- 저장소에 이미 올라간 같은 호 자료(git HEAD)에 실려 있던 문헌이 새 자료에서 빠지면 멈춘다. 제목을 바로잡았거나 잘못 실린 문헌을 뺀 것이면 --allow-drop으로 넘긴다."""
import json, sys, os, re, html, glob, subprocess

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECTIONS = [("art", "一", "불교미술·미술사"), ("heritage", "二", "문화유산학·법제"), ("science", "三", "AI·과학과 문화유산"), ("books", "四", "신간")]
FLAGS = {"초록만 확인", "목차만 확인", "서지 검증 필요", "본문 미확인", "원제 미확인"}
LEGEND = [("초록만 확인", "은 본문을 보지 못하고 초록으로 쓴 요지"), ("목차만 확인", "은 목차에서 서지만 확인한 문헌"), ("서지 검증 필요", "는 원문 DB에서 서지를 끝까지 대조하지 못한 문헌"),
          ("본문 미확인", "은 책을 보지 못하고 출판사 소개 등으로 쓴 신간"), ("원제 미확인", "은 한국어 원제를 찾지 못해 영문 제목으로 실은 국내 논문")]
CATS = [("art", "국내 · 미술사·불교미술·고고학 학술지"), ("other", "국내 · 그 밖의 학술지"), ("intl", "해외 · 한국미술·신중상 관련 글")]
DEEP = [("material", "자료"), ("method", "방법"), ("significance", "의의"), ("limits", "한계")]
IDENT = [r"(10\.\d{4,9}/[^\s?#]+)", r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", r"(JAKO\d{6,})", r"(ART\d{6,})", r"abstract_id=(\d+)", r"/pii/(S\w+)",
         r"mdpi\.com/(\d{4}-\d{4}/\d+/\d+/\d+)", r"nature\.com/articles/([\w.-]+)"]
e = lambda s: html.escape(str(s if s is not None else ""), quote=True)
norm = lambda s: re.sub(r"[\W_]+", "", str(s or "")).lower()

def ident(url):
    """주소에서 문헌을 가리키는 번호를 뽑는다. 없으면 빈 문자열."""
    for rx in IDENT:
        m = re.search(rx, str(url or ""), re.I)
        if m: return m.group(1).lower().rstrip("/.")
    return ""

def keys(it):
    """겹침을 가리는 열쇠: 제목(여섯 자 이상일 때)과 주소 속 식별 번호."""
    t = norm(it.get("title")); k = ["t:" + t] if len(t) >= 6 else []
    i = ident(it.get("url"))
    return k + (["i:" + i] if i else [])

def version():
    """틀의 판 번호와 날짜(data/version.json). 파일이 없으면 빈 문자열."""
    try:
        V = json.load(open(os.path.join(root, "data", "version.json"), encoding="utf-8"))
        return "%s · %s" % (V["version"], V["date"])
    except Exception:
        return ""

def fail(msg):
    print("오류: " + msg); sys.exit(1)

def check_item(it, where, need_summary):
    for k in ("title", "venue", "url"):
        if not str(it.get(k, "")).strip(): fail("%s: '%s' 비어 있음 — %s" % (where, k, it.get("title", "")[:40]))
    if not re.match(r"https?://", it["url"]): fail("%s: 링크가 http(s)로 시작하지 않음 — %s" % (where, it["url"]))
    if need_summary and not str(it.get("summary", "")).strip() and not it.get("deep"): fail("%s: 요지 없음 — %s" % (where, it["title"][:40]))
    if not str(it.get("authors", "")).strip() and "『" not in it["venue"] and not ident(it["url"]):
        fail("%s: 저자가 비면 학술지명(『 』)이나 식별 번호가 든 주소(DOI·arXiv 등)가 있어야 한다 — %s" % (where, it["title"][:40]))
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

def all_items(X):
    """호 자료에 실린 문헌 전부(네 부문의 items·more와 특집 묶음)."""
    out = []
    for s in X.get("sections", []): out += s.get("items", []) + s.get("more", [])
    for g in (X.get("special") or {}).get("groups", []): out += g.get("items", [])
    return out

def write_home(idx):
    """첫 화면의 지난 호 목록과 '이번 호' 링크를 고친다(스크립트 없이도 목록이 보이게)."""
    p = os.path.join(root, "index.html")
    if not os.path.exists(p): return
    h = open(p, encoding="utf-8").read()
    m = re.search(r"<!--issues:start-->.*?<!--issues:end-->", h, re.S)
    if not m: print("주의: index.html에 목록 표지(<!--issues:start-->)가 없어 첫 화면은 고치지 않았다."); return
    rows = sorted(idx, key=lambda x: x["id"], reverse=True)
    li = "\n".join('<li><a href="issues/%s.html"><span class="no">%s</span><span class="tt">%s</span><span class="ct">%s건 · %s</span></a></li>'
                   % (e(x["id"]), e(x.get("label") or "제%s호" % x["no"]), e(x["title"]), e(x["count"]), e(x["date"])) for x in rows)
    block = "<!--issues:start-->\n" + ('<ol id="issues">\n%s\n</ol>' % li if rows else '<ol id="issues"></ol>\n<p id="noissue">아직 발행한 호가 없습니다.</p>') + "\n<!--issues:end-->"
    h = h[:m.start()] + block + h[m.end():]
    if version(): h = re.sub(r"<!--ver:start-->.*?<!--ver:end-->", lambda k: "<!--ver:start--> | %s<!--ver:end-->" % e(version()), h, flags=re.S)
    if rows: h = re.sub(r'(id="latest" href=")[^"]*(")', lambda k: k.group(1) + "issues/%s.html" % rows[0]["id"] + k.group(2), h)
    open(p, "w", encoding="utf-8").write(h)

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
        for it in all_items(P):
            for k in keys(it): seen[k] = P["id"]
    dups, n_items, n_deep, local, used = [], 0, 0, {}, set()
    def track(it):
        used.update(it.get("flags", []))
        ks = keys(it)
        for k in ks:
            if k in local: fail("같은 호 안에서 겹치는 문헌: %s ↔ %s" % (it["title"][:50], local[k][:50]))
        for k in ks: local[k] = it["title"]
        for k in ks:
            if k in seen: dups.append("%s ← %s호에 이미 실림" % (it["title"][:50], seen[k])); break
    for key, num, name in SECTIONS:
        s = secs.get(key) or {}
        for it in s.get("items", []):
            check_item(it, name, True); n_items += 1; n_deep += 1 if it.get("deep") else 0
        for it in s.get("more", []):
            check_item(it, name + "(목록)", False); n_items += 1
        for it in s.get("items", []) + s.get("more", []): track(it)
    SP = D.get("special") or {}
    n_special = 0
    for g in SP.get("groups", []):
        if g.get("cat") not in [c for c, _ in CATS]: fail("특집: 알 수 없는 묶음 구분 cat '%s' — %s" % (g.get("cat"), g.get("journal")))
        if not str(g.get("journal", "")).strip(): fail("특집: 학술지 이름(journal) 없음")
        for it in g.get("items", []):
            check_item(dict(it, venue=it.get("venue") or "『%s』 %s" % (g["journal"], g.get("issue", ""))), "특집(%s)" % g["journal"], False)
            n_special += 1; track(it)
    n_items += n_special
    # 이미 올라간 같은 호 자료에 있던 문헌이 빠지지 않았는지 본다
    if not test and "--allow-drop" not in opts:
        try:
            rel = os.path.relpath(os.path.abspath(args[0]), root).replace(os.sep, "/")
            r = subprocess.run(["git", "-C", root, "show", "HEAD:" + rel], capture_output=True, text=True)
            O = json.loads(r.stdout) if r.returncode == 0 else None
        except Exception:
            O = None
        if O:
            now = set(k for it in all_items(D) for k in keys(it))
            gone = [it.get("title", "") for it in all_items(O) if keys(it) and not any(k in now for k in keys(it))]
            if gone: fail("앞서 실은 문헌 %d건이 자료에서 빠졌다(되살리거나, 정당한 사유가 있으면 --allow-drop):\n  " % len(gone) + "\n  ".join(t[:60] for t in gone[:8]))
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
    w('<link rel="icon" type="image/png" sizes="32x32" href="../assets/favicon-32.png">\n<link rel="icon" type="image/png" sizes="192x192" href="../assets/favicon-192.png">\n<link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">')
    w('<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    w('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;700;800&amp;family=Noto+Sans+KR:wght@400;700&amp;display=swap">')
    w('<link rel="stylesheet" href="../assets/dapdo.css">\n</head>\n<body class="issue">')
    w('<header class="wrap" id="top">\n<div class="topbar"><a class="cap" href="../">踏道 · BIMONTHLY REVIEW OF SCHOLARSHIP</a><span>%s · %s</span></div>' % (e(label), e(D["title"])))
    w('<div class="mast">\n<div>\n<div class="mast-art" id="mast-art" role="img" aria-label="연필로 그린 경주 장항리 서오층석탑 1층 탑신 북면. 가운데 문비에 귀면 문고리 한 쌍이 있고, 좌우 연화좌 위에 금강역사가 한 구씩 서 있다."></div>')
    w('<p class="figcap">경주 장항리 서오층석탑 · 1층 탑신 북면</p>\n</div>')
    w('<div class="mast-ttl">\n<div class="h"><h1>답도</h1><span class="seal">隔月刊</span></div>\n<p class="sub">불교미술·문화유산 연구 성과 격월간</p>')
    added = (" · %s 보탬" % e(D["updated"])) if D.get("updated") and D["updated"] != D["date"] else ""
    w('<p class="no">%s · %s 발행%s</p>\n<ul class="toc">' % (e(label), e(D["date"]), added))
    for key, num, name in SECTIONS:
        s = secs.get(key) or {}
        c = len(s.get("items", [])) + len(s.get("more", []))
        w('<li><a href="#%s"><b>%s</b>%s<i>%s</i></a></li>' % (key, num, e(name), ("%d건" % c) if c else "신규 없음"))
    if n_special: w('<li><a href="#special"><b>特</b>%s<i>%d건</i></a></li>' % (e(SP.get("title") or "특집"), n_special))
    w('</ul>\n<div><button class="ghost" id="replay" type="button">다시 그리기</button></div>\n</div>\n</div>\n</header>')
    deep = [(name, it) for key, num, name in SECTIONS for it in (secs.get(key) or {}).get("items", []) if it.get("deep")]
    # 따라다니는 목차: 화면을 내려도 위에 붙어 있다
    w('<nav class="pin" id="pin" aria-label="목차"><div class="pin-in">\n<a class="up" href="#top">답도 <span aria-hidden="true">↑</span></a>')
    if deep: w('<a href="#h-deep">눈여겨볼 연구</a>')
    for key, num, name in SECTIONS:
        w('<a href="#%s"><b>%s</b>%s</a>' % (key, num, e(name)))
    if n_special: w('<a href="#special"><b>特</b>특집</a>')
    if D.get("checked"): w('<a href="#h-chk">점검한 학술지</a>')
    w('</div></nav>')
    w('<main class="body">\n<p class="lead">%s</p>' % e(D["lead"]))
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
            w('<p class="none">이번 호 신규 없음.</p>')
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
    if n_special:
        w('<section class="special" aria-labelledby="special">\n<h2 id="special"><b>特</b>특집 · %s</h2>' % e(SP.get("title") or "특집"))
        if SP.get("lead"): w('<p class="splead">%s</p>' % e(SP["lead"]))
        for cat, cname in CATS:
            gs = [g for g in SP.get("groups", []) if g.get("cat") == cat and g.get("items")]
            if not gs: continue
            w('<h3 class="cat">%s <i>%d건</i></h3>' % (e(cname), sum(len(g["items"]) for g in gs)))
            order = []
            for g in gs:
                if g["journal"] not in order: order.append(g["journal"])
            for jn in order:
                js = [g for g in gs if g["journal"] == jn]
                w('<details class="more"><summary>『%s』 — %s%d건</summary>' % (e(jn), ("%d개 호 " % len(js)) if len(js) > 1 else "", sum(len(g["items"]) for g in js)))
                for g in js:
                    if g.get("issue"): w('<p class="iss">%s</p>' % e(g["issue"]))
                    w('<ul>')
                    for it in g["items"]:
                        w('<li>%s%s%s</li>' % (title_html(it), ('<br><span class="m">%s</span>' % e(it["authors"])) if it.get("authors") else "",
                                               ('<br><span class="s">%s</span>' % e(it["summary"])) if it.get("summary") else ""))
                    w('</ul>')
                w('</details>')
        cov = SP.get("coverage") or []
        if cov:
            w('<details><summary>특집에서 조사한 호 %d개 — 결과 보기</summary>\n<div class="tblbox"><table class="chk"><thead><tr><th>학술지</th><th>호</th><th>결과</th></tr></thead><tbody>' % len(cov))
            for c in cov:
                w('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (e(c.get("journal")), e(c.get("issue", "")), e(c.get("status", ""))))
            w('</tbody></table></div>\n</details>')
        w('</section>')
    if D.get("checked"):
        w('<section aria-labelledby="h-chk">\n<h2 id="h-chk">이번 호에 점검한 학술지</h2>\n<details><summary>%d종 펼쳐 보기</summary>\n<div class="tblbox"><table class="chk"><thead><tr><th>학술지</th><th>확인한 호</th><th>결과</th></tr></thead><tbody>' % len(D["checked"]))
        for c in D["checked"]:
            w('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (e(c.get("journal")), e(c.get("issue", "")), e(c.get("status", ""))))
        w('</tbody></table></div>\n</details>\n</section>')
    w('</main>\n<footer>\n<p>본문은 AI(Claude)가 공개된 서지와 초록을 바탕으로 엮었습니다. 요지는 원문을 대신하지 않으니, 인용하기 전에 원문을 확인해 주십시오.</p>')
    lg = ["‘%s’%s" % (f, t) for f, t in LEGEND if f in used]
    if lg: w('<p>%s입니다.</p>' % e(", ".join(lg)))
    w('<p>%s운영자: 한재원%s</p>' % (('엮은 모델: %s | ' % e(D["model"])) if D.get("model") else '', (' | %s' % e(version())) if version() else ''))
    w('<p><a href="../">답도 첫 화면</a></p>\n</footer>\n<script src="../assets/mast.js"></script>\n<script src="../assets/pin.js"></script>\n</body>\n</html>')
    os.makedirs(os.path.join(root, "issues"), exist_ok=True)
    open(os.path.join(root, "issues", iid + ".html"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    if not test:
        entry = {"id": iid, "no": no, "title": D["title"], "date": D["date"], "count": n_items}
        if issue_label: entry["label"] = issue_label
        idx = [x for x in idx if x["id"] != iid] + [entry]
        idx.sort(key=lambda x: x["id"])
        json.dump(idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        write_home(idx)
    if n_deep > 5: print("주의: 정밀 요약이 %d건이다(한 호에 3~5건)." % n_deep)
    print("완료: issues/%s.html — %s, 문헌 %d건(정밀 요약 %d건%s)%s%s" % (iid, label, n_items, n_deep, (", 특집 %d건 포함" % n_special) if n_special else "", ", 지난 호 목록 갱신" if not test else ", 지난 호 목록은 그대로", (", 중복 경고 %d건" % len(dups)) if dups else ""))

if __name__ == "__main__":
    main()
