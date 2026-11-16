# 223 리뷰 — PR #8

**대상:** `main...HEAD` — 7 commits, 17 files, +665 −102
**plan:** docs/plans/223-1116-plan-accuracy-up.md

단어장 검사: `docs/concepts.md` 용어 절의 「쓰지 말 말」을 diff에서 찾았다. 걸린 곳이 없다(`표준편차`는 `편차`와 다른 말, `정답 없음`은 `답 없음`을 포함할 뿐이다).

## 지적

| # | 심각도 | 위치 | 내용 | 처리 |
| --- | --- | --- | --- | --- |
| 1 | Suggestion | `/Users/jw/prv/.wt/223-accuracy-up/reports/compare.md:42` | plan 통과 기준은 `llm-tools-search` 대 `llm-tools` 줄을 말하는데 리포트 줄은 `llm-tools 대 llm-tools-search`이고 d 부호가 반대(-5.40)다. 줄 순서는 plan Task 3(첫 번째 대 두 번째)과 맞고 PR 본문이 부호를 밝혔다 | 기록만 |
| 2 | Suggestion | `/Users/jw/prv/.wt/223-accuracy-up/src/subway_route_agent/report.py:119` | `TOOL_CONFIGS`가 `cli.py`의 `TOOL_SETS`와 같은 매핑이라 새 구성을 더할 때 두 곳을 고쳐야 한다 | 기록만 |
| 3 | Suggestion | `/Users/jw/prv/.wt/223-accuracy-up/src/subway_route_agent/tools.py:229` | `SEARCH_TOOLS`가 `FINE_TOOLS[0]`을 위치로 가리킨다. 순서가 바뀌면 조용히 틀리지만 `test_search_tools_schema_is_strict_with_nullable_cap`이 이름 순서를 검사한다 | 기록만 |
| 4 | Suggestion | `/Users/jw/prv/.wt/223-accuracy-up/src/subway_route_agent/tools.py:274` | `max_transfers`에 음수 정수를 받아 `no_route`로 답한다(진짜 길 없음과 구분이 안 된다). 두 역이 모두 없으면 첫 오류만 돌려준다. 이번 측정에서 나온 적이 없다 | 기록만 |
| 5 | Suggestion | `/Users/jw/prv/.wt/223-accuracy-up/src/subway_route_agent/answerers.py:40` | 공통 `SYSTEM`에 더한 시한 문장은 q6을 세 구성 모두 0/5로 두었다(효과 없음). 조건이 바뀌는 비용만 남았지만 plan이 정한 일이고 PR 본문 실패 징후 4가 값을 적었다 | 기록만 |
| 6 | Important | `/Users/jw/prv/.wt/223-accuracy-up/src/subway_route_agent/answerers.py:129` | 주석 「두 도구 구성의 지시문은 도구 안내 한 문장만 다르다」가 경로 탐색 도구 구성(셋째)을 빠뜨려 거짓처럼 읽힌다 | fix `a2bb16d` |
| 7 | Important | `/Users/jw/prv/.wt/223-accuracy-up/tests/test_tools.py:304` | `call_tool`이 `max_transfers`를 빠뜨린 호출을 거절하는 것과 도착역 별칭(`dest`에 `총신대입구`)이 테스트에 없다. 별칭 처리를 `origin`에서만 해도 통과한다 | fix `027ef80` |
| 8 | Important | `/Users/jw/prv/.wt/223-accuracy-up/tests/test_cli.py:709` | `llm-tools-search` 리포트의 「도구: find_station, shortest_route (호출 상한 25)」 줄을 확인하는 테스트가 없다(`_notes`는 레지스트리 멤버십만 검사됨) | fix `79b7a99` |
| 9 | Important | `/Users/jw/prv/.wt/223-accuracy-up/tests/test_cli.py:76` | 비교 리포트의 검색 전용 줄(`SEARCH_DIFF`)이 검색이 없는 실행에 새지 않는다는 검사, 검색 하나만 돌렸을 때 도구 구성 비교 줄이 없다는 검사가 없다. #8과 한 커밋에 묶었다 | fix `79b7a99` |
| 10 | Suggestion | `/Users/jw/prv/.wt/223-accuracy-up/tests/test_llm_tools.py:160` | 「질문별 힌트가 없다」 검사가 테스트 파일 안 상수 `DEADLINE_SENTENCE`를 보므로 코드가 바뀌어도 실패하지 않는다. 같은 파일 위 줄이 `SYSTEM`이 이 문장으로 끝나는지 따로 본다 | 기록만 |
| 11 | Suggestion | `/Users/jw/prv/.wt/223-accuracy-up/tests/test_tools.py:241` | `shortest(` 부분 문자열 검사는 별칭 import나 helper를 거친 호출을 못 잡는다. 이전 파일 전체 검사보다 약하다 | 기록만 |
| 12 | Suggestion | `/Users/jw/prv/.wt/223-accuracy-up/tests/test_cli.py:52` | 세 답하는 쪽 테스트가 d와 `|d| ≥ e`를 한 짝·한 지표에서만 확인하고 `아니오` 분기와 머리 줄 「앞 이름 평균 − 뒤 이름 평균」은 확인하지 않는다 | 기록만 |
| 13 | Suggestion | `/Users/jw/prv/.wt/223-accuracy-up/src/subway_route_agent/report.py:233` | `llm`과 `llm-tools-search`만 돌리면 검색 지시문이 `SYSTEM` 위에 도구 안내 두 문장을 더 가진다는 줄이 리포트에 없다 | 기록만 |
| 14 | Suggestion | `/Users/jw/prv/.wt/223-accuracy-up/src/subway_route_agent/report.py:240` | 도구 구성 머리 줄의 「도구 안내 문장이 구성마다 다르다」는 검색 구성이 「경로는 직접 고른다」를 뺀 것까지 말하지 않는다. 바로 윗줄 `SEARCH_DIFF`가 말한다 | 기록만 |
| 15 | Suggestion | `/Users/jw/prv/.wt/223-accuracy-up/src/subway_route_agent/answerers.py:40` | 공통 `SYSTEM` 시한 문장이 `llm`·`llm-tools`·`llm-tools-coarse`의 조건을 바꾸는데 `COMPARE_DIFF`는 도구 지시문 차이만 말한다. 이전 PR과 비교 불가라는 사실은 PR 본문 `## 착수 전 기준`에 있다 | 기록만 |

