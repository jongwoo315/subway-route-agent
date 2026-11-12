# 187 리뷰 — PR #3

**대상:** `main...HEAD` — 6 commits(리뷰 fix 2 커밋은 별도, 아래 `fix` 해시), 14 files, +637 −37
**plan:** docs/plans/187-1110-plan-more-questions.md

단어장 검사: `docs/concepts.md` 용어 절의 「쓰지 말 말」을 diff의 코드·주석·docstring·문서에서 찾았고 0건이다.
리뷰는 `pr-review-toolkit`의 에이전트 4개(코드·테스트·조용한 실패·주석)와 직접 읽기로 했다. 새 타입이 없어 type-design은 건너뛰었다.

## 지적

| # | 심각도 | 위치 | 내용 | 처리 |
| --- | --- | --- | --- | --- |
| 1 | Important | `tests/test_cli.py:143` | 도착 시한 경계(`>`)가 테스트로 안 고정돼 있다. `>=`로 바뀌면 정확히 시한에 도착하는 질문이 정답 없음이 되는데 테스트가 통과한다 | fix `4000deb` |
| 2 | Important | `tests/test_grade.py:91` | 정답 없음(`truth=None`) 질문에 경로로 답하는 경우를 채점하는 단위 테스트가 없다. 이 PR로 q6·q7에서 일상이 된 경우이고 실제 호출로만 확인됐다 | fix `e1e5f2d` |
| 3 | Important | `src/subway_route_agent/cli.py:28` | 별칭 역(`총신대입구`→`이수`)은 정답 계산과 역 검사에만 적용되고 `grade()`는 질문의 원래 이름과 비교한다. 별칭 질문에서는 어떤 답도 맞을 수 없다. 지금 질문 10개에는 별칭이 없어 숨어 있다 | defer — plan이 「답 경로의 역 이름 맞춤」(#186 리뷰 #10)을 이번에 안 하는 것으로 정했다. 별칭 질문을 넣는 티켓에서 `grade.py`를 같이 고친다 |
| 4 | Important | `src/subway_route_agent/cli.py:32` | 정답 없음 질문(q6·q7)은 `correct`가 항상 거짓이라, 「길이 없다」고 옳게 답해도 틀린 답과 점수가 같다. 빈 경로는 #186 규칙으로 파싱 실패다. 정답률 최대가 8/10이다 | defer — 정답 없음 질문을 맞게 채점하는 규칙은 새 정답 기준이 필요하고, plan이 LLM 쪽·빈 경로 규칙 수정을 안 하는 것으로 정했다. 이번 실행은 q6·q7에도 경로로 답해 파싱 실패 0이다 |
| 5 | Important | `docs/concepts.md:17` | 용어 `직접 계산한 값`을 「정답 소요 시간」이라 정의하는데, q6은 정답이 없는데도 `hand_seconds`(900)가 있다. 정의가 q6을 빠뜨린다 | defer — `## 용어` 절은 Kickoff에서 main이 쓴 것이고 plan이 고치지 않는다고 못박았다. 고칠 말은 「CSV 구간 소요시간을 직접 더해 구한 최단 소요 시간. 시한 때문에 정답 없음인 질문(q6)에도 있다」다. jw가 게이트에서 정한다 |
| 6 | Suggestion | `src/subway_route_agent/cli.py:35` | 도착 시한 판정(`출발 + 소요 > 시한`)이 `truth_for`와 `grade.py:49`에 두 벌이고, `grade.py`의 비공개 `_minutes`를 가져온다. 한쪽만 바뀌면 정답 없음 판정과 `시한 초과`가 갈린다 | 기록만 |
| 7 | Suggestion | `src/subway_route_agent/cli.py:36` | `_minutes`가 자정을 넘는 시한(`23:50`→`00:20`)을 모른다. 이런 질문을 더하면 정답 없음이 된다. 지금 10개에는 없다 | 기록만 |
| 8 | Suggestion | `src/subway_route_agent/cli.py:74` | `hand_checked`는 `hand_seconds` 키가 있는지만 본다. 리포트의 「직접 계산으로 확인한 정답」은 값이 맞는지 실행 때 안 보고 테스트(`tests/test_route.py`)에 기댄다. 테스트 없이 리포트만 다시 만들면 값이 어긋나도 8/8이다 | 기록만 |
| 9 | Suggestion | `tests/test_route.py:17` | `JUNCTIONS`는 `graph.BRANCH_HEADS`와 값이 같은 사본이다. 지선 분기역이 잘못 적혀 있으면 직접 계산과 다익스트라가 같이 틀리고 테스트가 통과한다. 이 표를 타는 질문은 q3(둔촌동)·q10(도림천)이다. 주석의 「직접 계산은 그래프 코드와 따로다」는 `TRANSFER_SECONDS`를 graph에서 가져오는 점에서 조금 강하다 | 기록만 |
| 10 | Suggestion | `tests/test_cli.py:111` | 역 검사가 답하는 쪽을 부르기 전에 멈추는지는 테스트가 안 본다(exit 2와 리포트 없음만 본다). 검사가 루프 뒤로 밀려도 stub은 공짜라 통과한다. 실제 `llm`에서는 호출 비용이 먼저 든다 | 기록만 |
| 11 | Suggestion | `tests/test_cli.py:120` | 별칭 테스트는 출발역만, 정답 계산만 본다. 도착역에서 `_graph_name`이 빠지거나 별칭 질문을 채점하는 경우는 안 잡는다(#3과 이어진다) | 기록만 |
| 12 | Suggestion | `docs/concepts.md:37` | `hand_note` 행이 「`hand_path`가 없는 질문에서는 정답이 없는 이유」라 하지만 q6은 `hand_path`가 있으면서 `hand_note`가 정답 없음 이유도 설명한다. 「정답이 없는 질문(q6, q7)에서는 그 이유다」가 맞다 | 기록만 |
| 13 | Suggestion | `tests/test_cli.py:135` | 테스트 안 질문 id `q7`은 정답이 있는데 실제 `questions.json`의 q7은 정답 없음이라 헷갈린다. `missed`·`kept` 같은 이름이 낫다 | 기록만 |
| 14 | Suggestion | `tests/test_route.py:52` | `HAND_CHECKED`가 비면 parametrize가 조용히 건너뛴다. `assert HAND_CHECKED` 한 줄이 없다. `tests/test_llm.py`의 `use_recorded_questions`도 id가 없으면 조용히 줄어든다 | 기록만 |
| 15 | Suggestion | `src/subway_route_agent/cli.py:71` | `--raw` 파일을 `APIError` 때 일부만 담아 덮어쓴다(예: q1에서 실패하면 `{}`). 기존 완전한 파일이 사라진다. 이 줄은 #186에서 들어온 것이고 이 PR 변경이 아니다 | 기록만 |

## plan 대조

| plan 기준 | 코드가 만족하나 | 증거 |
| --- | --- | --- |
| `data/questions.json`에 질문이 10개 있다 | 예 | `tests/test_answerers.py` `test_questions_file_has_ten_questions_with_fields` |
| 정답이 있는 질문은 전부 `hand_path`·`hand_seconds`가 있고, 테스트가 그래프 없이 CSV 행을 더해 `shortest()`와 맞춘다 | 예 | `tests/test_route.py:55-61`, 정답 있는 8개 모두 `hand_seconds` 있음 |
| `subway-eval`(stub)과 `--answerer llm`이 10개 질문으로 끝까지 실행된다(exit 0) | 예 | 테스트 `test_main_runs_end_to_end`, PR 본문 Pre-PR 2번 exit 0 |
| 리포트 머리에 `- 직접 계산으로 확인한 정답: K/M` | 예 | `reports/stub.md:7`, `reports/llm.md:7` 모두 `8/8` |
| 출발·도착역이 그래프에 없으면 실행 전에 exit 2 | 예 | `tests/test_cli.py` `test_station_missing_from_graph_stops_before_running` |
| 최단 경로로도 도착 시한을 못 맞추면 정답 없음 | 예 | `src/subway_route_agent/cli.py:32-38`, `test_deadline_that_even_shortest_route_misses_has_no_truth`, 경계는 fix `4000deb` |
| `answerers.py`를 고치지 않았다 | 예 | `git diff main...HEAD -- src/subway_route_agent/answerers.py` 출력 0줄 |
| `hand_seconds`를 다익스트라 출력에 맞춰 고치지 않았다 | 판정 불가 | 값만 적는다: q2의 처음 손 경로(1호선 시청 환승 1,530초)가 90초 느려 `hand_note`에 적고 경로를 바꿨다고 PR 본문과 `hand_note`가 말한다. 커밋 이력에서 그 순서는 확인하지 못했다 |
| jw 기준: 파싱 실패 없고 llm이 답을 내놓는다 | 판정 불가 | 값만 적는다: `runs/187/raw-1.json` 기준 파싱 실패 0/10, `답 있음` O 10개, 토큰 합 4,334가 `reports/llm.md`와 같다. 판정은 jw가 한다 |

## 읽는 법 (코드 결함 아님)

- `reports/llm.md` 10행이 모두 「경로 끊김」이다. `raw-1.json` 기준 q2는 LLM이 1호선 종로3가에서 2호선 을지로3가로 바로 건너뛴 것이고, q7의 「지어낸 역 42」는 `삼각지역`처럼 이름 끝에 「역」을 붙인 것이 대부분이다. 역 이름 맞춤은 plan이 이번에 안 하는 것으로 뺐다(#186 리뷰 #10)
- 재실행: `env -u OPENAI_API_KEY uv run pytest -q` 70 passed, `uv run ruff check .` All checks passed (fix 커밋 둘 뒤)
