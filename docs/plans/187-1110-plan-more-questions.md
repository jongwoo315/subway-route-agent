# #187 질문 10개 Implementation Plan

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
**Notion:** #187 https://app.notion.com/p/41441e6165c081cc8885c7c61630a83f (page id `41441e61-65c0-81cc-8885-c7c61630a83f`)
**설계:** `/Users/jw/prv/.wt/187-more-questions/docs/plans/187-1110-design-more-questions.md` — 착수 전에 먼저 읽는다. 설계 결정 표가 거기 있다
**흐름:** 이미 있다(#185·#186). 바꾸는 stub: 질문 셋(`data/questions.json`) — 3개 고정을 10개로 늘린다

## jw 기준

n개 질문으로 늘렸을 때에도 파싱 실패건이 없고, llm이 답변을 내놓는다

## 통과 기준

- `data/questions.json`에 질문이 10개 있다(q1~q3는 그대로 두고 q4~q10을 더한다)
- 정답이 있는 질문은 전부 `hand_path`·`hand_seconds`가 있고, 테스트가 그래프를 쓰지 않고 CSV 행을 직접 더해 `hand_seconds`를 다시 계산한다. 그 값이 `shortest()`의 소요 시간과 같다
- `uv run subway-eval`(stub)과 `uv run subway-eval --answerer llm`이 10개 질문으로 끝까지 실행된다(exit 0)
- 리포트 머리에 `- 손 계산으로 확인한 정답: K/M`이 나온다
- 출발·도착역이 그래프에 없는 질문이 있으면 실행 전에 exit 2로 멈춘다
- 다익스트라 최단 경로로도 도착 시한을 못 맞추는 질문은 정답 없음이다
- **정답률은 이 티켓의 목표가 아니다.** LLM 혼자라 0/10도 나올 수 있다. 값을 적기만 한다

## 이번에 안 하는 것

- LLM 쪽 수정: `answerers.py`의 프롬프트(`SYSTEM`)·파싱·빈 경로 규칙을 바꾸지 않는다. 파싱 실패가 나와도 LLM 쪽을 고쳐 줄이지 않는다
- 도구 연결 (#188)
- 환승 시간·기다리는 시간 stub 수정 (#189) <!-- style-exempt -->
- 답 경로의 역 이름 맞춤(#186 리뷰 #10). 그래서 질문의 출발·도착역에 별칭 역(`총신대입구`)을 쓰지 않는다
- 「도착 시한만」 질문을 「늦어도 언제 출발하나」로 답하게 하는 것

## 실패 징후

1. **jw 기준을 잰다.** 잴 방법: 워크트리에서 실제 키로 `uv run subway-eval --answerer llm --raw runs/187/raw-1.json`을 돌린다. 리포트 머리의 `파싱 실패 N/10`과, 표에서 `답 있음`이 `O`인 행 수를 센다
   - 통과: 파싱 실패 0/10이고 `답 있음` `O`가 10개
   - 다시 잰다: 파싱 실패가 1~2개이거나 `답 있음` `X`가 1~2개다. `--raw` 원문으로 어느 질문에서 왜 났는지 적고(예: 정답 없음 질문에 빈 경로로 답함), LLM 쪽은 고치지 않고 같은 명령을 한 번 더 돌려(`raw-2.json`) 두 값을 나란히 적는다
   - 미완: 파싱 실패가 3개 이상이거나 `답 있음` `O`가 7개 이하다, 실행이 exit 0으로 끝나지 않는다, 또는 리포트가 실제 API 호출 없이 만들어졌다(fixture 재생·가짜 client 포함)
2. **손 계산이 다익스트라를 따라 쓴 것인지.** `hand_path`를 다익스트라 출력에서 옮겨 적으면 같은 구현끼리 맞춰 본 셈이다. 손 계산 값이 다익스트라와 처음부터 전부 같았는지, 다른 것이 있었으면 무엇이 왜 달랐는지 PR 본문에 적는다. 정답이 있는 질문 중 `hand_seconds`가 있는 질문이 q1 하나뿐이면 미완이다
3. 정답률·지어낸 역·조건 어김: 임계값 없음(10개 질문으로는 첫 측정). 값만 적는다. #186의 3개 질문 값과 섞어 비교하지 않는다

## 파일 구성

| 파일 | 할 일 |
| --- | --- |
| `data/questions.json` | q4~q10 추가, 정답이 있는 질문마다 `hand_path`·`hand_seconds`·`hand_note` |
| `src/subway_route_agent/cli.py` | 실행 전 역 검사(exit 2), 시한을 못 맞추면 정답 없음 |
| `src/subway_route_agent/report.py` | `- 손 계산으로 확인한 정답: K/M` 줄 |
| `tests/test_route.py` | CSV 행을 직접 더하는 손 계산 테스트 |
| `tests/test_cli.py` | 질문 수 하드코딩 수정, 역 검사·시한·리포트 줄 테스트 |
| `tests/test_grade.py` | 출발 시각만 / 도착 시한만 있으면 시한을 재지 않는다 |
| `reports/stub.md`, `reports/llm.md` | 다시 생성 |
| `docs/concepts.md` | `## 개념` 표. `## 용어` 절은 고치지 않는다(Kickoff에서 main이 썼다) |

### Task 1: 손 계산 테스트 장치와 q1~q3 손 계산

**Files:** Modify `data/questions.json`, `tests/test_route.py`

- `questions.json`의 질문 객체에 선택 필드 셋을 더한다
  - `hand_path`: 호선 구간 목록. `[{"line": 2, "stations": ["강남", "역삼", …, "홍대입구"]}, …]`. 갈아타는 역은 앞 구간의 끝과 다음 구간의 처음에 둘 다 쓴다
  - `hand_seconds`: 그 경로의 소요 시간(초). CSV `소요시간` 열을 구간마다 더하고 환승 한 번에 180초를 더한 값
  - `hand_note`: 계산 과정 한 줄(예: `2호선 강남→홍대입구 CSV 구간 합 1,740초, 환승 0`)
- 손 계산은 **다익스트라 출력을 보지 않고** CSV와 노선도 지식으로 경로를 고른 뒤 CSV 값을 더한다. 루프가 직접 CSV(`data/seoul_metro_1to8_240810.csv`)를 읽어 구간을 고른다
- `tests/test_route.py`에 테스트를 더한다
  - 헬퍼 `_csv_seconds(hand_path)`: **`build_graph`·`shortest`를 쓰지 않고** `load_rows()`가 준 CSV 행만으로, 구간마다 이웃한 두 역 사이 소요시간을 더하고 환승마다 `TRANSFER_SECONDS`를 더한다. 순환선(2호선 시청 두 번, 6호선 응암순환 한 방향)과 지선은 CSV 행 순서 그대로 따라간다. 이웃한 역이 CSV에 없으면 실패한다
  - 정답이 있고 `hand_seconds`가 있는 질문마다(파라미터화): `_csv_seconds(q["hand_path"]) == q["hand_seconds"] == shortest(...).seconds`
  - 기존 `test_q1_matches_hand_count`는 이 테스트로 합쳐 지운다. `test_q3_uses_macheon_branch`·`test_q2_needs_transfer`는 그대로 둔다
- q1·q2·q3에 손 계산 필드를 채운다. 손 계산 값이 다익스트라와 다르면 `hand_seconds`를 다익스트라에 맞춰 고치지 말고, 어느 쪽이 틀렸는지 찾는다. 손으로 고른 경로가 더 느렸으면 더 빠른 경로로 다시 손 계산하고, 그 사실을 `hand_note`에 적는다. 다익스트라나 그래프가 틀렸으면 PR 본문에 적고 멈추지 말고 계속하되 그 질문은 `hand_seconds` 없이 둔다
- 커밋: `test: CSV 행을 직접 더하는 손 계산으로 q1~q3 정답 소요 시간을 고정한다`

### Task 2: 역 검사와 시한을 못 맞추는 질문

**Files:** Modify `cli.py`, `tests/test_cli.py`, `tests/test_grade.py`

- cli: 질문을 돌기 전에 질문마다 `origin`·`dest`를 그래프 역 이름(별칭을 바꾼 뒤, `graph.ALIASES`)과 맞춘다. 없는 역이 하나라도 있으면 `질문 q5: 그래프에 없는 역 — 무슨역`처럼 stderr에 쓰고 exit 2. 리포트를 쓰지 않는다
- cli: `shortest()` 결과가 있고 질문에 `depart`와 `arrive_by`가 둘 다 있으며 `출발 시각 + 소요 시간 > 도착 시한`이면 그 질문의 정답을 `None`(정답 없음)으로 둔다. 판단 함수는 `grade.py`의 `_minutes`를 재사용한다
- 테스트 먼저
  - 없는 역이 든 질문 파일(monkeypatch로 `QUESTIONS`를 tmp 파일로)이면 `main`이 exit 2이고 리포트 파일이 안 생긴다
  - 시한을 못 맞추는 질문이면 리포트의 정답 경로·정답 시간이 `없음`이다
  - `grade()`: `depart`만 있거나 `arrive_by`만 있으면 `시한 초과`가 나오지 않는다(지금 동작을 고정)
- 커밋: `feature: 그래프에 없는 역이 든 질문은 실행 전에 멈추고, 시한을 못 맞추는 질문은 정답 없음으로 둔다`

### Task 3: 질문 7개 추가와 리포트 줄

**Files:** Modify `data/questions.json`, `report.py`, `tests/test_cli.py`, `tests/test_route.py`

- q4~q10을 더한다. 질문 문장(`text`)은 사람이 묻듯 자연스럽게 쓰고, 문장 안의 조건이 필드(`max_transfers`·`depart`·`arrive_by`)와 일치해야 한다
  | id | 종류 | 조건 |
  | --- | --- | --- |
  | q4 | 출발 시각만 | `depart`만 있다 |
  | q5 | 도착 시한만 | `arrive_by`만 있다 |
  | q6 | 정답 없음 — 시한 | `depart`·`arrive_by`가 둘 다 있고 최단 경로로도 못 맞춘다 |
  | q7 | 정답 없음 — 환승 상한 | `max_transfers: 0`인데 한 호선으로 갈 수 없는 두 역 | <!-- style-exempt -->
  | q8 | 환승 2회 이상 | 조건 없음 |
  | q9 | 다른 호선끼리, 환승 1회 상한 | `max_transfers: 1` | <!-- style-exempt -->
  | q10 | 지선 역 | `origin` 또는 `dest`가 2호선 지선(성수지선·신정지선) 역. 조건 없음 |
- 정답이 있는 질문(q4·q5·q8·q9·q10)은 Task 1 방식으로 손 계산 필드를 채운다. 정답 없음 질문(q6·q7)은 `hand_note`에 왜 정답이 없는지 손으로 확인한 근거를 적는다(q6: 최단 소요 시간과 시한 사이 분, q7: 두 역이 같은 호선에 없다)
- `tests/test_route.py`: q6·q7은 정답 없음이 맞는지(q7은 `shortest(...) is None`, q6은 cli 기준으로 정답 없음) 테스트한다
- report: 정답률·파싱 실패 줄 아래에 `- 손 계산으로 확인한 정답: K/M`. `M` = 정답이 있는 질문 수, `K` = 그중 질문에 `hand_seconds`가 있는 수. `render`가 이 두 값을 받도록 인자를 더한다(`Result`에 질문의 `hand_seconds` 유무를 넣어도 된다)
- `tests/test_cli.py`의 `0/3`·`q1~q3` 하드코딩을 질문 파일에서 읽은 개수로 바꾼다. 정답 없음 질문은 정답 경로가 `없음`인 것이 맞다
- `uv run subway-eval`로 `reports/stub.md`를 다시 쓴다
- 커밋: `feature: 질문을 10개로 늘리고 리포트에 손 계산으로 확인한 정답 수를 적는다`

### Task 4: 실제 호출 측정과 개념 표

1. 실제 키로 돌린다
   ```bash
   uv run subway-eval --answerer llm --raw runs/187/raw-1.json; echo "exit=$?"
   ```
   실패 징후 1의 구간을 정한다. 「다시 잰다」면 원문을 보고 원인을 적은 뒤 `--raw runs/187/raw-2.json`으로 한 번 더 돌린다. LLM 쪽은 고치지 않는다. 마지막 실행이 쓴 `reports/llm.md`를 커밋한다
2. `docs/concepts.md` `## 개념` 표
   - 추가: `hand_path`, `hand_seconds`, `hand_note`(질문 필드), 역 검사(exit 2), 시한을 못 맞추면 정답 없음, `손 계산으로 확인한 정답` 리포트 줄
   - 수정: `depart`·`arrive_by` 행에 「둘 중 하나만 있으면 시한을 재지 않는다」
   - 정의한 곳 줄 번호는 실제 파일에서 다시 확인한다
   - `## 용어` 절은 고치지 않는다
3. 커밋: `docs: #187 LLM 혼자 리포트(질문 10개)` / `docs: #187 개념 표`

## Pre-PR checks

Pre-PR checks (all required — do not assume pass, show output):
1. New env vars: `git diff main...HEAD` added lines matching `os\.environ\.get|os\.getenv|process\.env\.` — log any found.
   - 이번에는 나오지 않아야 한다. 나오면 `.env.example`에 있는지 같이 본다
2. Server boots — detached-safe, NO interactive Ctrl+C (no TTY in orch). Background + timeout + curl the port + kill. Never bare `runserver` (hangs the loop till ORCH_STUCK_SECS). Django → `source <venv>/bin/activate && cd web && (timeout 20 python manage.py runserver 127.0.0.1:8000 --noreload &) ; sleep 8; curl -sf http://127.0.0.1:8000/ -o /dev/null && echo BOOT_OK ; pkill -f runserver`; CDK → `cdk synth` (no server); Zappa/Lambda Django → same background+timeout with `PYENV_VERSION=<env> --settings=<app>.settings.local`; CLI/library → smoke-run the entrypoint (it must self-terminate); else project-specific.
   - 이 레포는 CLI다: `timeout 60 uv run subway-eval; echo exit=$?` 와 `timeout 300 uv run subway-eval --answerer llm --out /tmp/llm-smoke.md; echo exit=$?`
3. Full test suite green (show pass/fail). If no runner: state `no tests — skipped`, do not silently pass.
   - `env -u OPENAI_API_KEY uv run pytest -q` 와 `uv run ruff check .`

Then: completeness via `sc:reflect` vs plan; code review via `superpowers:requesting-code-review` (fix all Critical/Important); commit (`~/prv` repo면 `docs/plans/`도 포함); PR via `gh pr create --assignee @me --base main` (personal title + Summary/Changes/Notes, then update the Notion PR property). **PR을 만들면 이 루프는 끝난다** — 여기서 `pr-review-toolkit:review-pr`을 돌리지 말 것. 그 리뷰는 Phase C의 별도 세션이 맡는다.

내장 `/code-review`를 여기 쓰지 말 것 — 헤드리스 세션의 available-skills에 없다.

## Done criteria

- [ ] Task 1~4 완료, Task 1~3은 커밋 하나씩, Task 4는 커밋 둘
- [ ] Pre-PR checks 3개 출력이 PR 본문에 있다
- [ ] 실패 징후 1을 실제 호출로 재서 값(파싱 실패 수 · `답 있음` `O` 수 · exit code)과 구간을 PR 본문에 적었다. 「다시 잰다」였으면 두 실행 값과 원인을 나란히 적었다. 리포트 파일에는 손으로 쓰지 않는다
- [ ] 실패 징후 2: 질문마다 손 계산 값과 다익스트라 값을 나란히 적은 표를 PR 본문에 넣었다. 처음에 달랐던 질문이 있으면 무엇이 왜 달랐는지 적었다
- [ ] 실패 징후 3 값(정답률·지어낸 역·조건 어김·토큰 합)을 PR 본문에 적었다
- [ ] PR 본문 맨 위에 `## 착수 전 기준 (jw)` 절 — plan의 `## jw 기준` 원문 + 그 기준으로 잰 결과
- [ ] `docs/concepts.md` `## 개념` 표를 고쳤다. plan·리포트·PR 본문은 `docs/concepts.md` 용어 절의 말을 쓰고, 쓰지 말 말을 쓰지 않는다
- [ ] `src/subway_route_agent/answerers.py`를 고치지 않았다(`git diff main...HEAD -- src/subway_route_agent/answerers.py`가 비어 있다)
- [ ] `hand_seconds`를 다익스트라 출력에 맞춰 고치지 않았다
- [ ] 테스트는 API를 부르지 않는다(`OPENAI_API_KEY`를 지운 환경에서 `uv run pytest -q`가 통과한다). 녹화 fixture(`tests/fixtures/llm_responses.json`)는 q1~q3용이라 그대로 둔다. 재생 테스트가 질문 10개 때문에 깨지면, 재생 테스트가 녹화된 질문만 쓰도록 고친다
- [ ] base 브랜치(`main`)를 작업 브랜치에 merge·rebase하지 않았다
- [ ] PR 생성: `gh pr create --assignee @me --base main`. 계정은 `jongwoo315`(`gh api user -q .login`으로 확인)
- [ ] Notion PR 프로퍼티 갱신:
  ```bash
  printf '{"properties":{"PR":{"url":"%s"}}}' "<PR URL>" > /tmp/pr187.json
  "$HOME/.claude/tools/notion-api/notion-api" PATCH /v1/pages/41441e61-65c0-81cc-8885-c7c61630a83f /tmp/pr187.json
  ```
