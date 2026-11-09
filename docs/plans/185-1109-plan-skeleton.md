# #185 skeleton Implementation Plan

> **For Claude:** This plan is executed via /ralph-loop:ralph-loop in a detached orch session.
> You are ALREADY in the worktree, checked out on the feature branch. Do NOT switch branches,
> create another worktree, or use AskUserQuestion / any interactive prompt — the session is
> headless and cannot receive input, so always take the autonomous (recommended) default and
> keep working. Do NOT use superpowers:executing-plans or subagent-driven-development.
> Emit `<promise>RALPH_DONE</promise>` ONLY when every Done-criteria item and every Pre-PR check
> is genuinely true AND the PR has been created — never to escape the loop.
> Never write the promise tag in any other message, not even to say you will not emit it —
> the loop's stop hook can read an earlier message, so a mention ends the loop.
> RALPH_DONE means the work is finished, NOT that the result passed. If an honest measurement
> lands in a below-pass band of the plan (re-measure or 미완), and the plan step for that band has
> been carried out, write the band and the measured value verbatim in the report and at the top of
> the PR body, then emit RALPH_DONE. Judging the result is jw's call at the gate, not yours.
> Do not keep iterating to push a number over a threshold the plan's tasks no longer cover.
> Before emitting it, stop every background shell you started (TaskStop tool). A shell left
> running keeps the session in `bg` state, and orch never marks the step done.
> On a HARD, retry-proof API error (OpenAI insufficient_quota, 401/403, exhausted billing), STOP —
> do NOT emit RALPH_DONE, do NOT create a PR, do NOT spin retrying. It surfaces via the orch
> completion notification; a human fixes billing. (Transient TPM 429 is different — pace and retry.)
> A TRANSIENT error that stops being transient counts as HARD. If 429/529 keeps surfacing AND you
> have produced no commit and no file change for 20 minutes, STOP the same way. Waiting and
> spinning are indistinguishable in a headless loop — nobody is watching the screen, and the loop
> re-submits the prompt after every failed turn, so a server-side outage burns the whole iteration
> budget while the picker still reads `working`.

**Tier:** B
**Notion:** #185 https://app.notion.com/p/41341e6165c081b68c96caf861560aa5 (page id `41341e61-65c0-81b6-8c96-caf861560aa5`)
**설계:** `/Users/jw/prv/.wt/185-skeleton/docs/plans/185-1109-design-skeleton.md` — 착수 전에 먼저 읽는다. 데이터 실측, 지선·별칭 표, 질문 3개가 거기 있다
**흐름:** 이 티켓이 처음 만든다. Task 6에서 명령 하나로 끝까지 이어진다

## jw 기준

명령 하나로 전체 프로젝트가 처음부터 끝까지 잘 돈다 <!-- style-exempt -->

## 통과 기준

- 깨끗한 clone에서 `uv run subway-eval` 하나로 데이터 읽기 → 그래프 → 질문 3개 → 다익스트라 정답 → stub 답 → 채점 → 리포트가 끝까지 돈다 <!-- style-exempt -->
- 리포트(`reports/skeleton.md`, 같은 내용을 stdout에도)에 질문 3개 행이 있고, 행마다 정답 경로와 정답 소요 시간이 채워져 있다
- 답하는 쪽은 stub이라 **정답률 0/3(0%)이 정상이다.** stub을 채워 점수를 올리지 않는다. stub을 실제 구현으로 바꾸는 것은 다음 티켓이다
- q1 정답 소요 시간이 손으로 계산한 값 1,740초(29분), 환승 0회와 같다

## 이번에 안 하는 것

- LLM 연결. `answerers.py`에는 `stub` 하나만 둔다. LLM 혼자, LLM + 도구는 다음 티켓에서 이 자리에 들어간다
- 도구를 잘게 줄지 크게 줄지 비교
- 실시간 열차 시각표. 기다리는 시간은 0으로 본다 <!-- style-exempt -->
- 실제 환승 시간. 환승 한 번에 180초로 고정한다(`TRANSFER_SECONDS`, stub)
- 1~8호선 밖 노선(9호선, 1호선 코레일 구간 등), 버스
- 데이터를 실행할 때마다 다시 받는 기능. 한 번 받아 커밋한다

