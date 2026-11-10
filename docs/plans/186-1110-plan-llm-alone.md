# #186 LLM 혼자 Implementation Plan

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
**Notion:** #186 https://app.notion.com/p/41441e6165c081ebaf7cc1d12c379d21 (page id `41441e61-65c0-81eb-af7c-c1d12c379d21`)
**설계:** `/Users/jw/prv/.wt/186-llm-alone/docs/plans/186-1110-design-llm-alone.md` — 착수 전에 먼저 읽는다. 설계 결정 표가 거기 있다
**흐름:** 이미 있다(#185). 바꾸는 stub: `ANSWERERS`의 답하는 쪽 — `llm`(LLM 혼자)을 추가한다

## jw 기준

경로질문에 대한 답변을 llm이 하도록 변경된다 <!-- style-exempt -->

## 통과 기준

- `uv run subway-eval --answerer llm` 하나로 질문 3개가 실제 OpenAI 호출을 거쳐 답해지고, 다익스트라 정답과 채점되어 `reports/llm.md`가 나온다
- 리포트 머리에 답하는 쪽 `llm`과 모델 이름, `파싱 실패 N/3`이 나온다. 표에 `토큰` 열이 있다
- `uv run subway-eval`(기본 `stub`)은 키 없이도 지금처럼 끝까지 실행되고 `reports/stub.md`를 쓴다
- 테스트는 API를 부르지 않는다. 녹화해 둔 실제 응답(`tests/fixtures/llm_responses.json`)으로 파싱·채점까지 검증한다
- **정답률은 이 티켓의 목표가 아니다.** LLM 혼자라 0/3도 나올 수 있다. 값을 적기만 한다. 점수를 올리려고 프롬프트에 역 목록·정답·질문별 힌트를 넣지 않는다

## 이번에 안 하는 것

- 도구 연결 (#188)
- 질문 늘리기, q2·q3 정답 손 계산 (#187)
- 모델 여러 개 비교, 프롬프트 여러 개 비교
- 환승 시간 stub(180초)·기다리는 시간 stub(0) 수정 <!-- style-exempt -->
- 기본 답하는 쪽을 `llm`으로 바꾸는 것 — 기본은 `stub` 그대로

## 실패 징후

1. **jw 기준을 잰다.** 잴 방법: 워크트리에서 `uv run subway-eval --answerer llm --raw runs/186/raw-1.json`을 실제 키로 돌린다. 리포트 머리의 답하는 쪽이 `llm`인지, 질문 3개 중 `답 있음`이 `O`인 행(LLM 답을 읽어 경로가 비지 않은 행)이 몇 개인지 센다
   - 통과: 답하는 쪽이 `llm`이고 3개 모두 `답 있음` `O`, `파싱 실패 0/3`
   - 다시 잰다: `답 있음` `O`가 1~2개다. `--raw` 원문을 보고 프롬프트의 답 형식 설명이나 파싱을 한 번 고친 뒤 다시 잰다. 그래도 1~2개면 그 값과 원문 요약을 그대로 적는다
   - 미완: `답 있음` `O`가 0개다, 실행이 exit 0으로 끝나지 않는다, 또는 리포트가 실제 API 호출 없이 만들어졌다(fixture 재생·가짜 client 포함)
2. 정답률·지어낸 역·지어낸 소요 시간·조건 어김은 임계값이 없다. 이번이 첫 측정이라 baseline이 없다 — 값만 적고, #188(LLM + 도구)의 기준값이 된다
3. 같은 명령을 두 번 돌려(`raw-1.json`, `raw-2.json`) 정답률과 `답 있음` 수를 나란히 적는다. 두 번의 `답 있음` 수가 다르면 그 사실을 적는다(판정하지 않는다)
4. 프롬프트에 역 이름 목록이나 질문별 정답이 들어가 있으면 「LLM 혼자」가 아니다. 리뷰 때 `answerers.py`의 시스템 지시를 그대로 PR 본문에 붙인다

## 파일 구성

| 파일 | 할 일 |
| --- | --- |
| `pyproject.toml`, `uv.lock` | `uv add openai` |
| `.env.example` | 새로 만든다: `OPENAI_API_KEY=`, `OPENAI_MODEL=` |
| `.gitignore` | `runs/` 추가 |
| `src/subway_route_agent/answerers.py` | `Answer`에 `parse_error`·`tokens`·`raw` 추가, `llm` 답하는 쪽 |
| `src/subway_route_agent/report.py` | 머리 문구, `파싱 실패 N/M` 줄, `토큰` 열 |
| `src/subway_route_agent/cli.py` | 답하는 쪽마다 기본 출력 경로, `--raw`, 키 없을 때 exit 2 |
| `reports/skeleton.md` → `reports/stub.md` | `git mv` 후 다시 생성(손으로 적은 절이 빠진다) |
| `tests/test_answerers.py`, `tests/test_cli.py`, `tests/test_llm.py`, `tests/fixtures/llm_responses.json` | 테스트 |
| `docs/concepts.md` | `## 개념` 표 행 추가·수정. `## 용어` 절은 고치지 않는다(Kickoff에서 main이 썼다) |

### Task 1: Answer 필드와 리포트

**Files:** Modify `answerers.py`, `report.py`, `cli.py`, `tests/test_answerers.py`, `tests/test_cli.py`; `git mv reports/skeleton.md reports/stub.md`

- `Answer`에 필드 셋을 추가한다(기본값이 있어 stub은 그대로): `parse_error: str | None = None`, `tokens: int = 0`, `raw: str | None = None`
- 리포트
  - 첫 줄 `# skeleton 리포트` → `# 리포트`
  - 머리에 `- 파싱 실패 N/M`을 정답률 줄 아래에 둔다(`parse_error`가 있는 행 수)
  - `render(answerer, data_name, results, model=None)` — `model`이 있으면 `- 답하는 쪽: llm (모델 gpt-5.4-mini)`처럼 쓴다
  - `COLUMNS` 끝에 `토큰` 추가(11열). 값은 `Answer.tokens`
- cli: `--out` 기본값을 `reports/<answerer>.md`로 바꾼다(`--out`을 주면 그 경로)
- `reports/skeleton.md`를 `git mv`로 `reports/stub.md`로 옮긴 뒤 `uv run subway-eval`로 다시 써서 손으로 적은 「jw 기준 측정」 절이 빠지게 한다
- 테스트 먼저: `render`가 `파싱 실패 1/2`를 세는지, `토큰` 열이 있는지, `main([])`의 기본 출력 경로가 `reports/stub.md`인지(tmp 경로를 쓰려면 monkeypatch로 `REPORT_DIR`를 바꾼다)
- 커밋: `feature: Answer에 파싱 실패·토큰을 넣고 답하는 쪽마다 리포트를 따로 쓴다`

### Task 2: LLM 혼자 답하는 쪽

**Files:** Modify `answerers.py`, `cli.py`, `pyproject.toml`; Create `.env.example`, `tests/test_llm.py`

- `uv add openai`
- `answerers.py`
  - `MODEL = os.environ.get("OPENAI_MODEL") or "gpt-5.4-mini"`
  - 시스템 지시(상수 `SYSTEM`): 서울 지하철 1~8호선만 쓴다 / 출발역부터 도착역까지 **지나는 역을 빠짐없이** 순서대로, 역마다 그 구간에서 탄 호선 번호(1~8)를 쓴다 / 갈아타는 역은 내리는 호선과 타는 호선으로 두 번 쓴다 / 소요 시간은 초 단위 정수, 모르면 null. **역 이름 목록·질문별 정답·힌트를 넣지 않는다**
  - 갈아타는 역 표기는 `grade.py`가 쓰는 노드 모양(`(역, 호선)`)과 같게 한다. 예: 서울역(4) … 동대문역사문화공원(4), 동대문역사문화공원(2) … 잠실(2)
  - JSON schema: `{"path": [{"station": str, "line": int}], "seconds": int | null}`, `strict: true`
  - `make_llm(client=None) -> Callable[[str], Answer]` — client를 주입받는다. 없으면 `openai.OpenAI()`. 호출은 `client.responses.create(model=MODEL, instructions=SYSTEM, input=question_text, text={"format": {"type": "json_schema", ...}})`
  - 응답 처리: `raw = resp.output_text`, `tokens = resp.usage.input_tokens + resp.usage.output_tokens`. `json.loads` → path 원소마다 `(station: str, line: int)`로 바꾼다. JSON이 아니거나 키·타입이 틀리면 `Answer(parse_error="<이유 한 줄>", raw=raw, tokens=tokens)` — 예외를 밖으로 던지지 않는다
  - API 예외(`openai.APIError` 계열)는 잡지 않는다
  - `ANSWERERS = {"stub": stub, "llm": lambda text: _llm()(text)}`처럼 키 등록 시점에 client를 만들지 않는다(import만으로 키가 필요하면 안 된다)
- cli
  - `--answerer llm`인데 `OPENAI_API_KEY`가 비었으면 `OPENAI_API_KEY가 없다` 를 stderr에 쓰고 exit 2
  - API 예외가 나면 메시지를 stderr에 쓰고 exit 1(리포트를 쓰지 않는다)
  - `--raw PATH`: 질문별 `{qid: {"raw": ..., "tokens": ..., "parse_error": ...}}`를 JSON으로 쓴다
  - `render`에 `model`을 넘긴다(`llm`일 때만)
- `.env.example`: `OPENAI_API_KEY=` / `OPENAI_MODEL=`
- 테스트(`tests/test_llm.py`, API 호출 없음 — 가짜 client는 `output_text`와 `usage`만 가진 객체를 돌려준다)
  - 정상 JSON → `Answer.path`가 `(역, 호선)` 튜플 목록, `seconds`, `tokens`가 채워진다
  - JSON이 아님 / `path` 없음 / `line`이 문자열 → `parse_error`가 채워지고 path는 빈 목록, 예외 없음
  - 가짜 client가 받은 `instructions`에 질문의 정답 역 이름(예: `동대문역사문화공원`)이 없다 — 시스템 지시에 힌트가 없는지
  - `ANSWERERS`의 키가 `["stub", "llm"]`이고, import만으로 `openai.OpenAI()`가 불리지 않는다
  - `main(["--answerer", "llm"])`에 키가 없으면(monkeypatch로 지움) exit 2
- 기존 `test_registry_has_stub_only`는 이 변경에 맞게 고친다
- 커밋: `feature: 질문 문장만 받고 경로와 소요 시간을 답하는 LLM 혼자 답하는 쪽`

### Task 3: 실제 호출 — 녹화와 측정

1. `.gitignore`에 `runs/` 추가
2. 실제 키로 두 번 돌린다:
   ```bash
   uv run subway-eval --answerer llm --raw runs/186/raw-1.json; echo "exit=$?"
   uv run subway-eval --answerer llm --raw runs/186/raw-2.json; echo "exit=$?"
   ```
   두 번째 실행이 `reports/llm.md`를 쓴다. 그 파일을 커밋한다
3. `runs/186/raw-1.json`을 `tests/fixtures/llm_responses.json`으로 복사한다(실제 응답 녹화). 테스트 하나를 더한다: 녹화된 원문 3개를 가짜 client로 재생해 `main(["--answerer", "llm", "--out", tmp])`가 exit 0이고 리포트에 `q1`~`q3` 행이 있다. 녹화 원문에 `parse_error`가 있었으면 리포트에서도 같은 행이 `답 있음` `X`다
4. 실패 징후 1·3을 재서 구간과 값을 적는다. 「다시 잰다」 구간이면 그 절차(원문을 보고 한 번 고치고 다시 잰다)를 한 번 한 뒤 적는다
5. 커밋: `test: 실제 LLM 응답을 녹화해 재생 테스트로 고정` / `docs: #186 LLM 혼자 리포트`

### Task 4: 개념 표

- `docs/concepts.md` `## 개념` 표
  - 추가: `Answer.parse_error`, `Answer.tokens`, `Answer.raw`, `llm`(답하는 쪽), `SYSTEM`(LLM 혼자 시스템 지시), `OPENAI_MODEL`
  - 수정: 리포트 열(11개, `토큰` 추가), `ANSWERERS`(`stub`·`llm`)
  - 정의한 곳 줄 번호는 실제 파일에서 다시 확인한다
- `## 용어` 절은 고치지 않는다
- 커밋: `docs: #186 개념 표`

## Pre-PR checks

Pre-PR checks (all required — do not assume pass, show output):
1. New env vars: `git diff main...HEAD` added lines matching `os\.environ\.get|os\.getenv|process\.env\.` — log any found.
   - 이번에는 `OPENAI_MODEL`이 나와야 한다. `.env.example`에 있는지 같이 본다
2. Server boots — detached-safe, NO interactive Ctrl+C (no TTY in orch). Background + timeout + curl the port + kill. Never bare `runserver` (hangs the loop till ORCH_STUCK_SECS). Django → `source <venv>/bin/activate && cd web && (timeout 20 python manage.py runserver 127.0.0.1:8000 --noreload &) ; sleep 8; curl -sf http://127.0.0.1:8000/ -o /dev/null && echo BOOT_OK ; pkill -f runserver`; CDK → `cdk synth` (no server); Zappa/Lambda Django → same background+timeout with `PYENV_VERSION=<env> --settings=<app>.settings.local`; CLI/library → smoke-run the entrypoint (it must self-terminate); else project-specific.
   - 이 레포는 CLI다: `timeout 60 uv run subway-eval; echo exit=$?` 와 `timeout 120 uv run subway-eval --answerer llm --out /tmp/llm-smoke.md; echo exit=$?`
3. Full test suite green (show pass/fail). If no runner: state `no tests — skipped`, do not silently pass.
   - `uv run pytest -q` 와 `uv run ruff check .`

Then: completeness via `sc:reflect` vs plan; code review via `superpowers:requesting-code-review` (fix all Critical/Important); commit (`~/prv` repo면 `docs/plans/`도 포함); PR via `gh pr create --assignee @me --base main` (personal title + Summary/Changes/Notes, then update the Notion PR property). **PR을 만들면 이 루프는 끝난다** — 여기서 `pr-review-toolkit:review-pr`을 돌리지 말 것. 그 리뷰는 Phase C의 별도 세션이 맡는다.

내장 `/code-review`를 여기 쓰지 말 것 — 헤드리스 세션의 available-skills에 없다.

## Done criteria

- [ ] Task 1~4 완료, 각 Task가 커밋 하나(Task 3은 커밋 둘)
- [ ] Pre-PR checks 3개 출력이 PR 본문에 있다
- [ ] 실패 징후 1을 실제 호출로 재서 값(답하는 쪽 · `답 있음` `O` 수 · 파싱 실패 수)과 구간을 PR 본문에 적었다. 실패 징후 2·3 값(두 번 실행의 정답률·`답 있음` 수·지어낸 역·조건 어김·토큰 합)도 적었다. 리포트 파일에는 손으로 쓰지 않는다
- [ ] PR 본문에 `answerers.py`의 시스템 지시(`SYSTEM`) 전문을 붙였다
- [ ] PR 본문 맨 위에 `## 착수 전 기준 (jw)` 절 — plan의 `## jw 기준` 원문 + 그 기준으로 잰 결과
- [ ] `docs/concepts.md` `## 개념` 표를 고쳤다. plan·리포트·PR 본문은 `docs/concepts.md` 용어 절의 말을 쓰고, 쓰지 말 말을 쓰지 않는다
- [ ] 프롬프트에 역 목록·정답·질문별 힌트를 넣지 않았다. 정답률을 올리려고 프롬프트를 질문에 맞춰 고치지 않았다
- [ ] 테스트는 API를 부르지 않는다(`OPENAI_API_KEY`를 지운 환경에서 `uv run pytest -q`가 통과한다)
- [ ] base 브랜치(`main`)를 작업 브랜치에 merge·rebase하지 않았다
- [ ] PR 생성: `gh pr create --assignee @me --base main`. 계정은 `jongwoo315`(`gh api user -q .login`으로 확인)
- [ ] Notion PR 프로퍼티 갱신:
  ```bash
  printf '{"properties":{"PR":{"url":"%s"}}}' "<PR URL>" > /tmp/pr186.json
  "$HOME/.claude/tools/notion-api/notion-api" PATCH /v1/pages/41441e61-65c0-81eb-af7c-c1d12c379d21 /tmp/pr186.json
  ```
