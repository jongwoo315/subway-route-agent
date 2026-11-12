# 193 리뷰 — PR #5

**대상:** `main...HEAD` — 12 commits(리뷰 fix 5개 포함), 21 files, +840 −106
**plan:** docs/plans/193-1111-plan-grading.md

리뷰는 `pr-review-toolkit` 에이전트 4개(code-reviewer · pr-test-analyzer · silent-failure-hunter · comment-analyzer)로 했다. type-design-analyzer는 새 타입이 `Answer.tool_log` 필드 하나뿐이라 돌리지 않았다.
단어장 검사는 `docs/concepts.md` `## 용어`의 「쓰지 말 말」 칸을 diff에서 찾았다. 걸린 곳은 없다(아래 11·12번은 다른 개념이라 기록만 한다).

## 지적

| # | 심각도 | 위치 | 내용 | 처리 |
| --- | --- | --- | --- | --- |
| 1 | Important | `src/subway_route_agent/report.py:98` | 비교 리포트의 `답 경로 소요 시간`이 채우기 전 경로로 재서, 맞음(O)인 답이 `끊김`으로 나왔다(`reports/compare.md` q1 llm-tools: 맞음 O · 채운 역 16 · 끊김). 채점과 같은 `fill_path` 경로로 재도록 고치고, `runs/193/raw-2-*.json`에서 옛 셀이 리포트와 일치함을 확인한 뒤 `reports/compare.md` 셀을 새 값으로 바꿨다 | fix `626d777` |
| 2 | Important | `tests/test_regrade_188.py:64` | `unchanged > 0`만 봐서 파싱이 조용히 비어도 통과한다. 원문 파일별 질문 수(10)와 지나는 역을 다 쓴 답 수(7, 2)를 박았다 | fix `8441a25` |
| 3 | Important | `tests/test_grade.py:169` | 채운 경로로 환승 상한·도착 시한을 재는지 검사가 없었다. 규칙 2가 넣은 환승 1회가 상한 0을 넘는 사례와 채운 소요 시간 24분이 시한을 넘는 사례를 더했다 | fix `e2b8766` `255ce13`(방금 더한 주석이 ruff 100자를 넘어 줄을 나눈 것) | <!-- style-exempt -->
| 4 | Important | `tests/test_llm_tools.py:92` | `tool_log`가 한도 도달 경로에서만 검사됐다. 최종 답을 못 읽거나 응답이 끝나지 않은 경로에서도 남는지 더했다 | fix `a7e5eda` |
| 5 | Important | `src/subway_route_agent/grade.py:66` | 채울 수 없는 이유(데이터에 없는 노드 · 같은 노드 반복 · 규칙으로 못 잇는 구간)가 모두 `경로 끊김`과 채운 역 0으로 합쳐진다. 리포트에서 「채점이 못 채움」과 「답이 깨짐」을 못 가른다 | defer — plan이 못 채우는 경우를 `경로 끊김` 하나로 정했다(통과 기준·`## 개념` 표). 이유 구분이 필요하면 후속 티켓에서 조건 어김 값을 늘린다 |
| 6 | Important | `src/subway_route_agent/grade.py:70` | 규칙 2는 「앞 호선으로 갈아타는 역까지 가서 갈아탄다」 한 방향이다. `서울역(4) → 동대문역사문화공원(4) → 잠실(2)`처럼 새 호선에서 먼저 갈아타고 건너뛴 답, 교대(2) → 양재(3)처럼 새 호선에서 역을 건너뛴 답은 `경로 끊김`이다 | push-back — plan이 「채우는 규칙은 설계 문서의 규칙 1·규칙 2 둘뿐」이라고 못박았고 이 밖은 `이번에 안 하는 것`이다. 이 사례가 #188 원문 틀린 답의 원인이면 게이트에서 본다 |
| 7 | Important | `tests/test_regrade_188.py:48` | 채운 답(`filled > 0`)에 대한 느슨한 `invariant` 검사가 없다(예: 조건 어김이 비어 있어야 한다) | push-back — plan이 「차이를 테스트로 박지 말고 표로만 적는다. 참고 값도 main이 쓴 것이라 정답이 아니다」라고 했다 |
| 8 | Suggestion | `src/subway_route_agent/grade.py:72` | 규칙 2가 `via → b` 환승 간선이 있는지 확인하지 않는다 | 기록만 — `build_graph`가 한 역의 모든 노드를 서로 잇는다는 걸 코드 리뷰어가 실행으로 확인했다. 지금 그래프에서는 일어나지 않는다 |
| 9 | Suggestion | `src/subway_route_agent/grade.py:108` | `지어낸 소요 시간`이 채운 경로의 시간과 비교한다. 순환선에서 긴 쪽을 가고 그 시간을 맞게 말한 답이 `지어낸 소요 시간`으로 잡힌다 | defer — 순환선 방향 문제는 설계 문서 `## 열린 질문`에 있다. 실행하지 않은 사례라 후속에서 먼저 재현한다 |
| 10 | Suggestion | `src/subway_route_agent/answerers.py:158` | `output[:200]`이 잘렸다는 표시가 없다. `line_stations` 결과는 200자를 넘어 로그에서 JSON이 깨진다 | defer — plan이 「결과 앞 200자」로 정했다. 잘림 표시는 `--raw` 형식 변경이라 후속에서 다룬다 |
| 11 | Suggestion | `src/subway_route_agent/cli.py:25` | 질문 도중 API 오류가 나면 그 질문의 `tool_log`가 raw 파일에 없고 실패 표시도 없다 | defer — 이번 변경이 만든 문제가 아니라 `--raw`가 원래 끝난 질문만 쓴다. 후속에서 다룬다 |
| 12 | Suggestion | `src/subway_route_agent/grade.py:54` | `fill_path` docstring에 「갈아타는 역을 한 번 더 쓴 노드도 채운 역 1」과 「같은 노드 반복은 None」이 없다 | 기록만 |
| 13 | Suggestion | `docs/concepts.md:48` | `경로 끊김`의 못 채우는 이유 목록에 같은 노드 반복이 빠졌다 | 기록만 |
| 14 | Suggestion | `tests/test_regrade_188.py:26` | 주석 「실패·빈 경로는 답 없음」의 `답 없음`은 용어 절에서 `정답 없음`의 쓰지 말 말이다. 여기서는 답이 빈 것이라 다른 개념이지만 겹쳐 읽힌다 | 기록만 |
| 15 | Suggestion | `docs/plans/193-1111-plan-grading.md:61` | 「기대값이 표에 있다」의 `기대값`이 `손 계산 값`의 쓰지 말 말과 같은 글자다. 테스트 기대 결과를 뜻해 개념이 다르다 | 기록만 |
| 16 | Suggestion | `tests/test_grade.py:131` | 순환선 반대 방향, 6호선 한 방향, 규칙 2 중 앞 호선이 `via`에 못 닿는 경우, `tool_log` 200자 이하 경계, 머리 줄의 「맞음이고 채운 역 > 0」 반대편 검사가 없다 | 기록만 |
| 17 | Suggestion | `src/subway_route_agent/answerers.py:124` | `make_llm_tools` docstring이 도구 호출 상한(25)을 빠뜨렸다. 이번 diff가 바꾼 줄이 아니다 | 기록만 | <!-- style-exempt -->
| 18 | Suggestion | `tests/fixtures/gate188/` | Done criteria의 「diff가 비었다」를 글자 그대로 읽으면 `main...HEAD`에 fixture가 있어 어긋난다. 킥오프 커밋 `7e6af91`이 더한 것이고 그 뒤 바뀐 줄은 없다 | 기록만 |

