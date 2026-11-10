#!/usr/bin/env python3
"""틀(화면·도구)을 고쳤을 때 판 번호를 올리고 모든 호 쪽을 다시 만든다.
사용: python3 tools/version.py v0.17 [YYYY-MM-DD]
판 번호와 날짜의 정본은 data/version.json이고, 쪽의 표시는 tools/build_issue.py가 그 값으로 써 넣는다.
호 발행·사전 조사 같은 예약 실행은 이 도구를 쓰지 않는다(판 번호는 틀을 고칠 때만 오른다)."""
import json, sys, os, glob, subprocess, datetime
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) < 2: sys.exit(__doc__)
ver = sys.argv[1]
date = sys.argv[2] if len(sys.argv) > 2 else datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
p = os.path.join(root, "data", "version.json")
V = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
V.update(version=ver, date=date)
json.dump(V, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for f in sorted(glob.glob(os.path.join(root, "data", "issues", "*.json"))):
    i = os.path.basename(f)[:-5]
    if i.startswith("test") or i == "sample": continue
    if subprocess.run([sys.executable, os.path.join(root, "tools", "build_issue.py"), f]).returncode: sys.exit("오류: %s 쪽을 만들지 못했다" % i)
print("판 번호: %s · %s" % (ver, date))
