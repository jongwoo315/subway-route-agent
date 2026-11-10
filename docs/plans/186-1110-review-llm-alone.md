# #186 리뷰 — PR #2

**대상:** `main...HEAD` — 15 commits, 18 files, +1059 −54 (리뷰 파일 커밋 전, 리뷰 fix 9커밋 포함)
**plan:** docs/plans/186-1110-plan-llm-alone.md

단어장 검사: `docs/concepts.md` 용어 절의 「쓰지 말 말」(에이전트·솔버·기준 경로·레퍼런스·환각 역·제약 위반·순수 LLM·베이스라인 LLM·형식 오류·포맷 에러)을 이 PR의 코드·주석·docstring·문서(용어 절 자신 제외)에서 찾았다. 나온 곳 없음.

## 지적

| # | 심각도 | 위치 | 내용 | 처리 |
| --- | --- | --- | --- | --- |
| 1 | Important | `src/subway_route_agent/answerers.py:92` | 응답에 `usage`가 없거나(`None`) 거절·토큰 한도로 `status`가 `completed`가 아니면 `AttributeError`로 죽거나 빈 원문이 「JSON이 아니다」로 기록돼 원인이 가려진다 | fix `cf4fd10` |
| 2 | Important | `src/subway_route_agent/cli.py:40` | 질문 중간에 API 오류가 나면 이미 받은 질문의 원문이 `--raw` 파일에 안 남는다 (예: q3에서 429 → q1·q2 원문 유실) | fix `239e2c4` |
| 3 | Important | `src/subway_route_agent/answerers.py:62` | `{"path": [], ...}`는 파싱 실패로 세지 않고 stub 행과 같은 `답 있음 X`로 보여 구분이 안 된다 | fix `a0975f1` |
| 4 | Important | `tests/test_llm.py:129` | 재생 테스트의 `parse_error` 분기가 죽어 있다(녹화 3행 모두 `parse_error` 없음). 읽지 못한 행이 `X`가 되는지 아무 테스트도 확인하지 않는다. 파싱 실패 줄·모델 이름·맞음 열도 안 본다 | fix `3a61d79` |
| 5 | Important | `tests/test_llm.py:92` | API 오류 테스트가 `make_llm`을 거치지 않아, `make_llm` 안에서 예외를 삼켜 파싱 실패로 바꿔도 통과한다 | fix `9f0555a` |
| 6 | Important | `tests/test_cli.py:10` | `stub`이 키 없이 도는지 확인하는 테스트가 `OPENAI_API_KEY`를 지우지 않아, 키가 있는 개발 환경에서는 회귀가 가려진다 | fix `1526f0d` |
| 7 | Important | `src/subway_route_agent/answerers.py:21` | `stub` docstring의 「LLM 혼자가 이 자리에 들어간다」가 낡았다. `llm`이 들어왔고 `stub`은 그대로 남았다 | fix `b2f0627` |
| 8 | Critical | `docs/concepts.md:24-26` | `Answer.path`·`seconds`·`tool_calls` 정의한 곳이 `answerers.py:7/8/9`로 남았다(필드가 추가되며 실제 `:10/11/12`로 바뀜) | fix `2a6f337` |
| 9 | Important | `docs/concepts.md:39-40` | `ANSWERERS`(`:109`→`:115`)와 `llm`(`:76` `make_llm`→`:85` `def llm`) 정의한 곳이 어긋났고, 리뷰 fix로 `answerers.py`가 길어져 다시 어긋났다. `Answer.parse_error` 행의 조사(`행이 … 센다`)도 틀렸다 | fix `fcd222b` |
| 10 | Important | `src/subway_route_agent/grade.py:58` | LLM이 쓴 역 이름을 그래프 이름으로 맞추지 않아, 실제 역이 `지어낸 역`으로 세어지고 경로가 끊긴 것으로 채점된다 (예: raw-2 q1의 `총신대입구(이수)`, 그래프에는 `이수`). `지어낸 역` 열이 #188 기준값에 이름 차이로 부풀려 들어간다 | defer — 무엇을 「지어낸 역」으로 칠지는 채점 규칙이라 jw가 정한다. #185 리뷰 #9가 「LLM 답하는 쪽 티켓」으로 미룬 것이지만 plan 파일 목록에 `grade.py`가 없고, 바꾸면 이번 측정값이 바뀐다. 이름 맞춤을 넣는 후속 티켓에서 `grade.py`와 같이 다룬다 |
| 11 | Important | `tests/test_llm.py:87` | 레지스트리 테스트는 `ANSWERERS`를 모듈 맨 위에서 이미 import한 뒤 `OpenAI`를 막아서, import 시점에 client를 만들어도(키가 있는 환경에서는) 통과한다. 첫 호출에 한 번만 만드는지(`@cache`)도 확인하지 않는다 | defer — plan의 테스트 문구(「키가 `["stub","llm"]`이고 import만으로 `OpenAI()`가 불리지 않는다」)는 만족한다. 키 없는 서브프로세스 import로 바꾸는 것은 후속에서 다룬다 |
| 12 | Important | `docs/concepts.md:15` | 용어 절 `LLM 혼자` 뜻에 「답하는 답하는 쪽」으로 단어가 겹친다 | won't-fix — plan이 `## 용어` 절은 고치지 않는다고 못 박았다(Kickoff에서 main이 쓴 절). 고치려면 main에서 |
| 13 | Suggestion | `src/subway_route_agent/grade.py:58` | `지어낸 역`이 역 이름만 세어, 다른 호선에 있는 역을 엉뚱한 호선으로 쓴 경우나 1~8 밖 호선은 0으로 센다 (raw-2 q2의 `동작(9)`·`고속터미널(9)`) | 기록만 |
| 14 | Suggestion | `src/subway_route_agent/answerers.py:34` | 프롬프트가 「모르면 null」이라 6개 응답 모두 `seconds`가 `null`이고 경로도 모두 끊겨 있어, `지어낸 소요 시간` 0은 측정이 아니라 구조상 0이다. PR 본문 「실패 징후 값」에 이미 적었다 | 기록만 |
| 15 | Suggestion | `.env.example:1` | `.env`를 읽는 코드가 없어 복사만 하면 exit 2가 난다. PR 본문 Notes에 셸 환경변수로 내보내야 한다고 적었다 | 기록만 |
| 16 | Suggestion | `src/subway_route_agent/report.py:62` | 리포트에 파싱 실패 건수만 있고 어느 질문이 왜 실패했는지는 `--raw`에만 있다. stub 리포트에도 `파싱 실패 0/3`이 찍힌다 | 기록만 |
| 17 | Suggestion | `src/subway_route_agent/cli.py:32` | `--raw`가 `stub`에도 쓰여, 녹화 fixture 경로를 주면 덮어쓴다 | 기록만 |
| 18 | Suggestion | `src/subway_route_agent/answerers.py:101` | client를 첫 호출 안에서 만들어 q1 `응답 시간(ms)`에 client 생성이 들어가고, 생성 중 `OpenAIError`(`APIError` 아님)는 exit 1로 안 잡힌다. `line`이 1~8 밖이거나 `seconds`가 음수여도 파싱 실패가 아니다 | 기록만 |
| 19 | Suggestion | `tests/test_llm.py:43` | `_parse` 경계 일부(`line: true`, `seconds` 문자열·실수, path 원소가 dict 아님)와 `--raw` 형식·`reports/llm.md` 기본 경로·11셀 행 검사 테스트 없음. 힌트 검사가 하드코딩 7개 역 이름만 본다 | 기록만 |
| 20 | Suggestion | `src/subway_route_agent/report.py:60` | 「환승 한 번에 180초로 고정한 stub이다」의 `stub`(환승 시간 가정)이 `stub` 답하는 쪽과 같은 말이라 `llm` 리포트에서 헷갈린다. 이번 diff가 만든 줄이 아니다 | 기록만 |
| 21 | Suggestion | `docs/concepts.md:42` | `OPENAI_MODEL` 행은 코드의 `MODEL`(`answerers.py:26`)을 가리킨다는 말이 없다 | 기록만 |