## 실패 징후

1. **jw 기준을 잰다.** 잴 방법: 워크트리를 임시 디렉터리에 `git clone`하고, 그 안에서 `uv run subway-eval` 하나만 돌린다. exit code, 리포트 파일, 정답 경로가 채워진 질문 수를 본다
   - 통과: exit 0, `reports/skeleton.md`가 생기고, 질문 3개 모두 정답 경로·정답 소요 시간이 채워져 있다
   - 다시 잰다: exit 0이고 리포트도 나오는데 정답 경로가 빈 질문이 1~2개다. 그래프 연결(지선 표·별칭 표)을 고친 뒤 깨끗한 clone에서 다시 잰다
   - 미완: exit 0이 아니다, 리포트가 안 생긴다, 3개 모두 정답 경로가 비었다, 또는 명령이 둘 이상 필요하다(`uv sync`를 따로 쳐야 하는 것 포함)
2. 1~8호선 노드 중 `('서울역', 1)`에서 닿지 않는 노드가 1개 이상이면 지선 표나 별칭 표가 틀렸다
3. q3 정답 경로에 `('상일동', 5)`가 있거나 `('둔촌동', 5)`가 없으면 마천지선 연결이 틀렸다
4. stub인데 정답률이 0/3이 아니면 채점이 틀렸다

## 파일 구성

```
pyproject.toml
data/seoul_metro_1to8_240810.csv     # 받은 CSV, UTF-8로 바꿔 커밋
data/questions.json                  # 질문 3개
src/subway_route_agent/
  __init__.py
  data.py        # CSV → Row
  graph.py       # Row → 그래프 (지선 표, 별칭 표, 환승 180초)
  route.py       # 다익스트라 (환승 상한)
  answerers.py   # 답하는 쪽. stub 하나
  grade.py       # Answer 채점
  report.py      # 리포트 표
  cli.py         # subway-eval
tests/
docs/concepts.md
reports/skeleton.md                  # 마지막에 실행 결과를 커밋
```

---

### Task 1: uv 프로젝트와 데이터

**Files:**
- Create: `pyproject.toml`, `src/subway_route_agent/__init__.py`, `src/subway_route_agent/data.py`, `data/seoul_metro_1to8_240810.csv`, `tests/test_data.py`
- Modify: `README.md` (데이터 출처 절 추가)

**Step 1: pyproject**

```toml
[project]
name = "subway-route-agent"
version = "0.1.0"
description = "서울 지하철 길찾기 — LLM에게 도구를 주면 무엇이 좋아지고 무엇이 비싸지나"
requires-python = ">=3.11"
dependencies = []

[project.scripts]
subway-eval = "subway_route_agent.cli:main"

[dependency-groups]
dev = ["pytest>=8.3", "ruff>=0.8"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/subway_route_agent"]

[tool.pytest.ini_options]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

`uv sync`로 `.venv`와 `uv.lock`을 만든다. `uv.lock`은 커밋한다.

**Step 2: 데이터 받기 (한 번)**

```bash
curl -s -X POST 'https://datafile.seoul.go.kr/bigfile/iot/inf/nio_download.do?&useCache=false' \
  -d 'infId=OA-12034&infSeq=1&seq=9' -o /tmp/oa12034.csv
iconv -f cp949 -t utf-8 /tmp/oa12034.csv > data/seoul_metro_1to8_240810.csv
head -2 data/seoul_metro_1to8_240810.csv   # 연번,호선,역명,소요시간,역간거리(km),호선별누계(km)
```

받기가 실패하면(응답이 CSV가 아니거나 279행이 아니면) 설계 문서 §질문 3개를 풀 수 있는 노선만 손으로 넣은 작은 CSV를 같은 열로 만들고, 그 사실을 README와 리포트 머리에 적는다.

README에 `## 데이터` 절을 더한다: 출처(서울 열린데이터광장 OA-12034 「서울교통공사 역간거리 및 소요시간」, 2024-08-10 기준), 공공누리 1유형, 1~8호선만 있다는 것, 소요시간은 표준 운행시간이라는 것.

