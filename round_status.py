"""라운드 하네스(scripts/round.sh) 상태 — config.json 의 round.projects.

프로젝트마다 .orca 파일 세 개만 읽는다 (round.sh 의 status 출력은 자주 바뀌어서 파싱하지 않는다):
  round.wait.pid   → wait 루프가 살아 있나
  round.tsv        → 미정산 티켓 (4열 이슈 중 round.settled 에 없는 것 — round.sh inflight_issues 와 같은 규칙)
  round.attention  → 사람이 답할 것 (줄 수)
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from config import CFG
from mole import _ssh

PROJECTS = (CFG.get("round") or {}).get("projects") or []  # [{"name", "host"(null=이 맥), "root"}]

SCAN = r'''
for r in %s; do
  o="$HOME/$r/.orca"; p=$(cat "$o/round.wait.pid" 2>/dev/null)
  alive=0; [ -n "$p" ] && kill -0 "$p" 2>/dev/null && alive=1
  inflight=$(ST="$(cat "$o/round.settled" 2>/dev/null)" awk -F'\t' \
    'BEGIN{n=split(ENVIRON["ST"],a,"\n"); for(i=1;i<=n;i++) s[a[i]]=1} $4!="-" && $4!="" && !($4 in s)' \
    "$o/round.tsv" 2>/dev/null | wc -l | tr -d ' ')
  att=$(cat "$o/round.attention" 2>/dev/null | wc -l | tr -d ' ')
  echo "$r $alive ${inflight:-0} ${att:-0}"
done
'''


@dataclass
class RoundStatus:
    name: str
    host: str
    ok: bool = False  # 읽기 성공
    alive: bool = False
    inflight: int = 0
    attention: int = 0


def _scan(host: str, roots: list[str]) -> dict[str, tuple[bool, int, int]]:
    out = _ssh(host, SCAN % " ".join(json.dumps(r) for r in roots), 20).stdout
    res = {}
    for line in out.splitlines():
        parts = line.rsplit(" ", 3)
        if len(parts) == 4:
            res[parts[0]] = (parts[1] == "1", int(parts[2]), int(parts[3]))
    return res


def collect() -> list[RoundStatus]:
    by_host: dict[str, list[dict]] = {}
    for p in PROJECTS:
        by_host.setdefault(p.get("host") or "local", []).append(p)
    with ThreadPoolExecutor(max_workers=max(1, len(by_host))) as ex:
        futs = {h: ex.submit(_scan, h, [p["root"] for p in ps]) for h, ps in by_host.items()}
    stats = []
    for p in PROJECTS:
        host = p.get("host") or "local"
        try:
            got = futs[host].result().get(p["root"])
        except Exception:
            got = None
        s = RoundStatus(p["name"], host)
        if got:
            s.ok, (s.alive, s.inflight, s.attention) = True, got
        stats.append(s)
    return stats


if __name__ == "__main__":
    for s in collect():
        print(s)
