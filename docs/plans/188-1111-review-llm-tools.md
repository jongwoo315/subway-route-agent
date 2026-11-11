# #188 리뷰 — PR #4

**대상:** `main...HEAD` — 13 commits(리뷰 fix 6개 포함), 18 files, +3260 −62 (리뷰 파일 커밋 전)
**plan:** docs/plans/188-1111-plan-llm-tools.md

단어장 검사: `docs/concepts.md` 용어 절의 「쓰지 말 말」을 이 PR의 코드·주석·docstring·문서·리포트(용어 절 자신과 녹화 fixture 제외)에서 찾았다. 걸린 것은 `답 없음`(정답 없음의 쓰지 말 말) 하나이고 #8 행에 적었다. 나머지(에이전트·솔버·기준 경로·레퍼런스·환각 역·제약 위반·순수 LLM·베이스라인 LLM·형식 오류·포맷 에러·수동 정답·기대값·도달 불가·대조표·tool agent)는 나온 곳이 없다.

## 지적

| # | 심각도 | 위치 | 내용 | 처리 |
| --- | --- | --- | --- | --- |
| 1 | Critical | `tests/test_tools.py:72` | `travel_seconds`가 호선을 넘지 않는다는 테스트가 공허하게 통과한다. 서울역→잠실은 잠실이 1·4호선에 없어 역 검사에서 먼저 오류가 나고 다익스트라까지 가지 않는다. 환승 간선 필터 두 줄을 지워도 115개가 모두 통과했다(통과 기준 4번이 가리키는 안전장치가 테스트 없이 비어 있었다) | fix `1c298a2` `3eaf9ab` |
| 2 | Important | `src/subway_route_agent/answerers.py:24` | `stub` docstring의 「LLM + 도구는 다음 티켓에서 더한다」가 낡았다. 이 PR이 `llm-tools`를 더했다 | fix `ba7ab1a` |
| 3 | Important | `src/subway_route_agent/report.py:118` | 비교 리포트 머리의 「LLM + 도구 지시문에만 …」 줄이 `llm-tools`를 안 돌린 명령(`--answerer stub llm`)에서도 찍혔다 | fix `c8fcd34` |
| 4 | Important | `tests/test_tools.py:32` | `line_stations`가 그래프와 같은 구간을 낸다는 검증이 2·5·6호선뿐이다. 1호선 한 구간을 빼도 통과했다 | fix `ed116da` |
| 5 | Important | `src/subway_route_agent/report.py:123` | 「답이 말한 시간이 정답과 같은 질문」에서 정답 없음 질문(`truth=None`)을 빼는 조건이 테스트로 안 막혀 있었다. 조건을 지워도 통과해 stub이 2/10으로 셌을 것이다 | fix `76fb1b1` |
| 6 | Important | `src/subway_route_agent/cli.py:104` | 답하는 쪽이 둘 이상이면 `--out`을 줘도 답하는 쪽별 리포트는 `reports/<이름>.md`에 써서, `--out`으로 돌린 smoke 실행이 커밋된 리포트를 덮어쓴다. 비교 리포트만 다른 실행 값으로 남으면 두 리포트가 섞인다 | push-back — plan이 「답하는 쪽마다 지금처럼 `reports/<이름>.md`」「`--out`은 둘 이상이면 비교 리포트 경로」로 정했고 Task 5도 두 번째 실행이 `reports/`를 쓴다고 적었다. 이 PR의 커밋된 `reports/llm-tools.md`와 `compare.md`는 도구 호출 합 42·토큰 합 42871이 서로 같아 같은 실행(실행 4)의 값이다 |
| 7 | Important | `src/subway_route_agent/answerers.py:151` | `--raw`에 최종 `output_text`만 남아, plan 실패 징후 1의 「미완」 원인(도구를 안 불렀다, 도구 결과를 잘못 읽었다)을 `--raw`로 찾을 수 없다. 모델이 받은 도구 결과가 어디에도 저장되지 않는다 | defer — Task 2가 `raw`를 최종 `output_text`로 정했고 도구 호출 기록을 담으려면 공용 `Answer`에 필드를 더해야 한다. 이번 측정은 「다시 잰다」 구간이라 원인 조사가 요구되지 않았다. 다음 티켓에서 「미완」이 나오면 그 전에 호출 기록을 `--raw`에 남긴다 |
| 8 | Important | `src/subway_route_agent/answerers.py:156` | 모델이 거절(`refusal`)해도 `status`는 `completed`이고 `output_text`가 빈 문자열이라 「JSON이 아니다」로 기록되고 거절 사실이 사라진다. `make_llm`(기존 코드)에도 같은 구멍이 있고 `llm-tools`가 그대로 복제했다 | defer — plan이 `make_llm`·`_parse` 수정을 이번에 안 하는 것으로 못 박았다. 두 답하는 쪽을 같이 고치는 후속 티켓에서 다룬다 |
| 9 | Important | `src/subway_route_agent/cli.py:89` | 두 번째로 도는 답하는 쪽이 API 오류로 끝나면 먼저 끝난 답하는 쪽의 리포트와 비교 리포트가 안 써진다. `--raw`를 안 주면 먼저 끝난 쪽 결과가 stderr 메시지 없이 버려진다 | push-back — plan이 「API 오류 처리: 지금처럼 그 자리에서 exit 1. 이미 끝난 답하는 쪽의 원문은 `--raw`가 있으면 쓴다」로 정했고 `test_api_error_in_second_answerer_keeps_first_raw_and_writes_no_report`가 그 동작을 고정한다 |
| 10 | Important | `src/subway_route_agent/report.py:99` | 리포트 칸 `답 없음`이 용어 절 `정답 없음`의 쓰지 말 말이다. 같은 비교 표의 `정답 시간` 칸 `없음`(정답 없음)과 `답 경로 소요 시간` 칸 `답 없음`(빈 답)이 섞여 읽힌다. 걸린 곳: `report.py:99`, `reports/compare.md`, `tests/test_cli.py`, plan 142·148행 | defer — 칸 값 `답 없음`은 plan 142행이 정했다. 바꾸려면 용어 절에 빈 답을 가리키는 말이 먼저 필요하고(용어 절은 main이 쓴다) `reports/`를 실제 API로 다시 만들어야 한다 |
| 11 | Suggestion | `src/subway_route_agent/cli.py:89` | `openai.APIError`가 아닌 예외(`AttributeError` 등)가 15번째 질문에서 나면 앞 14개 원문이 `--raw`에 안 남는다. 기존 동작과 같다 | 기록만 |
| 12 | Suggestion | `src/subway_route_agent/answerers.py:158` | `status != completed`일 때 `incomplete_details.reason`을 안 읽어 토큰 한도 때문인지 필터 때문인지 알 수 없다 | 기록만 |
| 13 | Suggestion | `src/subway_route_agent/answerers.py:150` | 상한(25)에 닿은 질문이 `파싱 실패`에도 들어가 같은 줄의 「상한에 닿은 질문」과 겹쳐 센다. `concepts.md`가 그렇게 정의했다 | 기록만 | <!-- style-exempt -->
| 14 | Suggestion | `src/subway_route_agent/report.py:97` | `_path_cell`이 지어낸 역·끊김을 모두 `끊김`으로 표시하고, 경로가 노드 하나면 `0분 0초`가 찍힌다 | 기록만 |
| 15 | Suggestion | `scripts/record_llm_tools.py:38` | 녹화가 `parse_error`가 있어도 fixture에 쓰고 질문 수가 `QUESTION_IDS`와 달라도 실패하지 않는다. 한 질문이 실패하면 앞 질문 녹화도 파일에 못 쓴다 | 기록만 |
| 16 | Suggestion | `src/subway_route_agent/tools.py:34` | `find_station`의 후보 검색은 별칭을 바꾸기 전 `name`으로 찾고, 빈 문자열이면 아무 역 10개가 후보로 나온다 | 기록만 |
| 17 | Suggestion | `src/subway_route_agent/tools.py:134` | `json.loads`가 내는 `RecursionError`와 긴 정수 `ValueError`는 `call_tool`이 못 잡는다. PR 본문 Notes에 이미 있다 | 기록만 |
| 18 | Suggestion | `src/subway_route_agent/answerers.py:122` | `make_llm_tools` docstring이 상한 종료를 안 적고, `:181` 주석 「llm은 첫 호출 때 client를 만든다」는 `llm-tools`도 같다. `docs/concepts.md:52,60`의 「정의한 곳」 기준(안쪽 함수 / 팩토리)이 서로 다르다 | 기록만 | <!-- style-exempt -->
| 19 | Suggestion | `tests/test_llm_tools.py:198` | 재생 테스트가 리포트 열을 `rows[qid][8]` 위치 번호로 읽고, 요청 `seen`을 모으고도 안 쓰며, 녹화한 호출 인자를 지금 `call_tool`에 넣어 보지 않는다 | 기록만 |
| 20 | Suggestion | `tests/test_cli.py:297` | 여러 답하는 쪽 API 오류 테스트가 실패한 쪽의 부분 원문(`raw-llm-tools.json`)을 안 본다. `call_tool`의 bool 인자·여분 키 분기와 지시문의 역 이름 검사(하드코딩 7개)도 얇다 | 기록만 |
| 21 | Suggestion | `src/subway_route_agent/report.py:65` | 「환승 한 번에 180초로 고정한 stub이다」의 `stub`(환승 시간 가정)이 답하는 쪽 `stub`과 같은 말이다. 비교 리포트에 두 뜻이 섞인다 | 기록만 |