## plan 대조

| plan 기준 | 코드가 만족하나 | 증거 |
| --- | --- | --- |
| 채점이 답 경로의 빠진 중간 역을 채운 뒤 판정한다. 채우는 규칙은 규칙 1·규칙 2 둘뿐이다 | 예 | `src/subway_route_agent/grade.py:53`(`fill_path`)·`grade.py:92` |
| Task 1의 손으로 만든 사례가 전부 기대대로 판정된다 | 예 | `tests/test_grade.py:116`(`HAND_CASES` A·B·C·D·F·G) + 사례 E `test_hand_case_E_full_path_is_unchanged` |
| 지나는 역을 다 쓴 답(채운 역 0)은 판정이 #188과 같다 | 예 | `tests/test_regrade_188.py:64` — 원문 파일마다 질문 10개, 다 쓴 답 7개·2개가 옛 판정과 같다 |
| 리포트·비교 리포트에 `채운 역` 열, 비교 리포트 머리에 「채우지 않고도 맞은 질문 수」 | 예 | `src/subway_route_agent/report.py:10`·`report.py:125`, `tests/test_cli.py:384` |
| `--raw`에 LLM + 도구의 질문별 도구 호출 기록이 남는다 | 예 | `src/subway_route_agent/cli.py:25`, `tests/test_llm_tools.py:194` 근처 재생 테스트가 `saved[qid]["tool_log"]` 길이 = `tool_calls`를 본다 |
| 테스트는 API를 부르지 않는다 | 예 | `env -u OPENAI_API_KEY uv run pytest -q` → 140 passed, `uv run ruff check .` → All checks passed |
| LLM 쪽을 고치지 않았다(`SYSTEM`·`TOOLS_SYSTEM`·`SCHEMA`·`_parse`·`make_llm` 줄, `tools.py`, `data/questions.json`, `tests/fixtures/gate188/`) | 예 | `answerers.py` diff에 그 줄이 없다. 나머지 세 곳은 킥오프 커밋 `7e6af91` 뒤로 바뀐 줄이 없다(`git log main..HEAD -- <경로>`) |
| 실패 징후 1 ②: #188 main 실행 원문을 새 채점으로 다시 채점해 참고 값(LLM + 도구 5/10, LLM 혼자 0/10)과 맞춘다 | 판정 불가 | 이 세션은 판정하지 않는다. 다시 채점한 값은 PR 본문 표(질문 · 원문 경로 · 채운 역 · 새 판정 · 참고 값)에서 사람이 본다 |
| 실패 징후 2~4(너무 너그러운지 · 실제 키 두 번 측정 · 도구 호출 기록) | 판정 불가 | 값만 PR 본문과 `reports/compare.md`에 있다. 임계값이 없는 항목은 판정하지 않는다 |

## 마지막

- fix 5개(`626d777` `8441a25` `e2b8766` `255ce13` `a7e5eda`)를 push한 뒤 요약 코멘트 1건과 인라인 스레드(defer · push-back 행 5·6·7·9·10·11)를 올렸다.
- `reports/compare.md`의 `답 경로 소요 시간` 셀 12개를 `runs/193/raw-2-*.json` 원문으로 새로 계산한 값으로 바꿨다. API를 다시 부르지 않았다. 옛 셀이 raw-2에서 계산한 값과 20개 모두 일치함을 먼저 확인했다. 다음 실제 실행이 같은 값을 쓴다.
- 인라인 스레드 한 건이 실패했다: 9번(`src/subway_route_agent/grade.py:108`)은 이 줄이 PR diff 밖이라 GitHub이 422(`could not be resolved`)를 냈다. 처리 칸의 이유가 그 스레드의 내용이다.
