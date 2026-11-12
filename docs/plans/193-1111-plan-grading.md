# #193 채점 방식 Implementation Plan

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
> Also before emitting it, `git status --porcelain` must print nothing. Commit what belongs in
> the PR; add generated files (run logs, caches, scratch output) to `.gitignore`. A leftover
> untracked file keeps the dispatcher waiting, and the review never starts.
> On a HARD, retry-proof API error (OpenAI insufficient_quota, 401/403, exhausted billing), STOP —
> do NOT emit RALPH_DONE, do NOT create a PR, do NOT spin retrying. It surfaces via the orch
> completion notification; a human fixes billing. (Transient TPM 429 is different — pace and retry.)
> A TRANSIENT error that stops being transient counts as HARD. If 429/529 keeps surfacing AND you
> have produced no commit and no file change for 20 minutes, STOP the same way. Waiting and
> spinning are indistinguishable in a headless loop — nobody is watching the screen, and the loop
> re-submits the prompt after every failed turn, so a server-side outage burns the whole iteration

**Tier:** B
**Notion:** #193 https://app.notion.com/p/41541e6165c08102a14af4101275e82a (page id `41541e61-65c0-8102-a14a-f4101275e82a`)
**설계:** `/Users/jw/prv/.wt/193-grading/docs/plans/193-1111-design-grading.md` — 착수 전에 먼저 읽는다. 설계 결정 표가 거기 있다
**흐름:** 이미 있다(#185~#188). 바꾸는 stub: 채점 규칙의 「이웃한 역끼리만 이어진다」(`grade.py`)

## jw 기준

지나는 역을 확실히 채점을 하든지 이동 경로를 정확히 계산했다면 지나는 역이 모두 나오지 않아도 정답으로 보는 채점방식으로 수정한다

## 통과 기준

- 채점이 답 경로의 빠진 중간 역을 채운 뒤 판정한다. 채우는 규칙은 설계 문서의 규칙 1(같은 호선)·규칙 2(갈아타는 역을 한 번만 쓴 것) 둘뿐이다
- 아래 Task 1의 손으로 만든 사례가 전부 기대대로 판정된다
- 지나는 역을 다 쓴 답(채운 역 0)은 판정이 #188과 같다
- 리포트·비교 리포트에 `채운 역` 열이 있고, 비교 리포트 머리에 답하는 쪽마다 「채우지 않고도 맞은 질문 수」가 있다
- `--raw`에 LLM + 도구의 질문별 도구 호출 기록이 남는다
- 테스트는 API를 부르지 않는다

## 이번에 안 하는 것

- 지시문(`SYSTEM`·`TOOLS_SYSTEM`)·도구 셋·`_parse` 수정. 정답률을 올리려고 LLM 쪽을 고치지 않는다
- 정답 없음 질문 채점(#187 리뷰 #4), 별칭 역 채점(#187 리뷰 #3)
- 답이 말한 시간을 맞음 조건에 넣는 것
- 환승 시간 stub (#189), 도구 크기 비교 (#190) <!-- style-exempt -->
- 질문 셋 변경

## 실패 징후

1. **jw 기준을 잰다.** 「이동 경로를 정확히 계산했다면 지나는 역이 모두 나오지 않아도 정답」이 되는지를 두 가지로 본다
   - 잴 방법 ①: Task 1의 손 사례 테스트(기대값이 표에 있다)
   - 잴 방법 ②: #188 main 실행 원문(`tests/fixtures/gate188/raw-llm-tools.json`, `raw-llm.json`)을 새 채점으로 다시 채점해 질문별 맞음을 설계 문서 §참고 값 표와 맞춰 본다. 참고 값: LLM + 도구 5/10(q1, q2, q3, q9, q10), LLM 혼자 0/10
   - 통과: ①이 전부 기대대로이고, ②에서 참고 값의 5개 질문이 모두 맞았다. 참고 값과 다른 질문이 있으면 전부 규칙 2(갈아타는 역 한 번) 때문이고 질문마다 그 사실을 적었다
   - 다시 잰다: ①은 전부 기대대로인데 ②에서 규칙 2로 설명되지 않는 차이가 1~2개다. 질문마다 원문 경로, 채운 경로, 두 채점의 판정을 나란히 적는다. 참고 스크립트(`docs/plans/193-1111-fill-reference.py.txt`)와 새 코드 중 어느 쪽이 무엇을 다르게 했는지 적는다
   - 미완: ① 중 하나라도 기대와 다르다, ②에서 설명되지 않는 차이가 3개 이상이다, 또는 지나는 역을 다 쓴 답의 판정이 #188과 달라졌다
2. **너무 너그러워졌는지.** 채울 수 없는 답(`서울역(1) → 잠실(2)` 등)을 맞았다고 채점하면 미완. 순환선에서 짧은 쪽으로 채운 질문 수는 값만 적는다
3. **새 채점으로 #188 비교를 다시 잰다.** 실제 키로 `uv run subway-eval --answerer stub llm llm-tools --raw runs/193/raw-1.json`을 두 번 돌린다(두 번째 `raw-2.json`). 실행마다 두 정답률, 채우지 않고도 맞은 질문 수, 채운 역 합을 적는다. 임계값 없음 — 이 티켓은 채점을 바꾸는 것이고 이 값은 다음 티켓의 기준값이다
4. **지시문을 안 지킨 원인.** 3의 두 실행에서 LLM + 도구 답 중 채운 역이 1개 이상인 질문마다, 채운 구간의 호선으로 `line_stations`를 불렀는지 `--raw`의 도구 호출 기록으로 센다. 「불렀는데 역을 빠뜨린 질문 수 / 안 불렀는데 빠뜨린 질문 수」를 적는다. 임계값 없음

## 파일 구성

| 파일 | 할 일 |
| --- | --- |
| `.github/workflows/test.yml` (새) | CI: pytest + ruff |
| `src/subway_route_agent/grade.py` | `fill_path`(채우기), `Grade.filled`, `grade`가 채운 경로로 판정 |
| `src/subway_route_agent/answerers.py` | `Answer.tool_log` 필드, `make_llm_tools`가 호출마다 기록. `SYSTEM`·`TOOLS_SYSTEM`·`SCHEMA`·`_parse`·`make_llm`은 그대로 |
| `src/subway_route_agent/cli.py` | `_write_raw`에 `tool_log` |
| `src/subway_route_agent/report.py` | `채운 역` 열, 비교 리포트 머리 줄 |
| `tests/test_grade.py` | 손 사례, 실제 그래프 사례 |
| `tests/test_regrade_188.py` (새) | #188 원문 다시 채점 |
| `tests/test_llm_tools.py`, `tests/test_cli.py` | `tool_log`, 새 열 |
| `tests/fixtures/gate188/` | 이미 커밋돼 있다(#188 main 실행 원문). 고치지 않는다 |
| `reports/*.md` | 측정 명령으로 다시 생성 |
| `docs/concepts.md` | `## 개념` 표 |

### Task 0: CI

**Files:** Create `.github/workflows/test.yml`

- jw 지시(2026-11-11): 이 레포에도 CI를 넣는다. `~/prv/cheongyak-extract/.github/workflows/test.yml`과 같은 꼴로 쓰고 ruff를 더한다
  ```yaml
  name: test

  on:
    push:
      branches: [main]
    pull_request:

  jobs:
    pytest:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: astral-sh/setup-uv@v5
        - run: uv sync
        - run: uv run pytest -q
        - run: uv run ruff check .
  ```
- CI에는 `OPENAI_API_KEY`가 없다. 테스트가 키 없이 통과해야 한다(이미 그렇게 짜여 있다)
- 커밋: `add: GitHub Actions 테스트`

### Task 1: 빠진 역 채우기

**Files:** Modify `src/subway_route_agent/grade.py`, `tests/test_grade.py`

- `fill_path(g, path) -> tuple[list[Node], int] | None`: 채운 경로와 채운 역 수. 못 채우면 `None`
  - 붙은 두 노드가 그래프에서 이웃하면(환승 간선 포함) 그대로 둔다
  - 규칙 1: 같은 호선이고 이웃하지 않으면 그 호선 간선만으로 가장 짧은 길(다익스트라)의 중간 노드를 넣는다. 6호선 한 방향 구간은 그래프 방향 그대로 따른다
  - 규칙 2: 호선이 다르고 뒤 역이 앞 호선에도 있으면 `앞 → … → (뒤 역, 앞 호선) → (뒤 역, 뒤 호선)`으로 채운다. `(뒤 역, 앞 호선)`은 채운 역 수에 1로 센다
  - 그 밖은 못 채운다. 데이터에 없는 역이 하나라도 있으면 못 채운다
  - `route.shortest`를 쓰지 않는다(여러 호선을 거치는 길을 만들면 안 된다). `tools.travel_seconds`와 같은 한 호선 다익스트라를 쓰되, 공용 함수로 뽑아도 된다
- `Grade.filled: int`(채운 역 수, 못 채우면 0). `grade()`는 채운 경로가 있으면 그것으로 실제 소요 시간·출발·도착역·환승 수·시한·지어낸 소요 시간을 보고, 못 채우면 지금처럼 `경로 끊김`. 지어낸 역 수는 원래 답 경로로 센다
- 테스트 먼저 — 실제 그래프(`build_graph(load_rows())`)와 `data/questions.json`의 q1·q2로 손 사례를 고정한다

  | 사례 | 답 경로 | 기대 |
  | --- | --- | --- |
  | A | q2: `서울역(4) → 동대문역사문화공원(4) → 동대문역사문화공원(2) → 잠실(2)` | 맞음, 채운 역 13 |
  | B | q2: `서울역(4) → 동대문역사문화공원(2) → 잠실(2)` (갈아타는 역 한 번) | 맞음, 채운 역 14 |
  | C | q2: `서울역(1) → 시청(1) → 시청(2) → 잠실(2)` (더 느린 길) | 틀림, 실제 소요 시간 1,530초, 조건 어김 없음 |
  | D | q2: `서울역(1) → 잠실(2)` | 틀림, `경로 끊김`, 채운 역 0 |
  | E | q2: `hand_path` 전부 | 맞음, 채운 역 0 |
  | F | q1: `강남(2) → 홍대입구(2)` | 맞음(짧은 쪽으로 채움), 실제 소요 시간 1,740초 |
  | G | q2: `서울역(4) → 없는역(4) → 잠실(2)` | 틀림, `경로 끊김`, 지어낸 역 1 |

  - 기대한 채운 역 수가 실제와 다르면 기대값을 맞추지 말고 CSV에서 중간 역을 다시 센다. 손으로 세어 적은 값이 틀렸으면 고치고 그 사실을 PR 본문에 적는다
  - 기존 `tests/test_grade.py` 테스트는 그대로 통과해야 한다. 작은 그래프에서 같은 호선 두 역을 건너뛴 사례가 「끊김」을 기대하고 있으면, 그 테스트를 지우지 말고 기대를 새 규칙대로 바꾼 뒤 그 이유를 커밋 메시지에 적는다
- 커밋: `feature: 채점이 답 경로의 빠진 중간 역을 같은 호선 안에서 채운 뒤 판정한다`

### Task 2: #188 원문 다시 채점

**Files:** Create `tests/test_regrade_188.py`

- `tests/fixtures/gate188/raw-llm-tools.json`·`raw-llm.json`의 원문을 `_parse`로 읽고(실패·빈 경로는 답 없음), `cli.truth_for`로 정답을 구해 새 `grade`로 채점한다
- 테스트: 지나는 역을 다 쓴 답(새 채점에서 채운 역 0)은 옛 판정(`fill_path`를 거치지 않은 판정)과 같다. 옛 판정은 테스트 안에서 `path_seconds`만으로 다시 구현해도 된다
- 실패 징후 1 ②의 질문별 결과 표(질문 · 원문 경로 요약 · 채운 역 · 새 판정 · 참고 값 판정)를 PR 본문에 넣는다. 차이를 테스트로 박지 말고 표로만 적는다 — 참고 값도 main이 쓴 것이라 정답이 아니다
- 커밋: `test: #188 main 실행 원문을 새 채점으로 다시 채점한다`

### Task 3: 리포트와 도구 호출 기록

**Files:** Modify `report.py`, `answerers.py`, `cli.py`, `tests/test_cli.py`, `tests/test_llm_tools.py`

- 리포트(`render`) 열에 `채운 역`(`맞음` 다음). 비교 리포트 표에도 답하는 쪽마다 `<이름> 채운 역`
- 비교 리포트 머리 줄에 `채우지 않고도 맞은 질문 K/N`(맞음이고 채운 역 0)
- `Answer.tool_log: list[dict]` (기본 빈 목록). `make_llm_tools`가 도구 호출마다 `{"name", "arguments", "output": 결과 앞 200자}`를 쌓는다. `_write_raw`가 `tool_log`를 같이 쓴다
- 테스트: 열·머리 줄, 가짜 client로 `tool_log` 두 건, `--raw` 파일에 `tool_log`가 있다
- 기존 녹화 재생 테스트가 열 위치(`rows[qid][8]` 등)로 읽다가 깨지면 열 이름으로 찾도록 고친다
- 커밋: `feature: 리포트에 채운 역 수를, --raw에 도구 호출 기록을 남긴다`

### Task 4: 실제 호출 측정과 개념 표

1. 실제 키로 두 번 돌린다
   ```bash
   mkdir -p runs/193
   uv run subway-eval --answerer stub llm llm-tools --raw runs/193/raw-1.json --out runs/193/compare-1.md; echo "exit=$?"
   uv run subway-eval --answerer stub llm llm-tools --raw runs/193/raw-2.json; echo "exit=$?"
   ```
   두 번째 실행이 `reports/`의 리포트 넷을 쓴다. 실패 징후 3·4 값을 센다. `runs/`는 `.gitignore`에 있다
2. 실패 징후 4: `runs/193/raw-*-llm-tools.json`의 `tool_log`로 센다. 세는 데 쓴 스크립트는 커밋하지 않아도 되지만 명령과 결과를 PR 본문에 적는다
3. `docs/concepts.md` `## 개념` 표: `fill_path`, `Grade.filled`, `채운 역` 열, `Answer.tool_log`를 더하고 `경로 끊김`이 「채울 수 없을 때」로 바뀐 것을 적는다(행이 없으면 더한다). 정의한 곳 줄 번호는 실제 파일에서 확인한다. `## 용어` 절은 고치지 않는다(Kickoff에서 main이 썼다)
4. 커밋: `docs: #193 리포트` / `docs: #193 개념 표`

## Pre-PR checks

Pre-PR checks (all required — do not assume pass, show output):
1. New env vars: `git diff main...HEAD` added lines matching `os\.environ\.get|os\.getenv|process\.env\.` — log any found.
   - 이번에는 나오지 않아야 한다. 나오면 `.env.example`에 있는지 같이 본다
2. Server boots — detached-safe, NO interactive Ctrl+C (no TTY in orch). Background + timeout + curl the port + kill. Never bare `runserver` (hangs the loop till ORCH_STUCK_SECS). Django → `source <venv>/bin/activate && cd web && (timeout 20 python manage.py runserver 127.0.0.1:8000 --noreload &) ; sleep 8; curl -sf http://127.0.0.1:8000/ -o /dev/null && echo BOOT_OK ; pkill -f runserver`; CDK → `cdk synth` (no server); Zappa/Lambda Django → same background+timeout with `PYENV_VERSION=<env> --settings=<app>.settings.local`; CLI/library → smoke-run the entrypoint (it must self-terminate); else project-specific.
   - 이 레포는 CLI다: `env -u OPENAI_API_KEY timeout 60 uv run subway-eval; echo exit=$?` 와 `timeout 900 uv run subway-eval --answerer stub llm llm-tools --out /tmp/compare-smoke.md; echo exit=$?`
3. Full test suite green (show pass/fail). If no runner: state `no tests — skipped`, do not silently pass.
   - `env -u OPENAI_API_KEY uv run pytest -q` 와 `uv run ruff check .`

Then: completeness via `sc:reflect` vs plan; code review via `superpowers:requesting-code-review` (fix all Critical/Important); commit (`~/prv` repo면 `docs/plans/`도 포함); PR via `gh pr create --assignee @me --base main` (personal title + Summary/Changes/Notes, then update the Notion PR property). **PR을 만들면 이 루프는 끝난다** — 여기서 `pr-review-toolkit:review-pr`을 돌리지 말 것. 그 리뷰는 Phase C의 별도 세션이 맡는다.

내장 `/code-review`를 여기 쓰지 말 것 — 헤드리스 세션의 available-skills에 없다.


## Done criteria

- [ ] Task 0~3은 커밋 하나씩, Task 4는 커밋 둘
- [ ] PR의 CI(`test` 워크플로)가 통과했다: `gh pr checks <PR 번호> --watch`의 출력을 PR 본문에 적는다. 실패하면 고쳐서 push하고 다시 본다
- [ ] Pre-PR checks 3개 출력이 PR 본문에 있다
- [ ] 실패 징후 1을 재서 ① 손 사례 결과와 ② 질문별 표, 구간을 PR 본문에 적었다
- [ ] 실패 징후 2~4 값을 PR 본문에 적었다
- [ ] PR 본문 맨 위에 `## 착수 전 기준 (jw)` 절 — plan의 `## jw 기준` 원문 + 그 기준으로 잰 결과
- [ ] `docs/concepts.md` `## 개념` 표를 고쳤다. plan·리포트·PR 본문은 `docs/concepts.md` 용어 절의 말을 쓰고, 쓰지 말 말을 쓰지 않는다
- [ ] LLM 쪽을 고치지 않았다: `git diff main...HEAD -- src/subway_route_agent/answerers.py`에서 `SYSTEM`·`TOOLS_SYSTEM`·`SCHEMA`·`_parse`·`make_llm` 줄이 바뀌거나 지워진 것이 없다. `src/subway_route_agent/tools.py`·`data/questions.json`·`tests/fixtures/gate188/` diff가 비었다
- [ ] 테스트는 API를 부르지 않는다(`OPENAI_API_KEY`를 지운 환경에서 `uv run pytest -q`가 통과한다)
- [ ] base 브랜치(`main`)를 작업 브랜치에 merge·rebase하지 않았다
- [ ] PR 생성: `gh pr create --assignee @me --base main`. 계정은 `jongwoo315`(`gh api user -q .login`으로 확인)
- [ ] Notion PR 프로퍼티 갱신:
  ```bash
  printf '{"properties":{"PR":{"url":"%s"}}}' "<PR URL>" > /tmp/pr193.json
  "$HOME/.claude/tools/notion-api/notion-api" PATCH /v1/pages/41541e61-65c0-8102-a14a-f4101275e82a /tmp/pr193.json
  ```
