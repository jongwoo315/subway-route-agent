# #188 LLM + 도구 Implementation Plan

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
**Notion:** #188 https://app.notion.com/p/41441e6165c081e5ad29f5daee2f373e (page id `41441e61-65c0-81e5-ad29-f5daee2f373e`)
**설계:** `/Users/jw/prv/.wt/188-llm-tools/docs/plans/188-1111-design-llm-tools.md` — 착수 전에 먼저 읽는다. 설계 결정 표가 거기 있다
**흐름:** 이미 있다(#185~#187). 바꾸는 stub: 답하는 쪽 목록의 「LLM + 도구」 빈 자리, 리포트 `도구 호출` 열(늘 0)

## jw 기준

도구를 사용했을 때 역간 최단거리를 llm단독으로 계산했을 때보다 정확하게 계산한다, llm단독과 llm+도구로 같은 질의를 했을 때 결과를 비교할 수 있다

## 통과 기준

- `uv run subway-eval --answerer stub llm llm-tools` 명령 하나로 세 답하는 쪽이 같은 질문 10개에 답하고, `reports/stub.md`·`reports/llm.md`·`reports/llm-tools.md`와 비교 리포트 `reports/compare.md`가 생긴다(exit 0)
- `reports/compare.md`의 표에 질문 10개가 모두 있고, 질문마다 세 답하는 쪽의 `맞음`·`답 경로 소요 시간`·`답이 말한 시간`이 한 줄에 나온다
- `reports/llm-tools.md`의 `도구 호출` 열이 실제 호출 수다(질문 하나라도 0이 아닌 값)
- 도구는 여러 호선을 거치는 경로나 그 소요 시간을 돌려주지 않는다. `travel_seconds`는 갈아타지 않는 한 호선 안의 소요 시간만 준다(테스트로 고정)
- 테스트는 API를 부르지 않는다. 녹화한 도구 호출 응답으로 LLM + 도구를 끝까지 재생하는 테스트가 있다
- `uv run subway-eval`(인자 없음, stub)은 지금처럼 키 없이 `reports/stub.md`만 쓴다

## 이번에 안 하는 것

- 도구를 잘게 줄지 크게 줄지 비교 (다음 티켓)
- LLM 혼자 쪽 수정: `answerers.py`의 `SYSTEM`·`SCHEMA`·`_parse`·`make_llm`을 바꾸지 않는다. LLM + 도구는 `SCHEMA`·`_parse`를 그대로 가져다 쓴다
- 채점 규칙(`grade.py`) 수정: 별칭 역 채점(#187 리뷰 #3), 정답 없음 질문 채점(#187 리뷰 #4)
- 환승 시간·기다리는 시간 stub 수정 (#189) <!-- style-exempt -->
- 질문 셋(`data/questions.json`) 변경
- **지시문·도구 설명 문구를 바꿔 가며 정답률을 올리는 것.** 처음 쓴 문구로 잰다. 도구 구현 버그(테스트로 재현되는 것)는 고치고 다시 잰다

## 실패 징후

1. **jw 기준을 잰다.** 정답 = 소요 시간이 가장 짧은 경로(용어 `정답`). 「더 정확하게」는 같은 실행 안에서 LLM + 도구의 정답률이 LLM 혼자의 정답률보다 높은지로 본다. 정답 없음 질문(q6·q7) 때문에 둘 다 최대 8/10이다
   - 잴 방법: 실제 키로 `uv run subway-eval --answerer stub llm llm-tools --raw runs/188/raw-1.json`을 두 번 돌린다(두 번째는 `raw-2.json`). 실행마다 비교 리포트 머리의 두 정답률을 읽는다
   - 통과: 두 실행 모두 LLM + 도구 정답률이 같은 실행의 LLM 혼자 정답률보다 높다
   - 다시 잰다: 두 실행 중 하나에서만 높다. 같은 명령을 두 번 더 돌려(`raw-3`·`raw-4`) 네 실행 값을 나란히 적는다
   - 미완: 두 실행 모두 LLM + 도구가 같거나 낮다, 실행이 exit 0으로 끝나지 않는다, 또는 리포트가 실제 API 호출 없이 만들어졌다(fixture 재생·가짜 client 포함). 같거나 낮으면 `--raw` 원문에서 도구 설명이나 파싱 쪽 원인을 먼저 찾아 그 사실을 PR 본문에 적는다(티켓 실패 징후). 문구를 바꿔 다시 재지 않는다
2. **도구가 정답을 건네는지.** `travel_seconds`가 다른 호선으로 갈아타는 길을 계산하면 정답을 건네는 셈이다. 테스트: 서울역(1·4호선)→잠실(2·8호선)처럼 한 호선에 같이 없는 두 역을 주면 오류 결과를 돌려준다. `tools.py`가 `route.shortest`를 부르지 않는다(`grep -n shortest src/subway_route_agent/tools.py`가 비었다). 하나라도 어기면 미완
3. **비교할 수 있는지.** 비교 리포트 표 행이 질문 수(10)와 같고, 질문마다 세 답하는 쪽 값이 다 있다. 아니면 미완
4. 「계산」 쪽 값: 답이 말한 시간이 정답 소요 시간과 같은 질문 수를 답하는 쪽마다 센다. 임계값 없음. 값만 적는다
5. 비용: 답하는 쪽마다 도구 호출 합·토큰 합·응답 시간 합, 도구 호출 상한(25)에 닿은 질문 수. 임계값 없음(첫 측정). 값만 적는다 <!-- style-exempt -->

## 파일 구성

| 파일 | 할 일 |
| --- | --- |
| `src/subway_route_agent/tools.py` (새) | 도구 셋, OpenAI 도구 정의(`TOOLS`), 이름으로 실행하는 `call_tool` |
| `src/subway_route_agent/answerers.py` | `make_llm_tools`, `TOOL_CALL_LIMIT`, `ANSWERERS["llm-tools"]`. LLM 혼자 쪽 코드는 그대로 |
| `src/subway_route_agent/cli.py` | `--answerer` 여러 값, 답하는 쪽마다 리포트, 둘 이상이면 비교 리포트, `--raw` 나눠 쓰기 |
| `src/subway_route_agent/report.py` | `render_compare` |
| `tests/test_tools.py` (새) | 도구 셋 |
| `tests/test_llm_tools.py` (새) | 도구 호출 반복·상한·토큰 합, 녹화 재생 | <!-- style-exempt -->
| `tests/test_cli.py` | 여러 답하는 쪽, 비교 리포트 |
| `tests/fixtures/llm_tools_responses.json` (새) | 실제 키로 녹화한 응답(질문 2개) |
| `scripts/record_llm_tools.py` (새) | 녹화 스크립트 |
| `reports/*.md` | 측정 명령으로 다시 생성 |
| `docs/concepts.md` | `## 개념` 표 |

### Task 1: 도구 셋

**Files:** Create `src/subway_route_agent/tools.py`, `tests/test_tools.py`

- 그래프(`graph.build_graph(load_rows())`)와 CSV 행(`load_rows()`)만 쓴다. `route.shortest`를 import하지 않는다
- `find_station(name: str) -> dict`
  - 별칭(`graph.ALIASES`)을 바꾼 이름이 그래프에 있으면 `{"found": true, "station": 그래프 이름, "lines": [호선 오름차순]}`
  - 없으면 `{"found": false, "candidates": [이름에 name이 들어간 그래프 역, 가나다순 최대 10개]}`
- `line_stations(line: int) -> dict`
  - `{"line": L, "segments": [{"from", "to", "seconds", "one_way"}]}`. CSV 행 순서 그대로, `build_graph`와 같은 규칙으로 이은 구간이다: 지선 첫 행은 `graph.BRANCH_HEADS`의 역에서 갈라지고, 2호선은 마지막에 시청으로 돌아오고, 6호선 응암순환 구간은 `one_way: true`
  - 없는 호선이면 `{"error": "1~8호선만 있다"}`
- `travel_seconds(line: int, from_station: str, to_station: str) -> dict`
  - 그 호선의 노드와 같은 호선 간선만 남긴 그래프에서 다익스트라로 소요 시간(초)을 구해 `{"seconds": N}`. 환승 간선은 쓰지 않는다. 경로(지나는 역)는 돌려주지 않는다
  - 두 역 중 하나라도 그 호선에 없으면 `{"error": "<역>은 <L>호선에 없다"}`, 갈 수 없으면(응암순환 역방향 등) `{"error": "..."}`
  - 별칭은 바꾼 뒤 찾는다
- `TOOLS`: Responses API 함수 도구 정의 목록(`{"type": "function", "name", "description", "parameters", "strict": true}`). 설명은 한국어 한두 문장으로, 돌려주는 값만 설명한다. 「최단」·「추천」 같은 말을 쓰지 않는다
- `call_tool(name: str, arguments: str) -> str`: JSON 인자를 읽어 해당 도구를 부르고 결과를 JSON 문자열로 돌려준다. 모르는 도구·잘못된 인자는 예외 대신 `{"error": ...}`
- 테스트 먼저
  - `find_station("강남")` → 2호선. `find_station("총신대입구")` → `이수`, 4·7호선. 없는 이름 → `found: false`, 후보 목록
  - `line_stations(2)`: 구간 수가 CSV 2호선 행 수 − 1이다. `용답`의 `from`이 `성수`, `도림천`의 `from`이 `신도림`. 마지막 본선 구간이 `충정로→시청`
  - `travel_seconds(2, "강남", "홍대입구")` = 1740(q1 손 계산 값). `travel_seconds(5, "방화", "마천")` = q3 `hand_seconds`
  - 2번 실패 징후: `travel_seconds(2, "서울역", "잠실")` → `error`. `travel_seconds(1, "서울역", "잠실")` → `error`
  - `call_tool("없는도구", "{}")`·`call_tool("travel_seconds", "not json")` → `error`가 든 JSON
- 커밋: `feature: LLM에게 줄 도구 셋(역 검색, 노선 구간, 한 호선 안 소요 시간)을 더한다`

### Task 2: LLM + 도구 답하는 쪽

**Files:** Modify `src/subway_route_agent/answerers.py`, Create `tests/test_llm_tools.py`

- `TOOL_CALL_LIMIT = 25`
- `TOOLS_SYSTEM`: `SYSTEM`과 같은 답 형식 설명 + 「도구로 역·노선·한 호선 안 소요 시간을 확인할 수 있다. 환승 한 번은 180초다. 경로는 직접 고른다」. 역 목록·정답·질문별 힌트를 넣지 않는다. 180은 `graph.TRANSFER_SECONDS`에서 가져온다
- `make_llm_tools(client=None) -> Callable[[str], Answer]`
  - 요청: `model=MODEL`, `instructions=TOOLS_SYSTEM`, `input=[{"role": "user", "content": 질문}]`, `tools=TOOLS`, `text`는 LLM 혼자와 같은 json_schema(`SCHEMA`, strict)
  - 응답 `output`에서 `type == "function_call"` 항목을 찾는다. 있으면 응답의 `output` 항목을 전부 입력에 이어 붙이고, 호출마다 `{"type": "function_call_output", "call_id", "output": call_tool(...)}`를 붙여 다시 부른다. 호출 하나를 도구 호출 1번으로 센다
  - `function_call`이 없으면 `output_text`를 `_parse`로 읽는다. `status != "completed"`·파싱 실패 처리는 `make_llm`과 같다
  - 도구 호출이 `TOOL_CALL_LIMIT`을 넘기 직전에 멈추고 `Answer(parse_error="도구 호출 상한(25)에 닿았다", ...)` <!-- style-exempt -->
  - `tokens`는 모든 요청의 `usage.input_tokens + output_tokens` 합, `tool_calls`는 실행한 도구 호출 수, `raw`는 최종 `output_text`(상한이면 마지막 응답의 `output_text`) <!-- style-exempt -->
- `ANSWERERS["llm-tools"]`: `llm`처럼 첫 호출 때 client를 만든다(import만으로 키가 필요하면 안 된다)
- 테스트 먼저(가짜 client — `output`·`output_text`·`usage`·`status`를 가진 응답을 차례로 돌려준다) <!-- style-exempt -->
  - 도구 호출 2번 뒤 최종 JSON → `tool_calls == 2`, `tokens`가 세 요청 합, 두 번째 요청 `input`에 `function_call_output`이 `call_id`와 함께 있다
  - 매번 `function_call`만 돌려주면 25번에서 멈추고 `parse_error`가 고정 문구
  - 요청의 `instructions`에 역 이름 목록이 없다(#186 테스트 방식)
  - 키 없이 `ANSWERERS`를 import해도 client를 만들지 않는다
- 커밋: `feature: 도구를 불러 가며 답하는 LLM + 도구 답하는 쪽을 더한다`

### Task 3: 명령 하나로 비교

**Files:** Modify `cli.py`, `report.py`, `tests/test_cli.py`

- `--answerer`를 `nargs="+"`로 바꾼다. 기본값 `["stub"]`. 같은 이름이 두 번이면 한 번만 돈다 <!-- style-exempt -->
- `llm`이나 `llm-tools`가 있으면 키 검사(없으면 exit 2)
- 답하는 쪽마다 지금처럼 `reports/<이름>.md`를 쓴다(`render` 재사용, `llm-tools`도 모델 이름을 적는다). 머리에 LLM + 도구는 `- 도구: find_station, line_stations, travel_seconds (호출 상한 25)` 줄을 더한다 <!-- style-exempt -->
- 답하는 쪽이 둘 이상이면 `render_compare`로 `reports/compare.md`를 더 쓴다. `--out`은 답하는 쪽이 하나면 그 리포트, 둘 이상이면 비교 리포트 경로다
- `render_compare(data_name, by_answerer: dict[str, list[Result]], models)`
  - 머리: 답하는 쪽마다 한 줄 — 정답률 `K/N`, 파싱 실패, 도구 호출 합, 토큰 합, 응답 시간 합(초), 답이 말한 시간이 정답 소요 시간과 같은 질문 수, 도구 호출 상한에 닿은 질문 수 <!-- style-exempt -->
  - 머리에 두 지시문의 차이 한 줄: `LLM + 도구 지시문에만 환승 180초와 도구 사용 안내가 있다`
  - 표 열: `질문`, `정답 시간`, 그리고 답하는 쪽마다 `<이름> 맞음`, `<이름> 답 경로 소요 시간`, `<이름> 답이 말한 시간`. 답 경로 소요 시간은 `grade.path_seconds`로 잰다. 경로가 비면 `답 없음`, 끊기면 `끊김`. 시간 형식은 `format_seconds`
- `--raw`: 답하는 쪽이 하나면 그 파일, 둘 이상이면 `<stem>-<이름>.json`
- API 오류 처리: 지금처럼 그 자리에서 exit 1. 이미 끝난 답하는 쪽의 원문은 `--raw`가 있으면 쓴다
- 테스트 먼저(stub과 가짜 답하는 쪽을 `monkeypatch`로 `ANSWERERS`에 넣는다. API를 부르지 않는다)
  - `--answerer stub` 하나면 비교 리포트가 안 생긴다
  - 답하는 쪽 둘이면 각 리포트 + `compare.md`, 표 행 수 = 질문 수, 열에 두 이름이 다 있다
  - 끊긴 경로는 `끊김`, 빈 답은 `답 없음`
  - 키 없이 `--answerer stub llm-tools` → exit 2
- `uv run subway-eval`로 `reports/stub.md`가 그대로 나오는지 본다
- 커밋: `feature: 여러 답하는 쪽을 한 명령으로 돌려 비교 리포트를 쓴다`

### Task 4: 녹화와 재생 테스트

**Files:** Create `scripts/record_llm_tools.py`, `tests/fixtures/llm_tools_responses.json`, Modify `tests/test_llm_tools.py`

- 녹화 스크립트: 실제 client를 감싸 `responses.create`가 돌려준 응답을 `resp.model_dump()`로 질문별 목록에 쌓고, 질문 2개(q4, q10)를 `make_llm_tools`로 돌려 JSON으로 쓴다. 실행: `uv run python scripts/record_llm_tools.py`
- 재생: 가짜 client가 녹화된 dict를 `SimpleNamespace`로 바꿔 차례로 돌려준다(`output_text`는 dict에 없으면 `output`의 message 텍스트에서 만든다 — 녹화 때 `output_text`도 같이 저장하면 더 쉽다) <!-- style-exempt -->
- 재생 테스트: 질문 파일을 q4·q10만 든 파일로 바꾸고(`test_llm.py`의 `use_recorded_questions` 재사용) `main(["--answerer", "llm-tools", ...])`이 exit 0, 리포트 `도구 호출` 열이 녹화의 호출 수와 같다
- 커밋: `test: 실제 키로 녹화한 도구 호출 응답으로 LLM + 도구를 재생한다`

### Task 5: 실제 호출 측정과 개념 표

1. 실제 키로 두 번 돌린다
   ```bash
   mkdir -p runs/188
   uv run subway-eval --answerer stub llm llm-tools --raw runs/188/raw-1.json --out runs/188/compare-1.md; echo "exit=$?"
   uv run subway-eval --answerer stub llm llm-tools --raw runs/188/raw-2.json; echo "exit=$?"
   ```
   두 번째 실행이 `reports/`의 리포트 넷을 쓴다. 실패 징후 1의 구간을 정한다. 「다시 잰다」면 `raw-3`·`raw-4`로 두 번 더 돌리고(`--out runs/188/compare-3.md` 등), 마지막 실행의 리포트가 `reports/`에 남게 한다. `runs/`는 `.gitignore`에 이미 있다
2. 「미완」이면 `--raw` 원문에서 원인(도구를 안 불렀다, 도구 결과를 잘못 읽었다, 상한에 닿았다, 파싱 실패 등)을 질문별로 찾아 PR 본문에 적는다. 도구 구현 버그면 테스트로 재현해 고치고 1부터 다시 잰다. 지시문·도구 설명 문구는 바꾸지 않는다 <!-- style-exempt -->
3. `docs/concepts.md` `## 개념` 표에 행을 더한다: `find_station`, `line_stations`, `travel_seconds`, `TOOL_CALL_LIMIT`, `llm-tools`(답하는 쪽 이름), `compare.md`(비교 리포트 열), `--answerer` 여러 값. 정의한 곳 줄 번호는 실제 파일에서 확인한다. `## 용어` 절은 고치지 않는다(Kickoff에서 main이 썼다)
4. 커밋: `docs: #188 리포트(stub · LLM 혼자 · LLM + 도구 · 비교)` / `docs: #188 개념 표`

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

- [ ] Task 1~4는 커밋 하나씩, Task 5는 커밋 둘
- [ ] Pre-PR checks 3개 출력이 PR 본문에 있다
- [ ] 실패 징후 1을 실제 호출로 재서 실행마다 두 정답률(LLM 혼자, LLM + 도구)·exit code와 구간을 PR 본문에 적었다. 「다시 잰다」였으면 네 실행 값을 나란히 적었다. 「미완」이었으면 질문별 원인을 적었다. 리포트 파일에는 손으로 쓰지 않는다
- [ ] 실패 징후 2·3을 확인한 결과(테스트 이름, grep 출력, 비교 리포트 행 수)를 PR 본문에 적었다
- [ ] 실패 징후 4·5 값을 답하는 쪽마다 PR 본문에 적었다
- [ ] PR 본문 맨 위에 `## 착수 전 기준 (jw)` 절 — plan의 `## jw 기준` 원문 + 그 기준으로 잰 결과
- [ ] `docs/concepts.md` `## 개념` 표를 고쳤다. plan·리포트·PR 본문은 `docs/concepts.md` 용어 절의 말을 쓰고, 쓰지 말 말을 쓰지 않는다
- [ ] LLM 혼자 쪽을 고치지 않았다: `git diff main...HEAD -- src/subway_route_agent/answerers.py`에 `SYSTEM`·`SCHEMA`·`_parse`·`make_llm`의 줄이 바뀌거나 지워진 것이 없다(더한 줄만 있다). `grade.py`·`data/questions.json` diff가 비었다
- [ ] 테스트는 API를 부르지 않는다(`OPENAI_API_KEY`를 지운 환경에서 `uv run pytest -q`가 통과한다). 기존 녹화 fixture(`tests/fixtures/llm_responses.json`)는 그대로 둔다
- [ ] base 브랜치(`main`)를 작업 브랜치에 merge·rebase하지 않았다
- [ ] PR 생성: `gh pr create --assignee @me --base main`. 계정은 `jongwoo315`(`gh api user -q .login`으로 확인)
- [ ] Notion PR 프로퍼티 갱신:
  ```bash
  printf '{"properties":{"PR":{"url":"%s"}}}' "<PR URL>" > /tmp/pr188.json
  "$HOME/.claude/tools/notion-api/notion-api" PATCH /v1/pages/41441e61-65c0-81e5-ad29-f5daee2f373e /tmp/pr188.json
  ```
