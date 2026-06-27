#!/usr/bin/env bash
# SecuLog 발행 스크립트
# 헤르메스가 data/<날짜>.json 을 만든 뒤 이 스크립트 한 번만 호출하면 발행 완료.
set -e
cd "$(dirname "$0")"

echo "[1/3] 사이트 빌드..."
python3 build_site.py

echo "[2/3] 변경사항 커밋..."
git add -A
if git diff --cached --quiet; then
  echo "변경된 내용이 없습니다. 종료."
  exit 0
fi
git commit -m "brief: $(date +%F)"

echo "[3/3] 푸시 → GitHub Pages 자동 배포..."
git push

echo "✅ 발행 완료. 1분 내 사이트에 반영됩니다."
