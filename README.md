# 랩 업무일지 (공개 버전)

정적 페이지(`index.html`) + Supabase `docs` 테이블. GitHub Pages로 배포하고, GitHub Actions가 일간/주간/월간 요약 메일을 보냅니다.

- 스키마: `schema.sql` (Supabase SQL Editor에서 실행)
- 메일: `.github/workflows/summary.yml` → `scripts/summary.py`
  - Secrets: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`
  - Variables: `MAIL_TO` (쉼표 구분), `PAGE_URL`