## plan 대조

| plan 기준 | 코드가 만족하나 | 증거 |
| --- | --- | --- |
| 실제 키로 비교 리포트 `reports/compare.md`가 있고 회차별 지표 표에 세 구성 × 5회차 × 지표 빈칸이 없다 | 예 | `reports/compare.md:16-35` 표 18행 + 범위 3행, 빈칸 없음 |
| `llm-tools-search`의 회차별 맞힌 질문 수와 평균이 PR 본문 맨 위에 있다 | 예 | PR 본문 `## 착수 전 기준 (jw)`: 9, 9, 9, 9, 9 → 9.0. `runs/223/raw-*`를 PR 본문 집계 스크립트로 다시 세어 같은 값(`[9,9,9,9,9]`) |
| 평균 차이 줄에 `llm-tools-search` 대 `llm-tools` 줄이 있다 | 아니오 | 줄은 `llm-tools 대 llm-tools-search`(`reports/compare.md:42`)다. 이름 순서가 반대이고 d = -5.40. PR 본문이 부호를 밝혔다 |
| 테스트는 API·네트워크를 부르지 않는다 | 예 | `env -u OPENAI_API_KEY uv run pytest -q` → 231 passed, `uv run ruff check .` → All checks passed |
| 실패 징후 1: 5회차 평균 8.0 이상이고 `llm-tools` 대비 `d ≥ e` | 판정하지 않음 | 평균 9.00, 같은 실행 `llm-tools` 3.60, 크기 5.40 대 e = 0.49. 구간 판정은 jw 몫 |
| 실패 징후 2: 틀린 답 원인을 질문 수로 PR 본문에 적는다 | 예 | PR 본문 표 5건(파싱 1, 시한 비교 4). raw를 다시 세어 같은 값 |
| 실패 징후 3: 질문당 도구 호출 1.0 미만 회차 | 나타나지 않음 | `[1.6, 1.6, 1.4, 1.7, 1.8]` |
| 실패 징후 4: 다른 구성의 q6 값을 PR 본문에 적는다 | 예 | `llm-tools` 0/5, `llm-tools-coarse` 0/5 |
| 바꾸지 않을 것(`grade.py`·`route.py`·`graph.py`·`data.py`·`data/`·`tests/fixtures/`) | 예 | `git diff main...HEAD -- <그 경로들>` 출력 0줄 |
| `SCHEMA`·`_parse` 변경 없음 | 예 | `answerers.py` diff는 import·`SYSTEM`·`SEARCH_SYSTEM`·등록뿐 |
| `docs/concepts.md` 개념 표 줄 번호 | 예 | 변경된 행의 `path:line`을 파일에서 열어 대조, 전부 맞음 |
| 용어 절은 고치지 않는다 | 예 | 용어 절 변경은 `cad54b9`(main GATE 1) 하나뿐 |

실행: fix 커밋 3개 뒤 `env -u OPENAI_API_KEY uv run pytest -q` → 234 passed, `uv run ruff check .` → All checks passed. 리뷰 에이전트 셋(코드·테스트·조용한 실패+주석)의 결과를 위 표에 옮겼다. 인라인 스레드를 달 `push-back`·`defer`·`won't-fix` 행은 없다.