**Step 3: 실패하는 테스트**

```python
# tests/test_data.py
from subway_route_agent.data import load_rows, parse_mmss


def test_parse_mmss():
    assert parse_mmss("01:40") == 100
    assert parse_mmss("00:00") == 0


def test_load_rows_real_csv():
    rows = load_rows()
    assert len(rows) == 279
    assert {r.line for r in rows} == set(range(1, 9))
    assert rows[1].station == "시청" and rows[1].seconds == 120
```

**Step 4: 구현**

```python
# src/subway_route_agent/data.py
import csv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "seoul_metro_1to8_240810.csv"


@dataclass(frozen=True)
class Row:
    line: int
    station: str
    seconds: int  # 바로 위 행의 역에서 이 역까지. 노선 첫 행은 0


def parse_mmss(s: str) -> int:
    m, sec = s.strip().split(":")
    return int(m) * 60 + int(sec)


def load_rows(path: Path = DATA) -> list[Row]:
    with open(path, encoding="utf-8", newline="") as f:
        return [
            Row(int(r["호선"]), r["역명"].strip(), parse_mmss(r["소요시간"]))
            for r in csv.DictReader(f)
        ]
```

**Step 5:** `uv run pytest tests/test_data.py -v` → PASS. 커밋: `init: uv 프로젝트와 1~8호선 역간 소요시간 데이터`

### Task 2: 그래프

**Files:** Create `src/subway_route_agent/graph.py`, `tests/test_graph.py`

**Step 1: 실패하는 테스트**

```python
# tests/test_graph.py
from subway_route_agent.data import Row, load_rows
from subway_route_agent.graph import TRANSFER_SECONDS, build_graph


def _edges(g, node):
    return {n: w for n, w in g[node]}


def test_branch_head_attaches_to_named_station():
    rows = [Row(5, "강동", 0), Row(5, "길동", 90), Row(5, "둔촌동", 110), Row(5, "올림픽공원", 100)]
    g = build_graph(rows)
    assert ("길동", 5) not in _edges(g, ("둔촌동", 5))
    assert _edges(g, ("둔촌동", 5))[("강동", 5)] == 110


def test_alias_and_transfer():
    rows = [Row(4, "사당", 0), Row(4, "총신대입구", 120), Row(7, "이수", 0), Row(7, "내방", 90)]
    g = build_graph(rows)
    assert ("총신대입구", 4) not in g
    assert _edges(g, ("이수", 4))[("이수", 7)] == TRANSFER_SECONDS


def test_first_row_of_line_does_not_link_to_previous_line():
    rows = [Row(1, "청량리", 0), Row(2, "시청", 0), Row(2, "을지로입구", 90)]
    g = build_graph(rows)
    assert _edges(g, ("시청", 2)) == {("을지로입구", 2): 90}


def test_real_graph_is_connected():
    g = build_graph(load_rows())
    seen, stack = {("서울역", 1)}, [("서울역", 1)]
    while stack:
        for n, _ in g[stack.pop()]:
            if n not in seen:
                seen.add(n)
                stack.append(n)
    assert seen == set(g)
```

**Step 2: 구현**

