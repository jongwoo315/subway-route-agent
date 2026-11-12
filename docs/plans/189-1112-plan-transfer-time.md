# #189 환승 시간 Implementation Plan

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
**Notion:** #189 https://app.notion.com/p/41441e6165c081d3909cc00b0a8198aa (page id `41441e61-65c0-81d3-909c-c00b0a8198aa`)
**설계:** `/Users/jw/prv/.wt/189-transfer-time/docs/plans/189-1112-design-transfer-time.md` — 착수 전에 먼저 읽는다. 데이터를 받은 방법, 그래프와 맞춰 본 결과, 정답 참고 값, 설계 결정 표가 거기 있다
**흐름:** 이미 있다(#185~#193). 바꾸는 stub: 환승 시간 180초 고정(`graph.py` `TRANSFER_SECONDS`)

## jw 기준

환승 소요 시간을 180초 stub이 아닌 실제 값으로 계산한다

## 통과 기준

- 그래프의 갈아타는 간선이 환승역 데이터(`data/seoul_metro_transfer_260831.csv`)의 `환승소요시간`을 쓴다. 그 방향 값이 없으면 반대 방향 값, 둘 다 없을 때만 180초다
- 명령 하나(`uv run subway-eval`)로 끝까지 돌고, 리포트 머리에 「데이터 환승 시간을 쓴 환승역 수」와 「180초가 남은 환승역 수」가 나온다
- 정답이 있는 질문 8개 모두 `hand_seconds`(직접 계산한 값)가 다익스트라 정답과 같다. 직접 계산은 그래프 코드를 쓰지 않고 두 CSV만 읽는다
- 정답이 바뀐 질문(경로·시간)을 PR 본문 표에 적는다
- LLM 점수를 두 가지로 다시 잰다: #188 main 실행 원문을 새 정답으로 다시 채점(API 없음), 실제 키로 두 번 실행
- 테스트는 API와 네트워크를 부르지 않는다

## 이번에 안 하는 것

- 기다리는 시간(0초 그대로) <!-- style-exempt -->
- 1~8호선 밖 노선, 1호선 코레일 구간(창동·신길·도봉산·가산디지털단지·온수·신도림 1호선)
- 환승 데이터를 실행마다 다시 받기
- 채점 규칙(`grade.py`), 질문 셋(질문 추가·삭제·문장 수정), 도구 셋(`tools.py`)
- `SYSTEM`(LLM 혼자 지시문)·`SCHEMA`·`_parse` 수정
- 녹화 fixture(`tests/fixtures/llm_tools_responses.json`, `tests/fixtures/gate188/`) 다시 녹화

## 실패 징후

1. **jw 기준을 잰다.** 「환승 소요 시간을 180초 stub이 아닌 실제 값으로 계산한다」
   - 측정값 ①: 실제 그래프(`build_graph(load_rows())`)의 갈아타는 방향(역, 앞 호선 → 뒤 호선) 수와, 그중 간선 가중치가 (가) 그 방향의 데이터 값인 수, (나) 반대 방향의 데이터 값인 수, (다) 180초가 남은 수. 데이터에 값이 있는데 180초를 쓴 방향은 (라)로 따로 센다
   - 측정값 ②: 정답이 있는 질문 8개 중 직접 계산한 값(두 CSV만 읽어 더한 값)과 다익스트라 정답 소요 시간이 같은 질문 수
   - 설계 문서의 main 참고 값: 방향 78개, (가) 77, (나) 1(까치산 2→5), (다) 0
   - 통과: (라) 0개이고 ② 8/8. (다)가 1개 이상이면 그 방향마다 「데이터에 양쪽 다 없다」를 확인한 목록이 리포트·PR 본문에 있다
   - 다시 잰다: (라) 1개 이상이거나 ②가 8/8이 아니다. 역 이름·호선 매칭(별칭, 공백, `호선` 글자 처리)과 직접 계산을 고쳐 다시 센다. 최대 두 번
   - 미완: 두 번 고친 뒤에도 (라) 1개 이상이거나 ②가 8/8이 아니다. 또는 (가)+(나)가 0이다(역 이름 매칭이 통째로 안 된 것)
2. **데이터 값이 그래프 밖에서 남는다.** 데이터에서 호선·환승노선이 둘 다 1~8호선인 행 중 그래프에 안 쓰인 행 수와 목록을 센다. main 참고 값: 86행 중 9행(지선 같은 호선 3, 1호선 코레일 구간 6). 이 9행 말고 다른 행이 남으면 그 행이 왜 안 맞는지 PR 본문에 적는다
3. **정답 변화.** 질문마다 지금 정답과 새 정답(경로 요약·소요 시간·환승 수)을 표로 적는다. main 참고 값(설계 문서 표): 바뀐 질문 5개(q2·q4·q9 시간, q5·q8 경로와 시간). 참고 값과 다르면 직접 계산 결과를 따르고 차이를 PR 본문에 적는다
4. **LLM 점수.** 임계값 없음 — 새 정답 아래 첫 측정이고 다음 티켓의 기준값이 된다
   - ① #188 main 실행 원문 다시 채점: 비교 대상은 #193의 다시 채점 결과(LLM + 도구 5/10: q1·q2·q3·q9·q10, LLM 혼자 0/10). 질문별 맞음을 표로 적는다
   - ② 실제 키 두 번: 비교 대상은 #193 실제 실행(LLM + 도구 3/10·5/10, LLM 혼자 0/10). 실행마다 두 정답률, 채우지 않고도 맞은 질문 수를 적는다

## 바꾸는 파일

- Create: `data/seoul_metro_transfer_260831.csv` — 워크트리에 이미 있다(main이 받아 UTF-8로 바꿔 둔 것, 커밋 전). 내용을 고치지 않는다
- Modify: `src/subway_route_agent/data.py`, `graph.py`, `report.py`, `answerers.py`
- Modify: `data/questions.json` — q2·q4·q5·q8·q9의 `hand_path`·`hand_seconds`·`hand_note`만
- Modify: `tests/test_graph.py`, `tests/test_route.py`, `tests/test_data.py`, `tests/test_cli.py`, `tests/test_llm_tools.py`, 그 밖에 정답 값에 묶여 깨지는 테스트
- Modify: `docs/concepts.md` `## 개념` 표

## Tasks

### Task 1: 환승 데이터를 읽어 그래프 간선에 쓴다

**Files:** `data/seoul_metro_transfer_260831.csv`(커밋만), `data.py`, `graph.py`, `tests/test_data.py`, `tests/test_graph.py`

- `data.py`: `TRANSFER_DATA = ROOT / "data" / "seoul_metro_transfer_260831.csv"`, `load_transfers(path=TRANSFER_DATA) -> dict[tuple[str, int, int], int]`. 키는 (역 이름, 앞 호선, 뒤 호선), 값은 `환승소요시간`(`MM:SS`, 기존 `parse_mmss`)을 초로 바꾼 것. `환승노선`이 `N호선`(N은 1~8)인 행만 넣는다. 역 이름은 `strip()`만 하고 별칭은 여기서 바꾸지 않는다
- `graph.py`: `build_graph(rows, transfers=None)`. `None`이면 `load_transfers()`. 갈아타는 간선 (역 a 호선 → 역 a 뒤 호선) 가중치는 별칭을 거친 이름으로 찾아 그 방향 값 → 반대 방향 값 → `TRANSFER_SECONDS` 순서다. 별칭: 데이터의 `총신대입구`·`이수` 둘 다 그래프의 `이수`로 맞춘다(데이터에 어느 이름이 있는지 보고 처리한다)
- `TRANSFER_SECONDS = 180`은 남기고 주석을 「데이터에 양방향 다 없는 환승에만 쓴다」로 바꾼다. `ponytail:` 주석의 「실제 값은 …로 바꾼다」는 지운다
- 세는 함수 하나(이름은 루프가 정한다): 그래프와 환승 dict를 받아 실패 징후 1 ①의 (가)·(나)·(다)·(라) 방향 수, 환승역 수(역의 모든 방향이 (가)·(나)이면 「데이터 환승 시간을 쓴 환승역」, 하나라도 (다)면 「180초가 남은 환승역」), (다) 목록, 그래프에 안 쓰인 1~8호선 데이터 행(실패 징후 2)을 돌려준다
- 테스트(실제 데이터):
  - 이수 4→7호선 간선 = 데이터 값(테스트가 CSV에서 그 행을 직접 읽어 기대값으로 쓴다)
  - 까치산 2→5호선 간선 = 반대 방향(5→2호선) 데이터 값
  - 세는 함수: 방향 78, (가) 77, (나) 1, (다) 0, (라) 0, 환승역 35/0. 안 쓰인 행 9. **숫자는 실제로 돌려 확인한 뒤 박는다.** main 참고 값과 다르면 다른 이유를 커밋 메시지에 적는다
  - `load_transfers`: 1~8호선 밖 `환승노선`(공항철도 등) 행이 없다, 값이 `MM:SS`를 초로 바꾼 것이다
- 테스트(가짜 역): 데이터에 없는 역으로 만든 그래프는 갈아타는 간선이 180초다. `transfers={}`를 주면 실제 역이어도 180초다
- 기존 테스트 `test_graph.py:20,34`의 `== TRANSFER_SECONDS`는 데이터 값으로 바꾼다
- 커밋: `feature: 환승역 데이터로 갈아타는 시간을 정한다`

### Task 2: 직접 계산한 값과 질문 셋

**Files:** `tests/test_route.py`, `data/questions.json`, 정답에 묶인 테스트

- `tests/test_route.py`의 `_csv_seconds`: 갈아탄 곳마다 `TRANSFER_SECONDS` 대신 환승 CSV 값을 더한다. 환승 CSV는 테스트 안에서 `csv` 모듈로 직접 읽는다 — `build_graph`·`load_transfers`·`graph.ALIASES`를 쓰지 않는다(#187 「직접 계산은 그래프 코드와 따로」). 방향 규칙(그 방향 → 반대 방향)은 테스트 안에 다시 쓴다. 값이 양쪽 다 없으면 실패한다
- `data/questions.json`: q2·q4·q5·q8·q9의 `hand_path`·`hand_seconds`·`hand_note`를 새 정답으로 고친다. `hand_note`에는 구간 합과 갈아탄 역·호선·환승 시간을 적는다(예: 「4호선 서울역→동대문역사문화공원 330초 + 환승(동대문역사문화공원 4→2호선) N초 + …」). 다른 경로를 고르지 않은 이유가 지금 note에 있으면 새 값으로 다시 쓴다
  - q5·q8은 경로가 바뀐다(설계 문서 표). 새 `hand_path`는 다익스트라 결과를 옮기지 말고 CSV 구간을 직접 더해 확인한 경로로 쓴다
  - 질문 문장(`text`)·조건·`id`는 고치지 않는다. 나머지 질문 5개는 손대지 않는다
- `test_hand_seconds_matches_csv_sum_and_dijkstra`가 8개 모두 통과해야 한다
- `tests/test_route.py`의 `test_transfer_limit_forces_slower_route`처럼 가짜 역 그래프는 180초 그대로 통과해야 한다. 깨지면 `transfers={}`를 넘겨 의도를 드러낸다
- `tests/test_grade.py`·`tests/test_cli.py`·`tests/test_regrade_188.py` 등에서 실제 그래프 정답 값에 묶인 기대값이 깨지면, 직접 계산으로 새 기대값을 구해 고친다. 판정을 느슨하게 바꾸지 않는다. 가짜 역 그래프로 180초를 전제한 테스트는 `transfers={}`로 고친다. 기대값을 바꾼 테스트마다 이유를 커밋 메시지에 한 줄씩 적는다
- 커밋: `fix: 직접 계산한 값을 환승역 데이터 기준으로 다시 구한다`

### Task 3: 리포트 머리와 LLM + 도구 지시문

**Files:** `report.py`, `answerers.py`, `tests/test_cli.py`, `tests/test_llm_tools.py`

- 리포트(`render`)·비교 리포트(`render_compare`) 머리의 「환승 한 번에 180초로 고정한 stub이다. 기다리는 시간은 0으로 본다」를 두 줄로 바꾼다 <!-- style-exempt -->
  - `- 환승 시간: 서울교통공사 환승역 거리·소요시간 (data.go.kr 15044419, 2026-08-31 기준, 최단 환승거리 ÷ 초당 1.2m)`
  - `- 데이터 환승 시간을 쓴 환승역 N개 · 180초가 남은 환승역 M개 (갈아타는 방향 T개 중 반대 방향 값 K개). 기다리는 시간은 0으로 본다` <!-- style-exempt -->
  - N·M·T·K는 Task 1 세는 함수로 그 실행의 그래프에서 구한다(숫자를 박지 않는다). M이 1 이상이면 그 역 이름을 같은 줄 괄호에 적는다
- `TOOLS_SYSTEM`(Kickoff 결정 A): 「 환승 한 번은 {TRANSFER_SECONDS}초다.」를 「 환승 시간은 역과 호선마다 다르다.」로 바꾼다. 숫자·역별 값은 넣지 않는다. 다른 문장은 그대로. `answerers.py`의 `TRANSFER_SECONDS` import가 안 쓰이면 지운다
- `COMPARE_DIFF`를 「LLM + 도구 지시문에만 도구 사용 안내와 「환승 시간은 역과 호선마다 다르다」 문장이 있다」로 바꾼다
- 테스트: 머리 두 줄(실제 그래프에서 N=35·M=0을 기대 — Task 1에서 확인한 값), `TOOLS_SYSTEM`에 `180` 글자가 없고 새 문장이 있다, `COMPARE_DIFF`
- 녹화 재생 테스트(`tests/test_llm_tools.py` FIXTURE)는 fixture를 다시 녹화하지 않는다. 지시문 문자열 비교 때문에 깨지면 비교 대상을 고친다
- 커밋: `feature: 리포트에 환승 데이터 출처와 환승역 수를 적는다`

### Task 4: 측정과 개념 표

1. 실패 징후 1·2: Task 1 세는 함수 결과를 그대로 적는다
2. 실패 징후 3: `main`의 그래프(180초)와 새 그래프로 `cli.truth_for`를 질문마다 구해 표를 만든다. `main` 그래프는 `build_graph(load_rows(), transfers={})`로 다시 만들 수 있다
3. 실패 징후 4 ①: `tests/test_regrade_188.py`의 `_answers` 방식대로 `tests/fixtures/gate188/raw-llm-tools.json`·`raw-llm.json`을 `_parse`로 읽고(실패·빈 경로는 답 없음) 새 정답으로 `grade`를 돌린다. 같은 원문을 `transfers={}` 그래프로 채점한 결과와 나란히 질문별 맞음 표를 만든다. `transfers={}` 쪽은 #193 결과(LLM + 도구 q1·q2·q3·q9·q10 맞음, LLM 혼자 0/10)와 같아야 한다 — 다르면 그 사실을 PR 본문 맨 위에 적는다
4. 실패 징후 4 ②: 실제 키로 두 번 돌린다
   ```bash
   mkdir -p runs/189
   uv run subway-eval --answerer stub llm llm-tools --raw runs/189/raw-1.json --out runs/189/compare-1.md; echo "exit=$?"
   uv run subway-eval --answerer stub llm llm-tools --raw runs/189/raw-2.json; echo "exit=$?"
   ```
   두 번째 실행이 `reports/`의 리포트 넷을 쓴다(커밋한다). `runs/`는 `.gitignore`에 있다. 세는 데 쓴 스크립트는 커밋하지 않아도 되지만 명령과 결과를 PR 본문에 적는다
5. `docs/concepts.md` `## 개념` 표: `load_transfers`, `TRANSFER_SECONDS`(뜻이 「데이터에 없는 환승에만 쓰는 180초」로 바뀜), 세는 함수, `build_graph`의 `transfers` 인자, 리포트 머리 환승 줄, `TOOLS_SYSTEM`(180초 문장이 바뀜), `hand_seconds`(「환승 한 번에 180초」 → 환승 CSV 값)를 더하거나 고친다. 정의한 곳 줄 번호는 실제 파일에서 확인한다. `## 용어` 절은 고치지 않는다(Kickoff에서 main이 썼다)
6. 커밋: `docs: #189 리포트` / `docs: #189 개념 표`

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

- [ ] Task 1~3은 커밋 하나씩, Task 4는 커밋 둘
- [ ] PR의 CI(`test` 워크플로)가 통과했다: `gh pr checks <PR 번호> --watch`의 출력을 PR 본문에 적는다. 실패하면 고쳐서 push하고 다시 본다
- [ ] Pre-PR checks 3개 출력이 PR 본문에 있다
- [ ] 실패 징후 1을 재서 측정값 ①·②와 구간을 PR 본문에 적었다
- [ ] 실패 징후 2~4 값과 표를 PR 본문에 적었다
- [ ] PR 본문 맨 위에 `## 착수 전 기준 (jw)` 절 — plan의 `## jw 기준` 원문 + 그 기준으로 잰 결과
- [ ] `docs/concepts.md` `## 개념` 표를 고쳤다. plan·리포트·PR 본문은 `docs/concepts.md` 용어 절의 말을 쓰고, 쓰지 말 말을 쓰지 않는다
- [ ] 바꾸지 않을 것을 바꾸지 않았다: `git diff main...HEAD -- src/subway_route_agent/grade.py src/subway_route_agent/tools.py tests/fixtures/` 출력이 비었다. `answerers.py` diff는 `TOOLS_SYSTEM`의 환승 문장과 `TRANSFER_SECONDS` import뿐이다. `data/questions.json` diff는 q2·q4·q5·q8·q9의 `hand_path`·`hand_seconds`·`hand_note`뿐이다
- [ ] `data/seoul_metro_transfer_260831.csv`가 커밋됐고 sha256이 main이 넣은 파일과 같다: `shasum -a 256 data/seoul_metro_transfer_260831.csv`를 PR 본문에 적는다(UTF-8 사본의 값. 원본 CP949 sha256은 설계 문서에 있다)
- [ ] 테스트는 API와 네트워크를 부르지 않는다(`OPENAI_API_KEY`를 지운 환경에서 `uv run pytest -q`가 통과한다)
- [ ] 「손 계산」이라는 말을 쓰지 않는다. 「직접 계산」으로 쓴다
- [ ] base 브랜치(`main`)를 작업 브랜치에 merge·rebase하지 않았다
- [ ] PR 생성: `gh pr create --assignee @me --base main`. 계정은 `jongwoo315`(`gh api user -q .login`으로 확인, 아니면 `gh auth switch -u jongwoo315`)
- [ ] Notion PR 프로퍼티 갱신:
  ```bash
  printf '{"properties":{"PR":{"url":"%s"}}}' "<PR URL>" > /tmp/pr189.json
  "$HOME/.claude/tools/notion-api/notion-api" PATCH /v1/pages/41441e61-65c0-81d3-909c-c00b0a8198aa /tmp/pr189.json
  ```
