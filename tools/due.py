#!/usr/bin/env python3
"""이달 확인할 국내 학술지(파일 30종)를 발간 달력으로 가린다.
사용: python3 tools/due.py [오늘 YYYY-MM-DD]
state.json의 file_checked[학술지] 다음 날부터 오늘까지 발간일이 든 학술지를 출력한다."""
import json, sys, datetime, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = json.load(open(os.path.join(root, 'data', 'journals.json'), encoding='utf-8'))
S = json.load(open(os.path.join(root, 'data', 'state.json'), encoding='utf-8'))
today = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.date.today()
base = datetime.date.fromisoformat(S.get('baseline', '2026-08-31'))
def clamp(y, md):
    m, d = map(int, md.split('-'))
    while True:
        try: return datetime.date(y, m, d)
        except ValueError: d -= 1
due, idle = [], []
for j in J['file']:
    since = datetime.date.fromisoformat(S['file_checked'].get(j['name'], base.isoformat()))
    hits = sorted(dt for y in (today.year - 1, today.year) for md in j['pub'] for dt in [clamp(y, md)] if since < dt <= today)
    (due if hits else idle).append((j, hits))
print('# 확인 대상 %d종 (기준일 %s)' % (len(due), today))
for j, hits in due:
    print('- %s | %s | 발간일 %s%s | %s%s' % (j['name'], j['publisher'], ', '.join(h.isoformat() for h in hits), ' (추정)' if j.get('est') else '',
          '전 논문 목록' if j['mode'] == 'all' else '관련 논문만', ' | ' + j['note'] if j.get('note') else ''))
print('# 이달 발간 예정 없음 %d종: %s' % (len(idle), ', '.join(j['name'] for j, _ in idle)))
