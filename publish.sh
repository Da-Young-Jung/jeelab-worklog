#!/bin/zsh
# 2단계: (토큰에 workflow 권한을 추가한 뒤) 푸시 + GitHub Pages + 메일 Secrets. 여러 번 실행해도 안전.
set -e
cd "$(dirname "$0")"
OWNER=$(gh api user --jq .login)
touch .nojekyll
[ -d .git ] || git init -q -b main
git add -A
git -c user.name="Da-Young Jung" -c user.email="jdana412@gmail.com" commit -q -m "랩 업무일지 공개 버전 (Supabase + GitHub Pages)" || true
git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$OWNER/jeelab-worklog.git"
git push -u origin main
# Pages: main 브랜치 루트에서 서비스
gh api -X POST "repos/$OWNER/jeelab-worklog/pages" -f build_type=legacy -f 'source[branch]=main' -f 'source[path]=/' >/dev/null 2>&1 || true
# 메일 워크플로 값 (Gmail 앱 비밀번호는 저장소 Settings → Secrets 에서 직접)
gh secret set SUPABASE_URL      --body "https://kqcmkzflzvjllckqcpbq.supabase.co"
gh secret set SUPABASE_ANON_KEY --body "$(python3 -c "import re;print(re.search(r\"anonKey: '([^']+)'\",open('index.html').read()).group(1))")"
gh variable set MAIL_TO  --body "dayoung@kist.re.kr"
gh variable set PAGE_URL --body "https://$(echo $OWNER | tr 'A-Z' 'a-z').github.io/jeelab-worklog/"
echo
echo "완료. 1~2분 뒤 접속: https://$(echo $OWNER | tr 'A-Z' 'a-z').github.io/jeelab-worklog/"
echo "메일 활성화: https://github.com/$OWNER/jeelab-worklog/settings/secrets/actions 에 GMAIL_USER, GMAIL_APP_PASSWORD 추가"
