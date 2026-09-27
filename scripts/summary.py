"""랩 업무일지 요약 메일 — Supabase `docs` 테이블을 읽어 하나의 표(업무 종류 | 총 시간 | 인원 | 사람별 시간 | 퀘스트)로 정리해 Gmail SMTP로 보낸다.
Usage: python summary.py day|week|month   (env: SUPABASE_URL, SUPABASE_ANON_KEY, GMAIL_USER, GMAIL_APP_PASSWORD, MAIL_TO, MAIL_TO_REPORT, PAGE_URL)"""
import os, sys, json, datetime, smtplib, urllib.request, urllib.parse, collections
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from zoneinfo import ZoneInfo

period = sys.argv[1] if len(sys.argv) > 1 else 'day'
URL, KEY = os.environ['SUPABASE_URL'].rstrip('/'), os.environ['SUPABASE_ANON_KEY']
TO = [x.strip() for x in os.environ.get('MAIL_TO', 'dayoung@kist.re.kr').split(',') if x.strip()]
if period in ('week', 'month'):  # 주간·월간 보고만 받는 추가 수신자
    TO += [x for x in (y.strip() for y in os.environ.get('MAIL_TO_REPORT', '').split(',')) if x and x not in TO]
PAGE = os.environ.get('PAGE_URL', '')

def fetch(col, extra=''):
    q = f"{URL}/rest/v1/docs?collection=eq.{col}&select=id,data&limit=5000{extra}"
    req = urllib.request.Request(q, headers={'apikey': KEY, 'Authorization': 'Bearer ' + KEY})
    return json.load(urllib.request.urlopen(req, timeout=60))

today = datetime.datetime.now(ZoneInfo('Asia/Seoul')).date()
if period == 'day':
    f = t = today; label = f"{today:%Y-%m-%d} ({'월화수목금토일'[today.weekday()]}) 일간"
elif period == 'week':
    t = today; f = today - datetime.timedelta(days=6); label = f"{f:%m/%d} – {t:%m/%d} 주간"  # 금요일 발송 → 지난 토–이번 금
else:
    f = today.replace(day=1); t = today; label = f"{f:%Y년 %m월} 월간"  # 말일 발송 → 이번 달

members = {m['id']: m['data'] for m in fetch('members')}
types = {x['id']: x['data'] for x in fetch('taskTypes')}
days = fetch('days', f"&data->>date=gte.{f.isoformat()}&data->>date=lte.{t.isoformat()}")

rows = []
for d in days:
    dd = d['data']
    for r in dd.get('rows', []):
        rows.append(dict(date=dd['date'], member=members.get(dd.get('memberId'), {}).get('name', '?'),
                         type=types.get(r.get('typeId'), {}).get('name', '?'), quest=r.get('quest') or '', hours=float(r.get('hours') or 0), note=r.get('note', '')))
h = lambda x: f"{x:g}"
# 기간 중 기록이 하나도 없는 사람 → '자동기입': 근무일(평일, 공휴일 제외, 오늘까지) × 4 h
AUTO_H = 4
import holidays
kr = holidays.KR(years={f.year, t.year})
workdays = [f + datetime.timedelta(days=i) for i in range((min(t, today) - f).days + 1)]
workdays = [d for d in workdays if d.weekday() < 5 and d not in kr]
active = [m['name'] for m in members.values() if m.get('active', True) and m['name'] != '관리자']
missing = [n for n in active if n not in {r['member'] for r in rows}]
if workdays:
    for n in missing:
        rows.append(dict(date=t.isoformat(), member=n, type='자동기입', quest=f'근무일 {len(workdays)}일 × {AUTO_H} h', hours=float(AUTO_H * len(workdays)), note='기록 없음 → 자동기입'))
grand = sum(r['hours'] for r in rows); people = {r['member'] for r in rows}
by_type = collections.OrderedDict()
for r in rows:
    g = by_type.setdefault(r['type'], {'hours': 0, 'quests': {}})
    q = g['quests'].setdefault(r['quest'] or '(없음)', {'hours': 0, 'people': collections.Counter()})
    g['hours'] += r['hours']; q['hours'] += r['hours']; q['people'][r['member']] += r['hours']