## plan 대조

| plan 기준 | 코드가 만족하나 | 증거 |
| --- | --- | --- |
| `uv run subway-eval --answerer stub llm llm-tools` 하나로 세 답하는 쪽이 같은 질문 10개에 답하고 `reports/stub.md`·`llm.md`·`llm-tools.md`와 `compare.md`가 생긴다(exit 0) | 예 | `reports/` 네 파일 있음; `tests/test_cli.py::test_two_answerers_write_each_report_and_compare_with_one_row_per_question`; PR 본문 실행 1~4 모두 exit 0 |
| `reports/compare.md` 표에 질문 10개가 있고 질문마다 세 답하는 쪽의 `맞음`·`답 경로 소요 시간`·`답이 말한 시간`이 한 줄에 나온다 | 예 | `reports/compare.md` 표 행 10개, 열 11개 |
| `reports/llm-tools.md`의 `도구 호출` 열이 실제 호출 수다(질문 하나라도 0이 아닌 값) | 예 | 열 값 합 42(2+6+3+5+5+4+4+5+5+3), `compare.md` 머리의 도구 호출 42와 같음; 토큰 열 합 42871도 `compare.md`와 같음 |
| 도구는 여러 호선을 거치는 경로나 소요 시간을 돌려주지 않는다. `travel_seconds`는 한 호선 안만 준다(테스트로 고정) | 예 | 지적 #1 fix 뒤 `test_travel_seconds_does_not_use_transfer_edges`가 환승 필터를 지우면 실패함을 확인했다(시청→교대 1830·강남→시청 1740·지축→오금 3090); `grep -n shortest src/subway_route_agent/tools.py` 출력 없음 |
| 테스트는 API를 부르지 않는다. 녹화한 도구 호출 응답으로 끝까지 재생하는 테스트가 있다 | 예 | `tests/test_llm_tools.py::test_replay_recorded_tool_calls_end_to_end`; `env -u OPENAI_API_KEY uv run pytest -q` → 119 passed; `uv run ruff check .` → All checks passed |
| `uv run subway-eval`(인자 없음, stub)은 키 없이 `reports/stub.md`만 쓴다 | 예 | `tests/test_cli.py` 기본 실행 테스트(키 지움); PR 본문 Pre-PR 2 |
| 이번에 안 하는 것: `SYSTEM`·`SCHEMA`·`_parse`·`make_llm`을 바꾸지 않는다, `grade.py`·`data/questions.json` 변경 없음 | 예 | `git diff main...HEAD -- src/subway_route_agent/answerers.py`에서 지워진 줄은 리뷰 fix #2의 `stub` docstring 한 줄뿐이고 `SYSTEM`·`SCHEMA`·`_parse`·`make_llm`은 그대로다; `grade.py`·`data/questions.json`은 diff 목록에 없음 |
| 실패 징후 1 — 두 실행 모두 LLM + 도구 정답률이 같은 실행의 LLM 혼자보다 높으면 통과, 하나만 높으면 다시 잰다(네 실행 값 나란히), 같거나 낮으면 미완 | 판정 불가 | 값만 적는다: LLM 혼자 0/10 네 번, LLM + 도구 1/10·0/10·1/10·0/10 (PR 본문 표). 구간 판정은 PR 게이트에서 jw가 한다 |
| 실패 징후 4·5 — 값만 적는다 | 예 | PR 본문 실패 징후 4·5 표. 마지막 실행 값은 `reports/compare.md` 머리와 같다 |
| `docs/concepts.md` 개념 표의 정의한 곳 줄 번호가 실제 파일과 맞는다 | 예 | `find_station` `tools.py:28`, `line_stations` `:37`, `travel_seconds` `:58`, `TOOL_CALL_LIMIT` `answerers.py:111`, `TOOLS_SYSTEM` `:115`, `llm-tools` `:122`, `ANSWERERS` `:182`, `compare.md` `report.py:104`, `--answerer` `cli.py:58`를 `grep -n`으로 확인(리뷰 fix 뒤에도 줄 수 그대로) |

