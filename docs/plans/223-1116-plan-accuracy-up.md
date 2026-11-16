# #223 정답률 올리기 Implementation Plan

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
**Notion:** #223 https://app.notion.com/p/41a41e6165c08111801eeda45f117acd (page id `41a41e61-65c0-8111-801e-eda45f117acd`)
**설계:** `/Users/jw/prv/.wt/223-accuracy-up/docs/plans/223-1116-design-accuracy-up.md` — 착수 전에 먼저 읽는다. #190 오답 원인 표, 세 안 비교, 도구 정의가 거기 있다
**흐름:** 이미 있다(#185~#190). 바꾸는 stub: 경로를 고르는 일을 LLM이 하는 것(`_TOOLS_TAIL` 「경로는 직접 고른다」) — 경로 탐색 도구를 더한다
**안:** A안 — 경로 탐색 도구(`llm-tools-search`)

## jw 기준

정답률이 이전 PR보다 현저히 올라간다 (정답률 평균 80% 이상)

## 통과 기준

- 실제 키로 `uv run subway-eval --answerer llm-tools llm-tools-coarse llm-tools-search --repeat 5 --raw runs/223/raw`를 돌린 비교 리포트 `reports/compare.md`가 있고, 회차별 지표 표에 세 도구 구성 × 5회차 × 지표 빈칸이 없다
- 경로 탐색 도구(`llm-tools-search`)의 회차별 맞힌 질문 수와 평균이 PR 본문 맨 위에 있다
- 평균 차이 줄에 `llm-tools-search` 대 `llm-tools`(이전 PR에서 정답률이 가장 높던 구성) 줄이 있다
- 테스트는 API·네트워크를 부르지 않는다

## 실패 징후

1. **jw 기준** — `llm-tools-search`의 5회차 평균 맞힌 질문 수(/10)로 본다. 「현저히」는 같은 실행의 `llm-tools` 대비 평균 차이 `d`가 표준오차 2배 `e` 이상인지로 본다(#190과 같은 방법)
   - 통과: 5회차 평균 8.0 이상이고 `llm-tools` 대비 `d ≥ e`
   - 다시 잰다: 5회차 평균 7.0 이상 8.0 미만. `--repeat 10 --raw runs/223/raw10 --out runs/223/compare-10.md`로 따로 한 번 더 돌리고 그 결과로 본다
   - 미완: 5회차 평균 7.0 미만, 또는 10회차도 8.0 미만, 또는 `d < e`, 또는 회차별 지표 표에 빈칸
   - baseline: #190 두 번째 측정(10회차) `llm-tools` 평균 4.40, `llm-tools-coarse` 3.10. 다만 이번에 공통 `SYSTEM`에 시한 문장이 더해져 조건이 다르다. 같은 실행에서 잰 `llm-tools` 값을 비교 대상으로 쓴다
2. **도구가 정답과 같은 함수다** — `shortest_route`는 `route.shortest`를 부른다. 틀린 답의 원인을 PR 본문에 질문 수로 적는다: 파싱 실패 / 역 이름을 잘못 읽음(도구에 넘긴 출발·도착이 질문과 다름) / 환승 상한을 잘못 넘김(도구에 넘긴 `max_transfers`가 질문과 다름) / 시한 비교를 안 함(q6에 경로를 냄) / 도구 결과와 다른 경로를 냄 / 그 밖. `tool_log`의 입력 인자를 질문 필드(`origin`·`dest`·`max_transfers`)와 맞춰 센다. 「도구 결과와 다른 경로를 냄」이 2건 이상이면 PR 본문에 사례를 적는다  <!-- style-exempt -->
3. **도구를 안 쓴다** — `llm-tools-search` 질문당 도구 호출이 1.0 미만인 회차가 있으면 의심. 회차별 값을 PR 본문에 적는다
4. **시한 문장이 다른 구성을 바꿨다** — `llm-tools`·`llm-tools-coarse`의 q6 맞힌 횟수를 #190 10회차 값(0/10·1/10)과 나란히 PR 본문에 적는다. 판정에 안 쓰는 참고값이다

## 이번에 안 하는 것

- 질문 셋·정답·채점 규칙(`grade.py`·`_parse`). 파싱 실패 「`no_route` true + path 있음」도 그대로 둔다
- `llm-tools`·`llm-tools-coarse`의 도구와 지시문(공통 `SYSTEM` 한 문장 말고)
- 최적의 도구 수 판정(게이트에서 jw가 한다). 측정값만 만든다
- 시한 비교를 도구가 하게 만드는 것 — LLM이 한다

## 바꾸는 파일

- `src/subway_route_agent/tools.py` — `shortest_route`, `SEARCH_TOOLS`, `call_tool`의 nullable 정수 인자
- `src/subway_route_agent/answerers.py` — `SYSTEM` 한 문장, `SEARCH_SYSTEM`, `llm-tools-search` 등록
- `src/subway_route_agent/cli.py` — `LLM_ANSWERERS`·`TOOL_SETS`에 `llm-tools-search`
- `src/subway_route_agent/report.py` — 평균 차이 줄을 답하는 쪽 셋 이상에서도 쓴다, 머리 줄 도구 이름
- `tests/` — 각 Task의 테스트
- `reports/`, `docs/concepts.md`

바꾸지 않을 것: `grade.py`·`route.py`·`graph.py`·`data.py`·`data/`·`tests/fixtures/`, `SCHEMA`·`_parse`.

## Tasks

### Task 1: 경로 탐색 도구 `shortest_route`

1. 실패하는 테스트를 먼저 쓴다(`tests/test_tools.py`)
   - `shortest_route("서울역", "잠실", None)`의 `seconds`·`transfers`·path가 `route.shortest(그래프, "서울역", "잠실", None)`와 같다(q2, 1298초). path는 지나는 역을 빠짐없이, 갈아타는 역은 두 번(내리는 호선·타는 호선) 쓴다
   - `shortest_route("수락산", "시청", 1)`이 2204초, 환승 1(q9)
   - `shortest_route("서울역", "강남", 0)` → `{"no_route": true}`(q7)
   - 없는 역 → `error`와 `candidates`(`find_station`과 같은 후보)
   - 별칭 `총신대입구`를 받으면 `이수`로 찾는다
   - 출력 키는 `path`·`seconds`·`transfers`·`no_route`·`error`·`candidates`뿐이다
   - `call_tool("shortest_route", '{"origin":"서울역","dest":"잠실","max_transfers":null}', SEARCH_TOOLS)`가 성공하고, `max_transfers`에 `true`·`"1"`을 넣으면 형식 오류다
2. 구현: `route.shortest(_graph(), _name(origin), _name(dest), max_transfers)`를 부른다. 그래프는 `tools._graph()`를 쓴다 — `build_graph(rows)`는 transfers가 `None`이면 데이터 환승 시간을 읽으므로 정답 그래프와 같다. 테스트로 확인한다
3. 도구 스키마: `max_transfers`는 `{"type": ["integer", "null"]}`. strict라 셋 다 required. 설명은 설계 문서 A안 도구 정의를 따른다
4. `SEARCH_TOOLS = [find_station 스키마, shortest_route 스키마]`
5. 커밋: `feature: 경로 탐색 도구 shortest_route`

### Task 2: `SYSTEM` 시한 문장과 `llm-tools-search`

1. 실패하는 테스트를 먼저 쓴다
   - `SYSTEM`이 설계 문서 「공통으로 바꾸는 것」의 문장으로 끝난다
   - `SEARCH_SYSTEM`이 `SYSTEM`으로 시작하고 「경로는 직접 고른다」가 없다
   - `--answerer llm-tools-search`가 받아지고, 가짜 client로 `shortest_route`를 부른 뒤 답을 내는 흐름이 끝까지 동작한다(기존 `llm-tools` 테스트와 같은 방식, API 안 부름)
   - `TOOLS_SYSTEM`·`COARSE_SYSTEM`의 차이가 도구 안내 한 문장뿐이라는 기존 테스트는 그대로 통과한다
2. 구현: `ANSWERERS`, `LLM_ANSWERERS`, `TOOL_SETS`에 더한다. `make_llm_tools(tools=SEARCH_TOOLS, system=SEARCH_SYSTEM)`
3. 녹화 fixture는 다시 녹화하지 않는다. `SYSTEM`이 바뀌어 녹화 재생 테스트가 깨지면 비교 대상(요청 본문 비교)을 고친다. 녹화된 응답은 그대로 둔다
4. 커밋: `feature: llm-tools-search 답하는 쪽과 시한 문장`

### Task 3: 비교 리포트 — 답하는 쪽 셋

1. 실패하는 테스트를 먼저 쓴다(`tests/test_cli.py` 또는 `tests/test_report.py`)
   - 답하는 쪽이 셋이고 회차가 2 이상이면, 평균 차이 줄이 짝마다(첫 번째 대 두 번째, 첫 번째 대 세 번째, 두 번째 대 세 번째 답하는 쪽) 나온다. 각 줄 머리에 두 이름을 쓴다
   - 답하는 쪽이 둘일 때의 출력은 지금과 같다(기존 테스트 그대로)
   - 머리 줄에 세 구성의 도구 이름이 나온다. `llm-tools-search`가 있으면 「경로 탐색 도구는 정답과 같은 다익스트라(`route.shortest`)를 부른다」가 있다
2. 커밋: `feature: 비교 리포트 평균 차이 줄을 답하는 쪽 셋에서도 쓴다`

### Task 4: 실제 키 측정

1. `mkdir -p runs/223 && timeout 5400 uv run subway-eval --answerer llm-tools llm-tools-coarse llm-tools-search --repeat 5 --raw runs/223/raw; echo exit=$?`
   - 오래 걸리므로 백그라운드로 돌리고 끝나면 TaskStop할 것이 없게 한다. `reports/compare.md`·`reports/<이름>.md`가 새로 써진다
2. 실패 징후 1 구간을 정한다. 다시 잰다 구간이면 `--repeat 10 --raw runs/223/raw10 --out runs/223/compare-10.md`로 한 번 더 돌린다(그 리포트 파일은 커밋하지 않고 표를 PR 본문에 옮긴다)
3. 실패 징후 2~4 값을 `runs/223/raw*`에서 센다. 집계 스크립트는 저장소 밖(`/tmp`)에 두고 PR 본문 `<details>`에 붙인다
4. `runs/`는 gitignore다. raw 파일은 커밋하지 않는다
5. 커밋: `docs: #223 측정 리포트`

### Task 5: 개념 표

1. `docs/concepts.md` `## 개념` 표: `shortest_route`·`SEARCH_TOOLS`·`SEARCH_SYSTEM`·`llm-tools-search` 행을 더하고, `SYSTEM`·`ANSWERERS`·평균 차이 줄·`compare.md`·`call_tool`(`FINE_TOOLS`·`COARSE_TOOLS` 행) 행을 고친다. 줄 번호는 실제 코드에서 다시 본다
2. 용어 절은 고치지 않는다(main이 GATE 1에서 썼다)
3. 커밋: `docs: #223 개념 표`

## Pre-PR checks

Pre-PR checks (all required — do not assume pass, show output):
1. New env vars: `git diff main...HEAD` added lines matching `os\.environ\.get|os\.getenv|process\.env\.` — log any found.
   - 이번에는 나오지 않아야 한다. 나오면 `.env.example`에 있는지 같이 본다
2. Server boots — detached-safe, NO interactive Ctrl+C (no TTY in orch). Background + timeout + curl the port + kill. Never bare `runserver` (hangs the loop till ORCH_STUCK_SECS). Django → `source <venv>/bin/activate && cd web && (timeout 20 python manage.py runserver 127.0.0.1:8000 --noreload &) ; sleep 8; curl -sf http://127.0.0.1:8000/ -o /dev/null && echo BOOT_OK ; pkill -f runserver`; CDK → `cdk synth` (no server); Zappa/Lambda Django → same background+timeout with `PYENV_VERSION=<env> --settings=<app>.settings.local`; CLI/library → smoke-run the entrypoint (it must self-terminate); else project-specific.
   - 이 레포는 CLI다: `env -u OPENAI_API_KEY timeout 60 uv run subway-eval; echo exit=$?`. 실제 키 실행은 Task 4가 이미 했으므로 그 exit 값을 옮긴다
3. Full test suite green (show pass/fail). If no runner: state `no tests — skipped`, do not silently pass.
   - `env -u OPENAI_API_KEY uv run pytest -q` 와 `uv run ruff check .`
   - **macOS에서 Django 4.1 미만이면 `--parallel`을 붙이지 않는다.** CI 명령에 있어도 뺀다. macOS Python은 워커를 `spawn`으로 띄우는데, 4.1 미만 Django는 그 워커에서 앱을 불러오지 않는다. 워커가 `AppRegistryNotReady`로 바로 죽고, 부모 프로세스는 끝나지 않는다. CI는 Linux(`fork`)라 통과한다.
   - **백그라운드로 돌린 테스트는 멈췄는지 확인하며 기다린다.** 출력 파일 크기가 10분 동안 그대로이고 테스트 프로세스가 전부 CPU 0%면 멈춘 것이다. 남은 프로세스를 `pkill -f "manage.py test"`(러너에 맞게)로 끄고 병렬 없이 다시 돌린다. 같은 명령으로 더 기다리지 않는다.  <!-- style-exempt -->

Then: completeness via `sc:reflect` vs plan; code review via `superpowers:requesting-code-review` (fix all Critical/Important); commit (`~/prv` repo면 `docs/plans/`도 포함); PR via `gh pr create --assignee @me --base main` (personal title + Summary/Changes/Notes, then update the Notion PR property). **PR을 만들면 이 루프는 끝난다** — 여기서 `pr-review-toolkit:review-pr`을 돌리지 말 것. 그 리뷰는 Phase C의 별도 세션이 맡는다.

내장 `/code-review`를 여기 쓰지 말 것 — 헤드리스 세션의 available-skills에 없다.

## Done criteria

- [ ] Task 1~5는 커밋 하나씩
- [ ] PR의 CI(`test` 워크플로)가 통과했다: `gh pr checks <PR 번호> --watch`의 출력을 PR 본문에 적는다. 실패하면 고쳐서 push하고 다시 본다
- [ ] Pre-PR checks 3개 출력이 PR 본문에 있다
- [ ] 실패 징후 1을 재서 `llm-tools-search` 회차별 맞힌 질문 수·평균, `llm-tools` 대비 `d`·`e`, 구간을 PR 본문 맨 위에 적었다. 다시 잰다 구간이었으면 10회차 결과도 적었다
- [ ] 회차별 지표 표와 평균 차이 줄을 PR 본문에 옮겼다
- [ ] 실패 징후 2~4 값을 PR 본문에 적었다
- [ ] PR 본문 맨 위에 `## 착수 전 기준 (jw)` 절 — plan의 `## jw 기준` 원문 + 그 기준으로 잰 결과
- [ ] `docs/concepts.md` `## 개념` 표를 고쳤다. plan·리포트·PR 본문은 `docs/concepts.md` 용어 절의 말을 쓰고, 쓰지 말 말을 쓰지 않는다
- [ ] 바꾸지 않을 것을 바꾸지 않았다: `git diff main...HEAD -- src/subway_route_agent/grade.py src/subway_route_agent/route.py src/subway_route_agent/graph.py src/subway_route_agent/data.py data/ tests/fixtures/` 출력이 비었다. `answerers.py`의 `SCHEMA`·`_parse`는 diff가 없다
- [ ] 테스트는 API와 네트워크를 부르지 않는다(`OPENAI_API_KEY`를 지운 환경에서 `uv run pytest -q`가 통과한다)
- [ ] 「손 계산」이라는 말을 쓰지 않는다. 「직접 계산」으로 쓴다
- [ ] base 브랜치(`main`)를 작업 브랜치에 merge·rebase하지 않았다
- [ ] PR 생성: `gh pr create --assignee @me --base main`. 계정은 `jongwoo315`(`gh api user -q .login`으로 확인, 아니면 `gh auth switch -u jongwoo315`)
- [ ] Notion PR 프로퍼티 갱신:
  ```bash
  printf '{"properties":{"PR":{"url":"%s"}}}' "<PR URL>" > /tmp/pr223.json
  "$HOME/.claude/tools/notion-api/notion-api" PATCH /v1/pages/41a41e61-65c0-8111-801e-eda45f117acd /tmp/pr223.json
  ```