```python
# src/subway_route_agent/graph.py
from collections import defaultdict

from subway_route_agent.data import Row

Node = tuple[str, int]  # (역, 호선)
Graph = dict[Node, list[tuple[Node, int]]]

# CSV는 지선을 표시 없이 이어 붙였다. 이 행은 바로 위 행이 아니라 값의 역에 붙는다
BRANCH_HEADS = {(2, "용답"): "성수", (2, "도림천"): "신도림", (5, "둔촌동"): "강동"}
# 노선마다 이름이 다른 같은 역
ALIASES = {"총신대입구": "이수"}
# ponytail: 환승 시간 stub. 실제 값은 data.go.kr 15044419(환승역 거리·소요시간)로 바꾼다
TRANSFER_SECONDS = 180


def build_graph(rows: list[Row]) -> Graph:
    g: defaultdict[Node, list[tuple[Node, int]]] = defaultdict(list)
    prev: Node | None = None
    for r in rows:
        node = (ALIASES.get(r.station, r.station), r.line)
        g[node]  # 이웃이 없어도 노드는 만든다
        head = BRANCH_HEADS.get((r.line, r.station))
        if head:
            prev = (head, r.line)
        if prev is not None and prev[1] == r.line and r.seconds > 0:
            g[prev].append((node, r.seconds))
            g[node].append((prev, r.seconds))
        prev = node
    by_station: defaultdict[str, list[Node]] = defaultdict(list)
    for node in list(g):
        by_station[node[0]].append(node)
    for nodes in by_station.values():
        for a in nodes:
            for b in nodes:
                if a != b:
                    g[a].append((b, TRANSFER_SECONDS))
    return dict(g)
```

**Step 3:** `uv run pytest tests/test_graph.py -v` → PASS. 커밋: `feature: 역간 소요시간으로 그래프를 만든다 (지선 표, 별칭, 환승 180초 stub)`

### Task 3: 다익스트라

**Files:** Create `src/subway_route_agent/route.py`, `tests/test_route.py`

**Step 1: 실패하는 테스트**

```python
# tests/test_route.py
from subway_route_agent.data import Row, load_rows
from subway_route_agent.graph import build_graph
from subway_route_agent.route import shortest

REAL = build_graph(load_rows())


def test_transfer_limit_forces_slower_route():
    rows = [
        Row(1, "A", 0), Row(1, "B", 60), Row(1, "C", 600),
        Row(2, "B", 0), Row(2, "C", 60),
    ]
    g = build_graph(rows)
    fast = shortest(g, "A", "C")
    assert fast.transfers == 1 and fast.seconds == 60 + 180 + 60
    direct = shortest(g, "A", "C", max_transfers=0)
    assert direct.transfers == 0 and direct.seconds == 660


def test_unknown_station_returns_none():
    assert shortest(REAL, "없는역", "강남") is None


def test_q1_matches_hand_count():
    r = shortest(REAL, "강남", "홍대입구", max_transfers=1)
    assert r.seconds == 1740 and r.transfers == 0


def test_q3_uses_macheon_branch():
    r = shortest(REAL, "방화", "마천", max_transfers=0)
    assert ("둔촌동", 5) in r.nodes and ("상일동", 5) not in r.nodes


def test_q2_needs_transfer():
    r = shortest(REAL, "서울역", "잠실")
    assert r.transfers >= 1
```

**Step 2: 구현**

```python
# src/subway_route_agent/route.py
import heapq
from dataclasses import dataclass

from subway_route_agent.graph import Graph, Node


@dataclass
class Route:
    nodes: list[Node]
    seconds: int
    transfers: int


def shortest(g: Graph, origin: str, dest: str, max_transfers: int | None = None) -> Route | None:
    """상태를 (노드, 환승 횟수)로 늘린 다익스트라. 환승 상한이 있어도 최단을 구한다."""
    pq = [(0, 0, n, (n,)) for n in g if n[0] == origin]
    heapq.heapify(pq)
    done: set[tuple[Node, int]] = set()
    while pq:
        sec, tr, node, path = heapq.heappop(pq)
        if node[0] == dest:
            return Route(list(path), sec, tr)
        if (node, tr) in done:
            continue
        done.add((node, tr))
        for nxt, w in g[node]:
            ntr = tr + (nxt[1] != node[1])
            if max_transfers is not None and ntr > max_transfers:
                continue
            heapq.heappush(pq, (sec + w, ntr, nxt, path + (nxt,)))
    return None
```

**Step 3:** `uv run pytest tests/test_route.py -v` → PASS. `test_q1_matches_hand_count`가 실패하면 기대값을 고치지 말고 그래프를 의심한다(설계 문서 §질문 3개에 손으로 계산한 구간이 있다). 커밋: `feature: 환승 상한이 있는 다익스트라` <!-- style-exempt -->

