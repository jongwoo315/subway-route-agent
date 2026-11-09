# #185 리뷰 — PR #1

**대상:** `main...HEAD` — 14 commits(리뷰 전 구현 10 + 리뷰 fix 4), 24 files, +1682 −0
**plan:** docs/plans/185-1109-plan-skeleton.md

단어장: `docs/concepts.md` 용어 절의 「쓰지 말 말」(에이전트·솔버·기준 경로·레퍼런스·환각 역·제약 위반)을 코드·주석·docstring·README·리포트에서 찾았고 나온 곳이 없다.

## 지적

| # | 심각도 | 위치 | 내용 | 처리 |
| --- | --- | --- | --- | --- |
| 1 | Important | `src/subway_route_agent/graph.py:28` | 6호선 응암순환은 한 방향으로만 달리는데 간선을 양쪽으로 만들어서, 역촌→구산이 실제로 탈 수 없는 220초 경로(역촌→응암→구산)로 나온다. 실제 경로는 370초다 | fix `05d8818` |
| 2 | Important | `tests/test_graph.py:29` | 연결만 보는 테스트라 `BRANCH_HEADS`의 용답·도림천 항목이나 `ALIASES`를 비워도 통과한다(조용한 불일치) | fix `6d64dfd` — 실제 그래프에서 용답·도림천·이수 이웃과 시간을 고정하는 테스트를 더했다. 코드 쪽 assert는 넣지 않았다 |
| 3 | Important | `tests/test_route.py:39` | 2호선 시청, 6호선 응암처럼 같은 역이 두 번 나와서 고리가 닫히는 경우를 확인하는 테스트가 없다 | fix `0b01fcc` |
| 4 | Important | `tests/test_cli.py:8` | 리포트를 답이 전부 빈 stub으로만 그려서, 정답률 계산이나 맞음·답 있음 표시가 고장 나도 통과한다 | fix `3ed20e2` |
| 5 | Important | `reports/skeleton.md:1` | `subway-eval`을 다시 돌리면 이 파일을 통째로 덮어써서 손으로 적은 `## jw 기준 측정` 절(18줄)이 사라지고, 깨끗한 clone에서 실행하면 작업 트리가 더러워진다 | defer — plan Done criteria가 그 절을 이 파일 아래에 두라고 했다. 위치를 옮길지(별도 파일 또는 PR 본문만)는 jw가 정할 일이다 |
| 6 | Important | `src/subway_route_agent/cli.py:28` | questions.json의 출발·도착역이 그래프에 없으면 정답 없음(`None`)으로 처리되어 틀린 답처럼 보인다 | push-back — 질문 파일이 3개로 고정이고 `tests/test_cli.py:16`이 3개 모두 정답이 채워졌는지 확인한다. 질문을 늘리는 티켓에서 검증을 넣는다 |
| 7 | Important | `src/subway_route_agent/grade.py:57` | 답이 말한 시간이 틀려도(`지어낸 소요 시간 1`) 경로가 맞으면 `맞음`이다 | push-back — 설계 문서 §설계 결정 「정답 판정」이 실제 소요 시간만 정답과 비교하기로 정했고, `tests/test_grade.py:44`가 그 동작을 명시한다. 말한 시간은 `지어낸 소요 시간` 열에서 따로 센다 |
| 8 | Important | `src/subway_route_agent/grade.py:49` | 정답(`shortest`)이 도착 시한을 보지 않아서 시한을 못 맞추는 질문이면 정답 경로가 시한 초과로 나온다. 출발 시각과 도착 시한 중 하나만 있으면 시한을 조용히 무시한다. 정답이 없는(`truth=None`) 경로를 다루는 테스트도 없다 | defer — q1~q3 중 이 경우에 걸리는 질문이 없다. 시한이 빡빡한 질문이나 도달 불가 질문을 더하는 티켓에서 같이 정한다 |
| 9 | Important | `src/subway_route_agent/answerers.py:7` | JSON에서 온 답의 경로가 `["강남", 2, "x"]`이거나 시간이 문자열이면 `grade()`가 `ValueError`·`TypeError`로 죽어 실행 전체가 멈춘다. 별칭(`총신대입구`)을 쓴 답도 지어낸 역으로 센다 | defer — stub은 항상 빈 답이다. LLM 답을 `Answer`로 바꾸는 다음 티켓의 answerer가 파싱하고 검증한다 |
| 10 | Important | `tests/test_route.py:34` | q2·q3는 환승 수와 지나는 역만 확인하고 소요 시간을 고정하지 않아서 지선 간선 시간이나 환승 비용이 틀어져도 통과한다 | defer — 손으로 계산한 값이 q1(1,740초) 하나뿐이다. 구현 출력(24분 0초, 66분 40초)을 기대값으로 쓰면 같은 구현끼리 맞춰 보는 셈이라, 손으로 계산한 뒤에 고정한다 |
| 11 | Suggestion | `src/subway_route_agent/grade.py:50` | 시한 검사가 `>`라서 정확히 09:00에 도착해도 통과한다. q1 문장은 「9시 전에」다 | 기록만 — 설계 문서가 「출발 시각 + 소요 시간 ≤ 시한」으로 정했다 |
| 12 | Suggestion | `src/subway_route_agent/grade.py:52` | 경로가 끊겼거나 답이 비어 있으면 지어낸 소요 시간이 0으로 센다. 가짜 역과 가짜 시간을 같이 말해도 열은 0이다. 허용 오차 60초도 상수가 아니다 | 기록만 — 다음 티켓에서 LLM 답을 처음 채점할 때 정한다 |
| 13 | Suggestion | `src/subway_route_agent/graph.py:28` | `r.seconds > 0`을 「노선 첫 행」 대신 쓴다. CSV 중간에 `00:00` 행이나 음수가 들어와도 오류 없이 간선만 빠진다. 같은 역이 두 번 나오는 것(시청·응암) 말고 다른 중복도 걸러내지 않는다 | 기록만 — 현재 CSV에는 해당 행이 없다. 데이터를 다시 받을 때 검증을 넣는다 |
| 14 | Suggestion | `src/subway_route_agent/data.py:16` | `parse_mmss`에 범위 검사가 없고(`02:75` → 195초), 잘못된 행의 오류에 행 번호가 없고, 파일이 잘려도 알 수 없다 | 기록만 |
| 15 | Suggestion | `src/subway_route_agent/cli.py:27` | 답하는 쪽이 예외를 내면 앞 질문의 결과까지 잃고 리포트가 안 써진다. 질문 파일이 비어도 exit 0이다 | 기록만 — stub은 예외를 내지 않는다. LLM 연결 티켓에서 다룬다 |
| 16 | Suggestion | `src/subway_route_agent/report.py:55` | 데이터 줄이 「1~8호선, 2024-08-10 기준」으로 고정이고, 1·3·4·7호선의 코레일 구간이 없다는 설명이 리포트에 없다(README에는 있다) | 기록만 |
| 17 | Suggestion | `src/subway_route_agent/grade.py:58` | `invented_stations`는 역 이름만 센다. 실제 역이어도 호선이 틀린 노드(`("강남", 1)`)는 지어낸 역 0, 경로 끊김으로 나온다 | 기록만 — 현재 동작을 바꿀지는 LLM 답을 보고 정한다 |
| 18 | Suggestion | `README.md:6` | 「다익스트라가 계산한 최단 경로와 그대로 비교한다」는 실제와 다르다. 코드는 경로가 아니라 소요 시간과 조건을 비교한다 | 기록만 |
| 19 | Suggestion | `docs/concepts.md:10` | `정답` 뜻이 환승 상한을 말하지 않는다. 코드는 질문의 환승 상한 안에서 구한 최단 경로다. `경로 끊김`(`:30`) 뜻도 노드가 그래프에 없는 경우를 안 말한다 | 기록만 | <!-- style-exempt -->
| 20 | Suggestion | `src/subway_route_agent/grade.py:57` | 정답이 없을 때는 어떤 답도 맞을 수 없어서 「경로가 없다」고 답한 경우를 맞게 채점할 수 없다 | 기록만 — 8번과 같이 정한다 |
| 21 | Suggestion | `tests/test_grade.py:63` | 시한 경계(정확히 같은 시각)와 `arrive_by`만 있는 경우, 리스트 모양(JSON) 경로를 넘기는 경우의 테스트가 없다 | 기록만 |
| 22 | Suggestion | `tests/test_data.py:13` | CSV는 행 수와 한 행만 확인한다. 헤더·BOM·빈 시간 칸 같은 경우는 데이터를 다시 만들 때만 문제가 된다 | 기록만 |

