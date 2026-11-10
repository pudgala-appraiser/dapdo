#!/usr/bin/env python3
"""불교학논문 통합검색 저장소에서 새로 등록된 호의 논문을 뽑는다.
사용: python3 tools/portal_new.py <buddhist-studies-portal 복제 경로>
state.json의 portal_since 뒤에 등록된 호만 본다. 불교미술 3종은 전 논문, 나머지는 검색어에 걸린 논문만 초록과 함께 내고,
걸리지 않은 논문은 제목만 낸다(제목을 훑어 빠진 것이 없는지 확인하는 용도)."""
import json, sys, os, re, glob
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = sys.argv[1]
S = json.load(open(os.path.join(root, 'data', 'state.json'), encoding='utf-8'))
J = json.load(open(os.path.join(root, 'data', 'journals.json'), encoding='utf-8'))
K = json.load(open(os.path.join(root, 'data', 'keywords.json'), encoding='utf-8'))
since = S.get('portal_since', '2026-09-25')
rx = re.compile(K['portal_filter'], re.I)
ups = [u for u in json.load(open(os.path.join(P, 'output', 'updates.json'), encoding='utf-8'))['updates'] if u['date'] > since]
issues = {}
for u in ups:
    issues.setdefault((u['journal'], str(u['year']), str(u.get('volume', '')), str(u.get('issue', ''))), []).append(u['date'])
print('# 포털 신규 등록 호 %d건 (%s 이후)' % (len(issues), since))
def load(name):
    for f in glob.glob(os.path.join(P, 'output', '*_%s.json' % name)):
        return json.load(open(f, encoding='utf-8'))['articles']
    return []
for (jn, y, v, i), dates in sorted(issues.items(), key=lambda kv: min(kv[1])):
    arts = [a for a in load(jn) if str(a.get('year')) == y and str(a.get('volume', '')) == v and str(a.get('issue', '')) == i]
    allmode = jn in J['portal_all']
    print('\n## %s %s (%s) — 등록 %s — 논문 %d편%s' % (jn, (v if v not in ('', '0') else '') + ('(%s)' % i if i and v not in ('', '0') else i), y, min(dates), len(arts), ' — 전 논문' if allmode else ''))
    rest = []
    for a in arts:
        text = ' '.join([a.get('title_kr', ''), a.get('title_en', ''), ' '.join(a.get('keywords_kr', [])), ' '.join(a.get('keywords_en', [])), a.get('abstract_kr', '')])
        if allmode or rx.search(text):
            print('- 제목: %s' % a.get('title_kr', ''))
            print('  저자: %s' % ', '.join(p['name'] for p in a.get('authors', [])))
            print('  쪽: %s-%s | 링크: %s' % (a.get('start_page', ''), a.get('end_page', ''), a.get('kci_url') or a.get('riss_url') or a.get('doi') or ''))
            if a.get('keywords_kr'): print('  주제어: %s' % ', '.join(a['keywords_kr']))
            ab = (a.get('abstract_kr') or a.get('abstract_en') or '').replace('\n', ' ')
            print('  초록: %s' % (ab[:900] if ab else '(없음)'))
        else:
            rest.append(a.get('title_kr', ''))
    if rest:
        print('  · 검색어에 걸리지 않은 제목: ' + ' / '.join(rest))
