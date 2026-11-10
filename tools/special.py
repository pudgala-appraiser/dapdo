#!/usr/bin/env python3
"""창간호 특집 '2026년 연간 목록'의 사전 조사를 돕는다.
사용:
  python3 tools/special.py status                      남은 일과 실린 건수
  python3 tools/special.py next [N]                    다음에 조사할 일 N개(기본 6)
  python3 tools/special.py merge <결과.json> [오늘]     조사 결과를 호 자료의 special에 합치고 대기열 상태를 고친다
  python3 tools/special.py portal <포털 복제 경로> [--keep 번호,번호,…]
                                                       불교학 포털의 그해 논문 후보를 번호와 함께 보이거나, 고른 번호를 싣는다
대기열은 data/special.json, 실리는 곳은 data/issues/<issue>.json 의 "special" 이다.

merge에 넘기는 결과 파일:
{"tasks":  [{"id": "t03", "status": "done | none | notfound", "issue": "329호 (2026.3)"}],
 "groups": [{"task": "t03", "journal": "미술사학연구", "issue": "329호 (2026.3)",
             "items": [{"authors": "저자", "title": "원제", "url": "https://…", "flags": [], "summary": "(골라낸 글에만) 한두 문장"}]}]}
- status: done=실을 논문을 찾아 실음, none=목차를 확인했으나 실을 논문이 없음, notfound=목차를 확인하지 못함.
- 해외 글은 groups에 {"cat": "intl", "journal": "학술지", "issue": "권호 (연도)", "items": [… "title_ko": "번역 제목" …]}로 넣는다.
- 이미 호에 실린 문헌(제목이나 주소 속 식별 번호가 같은 것)은 건너뛰고 알려 준다."""
import json, sys, os, re, glob, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_issue import keys, all_items, FLAGS

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QP = os.path.join(root, "data", "special.json")
J = json.load(open(os.path.join(root, "data", "journals.json"), encoding="utf-8"))
Q = json.load(open(QP, encoding="utf-8"))
IP = os.path.join(root, "data", "issues", Q["issue"] + ".json")
STATUS = {"done": "확인", "none": "관련 논문 없음", "notfound": "목차 미확인"}
ORDER = [j["name"] for j in J["file"]] + list(J["portal"])
ARTS = set(j["name"] for j in J["file"] if j["mode"] == "all") | set(J["portal_all"])

def dump(path, obj):
    json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def cat_of(journal):
    return "art" if journal in ARTS else ("other" if journal in ORDER else "intl")

def sort_groups(gs):
    co = {"art": 0, "other": 1, "intl": 2}
    return sorted(gs, key=lambda g: (co.get(g.get("cat"), 9), ORDER.index(g["journal"]) if g["journal"] in ORDER else 999,
                                     g["journal"], g.get("pub", ""), g.get("issue", "")))

def add_groups(D, groups, pubs):
    """groups를 D["special"]에 합친다. (보탠 건수, 건너뛴 제목들)을 돌려준다."""
    S = D.setdefault("special", {})
    S.setdefault("title", "%d년 연간 목록" % Q["year"]); S.setdefault("groups", [])
    have = set(k for it in all_items(D) for k in keys(it))
    added, skipped = 0, []
    for g in groups:
        jn = str(g.get("journal", "")).strip()
        if not jn: sys.exit("오류: groups에 journal이 비었다")
        cat = g.get("cat") or cat_of(jn)
        tgt = next((x for x in S["groups"] if x["journal"] == jn and x.get("issue", "") == g.get("issue", "")), None)
        if not tgt:
            tgt = {"cat": cat, "journal": jn, "issue": g.get("issue", ""), "pub": g.get("pub") or pubs.get(g.get("task"), ""), "items": []}
            S["groups"].append(tgt)
        for it in g.get("items", []):
            for k in ("title", "url"):
                if not str(it.get(k, "")).strip(): sys.exit("오류: %s — '%s' 비어 있음: %s" % (jn, k, str(it.get("title", ""))[:40]))
            if not re.match(r"https?://", it["url"]): sys.exit("오류: 링크가 http(s)로 시작하지 않음 — " + it["url"])
            for f in it.get("flags", []):
                if f not in FLAGS: sys.exit("오류: 허용되지 않은 표시 '%s'" % f)
            ks = keys(it)
            if any(k in have for k in ks): skipped.append(it["title"]); continue
            have.update(ks)
            tgt["items"].append({k: it[k] for k in ("authors", "title", "title_ko", "url", "summary", "flags") if it.get(k)})
            added += 1
    S["groups"] = sort_groups([g for g in S["groups"] if g["items"]])
    return added, skipped

def coverage():
    return [{"journal": t.get("journal") or t.get("name", ""), "issue": t.get("issue") or (t.get("pub", "")[:7].replace("-", ".") + " 발간호" if t.get("pub") else ""),
             "status": STATUS[t["status"]]} for t in Q["tasks"] if t["status"] in STATUS]

def cmd_status():
    D = json.load(open(IP, encoding="utf-8"))
    gs = (D.get("special") or {}).get("groups", [])
    c = {}
    for t in Q["tasks"]: c[t["status"]] = c.get(t["status"], 0) + 1
    print("대기열 %d건 — 남음 %d, 실음 %d, 관련 논문 없음 %d, 목차 미확인 %d" % (len(Q["tasks"]), c.get("todo", 0), c.get("done", 0), c.get("none", 0), c.get("notfound", 0)))
    print("특집에 실린 문헌 %d건 (학술지 %d종)" % (sum(len(g["items"]) for g in gs), len(set(g["journal"] for g in gs))))

