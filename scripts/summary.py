"""랩 업무일지 요약 메일 — Supabase `docs` 테이블을 읽어 하나의 표(업무 종류 | 총 시간 | 인원 | 사람별 시간 | 퀘스트)로 정리해 Gmail SMTP로 보낸다.
Usage: python summary.py day|week|month   (env: SUPABASE_URL, SUPABASE_ANON_KEY, GMAIL_USER, GMAIL_APP_PASSWORD, MAIL_TO, PAGE_URL)"""
import os, sys, json, datetime, smtplib, urllib.request, urllib.parse, collections
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from zoneinfo import ZoneInfo

period = sys.argv[1] if len(sys.argv) > 1 else 'day'
URL, KEY = os.environ['SUPABASE_URL'].rstrip('/'), os.environ['SUPABASE_ANON_KEY']
TO = [x.strip() for x in os.environ.get('MAIL_TO', 'dayoung@kist.re.kr').split(',') if x.strip()]
PAGE = os.environ.get('PAGE_URL', '')

def fetch(col, extra=''):
    q = f"{URL}/rest/v1/docs?collection=eq.{col}&select=id,data&limit=5000{extra}"
    req = urllib.request.Request(q, headers={'apikey': KEY, 'Authorization': 'Bearer ' + KEY})
    return json.load(urllib.request.urlopen(req, timeout=60))

today = datetime.datetime.now(ZoneInfo('Asia/Seoul')).date()
if period == 'day':
    f = t = today; label = f"{today:%Y-%m-%d} ({'월화수목금토일'[today.weekday()]}) 일간"
elif period == 'week':
    f = today - datetime.timedelta(days=today.weekday() + 7); t = f + datetime.timedelta(days=6); label = f"{f:%m/%d} – {t:%m/%d} 주간"
else:
    first = today.replace(day=1); t = first - datetime.timedelta(days=1); f = t.replace(day=1); label = f"{f:%Y년 %m월} 월간"

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
grand = sum(r['hours'] for r in rows); people = {r['member'] for r in rows}
by_type = collections.OrderedDict()
for r in rows:
    g = by_type.setdefault(r['type'], {'hours': 0, 'people': collections.Counter(), 'quests': collections.Counter()})
    g['hours'] += r['hours']; g['people'][r['member']] += r['hours']; g['quests'][r['quest'] or '(없음)'] += r['hours']
active = [m['name'] for m in members.values() if m.get('active', True) and m['name'] != '관리자']
missing = [n for n in active if n not in people]

td = 'style="border:1px solid #ddd;padding:6px 8px"'; tdr = 'style="border:1px solid #ddd;padding:6px 8px;text-align:right"'
html = f'<div style="font-family:-apple-system,Segoe UI,Malgun Gothic,sans-serif;max-width:720px;color:#222">'
html += f'<h2 style="margin:0 0 4px">랩 업무일지 · {label} 요약</h2>'
html += f'<p style="margin:0 0 14px;color:#555">기간 {f} – {t} · 총 {h(grand)} 시간 · {len(people)}명 기록 · {len(rows)}건</p>'
if rows:
    html += '<table style="border-collapse:collapse;font-size:14px;width:100%"><tr style="background:#eef2f6">' + ''.join(f'<th {td} align="left">{c}</th>' for c in ['업무 종류', '총 시간', '인원', '사람별 시간', '퀘스트']) + '</tr>'
    for name, g in sorted(by_type.items(), key=lambda kv: -kv[1]['hours']):
        pp = ', '.join(f'{n} {h(v)}' for n, v in g['people'].most_common())
        qq = ', '.join(f'{n} {h(v)}' for n, v in g['quests'].most_common())
        html += f'<tr><td {td}>{name}</td><td {tdr}>{h(g["hours"])} h</td><td {tdr}>{len(g["people"])}명</td><td {td}>{pp}</td><td {td}>{qq}</td></tr>'
    html += f'<tr style="font-weight:700;background:#f7f7f7"><td {td}>합계</td><td {tdr}>{h(grand)} h</td><td {tdr}>{len(people)}명</td><td {td} colspan="2"></td></tr></table>'
else:
    html += '<p style="color:#888">기록 없음</p>'
if missing: html += f'<p style="color:#a8552a"><b>기록 없는 사람:</b> {", ".join(missing)}</p>'
if period == 'day' and rows:
    html += '<h3 style="margin:18px 0 6px;font-size:15px">기록 내역</h3><table style="border-collapse:collapse;font-size:13px;width:100%"><tr style="background:#eef2f6">' + ''.join(f'<th {td} align="left">{c}</th>' for c in ['사람', '종류', '퀘스트', '시간', '한 일']) + '</tr>'
    for r in sorted(rows, key=lambda r: (r['member'], r['date'])):
        html += f'<tr><td {td}>{r["member"]}</td><td {td}>{r["type"]}</td><td {td}>{r["quest"] or "–"}</td><td {tdr}>{h(r["hours"])}</td><td {td}>{r["note"]}</td></tr>'
    html += '</table>'
elif rows:
    per = collections.defaultdict(lambda: {'h': 0, 'd': set()})
    for r in rows: per[r['member']]['h'] += r['hours']; per[r['member']]['d'].add(r['date'])
    html += '<h3 style="margin:18px 0 6px;font-size:15px">사람별 총 시간</h3><table style="border-collapse:collapse;font-size:13px"><tr style="background:#eef2f6">' + ''.join(f'<th {td} align="left">{c}</th>' for c in ['이름', '시간', '기록한 날']) + '</tr>'
    for n, v in sorted(per.items(), key=lambda kv: -kv[1]['h']):
        html += f'<tr><td {td}>{n}</td><td {tdr}>{h(v["h"])} h</td><td {tdr}>{len(v["d"])}일</td></tr>'
    html += '</table>'
html += f'<p style="margin-top:20px;font-size:12px;color:#888">업무일지: <a href="{PAGE}">{PAGE}</a></p></div>'

msg = MIMEMultipart('alternative'); msg['Subject'] = f'[랩 업무일지] {label} 요약'; msg['From'] = f'랩 업무일지 <{os.environ["GMAIL_USER"]}>'; msg['To'] = ', '.join(TO)
msg.attach(MIMEText(html, 'html', 'utf-8'))
with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
    # app passwords are shown as 4x4 groups; strip spaces/newlines that come along when pasting
    s.login(os.environ['GMAIL_USER'].strip(), os.environ['GMAIL_APP_PASSWORD'].replace(' ', '').strip()); s.sendmail(msg['From'], TO, msg.as_string())
print(f'sent {label}: {h(grand)} h, {len(rows)} rows, {len(people)} people')
