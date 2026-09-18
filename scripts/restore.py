"""백업 JSON을 Supabase `docs` 테이블에 다시 넣는다 (같은 collection/id 는 덮어씀).
Usage: python restore.py backups/docs-YYYY-MM-DD.json   (env: SUPABASE_URL, SUPABASE_ANON_KEY)"""
import os, sys, json, urllib.request

URL, KEY = os.environ['SUPABASE_URL'].rstrip('/'), os.environ['SUPABASE_ANON_KEY']
docs = json.load(open(sys.argv[1], encoding='utf-8'))['docs']
for i in range(0, len(docs), 200):
    body = json.dumps([{k: d[k] for k in ('collection', 'id', 'data', 'updated_at') if k in d} for d in docs[i:i + 200]]).encode()
    req = urllib.request.Request(f"{URL}/rest/v1/docs?on_conflict=collection,id", data=body, method='POST',
                                 headers={'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json', 'Prefer': 'resolution=merge-duplicates'})
    urllib.request.urlopen(req, timeout=120).read()
print('restored', len(docs), 'docs')
