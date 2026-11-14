# #190 도구 구성 비교 Implementation Plan

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
> budget while the picker still reads `working`.

**Tier:** B
**Notion:** #190 https://app.notion.com/p/41441e6165c081c9b17bf7d2d51d5e31 (page id `41441e61-65c0-81c9-b17b-f7d2d51d5e31`)
**설계:** `/Users/jw/prv/.wt/190-tool-granularity/docs/plans/190-1114-design-tool-granularity.md` — 착수 전에 먼저 읽는다. 두 구성의 정보를 맞춘 이유, 도구 정의, 세 안 비교가 거기 있다
**흐름:** 이미 있다(#185~#189). 바꾸는 stub: 도구 구성이 하나뿐인 것(`tools.py` `TOOLS`)
**도구 구성:** A안 — Kickoff에서 jw가 골랐다

## jw 기준

도구 구성에 따라 정답과 결과에 대한 통계값들이 어떻게 바뀌는지 확인할 수 있다, 최적의 도구 수를 판단할 수 있다

## 통과 기준

- 명령 하나(`uv run subway-eval --answerer llm-tools llm-tools-coarse --repeat 3`)로 두 도구 구성이 같은 질문 셋에 각각 세 번 답하고, 비교 리포트(`reports/compare.md`)에 회차별 지표 표와 실행 간 범위가 나란히 나온다
- 지표 일곱 개: 정답률, 지어낸 역(합), 지어낸 소요 시간(질문 수), 질문당 도구 호출(평균), 질문당 응답 시간(평균 초), 파싱 실패, 토큰
- 크게 묶은 도구(`route_seconds`)는 경로를 돌려주지 않는다. 출력 키가 테스트로 고정돼 있다
- 두 구성의 지시문은 도구 안내 한 문장만 다르다. 테스트로 고정한다
- 테스트는 API와 네트워크를 부르지 않는다

## 이번에 안 하는 것

- 도구 구성 셋 이상(티켓)
- 질문 셋(`data/questions.json`)·채점(`grade.py`)·정답 계산(`route.py`·`graph.py`)
- `SYSTEM`·`SCHEMA`·`_parse` 수정
- LLM 혼자(`llm`) 다시 측정하기
- 녹화 fixture(`tests/fixtures/`) 다시 녹화

## 실패 징후

1. **jw 기준을 잰다.** 「도구 구성에 따라 정답과 결과에 대한 통계값들이 어떻게 바뀌는지 확인할 수 있다, 최적의 도구 수를 판단할 수 있다」
   - 측정값 ①: 비교 리포트의 회차별 지표 표에 두 구성 × 회차 × 지표 일곱 개가 빈칸 없이 있는가
   - 측정값 ②: 두 구성의 정답률 실행 간 범위(최저~최고)가 겹치는가. 한쪽 최저가 다른 쪽 최고보다 높으면 겹치지 않는 것이다
   - 질문당 도구 호출과 질문당 응답 시간의 범위가 겹치는지도 같은 방법으로 적는다(구간 판정에는 안 쓴다)
   - baseline: #189 실제 키 LLM + 도구 3/10·4/10, 도구 호출 합 52(그때 도구는 3개, 환승 시간 도구 없음 — 이번 잘게 나눈 도구와 조건이 다르다)
   - 통과: ① 빈칸 0이고 ② `--repeat 3`에서 겹치지 않는다
   - 다시 잰다: ① 빈칸 0이고 ② `--repeat 3`에서 겹친다. `--repeat 5`로 한 번 더 돌려 그 리포트로 ②를 다시 본다. 두 리포트를 다 PR 본문에 적는다
   - 미완: `--repeat 5`에서도 겹친다. 또는 ①에 빈칸이 있다
2. **크게 묶은 도구가 경로를 알려 준다.** `route_seconds` 출력에 `seconds`·`transfers`·`error`·`candidates`·`lines` 말고 다른 키가 나오면 미완이다. `--repeat 3` 실행의 `--raw` `tool_log`에서 `route_seconds` 출력 키를 모두 모아 PR 본문에 적는다
3. **크게 묶은 쪽이 도구를 안 쓴다.** 크게 묶은 쪽의 질문당 도구 호출 평균이 회차마다 0.5 미만이면 LLM 혼자와 다를 게 없다. 그 사실을 PR 본문 맨 위에 적는다(임계값 0.5는 이번이 첫 측정이라 정한 값이다)
4. **도구 호출 상한.** 회차마다 도구 호출 상한(25)에 닿은 질문 수를 적는다. 한 회차에서 3개 이상이면 그 질문의 `tool_log`를 PR 본문에 요약한다  <!-- style-exempt -->

## 바꾸는 파일

- Modify: `src/subway_route_agent/tools.py`, `answerers.py`, `cli.py`, `report.py`
- Modify: `tests/test_tools.py`, `tests/test_llm_tools.py`, `tests/test_cli.py`
- Modify: `reports/compare.md`(실제 키 실행 결과), `docs/concepts.md` `## 개념` 표

## Tasks

### Task 1: 도구 두 개를 더한다

**Files:** `tools.py`, `tests/test_tools.py`

- `transfer_seconds(station, from_line, to_line) -> dict`: 그래프의 `(역, from_line) → (역, to_line)` 간선 가중치를 `{"seconds": N}`로 돌려준다. 역 이름은 `_name`(별칭)을 거친다. 두 노드가 그래프에 없거나 간선이 없으면 `{"error": …}`. 값을 따로 계산하지 않는다 — 그래프 간선이 정답 계산과 같은 값이다
- `route_seconds(path: list[dict]) -> dict`: `path`는 `[{"station": str, "line": int}]`
  1. 역마다 별칭을 거친 이름으로 본다. 데이터에 없는 역이면 `{"error": "<역>은 데이터에 없다", "candidates": [...]}`(`find_station`의 후보와 같다). 그 호선에 없으면 `{"error": "<역>은 <N>호선에 없다", "lines": [...]}`
  2. `grade.fill_path`로 채우고 `grade.path_seconds`로 잰다. 못 채우면 `{"error": "<i>번째와 <i+1>번째를 이을 수 없다"}`(1부터 센다. 어느 쌍에서 못 채웠는지 찾으려면 앞에서부터 두 노드씩 `fill_path`를 불러 본다)
  3. 성공: `{"seconds": N, "transfers": K}`. K는 채운 경로에서 호선이 바뀐 횟수
  - 경로·역 목록을 돌려주지 않는다
  - `grade`를 모듈 맨 위에서 import하면 `tools → grade → answerers → tools`로 순환한다. 함수 안에서 import하고 이유를 주석 한 줄로 단다
- `TOOLS`를 두 목록으로 나눈다: `FINE_TOOLS`(지금 셋 + `transfer_seconds`), `COARSE_TOOLS`(`route_seconds` 하나). `route_seconds`의 `path` 파라미터 schema는 `answerers.SCHEMA`의 path와 같은 구조로 `tools.py` 안에 쓴다(answerers를 import하지 않는다)
- `call_tool(name, arguments, tools)`: 받은 도구 목록에 없는 이름은 `{"error": "모르는 도구: …"}`. 인자 형식 검사를 `path`(dict 목록, 각 dict가 `station: str`·`line: int`)까지 넓힌다
- 테스트(실제 데이터):
  - `transfer_seconds("이수", 4, 7)` = 환승 CSV의 이수 4→7 값(테스트가 CSV를 `csv` 모듈로 읽어 비교할 값으로 쓴다), `transfer_seconds("까치산", 2, 5)` = CSV의 5→2 값, `transfer_seconds("강남", 2, 3)` → error
  - `route_seconds`: q2 정답 경로를 출발·갈아타는 역·도착만 남겨 넘기면 `cli.truth_for` 정답 소요 시간·환승 수와 같다. 없는 역 → `candidates`, 호선이 틀린 역 → `lines`, 이을 수 없는 경로 → error에 몇 번째인지
  - 출력 키 고정: 위 네 경우의 출력 키가 `{seconds, transfers, error, candidates, lines}` 안에 있다
  - `call_tool`: 다른 구성의 도구 이름을 부르면 모르는 도구 오류, `path` 인자 형식이 틀리면 인자 오류
- 커밋: `feature: 환승 시간 도구와 경로 소요 시간 도구를 더한다`

### Task 2: 크게 묶은 도구를 받는 답하는 쪽

**Files:** `answerers.py`, `tests/test_llm_tools.py`

- `make_llm_tools(client=None, tools=FINE_TOOLS, system=TOOLS_SYSTEM)`. 루프 안의 `TOOLS`·`TOOLS_SYSTEM`·`call_tool` 호출을 인자로 바꾼다. 다른 동작은 그대로
- 지시문 두 개. `SYSTEM` 뒤에 도구 안내 한 문장 + 공통 꼬리 「 환승 시간은 역과 호선마다 다르다. 경로는 직접 고른다.」
  - `TOOLS_SYSTEM`(잘게 나눈 도구): 도구 안내 「 도구로 역·노선·한 호선 안 소요 시간·환승 시간을 확인할 수 있다.」
  - `COARSE_SYSTEM`(크게 묶은 도구): 도구 안내 「 도구로 고른 경로의 전체 소요 시간을 확인할 수 있다.」
- `ANSWERERS`에 `"llm-tools-coarse"`(첫 호출 때 client를 만든다, `llm-tools`와 같은 방식)
- 테스트(FakeClient, API 없음):
  - `llm-tools-coarse`가 `COARSE_TOOLS`와 `COARSE_SYSTEM`으로 부르고, `route_seconds` 호출 결과를 붙여 다시 부른다
  - 두 지시문이 도구 안내 문장만 다르다: 각각에서 도구 안내 문장을 지우면 같은 문자열이다. 둘 다 `SYSTEM`으로 시작하고 `180`이 없다
  - 기존 녹화 재생 테스트는 fixture를 다시 녹화하지 않는다. `call["tools"] == TOOLS` 같은 비교가 깨지면 `FINE_TOOLS`로 고친다
- 커밋: `feature: 크게 묶은 도구로 답하는 쪽을 더한다`

### Task 3: `--repeat`와 비교 리포트 지표

**Files:** `cli.py`, `report.py`, `tests/test_cli.py`

- `cli.py`
  - `--repeat N`(기본 1, 1 이상). 답하는 쪽마다 질문 셋을 N번 돈다. `LLM_ANSWERERS`에 `llm-tools-coarse`  <!-- style-exempt -->
  - `--raw`는 N이 2 이상이면 `<파일명>-<이름>-<회차>.json`
  - `_notes`: 답하는 쪽마다 그 구성의 도구 이름과 호출 상한  <!-- style-exempt -->
  - 답하는 쪽 하나 리포트(`render`)는 마지막 회차로 쓴다
- `report.py` `render_compare`
  - 받는 값을 `dict[str, list[list[Result]]]`(답하는 쪽 → 회차 → 질문)로 바꾼다. 회차가 하나여도 같은 모양이다
  - 머리: 지금 줄들 + 두 구성의 도구 이름과 지시문 차이 한 줄 + 「크게 묶은 도구는 한 호선의 역 목록을 볼 수 없다」 한 줄(`llm-tools-coarse`가 있을 때만). `COMPARE_DIFF`는 새 지시문에 맞게 고친다
  - 회차별 지표 표: 행 = 답하는 쪽 × 회차, 열 = 실패 징후 1의 지표 일곱 개 + 도구 호출 상한에 닿은 질문 수. 답하는 쪽마다 맨 아래 「범위」 행에 지표별 최저~최고  <!-- style-exempt -->
    - 정답률 `K/N`, 지어낸 역 = `Grade.invented_stations` 합, 지어낸 소요 시간 = `Grade.invented_time`이 1인 질문 수, 질문당 도구 호출 = 합 ÷ 질문 수(소수 1자리), 질문당 응답 시간 = 합 ÷ 질문 수(초, 소수 1자리)
  - 질문 표: 회차가 1이면 지금 형식 그대로. 2 이상이면 열 = 질문 · 정답 시간 · `<이름> 맞은 횟수`(`K/N`) · `<이름> 도구 호출`(회차별, 예 `3/5/4`)
- 테스트: `--repeat 2` stub 실행이 끝까지 돌고 비교 리포트에 회차별 지표 표·범위 행이 있다, 가짜 Result로 범위 계산(최저~최고)·질문당 평균을 확인한다, 회차 1 비교 리포트의 질문 표가 지금 열 그대로다
- 커밋: `feature: 비교 리포트에 회차별 지표와 실행 간 범위를 적는다`

### Task 4: 측정과 개념 표

1. 실제 키로 돌린다. 오래 걸리므로 백그라운드로 돌리고 끝나면 TaskStop 대상이 남지 않게 한다
   ```bash
   mkdir -p runs/190
   timeout 3600 uv run subway-eval --answerer llm-tools llm-tools-coarse --repeat 3 --raw runs/190/raw.json; echo "exit=$?"
   ```
   `reports/compare.md`·`reports/llm-tools.md`·`reports/llm-tools-coarse.md`를 커밋한다. `runs/`는 `.gitignore`에 있다
2. 실패 징후 1 ②가 「다시 잰다」면:
   ```bash
   timeout 5400 uv run subway-eval --answerer llm-tools llm-tools-coarse --repeat 5 --raw runs/190/raw5.json --out runs/190/compare-5.md; echo "exit=$?"
   ```
   `runs/190/compare-5.md`의 회차별 지표 표를 PR 본문에 옮긴다(파일은 커밋하지 않는다)
3. 실패 징후 2~4를 `runs/190/raw-*.json`의 `tool_log`와 리포트에서 센다. 센 명령을 PR 본문에 적는다
4. `docs/concepts.md` `## 개념` 표: `transfer_seconds`, `route_seconds`, `FINE_TOOLS`·`COARSE_TOOLS`, `COARSE_SYSTEM`, `llm-tools-coarse`, `--repeat`를 더하고 `TOOLS_SYSTEM`·`ANSWERERS`·`compare.md`·`--answerer` 여러 값·`llm-tools` 행을 고친다. 정의한 곳 줄 번호는 실제 파일에서 확인한다. `## 용어` 절은 고치지 않는다(Kickoff에서 main이 썼다)
5. 커밋: `docs: #190 리포트` / `docs: #190 개념 표`

## Pre-PR checks

Pre-PR checks (all required — do not assume pass, show output):
1. New env vars: `git diff main...HEAD` added lines matching `os\.environ\.get|os\.getenv|process\.env\.` — log any found.
   - 이번에는 나오지 않아야 한다. 나오면 `.env.example`에 있는지 같이 본다
2. Server boots — detached-safe, NO interactive Ctrl+C (no TTY in orch). Background + timeout + curl the port + kill. Never bare `runserver` (hangs the loop till ORCH_STUCK_SECS). Django → `source <venv>/bin/activate && cd web && (timeout 20 python manage.py runserver 127.0.0.1:8000 --noreload &) ; sleep 8; curl -sf http://127.0.0.1:8000/ -o /dev/null && echo BOOT_OK ; pkill -f runserver`; CDK → `cdk synth` (no server); Zappa/Lambda Django → same background+timeout with `PYENV_VERSION=<env> --settings=<app>.settings.local`; CLI/library → smoke-run the entrypoint (it must self-terminate); else project-specific.
   - 이 레포는 CLI다: `env -u OPENAI_API_KEY timeout 60 uv run subway-eval; echo exit=$?` 와 `timeout 1800 uv run subway-eval --answerer llm-tools llm-tools-coarse --out /tmp/compare-smoke.md; echo exit=$?`
3. Full test suite green (show pass/fail). If no runner: state `no tests — skipped`, do not silently pass.
   - `env -u OPENAI_API_KEY uv run pytest -q` 와 `uv run ruff check .`

Then: completeness via `sc:reflect` vs plan; code review via `superpowers:requesting-code-review` (fix all Critical/Important); commit (`~/prv` repo면 `docs/plans/`도 포함); PR via `gh pr create --assignee @me --base main` (personal title + Summary/Changes/Notes, then update the Notion PR property). **PR을 만들면 이 루프는 끝난다** — 여기서 `pr-review-toolkit:review-pr`을 돌리지 말 것. 그 리뷰는 Phase C의 별도 세션이 맡는다.

내장 `/code-review`를 여기 쓰지 말 것 — 헤드리스 세션의 available-skills에 없다.

## Done criteria

- [ ] Task 1~3은 커밋 하나씩, Task 4는 커밋 둘
- [ ] PR의 CI(`test` 워크플로)가 통과했다: `gh pr checks <PR 번호> --watch`의 출력을 PR 본문에 적는다. 실패하면 고쳐서 push하고 다시 본다
- [ ] Pre-PR checks 3개 출력이 PR 본문에 있다
- [ ] 실패 징후 1을 재서 측정값 ①·②와 구간을 PR 본문에 적었다. 회차별 지표 표(3회, 다시 쟀으면 5회도)를 PR 본문에 옮겼다
- [ ] 실패 징후 2~4 값을 PR 본문에 적었다
- [ ] PR 본문 맨 위에 `## 착수 전 기준 (jw)` 절 — plan의 `## jw 기준` 원문 + 그 기준으로 잰 결과
- [ ] `docs/concepts.md` `## 개념` 표를 고쳤다. plan·리포트·PR 본문은 `docs/concepts.md` 용어 절의 말을 쓰고, 쓰지 말 말을 쓰지 않는다
- [ ] 바꾸지 않을 것을 바꾸지 않았다: `git diff main...HEAD -- src/subway_route_agent/grade.py src/subway_route_agent/route.py src/subway_route_agent/graph.py data/ tests/fixtures/` 출력이 비었다. `answerers.py`의 `SYSTEM`·`SCHEMA`·`_parse`는 diff가 없다
- [ ] 테스트는 API와 네트워크를 부르지 않는다(`OPENAI_API_KEY`를 지운 환경에서 `uv run pytest -q`가 통과한다)
- [ ] 「손 계산」이라는 말을 쓰지 않는다. 「직접 계산」으로 쓴다
- [ ] base 브랜치(`main`)를 작업 브랜치에 merge·rebase하지 않았다
- [ ] PR 생성: `gh pr create --assignee @me --base main`. 계정은 `jongwoo315`(`gh api user -q .login`으로 확인, 아니면 `gh auth switch -u jongwoo315`)
- [ ] Notion PR 프로퍼티 갱신:
  ```bash
  printf '{"properties":{"PR":{"url":"%s"}}}' "<PR URL>" > /tmp/pr190.json
  "$HOME/.claude/tools/notion-api/notion-api" PATCH /v1/pages/41441e61-65c0-81c9-b17b-f7d2d51d5e31 /tmp/pr190.json
  ```