def cmd_next(n):
    todo = [t for t in Q["tasks"] if t["status"] == "todo"]
    print("# 남은 일 %d건 가운데 %d건 — 위에서부터 차례로 한다" % (len(todo), min(n, len(todo))))
    info = {j["name"]: j for j in J["file"]}
    for t in todo[:n]:
        if t["kind"] == "search":
            print("- %s | 검색 과제 | %s" % (t["id"], t["name"]))
        else:
            j = info.get(t["journal"], {})
            print("- %s | %s | %s | 발간일 %s%s | %s%s%s" % (t["id"], t["journal"], j.get("publisher", ""), t["pub"], " (추정)" if j.get("est") else "",
                  "전 논문 목록" if t["mode"] == "all" else "관련 논문만", (" | 목차 틀 " + j["toc"]) if j.get("toc") else "", (" | " + j["note"]) if j.get("note") else ""))

def cmd_merge(path, today):
    A = json.load(open(path, encoding="utf-8"))
    D = json.load(open(IP, encoding="utf-8"))
    byid = {t["id"]: t for t in Q["tasks"]}
    for t in A.get("tasks", []):
        if t["id"] not in byid: sys.exit("오류: 대기열에 없는 id — " + str(t["id"]))
        if t["status"] not in STATUS: sys.exit("오류: status는 done·none·notfound 가운데 하나 — " + str(t["status"]))
    pubs = {t["id"]: t.get("pub", "") for t in Q["tasks"]}
    added, skipped = add_groups(D, A.get("groups", []), pubs)
    for t in A.get("tasks", []):
        q = byid[t["id"]]; q["status"] = t["status"]; q["checked"] = today
        if t.get("issue"): q["issue"] = t["issue"]
        if t.get("note"): q["note"] = t["note"]
    D["special"]["coverage"] = coverage()
    if D.get("date") != today: D["updated"] = today
    dump(IP, D); dump(QP, Q)
    print("합침: 문헌 %d건 보탬, 이미 실려 건너뜀 %d건, 과제 %d건 상태 고침" % (added, len(skipped), len(A.get("tasks", []))))
    for s in skipped[:10]: print("  · 건너뜀: " + s[:70])
    cmd_status()

def cmd_portal(P, keep):
    K = json.load(open(os.path.join(root, "data", "keywords.json"), encoding="utf-8"))
    rx = re.compile(K["portal_filter"], re.I)
    D = json.load(open(IP, encoding="utf-8"))
    have = set(k for it in all_items(D) for k in keys(it))
    cands = []
    for jn in J["portal"]:
        fs = glob.glob(os.path.join(P, "output", "*_%s.json" % jn))
        if not fs: continue
        arts = [a for a in json.load(open(fs[0], encoding="utf-8"))["articles"] if str(a.get("year")) == str(Q["year"])]
        num = lambda x: int(re.sub(r"\D", "", str(x or "")) or 0)
        arts.sort(key=lambda a: (num(a.get("volume")), num(a.get("issue")), num(a.get("start_page"))))
        for a in arts:
            url = a.get("kci_url") or a.get("riss_url") or a.get("doi") or ""
            it = {"authors": ", ".join(p["name"] for p in a.get("authors", [])), "title": (a.get("title_kr") or a.get("title_en") or "").strip(), "url": url}
            if not it["title"] or not re.match(r"https?://", url) or any(k in have for k in keys(it)): continue
            text = " ".join([a.get("title_kr", ""), a.get("title_en", ""), " ".join(a.get("keywords_kr", []))])
            if not (jn in J["portal_all"] or rx.search(text)): continue
            v, i = str(a.get("volume", "") or ""), str(a.get("issue", "") or "")
            label = ((v if v not in ("", "0") else "") + (("(%s)" % i) if i and v not in ("", "0") else i)) + " (%s)" % Q["year"]
            cands.append((jn, label, it, a))
    if keep is None:
        print("# 후보 %d건 — 번호 | 학술지 권호 | 제목 | 주제어" % len(cands))
        for n, (jn, label, it, a) in enumerate(cands, 1):
            print("%d|%s %s|%s|%s" % (n, jn, label.split(" (")[0], it["title"][:90], ",".join(a.get("keywords_kr", [])[:4])[:50]))
        return
    groups = {}
    for n in keep:
        jn, label, it, a = cands[n - 1]
        groups.setdefault((jn, label), {"journal": jn, "issue": label, "items": []})["items"].append(it)
    added, skipped = add_groups(D, list(groups.values()), {})
    dump(IP, D)
    print("포털: 문헌 %d건 보탬, 건너뜀 %d건" % (added, len(skipped)))

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "status": cmd_status()
    elif a[0] == "next": cmd_next(int(a[1]) if len(a) > 1 else 6)
    elif a[0] == "merge": cmd_merge(a[1], a[2] if len(a) > 2 else datetime.date.today().isoformat())
    elif a[0] == "portal":
        keep = None
        if "--keep" in a: keep = [int(x) for x in a[a.index("--keep") + 1].split(",") if x.strip()]
        cmd_portal(a[1], keep)
    else: sys.exit(__doc__)
