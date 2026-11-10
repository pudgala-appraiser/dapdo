#!/usr/bin/env python3
"""이번 호에 확인할 국내 학술지(파일 34종)를 발간 달력으로 가린다.
사용: python3 tools/due.py [오늘 YYYY-MM-DD]
state.json의 file_checked[학술지] 다음 날부터 오늘까지 발간일이 든 학술지를 출력한다.
답도는 홀수 달 15일에 내는 격월간이다. cadence가 quarterly인 학술지(역사 계열)는 한 해 네 번,
3·6·9·12월 말 발간분이 걸리는 1·5·7·11월 실행에서만 확인 대상으로 낸다(3·9월 실행에서는 건너뛴다)."""
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
due, idle, later = [], [], []
quarter_month = today.month in (1, 5, 7, 11)
for j in J['file']:
    since = datetime.date.fromisoformat(S['file_checked'].get(j['name'], base.isoformat()))
    hits = sorted(dt for y in (today.year - 1, today.year) for md in j['pub'] for dt in [clamp(y, md)] if since < dt <= today)
    if hits and j.get('cadence') == 'quarterly' and not quarter_month:
        later.append((j, hits))
    else:
        (due if hits else idle).append((j, hits))
# 미술사 전문지(전 논문 목록)를 먼저 본다
due.sort(key=lambda jh: 0 if jh[0]['mode'] == 'all' else 1)
print('# 확인 대상 %d종 (기준일 %s) — 위에서부터 차례로 본다' % (len(due), today))
for j, hits in due:
    print('- %s | %s | 발간일 %s%s | %s%s' % (j['name'], j['publisher'], ', '.join(h.isoformat() for h in hits), ' (추정)' if j.get('est') else '',
          '전 논문 목록' if j['mode'] == 'all' else '관련 논문만', ' | ' + j['note'] if j.get('note') else ''))
print('# 분기 점검 대상이라 이번 호는 건너뜀 %d종(1·5·7·11월 실행에서 확인): %s' % (len(later), ', '.join(j['name'] for j, _ in later)))
print('# 이번 호 기간에 발간 예정 없음 %d종: %s' % (len(idle), ', '.join(j['name'] for j, _ in idle)))