### Task 4: 질문과 답하는 쪽 stub

**Files:** Create `data/questions.json`, `src/subway_route_agent/answerers.py`, `tests/test_answerers.py`

```json
[
  {"id": "q1", "text": "강남에서 홍대입구까지, 환승 한 번 이하로, 8시 20분에 출발해서 9시 전에 도착하고 싶어",
   "origin": "강남", "dest": "홍대입구", "max_transfers": 1, "depart": "08:20", "arrive_by": "09:00"},
  {"id": "q2", "text": "서울역에서 잠실까지 가장 빨리 가는 길 알려줘",
   "origin": "서울역", "dest": "잠실", "max_transfers": null, "depart": null, "arrive_by": null},
  {"id": "q3", "text": "방화에서 마천까지 환승 없이 가고 싶어",
   "origin": "방화", "dest": "마천", "max_transfers": 0, "depart": null, "arrive_by": null}
]
```

```python
# src/subway_route_agent/answerers.py
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class Answer:
    path: list[tuple[str, int]] = field(default_factory=list)  # [(역, 호선)]
    seconds: int | None = None
    tool_calls: int = 0


def stub(question_text: str) -> Answer:
    """LLM 없이 고정된 답. 모든 질문에 빈 답을 돌려준다. 다음 티켓에서 LLM 혼자 / LLM + 도구가 이 자리에 들어간다."""
    return Answer()


# 답하는 쪽은 질문 문장만 받는다. 구조화된 필드는 채점만 쓴다
ANSWERERS: dict[str, Callable[[str], Answer]] = {"stub": stub}
```

테스트: `stub`이 어떤 문장에도 빈 경로·`None`·도구 호출 0을 돌려준다. 커밋: `feature: 질문 3개와 답하는 쪽 stub`

### Task 5: 채점

**Files:** Create `src/subway_route_agent/grade.py`, `tests/test_grade.py`

규칙(설계 문서 §설계 결정과 같다):
- 답 있음: 경로가 비어 있지 않다. 답이 없으면 나머지는 세지 않고 맞음은 거짓이다
- 지어낸 역: 답 경로의 역 중 그래프에 없는 역 수
- 경로의 실제 소요 시간: 이웃한 두 노드가 그래프에서 이어져 있으면 그 간선 시간의 합. 하나라도 안 이어지면 `None`
- 지어낸 소요 시간: 답이 말한 시간과 경로의 실제 소요 시간이 60초 넘게 다르면 1. 실제 소요 시간이 `None`이면 0
- 조건 어김(목록): `출발역 다름` · `도착역 다름` · `경로 끊김` · `환승 초과` · `시한 초과`(출발 시각 + 실제 소요 시간 > 도착 시한)
- 맞음: 답 있음 + 조건 어김 0 + 실제 소요 시간 == 정답 소요 시간

```python
# src/subway_route_agent/grade.py
from dataclasses import dataclass, field

from subway_route_agent.answerers import Answer
from subway_route_agent.graph import Graph, Node
from subway_route_agent.route import Route


@dataclass
class Grade:
    answered: bool
    correct: bool
    invented_stations: int = 0
    invented_time: int = 0
    violations: list[str] = field(default_factory=list)


def path_seconds(g: Graph, path: list[Node]) -> int | None:
    total = 0
    for a, b in zip(path, path[1:]):
        w = next((w for n, w in g.get(a, []) if n == b), None)
        if w is None:
            return None
        total += w
    return total


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def grade(g: Graph, q: dict, ans: Answer, truth: Route | None) -> Grade:
    if not ans.path:
        return Grade(answered=False, correct=False)
    stations = {n[0] for n in g}
    path = [tuple(n) for n in ans.path]
    actual = path_seconds(g, path)
    v = []
    if path[0][0] != q["origin"]:
        v.append("출발역 다름")
    if path[-1][0] != q["dest"]:
        v.append("도착역 다름")
    if actual is None:
        v.append("경로 끊김")
    transfers = sum(a[1] != b[1] for a, b in zip(path, path[1:]))
    if q["max_transfers"] is not None and transfers > q["max_transfers"]:
        v.append("환승 초과")
    if actual is not None and q["arrive_by"] and q["depart"]:
        if _minutes(q["depart"]) * 60 + actual > _minutes(q["arrive_by"]) * 60:
            v.append("시한 초과")
    invented_time = int(
        ans.seconds is not None and actual is not None and abs(ans.seconds - actual) > 60
    )
    return Grade(
        answered=True,
        correct=not v and truth is not None and actual == truth.seconds,
        invented_stations=sum(s not in stations for s, _ in path),
        invented_time=invented_time,
        violations=v,
    )
```