## 메모

- 이 세션에서 테스트를 다시 돌렸다: 리뷰 fix 뒤 `env -u OPENAI_API_KEY uv run pytest -q` → 119 passed, `uv run ruff check .` → All checks passed. 리포트·fixture는 다시 만들지 않았다(실제 API 재호출 없음)
- 리뷰 fix는 `report.py`·`answerers.py`의 docstring 한 줄·표시 조건 한 줄만 바꿨다. 커밋된 리포트(`reports/*.md`)와 PR 본문 측정값에는 영향이 없다
- 테스트 fix 3개는 코드를 일부러 깨뜨려 새 테스트가 실패하는지 확인했다: 환승 필터 삭제(#1), `line_stations`에서 1호선 종로3가 구간 삭제(#4), `truth` 조건 삭제(#5)
- 참고(결함 아님): `reports/llm-tools.md`에서 10문항 중 7문항이 `경로 끊김`이다. 중간 역을 빼고 양 끝만 쓴 경우(q1·q10)와 갈아타는 역을 두 번 쓰지 않은 경우(q2)가 많고, q10은 말한 시간이 정답과 같은데도 틀림으로 채점됐다. 구간 판정은 jw가 한다
- GitHub 게시: 요약 코멘트 1건과 `push-back`·`defer` 행(#6~#10)의 인라인 스레드를 마지막 단계에서 올렸다. 실패한 건이 있으면 아래에 적는다
