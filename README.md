# 랩 업무일지 (공개 버전)

정적 페이지(`index.html`) + Supabase `docs` 테이블. GitHub Pages로 배포하고, GitHub Actions가 일간/주간/월간 요약 메일을 보냅니다.

- 스키마: `schema.sql` (Supabase SQL Editor에서 실행)
- 메일: `.github/workflows/summary.yml` → `scripts/summary.py`
  - Secrets: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`
  - 일정 (KST): 일간 평일 19:00 · 주간 금 19:00 (토–금) · 월간 말일 19:00 (이번 달)
  - 자동기입: 기록 없는 근무일(평일, 한국 공휴일 제외, 작성자 등록일부터) × 작성자별 계약시간(`members.dailyHours`, 관리자 탭 h/일; 비우면 4, 0이면 끔). 메일에만 표시, 사이트 기록은 그대로
  - Variables: `MAIL_TO` (전체 메일, 쉼표 구분), `MAIL_TO_REPORT` (주간·월간만 추가 수신, 쉼표 구분), `PAGE_URL`
- 백업: `.github/workflows/backup.yml` → `scripts/backup.py` (매주 월 04:00 KST, `backups/docs-YYYY-MM-DD.json`, 최근 12개 유지; 사진은 URL만)
  - 복구: `SUPABASE_URL=… SUPABASE_ANON_KEY=… python scripts/restore.py backups/docs-YYYY-MM-DD.json`
  - 수동 실행: `gh workflow run backup.yml`