테스트(작은 그래프로 만든 답을 넣는다): 정답 경로를 그대로 준 답 → 맞음 / 없는 역이 낀 답 → 지어낸 역 1, 경로 끊김 / 경로는 맞는데 시간을 크게 말한 답 → 지어낸 소요 시간 1 / 환승 상한 0인데 갈아탄 답 → 환승 초과 / 시한을 넘는 답 → 시한 초과 / 빈 답 → 답 없음, 맞음 거짓. 커밋: `feature: 답을 다익스트라 정답과 비교해 채점` <!-- style-exempt -->

### Task 6: 리포트와 명령 하나 — 끝까지 잇는다

**Files:** Create `src/subway_route_agent/report.py`, `src/subway_route_agent/cli.py`, `tests/test_cli.py`

- `cli.main(argv=None)`: `--answerer` (기본 `stub`, `ANSWERERS`의 키만). 데이터 → 그래프 → `data/questions.json` → 질문마다 `shortest`(정답) → 답하는 쪽 호출(`time.perf_counter`로 응답 시간) → `grade` → 리포트
- 리포트 머리: 답하는 쪽 이름, 데이터 출처(파일명, 손으로 넣은 데이터면 그 사실), 환승 180초 stub이라는 것, `정답률 N/3 (P%)`
- 표 열: `질문 | 정답 경로 | 정답 시간 | 답 있음 | 맞음 | 지어낸 역 | 지어낸 소요 시간 | 조건 어김 | 도구 호출 | 응답 시간(ms)`
  - 정답 경로는 출발역 · 갈아탄 역 · 도착역만 호선과 함께 쓴다(예: `강남(2) → 홍대입구(2)`)
  - 정답 시간은 `29분 0초`처럼 쓴다
- `reports/skeleton.md`에 쓰고 stdout에도 출력한다. 정답이 `None`인 질문이 있으면 그 행 정답 경로에 `없음`을 쓰고 exit code는 0을 유지한다(실패 징후 1의 「다시 잰다」 구간에서 읽을 수 있게)
- 테스트: `main([])`가 0을 돌려주고, 리포트에 `q1`·`q2`·`q3` 행과 `0/3`이 있다
- 커밋: `feature: subway-eval 명령 하나로 질문 3개를 끝까지 돌린다`

### Task 7: 개념 표, 실행 결과, jw 기준 측정