## plan 대조

| plan 기준 | 코드가 만족하나 | 증거 |
| --- | --- | --- |
| 깨끗한 clone에서 `uv run subway-eval` 하나로 데이터 읽기 → 그래프 → 질문 3개 → 다익스트라 정답 → stub 답 → 채점 → 리포트가 끝까지 돈다 | 예 | 리뷰 fix 뒤 HEAD를 새로 clone해서 `uv run subway-eval` 하나만 실행: exit 0, `reports/skeleton.md` 생성 | <!-- style-exempt -->
| 리포트에 질문 3개 행이 있고, 행마다 정답 경로와 정답 소요 시간이 채워져 있다 | 예 | 같은 clone의 리포트에 q1·q2·q3 행 3개, 정답 경로·정답 시간 모두 채워짐(29분 0초 · 24분 0초 · 66분 40초) |
| 정답률 0/3(0%)이 정상이다. stub을 채워 점수를 올리지 않는다 | 예 | 같은 clone의 리포트 `정답률 0/3 (0%)`, `src/subway_route_agent/answerers.py:12-17`은 빈 `Answer()`만 돌려준다 |
| q1 정답 소요 시간이 손으로 계산한 값 1,740초(29분), 환승 0회와 같다 | 예 | `tests/test_route.py:24` 통과, 리포트 q1 29분 0초 |
| 실패 징후 2: `('서울역', 1)`에서 닿지 않는 노드가 1개 이상이면 틀림 | 예 | `tests/test_graph.py:37` 통과(응암 단방향 fix 뒤에도 전부 닿는다), 노드 277개 |
| 실패 징후 3: q3 정답 경로에 `('상일동', 5)`가 있거나 `('둔촌동', 5)`가 없으면 틀림 | 예 | `tests/test_route.py:29` 통과 |
| 실패 징후 4: stub인데 정답률이 0/3이 아니면 채점이 틀림 | 예 | 리포트 0/3, 답이 있는 행을 그리는 경로는 `tests/test_cli.py`의 `test_render_counts_correct_and_answered_rows`로 확인 |
| 이번에 안 하는 것: LLM 연결, 도구 비교, 실시간 시각표, 실제 환승 시간, 1~8호선 밖 노선, 매번 다시 받기 | 예 | `answerers.py`에 `stub` 하나(`ANSWERERS`), 환승은 `TRANSFER_SECONDS = 180`(`graph.py`), 네트워크 호출 없음 |
| jw 기준: 명령 하나로 전체 프로젝트가 처음부터 끝까지 잘 돈다 | 판정 불가 | 위 첫 두 행의 값만 적는다 — clone에서 명령 1개, exit 0, 리포트 생성, 질문 3개 정답 채워짐. 「잘 돈다」의 판정은 jw 몫이다 | <!-- style-exempt -->

## 검증

- 리뷰 fix 뒤 `uv run pytest -q`: 30 passed (리뷰 전 26 passed)
- `uv run ruff check .`: All checks passed
- 리뷰 fix 4개 중 코드 변경은 1번(`graph.py`)뿐이고, 리포트의 q1~q3 정답 경로·시간은 변하지 않았다
- 1번의 방향은 CSV 행 순서(응암→역촌→…→구산→응암)를 따랐다. 응암 두 번째 행의 누계(6.6km)가 고리 한 바퀴라서 데이터가 한 방향으로 적혀 있다고 읽었다. 실제 운행 방향은 별도 자료로 확인하지 않았다