## plan 대조

| plan 기준 | 코드가 만족하나 | 증거 |
| --- | --- | --- |
| `uv run subway-eval --answerer llm` 하나로 질문 3개가 실제 OpenAI 호출을 거쳐 답해지고 `reports/llm.md`가 나온다 | 예 | `reports/llm.md`가 있고 `runs/186/out-2.txt`와 같다. 실행 1·2 모두 exit 0 (PR 본문, `runs/186/err-*.txt`) |
| 리포트 머리에 답하는 쪽 `llm`과 모델 이름, `파싱 실패 N/3`이 나온다. 표에 `토큰` 열이 있다 | 예 | `reports/llm.md:3,8` `- 답하는 쪽: llm (모델 gpt-5.4-mini)`, `- 파싱 실패 0/3`; 열 11개 `report.py:9`; `tests/test_cli.py` render 테스트, `tests/test_llm.py` 재생 테스트 |
| `uv run subway-eval`(기본 `stub`)은 키 없이도 끝까지 실행되고 `reports/stub.md`를 쓴다 | 예 | `reports/stub.md` 있음, `reports/skeleton.md` 없음; `test_main_runs_end_to_end`가 키를 지우고 실행 (`1526f0d`); `test_default_report_path_follows_answerer` |
| 테스트는 API를 부르지 않는다. 녹화한 실제 응답으로 파싱·채점까지 검증한다 | 예 | `tests/fixtures/llm_responses.json` = `runs/186/raw-1.json`(`cmp` 동일); `env -u OPENAI_API_KEY uv run pytest -q` → 49 passed; `uv run ruff check .` → All checks passed |
| 정답률은 이 티켓의 목표가 아니다. 값만 적고 프롬프트에 역 목록·정답·힌트를 넣지 않는다 | 예 | `answerers.py:29-35` `SYSTEM`에 역 이름 없음; `test_request_uses_instructions_and_json_schema_without_hints`; 정답률 0/3 두 번 모두 PR 본문에 적음 |
| 실패 징후 1 — 통과 구간: 답하는 쪽 `llm`, 3개 모두 `답 있음` `O`, `파싱 실패 0/3` | 판정 불가 | 값만 적는다: 실행 1·2 모두 `답 있음` `O` 3개, 파싱 실패 0/3 (`runs/186/out-1.txt`, `reports/llm.md`). 구간 판정은 PR 게이트에서 jw가 한다 |
| 실패 징후 3 — 같은 명령 두 번의 정답률·`답 있음` 수를 나란히 | 예 | PR 본문 「실패 징후 값」에 있다. 토큰 합 1350 / 1464를 `runs/186/raw-1.json`·`raw-2.json`으로 다시 계산해 일치를 확인했다 |

## 메모

- 이 세션에서 테스트를 다시 돌렸다: `env -u OPENAI_API_KEY uv run pytest -q` → 49 passed, `uv run ruff check .` → All checks passed. 리뷰 fix 뒤 `reports/llm.md`·`tests/fixtures`는 다시 만들지 않았다(실제 API 재호출 없음)
- 리뷰 fix 중 `a0975f1`(빈 path → 파싱 실패)은 `파싱 실패` 정의를 넓힌다. PR 본문의 실제 측정(두 번 모두 빈 path 없음, 파싱 실패 0/3)에는 영향이 없다
- GitHub 게시: 요약 코멘트 1건과 `defer`/`won't-fix` 행(#10, #11, #12)의 인라인 스레드를 마지막 단계에서 올렸다. 실패한 건이 있으면 아래에 적는다
- 게시 실패 1건: #10의 인라인 스레드. `grade.py`가 이 PR의 diff에 없는 파일이라 GitHub이 `422 pull_request_review_thread.path could not be resolved`로 거절했다. 같은 내용은 요약 코멘트의 #10 행에 그대로 있다. #11·#12 인라인 스레드는 올라갔다
