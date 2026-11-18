#!/bin/bash
# upstream 을 받아 충돌·테스트 실패가 없을 때만 머지 → 덱 재시작 → fork 에 push.
# ponytail: 실패하면 원래대로 되돌리고 로그만 남김. 사람이 손으로 머지.
set -u
cd "$(dirname "$0")/.." || exit 1
log() { echo "$(date '+%F %T') auto-update: $*"; }

[ -n "$(git status --porcelain)" ] && { log "커밋 안 된 수정 있음 — 건너뜀"; exit 0; }
[ "$(git branch --show-current)" = main ] || { log "main 브랜치 아님 — 건너뜀"; exit 0; }
git fetch -q upstream || { log "fetch 실패"; exit 1; }
[ "$(git rev-list --count HEAD..upstream/main)" = 0 ] && { log "최신"; exit 0; }

before=$(git rev-parse HEAD)
if ! git merge -q --no-edit upstream/main; then
  git merge --abort; log "충돌 — 손으로 머지 필요"; exit 1
fi
if ! .venv/bin/python -m unittest discover -s tests >/dev/null 2>&1; then
  git reset -q --hard "$before"; log "테스트 실패 — 되돌림"; exit 1
fi
launchctl kickstart -k "gui/$(id -u)/com.agentdeck.dashboard"
git push -q origin main || log "push 실패"
log "갱신 완료 $(git rev-parse --short "$before")..$(git rev-parse --short HEAD)"
