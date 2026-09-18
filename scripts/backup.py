"""Supabase `docs` 테이블 전체를 backups/docs-YYYY-MM-DD.json 으로 저장 (사진 파일은 URL만 포함).
Usage: python backup.py   (env: SUPABASE_URL, SUPABASE_ANON_KEY)"""
import os, json, datetime, urllib.request
from zoneinfo import ZoneInfo

URL, KEY = os.environ['SUPABASE_URL'].rstrip('/'), os.environ['SUPABASE_ANON_KEY']
rows, page = [], 1000
while True:
    req = urllib.request.Request(f"{URL}/rest/v1/docs?select=*&order=collection,id&limit={page}&offset={len(rows)}",
                                 headers={'apikey': KEY, 'Authorization': 'Bearer ' + KEY})
    chunk = json.load(urllib.request.urlopen(req, timeout=120))
    rows += chunk
    if len(chunk) < page: break

today = datetime.datetime.now(ZoneInfo('Asia/Seoul')).date()
os.makedirs('backups', exist_ok=True)
out = f"backups/docs-{today.isoformat()}.json"
with open(out, 'w', encoding='utf-8') as f:
    json.dump({'exported': datetime.datetime.now(ZoneInfo('Asia/Seoul')).isoformat(), 'count': len(rows), 'docs': rows}, f, ensure_ascii=False, indent=1)
# 최근 12개만 유지
old = sorted(x for x in os.listdir('backups') if x.startswith('docs-') and x.endswith('.json'))[:-12]
for x in old: os.remove(os.path.join('backups', x))
by = {}
for r in rows: by[r['collection']] = by.get(r['collection'], 0) + 1
print(out, len(rows), 'docs', by)