td = 'style="border:1px solid #ddd;padding:6px 8px"'; tdr = 'style="border:1px solid #ddd;padding:6px 8px;text-align:right"'
html = f'<div style="font-family:-apple-system,Segoe UI,Malgun Gothic,sans-serif;max-width:720px;color:#222">'
html += f'<h2 style="margin:0 0 4px">JEELAB worklog · {label} 요약</h2>'
html += f'<p style="margin:0 0 14px;color:#555">기간 {f} – {t} · 총 {h(grand)} 시간 · {len(people)}명 기록 · {len(rows)}건</p>'
if rows:
    html += '<table style="border-collapse:collapse;font-size:14px;width:100%"><tr style="background:#eef2f6">' + ''.join(f'<th {td} align="left">{c}</th>' for c in ['업무 종류', '세부내용 (시간)', '총 시간', '인원', '사람별 시간']) + '</tr>'
    for name, g in sorted(by_type.items(), key=lambda kv: -kv[1]['hours']):
        people_t = collections.Counter()
        for q in g['quests'].values(): people_t.update(q['people'])
        qq = '<br>'.join(f'{qn} ({h(q["hours"])} h)' for qn, q in sorted(g['quests'].items(), key=lambda kv: -kv[1]['hours']))
        pp = ', '.join(f'{n} {h(v)}' for n, v in people_t.most_common())
        html += f'<tr><td {td}>{name}</td><td {td}>{qq}</td><td {tdr}>{h(g["hours"])} h</td><td {tdr}>{len(people_t)}명</td><td {td}>{pp}</td></tr>'
    html += f'<tr style="font-weight:700;background:#f7f7f7"><td {td} colspan="2">합계</td><td {tdr}>{h(grand)} h</td><td {tdr}>{len(people)}명</td><td {td}></td></tr></table>'
else:
    html += '<p style="color:#888">기록 없음</p>'
if missing: html += f'<p style="color:#a8552a"><b>기록 없는 사람 (자동기입, 근무일 {len(workdays)}일 × {AUTO_H} h):</b> {", ".join(missing)}</p>'
if period == 'day' and rows:
    html += '<h3 style="margin:18px 0 6px;font-size:15px">기록 내역</h3><table style="border-collapse:collapse;font-size:13px;width:100%"><tr style="background:#eef2f6">' + ''.join(f'<th {td} align="left">{c}</th>' for c in ['사람', '종류', '퀘스트', '시간', '한 일']) + '</tr>'
    for r in sorted(rows, key=lambda r: (r['member'], r['date'])):
        html += f'<tr><td {td}>{r["member"]}</td><td {td}>{r["type"]}</td><td {td}>{r["quest"] or "–"}</td><td {tdr}>{h(r["hours"])}</td><td {td}>{r["note"]}</td></tr>'
    html += '</table>'
elif rows:
    per = collections.defaultdict(lambda: {'h': 0, 'd': set()})
    for r in rows: per[r['member']]['h'] += r['hours']; per[r['member']]['d'].update(map(str, workdays) if r['type'] == '자동기입' else [r['date']])
    html += '<h3 style="margin:18px 0 6px;font-size:15px">사람별 총 시간</h3><table style="border-collapse:collapse;font-size:13px"><tr style="background:#eef2f6">' + ''.join(f'<th {td} align="left">{c}</th>' for c in ['이름', '시간', '기록한 날']) + '</tr>'
    for n, v in sorted(per.items(), key=lambda kv: -kv[1]['h']):
        html += f'<tr><td {td}>{n}</td><td {tdr}>{h(v["h"])} h</td><td {tdr}>{len(v["d"])}일</td></tr>'
    html += '</table>'
html += f'<p style="margin-top:20px;font-size:12px;color:#888">업무일지: <a href="{PAGE}">{PAGE}</a></p></div>'

msg = MIMEMultipart('alternative'); msg['Subject'] = f'[JEELAB worklog] {label} 요약'; msg['From'] = f'JEELAB worklog <{os.environ["GMAIL_USER"]}>'; msg['To'] = ', '.join(TO)
msg.attach(MIMEText(html, 'html', 'utf-8'))
with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
    # app passwords are shown as 4x4 groups; strip spaces/newlines that come along when pasting
    s.login(os.environ['GMAIL_USER'].strip(), os.environ['GMAIL_APP_PASSWORD'].replace(' ', '').strip()); s.sendmail(msg['From'], TO, msg.as_string())
print(f'sent {label}: {h(grand)} h, {len(rows)} rows, {len(people)} people')