1. `docs/concepts.md`에 `## 개념` 표를 만든다(Kickoff 때 main이 `## 용어` 절을 먼저 만들어 둔다. 그 절은 고치지 않는다). 행: `Answer` 필드 3개, 조건 종류(`max_transfers`·`depart`·`arrive_by`), 조건 어김 5종, 리포트 열, `ANSWERERS` 목록. 열: 이름(코드 식별자) · 뜻 한 줄 · 정의한 파일·줄 · 만든 티켓(#185)
2. 워크트리에서 `uv run subway-eval`을 돌려 `reports/skeleton.md`를 커밋한다
3. 실패 징후 1을 잰다:
   ```bash
   T=$(mktemp -d) && git clone -q "$(pwd)" "$T/r" && cd "$T/r" && uv run subway-eval; echo "exit=$?"; ls reports/skeleton.md
   ```
   - 커밋 안 된 변경이 있으면 clone에 안 들어가므로 전부 커밋한 뒤 잰다
   - exit code, 리포트 존재, 정답 경로가 채워진 질문 수를 그대로 적는다. 구간(통과·다시 잰다·미완)을 고른다. 다시 잰다 구간이면 그래프를 고친 뒤 한 번 더 잰다
4. 실패 징후 2~4 값도 같이 적는다(닿지 않는 노드 수, q3 경로의 `둔촌동`·`상일동` 여부, 정답률)
5. 커밋: `docs: 개념 표와 skeleton 실행 결과`

---

## Pre-PR checks

Pre-PR checks (all required — do not assume pass, show output):
1. New env vars: `git diff main...HEAD` added lines matching `os\.environ\.get|os\.getenv|process\.env\.` — log any found.
2. Server boots — detached-safe, NO interactive Ctrl+C (no TTY in orch). Background + timeout + curl the port + kill. Never bare `runserver` (hangs the loop till ORCH_STUCK_SECS). Django → `source <venv>/bin/activate && cd web && (timeout 20 python manage.py runserver 127.0.0.1:8000 --noreload &) ; sleep 8; curl -sf http://127.0.0.1:8000/ -o /dev/null && echo BOOT_OK ; pkill -f runserver`; CDK → `cdk synth` (no server); Zappa/Lambda Django → same background+timeout with `PYENV_VERSION=<env> --settings=<app>.settings.local`; CLI/library → smoke-run the entrypoint (it must self-terminate); else project-specific.
   - 이 레포는 CLI다: `timeout 60 uv run subway-eval; echo exit=$?`
3. Full test suite green (show pass/fail). If no runner: state `no tests — skipped`, do not silently pass.
   - `uv run pytest -v` 와 `uv run ruff check .`

Then: completeness via `sc:reflect` vs plan; code review via `superpowers:requesting-code-review` (fix all Critical/Important); commit (`~/prv` repo면 `docs/plans/`도 포함); PR via `gh pr create --assignee @me --base main` (personal title + Summary/Changes/Notes, then update the Notion PR property). **PR을 만들면 이 루프는 끝난다** — 여기서 `pr-review-toolkit:review-pr`을 돌리지 말 것. 그 리뷰는 Phase C의 별도 세션이 맡는다.

내장 `/code-review`를 여기 쓰지 말 것 — 헤드리스 세션의 available-skills에 없다.

## Done criteria

- [ ] Task 1~7 완료, 각 Task가 커밋 하나
- [ ] Pre-PR checks 3개 출력이 PR 본문에 있다
- [ ] 실패 징후 1을 깨끗한 clone에서 재서, 값(exit code · 리포트 존재 · 정답 경로가 채워진 질문 수)과 구간을 `reports/skeleton.md` 아래와 PR 본문에 적었다. 실패 징후 2~4 값도 적었다
- [ ] PR 본문 맨 위에 `## 착수 전 기준 (jw)` 절 — plan의 `## jw 기준` 원문 + 그 기준으로 잰 결과
- [ ] `docs/concepts.md` `## 개념` 표를 만들었다. plan·리포트·PR 본문은 `docs/concepts.md` 용어 절의 말을 쓰고, 쓰지 말 말을 쓰지 않는다
- [ ] stub은 빈 답 그대로다. 정답률 0/3을 올리려고 stub을 채우지 않았다
- [ ] base 브랜치(`main`)를 작업 브랜치에 merge·rebase하지 않았다
- [ ] PR 생성: `gh pr create --assignee @me --base main`. 계정은 `jongwoo315`(`gh api user -q .login`으로 확인)
- [ ] Notion PR 프로퍼티 갱신:
  ```bash
  printf '{"properties":{"PR":{"url":"%s"}}}' "<PR URL>" > /tmp/pr185.json
  "$HOME/.claude/tools/notion-api/notion-api" PATCH /v1/pages/41341e61-65c0-81b6-8c96-caf861560aa5 /tmp/pr185.json
  ```
